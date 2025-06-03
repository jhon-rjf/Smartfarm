import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

export default function GraphBox({ title, data }) {
  return (
    <View style={styles.graphBox}>
      <Text style={styles.graphTitle}>{title}</Text>
      {data && data.length > 0 ? (
        <LineChart
          data={{
            labels: ['1h', '2h', '3h', '4h', '5h'], // 필요하면 props로도 전달 가능
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
          }}
          bezier
          style={{ borderRadius: 12 }}
        />
      ) : (
        <Text style={styles.placeholder}>📊 상태 카드를 눌러 데이터를 확인하세요</Text>
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
  graphTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 10,
  },
  placeholder: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    color: '#fff',
  },
});
