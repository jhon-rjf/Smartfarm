#!/bin/bash

# MyApp 시스템 서비스 등록 스크립트
# RPi에서 실행하여 백엔드를 시스템 서비스로 등록

PROJECT_DIR="/opt/myapp"
SERVICE_NAME="myapp-backend"
USER_NAME=$(whoami)

echo "🔧 MyApp 백엔드를 시스템 서비스로 등록합니다..."

# systemd 서비스 파일 생성
echo "📝 서비스 파일 생성 중..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=MyApp Flask Backend Server
Documentation=https://github.com/your-repo/myapp
After=network.target influxdb.service
Wants=influxdb.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=/home/$USER_NAME/myapp_env/bin
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=/home/$USER_NAME/myapp_env/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# 보안 설정
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_DIR

# 로그 설정
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp-backend

[Install]
WantedBy=multi-user.target
EOF

# Nginx 설정 파일 생성
echo "🌐 Nginx 설정 파일 생성 중..."
sudo tee /etc/nginx/sites-available/myapp > /dev/null << EOF
server {
    listen 80;
    server_name _;
    
    # API 프록시
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # CORS 헤더 추가
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
        
        # OPTIONS 요청 처리
        if (\$request_method = 'OPTIONS') {
            return 204;
        }
    }
    
    # 정적 파일 (웹 앱)
    location / {
        root $PROJECT_DIR/web;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
    
    # 헬스 체크
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Nginx 사이트 활성화
echo "🔗 Nginx 사이트 활성화 중..."
sudo ln -sf /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 로그 디렉토리 생성
echo "📋 로그 디렉토리 생성 중..."
sudo mkdir -p /var/log/myapp
sudo chown $USER_NAME:$USER_NAME /var/log/myapp

# 서비스 등록 및 시작
echo "🚀 서비스 등록 및 시작 중..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl enable nginx
sudo systemctl enable influxdb

# Nginx 설정 테스트
echo "✅ Nginx 설정 테스트 중..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 서비스 시작 중..."
    sudo systemctl restart influxdb
    sudo systemctl restart $SERVICE_NAME
    sudo systemctl restart nginx
    
    echo ""
    echo "✅ 서비스 등록이 완료되었습니다!"
    echo ""
    echo "📊 서비스 상태 확인:"
    echo "  sudo systemctl status $SERVICE_NAME"
    echo "  sudo systemctl status nginx"
    echo "  sudo systemctl status influxdb"
    echo ""
    echo "📋 로그 확인:"
    echo "  sudo journalctl -u $SERVICE_NAME -f"
    echo "  sudo tail -f /var/log/nginx/access.log"
    echo ""
    echo "🌐 웹 접속: http://$(hostname -I | awk '{print $1}')"
    echo "🔧 API 테스트: curl http://localhost/api/status"
else
    echo "❌ Nginx 설정에 오류가 있습니다. 확인 후 다시 시도하세요."
    exit 1
fi 