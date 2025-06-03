# 스마트 온실 시스템 인터페이스 문서

## 1. 장치 제어 인터페이스

### 1.1 디바이스 제어 API

```javascript
controlDevice(device, status)
```

**매개변수:**
- `device` (string): 제어할 장치의 식별자 ('fan', 'water', 'light', 'window')
- `status` (boolean): 장치 상태 (true: 켜기, false: 끄기)

**리턴값:**
- Promise<Object>: 장치 제어 결과 및 전체 장치 상태 객체
  ```json
  {
    "success": true,
    "devices": {
      "fan": false,
      "water": true,
      "light": false,
      "window": false
    }
  }
  ```

### 1.2 하드웨어 연결 방식

| 장치 ID | 제어 방식 | 연결 핀/포트 | 제어 신호 타입 |
|---------|-----------|--------------|---------------|
| fan | GPIO | GPIO 18 | 디지털 (0/1) |
| water | PWM 펌프 | GPIO 12 | PWM (0~255) |
| light | 릴레이 모듈 | GPIO 23 | 디지털 (0/1) |
| window | 서보 모터 | GPIO 25 | PWM (0~180) |

### 1.3 제어 명령 채널

**HTTP 요청:**
- URL: `http://gknu-comeng.kro.kr:5001/api/control`
- 메소드: POST
- 본문: `{ "device": "fan", "status": true }`

## 2. 센서 데이터 인터페이스

### 2.1 센서 데이터 API

```javascript
fetchStatus()
```

**리턴값:**
- Promise<Object>: 현재 센서 측정값 및 장치 상태
  ```json
  {
    "temperature": 23.5,     // 단위: °C
    "humidity": 58.0,        // 단위: %
    "power": 135.0,          // 단위: W
    "soil": 42.0,            // 단위: %
    "devices": {
      "fan": false,
      "water": false,
      "light": false,
      "window": false
    },
    "timestamp": "2023-05-15T08:30:45.123Z"
  }
  ```

### 2.2 센서 하드웨어 연결 방식

| 센서 타입 | 모델명 | 연결 핀/포트 | 데이터 형식 | 측정 범위 | 정확도 |
|-----------|--------|--------------|------------|-----------|--------|
| 온도 센서 | DHT22 | GPIO 4 | 디지털 | -40~80°C | ±0.5°C |
| 습도 센서 | DHT22 | GPIO 4 | 디지털 | 0~100% | ±2% |
| 토양 습도 | 저항형 | ADC 채널 0 | 아날로그 | 0~100% | ±5% |
| 전력 측정 | ACS712 | ADC 채널 1 | 아날로그 | 0~500W | ±1% |

### 2.3 데이터 폴링 주기

- 센서 데이터 갱신 주기: 5초
- 클라이언트 앱 데이터 요청 주기: 30초

## 3. 챗봇 명령 인터페이스

### 3.1 챗봇을 통한 장치 제어

챗봇은 사용자의 자연어 요청을 처리하여 장치를 제어할 수 있습니다. 백엔드에서는 다음과 같은 태그를 응답에 포함시켜 특정 액션을 트리거합니다:

| 액션 태그 | 설명 | 실행 명령 |
|-----------|------|-----------|
| [ACTION_FAN_ON] | 환풍기 켜기 | controlDevice('fan', true) |
| [ACTION_FAN_OFF] | 환풍기 끄기 | controlDevice('fan', false) |
| [ACTION_WATER_ON] | 급수 시작 | controlDevice('water', true) |
| [ACTION_WATER_OFF] | 급수 중단 | controlDevice('water', false) |
| [ACTION_LIGHT_ON] | 조명 켜기 | controlDevice('light', true) |
| [ACTION_LIGHT_OFF] | 조명 끄기 | controlDevice('light', false) |
| [ACTION_WINDOW_OPEN] | 창문 열기 | controlDevice('window', true) |
| [ACTION_WINDOW_CLOSE] | 창문 닫기 | controlDevice('window', false) |

### 3.2 사용자 명령어 예시

사용자는 다음과 같은 자연어 명령을 사용할 수 있습니다:

| 명령어 예시 | 액션 |
|------------|------|
| "불 켜줘", "조명 켜주세요" | 조명 켜기 |
| "불 꺼줘", "조명 꺼주세요" | 조명 끄기 |
| "팬 켜줘", "환풍기 켜주세요" | 팬 켜기 |
| "팬 꺼줘", "환풍기 꺼주세요" | 팬 끄기 |
| "물 줘", "급수 시작해줘" | 급수 시작 |
| "물 그만 줘", "급수 중단해줘" | 급수 중단 |
| "창문 열어줘" | 창문 열기 |
| "창문 닫아줘" | 창문 닫기 |

## 4. 실시간 데이터 구독 인터페이스

```javascript
subscribeToStatusUpdates(callback)
```

**매개변수:**
- `callback` (Function): 상태 업데이트 시 호출될 콜백 함수

**리턴값:**
- Function: 구독 취소 함수

앱 컴포넌트에서는 다음과 같이 실시간 업데이트를 구독할 수 있습니다:

```javascript
useEffect(() => {
  const unsubscribe = subscribeToStatusUpdates((data) => {
    if (data && data.devices) {
      setDevices(data.devices);
    }
  });
  
  return () => {
    unsubscribe(); // 컴포넌트 언마운트 시 구독 취소
  };
}, []);
```

## 5. 시스템 확장 가이드라인

### 5.1 새로운 센서 추가하기

1. 백엔드 서버에 센서 연결 및 데이터 수집 코드 추가
2. API 응답 포맷에 새 센서 데이터 필드 추가
3. `fetchStatus()` 함수의 반환 형식 업데이트
4. UI 컴포넌트에 새 센서 데이터 표시 추가

### 5.2 새로운 제어 장치 추가하기

1. 백엔드 서버에 장치 제어 인터페이스 추가
2. `devices` 객체에 새 장치 상태 필드 추가
3. 챗봇 명령어 인식 패턴에 새 장치 명령 추가
4. UI 컴포넌트에 제어 버튼 추가

## 6. 진단 및 문제해결

- 하드웨어 문제 시 서버 로그 확인: `/var/log/greenhouse-system.log`
- 센서 데이터 수집 오류: 기본값 대체 및 오류 알림
- 연결 실패 시 재시도 메커니즘: 최대 3회, 1초 간격
- 인증 오류 발생 시: API 키 재설정 필요 