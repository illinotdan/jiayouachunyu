"""
API版本管理
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class APIVersionManager:
    """API版本管理器"""
    
    def __init__(self):
        self.versions = {}
        self.current_version = '1.0.0'
        self.deprecated_versions = set()
        self.version_routes = {}
    
    def register_version(self, version: str, blueprint: Blueprint, deprecated: bool = False):
        """注册API版本"""
        self.versions[version] = {
            'blueprint': blueprint,
            'deprecated': deprecated,
            'registered_at': datetime.now().isoformat()
        }
        
        if deprecated:
            self.deprecated_versions.add(version)
        
        logger.info(f"API版本 {version} 已注册 (deprecated: {deprecated})")
    
    def create_versioned_blueprint(self, name: str, version: str, import_name: str) -> Blueprint:
        """创建版本化蓝图"""
        blueprint_name = f"{name}_v{version.replace('.', '_')}"
        url_prefix = f"/api/v{version}/{name}"
        
        blueprint = Blueprint(blueprint_name, import_name, url_prefix=url_prefix)
        
        # 添加版本信息到蓝图
        blueprint.version = version
        blueprint.original_name = name
        
        return blueprint
    
    def version_route(self, version: str, rule: str, **options):
        """版本化路由装饰器"""
        def decorator(func):
            # 存储版本化路由信息
            if version not in self.version_routes:
                self.version_routes[version] = []
            
            self.version_routes[version].append({
                'rule': rule,
                'function': func.__name__,
                'options': options
            })
            
            # 添加版本信息到函数
            func.api_version = version
            func.original_rule = rule
            
            return func
        
        return decorator
    
    def version_required(self, min_version: str = None, max_version: str = None):
        """版本要求装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取客户端版本
                client_version = self.get_client_version()
                
                # 检查版本要求
                if min_version and not self.is_version_compatible(client_version, min_version, '>='):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'VERSION_TOO_OLD',
                            'message': f'API版本过旧，需要 {min_version} 或更高版本'
                        }
                    }), 426  # Upgrade Required
                
                if max_version and not self.is_version_compatible(client_version, max_version, '<='):
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'VERSION_TOO_NEW',
                            'message': f'API版本过新，最高支持 {max_version}'
                        }
                    }), 400
                
                # 检查是否使用废弃版本
                if client_version in self.deprecated_versions:
                    return jsonify({
                        'success': False,
                        'warning': {
                            'code': 'VERSION_DEPRECATED',
                            'message': f'API版本 {client_version} 已废弃，请升级到最新版本'
                        }
                    }), 299  # 自定义状态码表示警告
                
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def get_client_version(self) -> str:
        """获取客户端API版本"""
        # 从请求头获取版本
        version = request.headers.get('API-Version')
        if version:
            return version
        
        # 从查询参数获取版本
        version = request.args.get('api_version')
        if version:
            return version
        
        # 从URL路径获取版本
        path = request.path
        if '/api/v' in path:
            parts = path.split('/')
            for part in parts:
                if part.startswith('v') and len(part) > 1:
                    return part[1:].replace('_', '.')
        
        # 默认返回当前版本
        return self.current_version
    
    def is_version_compatible(self, client_version: str, required_version: str, operator: str = '>=') -> bool:
        """检查版本兼容性"""
        try:
            client_parts = [int(x) for x in client_version.split('.')]
            required_parts = [int(x) for x in required_version.split('.')]
            
            # 补齐版本号位数
            max_len = max(len(client_parts), len(required_parts))
            client_parts.extend([0] * (max_len - len(client_parts)))
            required_parts.extend([0] * (max_len - len(required_parts)))
            
            if operator == '>=':
                return client_parts >= required_parts
            elif operator == '<=':
                return client_parts <= required_parts
            elif operator == '==':
                return client_parts == required_parts
            elif operator == '>':
                return client_parts > required_parts
            elif operator == '<':
                return client_parts < required_parts
            else:
                return False
        except (ValueError, AttributeError):
            return False
    
    def get_all_versions(self):
        """获取所有版本信息"""
        # 初始化版本列表如果不存在
        if not hasattr(self, 'versions'):
            self.versions = [
                {
                    'version': '1.0.0',
                    'status': 'deprecated',
                    'release_date': '2024-01-01',
                    'deprecation_date': '2024-04-01'
                },
                {
                    'version': '1.1.0',
                    'status': 'deprecated',
                    'release_date': '2024-02-01',
                    'deprecation_date': '2024-05-01'
                },
                {
                    'version': '1.2.0',
                    'status': 'current',
                    'release_date': '2024-03-01',
                    'deprecation_date': None
                }
            ]
        return self.versions.copy()
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的信息"""
        # 初始化版本详情如果不存在
        if not hasattr(self, 'version_details'):
            self.version_details = {
                '1.0.0': {
                    'status': 'deprecated',
                    'release_date': '2024-01-01',
                    'deprecation_date': '2024-04-01',
                    'changes': ['初始版本发布', '基础API端点实现'],
                    'endpoints': ['/api/auth/*', '/api/matches/*']
                },
                '1.1.0': {
                    'status': 'deprecated', 
                    'release_date': '2024-02-01',
                    'deprecation_date': '2024-05-01',
                    'changes': ['添加专家分析功能', '社区讨论系统'],
                    'endpoints': ['/api/experts/*', '/api/community/*']
                },
                '1.2.0': {
                    'status': 'current',
                    'release_date': '2024-03-01',
                    'deprecation_date': None,
                    'changes': ['API版本管理系统', '性能监控和限流', '缓存优化'],
                    'endpoints': ['/api/version/*', '/api/monitor/*', '/api/cache/*']
                }
            }
        return self.version_details.get(version)

    def get_current_version(self):
        """获取当前版本"""
        # 初始化当前版本如果不存在
        if not hasattr(self, 'current_version'):
            self.current_version = '1.2.0'
        return self.current_version
    
    def generate_version_changelog(self) -> Dict[str, Any]:
        """生成版本变更日志"""
        return {
            '1.0.0': {
                'release_date': '2024-01-01',
                'changes': [
                    '初始版本发布',
                    '用户认证系统',
                    '比赛数据API',
                    '评论系统',
                    '专家系统'
                ],
                'breaking_changes': [],
                'deprecated_endpoints': []
            },
            '1.1.0': {
                'release_date': '2024-02-01',
                'changes': [
                    '新增AI学习模块',
                    '优化比赛分析算法',
                    '增加批量操作API',
                    '改进错误处理机制'
                ],
                'breaking_changes': [
                    '/api/matches/bulk 端点参数格式变更',
                    '用户角色枚举值更新'
                ],
                'deprecated_endpoints': [
                    '/api/v1/users/old-format'
                ]
            },
            '2.0.0': {
                'release_date': '2024-03-01',
                'changes': [
                    '全新的API架构',
                    '改进的性能和安全性',
                    '支持WebSocket连接',
                    '增强的监控和日志'
                ],
                'breaking_changes': [
                    'API认证方式改为JWT',
                    '所有端点的响应格式更新',
                    '分页参数名称变更'
                ],
                'deprecated_endpoints': [
                    '/api/v1/auth/login',
                    '/api/v1/auth/logout'
                ]
            }
        }
    
    def get_migration_guide(self, version: str) -> Optional[Dict[str, Any]]:
        """获取版本迁移指南"""
        # 初始化迁移指南如果不存在
        if not hasattr(self, 'migration_guides'):
            self.migration_guides = {
                '1.1.0': {
                    'steps': [
                        '更新认证端点从 /api/auth/login 到 /api/v1.1/auth/login',
                        '替换旧的响应格式为新格式',
                        '添加错误处理逻辑'
                    ],
                    'breaking_changes': ['响应格式变更', '错误码重新定义'],
                    'deprecated_features': ['旧的认证方式', '某些端点参数']
                },
                '1.2.0': {
                    'steps': [
                        '添加版本管理相关的API调用',
                        '更新监控和限流配置',
                        '启用缓存优化功能'
                    ],
                    'breaking_changes': ['限流规则更新', '缓存策略变更'],
                    'deprecated_features': ['旧的数据同步方式']
                }
            }
        return self.migration_guides.get(version)

# 全局版本管理器
api_version_manager = APIVersionManager()

def init_version_manager(app):
    """初始化版本管理器"""
    # 创建版本管理蓝图
    version_bp = Blueprint('version', __name__, url_prefix='/api')
    
    @version_bp.route('/version', methods=['GET'])
    def get_version():
        """获取当前API版本信息"""
        return jsonify({
            'success': True,
            'data': api_version_manager.get_version_info(api_version_manager.current_version)
        })
    
    @version_bp.route('/version/changelog', methods=['GET'])
    def get_changelog():
        """获取版本变更日志"""
        return jsonify({
            'success': True,
            'data': api_version_manager.generate_version_changelog()
        })
    
    @version_bp.route('/version/migrate', methods=['POST'])
    def migrate_version():
        """获取版本迁移指南"""
        data = request.get_json() or {}
        from_version = data.get('from_version')
        to_version = data.get('to_version')
        
        if not from_version or not to_version:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'MISSING_PARAMETERS',
                    'message': '需要提供from_version和to_version参数'
                }
            }), 400
        
        return jsonify({
            'success': True,
            'data': api_version_manager.create_migration_guide(from_version, to_version)
        })
    
    app.register_blueprint(version_bp)
    
    logger.info("API版本管理器已初始化")

# 便捷装饰器
def api_version(version: str, rule: str, **options):
    """API版本路由装饰器"""
    return api_version_manager.version_route(version, rule, **options)

def require_version(min_version: str = None, max_version: str = None):
    """版本要求装饰器"""
    return api_version_manager.version_required(min_version, max_version)