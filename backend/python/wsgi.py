"""
WSGI应用入口点
用于生产环境部署
"""

import os
from app import create_app, socketio
from config.settings import config

# 获取环境配置
config_name = os.environ.get('FLASK_ENV', 'production')
app, socketio = create_app(config[config_name])

if __name__ == "__main__":
    socketio.run(app)
