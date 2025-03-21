import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

class Config:
    """Cấu hình cơ bản cho ứng dụng."""
    
    # Cấu hình bảo mật
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Cấu hình cơ sở dữ liệu
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cấu hình JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 giờ
    
    # Cấu hình bảo mật mật khẩu
    BCRYPT_LOG_ROUNDS = 12
    
    # Cấu hình ghi nhật ký
    AUDIT_LOG_ENABLED = True
    
    # Cấu hình phiên
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 giờ

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển."""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Cấu hình cho môi trường kiểm thử."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Cấu hình cho môi trường sản xuất."""
    
    DEBUG = False
    
    # Trong môi trường sản xuất, SECRET_KEY phải được đặt trong biến môi trường
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Xử lý lỗi qua email hoặc Sentry
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Đảm bảo thư mục logs tồn tại
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        file_handler = RotatingFileHandler('logs/employee_management.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Employee Management System startup')

# Từ điển cấu hình
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
