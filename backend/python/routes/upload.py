"""
文件上传相关API路由
"""

from flask import Blueprint, request, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from PIL import Image
import io

from config.database import db
from models.user import User
from utils.response import ApiResponse
from utils.decorators import limiter
from utils.validators import validate_file_extension, validate_image_file

upload_bp = Blueprint('upload', __name__)

def allowed_file(filename, allowed_extensions=None):
    """检查文件是否允许上传"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    # 获取文件扩展名
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # 生成UUID文件名
    unique_name = str(uuid.uuid4())
    
    return f"{unique_name}.{ext}" if ext else unique_name

def create_upload_path(subfolder=''):
    """创建上传路径"""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # 按日期组织文件夹
    date_folder = datetime.now().strftime('%Y/%m/%d')
    full_path = os.path.join(upload_folder, subfolder, date_folder)
    
    # 创建目录
    os.makedirs(full_path, exist_ok=True)
    
    return full_path

def resize_image(image_file, max_width=800, max_height=600, quality=85):
    """调整图片大小"""
    try:
        # 打开图片
        image = Image.open(image_file)
        
        # 如果是RGBA模式，转换为RGB
        if image.mode == 'RGBA':
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 计算新尺寸（保持宽高比）
        width, height = image.size
        if width > max_width or height > max_height:
            # 计算缩放比例
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # 调整大小
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 保存到内存
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output, image.size
        
    except Exception as e:
        current_app.logger.error(f"图片处理失败: {e}")
        return None, None

@upload_bp.route('/avatar', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def upload_avatar():
    """上传用户头像"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 检查文件
        if 'file' not in request.files:
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        if not allowed_file(file.filename):
            return ApiResponse.error(
                '不支持的文件格式，请上传 PNG、JPG、JPEG 或 GIF 格式的图片',
                'INVALID_FILE_TYPE',
                400
            )
        
        # 验证图片文件
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return ApiResponse.error(error_msg, 'INVALID_IMAGE', 400)
        
        # 调整图片大小
        resized_image, size = resize_image(file, max_width=400, max_height=400)
        if not resized_image:
            return ApiResponse.error('图片处理失败', 'IMAGE_PROCESSING_FAILED', 500)
        
        # 生成文件名和路径
        filename = generate_unique_filename(file.filename)
        upload_path = create_upload_path('avatars')
        file_path = os.path.join(upload_path, filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(resized_image.read())
        
        # 生成访问URL
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        avatar_url = url_for('static', filename=f'uploads/{relative_path}', _external=True)
        
        # 更新用户头像
        old_avatar = user.avatar_url
        user.avatar_url = avatar_url
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 删除旧头像文件（如果是本地文件）
        if old_avatar and 'uploads/' in old_avatar:
            try:
                old_file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    old_avatar.split('uploads/')[-1]
                )
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except:
                pass
        
        return ApiResponse.success({
            'avatarUrl': avatar_url,
            'size': size
        }, '头像上传成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"头像上传失败: {e}")
        return ApiResponse.error('头像上传失败', 'AVATAR_UPLOAD_FAILED', 500)

@upload_bp.route('/image', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def upload_image():
    """上传讨论中的图片"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return ApiResponse.error('用户不存在', 'USER_NOT_FOUND', 404)
        
        # 检查文件
        if 'file' not in request.files:
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        if not allowed_file(file.filename):
            return ApiResponse.error(
                '不支持的文件格式',
                'INVALID_FILE_TYPE',
                400
            )
        
        # 验证图片文件
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return ApiResponse.error(error_msg, 'INVALID_IMAGE', 400)
        
        # 调整图片大小
        resized_image, size = resize_image(file, max_width=1200, max_height=800)
        if not resized_image:
            return ApiResponse.error('图片处理失败', 'IMAGE_PROCESSING_FAILED', 500)
        
        # 生成文件名和路径
        filename = generate_unique_filename(file.filename)
        upload_path = create_upload_path('images')
        file_path = os.path.join(upload_path, filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(resized_image.read())
        
        # 生成访问URL
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        image_url = url_for('static', filename=f'uploads/{relative_path}', _external=True)
        
        # 记录上传日志
        current_app.logger.info(f"用户 {user.username} 上传图片: {filename}")
        
        return ApiResponse.success({
            'imageUrl': image_url,
            'filename': filename,
            'size': size,
            'originalName': file.filename
        }, '图片上传成功')
        
    except Exception as e:
        current_app.logger.error(f"图片上传失败: {e}")
        return ApiResponse.error('图片上传失败', 'IMAGE_UPLOAD_FAILED', 500)

@upload_bp.route('/team-logo', methods=['POST'])
@jwt_required()
@limiter.limit("3 per minute")
def upload_team_logo():
    """上传战队Logo（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role.value != 'admin':
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        # 检查文件
        if 'file' not in request.files:
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        file = request.files['file']
        team_id = request.form.get('team_id')
        
        if not team_id:
            return ApiResponse.error('缺少战队ID', 'MISSING_TEAM_ID', 400)
        
        # 验证战队是否存在
        from models.match import Team
        team = Team.query.get(team_id)
        if not team:
            return ApiResponse.error('战队不存在', 'TEAM_NOT_FOUND', 404)
        
        if file.filename == '':
            return ApiResponse.error('没有选择文件', 'NO_FILE_SELECTED', 400)
        
        if not allowed_file(file.filename):
            return ApiResponse.error('不支持的文件格式', 'INVALID_FILE_TYPE', 400)
        
        # 验证图片文件
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return ApiResponse.error(error_msg, 'INVALID_IMAGE', 400)
        
        # 调整图片大小（Logo通常是正方形）
        resized_image, size = resize_image(file, max_width=200, max_height=200)
        if not resized_image:
            return ApiResponse.error('图片处理失败', 'IMAGE_PROCESSING_FAILED', 500)
        
        # 生成文件名和路径
        filename = f"team_{team_id}_{generate_unique_filename(file.filename)}"
        upload_path = create_upload_path('logos')
        file_path = os.path.join(upload_path, filename)
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(resized_image.read())
        
        # 生成访问URL
        relative_path = os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])
        logo_url = url_for('static', filename=f'uploads/{relative_path}', _external=True)
        
        # 更新战队Logo
        old_logo = team.logo_url
        team.logo_url = logo_url
        team.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # 删除旧Logo文件
        if old_logo and 'uploads/' in old_logo:
            try:
                old_file_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    old_logo.split('uploads/')[-1]
                )
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            except:
                pass
        
        return ApiResponse.success({
            'logoUrl': logo_url,
            'teamId': team_id,
            'size': size
        }, '战队Logo上传成功')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Logo上传失败: {e}")
        return ApiResponse.error('Logo上传失败', 'LOGO_UPLOAD_FAILED', 500)

