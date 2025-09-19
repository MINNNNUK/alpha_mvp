"""
CSV 데이터를 announcements 테이블에 업로드하는 스크립트
"""
import pandas as pd
import os
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_announcements(supabase: Client, csv_path: str):
    """CSV 데이터를 announcements 테이블에 업로드"""
    try:
        # CSV 파일 읽기 (처음 100행만)
        logger.info(f"CSV 파일 읽기 시작: {csv_path}")
        
        df = pd.read_csv(csv_path, nrows=100)
        
        logger.info(f"CSV 컬럼: {list(df.columns)}")
        logger.info(f"읽은 행 수: {len(df)}")
        
        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)
        
        # 데이터를 딕셔너리 리스트로 변환
        data = df.to_dict('records')
        
        # 각 레코드에서 NaN 값을 None으로 변환
        for record in data:
            for key, value in record.items():
                if pd.isna(value) or value == float('inf') or value == float('-inf'):
                    record[key] = None
        
        # announcements 테이블에 맞춰서 매핑
        mapped_data = []
        for i, record in enumerate(data):
            mapped_record = {
                "id": i + 1,  # id 추가
                "title": record.get("title", ""),
                "url": record.get("url", ""),
                "keywords": [f"company_id:{record.get('company_id', '')}", f"program_id:{record.get('program_id', '')}"],
                "agency": "K-Startup",
                "source": "kstartup",
                "region": "전국",
                "stage": "예비창업",
                "amount_text": "미정",
                "budget_band": "소규모",
                "update_type": "신규"
            }
            mapped_data.append(mapped_record)
        
        logger.info(f"announcements 테이블에 {len(mapped_data)}행 삽입 시도...")
        
        # Supabase에 데이터 삽입
        result = supabase.table("announcements").insert(mapped_data).execute()
        
        logger.info(f"성공적으로 {len(mapped_data)}행이 삽입되었습니다.")
        logger.info(f"삽입된 데이터 샘플: {result.data[:2] if result.data else 'None'}")
        return True
        
    except Exception as e:
        logger.error(f"CSV 파일 처리 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    csv_path = "/Users/minkim/git_test/kpmg-2025/Version3/recommendations_keyword_enhanced.csv"
    
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # CSV 파일 확인
    if not os.path.exists(csv_path):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
        return
    
    logger.info(f"CSV 파일 확인 완료: {csv_path}")
    
    # announcements 테이블에 업로드
    if upload_to_announcements(supabase, csv_path):
        logger.info("CSV 파일 업로드가 성공적으로 완료되었습니다.")
    else:
        logger.error("CSV 파일 업로드에 실패했습니다.")

if __name__ == "__main__":
    main()
