"""
ID와 함께 기본 데이터를 삽입하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_basic_data_with_id(supabase: Client, table_name: str):
    """ID와 함께 기본 데이터를 삽입"""
    try:
        # 테이블에 기본 데이터 삽입 시도
        basic_data = {
            'id': 1,
            'company_id': 'test_company',
            'company_name': 'Test Company',
            'program_id': 'test_program',
            'title': 'Test Title',
            'priority_type': 'test_priority',
            'apply_start': '2024-01-01',
            'apply_end': '2024-12-31',
            'url': 'https://test.com',
            'kw_intersection': 'test_keywords',
            'kw_tfidf': 0.5,
            'kw_bm25': 0.3,
            'kw_phrase_hit': 1,
            'kw_must_have_hits': 2,
            'kw_forbid_hit': 0,
            'kw_gate': 'test_gate',
            'kw_reason': 'test_reason',
            'keyword_points': 10.0
        }
        
        result = supabase.table(table_name).insert(basic_data).execute()
        logger.info(f"기본 데이터 삽입 성공: {result.data}")
        
        # 삽입된 데이터 조회
        result = supabase.table(table_name).select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            logger.info(f"테이블 '{table_name}'의 컬럼 목록: {columns}")
            
            # 테스트 데이터 삭제
            supabase.table(table_name).delete().eq('id', 1).execute()
            logger.info("테스트 데이터 삭제 완료")
        
    except Exception as e:
        logger.error(f"기본 데이터 삽입 중 오류 발생: {e}")

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
    
    # 기본 데이터 삽입
    insert_basic_data_with_id(supabase, table_name)

if __name__ == "__main__":
    main()
