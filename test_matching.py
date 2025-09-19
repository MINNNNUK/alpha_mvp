#!/usr/bin/env python3
"""
수정된 매칭 로직 테스트 스크립트
"""

import os
import sys
sys.path.append('.')
from app_supabase import load_recommendations2, load_recommendations3_active
from config import SUPABASE_URL, SUPABASE_KEY

def test_recommendation_matching():
    """추천 데이터 매칭 테스트"""
    print("🧪 추천 데이터 매칭 테스트")
    print("=" * 40)
    
    # 첫 번째 회사 (No.1 - 대박드림스)로 테스트
    company_id = 1
    
    print(f"📊 회사 ID {company_id} (대박드림스) 테스트:")
    
    # recommendations2 테스트
    print("\n1️⃣ recommendations2 테스트:")
    try:
        rec2_df = load_recommendations2(company_id)
        print(f"   결과: {len(rec2_df)}개 추천 데이터")
        if not rec2_df.empty:
            print("   컬럼:", list(rec2_df.columns))
            print("   샘플 데이터:")
            for i, row in rec2_df.head(3).iterrows():
                print(f"     {i+1}. {row.get('공고이름', 'N/A')} - 점수: {row.get('추천점수', 'N/A')}")
        else:
            print("   ❌ 데이터 없음")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # recommendations3_active 테스트
    print("\n2️⃣ recommendations3_active 테스트:")
    try:
        rec3_df = load_recommendations3_active(company_id)
        print(f"   결과: {len(rec3_df)}개 추천 데이터")
        if not rec3_df.empty:
            print("   컬럼:", list(rec3_df.columns))
            print("   샘플 데이터:")
            for i, row in rec3_df.head(3).iterrows():
                print(f"     {i+1}. {row.get('공고이름', 'N/A')} - 점수: {row.get('추천점수', 'N/A')}")
        else:
            print("   ❌ 데이터 없음")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

def test_multiple_companies():
    """여러 회사 테스트"""
    print("\n🔍 여러 회사 매칭 테스트")
    print("=" * 40)
    
    test_companies = [1, 2, 3, 4, 5]  # 처음 5개 회사 테스트
    
    for company_id in test_companies:
        print(f"\n📊 회사 ID {company_id} 테스트:")
        
        try:
            rec2_df = load_recommendations2(company_id)
            rec3_df = load_recommendations3_active(company_id)
            
            print(f"   recommendations2: {len(rec2_df)}개")
            print(f"   recommendations3_active: {len(rec3_df)}개")
            
            if len(rec2_df) == 0 and len(rec3_df) == 0:
                print("   ⚠️ 두 테이블 모두 데이터 없음")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")

def main():
    """메인 함수"""
    test_recommendation_matching()
    test_multiple_companies()

if __name__ == "__main__":
    main()







