# 🔌 MyApp 아두이노 연결 가이드

## 📋 개요

MyApp의 더미 센서 데이터를 실제 아두이노 하드웨어로 교체하는 가이드입니다. 아두이노가 연결되지 않으면 자동으로 시뮬레이션 모드로 동작합니다.

## 🔧 필요한 하드웨어

### 아두이노 구성요소
- **Arduino Mega 2560** (또는 호환 보드)
- **DHT11** - 온도 센서 (DHT22 권장)
- **토양수분 센서** - 아날로그 센서
- **MQ-135** - CO2/공기질 센서 (선택사항)
- **CDS 광센서** - 조도 센서 (선택사항)
- **릴레이 모듈 4채널** - 액추에이터 제어
- **서보모터** - 창문 제어
- **16x2 LCD (I2C)** - 상태 표시 (선택사항)

### 액추에이터
- **팬** (Fan) - 환풍기
- **워터펌프** (Water Pump) - 급수 시스템
- **LED 스트립** - 조명
- **서보모터** - 창문 개폐

## ⚙️ 아두이노 핀 배치

```cpp
// 센서 핀
#define DHTPIN 12              // DHT11 온도센서
const int soilPin = A1;        // 토양수분 센서
const int co2Pin = A2;         // CO2 센서 (선택사항)
const int lightSensorPin = A0; // 조도 센서 (선택사항)

// 액추에이터 핀
const int fanPin = 32;         // 팬 릴레이
const int pumpPin = 31;        // 펌프 릴레이
const int ledPin = 4;          // LED 릴레이
const int servoPin = 9;        // 서보모터 (창문)
```

## 🛠️ 설치 단계

### 1. Python 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

새로 추가된 `pyserial==3.5` 라이브러리가 자동으로 설치됩니다.

### 2. 아두이노 펌웨어 업로드

제공된 `ARduino.md` 파일의 아두이노 코드를 Arduino IDE로 업로드하세요.

### 3. 연결 테스트

```bash
cd backend
python test_arduino_connection.py
```

### 4. 수동 테스트 (선택사항)

```bash
cd backend
python test_arduino_connection.py manual
```

## 📊 센서 매핑

| MyApp 센서 | 아두이노 센서 | 변환 |
|------------|---------------|------|
| `temperature` | DHT11 온도 | 직접 매핑 |
| `humidity` | 계산값 | 온도 기반 추정 |
| `soil` | 토양수분 센서 | 0-1023 → 0-100% |
| `power` | 계산값 | 장치 상태 기반 |

## 🎛️ 액추에이터 매핑

| MyApp 장치 | 아두이노 명령 | 기능 |
|------------|---------------|------|
| `fan` | `MANUAL_FAN_ON/OFF` | 팬 제어 |
| `water` | `MANUAL_PUMP_ON/OFF` | 급수펌프 제어 |
| `light` | `MANUAL_LED_ON/OFF` | LED 조명 제어 |
| `window` | `MANUAL_WINDOW_ON/OFF` | 창문 서보모터 제어 |

## 🔄 동작 모드

### 1. **하드웨어 모드** (아두이노 연결 시)
- 실제 센서에서 온도, 토양수분 데이터 수신
- 습도는 온도 기반 계산값 사용
- 전력은 장치 상태 기반 계산
- 액추에이터 실제 제어

### 2. **시뮬레이션 모드** (아두이노 미연결 시)
- 기존 더미 데이터 사용
- 모든 기능 정상 동작
- 개발/테스트 환경에서 유용

## 📡 API 확장

### 새로 추가된 엔드포인트

```bash
# 아두이노 연결 상태 확인
GET /api/arduino/status

# 아두이노 재연결 시도
POST /api/arduino/reconnect
```

### 응답 예시

```json
{
  "connected": true,
  "port": "/dev/ttyACM0",
  "mode": "하드웨어"
}
```

## 🐛 문제 해결

### 연결 문제
1. **포트 권한 오류**
   ```bash
   sudo chmod 666 /dev/ttyACM0
   # 또는
   sudo usermod -a -G dialout $USER
   ```

2. **포트 찾기**
   ```bash
   ls /dev/tty*
   # Linux: /dev/ttyACM*, /dev/ttyUSB*
   # macOS: /dev/cu.usbmodem*
   # Windows: COM*
   ```

3. **아두이노 재시작**
   - USB 케이블 재연결
   - 아두이노 리셋 버튼 누르기

### 센서 문제
1. **온도 센서 NaN**
   - DHT11 연결 확인
   - 3.3V 전원 확인

2. **토양수분 이상값**
   - 센서 보정 필요
   - 건조/습윤 상태 확인

3. **시리얼 통신 오류**
   - 보드레이트 확인 (9600)
   - 케이블 품질 확인

## 🧪 테스트 시나리오

### 자동 테스트
```bash
python test_arduino_connection.py
```
- 연결 상태 확인
- 센서 데이터 10회 읽기
- 모든 액추에이터 제어 테스트

### 수동 테스트
```bash
python test_arduino_connection.py manual
```
- 실시간 명령어 입력
- 센서 값 실시간 확인
- 개별 장치 제어

## 🔒 보안 고려사항

1. **포트 권한**
   - 필요한 최소 권한만 부여
   - 사용자 그룹 관리

2. **예외 처리**
   - 연결 끊김 자동 감지
   - 시뮬레이션 모드 자동 전환
   - 오류 로깅

## 📈 성능 최적화

1. **데이터 수신**
   - 별도 스레드에서 처리
   - 버퍼 관리
   - 비동기 읽기

2. **응답 시간**
   - 타임아웃 설정 (1초)
   - 연결 상태 캐싱

## 🚀 향후 확장

1. **센서 추가**
   - DHT11에서 습도도 읽기
   - pH 센서 추가
   - 조도 센서 활용

2. **자동 제어**
   - 아두이노 자동 모드 연동
   - 임계값 동적 설정
   - 스케줄 기반 제어

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 아두이노 연결 상태
2. 시리얼 포트 권한
3. 펌웨어 버전
4. 센서 연결 상태

모든 기존 MyApp 기능은 아두이노 연결 여부에 관계없이 정상 동작합니다. 