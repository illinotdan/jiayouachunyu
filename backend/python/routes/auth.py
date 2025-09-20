"""
认证相关API路由
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from marshmallow import Schema, fields, ValidationError
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import re

from ..config.database import db
from ..models.user import User, UserRole, ExpertTier, UserSession
from ..utils.response import ApiResponse
from ..utils.validators import validate_email, validate_password
from ..utils.decorators import limiter

auth_bp = Blueprint('auth', __name__)

# 请求验证模式
class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=lambda x: len(x) >= 3 and len(x) <= 20)
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 6)
    confirm_password = fields.Str(required=True)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

# 黑名单Token存储
blacklisted_tokens = set()

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """用户注册"""
    schema = RegisterSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    # 验证密码确认
    if data['password'] != data['confirm_password']:
        return ApiResponse.error('两次输入的密码不一致', 'PASSWORD_MISMATCH', 400)
    
    # 验证密码强度
    if not validate_password(data['password']):
        return ApiResponse.error(
            '密码必须包含字母和数字，长度6-50字符', 
            'WEAK_PASSWORD', 
            400
        )
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return ApiResponse.error('用户名已存在', 'USERNAME_EXISTS', 409)
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return ApiResponse.error('邮箱已被注册', 'EMAIL_EXISTS', 409)
    
    try:
        # 创建新用户
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            avatar_url=f"https://api.dicebear.com/7.x/avataaars/svg?seed={data['username']}"
        )
        
        db.session.add(user)
        db.session.commit()
        
        # 生成Token
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # 记录会话
        session = UserSession(
            user_id=user.id,
            token_hash=access_token[:50],  # 存储token的前50个字符作为标识
            expires_at=datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(session)
        db.session.commit()
        
        return ApiResponse.success({
            'user': user.to_dict(),
            'token': access_token,
            'refreshToken': refresh_token,
            'expiresIn': int((datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']).timestamp())
        }, '注册成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"注册失败: {e}")
        return ApiResponse.error('注册失败，请稍后重试', 'REGISTRATION_FAILED', 500)

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """用户登录"""
    schema = LoginSchema()
    
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return ApiResponse.error('参数验证失败', 'VALIDATION_ERROR', 400, err.messages)
    
    # 查找用户
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return ApiResponse.error('邮箱或密码错误', 'INVALID_CREDENTIALS', 401)
    
    if not user.is_active:
        return ApiResponse.error('账号已被禁用', 'ACCOUNT_DISABLED', 403)
    
    try:
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        
        # 生成Token
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        # 记录会话
        session = UserSession(
            user_id=user.id,
            token_hash=access_token[:50],
            expires_at=datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(session)
        db.session.commit()
        
        return ApiResponse.success({
            'user': user.to_dict(include_sensitive=True),
            'token': access_token,
            'refreshToken': refresh_token,
            'expiresIn': int((datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']).timestamp())
        }, '登录成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"登录失败: {e}")
        return ApiResponse.error('登录失败，请稍后重试', 'LOGIN_FAILED', 500)

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        # 获取当前token
        jti = get_jwt()['jti']
        blacklisted_tokens.add(jti)
        
        # 删除会话记录
        user_id = get_jwt_identity()
        UserSession.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        return ApiResponse.success(None, '登出成功')
        
    except Exception as e:
        current_app.logger.error(f"登出失败: {e}")
        return ApiResponse.error('登出失败', 'LOGOUT_FAILED', 500)

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新Token"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return ApiResponse.error('用户不存在或已被禁用', 'USER_NOT_FOUND', 404)
        
        # 生成新的访问Token
        access_token = create_access_token(identity=user_id)
        
        return ApiResponse.success({
            'token': access_token,
            'expiresIn': int((datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES']).timestamp())
        })
        
    except Exception as e:
        current_app.logger.error(f"Token刷新失败: {e}")
        return ApiResponse.error('Token刷新失败', 'REFRESH_FAILED', 500)

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        return ApiResponse.success({
            'user': user.to_dict(include_sensitive=True)
        })
        
    except Exception as e:
        current_app.logger.error(f"获取用户信息失败: {e}")
        return ApiResponse.error('获取用户信息失败', 'GET_USER_FAILED', 500)

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """更新当前用户信息"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        
        # 更新允许的字段
        if 'username' in data:
            # 检查用户名是否已被使用
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return ApiResponse.error('用户名已存在', 'USERNAME_EXISTS', 409)
            user.username = data['username']
        
        if 'bio' in data:
            user.bio = data['bio']
        
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return ApiResponse.success({
            'user': user.to_dict(include_sensitive=True)
        }, '用户信息更新成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户信息失败: {e}")
        return ApiResponse.error('更新失败，请稍后重试', 'UPDATE_FAILED', 500)

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        data = request.json
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        
        if not old_password or not new_password:
            return ApiResponse.error('请提供旧密码和新密码', 'MISSING_PASSWORDS', 400)
        
        # 验证旧密码
        if not user.check_password(old_password):
            return ApiResponse.error('原密码错误', 'INVALID_OLD_PASSWORD', 400)
        
        # 验证新密码强度
        if not validate_password(new_password):
            return ApiResponse.error(
                '新密码必须包含字母和数字，长度6-50字符', 
                'WEAK_PASSWORD', 
                400
            )
        
        # 更新密码
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        # 清除所有会话（强制重新登录）
        UserSession.query.filter_by(user_id=user.id).delete()
        
        db.session.commit()
        
        return ApiResponse.success(None, '密码修改成功，请重新登录')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"修改密码失败: {e}")
        return ApiResponse.error('修改密码失败', 'CHANGE_PASSWORD_FAILED', 500)

@auth_bp.route('/steam', methods=['GET'])
def steam_login():
    """Steam登录重定向"""
    # TODO: 实现Steam OAuth登录
    return ApiResponse.error('Steam登录功能开发中', 'NOT_IMPLEMENTED', 501)

@auth_bp.route('/steam/callback', methods=['GET'])
def steam_callback():
    """Steam登录回调"""
    # TODO: 实现Steam OAuth回调处理
    return ApiResponse.error('Steam登录功能开发中', 'NOT_IMPLEMENTED', 501)

# JWT Token黑名单检查
@auth_bp.before_app_request
def check_if_token_revoked():
    """检查Token是否被撤销"""
    if request.endpoint and 'auth' in request.endpoint:
        return
    
    try:
        if request.headers.get('Authorization'):
            jti = get_jwt().get('jti')
            if jti in blacklisted_tokens:
                return ApiResponse.error('Token已被撤销', 'TOKEN_REVOKED', 401)
    except:
        pass
