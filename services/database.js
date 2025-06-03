/**
 * SQLite 데이터베이스 서비스
 * 채팅 메시지 영구 저장 및 관리
 */

import * as SQLite from 'expo-sqlite';

// 데이터베이스 인스턴스
let db = null;

// 데이터베이스 초기화
export const initDatabase = async () => {
  try {
    console.log('[Database] 데이터베이스 초기화 시작...');
    
    // 데이터베이스 연결
    db = await SQLite.openDatabaseAsync('smartfarm_chat.db');
    
    console.log('[Database] 데이터베이스 연결 완료');
    
    // 테이블 생성
    await createTables();
    
    console.log('[Database] 데이터베이스 초기화 완료');
    return true;
  } catch (error) {
    console.error('[Database] 데이터베이스 초기화 오류:', error);
    return false;
  }
};

// 테이블 생성
const createTables = async () => {
  try {
    // 채팅 메시지 테이블
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        text TEXT,
        image_uri TEXT,
        session_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        message_order INTEGER
      );
    `);
    
    // 채팅 세션 테이블
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_message_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // RAG 문서 테이블 추가
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS rag_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        keywords TEXT NOT NULL,
        category TEXT NOT NULL,
        vector_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // RAG 검색 기록 테이블
    await db.execAsync(`
      CREATE TABLE IF NOT EXISTS rag_search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        found_documents INTEGER DEFAULT 0,
        search_type TEXT DEFAULT 'similarity',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);
    
    // 인덱스 생성
    await db.execAsync(`
      CREATE INDEX IF NOT EXISTS idx_messages_session_order 
      ON chat_messages(session_id, message_order);
    `);
    
    await db.execAsync(`
      CREATE INDEX IF NOT EXISTS idx_messages_created_at 
      ON chat_messages(created_at);
    `);

    // RAG 관련 인덱스
    await db.execAsync(`
      CREATE INDEX IF NOT EXISTS idx_rag_documents_category 
      ON rag_documents(category);
    `);

    await db.execAsync(`
      CREATE INDEX IF NOT EXISTS idx_rag_documents_title 
      ON rag_documents(title);
    `);

    await db.execAsync(`
      CREATE INDEX IF NOT EXISTS idx_rag_search_query 
      ON rag_search_history(query);
    `);
    
    console.log('[Database] 테이블 생성 완료');
  } catch (error) {
    console.error('[Database] 테이블 생성 오류:', error);
    throw error;
  }
};

// 채팅 메시지 저장
export const saveChatMessage = async (message, sessionId, messageOrder) => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return false;
    }
    
    console.log('[Database] 메시지 저장:', { 
      role: message.role, 
      textLength: message.text?.length || 0,
      hasImage: !!message.image,
      sessionId,
      messageOrder
    });
    
    // 세션 ID가 있으면 세션 테이블 업데이트
    if (sessionId) {
      await db.runAsync(`
        INSERT OR REPLACE INTO chat_sessions (session_id, last_message_at)
        VALUES (?, CURRENT_TIMESTAMP)
      `, [sessionId]);
    }
    
    // 메시지 저장
    const result = await db.runAsync(`
      INSERT INTO chat_messages (role, text, image_uri, session_id, message_order)
      VALUES (?, ?, ?, ?, ?)
    `, [
      message.role,
      message.text || null,
      message.image || null,
      sessionId || null,
      messageOrder
    ]);
    
    console.log('[Database] 메시지 저장 완료, ID:', result.lastInsertRowId);
    return result.lastInsertRowId;
  } catch (error) {
    console.error('[Database] 메시지 저장 오류:', error);
    return false;
  }
};

