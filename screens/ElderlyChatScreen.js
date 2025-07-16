import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
  Dimensions,
  Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { sendChatMessage, analyzeImage, controlDevice, fetchStatus, subscribeToChatSession, getGlobalChatSessionId, subscribeToChatLog, addMessageToGlobalChatLog, getGlobalChatLog, setGlobalChatLog } from '../services/api';

const { width, height } = Dimensions.get('window');

// 화면 크기에 비례한 크기 계산 함수
const scale = (size) => (width / 320) * size;
const verticalScale = (size) => (height / 568) * size;
const moderateScale = (size, factor = 0.5) => size + (scale(size) - size) * factor;

// 명령어 인식을 위한 패턴
const COMMAND_PATTERNS = {
  // 불/조명 제어
  LIGHT_ON: /(불|조명|전등|라이트)[\s]*(켜|켜줘|켜주세요|켜주실래요|켜줄래요|턴온|turn on)/i,
  LIGHT_OFF: /(불|조명|전등|라이트)[\s]*(꺼|꺼줘|꺼주세요|꺼주실래요|꺼줄래요|턴오프|turn off)/i,
  
  // 팬 제어
  FAN_ON: /(팬|선풍기|환풍기)[\s]*(켜|켜줘|켜주세요|켜주실래요|켜줄래요|턴온|turn on)/i,
  FAN_OFF: /(팬|선풍기|환풍기)[\s]*(꺼|꺼줘|꺼주세요|꺼주실래요|꺼줄래요|턴오프|turn off)/i,
    
  // 물/펌프 제어
  WATER_ON: /(물|펌프|워터펌프|급수)[\s]*(켜|켜줘|켜주세요|켜주실래요|켜줄래요|턴온|turn on|공급|공급해줘|공급해주세요)/i,
  WATER_OFF: /(물|펌프|워터펌프|급수)[\s]*(꺼|꺼줘|꺼주세요|꺼주실래요|꺼줄래요|턴오프|turn off|중단|중단해줘|중단해주세요)/i,
  
  // 창문 제어
  WINDOW_OPEN: /(창문|윈도우)[\s]*(열어|열어줘|열어주세요|열어주실래요|열어줄래요|오픈|open)/i,
  WINDOW_CLOSE: /(창문|윈도우)[\s]*(닫아|닫아줘|닫아주세요|닫아주실래요|닫아줄래요|클로즈|close)/i,
};

