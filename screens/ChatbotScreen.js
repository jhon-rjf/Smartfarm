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
  Keyboard,
  ImageBackground,
  Image,
  Alert,
  ActivityIndicator,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { sendChatMessage, analyzeImage, controlDevice, fetchStatus, subscribeToChatSession, getGlobalChatSessionId, subscribeToChatLog, addMessageToGlobalChatLog, getGlobalChatLog, setGlobalChatLog } from '../services/api';

// 모든 명령어는 Gemini API를 통해 자연어 처리됩니다

export default function ChatbotScreen({ navigation, userLocation = '서울' }) {
  const [chatInput, setChatInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [imageUri, setImageUri] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [deviceStatus, setDeviceStatus] = useState(null);
  const [sessionId, setSessionId] = useState(null); // 세션 ID 관리
  const [safeLocation, setSafeLocation] = useState(userLocation || '서울'); // 안전한 위치 상태

  const listRef = useRef(null);

  // 유효하지 않은 위치 문자열 확인 및 안전한 위치 설정
  useEffect(() => {
    if (!userLocation || typeof userLocation !== 'string') {
      console.warn('[ChatbotScreen] 유효하지 않은 위치 정보. 기본값 "서울"을 사용합니다.');
      setSafeLocation('서울');
    } else {
      setSafeLocation(userLocation);
    }
  }, [userLocation]);

  // 전역 채팅 세션 구독
  useEffect(() => {
    console.log('[ChatbotScreen] 전역 세션 구독 시작');
    
    // 현재 전역 세션 ID 가져오기
    const currentGlobalSessionId = getGlobalChatSessionId();
    if (currentGlobalSessionId) {
      console.log('[ChatbotScreen] 기존 전역 세션 ID 적용:', currentGlobalSessionId);
      setSessionId(currentGlobalSessionId);
    }
    
    // 세션 ID 변경 구독
    const unsubscribe = subscribeToChatSession((newSessionId) => {
      console.log('[ChatbotScreen] 전역 세션 ID 변경됨:', newSessionId);
      setSessionId(newSessionId);
    });
    
    return () => {
      console.log('[ChatbotScreen] 전역 세션 구독 해제');
      unsubscribe();
    };
  }, []);

  // 전역 채팅 로그 구독
  useEffect(() => {
    console.log('[ChatbotScreen] 전역 채팅 로그 구독 시작');
    
    // 현재 전역 채팅 로그 가져오기
    const currentGlobalChatLog = getGlobalChatLog();
    if (currentGlobalChatLog.length > 0) {
      console.log('[ChatbotScreen] 기존 전역 채팅 로그 적용:', currentGlobalChatLog.length, '개 메시지');
      setChatLog(currentGlobalChatLog);
    }
    
    // 채팅 로그 변경 구독
    const unsubscribe = subscribeToChatLog((newChatLog) => {
      console.log('[ChatbotScreen] 전역 채팅 로그 변경됨:', newChatLog.length, '개 메시지');
      setChatLog(newChatLog);
    });
    
    return () => {
      console.log('[ChatbotScreen] 전역 채팅 로그 구독 해제');
      unsubscribe();
    };
  }, []);

  // 초기 메시지 설정 및 기기 상태 로드
  useEffect(() => {
    const initializeMessages = async () => {
      // 전역 채팅 로그가 비어있을 때만 초기 메시지 설정
      const currentGlobalChatLog = getGlobalChatLog();
      if (currentGlobalChatLog.length === 0) {
        let initialMessage = `안녕하세요! 스마트 온실 도우미입니다. 무엇을 도와드릴까요?\n\n자연스러운 대화로 기기를 제어하고 온실 관리에 대한 조언을 받을 수 있습니다. 예: "불 켜줘", "습도가 너무 높은데 어떻게 해야 할까?"`;
        
        // 위치 정보가 있으면 추가
        if (userLocation && userLocation !== '서울') {
          initialMessage += `\n\n현재 위치는 ${userLocation}로 설정되어 있습니다. 날씨 정보를 물어보시면 ${userLocation} 지역의 날씨를 알려드립니다.`;
        }
        
        const initialBotMessage = {
          role: 'bot', 
          text: initialMessage
        };
        
        // 전역 채팅 로그에 초기 메시지 설정
        await setGlobalChatLog([initialBotMessage]);
        
        console.log('[ChatbotScreen] 초기 메시지 설정 완료');
      }
    };
    
    initializeMessages();
    
    // 초기 기기 상태 로드
    loadDeviceStatus();
  }, [userLocation]);

  // 기기 상태 로드 함수
  const loadDeviceStatus = async () => {
    try {
      const status = await fetchStatus();
      setDeviceStatus(status.devices);
    } catch (error) {
      console.error('기기 상태 로드 실패:', error);
    }
  };

  const handleImagePick = async () => {
    Alert.alert(
      '이미지 선택',
      '어떤 방법으로 이미지를 추가할까요?',
      [
        {
          text: '📷 사진 촬영',
          onPress: async () => {
            const cameraPerm = await ImagePicker.requestCameraPermissionsAsync();
            if (!cameraPerm.granted) {
              alert('카메라 접근 권한이 필요합니다.');
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
              alert('사진 접근 권한이 필요합니다.');
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
  


  // 이미지 분석 처리 함수
  const handleImageAnalysis = async () => {
    try {
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
      setChatInput(''); // 입력 필드 초기화
      
      // 분석 요청
      const response = await analyzeImage(imageUri, analysisPrompt);
      
      // 봇 응답 추가
      const botMessage = { 
        role: 'bot', 
        text: response.analysis || '이미지 분석 중 오류가 발생했습니다.' 
      };
      await addMessageToGlobalChatLog(botMessage);
    } catch (error) {
      console.error('이미지 분석 처리 오류:', error);
      const errorMessage = { 
        role: 'bot', 
        text: '이미지 분석 중 오류가 발생했습니다. 다시 시도해주세요.' 
      };
      await addMessageToGlobalChatLog(errorMessage);
    } finally {
      setIsLoading(false);
      setImageUri(null);
    }
  };

  // API 응답에서 명령어 태그 제거 함수
  const cleanResponseText = (text) => {
    if (!text) return text;
    
    // [ACTION_XXX] 형태의 태그 제거
    return text.replace(/\[ACTION_[A-Z_]+\]/g, '');
  };

  const handleSend = async () => {
    if (!chatInput.trim() && !imageUri) {
      return; // 빈 메시지와 이미지가 없으면 무시
    }
    
    try {
      // 이미지가 있으면 이미지 분석 처리
      if (imageUri) {
        await handleImageAnalysis();
        return;
      }
      
      const input = chatInput.trim();
      setChatInput(''); // 입력 필드 초기화
      setIsLoading(true);
      
      // 사용자 메시지 추가
      await addMessageToGlobalChatLog({ role: 'user', text: input });
      
      // 모든 메시지를 Gemini API로 전송하여 자연어 처리
      
      // API 서버에 메시지 전송
      try {
        const response = await sendChatMessage(input, sessionId, safeLocation);
        
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
          const botMessage = {
            role: 'bot',
            text: cleanedResponse
          };
          await addMessageToGlobalChatLog(botMessage);
        } else {
          await addMessageToGlobalChatLog({ role: 'bot', text: '죄송합니다. 응답을 받지 못했습니다. 다시 시도해주세요.' });
        }
      } catch (error) {
        console.error('채팅 API 오류:', error);
        await addMessageToGlobalChatLog({ role: 'bot', text: '죄송합니다. 메시지 처리 중 문제가 발생했습니다.' });
      }
    } catch (e) {
      console.error('메시지 전송 오류:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (chatLog.length > 0) {
      listRef.current?.scrollToEnd({ animated: true });
    }
  }, [chatLog]);

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

  const renderItem = ({ item }) => {
    return (
      <View
        style={[
          styles.messageWrapper,
          item.role === 'user' ? styles.userBubble : styles.botBubble,
        ]}
      >
        {/* 이미지 표시 */}
        {item.image && (
          <Image
            source={{ uri: item.image }}
            style={{ width: 200, height: 200, borderRadius: 10, marginBottom: 8 }}
          />
        )}
        
        {/* 텍스트 표시 */}
        {item.text && (
          <Text style={styles.messageText}>
            {item.role === 'user' ? '👤' : '🤖'} {item.role === 'bot' ? convertMarkdownToText(item.text) : item.text}
          </Text>
        )}
        
        {/* 이미지만 있고 텍스트가 없는 경우 */}
        {item.image && !item.text && (
          <Text style={styles.messageText}>
            👤 📷 사진
          </Text>
        )}
      </View>
    );
  };

  return (
    <ImageBackground
      source={require('../assets/greenhouse.png')}
      style={styles.container}
      resizeMode="cover"
    >
      <Text style={styles.title}>Chatbot</Text>

      {isLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#ffffff" />
        </View>
      )}

      <FlatList
        ref={listRef}
        data={chatLog}
        keyExtractor={(_, idx) => idx.toString()}
        renderItem={renderItem}
        contentContainerStyle={styles.chatContent}
        style={styles.chatList}
      />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={80}
      >
        <View style={styles.inputWrapper}>
          <TouchableOpacity style={styles.plusButton} onPress={handleImagePick}>
            <Text style={styles.plusText}>+</Text>
          </TouchableOpacity>

          <View style={styles.inputArea}>
            {imageUri && (
              <View style={styles.imagePreviewContainer}>
                <Image source={{ uri: imageUri }} style={styles.imagePreview} />
              </View>
            )}

            <TextInput
              style={styles.input}
              placeholder="Ask something..."
              placeholderTextColor="rgba(255,255,255,0.7)"
              value={chatInput}
              onChangeText={setChatInput}
              returnKeyType="send"
              onSubmitEditing={handleSend}
            />
          </View>

          <TouchableOpacity style={styles.sendButton} onPress={handleSend} disabled={isLoading}>
            <Text style={styles.sendText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </ImageBackground>
  );
  
}


const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  title: {
    fontSize: 28,
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 12,
  },
  chatList: {
    flex: 1,
    paddingHorizontal: 12,
  },
  chatContent: {
    paddingBottom: 10,
  },
  messageWrapper: {
    padding: 10,
    borderRadius: 8,
    marginVertical: 6,
    maxWidth: '75%',
  },
  userBubble: {
    backgroundColor: '#e0ffe0',
    alignSelf: 'flex-end',
  },
  botBubble: {
    backgroundColor: '#ffffffaa',
    alignSelf: 'flex-start',
  },
  messageText: {
    fontSize: 16,
    color: '#333',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: 'rgba(0,100,0,0.7)',
  },
  plusButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#388e3c',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  plusText: {
    fontSize: 24,
    color: 'white',
    lineHeight: 24,
  },
  inputArea: {
    flex: 1,
    flexDirection: 'column',
  },
  imagePreviewContainer: {
    marginBottom: 4,
    alignSelf: 'flex-start',
  },
  imagePreview: {
    width: 60,
    height: 60,
    borderRadius: 6,
  },
  input: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontSize: 16,
    color: 'white',
  },
  sendButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginLeft: 8,
  },
  sendText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
    zIndex: 999,
  },
  header: {
    backgroundColor: '#fff',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
    flexDirection: 'row',
    alignItems: 'center',
  },
  historyIndicator: {
    backgroundColor: '#ffffffaa',
    padding: 4,
    borderRadius: 4,
    marginTop: 4,
    alignSelf: 'flex-start',
  },
  historyIndicatorText: {
    fontSize: 12,
    color: '#333',
  },
});
