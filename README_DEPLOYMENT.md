# 🚀 MyApp Raspberry Pi 배포 가이드

이 가이드는 MyApp 프로젝트를 Raspberry Pi 5 (Ubuntu 24.04)에 배포하는 방법을 설명합니다.

## 📋 사전 준비사항

### 1. Raspberry Pi 준비
- **하드웨어**: Raspberry Pi 5
- **OS**: Ubuntu 24.04 LTS (ARM64)
- **네트워크**: Wi-Fi 또는 이더넷 연결
- **저장공간**: 최소 8GB (16GB 권장)

### 2. 필요한 정보
- Raspberry Pi IP 주소
- SSH 사용자명 (기본: ubuntu)
- Google Gemini API 키

## 🔧 배포 과정

### 1단계: 환경 설정 스크립트 준비

현재 서버에서 다음 명령어를 실행하여 스크립트에 실행 권한을 부여합니다:

```bash
chmod +x rpi_setup.sh deploy_to_rpi.sh install_service.sh
```

### 2단계: Raspberry Pi 환경 설정

먼저 Raspberry Pi에 SSH로 접속하여 환경을 설정합니다:

```bash
# RPi에 SSH 접속
ssh ubuntu@[RPi_IP_ADDRESS]

# 환경 설정 스크립트 다운로드 (또는 파일 전송)
wget [스크립트_URL]/rpi_setup.sh
chmod +x rpi_setup.sh
./rpi_setup.sh
```

### 3단계: 프로젝트 배포

현재 서버에서 배포 스크립트를 실행합니다:

```bash
# 배포 스크립트 실행
./deploy_to_rpi.sh [RPi_IP_ADDRESS] [SSH_USER]

# 예시
./deploy_to_rpi.sh 192.168.1.100 ubuntu
```

### 4단계: 환경변수 설정

Raspberry Pi에 SSH로 접속하여 환경변수를 설정합니다:

```bash
# RPi에 접속
ssh ubuntu@[RPi_IP_ADDRESS]

# 환경변수 파일 생성
cp /opt/myapp/env_example.txt /opt/myapp/.env

# 환경변수 편집
nano /opt/myapp/.env
```

필수 설정 항목:
```bash
GEMINI_API_KEY=your_actual_api_key_here
INFLUXDB_PASSWORD=secure_password_here
SECRET_KEY=your_secret_key_here
```

### 5단계: InfluxDB 초기 설정

```bash
# InfluxDB 웹 인터페이스 접속: http://[RPi_IP]:8086
# 초기 설정:
# - Username: admin
# - Password: env_example.txt에서 설정한 비밀번호
# - Organization: myapp_org
# - Bucket: greenhouse_data
```

### 6단계: 서비스 등록 및 시작

```bash
# 서비스 설치 스크립트 실행
cd /opt/myapp
./install_service.sh
```

## 📊 서비스 관리

### 서비스 상태 확인
```bash
# 백엔드 서비스 상태
sudo systemctl status myapp-backend

# 전체 서비스 상태
sudo systemctl status myapp-backend nginx influxdb
```

### 서비스 제어
```bash
# 서비스 시작
sudo systemctl start myapp-backend

# 서비스 중지
sudo systemctl stop myapp-backend

# 서비스 재시작
sudo systemctl restart myapp-backend

# 서비스 활성화 (부팅시 자동 시작)
sudo systemctl enable myapp-backend
```

### 로그 확인
```bash
# 실시간 로그 확인
sudo journalctl -u myapp-backend -f

# 최근 로그 확인
sudo journalctl -u myapp-backend --lines=100

# Nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🌐 접속 및 테스트

### 웹 인터페이스
- **메인 페이지**: `http://[RPi_IP]`
- **API 테스트**: `http://[RPi_IP]/api/status`
- **InfluxDB**: `http://[RPi_IP]:8086`

### API 테스트
```bash
# 상태 확인
curl http://[RPi_IP]/api/status

# 헬스 체크
curl http://[RPi_IP]/health
```

### React Native 앱 연결
앱의 `services/api.js` 파일에서 기본 URL을 수정:
```javascript
const BASE_URL = 'http://[RPi_IP]/api';
```

## 🔒 보안 설정

### 방화벽 설정
```bash
# 현재 상태 확인
sudo ufw status

# 필요한 포트만 허용
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (향후 SSL 적용시)
sudo ufw enable
```

### SSL/HTTPS 설정 (선택사항)
```bash
# Let's Encrypt 인증서 설치
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🔧 문제 해결

### 자주 발생하는 문제

1. **서비스 시작 실패**
   ```bash
   sudo journalctl -u myapp-backend --lines=50
   ```

2. **포트 충돌**
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo lsof -i :8000
   ```

3. **권한 문제**
   ```bash
   sudo chown -R $USER:$USER /opt/myapp
   ```

4. **Python 패키지 오류**
   ```bash
   source ~/myapp_env/bin/activate
   pip install --upgrade pip
   pip install -r /opt/myapp/backend/requirements.txt
   ```

### 성능 최적화

1. **메모리 사용량 모니터링**
   ```bash
   htop
   sudo systemctl status myapp-backend
   ```

2. **로그 로테이션 설정**
   ```bash
   sudo nano /etc/logrotate.d/myapp
   ```

## 📱 모바일 앱 연결

### React Native Expo 앱
1. `services/api.js`에서 서버 IP 변경
2. 앱 재빌드 및 테스트

### 외부 접속 설정
1. 라우터 포트포워딩 설정 (80, 443 포트)
2. 동적 DNS 설정 (선택사항)
3. 방화벽 규칙 확인

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 서비스 로그: `sudo journalctl -u myapp-backend -f`
2. Nginx 로그: `sudo tail -f /var/log/nginx/error.log`
3. 시스템 리소스: `htop`, `df -h` 