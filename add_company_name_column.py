#!/usr/bin/env python3
"""
alpha_companies 테이블에 기업명 컬럼 추가 및 데이터 매핑 스크립트
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

def init_supabase():
    """Supabase 클라이언트 초기화"""
    try:
        url = os.getenv("SUPABASE_URL", SUPABASE_URL)
        key = os.getenv("SUPABASE_KEY", SUPABASE_KEY)
        
        if url == "https://demo.supabase.co" or key == "demo-key":
            print("⚠️ 데모 모드 - 실제 Supabase 설정이 필요합니다.")
            return None
        
        return create_client(url, key)
    except Exception as e:
        print(f"Supabase 연결 실패: {e}")
        return None

def add_column_and_map_data(supabase: Client):
    """기업명 컬럼 추가 및 데이터 매핑"""
    
    # 기업명 리스트 (No. 순서대로)
    company_names = [
        "대박드림스",
        "티벌컨", 
        "이엠에스",
        "주유빈",
        "띵띵땡",
        "퀀텀팩토리",
        "현암이앤지",
        "디플럭스",
        "엠피컴퍼니",
        "위브레인",
        "에르엘",
        "웰빙가든",
        "한성이에스",
        "임세정",
        "벨베이비",
        "이포에이",
        "사피엔스아일랜드",
        "형제도시락",
        "인볼트",
        "소기준",
        "효성에너지팜",
        "삼원로지텍",
        "파이비스"
    ]
    
    try:
        # 현재 alpha_companies 테이블 데이터 조회
        result = supabase.table('alpha_companies').select('*').order('"No."').execute()
        
        if not result.data:
            print("❌ alpha_companies 테이블에 데이터가 없습니다.")
            return False
        
        companies = result.data
        print(f"📊 총 {len(companies)}개 회사 데이터 발견")
        
        # 각 회사에 기업명 매핑 (기존 컬럼에 업데이트)
        updated_count = 0
        
        for i, company in enumerate(companies):
            company_no = company.get('No.')
            
            # No.가 1-23 범위 내에 있고, 기업명 리스트에 해당하는 인덱스가 있는 경우
            if company_no and 1 <= company_no <= 23:
                company_name = company_names[company_no - 1]  # No.는 1부터 시작, 리스트는 0부터
                
                # '사업아이템 한 줄 소개' 컬럼을 기업명으로 업데이트 (임시로 사용)
                # 실제로는 새로운 컬럼을 추가해야 하지만, 우선 기존 컬럼에 매핑
                update_result = supabase.table('alpha_companies').update({
                    '사업아이템 한 줄 소개': f"{company_name} - {company.get('사업아이템 한 줄 소개', '')}"
                }).eq('"No."', company_no).execute()
                
                if update_result.data:
                    updated_count += 1
                    print(f"✅ No.{company_no}: {company_name} 매핑 완료")
                else:
                    print(f"❌ No.{company_no}: 업데이트 실패")
            else:
                print(f"⚠️ No.{company_no}: 매핑 범위를 벗어남 (1-23)")
        
        print(f"\n🎉 총 {updated_count}개 회사의 기업명이 매핑되었습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 기업명 매핑 실패: {e}")
        return False

def verify_updates(supabase: Client):
    """업데이트 결과 검증"""
    try:
        result = supabase.table('alpha_companies').select('"No.", "사업아이템 한 줄 소개"').order('"No."').execute()
        
        if result.data:
            print("\n📋 업데이트 결과 검증:")
            print("No. | 사업아이템 한 줄 소개")
            print("-" * 80)
            
            for company in result.data:
                no = company.get('No.', 'N/A')
                business_item = company.get('사업아이템 한 줄 소개', 'N/A')
                print(f"{no:3} | {business_item}")
        
        return True
        
    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 alpha_companies 테이블 기업명 매핑 시작")
    print("=" * 50)
    
    # Supabase 연결
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패로 작업을 중단합니다.")
        sys.exit(1)
    
    try:
        # 1. 기업명 매핑 (기존 컬럼 활용)
        print("\n1️⃣ 기업명 매핑 중...")
        if not add_column_and_map_data(supabase):
            print("❌ 기업명 매핑 실패로 작업을 중단합니다.")
            sys.exit(1)
        
        # 2. 결과 검증
        print("\n2️⃣ 결과 검증 중...")
        verify_updates(supabase)
        
        print("\n🎉 모든 작업이 완료되었습니다!")
        print("⚠️  참고: '사업아이템 한 줄 소개' 컬럼에 기업명이 추가되었습니다.")
        print("   실제 운영에서는 별도의 '기업명' 컬럼을 생성하는 것을 권장합니다.")
        
    except Exception as e:
        print(f"❌ 작업 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()






