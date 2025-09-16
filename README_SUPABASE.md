# 정부지원사업 맞춤 추천 시스템 - Supabase 연동

## 개요
기존 CSV 파일 기반 데이터를 Supabase 데이터베이스로 마이그레이션하여 실시간 데이터 관리가 가능한 MVP 시스템입니다.

## 주요 기능
- 🏢 **회사 관리**: 회사 정보 CRUD, 검색, 필터링
- 📋 **맞춤 추천**: 전체/활성 공고 추천 시스템
- 🔔 **신규 공고 알림**: 실시간 알림 및 확인 처리
- 🗓️ **12개월 로드맵**: 월별 공고 배치 및 금액 차트
- 📊 **실시간 데이터**: Supabase 기반 실시간 데이터 동기화

## 빠른 시작

### 자동 설정 (권장)
```bash
# 1. 자동 설정 및 초기화
python setup_supabase.py

# 2. 앱 실행
python run_supabase_app.py
```

### 수동 설정

#### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 2. Supabase 프로젝트 설정
1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. 프로젝트 URL과 API 키 확인
3. 환경변수 설정:
```bash
# .env 파일 생성
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

#### 3. 데이터베이스 스키마 생성
Supabase 대시보드의 SQL Editor에서 `supabase_schema.sql` 파일의 내용을 실행하여 테이블을 생성합니다.

#### 4. 연결 테스트
```bash
python test_supabase_connection.py
```

#### 5. 데이터 마이그레이션
```bash
python migrate_to_supabase.py
```

#### 6. 앱 실행
```bash
streamlit run app_supabase.py
```

## 파일 구조
```
├── app_supabase.py              # Supabase 연동 Streamlit 앱
├── migrate_to_supabase.py       # 데이터 마이그레이션 스크립트
├── setup_supabase.py            # 자동 설정 스크립트
├── test_supabase_connection.py  # 연결 테스트 스크립트
├── run_supabase_app.py          # 앱 실행 스크립트
├── supabase_schema.sql          # 데이터베이스 스키마
├── config.py                    # Supabase 설정
├── requirements.txt             # Python 의존성
├── env_example.txt              # 환경변수 예시
├── .env                         # 환경변수 (생성 필요)
└── README_SUPABASE.md           # 이 파일
```

## 데이터베이스 스키마

### companies (회사)
- id: 기본키
- name: 회사명
- business_type: 사업자 유형
- region: 지역
- years: 업력
- stage: 성장단계
- industry: 업종
- keywords: 키워드 배열
- preferred_uses: 선호 지원용도 배열
- preferred_budget: 선호 예산규모

### announcements (공고)
- id: 공고 ID (기본키)
- title: 공고명
- agency: 기관명
- source: 수집원
- region: 지원지역
- stage: 사업경력
- due_date: 마감일
- amount_krw: 지원금액 (원)
- amount_text: 금액 원문
- url: 공고 URL

### recommendations (추천)
- id: 기본키
- company_id: 회사 ID (외래키)
- announcement_id: 공고 ID (외래키)
- rank: 추천순위
- score: 추천점수
- reason: 추천이유
- start_date: 모집시작일
- end_date: 마감일
- amount_krw: 지원금액
- status: 공고상태
- year: 공고연도
- month: 공고월

### notification_states (알림상태)
- id: 기본키
- company_id: 회사 ID (외래키)
- last_seen_announcement_ids: 마지막 확인한 공고 ID 배열
- last_updated: 마지막 업데이트 시간

## 주요 개선사항

### 로컬 파일 대비 장점
1. **실시간 동기화**: 여러 사용자가 동시에 접근 가능
2. **데이터 일관성**: 중앙 집중식 데이터 관리
3. **확장성**: 대용량 데이터 처리 가능
4. **백업 및 복구**: 자동 백업 및 버전 관리
5. **보안**: RLS(Row Level Security) 지원

### 성능 최적화
- 캐싱: `@st.cache_data`로 데이터 로딩 최적화
- 인덱싱: 자주 사용되는 컬럼에 인덱스 생성
- 배치 처리: 대용량 데이터 삽입 시 배치 처리

## 사용법

### 1. 회사 관리
- 사이드바에서 기존 회사 검색 및 선택
- 신규 회사 추가 폼으로 새 회사 등록
- 회사별 상세 정보 확인

### 2. 맞춤 추천
- 선택된 회사에 대한 추천 공고 확인
- 전체 추천과 활성 공고만 보기 탭으로 구분
- 추천 점수 및 이유 확인

### 3. 신규 공고 알림
- 마지막 확인 이후 새로 등록된 공고 확인
- "모두 확인 처리" 버튼으로 알림 상태 업데이트

### 4. 12개월 로드맵
- 월별 공고 배치 및 예상 지원금액 차트
- 월별 상세 공고 정보 확인
- CSV 형태로 로드맵 데이터 다운로드

## 개발자 가이드

### 환경변수 설정
```bash
# .env 파일 생성
cp env_example.txt .env
# .env 파일을 편집하여 실제 Supabase 정보 입력
```

### 데이터베이스 스키마 확인
```sql
-- Supabase 대시보드 > SQL Editor에서 실행
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;
```

### 로그 확인
```bash
# Streamlit 앱 로그
streamlit run app_supabase.py --logger.level debug

# 마이그레이션 로그
python migrate_to_supabase.py
```

## 문제 해결

### 환경변수 오류
```
환경변수 SUPABASE_URL과 SUPABASE_KEY를 설정해주세요.
```
→ `.env` 파일을 생성하고 Supabase 프로젝트 정보를 입력하세요.

### 데이터 로드 실패
```
회사 데이터 로드 실패: ...
```
→ Supabase 프로젝트가 활성화되어 있는지, API 키가 올바른지 확인하세요.

### 마이그레이션 실패
```
마이그레이션 실패: ...
```
→ 데이터베이스 스키마가 올바르게 생성되었는지 확인하세요.

## 향후 개선 계획
1. **사용자 인증**: Supabase Auth 연동
2. **실시간 알림**: WebSocket 기반 실시간 알림
3. **고급 필터링**: 다중 조건 필터링 시스템
4. **대시보드**: 통계 및 분석 대시보드
5. **API**: REST API 제공
