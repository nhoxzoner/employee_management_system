# Hướng dẫn triển khai ứng dụng

## Cấu trúc dự án
Dự án bao gồm hai phần chính:
1. **Backend API** - Ứng dụng Flask Python
2. **Frontend** - Ứng dụng Next.js

## Yêu cầu hệ thống
- Python 3.10+
- Node.js 14+
- npm hoặc yarn

## Triển khai Backend

### Cài đặt dependencies
```bash
cd /path/to/employee_management_system
pip install -r requirements.txt
```

### Cấu hình môi trường
Tạo file `.env` với nội dung:
```
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_APP=run.py
FLASK_ENV=production
DATABASE_URL=sqlite:///app.db
```

### Khởi tạo cơ sở dữ liệu
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Chạy ứng dụng backend
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Triển khai Frontend

### Cài đặt dependencies
```bash
cd /path/to/employee_management_system/frontend-app
npm install
```

### Build ứng dụng
```bash
npm run build
```

### Triển khai static files
Sau khi build, các file static sẽ được tạo trong thư mục `out`. Bạn có thể triển khai các file này lên bất kỳ web server nào như Nginx, Apache, hoặc dịch vụ hosting static như Netlify, Vercel, GitHub Pages.

## Triển khai tích hợp

### Cấu hình Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/employee_management_system/frontend-app/out;
        try_files $uri $uri.html $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Sử dụng Docker (tùy chọn)
Bạn có thể đóng gói ứng dụng trong Docker containers để dễ dàng triển khai.

#### Dockerfile cho Backend
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

#### Dockerfile cho Frontend
```dockerfile
FROM node:14-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/out /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## Kiểm tra triển khai
Sau khi triển khai, hãy kiểm tra các chức năng sau:
1. Đăng nhập/đăng xuất
2. Quản lý người dùng
3. Quản lý nhân viên
4. Quản lý phòng ban
5. Xem nhật ký hệ thống
6. Kiểm tra phân quyền theo chính sách công ty

## Bảo trì
- Sao lưu cơ sở dữ liệu định kỳ
- Cập nhật dependencies khi có phiên bản mới
- Theo dõi nhật ký hệ thống để phát hiện vấn đề
