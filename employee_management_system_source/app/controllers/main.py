from flask import Blueprint

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return {'message': 'Chào mừng đến với Hệ thống Quản lý Nhân viên'}
