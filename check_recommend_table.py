"""
recommend_keyword4 테이블 구조를 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_recommend_table(supabase: Client):
    """recommend_keyword4 테이블 구조 확인"""
    try:
        # 테이블 존재 확인
        result = supabase.table("recommend_keyword4").select("*").limit(1).execute()
        
        if result.data:
            logger.info("recommend_keyword4 테이블에 데이터가 있습니다.")
            logger.info("테이블 컬럼:")
            for key in result.data[0].keys():
                logger.info(f"  - {key}")
        else:
            logger.info("recommend_keyword4 테이블이 비어있습니다.")
            
        # 테이블 스키마 정보 확인을 위해 다른 방법 시도
        try:
            # 빈 데이터로 테이블 구조 확인
            test_data = {"test": "value"}
            supabase.table("recommend_keyword4").insert(test_data).execute()
        except Exception as e:
            logger.info(f"테이블 스키마 확인을 위한 테스트: {e}")
            
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
    
    # 테이블 확인
    check_recommend_table(supabase)

if __name__ == "__main__":
    main()
