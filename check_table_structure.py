"""
테이블 구조 확인 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_structure(supabase: Client, table_name: str):
    """테이블 구조 확인"""
    try:
        # 테이블에 데이터 삽입 시도 (빈 데이터로)
        test_data = {
            'company_id': 'test',
            'company_name': 'test',
            'program_id': 'test',
            'title': 'test',
            'priority_type': 'test',
            'apply_start': 'test',
            'apply_end': 'test',
            'url': 'test',
            'kw_intersection': 'test',
            'kw_tfidf': 0.0,
            'kw_bm25': 0.0,
            'kw_phrase_hit': 0,
            'kw_must_have_hits': 0,
            'kw_forbid_hit': 0,
            'kw_gate': 'test',
            'kw_reason': 'test',
            'keyword_points': 0.0
        }
        
        result = supabase.table(table_name).insert(test_data).execute()
        logger.info(f"테스트 데이터 삽입 성공: {result.data}")
        
        # 삽입된 데이터 조회
        result = supabase.table(table_name).select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            logger.info(f"테이블 '{table_name}'의 컬럼 목록: {columns}")
            
            # 테스트 데이터 삭제
            supabase.table(table_name).delete().eq('company_id', 'test').execute()
            logger.info("테스트 데이터 삭제 완료")
        
    except Exception as e:
        logger.error(f"테이블 구조 확인 중 오류 발생: {e}")

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
    
    # 테이블 구조 확인
    check_table_structure(supabase, table_name)

if __name__ == "__main__":
    main()