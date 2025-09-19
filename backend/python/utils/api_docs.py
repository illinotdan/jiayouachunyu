"""
API文档生成器
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime
import inspect
from flask import current_app, Blueprint

class APIDocumentationGenerator:
    """API文档生成器"""
    
    def __init__(self):
        self.docs = {
            'info': {
                'title': 'Dota Analysis API',
                'version': '1.0.0',
                'description': 'Dota比赛分析和评论API',
                'created_at': datetime.now().isoformat()
            },
            'endpoints': [],
            'schemas': {},
            'error_codes': {}
        }
    
    def scan_blueprints(self, app) -> List[Dict]:
        """扫描所有蓝图和路由"""
        endpoints = []
        
        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'static':
                continue
                
            endpoint_info = {
                'path': str(rule),
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'endpoint': rule.endpoint,
                'function': app.view_functions.get(rule.endpoint).__name__ if rule.endpoint in app.view_functions else None
            }
            
            # 提取蓝图信息
            if '.' in rule.endpoint:
                blueprint_name, func_name = rule.endpoint.split('.', 1)
                endpoint_info['blueprint'] = blueprint_name
                endpoint_info['function'] = func_name
            
            endpoints.append(endpoint_info)
        
        return endpoints
    
    def extract_docstring_info(self, func) -> Dict:
        """从函数的docstring提取API信息"""
        if not func or not func.__doc__:
            return {}
        
        docstring = func.__doc__.strip()
        lines = docstring.split('\n')
        
        info = {
            'description': lines[0] if lines else '',
            'parameters': [],
            'responses': {},
            'example': None
        }
        
        current_section = None
        
        for line in lines[1:]:
            line = line.strip()
            
            if line.startswith('Args:'):
                current_section = 'args'
                continue
            elif line.startswith('Returns:'):
                current_section = 'returns'
                continue
            elif line.startswith('Example:'):
                current_section = 'example'
                continue
            
            if current_section == 'args' and ':' in line:
                param_name, param_desc = line.split(':', 1)
                info['parameters'].append({
                    'name': param_name.strip(),
                    'description': param_desc.strip()
                })
            elif current_section == 'example' and line:
                if not info['example']:
                    info['example'] = line
                else:
                    info['example'] += '\n' + line
        
        return info
    
    def generate_openapi_spec(self, app) -> Dict:
        """生成OpenAPI规范"""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'Dota Analysis API',
                'version': '1.0.0',
                'description': 'Dota比赛分析和评论API',
                'contact': {
                    'name': 'API Support',
                    'email': 'support@dotaanalysis.com'
                },
                'license': {
                    'name': 'MIT',
                    'url': 'https://opensource.org/licenses/MIT'
                }
            },
            'servers': [
                {
                    'url': 'http://localhost:5000/api',
                    'description': '开发环境'
                },
                {
                    'url': 'https://dotaanalysis.com/api',
                    'description': '生产环境'
                }
            ],
            'paths': {},
            'components': {
                'securitySchemes': {
                    'BearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    }
                },
                'schemas': self.generate_schemas()
            },
            'security': [{'BearerAuth': []}],
            'tags': [
                {'name': '认证', 'description': '用户认证相关API'},
                {'name': '比赛', 'description': '比赛数据相关API'},
                {'name': '评论', 'description': '比赛评论相关API'},
                {'name': '专家', 'description': '专家系统相关API'},
                {'name': '统计', 'description': '数据统计相关API'},
                {'name': '用户', 'description': '用户管理相关API'},
                {'name': '学习', 'description': 'AI学习相关API'}
            ]
        }
        
        # 生成路径
        endpoints = self.scan_blueprints(app)
        
        for endpoint in endpoints:
            path = endpoint['path']
            methods = endpoint['methods']
            
            if path not in spec['paths']:
                spec['paths'][path] = {}
            
            for method in methods:
                operation = {
                    'summary': f"{method} {path}",
                    'operationId': f"{method.lower()}_{endpoint['endpoint'].replace('.', '_')}",
                    'tags': [self.get_tag_for_blueprint(endpoint.get('blueprint'))],
                    'responses': {
                        '200': {
                            'description': '成功响应',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'success': {'type': 'boolean'},
                                            'data': {'type': 'object'},
                                            'message': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                
                spec['paths'][path][method.lower()] = operation
        
        return spec
    
    def generate_schemas(self) -> Dict:
        """生成数据模式"""
        return {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'role': {'type': 'string', 'enum': ['user', 'expert', 'admin']},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'Match': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'match_id': {'type': 'string'},
                    'radiant_team': {'type': 'string'},
                    'dire_team': {'type': 'string'},
                    'start_time': {'type': 'integer'},
                    'duration': {'type': 'integer'},
                    'winner': {'type': 'string', 'enum': ['radiant', 'dire']}
                }
            },
            'Comment': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'content': {'type': 'string'},
                    'game_time': {'type': 'integer'},
                    'event_type': {'type': 'string'},
                    'importance': {'type': 'integer', 'minimum': 1, 'maximum': 5},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'ApiResponse': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {'type': 'object'},
                    'message': {'type': 'string'},
                    'error': {
                        'type': 'object',
                        'properties': {
                            'code': {'type': 'string'},
                            'message': {'type': 'string'},
                            'details': {'type': 'object'}
                        }
                    },
                    'timestamp': {'type': 'string', 'format': 'date-time'}
                }
            }
        }
    
    def get_tag_for_blueprint(self, blueprint_name: str) -> str:
        """根据蓝图名称获取标签"""
        tag_mapping = {
            'auth': '认证',
            'matches': '比赛',
            'comments': '评论',
            'experts': '专家',
            'stats': '统计',
            'users': '用户',
            'learning': '学习',
            'admin': '管理员'
        }
        
        return tag_mapping.get(blueprint_name, '其他')
    
    def save_documentation(self, spec: Dict, output_dir: str = 'docs/api'):
        """保存文档到文件"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存OpenAPI规范
        openapi_file = os.path.join(output_dir, 'openapi.json')
        with open(openapi_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
        
        # 生成HTML文档
        html_content = self.generate_html_documentation(spec)
        html_file = os.path.join(output_dir, 'index.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            'openapi': openapi_file,
            'html': html_file
        }
    
    def generate_html_documentation(self, spec: Dict) -> str:
        """生成HTML格式的文档"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec['info']['title']} - API文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .endpoint {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .method {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }}
        .method-get {{ background-color: #61affe; color: white; }}
        .method-post {{ background-color: #49cc90; color: white; }}
        .method-put {{ background-color: #fca130; color: white; }}
        .method-delete {{ background-color: #f93e3e; color: white; }}
        .path {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
            color: #2c3e50;
        }}
        .schema {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 15px;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
        }}
        .tag {{
            display: inline-block;
            background-color: #e74c3c;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{spec['info']['title']}</h1>
        <p>{spec['info']['description']}</p>
        <p>版本: {spec['info']['version']} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>API端点</h2>
"""
        
        # 添加端点信息
        for path, methods in spec['paths'].items():
            for method, operation in methods.items():
                html += f"""
    <div class="endpoint">
        <div>
            <span class="method method-{method}">{method.upper()}</span>
            <span class="path">{path}</span>
            <span class="tag">{operation.get('tags', ['其他'])[0]}</span>
        </div>
        <p>{operation.get('summary', '')}</p>
        
        <h4>响应:</h4>
        <div class="schema">
            <pre>{json.dumps(operation.get('responses', {}), ensure_ascii=False, indent=2)}</pre>
        </div>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html

def generate_api_documentation(app, output_dir: str = 'docs/api'):
    """生成API文档"""
    generator = APIDocumentationGenerator()
    
    # 生成OpenAPI规范
    spec = generator.generate_openapi_spec(app)
    
    # 保存文档
    files = generator.save_documentation(spec, output_dir)
    
    print(f"API文档已生成:")
    print(f"- OpenAPI规范: {files['openapi']}")
    print(f"- HTML文档: {files['html']}")
    
    return files