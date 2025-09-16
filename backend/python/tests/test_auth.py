"""
认证API测试
"""

import pytest
import json
from app import create_app, socketio
from config.settings import TestingConfig
from config.database import db
from models.user import User

@pytest.fixture
def app():
    """创建测试应用"""
    app, _ = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """创建认证头"""
    # 注册测试用户
    register_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'test123456',
        'confirm_password': 'test123456'
    }
    
    response = client.post('/api/auth/register', 
                          data=json.dumps(register_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    token = data['data']['token']
    
    return {'Authorization': f'Bearer {token}'}

class TestAuthAPI:
    """认证API测试类"""
    
    def test_register_success(self, client):
        """测试成功注册"""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response = client.post('/api/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'token' in response_data['data']
        assert response_data['data']['user']['username'] == 'newuser'
    
    def test_register_duplicate_username(self, client):
        """测试重复用户名注册"""
        # 先注册一个用户
        data1 = {
            'username': 'testuser',
            'email': 'test1@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response1 = client.post('/api/auth/register',
                               data=json.dumps(data1),
                               content_type='application/json')
        assert response1.status_code == 200
        
        # 尝试注册相同用户名
        data2 = {
            'username': 'testuser',
            'email': 'test2@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response2 = client.post('/api/auth/register',
                               data=json.dumps(data2),
                               content_type='application/json')
        
        assert response2.status_code == 409
        response_data = json.loads(response2.data)
        assert response_data['success'] is False
        assert 'USERNAME_EXISTS' in response_data['error']['code']
    
    def test_register_invalid_password(self, client):
        """测试无效密码注册"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123',  # 太短
            'confirm_password': '123'
        }
        
        response = client.post('/api/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False
    
    def test_login_success(self, client):
        """测试成功登录"""
        # 先注册用户
        register_data = {
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        client.post('/api/auth/register',
                   data=json.dumps(register_data),
                   content_type='application/json')
        
        # 登录
        login_data = {
            'email': 'login@example.com',
            'password': 'password123'
        }
        
        response = client.post('/api/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'token' in response_data['data']
    
    def test_login_invalid_credentials(self, client):
        """测试无效凭据登录"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False
    
    def test_get_current_user(self, client, auth_headers):
        """测试获取当前用户信息"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['user']['username'] == 'testuser'
    
    def test_get_current_user_unauthorized(self, client):
        """测试未授权获取用户信息"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False
    
    def test_logout(self, client, auth_headers):
        """测试登出"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_update_user_info(self, client, auth_headers):
        """测试更新用户信息"""
        data = {
            'bio': '这是我的新简介'
        }
        
        response = client.put('/api/auth/me',
                             data=json.dumps(data),
                             content_type='application/json',
                             headers=auth_headers)
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['user']['bio'] == '这是我的新简介'
