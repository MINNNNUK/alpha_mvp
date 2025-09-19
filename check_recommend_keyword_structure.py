"""
recommend_keyword 테이블의 구조를 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recommend_keyword_structure(supabase: Client):
    """recommend_keyword 테이블의 구조 확인"""
    try:
        table_name = "recommend_keyword"
        
        # 테이블 구조 확인을 위해 빈 데이터 삽입 시도
        logger.info(f"테이블 '{table_name}' 구조 확인 중...")
        
        # 테스트 데이터로 테이블 구조 확인
        test_data = {"id": 1}
        
        try:
            result = supabase.table(table_name).insert(test_data).execute()
            logger.info("id 컬럼으로 테스트 데이터 삽입 성공")
            
            # 삽입된 데이터 확인
            result = supabase.table(table_name).select("*").limit(1).execute()
            if result.data:
                logger.info("테이블 컬럼:")
                for key in result.data[0].keys():
                    logger.info(f"  - {key}")
                logger.info(f"샘플 데이터: {result.data[0]}")
            
        except Exception as e:
            logger.error(f"테이블 구조 확인 중 오류: {e}")
            
            # 다른 방법으로 테이블 구조 확인
            try:
                # 빈 쿼리로 테이블 존재 확인
                result = supabase.table(table_name).select("*").limit(0).execute()
                logger.info("테이블이 존재하지만 컬럼 정보를 가져올 수 없습니다.")
                
            except Exception as e2:
                logger.error(f"테이블 접근 실패: {e2}")
        
        return True
        
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
    
    # recommend_keyword 테이블 구조 확인
    check_recommend_keyword_structure(supabase)

if __name__ == "__main__":
    main()