@upload_bp.route('/files/<path:filename>')
def uploaded_file(filename):
    """获取上传的文件"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return ApiResponse.error('文件不存在', 'FILE_NOT_FOUND', 404)
        
        # 安全检查：确保文件在上传目录内
        if not os.path.abspath(file_path).startswith(os.path.abspath(upload_folder)):
            return ApiResponse.error('无效的文件路径', 'INVALID_PATH', 403)
        
        from flask import send_file
        return send_file(file_path)
        
    except Exception as e:
        current_app.logger.error(f"获取文件失败: {e}")
        return ApiResponse.error('获取文件失败', 'GET_FILE_FAILED', 500)

@upload_bp.route('/cleanup', methods=['POST'])
@jwt_required()
def cleanup_unused_files():
    """清理未使用的文件（管理员）"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role.value != 'admin':
            return ApiResponse.error('权限不足', 'PERMISSION_DENIED', 403)
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # 获取数据库中引用的所有文件URL
        referenced_files = set()
        
        # 用户头像
        avatars = db.session.query(User.avatar_url).filter(User.avatar_url.isnot(None)).all()
        for avatar in avatars:
            if avatar[0] and 'uploads/' in avatar[0]:
                referenced_files.add(avatar[0].split('uploads/')[-1])
        
        # 战队Logo
        from models.match import Team
        logos = db.session.query(Team.logo_url).filter(Team.logo_url.isnot(None)).all()
        for logo in logos:
            if logo[0] and 'uploads/' in logo[0]:
                referenced_files.add(logo[0].split('uploads/')[-1])
        
        # 扫描上传目录中的所有文件
        deleted_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, upload_folder)
                
                # 检查文件是否被引用
                if relative_path not in referenced_files:
                    # 检查文件是否超过7天未使用
                    file_mtime = os.path.getmtime(file_path)
                    if datetime.fromtimestamp(file_mtime) < datetime.now() - timedelta(days=7):
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_files.append(relative_path)
                        total_size += file_size
        
        return ApiResponse.success({
            'deletedFiles': len(deleted_files),
            'totalSize': total_size,
            'files': deleted_files[:100]  # 只返回前100个文件名
        }, f'清理完成，删除了 {len(deleted_files)} 个文件')
        
    except Exception as e:
        current_app.logger.error(f"文件清理失败: {e}")
        return ApiResponse.error('文件清理失败', 'CLEANUP_FAILED', 500)
