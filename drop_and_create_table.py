"""
테이블 삭제 및 생성 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_and_create_table(supabase: Client, table_name: str):
    """테이블 삭제 및 생성"""
    try:
        # 테이블 삭제 SQL
        drop_sql = f"DROP TABLE IF EXISTS {table_name};"
        
        # 테이블 생성 SQL (CSV 컬럼에 맞춰서)
        create_sql = f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            company_id TEXT,
            company_name TEXT,
            program_id TEXT,
            title TEXT,
            priority_type TEXT,
            apply_start TEXT,
            apply_end TEXT,
            url TEXT,
            kw_intersection TEXT,
            kw_tfidf FLOAT,
            kw_bm25 FLOAT,
            kw_phrase_hit INTEGER,
            kw_must_have_hits INTEGER,
            kw_forbid_hit INTEGER,
            kw_gate TEXT,
            kw_reason TEXT,
            keyword_points FLOAT
        );
        """
        
        # SQL 실행
        result = supabase.rpc('exec_sql', {'sql': drop_sql}).execute()
        logger.info(f"테이블 '{table_name}' 삭제 완료")
        
        result = supabase.rpc('exec_sql', {'sql': create_sql}).execute()
        logger.info(f"테이블 '{table_name}' 생성 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {e}")
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
    
    # 테이블 삭제 및 생성
    if drop_and_create_table(supabase, table_name):
        logger.info("테이블 생성이 성공적으로 완료되었습니다.")
    else:
        logger.error("테이블 생성에 실패했습니다.")

if __name__ == "__main__":
    main()
