"""
테이블 스키마 확인 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_schema(supabase: Client, table_name: str):
    """테이블 스키마 확인"""
    try:
        # 테이블 정보 조회
        result = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"테이블 '{table_name}' 스키마 확인:")
        
        if result.data:
            # 첫 번째 레코드의 키들을 출력
            columns = list(result.data[0].keys())
            logger.info(f"컬럼 목록: {columns}")
            
            # 각 컬럼의 타입 확인
            for column in columns:
                value = result.data[0][column]
                value_type = type(value).__name__
                logger.info(f"  {column}: {value_type}")
        else:
            logger.info("테이블이 비어있습니다.")
            
    except Exception as e:
        logger.error(f"테이블 스키마 확인 중 오류 발생: {e}")

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
    
    # 테이블 스키마 확인
    check_table_schema(supabase, table_name)

if __name__ == "__main__":
    main()
