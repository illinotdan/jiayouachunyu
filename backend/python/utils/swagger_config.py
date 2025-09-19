"""
Swagger API文档配置
"""

from flasgger import Swagger

def init_swagger(app):
    """初始化Swagger文档"""
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/"
    }
    
    swagger_template = {
        "swagger": "3.0",
        "info": {
            "title": "Dota Analysis API",
            "description": "Dota比赛分析和评论API文档",
            "version": "1.0.0",
            "contact": {
                "name": "API Support",
                "email": "support@dotaanalysis.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "basePath": "/api",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT认证令牌，格式: Bearer <token>"
            }
        },
        "security": [{"Bearer": []}],
        "tags": [
            {
                "name": "认证",
                "description": "用户认证相关API"
            },
            {
                "name": "比赛",
                "description": "比赛数据相关API"
            },
            {
                "name": "评论",
                "description": "比赛评论相关API"
            },
            {
                "name": "专家",
                "description": "专家系统相关API"
            },
            {
                "name": "统计",
                "description": "数据统计相关API"
            },
            {
                "name": "用户",
                "description": "用户管理相关API"
            },
            {
                "name": "学习",
                "description": "AI学习相关API"
            }
        ]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)

def get_swagger_config():
    """获取Swagger配置"""
    return {
        "title": "Dota Analysis API",
        "version": "1.0.0",
        "description": "Dota比赛分析和评论API",
        "termsOfService": "https://dotaanalysis.com/terms",
        "contact": {
            "name": "API Support",
            "email": "support@dotaanalysis.com"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        }
    }