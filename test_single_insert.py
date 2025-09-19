"""
단일 레코드 삽입으로 테이블 스키마를 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_insert(supabase: Client, table_name: str):
    """단일 레코드 삽입으로 테이블 스키마 확인"""
    try:
        # 가장 간단한 데이터로 시도
        test_data = {
            "id": 1,
            "test_field": "test_value"
        }
        
        result = supabase.table(table_name).insert(test_data).execute()
        logger.info(f"테스트 데이터 삽입 성공: {result}")
        return True
        
    except Exception as e:
        logger.error(f"테스트 데이터 삽입 실패: {e}")
        
        # 다른 필드명으로 시도
        try:
            test_data2 = {
                "company_id": 1,
                "company_name": "test_company"
            }
            
            result = supabase.table(table_name).insert(test_data2).execute()
            logger.info(f"두 번째 테스트 데이터 삽입 성공: {result}")
            return True
            
        except Exception as e2:
            logger.error(f"두 번째 테스트 데이터 삽입도 실패: {e2}")
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
    
    # 테스트 삽입
    test_single_insert(supabase, table_name)

if __name__ == "__main__":
    main()
