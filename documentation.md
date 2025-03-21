# Tài liệu Ứng dụng Quản lý Nhân viên

## Giới thiệu

Ứng dụng Quản lý Nhân viên là một hệ thống quản lý nhân sự toàn diện được phát triển bằng Python và Flask. Ứng dụng cung cấp các chức năng quản lý người dùng, nhân viên, phòng ban với hệ thống phân quyền chi tiết và ghi nhật ký hoạt động.

## Kiến trúc hệ thống

Ứng dụng được xây dựng theo mô hình MVC (Model-View-Controller) với các thành phần chính:

1. **Models**: Định nghĩa cấu trúc dữ liệu và quan hệ giữa các đối tượng
2. **Controllers**: Xử lý các yêu cầu từ người dùng và tương tác với Models
3. **Services**: Chứa logic nghiệp vụ của ứng dụng
4. **Utils**: Các tiện ích và công cụ hỗ trợ

### Công nghệ sử dụng

- **Backend**: Python, Flask
- **Database**: SQLite (có thể mở rộng sang các CSDL khác)
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login, JWT
- **Migration**: Flask-Migrate

## Cấu trúc dự án

```
employee_management_system/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   └── auth_utils.py
│   ├── controllers/
│   │   ├── audit.py
│   │   ├── department.py
│   │   ├── employee.py
│   │   ├── main.py
│   │   ├── permission.py
│   │   ├── role.py
│   │   └── user.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database_schema.py
│   │   └── init_db.py
│   ├── services/
│   │   ├── department_service.py
│   │   ├── employee_service.py
│   │   └── user_service.py
│   ├── static/
│   ├── templates/
│   ├── utils/
│   │   ├── audit_logger.py
│   │   ├── error_handlers.py
│   │   └── rbac.py
│   └── __init__.py
├── config.py
├── requirements.txt
└── run.py
```

## Mô hình dữ liệu

### User (Người dùng)
- Quản lý thông tin đăng nhập và xác thực
- Liên kết với Employee (nếu có)
- Có nhiều Role (vai trò)

### Role (Vai trò)
- Định nghĩa các vai trò trong hệ thống (Admin, Manager, Employee, HR, Accounting)
- Có nhiều Permission (quyền)

### Permission (Quyền)
- Định nghĩa các quyền chi tiết trên từng tài nguyên
- Gắn với các Role

### Department (Phòng ban)
- Quản lý thông tin phòng ban
- Có một Manager (trưởng phòng)
- Có nhiều Employee (nhân viên)

### Employee (Nhân viên)
- Quản lý thông tin nhân viên (mã số, tên, ngày sinh, email, lương, mã số thuế)
- Thuộc về một Department
- Có thể là Manager của một hoặc nhiều Department

### AuditLog (Nhật ký)
- Ghi lại các hoạt động trong hệ thống
- Liên kết với User thực hiện hành động

## Chính sách phân quyền

Ứng dụng triển khai hệ thống kiểm soát truy cập dựa trên vai trò (RBAC) với các chính sách:

1. **Nhân viên thông thường**:
   - Chỉ xem được thông tin (trừ lương) của nhân viên cùng phòng ban
   - Không có quyền chỉnh sửa thông tin

2. **Trưởng phòng**:
   - Xem được mọi thông tin của nhân viên trong phòng, kể cả lương
   - Không có quyền chỉnh sửa thông tin

3. **Nhân viên phòng nhân sự (HR)**:
   - Xem, chỉnh sửa thông tin của nhân viên khác phòng
   - Chỉ xem (không sửa) thông tin nhân viên cùng phòng HR

4. **Trưởng phòng nhân sự (HR Manager)**:
   - Xem, chỉnh sửa thông tin của mọi nhân viên
   - Giám sát việc chỉnh sửa thông tin của nhân viên phòng HR

5. **Nhân viên phòng kế toán (Accounting)**:
   - Xem được mã số, lương và mã số thuế của mọi nhân viên
   - Không có quyền chỉnh sửa thông tin

6. **Quản trị viên (Admin)**:
   - Có tất cả quyền trong hệ thống
   - Quản lý người dùng, vai trò, phân quyền

## API Endpoints

### Authentication

- `POST /auth/login`: Đăng nhập
- `POST /auth/logout`: Đăng xuất
- `GET /auth/profile`: Xem thông tin cá nhân
- `PUT /auth/change-password`: Thay đổi mật khẩu
- `POST /auth/token`: Lấy JWT token
- `POST /auth/refresh-token`: Làm mới JWT token

### User Management

- `GET /users/`: Lấy danh sách người dùng
- `GET /users/<id>`: Lấy thông tin người dùng
- `POST /users/`: Tạo người dùng mới
- `PUT /users/<id>`: Cập nhật thông tin người dùng
- `DELETE /users/<id>`: Xóa người dùng
- `GET /users/<id>/roles`: Lấy danh sách vai trò của người dùng
- `POST /users/<id>/roles`: Gán vai trò cho người dùng
- `DELETE /users/<id>/roles/<role_id>`: Thu hồi vai trò từ người dùng

