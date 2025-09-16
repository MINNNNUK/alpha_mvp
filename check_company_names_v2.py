#!/usr/bin/env python3
"""
추천 데이터 테이블의 기업명 확인 스크립트 (v2)
"""

import os
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

def check_company_names_in_recommendations(supabase: Client):
    """추천 데이터 테이블의 기업명 확인"""
    print("🔍 추천 데이터 테이블의 기업명 확인")
    print("=" * 50)
    
    # alpha_companies의 기업명 목록
    alpha_companies_result = supabase.table('alpha_companies').select('"No.", "사업아이템 한 줄 소개"').execute()
    
    if alpha_companies_result.data:
        print("📋 alpha_companies의 기업명:")
        alpha_company_names = []
        for company in alpha_companies_result.data:
            company_no = company.get('No.')
            full_name = company.get('사업아이템 한 줄 소개', '')
            # "기업명 - 사업아이템" 형태에서 기업명만 추출
            company_name = full_name.split(' - ')[0] if ' - ' in full_name else full_name
            alpha_company_names.append(company_name)
            print(f"   No.{company_no}: {company_name}")
        
        print(f"\n총 {len(alpha_company_names)}개 기업명")
    
    # recommendations2 테이블의 기업명 확인
    print("\n📊 recommendations2 테이블의 기업명 (샘플):")
    try:
        rec2_result = supabase.table('recommendations2').select('기업명').limit(20).execute()
        if rec2_result.data:
            rec2_company_names = [record['기업명'] for record in rec2_result.data if record.get('기업명')]
            unique_names = list(set(rec2_company_names))
            print(f"   샘플 {len(rec2_company_names)}개 중 고유 기업명 {len(unique_names)}개:")
            for name in sorted(unique_names):
                print(f"   - {name}")
            
            # 매칭 확인
            print(f"\n🔗 매칭 확인:")
            matches = []
            for alpha_name in alpha_company_names:
                for rec2_name in unique_names:
                    if alpha_name in rec2_name or rec2_name in alpha_name:
                        matches.append((alpha_name, rec2_name))
            
            if matches:
                print(f"   {len(matches)}개 매칭 발견:")
                for alpha_name, rec2_name in matches:
                    print(f"   {alpha_name} ↔ {rec2_name}")
            else:
                print("   ❌ 매칭되는 기업명이 없습니다!")
        else:
            print("   데이터 없음")
    except Exception as e:
        print(f"   오류: {e}")
    
    # recommendations3_active 테이블의 기업명 확인
    print("\n📊 recommendations3_active 테이블의 기업명 (샘플):")
    try:
        rec3_result = supabase.table('recommendations3_active').select('기업명').limit(20).execute()
        if rec3_result.data:
            rec3_company_names = [record['기업명'] for record in rec3_result.data if record.get('기업명')]
            unique_names = list(set(rec3_company_names))
            print(f"   샘플 {len(rec3_company_names)}개 중 고유 기업명 {len(unique_names)}개:")
            for name in sorted(unique_names):
                print(f"   - {name}")
            
            # 매칭 확인
            print(f"\n🔗 매칭 확인:")
            matches = []
            for alpha_name in alpha_company_names:
                for rec3_name in unique_names:
                    if alpha_name in rec3_name or rec3_name in alpha_name:
                        matches.append((alpha_name, rec3_name))
            
            if matches:
                print(f"   {len(matches)}개 매칭 발견:")
                for alpha_name, rec3_name in matches:
                    print(f"   {alpha_name} ↔ {rec3_name}")
            else:
                print("   ❌ 매칭되는 기업명이 없습니다!")
        else:
            print("   데이터 없음")
    except Exception as e:
        print(f"   오류: {e}")

def main():
    """메인 함수"""
    print("🔍 추천 데이터 기업명 매칭 확인 (v2)")
    print("=" * 40)
    
    supabase = init_supabase()
    if not supabase:
        print("❌ Supabase 연결 실패")
        return
    
    check_company_names_in_recommendations(supabase)

if __name__ == "__main__":
    main()






