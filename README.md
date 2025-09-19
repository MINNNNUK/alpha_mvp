# KPMG 추천 시스템 MVP

## 개요
KPMG를 위한 종합적인 정부지원사업 추천 시스템입니다. 다양한 추천 알고리즘을 통해 기업에 맞는 정부지원사업을 추천합니다.

## 주요 기능

### 추천 탭
1. **전체 추천** - 모든 추천 데이터를 종합적으로 표시
2. **활성 공고만** - 현재 접수 중인 공고만 필터링
3. **추천(지역)** - 지역 기반 추천 (recommend_region4)
4. **추천(키워드)** - 키워드 매칭 기반 추천 (recommend_keyword4)
5. **추천(규칙)** - 규칙 기반 추천 (recommend_rules4)
6. **추천(3대장)** - 우선순위 기반 추천 (recommend_priority4)

### 핵심 특징
- **회사별 맞춤 추천**: 선택한 회사에 따라 개별화된 추천 제공
- **다양한 추천 알고리즘**: 지역, 키워드, 규칙, 우선순위 기반 추천
- **실시간 통계**: 평균/최고 점수, 통과율 등 통계 정보 제공
- **CSV 다운로드**: 각 추천 유형별 데이터 다운로드 가능
- **한국어 UI**: 사용자 친화적인 한국어 인터페이스

## 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python, Pandas
- **Database**: Supabase
- **Deployment**: Streamlit Cloud

## 설치 및 실행

### 로컬 실행
```bash
# 저장소 클론
git clone https://github.com/MINNNNUK/alpha_mvp.git
cd alpha_mvp

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# 애플리케이션 실행
streamlit run app_supabase.py
```

### Streamlit Cloud 배포
1. GitHub 저장소를 Streamlit Cloud에 연결
2. 환경변수 설정:
   - `SUPABASE_URL`: Supabase 프로젝트 URL
   - `SUPABASE_KEY`: Supabase API 키
3. 자동 배포 완료

## 데이터베이스 구조

### 주요 테이블
- `alpha_companies2`: 기업 정보
- `recommend_region4`: 지역 기반 추천 데이터
- `recommend_keyword4`: 키워드 기반 추천 데이터
- `recommend_rules4`: 규칙 기반 추천 데이터
- `recommend_priority4`: 우선순위 기반 추천 데이터

## 사용법
1. 사이드바에서 회사 선택
2. 원하는 추천 탭 클릭
3. 추천 결과 확인 및 CSV 다운로드
4. 통계 정보로 추천 품질 파악

## 라이선스
MIT License

## 기여
이슈나 풀 리퀘스트를 통해 기여해주세요.

## 문의
프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.
