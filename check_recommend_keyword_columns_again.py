"""
recommend_keyword 테이블의 컬럼을 다시 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recommend_keyword_columns_again(supabase: Client):
    """recommend_keyword 테이블의 컬럼을 다시 확인"""
    try:
        table_name = "recommend_keyword"
        
        logger.info(f"테이블 '{table_name}' 컬럼 확인 중...")
        
        # 방법 1: 기존 데이터가 있는지 확인
        try:
            result = supabase.table(table_name).select("*").limit(1).execute()
            if result.data:
                logger.info("테이블에 데이터가 있습니다!")
                logger.info("테이블 컬럼:")
                for key in result.data[0].keys():
                    logger.info(f"  - {key}")
                logger.info(f"샘플 데이터: {result.data[0]}")
                return True
            else:
                logger.info("테이블이 비어있습니다.")
        except Exception as e:
            logger.info(f"데이터 조회 실패: {e}")
        
        # 방법 2: 빈 쿼리로 테이블 존재 확인
        try:
            result = supabase.table(table_name).select("*").limit(0).execute()
            logger.info("테이블이 존재합니다.")
        except Exception as e:
            logger.error(f"테이블 접근 실패: {e}")
            return False
        
        # 방법 3: 다른 방법으로 컬럼 정보 확인
        try:
            # 간단한 데이터로 테스트
            test_data = {"test": "value"}
            result = supabase.table(table_name).insert(test_data).execute()
            logger.info("테스트 데이터 삽입 성공")
            
            # 삽입된 데이터 확인
            result = supabase.table(table_name).select("*").limit(1).execute()
            if result.data:
                logger.info("테이블 컬럼:")
                for key in result.data[0].keys():
                    logger.info(f"  - {key}")
                logger.info(f"샘플 데이터: {result.data[0]}")
                return True
                
        except Exception as e:
            logger.info(f"테스트 데이터 삽입 실패: {e}")
        
        # 방법 4: CSV 컬럼으로 시도
        try:
            csv_columns = [
                "company_id", "company_name", "program_id", "title", 
                "priority_type", "apply_start", "apply_end", "url",
                "kw_intersection", "kw_tfidf", "kw_bm25", "kw_phrase_hit",
                "kw_must_have_hits", "kw_forbid_hit", "kw_gate", 
                "kw_reason", "keyword_points"
            ]
            
            test_data = {}
            for col in csv_columns:
                test_data[col] = "test_value"
            
            result = supabase.table(table_name).insert(test_data).execute()
            logger.info("CSV 컬럼으로 테스트 데이터 삽입 성공")
            
            # 삽입된 데이터 확인
            result = supabase.table(table_name).select("*").limit(1).execute()
            if result.data:
                logger.info("테이블 컬럼:")
                for key in result.data[0].keys():
                    logger.info(f"  - {key}")
                logger.info(f"샘플 데이터: {result.data[0]}")
                return True
                
        except Exception as e:
            logger.info(f"CSV 컬럼으로 테스트 데이터 삽입 실패: {e}")
        
        logger.info("모든 방법으로 컬럼 정보를 확인할 수 없습니다.")
        return False
        
    except Exception as e:
        logger.error(f"테이블 확인 중 오류 발생: {e}")
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
    
    # recommend_keyword 테이블 컬럼 확인
    check_recommend_keyword_columns_again(supabase)

if __name__ == "__main__":
    main()
