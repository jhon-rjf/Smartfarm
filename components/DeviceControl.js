import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { fetchStatus, controlDevice, subscribeToStatusUpdates, getAutoMode, subscribeToAutoModeUpdates, setAutoMode, getAutoControlSettings, subscribeToAutoControlSettings } from '../services/api';

export default function DeviceControl({ currentTemperature, currentCo2, currentSoil }) {
  const [devices, setDevices] = useState({
    fan: false,
    water: false,
    light: false,
    window: false,
    lightSensor: false,
  });

  const [autoMode, setAutoMode] = useState(false);
  const [lastAutoAction, setLastAutoAction] = useState(null); // 마지막 자동 제어 기록
  const [autoSettings, setAutoSettings] = useState({
    light: { enabled: true, sensor: 'temperature', condition: 'below', threshold: 20, action: 'on' },
    fan: { enabled: true, sensor: 'co2', condition: 'above', threshold: 450, action: 'on' },
    water: { enabled: true, sensor: 'soil', condition: 'below', threshold: 40, action: 'on' },
    window: { enabled: true, sensor: 'temperature', condition: 'above', threshold: 25, action: 'on' }
  });

  useEffect(() => {
    loadDeviceStatus();

    const unsubscribe = subscribeToStatusUpdates((data) => {
      if (data && data.devices) {
        setDevices(data.devices);
      }
    });

    // 자동모드 상태 구독
    const unsubscribeAutoMode = subscribeToAutoModeUpdates((enabled) => {
      setAutoMode(enabled);
      // 자동모드가 꺼지면 자동 제어 기록도 초기화
      if (!enabled) {
        setLastAutoAction(null);
      }
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

  // 자동제어 로직 - 4가지 기기 모두 체크
  useEffect(() => {
    if (!autoMode) return;

    const checkAndControlDevice = async (deviceName, settings, sensorValue) => {
      if (!settings.enabled) return;
      
      const shouldActivate = settings.condition === 'above' 
        ? sensorValue >= settings.threshold 
        : sensorValue <= settings.threshold;

      const currentDeviceStatus = devices[deviceName];
      const targetStatus = shouldActivate ? (settings.action === 'on') : false; // 조건 불만족시 항상 끄기

      // 현재 상태와 목표 상태가 다르면 제어
      if (currentDeviceStatus !== targetStatus) {
        setLastAutoAction({ 
          device: deviceName, 
          action: targetStatus ? 'on' : 'off', 
          time: Date.now() 
        });
        
        try {
          setDevices((prev) => ({ ...prev, [deviceName]: targetStatus }));
          const response = await controlDevice(deviceName, targetStatus);
          if (response && response.devices) {
            setDevices(response.devices);
          }
          console.log(`자동모드: ${deviceName} ${targetStatus ? 'ON' : 'OFF'} (${settings.sensor}: ${sensorValue} ${settings.condition} ${settings.threshold})`);
        } catch (error) {
          console.error(`자동 ${deviceName} 제어 오류:`, error);
          await loadDeviceStatus();
        }
      }
    };

    // 각 기기별 자동제어 체크
    const sensorValues = {
      temperature: currentTemperature,
      co2: currentCo2,
      soil: currentSoil,
    };

    // 조명 제어 (온도 기반)
    checkAndControlDevice('light', autoSettings.light, sensorValues.temperature);
    
    // 환풍기 제어 (CO2 기반)
    checkAndControlDevice('fan', autoSettings.fan, sensorValues.co2);
    
    // 물주기 제어 (토양습도 기반)
    checkAndControlDevice('water', autoSettings.water, sensorValues.soil);
    
    // 창문 제어 (온도 기반)
    checkAndControlDevice('window', autoSettings.window, sensorValues.temperature);

  }, [autoMode, autoSettings, currentTemperature, currentCo2, currentSoil, devices]);

  const loadDeviceStatus = async () => {
    try {
      const status = await fetchStatus();
      if (status && status.devices) {
        setDevices(status.devices);
      }
    } catch (error) {
      console.error('장치 상태 로드 실패:', error);
    }
  };

  const handleControl = useCallback(async (device, status) => {
    try {
      // 최근에 자동으로 조명을 껐는데 사용자가 다시 켜는 경우
      if (autoMode && device === 'light' && status === true && 
          lastAutoAction && lastAutoAction.device === 'light' && 
          lastAutoAction.action === 'off' && 
          Date.now() - lastAutoAction.time < 30000) { // 30초 이내
        
        setAutoMode(false);
        setLastAutoAction(null);
        Alert.alert(
          '자동모드 해제',
          '자동으로 끄진 조명을 다시 켜셔서 자동모드가 해제되었습니다.\n앞으로 수동으로 제어하실 수 있습니다.',
          [{ text: '확인' }],
          { cancelable: true }
        );
      }
      // 자동모드가 켜져있고 해당 기기의 개별 자동제어도 켜져있을 때만 자동모드 해제
      else if (autoMode && autoSettings[device] && autoSettings[device].enabled) {
        setAutoMode(false);
        setLastAutoAction(null);
        Alert.alert(
          '자동모드 해제',
          `${device === 'light' ? '조명' : device === 'fan' ? '환풍기' : device === 'water' ? '물주기' : device === 'window' ? '창문' : device} 자동제어가 켜져있어서 수동 제어 시 자동모드가 해제되었습니다.`,
          [{ text: '확인' }],
          { cancelable: true }
        );
      }

      // UI 즉시 반영
      setDevices((prev) => ({ ...prev, [device]: status }));

      const response = await controlDevice(device, status);

      if (response && response.devices) {
        setDevices(response.devices);
      } else if (!response.success) {
        await loadDeviceStatus();
      }
    } catch (error) {
      console.error('장치 제어 오류:', error);
      await loadDeviceStatus();
    }
  }, [autoMode, lastAutoAction, autoSettings]); // autoSettings 의존성 추가

  return (
    <View style={styles.box}>
      <Text style={styles.boxTitle}>장치 제어</Text>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={() => handleControl('light', !devices.light)}
      >
        <Text style={styles.controlButtonText}>
          💡 {devices.light ? '조명 끄기' : '조명 켜기'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={() => handleControl('fan', !devices.fan)}
      >
        <Text style={styles.controlButtonText}>
          🌀 {devices.fan ? '환풍기 끄기' : '환풍기 켜기'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={() => handleControl('water', !devices.water)}
      >
        <Text style={styles.controlButtonText}>
          💧 {devices.water ? '급수 중단' : '급수 시작'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={() => handleControl('window', !devices.window)}
      >
        <Text style={styles.controlButtonText}>
          🪟 {devices.window ? '창문 닫기' : '창문 열기'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.controlButton}
        onPress={() => handleControl('lightSensor', !devices.lightSensor)}
      >
        <Text style={styles.controlButtonText}>
          🌞 {devices.lightSensor ? '조도센서 끄기' : '조도센서 켜기'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    backgroundColor: 'rgba(0,100,0,0.7)',
    padding: 15,
    borderRadius: 10,
    marginTop: 20,
    width: '80%',
    alignItems: 'center',
  },
  boxTitle: {
    fontSize: 24,
    color: 'white',
    marginBottom: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  controlButton: {
    backgroundColor: 'white',
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 8,
    marginVertical: 6,
    alignItems: 'center',
    width: '100%',
  },
  controlButtonText: {
    fontSize: 17,
    fontWeight: 'bold',
    color: '#2c2c2c',
  },
});
