"""
刀塔解析 - Flask后端主应用
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from flask_socketio import SocketIO
import os
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler

# 导入配置
from config.settings import Config
from config.database import db
from utils.response import ApiResponse
from utils.errors import register_error_handlers
from utils.api_monitor import init_monitor, api_monitor
from utils.api_cache import init_cache_manager, cache_route
from utils.rate_limiter import init_rate_limiter, rate_limit_by_user_role
from utils.api_version import init_version_manager, api_version_manager
from utils.swagger_config import init_swagger
from utils.performance import init_performance_monitoring

def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    
    # CORS配置
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # 限流配置 - 使用自定义限流器
    # limiter = Limiter(
    #     app,
    #     key_func=get_remote_address,
    #     default_limits=["100 per minute"]
    # )
    
    # 初始化新的API工具
    init_monitor(app)
    init_cache_manager(app)
    init_rate_limiter(app)
    init_version_manager(app)
    init_swagger(app)
    init_performance_monitoring(app)
    
    # WebSocket配置 - 暂时禁用
    # socketio = SocketIO(app, 
    #                    cors_allowed_origins=app.config['CORS_ORIGINS'],
    #                    async_mode='threading')
    
    # 初始化数据库（如果需要）
    with app.app_context():
        try:
            # 测试数据库连接
            db.engine.connect()
            app.logger.info('数据库连接成功')
        except Exception as e:
            app.logger.error(f'数据库连接失败: {e}')
            raise
    
    # 注册蓝图
    register_blueprints(app)
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 配置日志
    configure_logging(app)
    
    # JWT配置
    configure_jwt(app, jwt)
    
    # 健康检查 - 集成监控功能
    @app.route('/health')
    @app.route('/api/monitor/health')
    def health_check():
        return ApiResponse.success({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': app.config['VERSION'],
            'monitoring': {
                'performance': 'enabled',
                'rate_limiting': 'enabled',
                'caching': 'enabled',
                'versioning': 'enabled'
            }
        })
    
    # API信息
    @app.route('/api/info')
    @cache_route(cache_type='static', ttl=3600)  # 缓存1小时
    def api_info():
        return ApiResponse.success({
            'name': 'Dota Analysis API',
            'version': app.config['VERSION'],
            'description': '刀塔解析API服务',
            'monitoring': {
                'health': '/api/monitor/health',
                'stats': '/api/monitor/stats',
                'rate_limit': '/api/rate-limit/status'
            },
            'endpoints': {
                'auth': '/api/auth',
                'matches': '/api/matches', 
                'experts': '/api/experts',
                'community': '/api/discussions',
                'stats': '/api/stats',
                'unified_data': '/api/unified',
                'learning': '/api/learning',
                'realtime_sync': '/api/realtime',
                'upload': '/api/upload',
                'notifications': '/api/notifications',
                'admin': '/api/admin',
                'search': '/api/search',
                'dem_parser': '/api/dem',
                'version': '/api/version',
                'docs': '/api/docs'
            }
        })
    
    return app, None  # 暂时返回None代替socketio

def register_blueprints(app):
    """注册所有蓝图"""
    from routes.auth import auth_bp
    from routes.matches import matches_bp
    from routes.experts import experts_bp
    from routes.discussions import discussions_bp
    from routes.stats_new import stats_bp  # 使用新的统计路由
    from routes.upload import upload_bp
    from routes.notifications import notifications_bp
    from routes.admin import admin_bp
    from routes.search import search_bp
    from routes.learning import learning_bp
    from routes.realtime_sync import realtime_sync_bp
    from routes.unified_data import unified_data_bp
    from routes.dem_parser import dem_parser_bp
    from routes.monitor import monitor_bp
    from routes.version import version_bp
    
    # 注册API蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(matches_bp, url_prefix='/api/matches')
    app.register_blueprint(experts_bp, url_prefix='/api/experts')
    app.register_blueprint(discussions_bp, url_prefix='/api/discussions')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')  # 新的完整统计API
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(learning_bp, url_prefix='/api/learning')
    app.register_blueprint(realtime_sync_bp, url_prefix='/api/realtime')
    app.register_blueprint(unified_data_bp, url_prefix='/api/unified')
    app.register_blueprint(dem_parser_bp, url_prefix='/api/dem')
    app.register_blueprint(monitor_bp)
    app.register_blueprint(version_bp)

def configure_logging(app):
    """配置日志"""
    if not app.debug and not app.testing:
        # 创建日志目录
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # 文件日志处理器
        file_handler = RotatingFileHandler(
            'logs/dota_analysis.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Dota Analysis API startup')

def configure_jwt(app, jwt):
    """配置JWT"""
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return ApiResponse.error('Token已过期', 'TOKEN_EXPIRED', 401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return ApiResponse.error('Token无效', 'INVALID_TOKEN', 401)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return ApiResponse.error('需要认证', 'MISSING_TOKEN', 401)

# 创建应用实例
app, socketio = create_app()

if __name__ == '__main__':
    # 开发环境运行
    socketio.run(app, 
                debug=app.config['DEBUG'],
                host=app.config['HOST'],
                port=app.config['PORT'])
