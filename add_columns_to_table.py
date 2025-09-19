"""
테이블에 컬럼들을 추가하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_columns_to_table(supabase: Client, table_name: str):
    """테이블에 컬럼들을 추가"""
    try:
        # CSV 파일의 컬럼들
        csv_columns = [
            'company_id', 'company_name', 'program_id', 'title', 'priority_type',
            'apply_start', 'apply_end', 'url', 'kw_intersection', 'kw_tfidf',
            'kw_bm25', 'kw_phrase_hit', 'kw_must_have_hits', 'kw_forbid_hit',
            'kw_gate', 'kw_reason', 'keyword_points'
        ]
        
        # 각 컬럼을 하나씩 추가
        for column in csv_columns:
            try:
                # 컬럼 추가를 위한 기본 데이터 삽입
                test_data = {column: 'test'}
                result = supabase.table(table_name).insert(test_data).execute()
                logger.info(f"컬럼 '{column}' 추가 성공")
                
                # 테스트 데이터 삭제
                supabase.table(table_name).delete().eq(column, 'test').execute()
                
            except Exception as e:
                logger.error(f"컬럼 '{column}' 추가 실패: {e}")
        
    except Exception as e:
        logger.error(f"컬럼 추가 중 오류 발생: {e}")

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
    
    # 컬럼들 추가
    add_columns_to_table(supabase, table_name)

if __name__ == "__main__":
    main()
