import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { fetchStatus } from '../services/api';

export default function StatusCards({ onCardPress }) {
  const [statusData, setStatusData] = useState({
    temperature: 23.5,
    humidity: 58.0,
    power: 135.0,
    soil: 42.0,
    co2: 420.0, // 초기 CO₂ 수치
    light: 50, // 초기 조도 수치
  });

  // 상태 데이터 로드
  useEffect(() => {
    loadStatusData();

    // 주기적으로 상태 업데이트 (30초마다)
    const interval = setInterval(loadStatusData, 30000);

    return () => clearInterval(interval);
  }, []);

  const loadStatusData = async () => {
    try {
      const data = await fetchStatus();
      setStatusData({
        temperature: data.temperature,
        humidity: data.humidity,
        power: data.power,
        soil: data.soil,
        co2: data.co2, // CO2 포함
        light: data.light, // 조도 포함
      });
    } catch (error) {
      console.error('상태 데이터 로드 오류:', error);
    }
  };

  const cards = [
    { label: '🌡 온도', value: `${statusData.temperature?.toFixed(1) ?? '--'}°C`, key: 'temperature' },
    { label: '💧 습도', value: `${statusData.humidity?.toFixed(1) ?? '--'}%`, key: 'humidity' },
    { label: '⚡ 전력', value: `${statusData.power?.toFixed(1) ?? '--'}W`, key: 'power' },
    { label: '🌱 토양 습도', value: `${statusData.soil?.toFixed(1) ?? '--'}%`, key: 'soil' },
    { label: '💨 CO₂', value: `${statusData.co2?.toFixed(1) ?? '--'} ppm`, key: 'co2' }, // CO2 카드
    { label: '🌞 조도', value: `${statusData.light?.toFixed(0) ?? '--'}`, key: 'light' }, // 조도 카드
  ];

  return (
    <View style={styles.container}>
      {cards.map((card) => (
        <TouchableOpacity key={card.key} style={styles.card} onPress={() => onCardPress(card.key)}>
          <Text style={styles.cardText}>
            {card.label}
            {'\n'}
            {card.value}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    width: '90%',
  },
  card: {
    backgroundColor: 'rgba(0,0,0,0.6)',
    paddingVertical: 20,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginVertical: 10,
    width: '45%',
    minHeight: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardText: {
    color: 'white',
    fontSize: 18,
    textAlign: 'center',
    fontWeight: '600',
  },
});
