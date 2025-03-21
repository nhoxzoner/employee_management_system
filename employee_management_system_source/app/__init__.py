from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from config import config
from app.models.database_schema import db, User
from app.auth.auth_utils import init_auth

# Khởi tạo các extension
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'info'

migrate = Migrate()
csrf = CSRFProtect()

def create_app(config_name='default'):
    """Tạo và cấu hình ứng dụng Flask."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Khởi tạo các extension với app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Khởi tạo hệ thống xác thực
    init_auth(app, login_manager)
    
    # Đăng ký các blueprint
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.controllers.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.controllers.user import user_routes as user_blueprint
    app.register_blueprint(user_blueprint, url_prefix='/users')
    
    from app.controllers.role import role_routes as role_blueprint
    app.register_blueprint(role_blueprint, url_prefix='/roles')
    
    from app.controllers.permission import permission_routes as permission_blueprint
    app.register_blueprint(permission_blueprint, url_prefix='/permissions')
    
    from app.controllers.employee import employee_routes as employee_blueprint
    app.register_blueprint(employee_blueprint, url_prefix='/employees')
    
    from app.controllers.department import department_routes as department_blueprint
    app.register_blueprint(department_blueprint, url_prefix='/departments')
    
    from app.controllers.audit import audit_routes as audit_blueprint
    app.register_blueprint(audit_blueprint, url_prefix='/audit')
    
    # Đăng ký hàm xử lý lỗi
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Khởi tạo cơ sở dữ liệu với dữ liệu ban đầu
    with app.app_context():
        from app.models.init_db import init_db
        init_db()
    
    return app
