# 🚀 Streamlit Cloud 배포 가이드

## 📋 배포 전 준비사항

### 1. GitHub 저장소 준비
- [ ] 코드를 GitHub 저장소에 업로드
- [ ] `requirements.txt` 파일 확인
- [ ] `.streamlit/secrets.toml` 파일 확인

### 2. Supabase 설정 확인
- [ ] Supabase 프로젝트 URL 확인
- [ ] Supabase Anon Key 확인
- [ ] 데이터베이스 연결 테스트

## 🔧 Streamlit Cloud 배포 단계

### 1. Streamlit Cloud 접속
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭

### 2. 앱 설정
- **Repository**: `your-username/your-repo-name`
- **Branch**: `main` (또는 `master`)
- **Main file path**: `supabase1/app_supabase.py`

### 3. Secrets 설정
Streamlit Cloud 대시보드에서 "Secrets" 탭으로 이동하여 다음 내용 추가:

```toml
[supabase]
url = "your_supabase_project_url"
key = "your_supabase_anon_key"
```

### 4. 배포 실행
- "Deploy!" 버튼 클릭
- 배포 완료까지 대기 (약 2-3분)

## 🔍 배포 후 확인사항

### 1. 앱 접속 테스트
- 제공된 URL로 접속: `https://your-app-name.streamlit.app`
- 회사 선택 기능 테스트
- 추천 시스템 동작 확인

### 2. 오류 확인
- Streamlit Cloud 로그 확인
- Supabase 연결 상태 확인
- 데이터 로딩 테스트

## 🛠️ 문제 해결

### ModuleNotFoundError
```bash
# requirements.txt에 누락된 패키지 추가
pip install package_name
```

### Supabase 연결 오류
- Secrets 설정 확인
- Supabase 프로젝트 상태 확인
- API 키 권한 확인

### 데이터 로딩 오류
- Supabase 테이블 존재 확인
- RLS 정책 확인
- 데이터 형식 확인

## 📱 접속 정보

배포 완료 후:
- **URL**: `https://your-app-name.streamlit.app`
- **24/7 접속 가능**
- **모든 기기에서 접속 가능**

## 🔄 업데이트 방법

1. GitHub에 코드 변경사항 푸시
2. Streamlit Cloud에서 자동 재배포
3. 새 버전 확인

## 📞 지원

문제가 발생하면:
1. Streamlit Cloud 로그 확인
2. GitHub Issues에 문제 보고
3. 개발팀에 연락

---

*이 가이드를 따라하면 안정적인 클라우드 배포가 가능합니다! 🎉*

