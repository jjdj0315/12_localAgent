# DBeaver로 PostgreSQL 연결하기

## 📋 연결 정보

```
Host: localhost
Port: 5432
Database: llm_webapp
Username: llm_app
Password: TestPassword123!
```

## 🔧 DBeaver 연결 설정 단계

### 1단계: 새 연결 생성

1. DBeaver를 실행합니다
2. 좌측 상단의 **"새 데이터베이스 연결"** 버튼을 클릭하거나
   - 메뉴: `Database` → `New Database Connection`
   - 단축키: `Ctrl + Shift + N` (Windows)

### 2단계: PostgreSQL 선택

1. 연결 마법사에서 **PostgreSQL**을 선택합니다
2. **다음(Next)** 버튼을 클릭합니다

### 3단계: 연결 정보 입력

다음 정보를 입력합니다:

| 필드 | 값 |
|------|-----|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `llm_webapp` |
| **Username** | `llm_app` |
| **Password** | `TestPassword123!` |

#### 상세 설정:

- **Server Host**: `localhost`
- **Port**: `5432`
- **Database**: `llm_webapp`
- **Authentication**: Database Native
- **User name**: `llm_app`
- **Password**: `TestPassword123!`
- **Save password locally** 체크 (비밀번호 저장)

### 4단계: 드라이버 다운로드

처음 PostgreSQL을 연결하는 경우:
1. "Download driver files" 메시지가 나타나면 **다운로드** 클릭
2. PostgreSQL JDBC 드라이버가 자동으로 다운로드됩니다

### 5단계: 연결 테스트

1. 하단의 **"Test Connection"** 버튼을 클릭합니다
2. "Connected" 메시지가 나타나면 성공!
   ```
   Connected to:
   PostgreSQL 15.x
   Database: llm_webapp
   ```

3. **"Finish"** 버튼을 클릭하여 연결을 완료합니다

## 📂 데이터 탐색하기

연결이 완료되면 좌측 Database Navigator에서 다음과 같이 탐색할 수 있습니다:

```
localhost (PostgreSQL)
└── Databases
    └── llm_webapp
        └── Schemas
            └── public
                └── Tables
                    ├── users          (사용자)
                    ├── conversations  (대화 목록)
                    ├── messages       (메시지)
                    ├── documents      (문서)
                    ├── conversation_documents (대화-문서 연결)
                    ├── sessions       (세션)
                    └── alembic_version (DB 버전)
```

## 🔍 자주 사용하는 쿼리

DBeaver에서 SQL Editor를 열고 (F3 또는 테이블 우클릭 → SQL Editor) 다음 쿼리를 실행할 수 있습니다:

### 1. 전체 사용자 조회
```sql
SELECT id, username, is_admin, created_at, last_login_at
FROM users
ORDER BY created_at DESC;
```

### 2. 대화 목록 조회 (사용자 정보 포함)
```sql
SELECT
    c.id,
    c.title,
    u.username,
    c.created_at,
    c.updated_at
FROM conversations c
JOIN users u ON c.user_id = u.id
ORDER BY c.created_at DESC
LIMIT 20;
```

### 3. 대화와 메시지 조회
```sql
SELECT
    c.title as conversation,
    m.role,
    LEFT(m.content, 100) as message_preview,
    m.created_at
FROM messages m
JOIN conversations c ON m.conversation_id = c.id
ORDER BY m.created_at DESC
LIMIT 10;
```

### 4. 문서 업로드 현황
```sql
SELECT
    d.filename,
    d.file_type,
    d.file_size,
    u.username as uploaded_by,
    d.created_at
FROM documents d
JOIN users u ON d.user_id = u.id
ORDER BY d.created_at DESC;
```

### 5. 특정 대화의 전체 메시지
```sql
SELECT
    m.role,
    m.content,
    m.created_at
FROM messages m
WHERE m.conversation_id = 'YOUR-CONVERSATION-ID-HERE'
ORDER BY m.created_at ASC;
```

### 6. 데이터베이스 통계
```sql
SELECT
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM conversations) as total_conversations,
    (SELECT COUNT(*) FROM messages) as total_messages,
    (SELECT COUNT(*) FROM documents) as total_documents;
```

## 🎨 DBeaver 팁

### 데이터 조회
- 테이블 더블클릭 → 자동으로 데이터 조회
- `Ctrl + Enter` → SQL 실행
- `F3` → SQL Editor 열기

### 데이터 편집
- 데이터 조회 후 직접 셀을 더블클릭하여 편집 가능
- 편집 후 `Ctrl + S`로 저장

### ER 다이어그램 보기
1. 테이블 우클릭 → `View Diagram`
2. 테이블 간의 관계(Foreign Key)를 시각적으로 확인 가능

### 데이터 내보내기
1. 조회 결과에서 우클릭 → `Export Data`
2. CSV, JSON, Excel 등 다양한 형식으로 내보내기 가능

## ⚠️ 주의사항

1. **프로덕션 환경 주의**
   - 현재는 개발/테스트 환경이므로 자유롭게 조회 가능
   - 프로덕션 환경에서는 데이터 수정/삭제에 주의

2. **비밀번호 변경**
   - 현재 비밀번호 `TestPassword123!`는 개발용입니다
   - 프로덕션 환경에서는 반드시 강력한 비밀번호로 변경하세요
   - `.env` 파일에서 `POSTGRES_PASSWORD` 설정

3. **성능**
   - 대량 데이터 조회 시 `LIMIT`를 사용하여 제한
   - 인덱스가 있는 컬럼 활용 (id, username 등)

## 🔒 연결이 안 될 때 체크리스트

- [ ] Docker 컨테이너가 실행 중인지 확인: `docker ps | findstr postgres`
- [ ] 포트 5432가 열려있는지 확인: `netstat -an | findstr 5432`
- [ ] 방화벽 설정 확인
- [ ] DBeaver에서 드라이버가 정상 다운로드 되었는지 확인
- [ ] 비밀번호가 정확한지 확인 (`TestPassword123!`)

## 📞 문제 해결

### 연결 오류: "Connection refused"
```bash
# PostgreSQL 컨테이너 상태 확인
docker ps -a | findstr postgres

# 컨테이너가 중지되어 있다면 시작
docker start llm-webapp-postgres-test
```

### 연결 오류: "Authentication failed"
비밀번호 확인:
```bash
# .env 파일에서 설정된 비밀번호 확인
# 현재 비밀번호: TestPassword123!

# 또는 컨테이너에서 직접 확인
docker exec llm-webapp-postgres-test printenv POSTGRES_PASSWORD
```

### 드라이버 다운로드 실패
1. DBeaver 메뉴 → `Database` → `Driver Manager`
2. PostgreSQL 선택 → `Download/Update` 클릭