### Role Management

- `GET /roles/`: Lấy danh sách vai trò
- `GET /roles/<id>`: Lấy thông tin vai trò
- `POST /roles/`: Tạo vai trò mới
- `PUT /roles/<id>`: Cập nhật thông tin vai trò
- `DELETE /roles/<id>`: Xóa vai trò
- `GET /roles/<id>/permissions`: Lấy danh sách quyền của vai trò
- `GET /roles/permissions`: Lấy danh sách tất cả quyền

### Permission Management

- `GET /permissions/`: Lấy danh sách quyền
- `GET /permissions/<id>`: Lấy thông tin quyền
- `POST /permissions/`: Tạo quyền mới
- `PUT /permissions/<id>`: Cập nhật thông tin quyền
- `DELETE /permissions/<id>`: Xóa quyền
- `GET /permissions/<id>/roles`: Lấy danh sách vai trò có quyền này

### Employee Management

- `GET /employees/`: Lấy danh sách nhân viên (theo quyền)
- `GET /employees/<id>`: Lấy thông tin nhân viên
- `POST /employees/`: Tạo nhân viên mới
- `PUT /employees/<id>`: Cập nhật thông tin nhân viên
- `DELETE /employees/<id>`: Xóa nhân viên
- `GET /employees/department/<id>`: Lấy danh sách nhân viên theo phòng ban
- `GET /employees/search`: Tìm kiếm nhân viên

### Department Management

- `GET /departments/`: Lấy danh sách phòng ban
- `GET /departments/<id>`: Lấy thông tin phòng ban
- `POST /departments/`: Tạo phòng ban mới
- `PUT /departments/<id>`: Cập nhật thông tin phòng ban
- `DELETE /departments/<id>`: Xóa phòng ban
- `PUT /departments/<id>/manager`: Thiết lập trưởng phòng
- `GET /departments/<id>/employees`: Lấy danh sách nhân viên của phòng ban
- `GET /departments/statistics`: Lấy thống kê về các phòng ban

### Audit Logging

- `GET /audit/`: Lấy danh sách nhật ký hệ thống
- `GET /audit/actions`: Lấy danh sách các loại hành động
- `GET /audit/resources`: Lấy danh sách các loại tài nguyên
- `GET /audit/users`: Lấy danh sách người dùng có nhật ký
- `GET /audit/statistics`: Lấy thống kê về nhật ký hệ thống

## Cài đặt và chạy ứng dụng

### Yêu cầu hệ thống

- Python 3.8+
- Pip

### Cài đặt

1. Clone repository:
```
git clone <repository-url>
cd employee_management_system
```

2. Cài đặt các thư viện:
```
pip install -r requirements.txt
```

3. Thiết lập biến môi trường:
```
cp .env.example .env
```

4. Chạy ứng dụng:
```
python run.py
```

Ứng dụng sẽ chạy trên địa chỉ http://0.0.0.0:5000

### Tài khoản mặc định

- **Admin**: username=admin, password=admin123
- **Trưởng phòng HR**: username=hr_manager, password=password
- **Nhân viên HR**: username=hr_employee1, password=password
- **Trưởng phòng kế toán**: username=accounting_manager, password=password
- **Nhân viên kế toán**: username=accounting_employee1, password=password

## Bảo mật

Ứng dụng triển khai các cơ chế bảo mật:

1. **Xác thực**:
   - Mật khẩu được mã hóa bằng bcrypt
   - Hỗ trợ JWT token cho API
   - Quản lý phiên với Flask-Login

2. **Phân quyền**:
   - Kiểm soát truy cập dựa trên vai trò (RBAC)
   - Kiểm tra quyền chi tiết trên từng tài nguyên

3. **Ghi nhật ký**:
   - Ghi lại tất cả các hoạt động quan trọng
   - Lưu thông tin người dùng, hành động, tài nguyên, IP

4. **Bảo vệ dữ liệu**:
   - Kiểm tra tính hợp lệ của dữ liệu đầu vào
   - Xử lý lỗi an toàn

## Mở rộng

Ứng dụng có thể được mở rộng với các tính năng:

1. **Giao diện người dùng**: Thêm frontend sử dụng React, Vue hoặc Angular
2. **Cơ sở dữ liệu**: Chuyển từ SQLite sang MySQL, PostgreSQL
3. **Xác thực**: Tích hợp OAuth, xác thực hai yếu tố
4. **Báo cáo**: Thêm chức năng tạo báo cáo, biểu đồ thống kê
5. **Thông báo**: Email, tin nhắn thông báo

## Kết luận

Ứng dụng Quản lý Nhân viên cung cấp giải pháp toàn diện cho việc quản lý nhân sự với các tính năng bảo mật cao cấp, phân quyền chi tiết và ghi nhật ký đầy đủ. Hệ thống được thiết kế để dễ dàng mở rộng và tùy chỉnh theo nhu cầu cụ thể của tổ chức.
