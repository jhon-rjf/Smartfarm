import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ImageBackground,
  Alert,
} from 'react-native';
import { getAutoControlSettings, updateAutoControlSettings, subscribeToAutoControlSettings, fetchStatus, subscribeToStatusUpdates, getAutoMode, subscribeToAutoModeUpdates } from '../services/api';

export default function AutoModeSettingsScreen({ navigation }) {
  // 자동제어 설정 상태
  const [autoSettings, setAutoSettings] = useState({
    light: { enabled: true, sensor: 'light', condition: 'above', threshold: 800, action: 'on' },
    fan: { enabled: true, sensor: 'co2', condition: 'above', threshold: 450, action: 'on' },
    water: { enabled: true, sensor: 'soil', condition: 'below', threshold: 40, action: 'on' },
    window: { enabled: true, sensor: 'temperature', condition: 'above', threshold: 25, action: 'on' }
  });

  // 센서 데이터 상태
  const [sensorData, setSensorData] = useState({
    temperature: 25,
    humidity: 61,
    power: 144,
    soil: 46,
    co2: 410,
    light: 50,
  });

  // 자동모드 상태
  const [autoMode, setAutoMode] = useState(false);

  useEffect(() => {
    loadInitialData();

    // 실시간 상태 업데이트 구독
    const unsubscribeStatus = subscribeToStatusUpdates((data) => {
      if (data) {
        if (data.temperature !== undefined) setSensorData(prev => ({ ...prev, temperature: data.temperature }));
        if (data.humidity !== undefined) setSensorData(prev => ({ ...prev, humidity: data.humidity }));
        if (data.power !== undefined) setSensorData(prev => ({ ...prev, power: data.power }));
        if (data.soil !== undefined) setSensorData(prev => ({ ...prev, soil: data.soil }));
        if (data.co2 !== undefined) setSensorData(prev => ({ ...prev, co2: data.co2 }));
        if (data.light !== undefined) setSensorData(prev => ({ ...prev, light: data.light }));
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
      unsubscribeStatus();
      unsubscribeAutoMode();
      unsubscribeAutoSettings();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      const status = await fetchStatus();
      if (status) {
        setSensorData({
          temperature: status.temperature || 25,
          humidity: status.humidity || 61,
          power: status.power || 144,
          soil: status.soil || 46,
          co2: status.co2 || 410,
          light: status.light || 50,
        });
      }

      const currentAutoMode = getAutoMode();
      setAutoMode(currentAutoMode);

      const settings = getAutoControlSettings();
      if (settings) {
        setAutoSettings(settings);
      }
    } catch (error) {
      console.error('초기 데이터 로드 오류:', error);
    }
  };

  const updateSetting = (device, newSettings) => {
    const updatedSettings = { ...autoSettings, [device]: { ...autoSettings[device], ...newSettings } };
    updateAutoControlSettings(updatedSettings);
  };

  return (
    <ImageBackground
      source={require('../assets/greenhouse.png')}
      style={styles.background}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>⚙️ 자동모드 설정 ⚙️</Text>
        
        {/* 현재 상태 카드 */}
        <View style={styles.statusCard}>
          <Text style={styles.statusTitle}>현재 상태</Text>
          <Text style={styles.statusText}>자동모드: {autoMode ? '켜짐' : '꺼짐'}</Text>
          <Text style={styles.statusText}>온도: {sensorData.temperature}°C</Text>
          <Text style={styles.statusText}>CO2: {sensorData.co2}ppm</Text>
          <Text style={styles.statusText}>토양습도: {sensorData.soil}%</Text>
          <Text style={styles.statusText}>조도: {sensorData.light}</Text>
        </View>

        {/* 조명 자동제어 설정 */}
        <View style={styles.settingCard}>
          <Text style={styles.cardTitle}>조명 자동제어</Text>
          <Text style={styles.cardDescription}>
            조도가 {autoSettings.light.threshold} 이상일 때 자동으로 켜기 (어두우면 켜짐)
          </Text>
          
          <TouchableOpacity 
            style={[styles.toggleButton, autoSettings.light.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => updateSetting('light', { enabled: !autoSettings.light.enabled })}
          >
            <Text style={styles.toggleText}>
              {autoSettings.light.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.thresholdControls}>
            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.max(100, autoSettings.light.threshold - 50);
                updateSetting('light', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>-50</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdValue}>{autoSettings.light.threshold}</Text>

            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.min(950, autoSettings.light.threshold + 50);
                updateSetting('light', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>+50</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.statusIndicator}>
            상태: {autoSettings.light.enabled && autoMode && sensorData.light >= autoSettings.light.threshold ? '자동제어 활성' : '비활성'}
          </Text>
        </View>

        {/* 환풍기 자동제어 설정 */}
        <View style={styles.settingCard}>
          <Text style={styles.cardTitle}>환풍기 자동제어</Text>
          <Text style={styles.cardDescription}>
            CO2가 {autoSettings.fan.threshold}ppm 이상일 때 자동으로 켜기
          </Text>
          
          <TouchableOpacity 
            style={[styles.toggleButton, autoSettings.fan.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => updateSetting('fan', { enabled: !autoSettings.fan.enabled })}
          >
            <Text style={styles.toggleText}>
              {autoSettings.fan.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.thresholdControls}>
            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.max(350, autoSettings.fan.threshold - 50);
                updateSetting('fan', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>-50ppm</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdValue}>{autoSettings.fan.threshold}ppm</Text>

            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.min(600, autoSettings.fan.threshold + 50);
                updateSetting('fan', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>+50ppm</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.statusIndicator}>
            상태: {autoSettings.fan.enabled && autoMode && sensorData.co2 >= autoSettings.fan.threshold ? '자동제어 활성' : '비활성'}
          </Text>
        </View>

        {/* 물주기 자동제어 설정 */}
        <View style={styles.settingCard}>
          <Text style={styles.cardTitle}>물주기 자동제어</Text>
          <Text style={styles.cardDescription}>
            토양습도가 {autoSettings.water.threshold}% 이하일 때 자동으로 켜기
          </Text>
          
          <TouchableOpacity 
            style={[styles.toggleButton, autoSettings.water.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => updateSetting('water', { enabled: !autoSettings.water.enabled })}
          >
            <Text style={styles.toggleText}>
              {autoSettings.water.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.thresholdControls}>
            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.max(20, autoSettings.water.threshold - 5);
                updateSetting('water', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>-5%</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdValue}>{autoSettings.water.threshold}%</Text>

            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newValue = Math.min(60, autoSettings.water.threshold + 5);
                updateSetting('water', { threshold: newValue });
              }}
            >
              <Text style={styles.adjustButtonText}>+5%</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.statusIndicator}>
            상태: {autoSettings.water.enabled && autoMode && sensorData.soil <= autoSettings.water.threshold ? '자동제어 활성' : '비활성'}
          </Text>
        </View>

        {/* 창문 자동제어 설정 */}
        <View style={styles.settingCard}>
          <Text style={styles.cardTitle}>창문 자동제어</Text>
          <Text style={styles.cardDescription}>
            온도가 {autoSettings.window.threshold}°C 이상일 때 자동으로 열기
          </Text>
          
          <TouchableOpacity 
            style={[styles.toggleButton, autoSettings.window.enabled ? styles.toggleActive : styles.toggleInactive]}
            onPress={() => updateSetting('window', { enabled: !autoSettings.window.enabled })}
          >
            <Text style={styles.toggleText}>
              {autoSettings.window.enabled ? '켜짐' : '꺼짐'}
            </Text>
          </TouchableOpacity>
          
          <View style={styles.thresholdControls}>
            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newTemp = Math.max(20, autoSettings.window.threshold - 1);
                updateSetting('window', { threshold: newTemp });
              }}
            >
              <Text style={styles.adjustButtonText}>-1°C</Text>
            </TouchableOpacity>

            <Text style={styles.thresholdValue}>{autoSettings.window.threshold}°C</Text>

            <TouchableOpacity 
              style={styles.adjustButton}
              onPress={() => {
                const newTemp = Math.min(35, autoSettings.window.threshold + 1);
                updateSetting('window', { threshold: newTemp });
              }}
            >
              <Text style={styles.adjustButtonText}>+1°C</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.statusIndicator}>
            상태: {autoSettings.window.enabled && autoMode && sensorData.temperature >= autoSettings.window.threshold ? '자동제어 활성' : '비활성'}
          </Text>
        </View>

        {/* 뒤로가기 버튼 */}
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← 뒤로가기</Text>
        </TouchableOpacity>
      </ScrollView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: { 
    flex: 1 
  },
  scrollContainer: { 
    alignItems: 'center', 
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
    textAlign: 'center',
  },
  statusCard: {
    backgroundColor: 'rgba(0,100,0,0.8)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
    width: '100%',
    alignItems: 'center',
  },
  statusTitle: {
    fontSize: 24,
    color: 'white',
    fontWeight: 'bold',
    marginBottom: 10,
  },
  statusText: {
    fontSize: 18,
    color: 'white',
    marginBottom: 5,
  },
  settingCard: {
    backgroundColor: 'rgba(0,100,0,0.7)',
    padding: 20,
    borderRadius: 15,
    marginBottom: 20,
    width: '100%',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 24,
    color: 'white',
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  cardDescription: {
    fontSize: 16,
    color: 'white',
    marginBottom: 15,
    textAlign: 'center',
    opacity: 0.9,
  },
  toggleButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 15,
    minWidth: 100,
    alignItems: 'center',
  },
  toggleActive: {
    backgroundColor: '#4CAF50',
  },
  toggleInactive: {
    backgroundColor: '#f44336',
  },
  toggleText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  thresholdControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
    gap: 15,
  },
  adjustButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  adjustButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  thresholdValue: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
    minWidth: 80,
    textAlign: 'center',
  },
  statusIndicator: {
    fontSize: 14,
    color: 'white',
    textAlign: 'center',
    opacity: 0.8,
    marginTop: 5,
  },
  backButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 10,
    marginTop: 20,
    marginBottom: 40,
  },
  backButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
}); 