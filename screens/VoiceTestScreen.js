import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ImageBackground,
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { fetchStatus, controlDevice, subscribeToStatusUpdates, setAutoMode as setGlobalAutoMode, getAutoMode, subscribeToAutoModeUpdates, getAutoControlSettings, updateAutoControlSettings, subscribeToAutoControlSettings } from '../services/api';

const { width, height } = Dimensions.get('window');

// 화면 크기에 비례한 크기 계산 함수 (글자도 반응형으로)
const scale = (size) => (width / 320) * size;
const verticalScale = (size) => (height / 568) * size;
const moderateScale = (size, factor = 0.5) => size + (scale(size) - size) * factor;

const SmartFarmScreen = ({ navigation, route }) => {
  const [currentPage, setCurrentPage] = useState('main'); // 'main', 'status', 'control', 'settings'
  
  // 실제 센서 데이터를 위한 상태
  const [sensorData, setSensorData] = useState({
    temperature: 25,
    humidity: 61,
    power: 144,
    soil: 46,
    co2: 410,
  });

  // 실제 기기 상태를 위한 상태
  const [deviceStatus, setDeviceStatus] = useState({
    fan: false,
    water: false,
    light: false,
    window: false,
  });

  // 자동모드 상태 추가
  const [autoMode, setAutoMode] = useState(false);

  // 자동제어 설정 상태 추가
  const [autoSettings, setAutoSettings] = useState({
    light: { enabled: true, sensor: 'light', condition: 'above', threshold: 800, action: 'on' },
    fan: { enabled: true, sensor: 'co2', condition: 'above', threshold: 450, action: 'on' },
    water: { enabled: true, sensor: 'soil', condition: 'below', threshold: 40, action: 'on' },
    window: { enabled: true, sensor: 'temperature', condition: 'above', threshold: 25, action: 'on' }
  });

  const [isLoading, setIsLoading] = useState(true);

  // 컴포넌트 마운트 시 API 연동 설정
  useEffect(() => {
    loadInitialData();

    // 자동모드 초기 상태 설정
    setAutoMode(getAutoMode());

    // 실시간 상태 업데이트 구독
    const unsubscribe = subscribeToStatusUpdates((data) => {
      if (data) {
        // 센서 데이터 업데이트
        if (data.temperature !== undefined) setSensorData(prev => ({ ...prev, temperature: data.temperature }));
        if (data.humidity !== undefined) setSensorData(prev => ({ ...prev, humidity: data.humidity }));
        if (data.power !== undefined) setSensorData(prev => ({ ...prev, power: data.power }));
        if (data.soil !== undefined) setSensorData(prev => ({ ...prev, soil: data.soil }));
        if (data.light !== undefined) setSensorData(prev => ({ ...prev, light: data.light }));
        
        // 기기 상태 업데이트
        if (data.devices) {
          setDeviceStatus(data.devices);
        }
      }
    });

    // 자동모드 상태 구독
    const unsubscribeAutoMode = subscribeToAutoModeUpdates((enabled) => {
      setAutoMode(enabled);
    });

    // 자동제어 설정 구독
    const unsubscribeAutoSettings = subscribeToAutoControlSettings((settings) => {
      setAutoSettings(settings);
    });

    return () => {
      unsubscribe();
      unsubscribeAutoMode();
      unsubscribeAutoSettings();
    };
  }, []);

  // 초기 데이터 로드
  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      console.log('[VoiceTestScreen] 초기 데이터 로드 중...');
      const status = await fetchStatus();
      console.log('[VoiceTestScreen] 수신된 상태 데이터:', status);
      
      if (status) {
        // 센서 데이터 설정
        setSensorData({
          temperature: status.temperature || 25,
          humidity: status.humidity || 61,
          power: status.power || 144,
          soil: status.soil || 46,
          co2: status.co2 || 410,
          light: status.light || 50,
        });
        
        // 기기 상태 설정 (백엔드 기본값: 모두 false)
        const deviceState = status.devices || {
          fan: false,
          water: false,
          light: false,
          window: false,
        };
        setDeviceStatus(deviceState);
        console.log('[VoiceTestScreen] 장치 상태 설정 완료:', deviceState);
      } else {
        console.warn('[VoiceTestScreen] 상태 데이터가 없어 기본값 사용');
        // 백엔드 기본값으로 설정
        setDeviceStatus({
          fan: false,
          water: false,
          light: false,
          window: false,
        });
      }
    } catch (error) {
      console.error('[VoiceTestScreen] 초기 데이터 로드 오류:', error);
      // 오류 시에도 백엔드 기본값으로 설정
      setDeviceStatus({
        fan: false,
        water: false,
        light: false,
        window: false,
      });
      Alert.alert('오류', '데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const checkSensorData = (type) => {
    const value = sensorData[type];
    let status = '';
    let unit = '';
    let title = '';
    
    switch (type) {
      case 'temperature':
        title = '온도';
        unit = '°C';
        status = value >= 20 && value <= 26 ? '😊 정상' : '😰 주의';
        break;
      case 'humidity':
        title = '습도';
        unit = '%';
        status = value >= 50 && value <= 70 ? '😊 정상' : '😰 주의';
        break;
      case 'power':
        title = '전력사용량';
        unit = 'W';
        status = value <= 150 ? '😊 정상' : '⚠️ 높음';
        break;
      case 'soil':
        title = '토양습도';
        unit = '%';
        status = value >= 40 && value <= 60 ? '😊 정상' : '😰 주의';
        break;
      case 'co2':
        title = '공기질';
        unit = 'ppm';
        status = value >= 350 && value <= 450 ? '😊 정상' : '😰 주의';
        break;
      case 'light':
        title = '조도';
        unit = '';
        status = value <= 500 ? '😊 밝음' : '😰 어두움';
        break;
    }
    
    Alert.alert(
      `${title} 정보`,
      `현재 값: ${value}${unit}\n상태: ${status}\n\n💡 더 자세한 정보가 필요하시면 챗봇에게 문의하세요!`,
      [
        { text: '확인' },
        { 
          text: '챗봇 문의', 
          onPress: () => navigation.navigate('ElderlyChatScreen')
        }
      ]
    );
  };

  // 자동모드 토글 함수
  const toggleAutoMode = () => {
    const newAutoMode = !autoMode;
    setGlobalAutoMode(newAutoMode); // 전역 상태 업데이트
    Alert.alert(
      '자동모드',
      `자동모드가 ${newAutoMode ? '켜졌습니다' : '꺼졌습니다'}.\n${newAutoMode ? '센서 조건에 따라 자동으로 기기가 제어됩니다.' : '수동으로만 기기를 제어할 수 있습니다.'}`,
      [{ text: '확인' }]
    );
  };

  // 실제 기기 제어 함수
  const controlDeviceAction = async (device, actionName) => {
    try {
      Alert.alert(
        '기기 제어',
        `${actionName}을 실행하시겠습니까?`,
        [
          { text: '취소', style: 'cancel' },
          { 
            text: '실행',
            onPress: async () => {
              try {
                // 현재 기기 상태의 반대로 제어
                const newStatus = !deviceStatus[device];
                
                // 자동모드가 켜져있고 해당 기기의 개별 자동제어도 켜져있을 때만 자동모드 해제
                if (autoMode && autoSettings[device] && autoSettings[device].enabled) {
                  setGlobalAutoMode(false);
                  Alert.alert(
                    '자동모드 해제',
                    `${device === 'light' ? '조명' : device === 'fan' ? '환풍기' : device === 'water' ? '물주기' : '창문'} 자동제어가 켜져있어서 수동 제어 시 자동모드가 해제되었습니다.`,
                    [{ text: '확인' }],
                    { cancelable: true }
                  );
                }
                
                // UI 즉시 반영
                setDeviceStatus(prev => ({ ...prev, [device]: newStatus }));
                
                // API 호출
                const response = await controlDevice(device, newStatus);
                
                if (response && response.devices) {
                  setDeviceStatus(response.devices);
                  Alert.alert('완료', `${actionName}이 완료되었습니다.`);
                } else if (response && response.success) {
                  Alert.alert('완료', `${actionName}이 완료되었습니다.`);
                } else {
                  // 실패 시 원래 상태로 복원
                  setDeviceStatus(prev => ({ ...prev, [device]: !newStatus }));
                  Alert.alert('오류', '기기 제어에 실패했습니다.');
                }
              } catch (error) {
                console.error('기기 제어 오류:', error);
                // 오류 시 원래 상태로 복원
                setDeviceStatus(prev => ({ ...prev, [device]: !deviceStatus[device] }));
                Alert.alert('오류', '기기 제어 중 오류가 발생했습니다.');
              }
            }
          }
        ]
      );
    } catch (error) {
      console.error('기기 제어 함수 오류:', error);
    }
  };

  const emergencyStop = () => {
    Alert.alert(
      '긴급 정지',
      '모든 기기를 정지하시겠습니까?',
      [
        { text: '취소', style: 'cancel' },
        { 
          text: '정지',
          style: 'destructive',
          onPress: async () => {
            try {
              // 모든 기기를 false로 설정
              const devices = ['fan', 'water', 'light', 'window'];
              
              // UI 즉시 반영
              setDeviceStatus({
                fan: false,
                water: false,
                light: false,
                window: false,
              });
              
              // 모든 기기를 순차적으로 끄기
              for (const device of devices) {
                try {
                  await controlDevice(device, false);
                } catch (error) {
                  console.error(`${device} 정지 오류:`, error);
                }
              }
              
              Alert.alert('완료', '모든 기기가 정지되었습니다.');
            } catch (error) {
              console.error('긴급 정지 오류:', error);
              Alert.alert('오류', '긴급 정지 중 오류가 발생했습니다.');
            }
          }
        }
      ]
    );
  };

  // 메인 화면
  const renderMainPage = () => (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>스마트팜 관리</Text>
      </View>

      <View style={styles.mainContainer}>
        <TouchableOpacity 
          style={[styles.mainButton, styles.statusButton]}
          onPress={() => setCurrentPage('status')}
        >
          <Text style={styles.mainButtonText}>상태 확인</Text>
          <Text style={styles.mainButtonSubText}>센서 정보 보기</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.mainButton, styles.controlMainButton]}
          onPress={() => setCurrentPage('control')}
        >
          <Text style={styles.mainButtonText}>제어하기</Text>
          <Text style={styles.mainButtonSubText}>기기 조작하기</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.mainButton, styles.settingsMainButton]}
          onPress={() => setCurrentPage('settings')}
        >
          <Text style={styles.mainButtonText}>설정</Text>
          <Text style={styles.mainButtonSubText}>자동제어 조건 설정</Text>
        </TouchableOpacity>
      </View>

      {/* 챗봇 바로가기 버튼 */}
      <TouchableOpacity 
        style={styles.chatbotFloatingButton}
        onPress={() => navigation.navigate('ElderlyChatScreen')}
      >
        <Text style={styles.chatbotButtonText}>💬 챗봇 문의</Text>
      </TouchableOpacity>
    </View>
  );

  // 상태확인 화면
  const renderStatusPage = () => (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => setCurrentPage('main')}
        >
          <Text style={styles.backButtonText}>← 뒤로가기</Text>
        </TouchableOpacity>
        <Text style={styles.title}>상태 확인</Text>
      </View>

      <View style={styles.pageContainer}>
        {/* 첫 번째 줄 */}
        <View style={styles.gridRow}>
          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('temperature')}
          >
            <Text style={styles.gridButtonText}>온도</Text>
            <Text style={styles.gridButtonValue}>{sensorData.temperature}°C</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('humidity')}
          >
            <Text style={styles.gridButtonText}>습도</Text>
            <Text style={styles.gridButtonValue}>{sensorData.humidity}%</Text>
          </TouchableOpacity>
        </View>

        {/* 두 번째 줄 */}
        <View style={styles.gridRow}>
          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('soil')}
          >
            <Text style={styles.gridButtonText}>토양습도</Text>
            <Text style={styles.gridButtonValue}>{sensorData.soil}%</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('co2')}
          >
            <Text style={styles.gridButtonText}>공기질</Text>
            <Text style={styles.gridButtonValue}>{sensorData.co2}ppm</Text>
          </TouchableOpacity>
        </View>

        {/* 세 번째 줄 */}
        <View style={styles.gridRow}>
          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('power')}
          >
            <Text style={styles.gridButtonText}>전력사용량</Text>
            <Text style={styles.gridButtonValue}>{sensorData.power}W</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, styles.infoButton]}
            onPress={() => checkSensorData('light')}
          >
            <Text style={styles.gridButtonText}>조도</Text>
            <Text style={styles.gridButtonValue}>{sensorData.light}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  // 제어하기 화면
  const renderControlPage = () => (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => setCurrentPage('main')}
        >
          <Text style={styles.backButtonText}>← 뒤로가기</Text>
        </TouchableOpacity>
        <Text style={styles.title}>제어하기</Text>
      </View>

      <View style={styles.pageContainer}>
        {/* 첫 번째 줄 */}
        <View style={styles.gridRow}>
          <TouchableOpacity 
            style={[styles.gridButton, deviceStatus.light ? styles.activeButton : styles.controlButton]}
            onPress={() => controlDeviceAction('light', deviceStatus.light ? '조명 끄기' : '조명 켜기')}
          >
            <Text style={styles.gridButtonText}>
              {deviceStatus.light ? '조명 끄기' : '조명 켜기'}
            </Text>
            <Text style={styles.deviceStatusText}>
              {deviceStatus.light ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, deviceStatus.fan ? styles.activeButton : styles.controlButton]}
            onPress={() => controlDeviceAction('fan', deviceStatus.fan ? '환풍기 끄기' : '환풍기 켜기')}
          >
            <Text style={styles.gridButtonText}>
              {deviceStatus.fan ? '환풍기 끄기' : '환풍기 켜기'}
            </Text>
            <Text style={styles.deviceStatusText}>
              {deviceStatus.fan ? '작동중' : '정지'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, deviceStatus.water ? styles.activeButton : styles.controlButton]}
            onPress={() => controlDeviceAction('water', deviceStatus.water ? '물 그만주기' : '물 주기')}
          >
            <Text style={styles.gridButtonText}>
              {deviceStatus.water ? '물 그만주기' : '물 주기'}
            </Text>
            <Text style={styles.deviceStatusText}>
              {deviceStatus.water ? '물 주는중' : '정지'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* 두 번째 줄 */}
        <View style={styles.gridRow}>
          <TouchableOpacity 
            style={[styles.gridButton, deviceStatus.window ? styles.activeButton : styles.controlButton]}
            onPress={() => controlDeviceAction('window', deviceStatus.window ? '창문 닫기' : '창문 열기')}
          >
            <Text style={styles.gridButtonText}>
              {deviceStatus.window ? '창문 닫기' : '창문 열기'}
            </Text>
            <Text style={styles.deviceStatusText}>
              {deviceStatus.window ? '열림' : '닫힘'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, styles.emergencyButton]}
            onPress={emergencyStop}
          >
            <Text style={styles.gridButtonText}>긴급 정지</Text>
            <Text style={styles.deviceStatusText}>모든 기기 정지</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.gridButton, autoMode ? styles.autoModeActiveButton : styles.autoModeButton]}
            onPress={toggleAutoMode}
          >
            <Text style={styles.gridButtonText}>자동모드</Text>
            <Text style={styles.deviceStatusText}>
              {autoMode ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );

  // 설정 화면
  const renderSettingsPage = () => (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => setCurrentPage('main')}
        >
          <Text style={styles.backButtonText}>← 뒤로가기</Text>
        </TouchableOpacity>
        <Text style={styles.title}>자동제어 설정</Text>
      </View>

      <ScrollView 
        style={styles.settingsScrollView}
        contentContainerStyle={styles.settingsContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 조명 설정 */}
        <View style={styles.settingSection}>
          <Text style={styles.settingTitle}>조명 자동제어</Text>
          <Text style={styles.settingDescription}>조도가 {autoSettings.light.threshold} 이상일 때 자동으로 켜기 (어두우면 켜짐)</Text>
          
          <TouchableOpacity 
            style={[styles.settingToggle, autoSettings.light.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => {
              const newSettings = { ...autoSettings, light: { ...autoSettings.light, enabled: !autoSettings.light.enabled } };
              updateAutoControlSettings(newSettings);
            }}
          >
            <Text style={styles.settingToggleText}>
              {autoSettings.light.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.temperatureButtons}>
            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.max(100, autoSettings.light.threshold - 50);
                updateAutoControlSettings({ light: { ...autoSettings.light, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>-50</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdText}>{autoSettings.light.threshold}</Text>

            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.min(950, autoSettings.light.threshold + 50);
                updateAutoControlSettings({ light: { ...autoSettings.light, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>+50</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 환풍기 설정 */}
        <View style={styles.settingSection}>
          <Text style={styles.settingTitle}>환풍기 자동제어</Text>
          <Text style={styles.settingDescription}>CO2가 {autoSettings.fan.threshold}ppm 이상일 때 자동으로 켜기</Text>
          
          <TouchableOpacity 
            style={[styles.settingToggle, autoSettings.fan.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => {
              const newSettings = { ...autoSettings, fan: { ...autoSettings.fan, enabled: !autoSettings.fan.enabled } };
              updateAutoControlSettings(newSettings);
            }}
          >
            <Text style={styles.settingToggleText}>
              {autoSettings.fan.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.temperatureButtons}>
            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.max(350, autoSettings.fan.threshold - 50);
                updateAutoControlSettings({ fan: { ...autoSettings.fan, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>-50ppm</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdText}>{autoSettings.fan.threshold}ppm</Text>

            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.min(600, autoSettings.fan.threshold + 50);
                updateAutoControlSettings({ fan: { ...autoSettings.fan, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>+50ppm</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 물주기 설정 */}
        <View style={styles.settingSection}>
          <Text style={styles.settingTitle}>물주기 자동제어</Text>
          <Text style={styles.settingDescription}>토양습도가 {autoSettings.water.threshold}% 이하일 때 자동으로 켜기</Text>
          
          <TouchableOpacity 
            style={[styles.settingToggle, autoSettings.water.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => {
              const newSettings = { ...autoSettings, water: { ...autoSettings.water, enabled: !autoSettings.water.enabled } };
              updateAutoControlSettings(newSettings);
            }}
          >
            <Text style={styles.settingToggleText}>
              {autoSettings.water.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.temperatureButtons}>
            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.max(20, autoSettings.water.threshold - 5);
                updateAutoControlSettings({ water: { ...autoSettings.water, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>-5%</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdText}>{autoSettings.water.threshold}%</Text>

            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newValue = Math.min(60, autoSettings.water.threshold + 5);
                updateAutoControlSettings({ water: { ...autoSettings.water, threshold: newValue } });
              }}
            >
              <Text style={styles.tempButtonText}>+5%</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 창문 설정 */}
        <View style={styles.settingSection}>
          <Text style={styles.settingTitle}>창문 자동제어</Text>
          <Text style={styles.settingDescription}>온도가 {autoSettings.window.threshold}°C 이상일 때 자동으로 열기</Text>
          
          <TouchableOpacity 
            style={[styles.settingToggle, autoSettings.window.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => {
              const newSettings = { ...autoSettings, window: { ...autoSettings.window, enabled: !autoSettings.window.enabled } };
              updateAutoControlSettings(newSettings);
            }}
          >
            <Text style={styles.settingToggleText}>
              {autoSettings.window.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.temperatureButtons}>
            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newTemp = Math.max(20, autoSettings.window.threshold - 1);
                updateAutoControlSettings({ window: { ...autoSettings.window, threshold: newTemp } });
              }}
            >
              <Text style={styles.tempButtonText}>-1°C</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdText}>{autoSettings.window.threshold}°C</Text>

            <TouchableOpacity 
              style={styles.tempButton}
              onPress={() => {
                const newTemp = Math.min(35, autoSettings.window.threshold + 1);
                updateAutoControlSettings({ window: { ...autoSettings.window, threshold: newTemp } });
              }}
            >
              <Text style={styles.tempButtonText}>+1°C</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 현재 상태 표시 */}
        <View style={styles.settingSection}>
          <Text style={styles.settingTitle}>현재 상태</Text>
          <Text style={styles.settingInfo}>자동모드: {autoMode ? '켜짐' : '꺼짐'}</Text>
          <Text style={styles.settingInfo}>현재 온도: {sensorData.temperature}°C</Text>
          <Text style={styles.settingInfo}>현재 CO2: {sensorData.co2}ppm</Text>
          <Text style={styles.settingInfo}>현재 토양습도: {sensorData.soil}%</Text>
          <Text style={styles.settingInfo}>현재 조도: {sensorData.light}</Text>
          
          <Text style={styles.settingInfo}>
            조명: {autoSettings.light.enabled && autoMode && sensorData.light >= autoSettings.light.threshold ? '자동제어 활성' : '비활성'}
          </Text>
          <Text style={styles.settingInfo}>
            환풍기: {autoSettings.fan.enabled && autoMode && sensorData.co2 >= autoSettings.fan.threshold ? '자동제어 활성' : '비활성'}
          </Text>
          <Text style={styles.settingInfo}>
            물주기: {autoSettings.water.enabled && autoMode && sensorData.soil <= autoSettings.water.threshold ? '자동제어 활성' : '비활성'}
          </Text>
          <Text style={styles.settingInfo}>
            창문: {autoSettings.window.enabled && autoMode && sensorData.temperature >= autoSettings.window.threshold ? '자동제어 활성' : '비활성'}
          </Text>
        </View>
      </ScrollView>
    </View>
  );

  // 로딩 상태 처리
  if (isLoading) {
    return (
      <View style={[styles.container, styles.loadingContainer]}>
        <Text style={styles.loadingText}>스마트팜 데이터를 불러오는 중...</Text>
      </View>
    );
  }

  // 현재 페이지에 따라 화면 렌더링
  switch (currentPage) {
    case 'main':
      return renderMainPage();
    case 'status':
      return renderStatusPage();
    case 'control':
      return renderControlPage();
    case 'settings':
      return renderSettingsPage();
    default:
      return renderMainPage();
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#e0e0e0',
  },
  header: {
    backgroundColor: '#2E7D32',
    paddingVertical: verticalScale(12),
    paddingHorizontal: scale(10),
    paddingTop: verticalScale(30),
    alignItems: 'center',
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    left: scale(10),
    top: verticalScale(30),
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: scale(8),
    paddingVertical: verticalScale(6),
    borderRadius: moderateScale(6),
    minWidth: scale(60),
    maxWidth: scale(80),
  },
  backButtonText: {
    color: '#fff',
    fontSize: moderateScale(14),
    fontWeight: 'bold',
    textAlign: 'center',
  },
  title: {
    fontSize: moderateScale(32),
    fontWeight: 'bold',
    color: '#fff',
    textAlign: 'center',
  },
  subtitle: {
    fontSize: moderateScale(24),
    color: '#C8E6C9',
    textAlign: 'center',
    marginTop: verticalScale(5),
    fontWeight: '600',
  },
  mainContainer: {
    flex: 1,
    padding: scale(8),
    justifyContent: 'center',
    gap: verticalScale(15),
  },
  mainButton: {
    flex: 1,
    maxHeight: verticalScale(180),
    borderRadius: moderateScale(15),
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: verticalScale(6) },
    shadowOpacity: 0.3,
    shadowRadius: moderateScale(10),
    elevation: 12,
    borderWidth: moderateScale(4),
  },
  statusButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#2E7D32',
  },
  controlMainButton: {
    backgroundColor: '#2196F3',
    borderColor: '#1565C0',
  },
  settingsMainButton: {
    backgroundColor: '#9E9E9E',
    borderColor: '#616161',
  },
  mainButtonText: {
    color: '#fff',
    fontSize: moderateScale(36),
    fontWeight: 'bold',
    textAlign: 'center',
  },
  mainButtonSubText: {
    color: '#fff',
    fontSize: moderateScale(20),
    textAlign: 'center',
    marginTop: verticalScale(5),
    opacity: 0.9,
  },
  pageContainer: {
    flex: 1,
    padding: scale(8),
    justifyContent: 'space-evenly',
  },
  gridRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: scale(4),
    flex: 1,
  },
  gridButton: {
    flex: 1,
    borderRadius: moderateScale(12),
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: verticalScale(4) },
    shadowOpacity: 0.3,
    shadowRadius: moderateScale(8),
    elevation: 10,
    borderWidth: moderateScale(3),
  },
  infoButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#2E7D32',
  },
  controlButton: {
    backgroundColor: '#2196F3',
    borderColor: '#1565C0',
  },
  emergencyButton: {
    backgroundColor: '#F44336',
    borderColor: '#C62828',
  },
  gridButtonText: {
    color: '#fff',
    fontSize: moderateScale(28),
    fontWeight: 'bold',
    textAlign: 'center',
  },
  gridButtonValue: {
    color: '#fff',
    fontSize: moderateScale(24),
    textAlign: 'center',
    marginTop: verticalScale(5),
    fontWeight: 'bold',
  },
  emptySpace: {
    flex: 1,
  },
  loadingContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: moderateScale(24),
    fontWeight: 'bold',
    color: '#333',
  },
  chatbotFloatingButton: {
    position: 'absolute',
    bottom: verticalScale(20),
    right: scale(20),
    backgroundColor: '#2196F3',
    paddingHorizontal: scale(20),
    paddingVertical: verticalScale(12),
    borderRadius: moderateScale(25),
    shadowColor: '#000',
    shadowOffset: { width: 0, height: verticalScale(4) },
    shadowOpacity: 0.3,
    shadowRadius: moderateScale(8),
    elevation: 10,
  },
  chatbotButtonText: {
    color: '#fff',
    fontSize: moderateScale(18),
    fontWeight: 'bold',
  },
  deviceStatusText: {
    color: '#fff',
    fontSize: moderateScale(16),
    textAlign: 'center',
    marginTop: verticalScale(5),
    fontWeight: '600',
    opacity: 0.9,
  },
  activeButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#2E7D32',
  },
  autoModeButton: {
    backgroundColor: '#2196F3',
    borderColor: '#1565C0',
  },
  autoModeActiveButton: {
    backgroundColor: '#4CAF50',
    borderColor: '#2E7D32',
  },
  settingSection: {
    padding: scale(12),
    borderWidth: 2,
    borderColor: '#2E7D32',
    borderRadius: moderateScale(8),
    marginBottom: verticalScale(10),
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
  },
  settingTitle: {
    fontSize: moderateScale(20),
    fontWeight: 'bold',
    color: '#2E7D32',
    marginBottom: verticalScale(8),
  },
  settingDescription: {
    fontSize: moderateScale(16),
    color: '#616161',
    marginBottom: verticalScale(8),
  },
  settingToggle: {
    backgroundColor: '#2196F3',
    padding: scale(8),
    borderRadius: moderateScale(5),
    marginBottom: verticalScale(5),
    alignItems: 'center',
  },
  toggleActive: {
    backgroundColor: '#4CAF50',
  },
  toggleInactive: {
    backgroundColor: '#F44336',
  },
  settingToggleText: {
    color: '#fff',
    fontSize: moderateScale(16),
    fontWeight: 'bold',
  },
  temperatureButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: scale(10),
  },
  tempButton: {
    backgroundColor: '#2196F3',
    padding: scale(8),
    borderRadius: moderateScale(5),
    flex: 1,
    alignItems: 'center',
  },
  tempButtonText: {
    color: '#fff',
    fontSize: moderateScale(16),
    fontWeight: 'bold',
  },
  thresholdText: {
    color: '#616161',
    fontSize: moderateScale(16),
    fontWeight: 'bold',
  },
  settingInfo: {
    fontSize: moderateScale(14),
    color: '#616161',
    marginTop: verticalScale(3),
  },
  settingsScrollView: {
    flex: 1,
  },
  settingsContent: {
    padding: scale(8),
  },
});

export default SmartFarmScreen; 