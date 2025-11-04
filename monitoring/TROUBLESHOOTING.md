# Prometheus & Grafana 문제 해결 가이드

## ✅ 현재 상태 (모두 정상)

```bash
# 1. Prometheus가 메트릭 수집 중 (확인됨)
curl http://localhost:9090/api/v1/targets
# Result: backend:8000 - health: "up" ✅

# 2. 메트릭 데이터 존재 (확인됨)
curl http://localhost:9090/api/v1/query?query=http_requests_total
# Result: 12개의 시계열 데이터 수집 중 ✅

# 3. Grafana Prometheus datasource 연결 (확인됨)
# Log: "inserting datasource from configuration name=Prometheus" ✅

# 4. Grafana 대시보드 로드 (확인됨)
# Log: "Initialized channel handler channel=grafana/dashboard/uid/llm-webapp-overview" ✅
```

## 📊 Grafana 대시보드 접속 방법

### Step 1: Grafana 로그인
```
URL: http://localhost:3001
Username: admin
Password: admin
```

### Step 2: 대시보드 찾기

**방법 A: 메뉴에서 찾기**
1. 좌측 메뉴에서 "Dashboards" 클릭
2. "LLM Web App - 성능 대시보드" 찾기
3. 클릭해서 열기

**방법 B: 직접 URL 접속**
```
http://localhost:3001/d/llm-webapp-overview/llm-web-app-seongneung-daesibodeu
```

### Step 3: 데이터가 안 보이는 경우

#### 🔧 해결 방법 1: 시간 범위 조정
- 우측 상단 시계 아이콘 클릭
- "Last 1 hour" 또는 "Last 6 hours" 선택
- "Apply time range" 클릭

#### 🔧 해결 방법 2: Datasource 수동 추가

1. 좌측 메뉴 → "Connections" → "Data sources"
2. "Add data source" 클릭
3. "Prometheus" 선택
4. 설정:
   ```
   Name: Prometheus
   URL: http://prometheus:9090
   ```
5. "Save & Test" 클릭 → "Data source is working" 확인

#### 🔧 해결 방법 3: 대시보드 수동 임포트

1. 좌측 메뉴 → "Dashboards" → "New" → "Import"
2. 다음 JSON 파일 업로드: `/monitoring/grafana/dashboards/llm-webapp-overview.json`
3. "Prometheus" datasource 선택
4. "Import" 클릭

## 🧪 Prometheus 직접 확인

### 방법 1: Prometheus UI

```
URL: http://localhost:9090

테스트 쿼리:
1. http_requests_total
2. rate(http_requests_total[5m])
3. process_resident_memory_bytes
```

### 방법 2: 커맨드라인

```bash
# 현재 수집 중인 메트릭 확인
curl http://localhost:8000/metrics | grep http_request

# Prometheus 쿼리
curl 'http://localhost:9090/api/v1/query?query=http_requests_total'
```

## 🎯 자주 묻는 질문

### Q1: Grafana에 아무것도 안 보여요
**A**:
1. 시간 범위를 "Last 6 hours"로 변경
2. 페이지 새로고침 (Ctrl+R)
3. Datasource 연결 확인

### Q2: "No data" 또는 "N/A" 표시
**A**:
1. 백엔드 API에 요청 몇 개 보내기:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/health
   curl http://localhost:8000/health
   ```
2. 1-2분 대기 (메트릭 수집 간격: 10초)
3. Grafana 새로고침

### Q3: Grafana 로그인 안 됨
**A**:
```bash
# 컨테이너 재시작
docker restart llm-webapp-grafana

# 로그 확인
docker logs llm-webapp-grafana | tail -20
```

### Q4: 대시보드 목록이 비어있음
**A**:
대시보드를 수동으로 임포트하세요 (위의 "해결 방법 3" 참조)

## 📸 스크린샷으로 확인하기

각 화면에서 스크린샷을 찍어서 확인:

1. **Prometheus Targets**: http://localhost:9090/targets
   - 기대: "backend:8000 (1/1 up)" 녹색 표시

2. **Prometheus Graph**: http://localhost:9090/graph
   - 쿼리 입력: `http_requests_total`
   - 기대: 그래프에 선이 표시됨

3. **Grafana Datasources**: http://localhost:3001/connections/datasources
   - 기대: "Prometheus" 항목 존재

4. **Grafana Dashboards**: http://localhost:3001/dashboards
   - 기대: "LLM Web App - 성능 대시보드" 항목 존재

---

## 🆘 여전히 안 되면?

다음 정보를 수집해주세요:

```bash
# 1. 컨테이너 상태
docker ps | grep -E "prometheus|grafana|backend"

# 2. Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | head -50

# 3. Grafana 로그
docker logs llm-webapp-grafana 2>&1 | tail -30

# 4. 메트릭 확인
curl http://localhost:8000/metrics | head -50
```