// 채팅 메시지 전체 조회
export const getAllChatMessages = async () => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return [];
    }
    
    console.log('[Database] 전체 메시지 조회 시작...');
    
    const result = await db.getAllAsync(`
      SELECT role, text, image_uri as image, session_id, created_at, message_order
      FROM chat_messages
      ORDER BY created_at ASC, message_order ASC
    `);
    
    console.log('[Database] 메시지 조회 완료:', result.length, '개');
    
    // image_uri를 image로 변환하고 null 값 처리
    const messages = result.map(row => ({
      role: row.role,
      text: row.text || undefined,
      image: row.image || undefined,
      session_id: row.session_id,
      created_at: row.created_at,
      message_order: row.message_order
    }));
    
    return messages;
  } catch (error) {
    console.error('[Database] 메시지 조회 오류:', error);
    return [];
  }
};

// 특정 세션의 채팅 메시지 조회
export const getChatMessagesBySession = async (sessionId) => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return [];
    }
    
    console.log('[Database] 세션별 메시지 조회:', sessionId);
    
    const result = await db.getAllAsync(`
      SELECT role, text, image_uri as image, session_id, created_at, message_order
      FROM chat_messages
      WHERE session_id = ?
      ORDER BY created_at ASC, message_order ASC
    `, [sessionId]);
    
    console.log('[Database] 세션별 메시지 조회 완료:', result.length, '개');
    
    // image_uri를 image로 변환하고 null 값 처리
    const messages = result.map(row => ({
      role: row.role,
      text: row.text || undefined,
      image: row.image || undefined,
      session_id: row.session_id,
      created_at: row.created_at,
      message_order: row.message_order
    }));
    
    return messages;
  } catch (error) {
    console.error('[Database] 세션별 메시지 조회 오류:', error);
    return [];
  }
};

// 채팅 기록 삭제
export const clearChatHistory = async () => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return false;
    }
    
    console.log('[Database] 채팅 기록 삭제 시작...');
    
    await db.runAsync('DELETE FROM chat_messages');
    await db.runAsync('DELETE FROM chat_sessions');
    
    console.log('[Database] 채팅 기록 삭제 완료');
    return true;
  } catch (error) {
    console.error('[Database] 채팅 기록 삭제 오류:', error);
    return false;
  }
};

// 오래된 메시지 정리 (30일 이상)
export const cleanupOldMessages = async () => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return false;
    }
    
    console.log('[Database] 오래된 메시지 정리 시작...');
    
    const result = await db.runAsync(`
      DELETE FROM chat_messages 
      WHERE created_at < datetime('now', '-30 days')
    `);
    
    await db.runAsync(`
      DELETE FROM chat_sessions 
      WHERE last_message_at < datetime('now', '-30 days')
    `);
    
    console.log('[Database] 오래된 메시지 정리 완료. 삭제된 메시지:', result.changes);
    return result.changes;
  } catch (error) {
    console.error('[Database] 오래된 메시지 정리 오류:', error);
    return false;
  }
};

// 데이터베이스 상태 확인
export const getDatabaseStats = async () => {
  try {
    if (!db) {
      return { messages: 0, sessions: 0, connected: false };
    }
    
    const messageCount = await db.getFirstAsync('SELECT COUNT(*) as count FROM chat_messages');
    const sessionCount = await db.getFirstAsync('SELECT COUNT(*) as count FROM chat_sessions');
    
    return {
      messages: messageCount.count,
      sessions: sessionCount.count,
      connected: true
    };
  } catch (error) {
    console.error('[Database] 상태 확인 오류:', error);
    return { messages: 0, sessions: 0, connected: false };
  }
};

// 데이터베이스 연결 해제
export const closeDatabase = async () => {
  try {
    if (db) {
      await db.closeAsync();
      db = null;
      console.log('[Database] 데이터베이스 연결 해제 완료');
    }
  } catch (error) {
    console.error('[Database] 연결 해제 오류:', error);
  }
};

