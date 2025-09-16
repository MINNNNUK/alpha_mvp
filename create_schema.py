"""
Supabase 데이터베이스 스키마 생성 스크립트
"""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

def create_tables():
    """필요한 테이블들을 생성"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # SQL 스키마 읽기
    with open('supabase_schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print("📋 데이터베이스 스키마 생성 중...")
    
    # SQL을 세미콜론으로 분리하여 각각 실행
    sql_statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    
    for i, sql in enumerate(sql_statements):
        if sql:
            try:
                print(f"실행 중: {sql[:50]}...")
                # Supabase에서는 직접 SQL 실행이 제한적이므로
                # 대신 테이블 생성 API를 사용하거나
                # Supabase 대시보드에서 수동으로 실행해야 함
                print(f"✅ SQL {i+1} 준비 완료")
            except Exception as e:
                print(f"❌ SQL {i+1} 실행 실패: {e}")
    
    print("\n⚠️  중요: Supabase 대시보드에서 다음을 수행해주세요:")
    print("1. Supabase 대시보드 > SQL Editor로 이동")
    print("2. supabase_schema.sql 파일의 내용을 복사하여 실행")
    print("3. 테이블 생성 완료 후 다시 실행하세요")

if __name__ == "__main__":
    create_tables()
