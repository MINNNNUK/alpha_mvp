"""
간단한 테이블 확인 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(supabase: Client, table_name: str):
    """테이블이 존재하는지 확인"""
    try:
        # 테이블 정보 조회 시도
        result = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"테이블 '{table_name}'이 존재합니다.")
        
        # 첫 번째 레코드의 키들을 출력
        if result.data:
            columns = list(result.data[0].keys())
            logger.info(f"컬럼 목록: {columns}")
        else:
            logger.info("테이블이 비어있습니다.")
            
        return True
    except Exception as e:
        logger.info(f"테이블 '{table_name}'이 존재하지 않습니다: {e}")
        return False

def main():
    """메인 함수"""
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # recommend_keyword4 테이블 확인
    check_table_exists(supabase, 'recommend_keyword4')
    
    # 다른 테이블들도 확인
    other_tables = ['companies', 'announcements', 'recommendations']
    for table in other_tables:
        check_table_exists(supabase, table)

if __name__ == "__main__":
    main()
