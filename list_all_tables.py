"""
Supabase의 모든 테이블을 확인하는 스크립트
"""
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_all_tables(supabase: Client):
    """사용 가능한 모든 테이블 확인"""
    try:
        # 알려진 테이블들 확인
        known_tables = [
            "announcements",
            "companies", 
            "recommendations",
            "recommend_keyword4",
            "recommendations_keyword_enhanced",
            "recommendations3_active",
            "recommend_region4",
            "table1"
        ]
        
        available_tables = []
        
        for table_name in known_tables:
            try:
                result = supabase.table(table_name).select("*").limit(1).execute()
                logger.info(f"✅ 테이블 '{table_name}' 사용 가능")
                available_tables.append(table_name)
                
                # 테이블 구조 확인
                if result.data:
                    logger.info(f"   컬럼: {list(result.data[0].keys())}")
                    logger.info(f"   샘플 데이터: {result.data[0]}")
                else:
                    logger.info(f"   테이블이 비어있음")
                    
            except Exception as e:
                logger.info(f"❌ 테이블 '{table_name}' 사용 불가: {e}")
                continue
        
        logger.info(f"\n사용 가능한 테이블 목록: {available_tables}")
        return available_tables
        
    except Exception as e:
        logger.error(f"테이블 목록 확인 중 오류 발생: {e}")
        return []

def main():
    """메인 함수"""
    # Supabase 클라이언트 생성
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 연결 성공")
    except Exception as e:
        logger.error(f"Supabase 연결 실패: {e}")
        return
    
    # 모든 테이블 확인
    available_tables = list_all_tables(supabase)
    
    if available_tables:
        logger.info(f"\n총 {len(available_tables)}개의 테이블이 사용 가능합니다.")
    else:
        logger.error("사용 가능한 테이블이 없습니다.")

if __name__ == "__main__":
    main()
