import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ImageBackground,
} from 'react-native';
import { fetchStatus } from '../services/api';

export default function ElderlyScreen({ navigation, route }) {
  // 실시간 센서 데이터 상태 추가
  const [latestValues, setLatestValues] = useState({
    temperature: 25,
    humidity: 61,
    power: 144,
    soil: 46,
    co2: 410,
    light: 50,
  });

  // 더미 히스토리 데이터 (그래프용)
  const [metricData] = useState({
    temperature: [22, 23, 24, 24, 25],
    humidity: [55, 58, 60, 59, 61],
    power: [130, 135, 140, 142, 144],
    soil: [40, 42, 45, 44, 46],
    co2: [400, 420, 430, 415, 410],
    light: [45, 48, 52, 50, 50],
  });

  // 실시간 센서 데이터 로드 (1초마다)
  useEffect(() => {
    const loadSensorData = async () => {
      try {
        const data = await fetchStatus();
        setLatestValues({
          temperature: data.temperature || 25,
          humidity: data.humidity || 61,
          power: data.power || 144,
          soil: data.soil || 46,
          co2: data.co2 || 410,
          light: data.light || 50,
        });
      } catch (error) {
        console.error('어르신 모드 센서 데이터 로드 오류:', error);
      }
    };

    // 초기 로드
    loadSensorData();

    // 1초마다 업데이트 (거의 실시간)
    const interval = setInterval(loadSensorData, 1000);

    return () => clearInterval(interval);
  }, []);

  const metricTitles = {
    temperature: '🌡 온도',
    humidity: '💧 습도',
    power: '⚡ 전력 사용량',
    soil: '🌱 토양 습도',
    co2: '🟢 이산화탄소',
  };

  const speak = (text) => {
    Alert.alert('음성 안내', text);
  };

  const onCardPress = (metric) => {
    navigation.navigate('GraphScreen', { metric, data: metricData[metric] });
  };

  const onControlPress = (action) => {
    Alert.alert('기기 제어', action);
  };

  return (
    <ImageBackground
      source={require('../assets/greenhouse.png')}
      style={styles.background}
      imageStyle={{ resizeMode: 'cover', opacity: 0.15 }}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.locationText}>
          현재 위치: {route?.params?.userLocation || '서울'}
        </Text>

        <Text style={styles.header}>👵 스마트 온실 - 노인 맞춤 화면</Text>

        {Object.keys(latestValues).map((metric) => (
          <TouchableOpacity
            key={metric}
            style={styles.card}
            onPress={() => onCardPress(metric)}
            onLongPress={() =>
              speak(`${metricTitles[metric]} 현재 값은 ${latestValues[metric]} 입니다.`)
            }
            activeOpacity={0.7}
          >
            <Text style={styles.cardTitle}>{metricTitles[metric]}</Text>
            <Text style={styles.cardValue}>{latestValues[metric]}</Text>
            <Text style={styles.cardHint}>(길게 눌러 음성 안내)</Text>
          </TouchableOpacity>
        ))}

        <View style={styles.controlSection}>
          <Text style={styles.sectionTitle}>⚙️ 기기 제어</Text>

          <TouchableOpacity
            style={styles.controlButton}
            onPress={() => onControlPress('환기 팬 켜기')}
            onLongPress={() => speak('환기 팬을 켰습니다')}
          >
            <Text style={styles.controlButtonText}>환기 팬 켜기</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.controlButton}
            onPress={() => onControlPress('스프링클러 작동')}
            onLongPress={() => speak('스프링클러가 작동 중입니다')}
          >
            <Text style={styles.controlButtonText}>스프링클러 작동</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.chatbotButton}
          onPress={() => navigation.navigate('ChatScreen')}
        >
          <Text style={styles.chatbotButtonText}>💬 챗봇 대화 시작</Text>
        </TouchableOpacity>
      </ScrollView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: {
    flex: 1,
  },
  container: {
    paddingVertical: 40,
    paddingHorizontal: 30,
    alignItems: 'center',
  },
  locationText: {
    fontSize: 18,
    color: '#4a6351', // 차분한 짙은 그린
    marginBottom: 10,
  },
  header: {
    fontSize: 36,
    fontWeight: 'bold',
    marginBottom: 40,
    color: '#2e7d32',
  },
  card: {
    width: '100%',
    backgroundColor: 'rgba(72, 129, 97, 0.85)', // 세련된 연두녹색 투명
    borderRadius: 15,
    paddingVertical: 30,
    paddingHorizontal: 25,
    marginBottom: 30,
    elevation: 8,
    shadowColor: '#34613e',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#e0f2f1', // 부드러운 연한 청록
  },
  cardValue: {
    fontSize: 48,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#ffffff',
  },
  cardHint: {
    fontSize: 14,
    marginTop: 8,
    color: '#c8e6c9',
  },
  controlSection: {
    width: '100%',
    marginTop: 20,
    marginBottom: 40,
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 30,
    fontWeight: 'bold',
    color: '#2e7d32',
    marginBottom: 20,
  },
  controlButton: {
    backgroundColor: 'rgba(56, 142, 60, 0.85)', // 세련된 진한 초록 투명
    paddingVertical: 20,
    borderRadius: 12,
    marginBottom: 20,
    alignItems: 'center',
    width: '80%',
    elevation: 6,
    shadowColor: '#1b5e20',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.5,
    shadowRadius: 5,
  },
  controlButtonText: {
    fontSize: 24,
    color: '#dcedc8',
    fontWeight: 'bold',
  },
  chatbotButton: {
    backgroundColor: '#1b5e20',
    paddingVertical: 25,
    paddingHorizontal: 50,
    borderRadius: 30,
    elevation: 8,
    shadowColor: '#004d40',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.7,
    shadowRadius: 8,
  },
  chatbotButtonText: {
    fontSize: 26,
    color: 'white',
    fontWeight: 'bold',
  },
});