// RAG 문서 저장
export const saveRAGDocument = async (doc) => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return false;
    }
    
    console.log('[Database] RAG 문서 저장:', doc.title);
    
    const result = await db.runAsync(`
      INSERT OR REPLACE INTO rag_documents (title, content, keywords, category, vector_data)
      VALUES (?, ?, ?, ?, ?)
    `, [
      doc.title,
      doc.content,
      JSON.stringify(doc.keywords),
      doc.category,
      doc.vector_data || null
    ]);
    
    console.log('[Database] RAG 문서 저장 완료, ID:', result.lastInsertRowId);
    return result.lastInsertRowId;
  } catch (error) {
    console.error('[Database] RAG 문서 저장 오류:', error);
    return false;
  }
};

// RAG 문서 전체 조회
export const getAllRAGDocuments = async () => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return [];
    }
    
    console.log('[Database] RAG 문서 전체 조회 시작...');
    
    const result = await db.getAllAsync(`
      SELECT id, title, content, keywords, category, vector_data, created_at, updated_at
      FROM rag_documents
      ORDER BY category, title
    `);
    
    console.log('[Database] RAG 문서 조회 완료:', result.length, '개');
    
    // keywords를 JSON으로 파싱
    const documents = result.map(row => ({
      ...row,
      keywords: JSON.parse(row.keywords)
    }));
    
    return documents;
  } catch (error) {
    console.error('[Database] RAG 문서 조회 오류:', error);
    return [];
  }
};

// 카테고리별 RAG 문서 조회
export const getRAGDocumentsByCategory = async (category) => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return [];
    }
    
    console.log('[Database] 카테고리별 RAG 문서 조회:', category);
    
    const result = await db.getAllAsync(`
      SELECT id, title, content, keywords, category, vector_data, created_at, updated_at
      FROM rag_documents
      WHERE category = ?
      ORDER BY title
    `, [category]);
    
    console.log('[Database] 카테고리별 RAG 문서 조회 완료:', result.length, '개');
    
    const documents = result.map(row => ({
      ...row,
      keywords: JSON.parse(row.keywords)
    }));
    
    return documents;
  } catch (error) {
    console.error('[Database] 카테고리별 RAG 문서 조회 오류:', error);
    return [];
  }
};

// RAG 검색 기록 저장
export const saveRAGSearchHistory = async (query, foundDocuments, searchType = 'similarity') => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return false;
    }
    
    const result = await db.runAsync(`
      INSERT INTO rag_search_history (query, found_documents, search_type)
      VALUES (?, ?, ?)
    `, [query, foundDocuments, searchType]);
    
    return result.lastInsertRowId;
  } catch (error) {
    console.error('[Database] RAG 검색 기록 저장 오류:', error);
    return false;
  }
};

// RAG 검색 기록 조회 (최근 20개)
export const getRAGSearchHistory = async () => {
  try {
    if (!db) {
      console.warn('[Database] 데이터베이스가 초기화되지 않았습니다.');
      return [];
    }
    
    const result = await db.getAllAsync(`
      SELECT query, found_documents, search_type, created_at
      FROM rag_search_history
      ORDER BY created_at DESC
      LIMIT 20
    `);
    
    return result;
  } catch (error) {
    console.error('[Database] RAG 검색 기록 조회 오류:', error);
    return [];
  }
};

// RAG 데이터베이스 통계
export const getRAGStats = async () => {
  try {
    if (!db) {
      return { documents: 0, categories: 0, searches: 0 };
    }
    
    const docCount = await db.getFirstAsync('SELECT COUNT(*) as count FROM rag_documents');
    const categoryCount = await db.getFirstAsync('SELECT COUNT(DISTINCT category) as count FROM rag_documents');
    const searchCount = await db.getFirstAsync('SELECT COUNT(*) as count FROM rag_search_history');
    
    return {
      documents: docCount.count,
      categories: categoryCount.count,
      searches: searchCount.count
    };
  } catch (error) {
    console.error('[Database] RAG 통계 조회 오류:', error);
    return { documents: 0, categories: 0, searches: 0 };
  }
}; 