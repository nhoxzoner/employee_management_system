from flask import request, jsonify, current_app
from flask_login import login_user, current_user
from werkzeug.security import check_password_hash
from functools import wraps
import jwt
from datetime import datetime, timedelta
from app.models.database_schema import User, db
from app.utils.audit_logger import log_action

def authenticate_user(username, password):
    """
    Xác thực người dùng bằng tên đăng nhập và mật khẩu.
    
    Args:
        username: Tên đăng nhập
        password: Mật khẩu
        
    Returns:
        User object nếu xác thực thành công, None nếu thất bại
    """
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return None
    
    if not user.is_active:
        return None
    
    return user

def generate_token(user):
    """
    Tạo JWT token cho người dùng.
    
    Args:
        user: User object
        
    Returns:
        JWT token
    """
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
        'iat': datetime.utcnow(),
        'roles': [role.role_type.value for role in user.roles]
    }
    
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

def token_required(f):
    """Decorator để kiểm tra JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Lấy token từ header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token không được cung cấp'}), 401
        
        try:
            # Giải mã token
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            
            # Lấy thông tin người dùng từ token
            user_id = payload['user_id']
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'Người dùng không tồn tại'}), 401
            
            if not user.is_active:
                return jsonify({'error': 'Tài khoản đã bị vô hiệu hóa'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token đã hết hạn'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token không hợp lệ'}), 401
        
        # Gán thông tin người dùng vào request
        request.user = user
        
        return f(*args, **kwargs)
    
    return decorated

def load_user_from_request(request):
    """
    Tải thông tin người dùng từ request cho Flask-Login.
    
    Args:
        request: Flask request object
        
    Returns:
        User object nếu xác thực thành công, None nếu thất bại
    """
    # Kiểm tra xác thực qua session (Flask-Login)
    if current_user.is_authenticated:
        return current_user
    
    # Kiểm tra xác thực qua JWT token
    token = None
    
    # Lấy token từ header Authorization
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    if not token:
        return None
    
    try:
        # Giải mã token
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        
        # Lấy thông tin người dùng từ token
        user_id = payload['user_id']
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def init_auth(app, login_manager):
    """
    Khởi tạo hệ thống xác thực.
    
    Args:
        app: Flask app
        login_manager: Flask-Login LoginManager
    """
    # Thiết lập user loader cho Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Thiết lập request loader cho Flask-Login
    @login_manager.request_loader
    def load_user_from_request_loader(request):
        return load_user_from_request(request)
