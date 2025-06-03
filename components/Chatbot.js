// components/Chatbot.js
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Image,
  Keyboard,
} from 'react-native';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';

export default function Chatbot() {
  const [chatInput, setChatInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [image, setImage] = useState(null);
  const [showOptions, setShowOptions] = useState(false);

  const handleSend = () => {
    if (chatInput.trim() === '' && !image) return;
    const userMsg = { role: 'user', text: chatInput, image };
    const botMsg = {
      role: 'bot',
      text: image ? '🤖 사진을 잘 받았습니다!' : `🤖 "${chatInput}"에 대한 응답입니다.`,
    };
    setChatLog(prev => [...prev, userMsg, botMsg]);
    setChatInput('');
    setImage(null);
    setShowOptions(false);
    Keyboard.dismiss();
  };

  const pickImage = () => {
    launchImageLibrary({ mediaType: 'photo', quality: 0.7 }, res => {
      if (res.assets?.[0]?.uri) {
        setImage(res.assets[0].uri);
        setShowOptions(false);
      }
    });
  };

  const takePhoto = () => {
    launchCamera({ mediaType: 'photo', quality: 0.7 }, res => {
      if (res.assets?.[0]?.uri) {
        setImage(res.assets[0].uri);
        setShowOptions(false);
      }
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Chatbot</Text>

      <ScrollView
        style={styles.logWrapper}
        contentContainerStyle={styles.logContent}
      >
        {chatLog.map((msg, i) => (
          <View
            key={i}
            style={[
              styles.messageWrapper,
              msg.role === 'user' ? styles.userBubble : styles.botBubble,
            ]}
          >
            {msg.image && (
              <Image source={{ uri: msg.image }} style={styles.msgImage} />
            )}
            <Text style={styles.msgText}>
              {msg.role === 'user' ? '👤' : '🤖'} {msg.text}
            </Text>
          </View>
        ))}
      </ScrollView>

      {showOptions && (
        <View style={styles.optionsRow}>
          <TouchableOpacity style={styles.optionBtn} onPress={takePhoto}>
            <Text style={styles.optionText}>📸 카메라</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.optionBtn} onPress={pickImage}>
            <Text style={styles.optionText}>🖼️ 앨범</Text>
          </TouchableOpacity>
        </View>
      )}

      {image && (
        <View style={styles.previewRow}>
          <Image source={{ uri: image }} style={styles.previewImage} />
        </View>
      )}

      <View style={styles.inputRow}>
        {/* + 버튼 */}
        <TouchableOpacity
          style={styles.plusBtn}
          onPress={() => setShowOptions(prev => !prev)}
        >
          <Text style={styles.plusText}>＋</Text>
        </TouchableOpacity>

        {/* 텍스트 입력 */}
        <TextInput
          style={styles.input}
          placeholder="Ask something..."
          placeholderTextColor="#aaa"
          value={chatInput}
          onChangeText={setChatInput}
          onSubmitEditing={handleSend}
          returnKeyType="send"
        />

        {/* Send 버튼 */}
        <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
          <Text style={styles.sendText}>Send</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,                         // 화면 가득 채우기
    backgroundColor: 'rgba(0,100,0,0.7)',
    borderRadius: 10,
    padding: 15,
    marginTop: 20,
    width: '80%',
  },
  title: {
    fontSize: 30,
    color: 'white',
    marginBottom: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  logWrapper: {
    flex: 1,                        // 남은 공간 모두 사용
  },
  logContent: {
    paddingBottom: 10,
  },
  messageWrapper: {
    padding: 8,
    borderRadius: 8,
    marginBottom: 6,
    maxWidth: '80%',
  },
  userBubble: {
    backgroundColor: '#e0ffe0',
    alignSelf: 'flex-end',
  },
  botBubble: {
    backgroundColor: '#ffffffaa',
    alignSelf: 'flex-start',
  },
  msgText: {
    fontSize: 14,
    color: '#333',
  },
  msgImage: {
    width: 120,
    height: 120,
    borderRadius: 8,
    marginBottom: 4,
  },
  optionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginVertical: 10,
  },
  optionBtn: {
    backgroundColor: 'white',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  optionText: {
    color: '#4CAF50',
    fontSize: 14,
    fontWeight: '600',
  },
  previewRow: {
    alignItems: 'center',
    marginBottom: 10,
  },
  previewImage: {
    width: 200,
    height: 200,
    borderRadius: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  plusBtn: {
    backgroundColor: 'white',
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    // 만약 그래도 보이지 않으면 아래 두 줄을 주석 해제해보세요.
    // borderWidth: 1,
    // borderColor: 'red',
  },
  plusText: {
    fontSize: 24,
    color: '#4CAF50',
    lineHeight: 24,
  },
  input: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontSize: 16,
    marginRight: 8,
  },
  sendBtn: {
    backgroundColor: '#4CAF50',
    borderRadius: 20,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  sendText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
