import React from 'react';
import { View, Text, StyleSheet, Dimensions, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

export default function GraphBox({ title, data, isLoading, onRefresh }) {
  // 차트 라벨 생성: 데이터가 있으면 순서대로, 없으면 기본값
  const generateLabels = (dataLength) => {
    if (dataLength <= 5) {
      return Array.from({ length: dataLength }, (_, i) => `${i + 1}h`);
    } else {
      // 10개 이상일 경우 간격을 두고 표시
      const step = Math.ceil(dataLength / 5);
      return Array.from({ length: 5 }, (_, i) => `${(i + 1) * step}h`);
    }
  };

  return (
    <View style={styles.graphBox}>
      <View style={styles.titleRow}>
        <Text style={styles.graphTitle}>{title}</Text>
        {onRefresh && (
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={onRefresh}
            disabled={isLoading}
          >
            <Text style={styles.refreshText}>🔄</Text>
          </TouchableOpacity>
        )}
      </View>

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#ffffff" />
          <Text style={styles.loadingText}>차트 데이터 로딩 중...</Text>
        </View>
      ) : data && data.length > 0 ? (
        <View>
          <LineChart
            data={{
              labels: generateLabels(data.length),
              datasets: [{ data }],
            }}
            width={Dimensions.get('window').width * 0.4}
            height={250}
            chartConfig={{
              backgroundGradientFrom: 'rgba(0,0,0,0)',
              backgroundGradientTo: 'rgba(0,0,0,0)',
              color: () => `rgba(255, 255, 255, 0.9)`,
              labelColor: () => '#fff',
              strokeWidth: 2,
              decimalPlaces: 1,
            }}
            bezier
            style={{ borderRadius: 12 }}
          />
          <Text style={styles.dataInfo}>
            📊 {data.length}개 데이터 포인트 | 최신: {data[data.length - 1]?.toFixed(1)}
          </Text>
        </View>
      ) : (
        <View style={styles.placeholderContainer}>
          <Text style={styles.placeholder}>📊 상태 카드를 눌러 데이터를 확인하세요</Text>
          <Text style={styles.placeholderSub}>데이터 수집 중이거나 연결을 확인해주세요</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  graphBox: {
    backgroundColor: 'rgba(0,100,0,0.7)',
    padding: 15,
    borderRadius: 10,
    width: '100%',
    alignItems: 'center',
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 10,
  },
  graphTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    flex: 1,
  },
  refreshButton: {
    padding: 8,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: 20,
    marginLeft: 10,
  },
  refreshText: {
    fontSize: 16,
    color: 'white',
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  loadingText: {
    fontSize: 14,
    color: '#fff',
    marginTop: 10,
    textAlign: 'center',
  },
  placeholderContainer: {
    alignItems: 'center',
    padding: 20,
  },
  placeholder: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    color: '#fff',
    marginBottom: 5,
  },
  placeholderSub: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
  },
  dataInfo: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    marginTop: 10,
  },
});