export default function ElderlyChatScreen({ navigation, userLocation = '서울' }) {
  const [chatInput, setChatInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [imageUri, setImageUri] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [safeLocation, setSafeLocation] = useState(userLocation || '서울');
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  const listRef = useRef(null);

  // 유효하지 않은 위치 문자열 확인 및 안전한 위치 설정
  useEffect(() => {
    if (!userLocation || typeof userLocation !== 'string') {
      console.warn('[ElderlyChatScreen] 유효하지 않은 위치 정보. 기본값 "서울"을 사용합니다.');
      setSafeLocation('서울');
    } else {
      setSafeLocation(userLocation);
    }
  }, [userLocation]);

  // imageUri 상태 변화 추적
  useEffect(() => {
    console.log('[ElderlyChatScreen] imageUri 상태 변화:', imageUri);
  }, [imageUri]);

  // 전역 채팅 세션 구독
  useEffect(() => {
    console.log('[ElderlyChatScreen] 전역 세션 구독 시작');
    
    // 현재 전역 세션 ID 가져오기
    const currentGlobalSessionId = getGlobalChatSessionId();
    if (currentGlobalSessionId) {
      console.log('[ElderlyChatScreen] 기존 전역 세션 ID 적용:', currentGlobalSessionId);
      setSessionId(currentGlobalSessionId);
    }
    
    // 세션 ID 변경 구독
    const unsubscribe = subscribeToChatSession((newSessionId) => {
      console.log('[ElderlyChatScreen] 전역 세션 ID 변경됨:', newSessionId);
      setSessionId(newSessionId);
    });
    
    return () => {
      console.log('[ElderlyChatScreen] 전역 세션 구독 해제');
      unsubscribe();
    };
  }, []);

  // 전역 채팅 로그 구독
  useEffect(() => {
    console.log('[ElderlyChatScreen] 전역 채팅 로그 구독 시작');
    
    // 현재 전역 채팅 로그 가져오기
    const currentGlobalChatLog = getGlobalChatLog();
    if (currentGlobalChatLog.length > 0) {
      console.log('[ElderlyChatScreen] 기존 전역 채팅 로그 적용:', currentGlobalChatLog.length, '개 메시지');
      setChatLog(currentGlobalChatLog);
    }
    
    // 채팅 로그 변경 구독
    const unsubscribe = subscribeToChatLog((newChatLog) => {
      console.log('[ElderlyChatScreen] 전역 채팅 로그 변경됨:', newChatLog.length, '개 메시지');
      setChatLog(newChatLog);
    });
    
    return () => {
      console.log('[ElderlyChatScreen] 전역 채팅 로그 구독 해제');
      unsubscribe();
    };
  }, []);

  // 초기 메시지 설정 및 기기 상태 로드
  useEffect(() => {
    const initializeMessages = async () => {
      // 전역 채팅 로그가 비어있을 때만 초기 메시지 설정 (ChatbotScreen과 동일한 메시지 사용)
      const currentGlobalChatLog = getGlobalChatLog();
      if (currentGlobalChatLog.length === 0) {
        let initialMessage = `안녕하세요! 스마트 온실 도우미입니다. 무엇을 도와드릴까요?\n\n불 켜줘, 팬 꺼줘 등의 명령으로 기기를 제어할 수 있습니다.`;
        
        // 위치 정보가 있으면 추가
        if (safeLocation && safeLocation !== '서울') {
          initialMessage += `\n\n현재 위치는 ${safeLocation}로 설정되어 있습니다. 날씨 정보를 물어보시면 ${safeLocation} 지역의 날씨를 알려드립니다.`;
        }
        
        const initialBotMessage = {
          role: 'bot', 
          text: initialMessage
        };
        
        // 전역 채팅 로그에 초기 메시지 설정
        await setGlobalChatLog([initialBotMessage]);
        
        console.log('[ElderlyChatScreen] 초기 메시지 설정 완료');
      }
    };
    
    initializeMessages();
    
    // 초기 기기 상태 로드
    loadDeviceStatus();
  }, [safeLocation]);

  // 기기 상태 로드 함수
  const loadDeviceStatus = async () => {
    try {
      const status = await fetchStatus();
      setDeviceStatus(status.devices);
    } catch (error) {
      console.error('기기 상태 로드 실패:', error);
    }
  };

  // 장치 제어 명령 인식 및 처리
  const processDeviceCommand = async (message) => {
    let commandDetected = false;
    let responseText = '';
    let controlSuccess = false;
    
    // 조명 켜기 명령
    if (COMMAND_PATTERNS.LIGHT_ON.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('light', true);
        if (response.success) {
          responseText = '네! 조명을 켰습니다 💡';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '조명을 켜는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '조명 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 조명 끄기
    else if (COMMAND_PATTERNS.LIGHT_OFF.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('light', false);
        if (response.success) {
          responseText = '네! 조명을 껐습니다';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '조명을 끄는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '조명 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 팬 켜기
    else if (COMMAND_PATTERNS.FAN_ON.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('fan', true);
        if (response.success) {
          responseText = '네! 환풍기를 켰습니다 🌀';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '환풍기를 켜는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '환풍기 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 팬 끄기
    else if (COMMAND_PATTERNS.FAN_OFF.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('fan', false);
        if (response.success) {
          responseText = '네! 환풍기를 껐습니다';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '환풍기를 끄는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '환풍기 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 물주기 켜기
    else if (COMMAND_PATTERNS.WATER_ON.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('water', true);
        if (response.success) {
          responseText = '네! 물주기를 시작했습니다 💧';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '물주기를 시작하는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '물주기 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 물주기 끄기
    else if (COMMAND_PATTERNS.WATER_OFF.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('water', false);
        if (response.success) {
          responseText = '네! 물주기를 중단했습니다';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '물주기를 중단하는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '물주기 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 창문 열기
    else if (COMMAND_PATTERNS.WINDOW_OPEN.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('window', true);
        if (response.success) {
          responseText = '네! 창문을 열었습니다 🪟';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '창문을 여는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '창문 제어 중 오류가 발생했습니다.';
      }
    }
    
    // 창문 닫기
    else if (COMMAND_PATTERNS.WINDOW_CLOSE.test(message)) {
      commandDetected = true;
      try {
        const response = await controlDevice('window', false);
        if (response.success) {
          responseText = '네! 창문을 닫았습니다';
          setDeviceStatus(response.devices);
          controlSuccess = true;
        } else {
          responseText = '창문을 닫는데 문제가 생겼어요. 다시 말씀해주세요.';
        }
      } catch (error) {
        responseText = '창문 제어 중 오류가 발생했습니다.';
      }
    }
    
    return {
      detected: commandDetected,
      response: responseText,
      success: controlSuccess
    };
  };

  const handleImagePick = async () => {
    Alert.alert(
      '사진 선택',
      '어떻게 사진을 추가할까요?',
      [
        {
          text: '📷 사진 찍기',
          onPress: async () => {
            const cameraPerm = await ImagePicker.requestCameraPermissionsAsync();
            if (!cameraPerm.granted) {
              Alert.alert('알림', '카메라 사용 권한이 필요합니다.');
              return;
            }
            const result = await ImagePicker.launchCameraAsync({
              mediaTypes: ImagePicker.MediaTypeOptions.Images,
              quality: 0.5,
              allowsEditing: true,
              aspect: [1, 1],
              maxWidth: 800,
              maxHeight: 800,
            });

            if (!result.canceled) {
              setImageUri(result.assets[0].uri);
            }
          },
        },
        {
          text: '🖼 앨범에서 선택',
          onPress: async () => {
            const galleryPerm = await ImagePicker.requestMediaLibraryPermissionsAsync();
            if (!galleryPerm.granted) {
              Alert.alert('알림', '사진 접근 권한이 필요합니다.');
              return;
            }
            const result = await ImagePicker.launchImageLibraryAsync({
              mediaTypes: ImagePicker.MediaTypeOptions.Images,
              quality: 0.5,
              allowsEditing: true,
              aspect: [1, 1],
              maxWidth: 800,
              maxHeight: 800,
            });

            if (!result.canceled) {
              setImageUri(result.assets[0].uri);
            }
          },
        },
        {
          text: '취소',
          style: 'cancel',
        },
      ],
      { cancelable: true }
    );
  };

  const handleImageAnalysis = async () => {
    try {
      console.log('[handleImageAnalysis] 이미지 분석 시작, imageUri:', imageUri);
      setIsLoading(true);
      
      // 사용자 메시지 추가 (이미지와 텍스트가 있으면 둘 다 표시)
      const userMessage = {
        role: 'user',
        image: imageUri,
        text: chatInput || undefined
      };
      await addMessageToGlobalChatLog(userMessage);
      
      // 프롬프트 설정
      const analysisPrompt = chatInput || '이 이미지의 온실 식물 상태를 분석하고 조언해주세요.';
      console.log('[handleImageAnalysis] 프롬프트:', analysisPrompt);
      setChatInput(''); // 입력 필드 초기화
      
      // 분석 요청
      console.log('[handleImageAnalysis] API 호출 시작...');
      const response = await analyzeImage(imageUri, analysisPrompt);
      console.log('[handleImageAnalysis] API 응답 받음:', response);
      
      // 봇 응답 추가
      const botMessage = { 
        role: 'bot', 
        text: response.analysis || '이미지 분석 중 오류가 발생했습니다.' 
      };
      await addMessageToGlobalChatLog(botMessage);
    } catch (error) {
      console.error('[handleImageAnalysis] 이미지 분석 처리 오류:', error);
      const errorMessage = { 
        role: 'bot', 
        text: '이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요.' 
      };
      await addMessageToGlobalChatLog(errorMessage);
    } finally {
      console.log('[handleImageAnalysis] finally 블록 실행 - 이미지 제거 시작');
      setIsLoading(false);
      setImageUri(null);
      console.log('[handleImageAnalysis] 이미지 제거 완료');
    }
  };

  const handleSend = async () => {
    if (!chatInput.trim() && !imageUri) {
      return; // 빈 메시지와 이미지가 없으면 무시
    }

    // 이미지가 있으면 이미지 분석 처리
    if (imageUri) {
      console.log('[handleSend] 이미지 분석 호출 전 imageUri:', imageUri);
      await handleImageAnalysis();
      // 추가 안전장치: 여기서도 이미지 제거
      console.log('[handleSend] 이미지 분석 완료 후 추가 제거');
      setImageUri(null);
      return;
    }

    const userInput = chatInput.trim();
    setChatInput('');

    // 사용자 메시지 추가
    const userMessage = {
      role: 'user',
      text: userInput,
    };
    await addMessageToGlobalChatLog(userMessage);

    setIsLoading(true);

    try {
      // 먼저 기기 제어 명령인지 확인
      const deviceCommand = await processDeviceCommand(userInput);
      
      if (deviceCommand.detected) {
        // 기기 제어 명령이면 바로 응답
        const botMessage = {
          role: 'bot',
          text: deviceCommand.response,
        };
        await addMessageToGlobalChatLog(botMessage);
      } else {
        // API 서버에 메시지 전송
        try {
          const response = await sendChatMessage(userInput, sessionId, safeLocation);
          
          if (response && response.response) {
            // 세션 ID 저장
            if (response.session_id) {
              setSessionId(response.session_id);
            }

            // 액션 태그 제거하고 봇 응답 추가
            const cleanedResponse = cleanResponseText(response.response);
            
            // 명령어 실행이 감지되면 디바이스 상태 업데이트
            if (response.response.includes('[ACTION_')) {
              // 팬 켜기 명령 감지
              if (response.response.includes('[ACTION_FAN_ON]')) {
                await controlDevice('fan', true);
              }
              // 팬 끄기 명령 감지
              else if (response.response.includes('[ACTION_FAN_OFF]')) {
                await controlDevice('fan', false);
              }
              // 물 공급 켜기 명령 감지
              else if (response.response.includes('[ACTION_WATER_ON]')) {
                await controlDevice('water', true);
              }
              // 물 공급 끄기 명령 감지
              else if (response.response.includes('[ACTION_WATER_OFF]')) {
                await controlDevice('water', false);
              }
              // 조명 켜기 명령 감지
              else if (response.response.includes('[ACTION_LIGHT_ON]')) {
                await controlDevice('light', true);
              }
              // 조명 끄기 명령 감지
              else if (response.response.includes('[ACTION_LIGHT_OFF]')) {
                await controlDevice('light', false);
              }
              // 창문 열기 명령 감지
              else if (response.response.includes('[ACTION_WINDOW_OPEN]')) {
                await controlDevice('window', true);
              }
              // 창문 닫기 명령 감지
              else if (response.response.includes('[ACTION_WINDOW_CLOSE]')) {
                await controlDevice('window', false);
              }
              
              // 디바이스 상태 다시 로드
              await loadDeviceStatus();
            }
            
            // 봇 응답 추가
            const convertedResponse = convertMarkdownToText(cleanedResponse);
            const botMessage = {
              role: 'bot',
              text: convertedResponse
            };
            await addMessageToGlobalChatLog(botMessage);
          } else {
            await addMessageToGlobalChatLog({ role: 'bot', text: '죄송합니다. 응답을 받지 못했습니다. 다시 시도해주세요.' });
          }
        } catch (error) {
          console.error('채팅 API 오류:', error);
          await addMessageToGlobalChatLog({ role: 'bot', text: '죄송합니다. 메시지 처리 중 문제가 발생했습니다.' });
        }
      }
    } catch (error) {
      console.error('메시지 전송 오류:', error);
      const errorMessage = {
        role: 'bot',
        text: '네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
      };
      await addMessageToGlobalChatLog(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const cleanResponseText = (text) => {
    if (!text) return text;
    
    // [ACTION_XXX] 형태의 태그 제거
    return text.replace(/\[ACTION_[A-Z_]+\]/g, '');
  };

  // 마크다운을 일반 텍스트로 변환하는 함수
  const convertMarkdownToText = (text) => {
    if (!text) return text;
    
    return text
      // 볼드 텍스트 (**text** -> text)
      .replace(/\*\*(.*?)\*\*/g, '$1')
      // 이탤릭 텍스트 (*text* -> text)
      .replace(/\*(.*?)\*/g, '$1')
      // 헤더 (### -> 없음)
      .replace(/#{1,6}\s*/g, '')
      // 코드 블록 (```code``` -> code)
      .replace(/```[\s\S]*?```/g, (match) => match.replace(/```/g, ''))
      // 인라인 코드 (`code` -> code)
      .replace(/`(.*?)`/g, '$1')
      // 링크 ([text](url) -> text)
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // 리스트 마커 (- -> •)
      .replace(/^[\s]*-\s/gm, '• ')
      .replace(/^[\s]*\*\s/gm, '• ')
      // 숫자 리스트 (1. -> 1. 유지)
      .replace(/^[\s]*(\d+)\.\s/gm, '$1. ')
      // 줄바꿈 정리
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  };

  const renderItem = ({ item }) => (
    <View style={[
      styles.messageContainer,
      item.role === 'user' ? styles.userMessage : styles.botMessage
    ]}>
      {/* 이미지 표시 */}
      {item.image && (
        <Image
          source={{ uri: item.image }}
          style={styles.messageImage}
        />
      )}
      
      {/* 텍스트 표시 */}
      {item.text && (
        <Text style={[
          styles.messageText,
          item.role === 'user' ? styles.userMessageText : styles.botMessageText
        ]}>
          {item.text}
        </Text>
      )}

      {/* 이미지만 있고 텍스트가 없는 경우 */}
      {item.image && !item.text && (
        <Text style={[
          styles.messageText,
          item.role === 'user' ? styles.userMessageText : styles.botMessageText
        ]}>
          사진
        </Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {/* 헤더 */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.backButtonText}>← 뒤로가기</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>스마트팜 도우미</Text>
      </View>

      {/* 채팅 영역 */}
      <View style={styles.chatContainer}>
        <FlatList
          ref={listRef}
          data={chatLog}
          renderItem={renderItem}
          keyExtractor={(_, index) => index.toString()}
          contentContainerStyle={styles.chatList}
          onContentSizeChange={() => {
            if (!isUserScrolling) {
              listRef.current?.scrollToEnd({ animated: true });
            }
          }}
          onScroll={(event) => {
            const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
            // 사용자가 맨 아래에서 20px 이상 위로 스크롤하면 사용자 스크롤 중으로 판단
            if (contentOffset.y < contentSize.height - layoutMeasurement.height - 20) {
              setIsUserScrolling(true);
            } else {
              setIsUserScrolling(false);
            }
          }}
          scrollEventThrottle={16}
          showsVerticalScrollIndicator={false}
        />

        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#4CAF50" />
            <Text style={styles.loadingText}>답변을 생각하고 있어요...</Text>
          </View>
        )}
      </View>

      {/* 입력 영역 */}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.inputContainer}
      >
        <View style={styles.inputWrapper}>
          {/* 이미지 미리보기 추가 */}
          {imageUri && (
            <View style={styles.imagePreviewContainer}>
              <Image source={{ uri: imageUri }} style={styles.imagePreview} />
              <TouchableOpacity
                style={styles.removeImageButtonSmall}
                onPress={() => setImageUri(null)}
              >
                <Text style={styles.removeImageTextSmall}>✕</Text>
              </TouchableOpacity>
            </View>
          )}

          <TextInput
            style={styles.textInput}
            value={chatInput}
            onChangeText={setChatInput}
            placeholder="여기에 질문을 입력하세요..."
            placeholderTextColor="#999"
            multiline
            maxLength={500}
          />
          
          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={styles.imageButton}
              onPress={handleImagePick}
            >
              <Text style={styles.buttonText}>사진</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.sendButton}
              onPress={handleSend}
              disabled={isLoading}
            >
              <Text style={styles.sendButtonText}>전송</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#e0e0e0',
  },
  header: {
    backgroundColor: '#fff',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backButton: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    paddingHorizontal: scale(8),
    paddingVertical: verticalScale(6),
    borderRadius: moderateScale(6),
    minWidth: scale(60),
    maxWidth: scale(80),
  },
  backButtonText: {
    color: '#333',
    fontSize: moderateScale(14),
    fontWeight: 'bold',
    textAlign: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: moderateScale(24),
    fontWeight: 'bold',
    color: '#333',
    textAlign: 'center',
    marginHorizontal: scale(10),
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  chatList: {
    padding: scale(10),
    paddingBottom: verticalScale(15),
  },
  messageContainer: {
    marginVertical: verticalScale(6),
    paddingHorizontal: scale(12),
    paddingVertical: verticalScale(10),
    borderRadius: moderateScale(12),
    maxWidth: '85%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#4CAF50',
  },
  botMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderWidth: 2,
    borderColor: '#ddd',
  },
  messageText: {
    fontSize: moderateScale(16),
    lineHeight: moderateScale(22),
  },
  userMessageText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  botMessageText: {
    color: '#333',
  },
  messageImage: {
    width: scale(150),
    height: scale(150),
    borderRadius: moderateScale(8),
    marginBottom: verticalScale(6),
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: verticalScale(15),
  },
  loadingText: {
    marginTop: verticalScale(8),
    fontSize: moderateScale(16),
    color: '#666',
  },
  inputContainer: {
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  inputWrapper: {
    padding: scale(12),
  },
  imagePreviewContainer: {
    position: 'relative',
    marginBottom: verticalScale(8),
    alignSelf: 'flex-start',
  },
  imagePreview: {
    width: scale(60),
    height: scale(60),
    borderRadius: moderateScale(6),
  },
  removeImageButtonSmall: {
    position: 'absolute',
    top: -scale(5),
    right: -scale(5),
    backgroundColor: '#f44336',
    borderRadius: moderateScale(10),
    width: scale(20),
    height: scale(20),
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeImageTextSmall: {
    color: '#fff',
    fontSize: moderateScale(10),
    fontWeight: 'bold',
  },
  textInput: {
    backgroundColor: '#f9f9f9',
    borderRadius: moderateScale(10),
    paddingHorizontal: scale(12),
    paddingVertical: verticalScale(10),
    fontSize: moderateScale(16),
    maxHeight: verticalScale(100),
    textAlignVertical: 'top',
    borderWidth: 2,
    borderColor: '#ddd',
    marginBottom: verticalScale(8),
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: scale(8),
  },
  imageButton: {
    flex: 1,
    backgroundColor: '#2196F3',
    paddingVertical: verticalScale(12),
    paddingHorizontal: scale(16),
    borderRadius: moderateScale(10),
    alignItems: 'center',
  },
  sendButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    paddingVertical: verticalScale(12),
    paddingHorizontal: scale(16),
    borderRadius: moderateScale(10),
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: moderateScale(16),
    fontWeight: 'bold',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: moderateScale(16),
    fontWeight: 'bold',
  },
  historyIndicator: {
    backgroundColor: '#4CAF50',
    padding: scale(4),
    borderRadius: moderateScale(4),
    marginTop: verticalScale(4),
  },
  historyIndicatorText: {
    color: '#fff',
    fontSize: moderateScale(12),
    fontWeight: 'bold',
  },
}); 