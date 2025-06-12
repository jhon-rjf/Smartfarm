import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ImageBackground,
  TouchableOpacity,
  Image,
  LogBox,
  Alert,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import ChatbotScreen from './screens/ChatbotScreen';
import VoiceTestScreen from './screens/VoiceTestScreen';
import AutoModeSettingsScreen from './screens/AutoModeSettingsScreen';
import ElderlyChatScreen from './screens/ElderlyChatScreen';
import StatusCards from './components/StatusCards';
import DeviceControl from './components/DeviceControl';
import GraphBox from './components/GraphBox';
import ElderlyScreen from './screens/ElderlyScreen';
import { StatusBar } from 'expo-status-bar';
import { getAutoMode, setAutoMode as setGlobalAutoMode, subscribeToAutoModeUpdates, initApiService, fetchHistory } from './services/api';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
  'Failed to get permissions for location',
]);

function FloatingButtons({ navigation }) {
  return (
    <>
      {/* 오른쪽 하단 챗봇 버튼 */}
      <TouchableOpacity
        style={[styles.fab, { bottom: 30, right: 30 }]}
        onPress={() => navigation.navigate('ChatScreen')}
      >
        <Image
          source={require('./assets/chatbot.png')}
          style={styles.fabIcon}
          resizeMode="cover"
        />
      </TouchableOpacity>
    </>
  );
}


