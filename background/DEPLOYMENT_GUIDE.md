# Streamlit 앱 24시간 실행 가이드

## 1. nohup을 사용한 백그라운드 실행 (가장 간단)

```bash
# 앱 실행
nohup streamlit run app_supabase.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &

# 실행 상태 확인
ps aux | grep streamlit

# 로그 확인
tail -f streamlit.log

# 앱 종료
pkill -f streamlit
```

## 2. systemd 서비스로 등록 (더 안정적)

```bash
# 서비스 파일 복사
sudo cp streamlit-app.service /etc/systemd/system/

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable streamlit-app
sudo systemctl start streamlit-app

# 서비스 상태 확인
sudo systemctl status streamlit-app

# 서비스 중지
sudo systemctl stop streamlit-app
```

## 3. Docker를 사용한 컨테이너화

```bash
# Docker 이미지 빌드
docker build -t streamlit-app .

# Docker 컨테이너 실행
docker run -d -p 8501:8501 --name streamlit-app streamlit-app

# 또는 docker-compose 사용
docker-compose up -d

# 컨테이너 상태 확인
docker ps

# 컨테이너 중지
docker stop streamlit-app
```

## 4. 클라우드 배포 옵션

### Streamlit Cloud (무료)
1. GitHub에 코드 업로드
2. https://share.streamlit.io 에서 배포
3. 자동으로 24시간 실행

### Heroku
1. Procfile 생성: `web: streamlit run app_supabase.py --server.port $PORT --server.address 0.0.0.0`
2. Heroku CLI로 배포

### AWS EC2
1. EC2 인스턴스 생성
2. 위의 방법 중 하나 사용

### Google Cloud Run
1. Dockerfile 사용
2. Cloud Run에 배포

## 5. 모니터링 및 관리

### 로그 확인
```bash
# nohup 사용시
tail -f streamlit.log

# systemd 사용시
sudo journalctl -u streamlit-app -f

# Docker 사용시
docker logs -f streamlit-app
```

### 자동 재시작 설정
- systemd: `Restart=always` (이미 설정됨)
- Docker: `restart: unless-stopped` (이미 설정됨)

### 포트 확인
```bash
# 포트 8501 사용 확인
lsof -i :8501
netstat -tulpn | grep 8501
```

## 6. 보안 고려사항

1. 방화벽 설정
2. SSL 인증서 설정 (프로덕션용)
3. 환경 변수 보안 관리
4. 접근 제한 설정

## 7. 성능 최적화

1. 메모리 사용량 모니터링
2. CPU 사용량 모니터링
3. 데이터베이스 연결 풀 설정
4. 캐싱 전략 적용
