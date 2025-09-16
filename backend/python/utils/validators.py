"""
数据验证工具
"""

import re
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email):
    """验证邮箱格式"""
    try:
        email_validate(email)
        return True
    except EmailNotValidError:
        return False

def validate_password(password):
    """验证密码强度"""
    if not password or len(password) < 6 or len(password) > 50:
        return False
    
    # 必须包含字母和数字
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    return has_letter and has_digit

def validate_username(username):
    """验证用户名格式"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    
    # 只允许字母、数字、下划线、中文
    pattern = r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$'
    return bool(re.match(pattern, username))

def validate_tags(tags):
    """验证标签"""
    if not isinstance(tags, list):
        return False
    
    if len(tags) > 5:
        return False
    
    for tag in tags:
        if not isinstance(tag, str) or len(tag) > 20 or len(tag) < 1:
            return False
    
    return True

def validate_content_length(content, min_length=10, max_length=10000):
    """验证内容长度"""
    if not content or not isinstance(content, str):
        return False
    
    content_length = len(content.strip())
    return min_length <= content_length <= max_length

def sanitize_html(content):
    """清理HTML内容"""
    import bleach
    
    # 允许的HTML标签
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img'
    ]
    
    # 允许的属性
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        '*': ['class']
    }
    
    # 允许的协议
    allowed_protocols = ['http', 'https', 'mailto']
    
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=allowed_protocols,
        strip=True
    )

def validate_file_extension(filename, allowed_extensions):
    """验证文件扩展名"""
    if not filename:
        return False
    
    extension = filename.rsplit('.', 1)[-1].lower()
    return extension in allowed_extensions

def validate_image_file(file):
    """验证图片文件"""
    from PIL import Image
    import io
    
    try:
        # 检查是否为有效图片
        image = Image.open(io.BytesIO(file.read()))
        image.verify()
        
        # 重置文件指针
        file.seek(0)
        
        # 检查图片尺寸
        if image.width > 2048 or image.height > 2048:
            return False, "图片尺寸不能超过2048x2048"
        
        # 检查文件大小（5MB）
        if len(file.read()) > 5 * 1024 * 1024:
            return False, "文件大小不能超过5MB"
        
        file.seek(0)
        return True, None
        
    except Exception as e:
        return False, f"无效的图片文件: {str(e)}"

def validate_url(url):
    """验证URL格式"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))

class ContentValidator:
    """内容验证器类"""
    
    @staticmethod
    def validate_discussion_title(title):
        """验证讨论标题"""
        if not title or not isinstance(title, str):
            return False, "标题不能为空"
        
        title = title.strip()
        if len(title) < 5:
            return False, "标题至少需要5个字符"
        
        if len(title) > 200:
            return False, "标题不能超过200个字符"
        
        # 检查是否包含敏感词
        if ContentValidator.contains_sensitive_words(title):
            return False, "标题包含不当内容"
        
        return True, None
    
    @staticmethod
    def validate_discussion_content(content):
        """验证讨论内容"""
        if not content or not isinstance(content, str):
            return False, "内容不能为空"
        
        content = content.strip()
        if len(content) < 50:
            return False, "内容至少需要50个字符"
        
        if len(content) > 10000:
            return False, "内容不能超过10000个字符"
        
        # 检查是否包含敏感词
        if ContentValidator.contains_sensitive_words(content):
            return False, "内容包含不当内容"
        
        return True, None
    
    @staticmethod
    def contains_sensitive_words(text):
        """检查敏感词"""
        # 简单的敏感词检查，实际项目中应该使用更完善的敏感词库
        sensitive_words = [
            '垃圾', '傻逼', '脑残', '智障', '废物', 
            'fuck', 'shit', 'damn', 'stupid'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in sensitive_words)
    
    @staticmethod
    def extract_mentions(content):
        """提取@用户提及"""
        mention_pattern = r'@([a-zA-Z0-9_\u4e00-\u9fa5]+)'
        mentions = re.findall(mention_pattern, content)
        return list(set(mentions))  # 去重
    
    @staticmethod
    def extract_hashtags(content):
        """提取话题标签"""
        hashtag_pattern = r'#([a-zA-Z0-9_\u4e00-\u9fa5]+)'
        hashtags = re.findall(hashtag_pattern, content)
        return list(set(hashtags))  # 去重

def validate_pagination_params(page=1, page_size=20, max_page_size=100):
    """验证分页参数"""
    try:
        page = int(page)
        page_size = int(page_size)
        
        if page < 1:
            page = 1
        
        if page_size < 1:
            page_size = 20
        elif page_size > max_page_size:
            page_size = max_page_size
        
        return page, page_size
        
    except (ValueError, TypeError):
        return 1, 20

def validate_sort_params(sort_by, allowed_sorts):
    """验证排序参数"""
    if not sort_by or sort_by not in allowed_sorts:
        return allowed_sorts[0] if allowed_sorts else None
    
    return sort_by

def validate_date_range(date_from, date_to):
    """验证日期范围"""
    from datetime import datetime
    
    try:
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        if date_from and date_to and date_from > date_to:
            return None, None, "开始日期不能晚于结束日期"
        
        return date_from, date_to, None
        
    except ValueError as e:
        return None, None, f"日期格式错误: {str(e)}"
