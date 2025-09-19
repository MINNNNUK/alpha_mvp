"""
최소한의 데이터를 삽입하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_minimal_data(supabase: Client, table_name: str):
    """최소한의 데이터를 삽입"""
    try:
        # 테이블에 최소한의 데이터 삽입 시도
        minimal_data = {
            'id': 1,
            'company_id': 'test_company',
            'company_name': 'Test Company'
        }
        
        result = supabase.table(table_name).insert(minimal_data).execute()
        logger.info(f"최소한의 데이터 삽입 성공: {result.data}")
        
        # 삽입된 데이터 조회
        result = supabase.table(table_name).select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            logger.info(f"테이블 '{table_name}'의 컬럼 목록: {columns}")
            
            # 테스트 데이터 삭제
            supabase.table(table_name).delete().eq('id', 1).execute()
            logger.info("테스트 데이터 삭제 완료")
        
    except Exception as e:
        logger.error(f"최소한의 데이터 삽입 중 오류 발생: {e}")

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
    
    # 최소한의 데이터 삽입
    insert_minimal_data(supabase, table_name)

if __name__ == "__main__":
    main()
