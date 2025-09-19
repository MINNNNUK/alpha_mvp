"""
기존 테이블들 확인 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_existing_tables(supabase: Client):
    """기존 테이블들 확인"""
    try:
        # 모든 테이블 조회
        result = supabase.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
        
        logger.info("기존 테이블 목록:")
        for table in result.data:
            logger.info(f"  - {table['table_name']}")
            
    except Exception as e:
        logger.error(f"테이블 목록 조회 중 오류 발생: {e}")

def check_table_columns(supabase: Client, table_name: str):
    """특정 테이블의 컬럼들 확인"""
    try:
        # 테이블 컬럼 조회
        result = supabase.table('information_schema.columns').select('column_name, data_type').eq('table_name', table_name).eq('table_schema', 'public').execute()
        
        logger.info(f"테이블 '{table_name}'의 컬럼 목록:")
        for column in result.data:
            logger.info(f"  - {column['column_name']}: {column['data_type']}")
            
    except Exception as e:
        logger.error(f"테이블 컬럼 조회 중 오류 발생: {e}")

def main():
    """메인 함수"""
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # 기존 테이블들 확인
    check_existing_tables(supabase)
    
    # recommend_keyword4 테이블의 컬럼들 확인
    check_table_columns(supabase, 'recommend_keyword4')

if __name__ == "__main__":
    main()