function HomeScreen({ navigation, userLocation }) {
  const [selectedMetric, setSelectedMetric] = useState('temperature');
  const [autoMode, setAutoMode] = useState(false);
  const [chartData, setChartData] = useState({});
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  const [currentSensorData, setCurrentSensorData] = useState({
    temperature: 23.5,
    humidity: 58.0,
    power: 135.0,
    soil: 42.0,
    co2: 420.0,
    light: 50,
  });

  // 기본 더미 데이터 (API 실패시 사용)
  const fallbackMetricData = {
    temperature: [22, 23, 24, 24, 25],
    humidity: [55, 58, 60, 59, 61],
    power: [130, 135, 140, 142, 144],
    soil: [40, 42, 45, 44, 46],
    co2: [400, 420, 430, 415, 410],
    light: [45, 50, 55, 48, 52],
  };

  const metricTitles = {
    temperature: '🌡 온도 변화',
    humidity: '💧 습도 변화',
    power: '⚡ 전력 사용량 변화 (계산값)',
    soil: '🌱 토양 습도 변화',
    co2: '🟢 이산화탄소 농도 변화',
    light: '🌞 조도 변화',
  };

  // 차트 데이터 로드 함수
  const loadChartData = async (metric) => {
    setIsLoadingChart(true);
    try {
      console.log(`[HomeScreen] ${metric} 차트 데이터 로딩 중...`);
      const historyData = await fetchHistory(metric);
      
      console.log(`[HomeScreen] ${metric} 받은 데이터:`, historyData ? historyData.length : 0, '개');
      
      if (historyData && historyData.length > 0) {
        // API에서 받은 실제 데이터를 차트 형식으로 변환
        const chartValues = historyData.slice(-10).map(item => item.value); // 최근 10개 데이터
        console.log(`[HomeScreen] ${metric} 변환된 차트 값들:`, chartValues);
        
        setChartData(prev => {
          const newData = {
            ...prev,
            [metric]: chartValues
          };
          console.log(`[HomeScreen] ${metric} 차트 상태 업데이트:`, newData[metric]);
          return newData;
        });
        
        console.log(`[HomeScreen] ${metric} 실제 데이터 로드 완료:`, chartValues.length, '개 포인트');
      } else {
        // 데이터가 없으면 더미 데이터 사용
        setChartData(prev => ({
          ...prev,
          [metric]: fallbackMetricData[metric]
        }));
        console.log(`[HomeScreen] ${metric} 더미 데이터 사용:`, fallbackMetricData[metric]);
      }
    } catch (error) {
      console.error(`[HomeScreen] ${metric} 차트 데이터 로드 오러:`, error);
      // 오류 시 더미 데이터 사용
      setChartData(prev => ({
        ...prev,
        [metric]: fallbackMetricData[metric]
      }));
    } finally {
      setIsLoadingChart(false);
    }
  };

  // 현재 표시될 차트 데이터
  const currentChartData = chartData[selectedMetric] || fallbackMetricData[selectedMetric];
  console.log(`[HomeScreen] ${selectedMetric} 현재 차트 데이터:`, currentChartData);
  
  // 현재 센서 데이터 로드 함수
  const loadCurrentSensorData = async () => {
    try {
      const { fetchStatus } = await import('./services/api');
      const data = await fetchStatus();
      setCurrentSensorData({
        temperature: data.temperature || fallbackMetricData.temperature[fallbackMetricData.temperature.length - 1],
        humidity: data.humidity || fallbackMetricData.humidity[fallbackMetricData.humidity.length - 1],
        power: data.power || fallbackMetricData.power[fallbackMetricData.power.length - 1],
        soil: data.soil || fallbackMetricData.soil[fallbackMetricData.soil.length - 1],
        co2: data.co2 || fallbackMetricData.co2[fallbackMetricData.co2.length - 1],
        light: data.light || fallbackMetricData.light[fallbackMetricData.light.length - 1],
      });
    } catch (error) {
      console.error('현재 센서 데이터 로드 오류:', error);
    }
  };

  // 디바이스 제어용 현재 값들
  const currentTemperature = currentSensorData.temperature;
  const currentCo2 = currentSensorData.co2;
  const currentSoil = currentSensorData.soil;
  const currentLight = currentSensorData.light;

  useEffect(() => {
    (async () => {
      try {
        const autoMode = await getAutoMode();
        setAutoMode(autoMode);
      } catch (error) {
        console.error('자동모드 정보 가져오기 오류:', error);
      }
    })();

    // 초기 센서 데이터 로드
    loadCurrentSensorData();

    // 주기적으로 센서 데이터 업데이트 (30초마다)
    const sensorInterval = setInterval(loadCurrentSensorData, 30000);

    // 자동모드 상태 실시간 구독
    const unsubscribeAutoMode = subscribeToAutoModeUpdates((enabled) => {
      setAutoMode(enabled);
    });

    return () => {
      unsubscribeAutoMode();
      clearInterval(sensorInterval);
    };
  }, []);

  // 선택된 메트릭이 변경될 때 차트 데이터 로드
  useEffect(() => {
    loadChartData(selectedMetric);
  }, [selectedMetric]);

  // 메트릭 선택 핸들러
  const handleMetricSelect = async (metric) => {
    setSelectedMetric(metric);
  };

  const handleAutoMode = async () => {
    try {
      const newAutoMode = !autoMode;
      await setGlobalAutoMode(newAutoMode);
      setAutoMode(newAutoMode);
      Alert.alert(
        '자동모드',
        `자동모드가 ${newAutoMode ? '켜졌습니다' : '꺼졌습니다'}.\n${newAutoMode ? '온도, CO2, 토양습도 조건에 따라 자동으로 기기가 제어됩니다.' : '수동으로만 기기를 제어할 수 있습니다.'}`,
        [{ text: '확인' }]
      );
    } catch (error) {
      console.error('자동모드 설정 오류:', error);
      Alert.alert('오류', '자동모드 설정 중 오류가 발생했습니다.');
    }
  };

  return (
    <ImageBackground
      source={require('./assets/greenhouse.png')}
      style={styles.background}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>🌿 Smart Greenhouse System 🌿</Text>
        <StatusCards onCardPress={handleMetricSelect} />

        <View style={styles.mainSectionWrapper}>
          <View style={styles.deviceControlWrapper}>
            <DeviceControl 
              currentTemperature={currentTemperature}
              currentCo2={currentCo2}
              currentSoil={currentSoil}
              currentLight={currentLight}
            />
            
            {/* 자동모드 제어 버튼들 */}
            <View style={styles.autoModeControls}>
              <TouchableOpacity
                style={[styles.autoModeToggleButton, autoMode ? styles.autoModeActive : styles.autoModeInactive]}
                onPress={handleAutoMode}
              >
                <Text style={styles.autoModeToggleText}>
                  {autoMode ? '자동모드 끄기' : '자동모드 켜기'}
                </Text>
                <Text style={styles.autoModeStatusText}>
                  현재: {autoMode ? '켜짐' : '꺼짐'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.autoModeSettingsButton}
                onPress={() => navigation.navigate('AutoModeSettings')}
              >
                <Text style={styles.autoModeSettingsText}>⚙️ 자동모드 설정</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.graphSectionWrapper}>
            <GraphBox
              title={metricTitles[selectedMetric]}
              data={currentChartData}
              isLoading={isLoadingChart}
              onRefresh={() => loadChartData(selectedMetric)}
            />
          </View>
        </View>
      </ScrollView>

      <FloatingButtons navigation={navigation} />
    </ImageBackground>
  );
}

