from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.database_schema import User, db
from app.utils.audit_logger import log_action
from app.auth.auth_utils import authenticate_user, generate_token

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    """Xử lý đăng nhập người dùng."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Kiểm tra thông tin đăng nhập
    user = authenticate_user(username, password)
    
    if not user:
        log_action('FAILED_LOGIN', 'auth', None, f"Đăng nhập thất bại với tên đăng nhập: {username}")
        return jsonify({'error': 'Tên đăng nhập hoặc mật khẩu không đúng'}), 401
    
    # Đăng nhập người dùng với Flask-Login
    login_user(user)
    
    # Tạo JWT token
    token = generate_token(user)
    
    log_action('LOGIN', 'auth', user.id, f"Đăng nhập thành công: {username}")
    
    return jsonify({
        'message': 'Đăng nhập thành công',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'roles': [role.role_type.value for role in user.roles]
        }
    })

@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """Xử lý đăng xuất người dùng."""
    user_id = current_user.id
    username = current_user.username
    
    logout_user()
    log_action('LOGOUT', 'auth', user_id, f"Đăng xuất: {username}")
    
    return jsonify({'message': 'Đăng xuất thành công'})

@auth.route('/profile', methods=['GET'])
@login_required
def profile():
    """Lấy thông tin hồ sơ người dùng hiện tại."""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'roles': [{'id': role.id, 'name': role.name, 'role_type': role.role_type.value} for role in current_user.roles],
        'employee': {
            'id': current_user.employee.id,
            'full_name': current_user.employee.full_name,
            'department': current_user.employee.department.name
        } if current_user.employee else None
    })

@auth.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Thay đổi mật khẩu người dùng hiện tại."""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    # Kiểm tra mật khẩu hiện tại
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'error': 'Mật khẩu hiện tại không đúng'}), 400
    
    # Cập nhật mật khẩu mới
    from werkzeug.security import generate_password_hash
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    log_action('UPDATE', 'user', current_user.id, "Thay đổi mật khẩu")
    
    return jsonify({'message': 'Thay đổi mật khẩu thành công'})

@auth.route('/token/refresh', methods=['POST'])
@login_required
def refresh_token():
    """Làm mới token JWT."""
    # Tạo token mới
    token = generate_token(current_user)
    
    return jsonify({
        'message': 'Làm mới token thành công',
        'token': token
    })
