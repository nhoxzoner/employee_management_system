from app.models.database_schema import User

def register_error_handlers(app):
    """Đăng ký các hàm xử lý lỗi cho ứng dụng."""
    
    @app.errorhandler(404)
    def page_not_found(e):
        return {'error': 'Không tìm thấy trang'}, 404
    
    @app.errorhandler(403)
    def forbidden(e):
        return {'error': 'Không có quyền truy cập'}, 403
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return {'error': 'Lỗi máy chủ nội bộ'}, 500
    
    @app.errorhandler(400)
    def bad_request(e):
        return {'error': 'Yêu cầu không hợp lệ'}, 400
