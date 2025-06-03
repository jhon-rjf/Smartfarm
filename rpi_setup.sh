#!/bin/bash

# Raspberry Pi 5 Ubuntu 24.04 환경 설정 스크립트
# MyApp 프로젝트 실행을 위한 환경 구성

echo "🍓 Raspberry Pi 5 환경 설정을 시작합니다..."

# 시스템 업데이트
echo "📦 시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y

# Python 3.9+ 및 필수 패키지 설치
echo "🐍 Python 환경 설정 중..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    portaudio19-dev \
    pkg-config \
    git \
    curl \
    wget \
    nginx \
    htop

# Node.js 18+ 설치 (Expo 웹 버전용)
echo "📦 Node.js 설치 중..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# InfluxDB 설치
echo "📊 InfluxDB 설치 중..."
curl -s https://repos.influxdata.com/influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt update
sudo apt install -y influxdb2

# Python 가상환경 생성
echo "🔧 Python 가상환경 설정 중..."
python3 -m venv ~/myapp_env
source ~/myapp_env/bin/activate

# Python 패키지 설치
echo "📚 Python 의존성 설치 중..."
pip install --upgrade pip
pip install flask flask-cors requests python-dotenv pillow numpy \
    influxdb-client urllib3 certifi PyYAML flask-socketio \
    google-generativeai sounddevice websockets gunicorn

# 서비스 사용자 생성
echo "👤 서비스 사용자 생성 중..."
sudo useradd -r -s /bin/false myapp || echo "사용자 이미 존재"

# 프로젝트 디렉토리 설정
echo "📁 프로젝트 디렉토리 설정 중..."
sudo mkdir -p /opt/myapp
sudo chown $USER:$USER /opt/myapp

# 방화벽 설정
echo "🔥 방화벽 설정 중..."
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 8000  # Flask 백엔드
sudo ufw allow 8086  # InfluxDB
sudo ufw --force enable

# InfluxDB 서비스 시작
echo "🚀 InfluxDB 서비스 시작 중..."
sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "✅ 환경 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 프로젝트 파일을 /opt/myapp 으로 복사"
echo "2. 환경변수 설정: sudo nano /opt/myapp/.env"
echo "3. 서비스 등록 및 시작"
echo ""
echo "가상환경 활성화: source ~/myapp_env/bin/activate" 