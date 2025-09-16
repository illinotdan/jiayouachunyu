"""
分页工具
"""

from flask import request
from flask_sqlalchemy import Pagination
from math import ceil

def paginate(query, page=None, per_page=None, max_per_page=100):
    """
    通用分页函数
    
    Args:
        query: SQLAlchemy查询对象
        page: 页码，默认从request.args获取
        per_page: 每页数量，默认从request.args获取
        max_per_page: 最大每页数量
    
    Returns:
        Pagination对象
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    
    if per_page is None:
        per_page = request.args.get('page_size', 20, type=int)
    
    # 验证参数
    if page < 1:
        page = 1
    
    if per_page < 1:
        per_page = 20
    elif per_page > max_per_page:
        per_page = max_per_page
    
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

class PaginationHelper:
    """分页助手类"""
    
    @staticmethod
    def get_pagination_info(pagination):
        """获取分页信息"""
        return {
            'page': pagination.page,
            'pageSize': pagination.per_page,
            'total': pagination.total,
            'totalPages': pagination.pages,
            'hasNext': pagination.has_next,
            'hasPrev': pagination.has_prev,
            'nextPage': pagination.next_num if pagination.has_next else None,
            'prevPage': pagination.prev_num if pagination.has_prev else None
        }
    
    @staticmethod
    def create_pagination_links(pagination, endpoint, **kwargs):
        """创建分页链接"""
        from flask import url_for
        
        links = {}
        
        if pagination.has_prev:
            links['prev'] = url_for(endpoint, page=pagination.prev_num, **kwargs)
            links['first'] = url_for(endpoint, page=1, **kwargs)
        
        if pagination.has_next:
            links['next'] = url_for(endpoint, page=pagination.next_num, **kwargs)
            links['last'] = url_for(endpoint, page=pagination.pages, **kwargs)
        
        links['self'] = url_for(endpoint, page=pagination.page, **kwargs)
        
        return links
    
    @staticmethod
    def validate_pagination_request():
        """验证分页请求参数"""
        page = request.args.get('page', 1)
        page_size = request.args.get('page_size', 20)
        
        try:
            page = max(1, int(page))
        except (ValueError, TypeError):
            page = 1
        
        try:
            page_size = max(1, min(100, int(page_size)))
        except (ValueError, TypeError):
            page_size = 20
        
        return page, page_size

def create_pagination_response(items, pagination, message="获取成功"):
    """创建分页响应"""
    from utils.response import ApiResponse
    
    return ApiResponse.success({
        'items': items,
        'pagination': PaginationHelper.get_pagination_info(pagination)
    }, message)

def offset_paginate(query, page, per_page):
    """
    使用OFFSET/LIMIT的分页实现
    适用于大数据量的场景
    """
    # 计算偏移量
    offset = (page - 1) * per_page
    
    # 获取总数（可能很慢，对于大表可以考虑缓存或估算）
    total = query.count()
    
    # 获取当前页数据
    items = query.offset(offset).limit(per_page).all()
    
    # 计算总页数
    pages = ceil(total / per_page) if per_page > 0 else 0
    
    # 创建类似Flask-SQLAlchemy Pagination的对象
    class OffsetPagination:
        def __init__(self, items, page, per_page, total, pages):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = pages
            self.has_next = page < pages
            self.has_prev = page > 1
            self.next_num = page + 1 if self.has_next else None
            self.prev_num = page - 1 if self.has_prev else None
    
    return OffsetPagination(items, page, per_page, total, pages)

def cursor_paginate(query, cursor_field, cursor_value=None, per_page=20, direction='next'):
    """
    游标分页实现
    适用于实时数据和大数据量场景
    
    Args:
        query: SQLAlchemy查询对象
        cursor_field: 游标字段（通常是id或created_at）
        cursor_value: 游标值
        per_page: 每页数量
        direction: 分页方向 ('next' 或 'prev')
    
    Returns:
        包含items和游标信息的字典
    """
    if cursor_value:
        if direction == 'next':
            query = query.filter(cursor_field > cursor_value)
            query = query.order_by(cursor_field.asc())
        else:  # prev
            query = query.filter(cursor_field < cursor_value)
            query = query.order_by(cursor_field.desc())
    else:
        query = query.order_by(cursor_field.desc())
    
    # 多获取一个，用于判断是否有下一页
    items = query.limit(per_page + 1).all()
    
    has_more = len(items) > per_page
    if has_more:
        items = items[:per_page]
    
    # 获取游标值
    next_cursor = None
    prev_cursor = None
    
    if items:
        if direction == 'next' or cursor_value is None:
            next_cursor = getattr(items[-1], cursor_field.name) if has_more else None
            prev_cursor = getattr(items[0], cursor_field.name) if cursor_value else None
        else:
            next_cursor = getattr(items[0], cursor_field.name) if cursor_value else None
            prev_cursor = getattr(items[-1], cursor_field.name) if has_more else None
            
            # 反转列表（因为prev方向是倒序查询的）
            items.reverse()
    
    return {
        'items': items,
        'hasMore': has_more,
        'nextCursor': next_cursor,
        'prevCursor': prev_cursor,
        'count': len(items)
    }
