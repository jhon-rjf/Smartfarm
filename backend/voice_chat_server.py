import asyncio
import base64
import json
import os
import logging
from websockets.server import serve
from websockets.client import connect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiVoiceServer:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash-exp"
        self.gemini_uri = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={self.api_key}"
        self.active_connections = {}
        
    def get_system_instruction(self, persona="친근한_어시스턴트"):
        personas = {
            "친근한_어시스턴트": """당신은 스마트팜을 제어할 수 있는 AI 어시스턴트입니다. 
            
특징:
- 항상 한국어로 대화합니다
- 당신은 스마트팜을 제어할 수 있는 AI 어시스턴트입니다.
- 스마트팜에서 일어날 수 있는 다양한 것들에 대해서 설명합니다.
- 친근하고 따뜻한 말투를 사용합니다
- 질문에 명확하고 간결하게 답변합니다
- 모르는 것은 솔직히 모른다고 말합니다
- 대화를 자연스럽게 이어갑니다"""
        }
        
        return personas.get(persona, personas["친근한_어시스턴트"])

    async def handle_client(self, websocket, path):
        """클라이언트 WebSocket 연결 처리"""
        client_id = id(websocket)
        logger.info(f"클라이언트 연결: {client_id}")
        
        try:
            # Gemini와 연결
            gemini_ws = await connect(
                self.gemini_uri,
                extra_headers={"Content-Type": "application/json"}
            )
            
            # System instruction 설정
            setup_message = {
                "setup": {
                    "model": f"models/{self.model}",
                    "system_instruction": {
                        "parts": [{
                            "text": self.get_system_instruction()
                        }]
                    }
                }
            }
            
            await gemini_ws.send(json.dumps(setup_message))
            await gemini_ws.recv()
            
            # 연결 정보 저장
            self.active_connections[client_id] = {
                "websocket": websocket,
                "gemini_ws": gemini_ws,
                "model_speaking": False
            }
            
            await websocket.send(json.dumps({
                "type": "connected",
                "message": "Voice chat ready!"
            }))
            
            # 동시에 처리할 태스크들
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.handle_client_messages(client_id))
                tg.create_task(self.handle_gemini_responses(client_id))
                
        except Exception as e:
            logger.error(f"클라이언트 처리 오류: {e}")
        finally:
            await self.cleanup_connection(client_id)

    async def handle_client_messages(self, client_id):
        """클라이언트로부터 메시지 처리"""
        connection = self.active_connections.get(client_id)
        if not connection:
            return
            
        websocket = connection["websocket"]
        gemini_ws = connection["gemini_ws"]
        
        try:
            async for message in websocket:
                data = json.loads(message)
                logger.info(f"클라이언트 {client_id}로부터 메시지 수신: {data.get('type')}")
                
                if data.get("type") == "audio":
                    # 모델이 말하고 있지 않을 때만 오디오 전송
                    if not connection["model_speaking"]:
                        audio_data = data.get("audio")
                        if audio_data:
                            logger.info(f"클라이언트 {client_id}의 오디오 데이터를 Gemini로 전송 (크기: {len(audio_data)})")
                            await gemini_ws.send(json.dumps({
                                "realtime_input": {
                                    "media_chunks": [{
                                        "data": audio_data,
                                        "mime_type": "audio/pcm",
                                    }]
                                }
                            }))
                    else:
                        logger.info(f"클라이언트 {client_id}: 모델이 말하는 중이므로 오디오 무시")
                elif data.get("type") == "stop":
                    logger.info(f"클라이언트 {client_id}: 연결 중지 요청")
                    break
                    
        except Exception as e:
            logger.error(f"클라이언트 메시지 처리 오류: {e}")

    async def handle_gemini_responses(self, client_id):
        """Gemini 응답 처리 후 클라이언트로 전송"""
        connection = self.active_connections.get(client_id)
        if not connection:
            return
            
        websocket = connection["websocket"]
        gemini_ws = connection["gemini_ws"]
        
        try:
            async for msg in gemini_ws:
                response = json.loads(msg)
                logger.info(f"Gemini로부터 응답 수신: {list(response.keys())}")
                
                try:
                    audio_data = response["serverContent"]["modelTurn"]["parts"][0]["inlineData"]["data"]
                    if not connection["model_speaking"]:
                        connection["model_speaking"] = True
                        logger.info(f"클라이언트 {client_id}: AI 응답 시작")
                        await websocket.send(json.dumps({
                            "type": "speaking_start",
                            "message": "AI가 말하기 시작했습니다"
                        }))
                    
                    logger.info(f"클라이언트 {client_id}로 오디오 데이터 전송 (크기: {len(audio_data)})")
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "audio": audio_data
                    }))
                    
                except KeyError:
                    # 오디오 데이터가 없는 경우
                    pass
                
                try:
                    turn_complete = response["serverContent"]["turnComplete"]
                except KeyError:
                    pass
                else:
                    if turn_complete:
                        connection["model_speaking"] = False
                        logger.info(f"클라이언트 {client_id}: AI 응답 완료")
                        await websocket.send(json.dumps({
                            "type": "speaking_end",
                            "message": "AI가 말하기를 마쳤습니다"
                        }))
                        
        except Exception as e:
            logger.error(f"Gemini 응답 처리 오류: {e}")

    async def cleanup_connection(self, client_id):
        """연결 정리"""
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            try:
                if connection.get("gemini_ws"):
                    await connection["gemini_ws"].close()
            except:
                pass
            del self.active_connections[client_id]
        logger.info(f"클라이언트 연결 정리 완료: {client_id}")

    async def start_server(self, host="0.0.0.0", port=8766):
        """WebSocket 서버 시작"""
        logger.info(f"Voice WebSocket 서버 시작: {host}:{port}")
        async with serve(self.handle_client, host, port):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    server = GeminiVoiceServer()
    asyncio.run(server.start_server()) 