function HomeStackNavigator({ userLocation }) {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeScreen">
        {props => <HomeScreen {...props} userLocation={userLocation} />}
      </Stack.Screen>
      <Stack.Screen name="ChatScreen">
        {props => <ChatbotScreen {...props} userLocation={userLocation} />}
      </Stack.Screen>
      <Stack.Screen name="ElderlyScreen" component={ElderlyScreen} />
      <Stack.Screen name="AutoModeSettings" component={AutoModeSettingsScreen} />
      <Stack.Screen name="ElderlyChatScreen" component={ElderlyChatScreen} />
    </Stack.Navigator>
  );
}

function VoiceTestStackNavigator({ userLocation }) {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="VoiceTestScreen">
        {props => <VoiceTestScreen {...props} userLocation={userLocation} />}
      </Stack.Screen>
      <Stack.Screen name="ElderlyChatScreen">
        {props => <ElderlyChatScreen {...props} userLocation={userLocation} />}
      </Stack.Screen>
    </Stack.Navigator>
  );
}

export default function App() {
  const [userLocation, setUserLocation] = useState('서울');

  useEffect(() => {
    // API 서비스 초기화
    const initializeServices = async () => {
      try {
        console.log('[App] API 서비스 초기화 시작...');
        await initApiService();
        console.log('[App] API 서비스 초기화 완료');
      } catch (error) {
        console.error('[App] API 서비스 초기화 오류:', error);
      }
    };

    initializeServices();

    // 위치 정보 가져오기
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          console.log('위치 권한이 거부되었습니다');
          return;
        }
        const location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        });
        const geocode = await Location.reverseGeocodeAsync({
          latitude: location.coords.latitude,
          longitude: location.coords.longitude,
        });
        if (geocode && geocode.length > 0) {
          const address = geocode[0];
          const city = address.city || address.region || '서울';
          console.log('위치 정보:', city);
          setUserLocation(city);
        }
      } catch (error) {
        console.error('위치 정보 가져오기 오류:', error);
      }
    })();
  }, []);

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;
            if (route.name === 'Home') {
              iconName = focused ? 'ios-home' : 'ios-home-outline';
            } else if (route.name === 'Chatbot') {
              iconName = focused ? 'ios-chatbubble' : 'ios-chatbubble-outline';
            } else if (route.name === 'VoiceTest') {
              iconName = focused ? 'ios-settings' : 'ios-settings-outline';
            }
            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#4CAF50',
          tabBarInactiveTintColor: 'gray',
          tabBarLabelStyle: { fontSize: 12 },
          tabBarStyle: {
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            borderTopWidth: 1,
            borderTopColor: '#e0e0e0',
          },
          headerShown: false,
        })}
      >
        <Tab.Screen name="Home">
          {props => <HomeStackNavigator {...props} userLocation={userLocation} />}
        </Tab.Screen>
        <Tab.Screen name="Chatbot">
          {props => <ChatbotScreen {...props} userLocation={userLocation} />}
        </Tab.Screen>
        <Tab.Screen
          name="VoiceTest"
          options={{ tabBarLabel: '노인맞춤 제어' }}
        >
          {props => <VoiceTestStackNavigator {...props} userLocation={userLocation} />}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  background: { flex: 1 },
  scrollContainer: { alignItems: 'center', paddingVertical: 40 },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  mainSectionWrapper: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '90%',
    alignItems: 'flex-start',
  },
  deviceControlWrapper: {
    width: '45%',
    alignItems: 'center',
  },
  graphSectionWrapper: {
    width: '48%',
    alignItems: 'center',
    marginTop: 30,
    marginRight: -21,
  },
  fab: {
    position: 'absolute',
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  fabIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
  },

  autoModeControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 15,
    gap: 10,
  },
  autoModeToggleButton: {
    flex: 1,
    backgroundColor: 'rgba(0,100,0,0.7)',
    paddingVertical: 12,
    paddingHorizontal: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  autoModeToggleText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  autoModeStatusText: {
    color: '#fff',
    fontSize: 14,
    opacity: 0.9,
    marginTop: 4,
  },
  autoModeSettingsButton: {
    flex: 1,
    backgroundColor: 'rgba(0,100,0,0.7)',
    paddingVertical: 12,
    paddingHorizontal: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  autoModeSettingsText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  autoModeActive: {
    backgroundColor: 'rgba(76,175,80,0.8)',
  },
  autoModeInactive: {
    backgroundColor: 'rgba(244,67,54,0.8)',
  },
});
