"""
테이블의 컬럼 구조를 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_columns(supabase: Client, table_name: str):
    """테이블의 컬럼 구조 확인"""
    try:
        # 테이블 정보 조회
        result = supabase.table(table_name).select("*").limit(1).execute()
        
        if result.data:
            logger.info(f"테이블 '{table_name}'의 첫 번째 레코드:")
            for key, value in result.data[0].items():
                logger.info(f"  {key}: {type(value).__name__} = {value}")
        else:
            logger.info(f"테이블 '{table_name}'이 비어있습니다.")
            
        return True
        
    except Exception as e:
        logger.error(f"테이블 '{table_name}' 조회 중 오류 발생: {e}")
        return False

def main():
    """메인 함수"""
    table_name = "recommend_keyword4"
    
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # 테이블 컬럼 확인
    check_table_columns(supabase, table_name)

if __name__ == "__main__":
    main()
