#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신규 회사 추가 및 자동 추천 생성 기능
- 신규 회사 추가 시 자동으로 맞춤 추천 생성
- biz2 + kstartup2 데이터 기반 추천
- Supabase 테이블 연동
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client
import os

def enhanced_save_company_with_recommendations(company_data: Dict, supabase: Client) -> bool:
    """신규 회사 추가 및 자동 추천 생성"""
    try:
        # 1. 회사 데이터를 alpha_companies2 테이블에 저장
        company_insert_data = {
            'No.': company_data.get('id', None),  # 자동 생성되면 None
            '기업명': company_data['name'],
            '기업형태': company_data['business_type'],
            '소재지': company_data['region'],
            '설립연월일': company_data.get('설립일', ''),
            '주업종 (사업자등록증 상)': company_data['industry'],
            '주요 산업': company_data['industry'],
            '사업아이템 한 줄 소개': f"{company_data['name']} - {company_data.get('description', '')}",
            '특화분야': ', '.join(company_data.get('keywords', [])),
            '#매출': company_data.get('매출', ''),
            '#고용': company_data.get('고용', ''),
            '#기술특허(등록)': company_data.get('특허', ''),
            '#기업인증': company_data.get('인증', ''),
            '업력': company_data.get('years', 0),
            '성장단계': company_data.get('stage', '예비'),
            '선호지원용도': ', '.join(company_data.get('preferred_uses', [])),
            '선호예산규모': company_data.get('preferred_budget', '소액')
        }
        
        # 회사 저장
        result = supabase.table('alpha_companies2').insert(company_insert_data).execute()
        
        if not result.data:
            st.error("회사 저장 실패")
            return False
        
        # 저장된 회사의 ID 가져오기
        company_id = result.data[0]['No.']
        
        # 2. 자동 추천 생성
        recommendations = generate_company_recommendations(company_data, supabase)
        
        if recommendations:
            # 3. 추천 결과를 recommend2 테이블에 저장
            save_recommendations_to_supabase(company_id, recommendations, supabase)
            
            # 4. 알림 상태 초기화
            initialize_notification_state(company_id, supabase)
            
            st.success(f"✅ 회사가 추가되었습니다! (ID: {company_id})")
            st.success(f"🎯 {len(recommendations)}개의 맞춤 추천이 생성되었습니다!")
            
            return True
        else:
            st.warning("회사는 추가되었지만 추천 생성에 실패했습니다.")
            return True
            
    except Exception as e:
        st.error(f"회사 추가 및 추천 생성 실패: {e}")
        return False

def generate_company_recommendations(company_data: Dict, supabase: Client) -> List[Dict]:
    """신규 회사에 대한 맞춤 추천 생성"""
    try:
        recommendations = []
        
        # 1. biz2 데이터에서 추천 생성
        biz_recommendations = generate_biz_recommendations(company_data, supabase)
        recommendations.extend(biz_recommendations)
        
        # 2. kstartup2 데이터에서 추천 생성
        kstartup_recommendations = generate_kstartup_recommendations(company_data, supabase)
        recommendations.extend(kstartup_recommendations)
        
        # 3. 추천 결과 정렬 및 중복 제거
        recommendations = deduplicate_and_sort_recommendations(recommendations)
        
        return recommendations[:20]  # 상위 20개만 반환
        
    except Exception as e:
        st.error(f"추천 생성 실패: {e}")
        return []

def generate_biz_recommendations(company_data: Dict, supabase: Client) -> List[Dict]:
    """기업마당(biz2) 데이터 기반 추천 생성"""
    try:
        # biz2 데이터 로드
        result = supabase.table('biz2').select('*').execute()
        if not result.data:
            return []
        
        biz_df = pd.DataFrame(result.data)
        recommendations = []
        
        # 업종 매칭
        industry = company_data.get('industry', '')
        keywords = company_data.get('keywords', [])
        
        for _, announcement in biz_df.iterrows():
            score = 0
            matching_reasons = []
            
            # 업종 매칭
            if industry and '지원분야' in announcement:
                if industry in str(announcement['지원분야']):
                    score += 80
                    matching_reasons.append(f"업종 매칭: {industry}")
            
            # 키워드 매칭
            for keyword in keywords:
                if keyword and '공고명' in announcement:
                    if keyword in str(announcement['공고명']):
                        score += 70
                        matching_reasons.append(f"키워드 매칭: {keyword}")
                        break
            
            # 지역 매칭
            region = company_data.get('region', '')
            if region and '소관부처' in announcement:
                if region in str(announcement['소관부처']):
                    score += 60
                    matching_reasons.append(f"지역 매칭: {region}")
            
            if score > 0:
                recommendations.append({
                    'company_id': company_data.get('id'),
                    'company_name': company_data['name'],
                    'announcement_title': announcement.get('공고명', ''),
                    'announcement_source': '기업마당',
                    'total_score': score,
                    'matching_reason': '; '.join(matching_reasons),
                    'application_start_date': announcement.get('신청시작일자', ''),
                    'application_end_date': announcement.get('신청종료일자', ''),
                    'detail_page_url': announcement.get('공고상세URL', ''),
                    'announcement_details': f"소관부처: {announcement.get('소관부처', 'N/A')}, 사업수행기관: {announcement.get('사업수행기관', 'N/A')}",
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        return recommendations
        
    except Exception as e:
        st.error(f"biz2 추천 생성 실패: {e}")
        return []

def generate_kstartup_recommendations(company_data: Dict, supabase: Client) -> List[Dict]:
    """K-스타트업(kstartup2) 데이터 기반 추천 생성"""
    try:
        # kstartup2 데이터 로드
        result = supabase.table('kstartup2').select('*').execute()
        if not result.data:
            return []
        
        kstartup_df = pd.DataFrame(result.data)
        recommendations = []
        
        # 업종 및 키워드 매칭
        industry = company_data.get('industry', '')
        keywords = company_data.get('keywords', [])
        
        for _, announcement in kstartup_df.iterrows():
            score = 0
            matching_reasons = []
            
            # 업종 매칭
            if industry and '지원사업분류' in announcement:
                if industry in str(announcement['지원사업분류']):
                    score += 80
                    matching_reasons.append(f"업종 매칭: {industry}")
            
            # 키워드 매칭 (공고내용에서)
            for keyword in keywords:
                if keyword and '공고내용' in announcement:
                    if keyword in str(announcement['공고내용']):
                        score += 70
                        matching_reasons.append(f"키워드 매칭: {keyword}")
                        break
            
            # 사업아이템 매칭
            if '사업아이템 한 줄 소개' in company_data:
                business_item = company_data['사업아이템 한 줄 소개']
                if business_item and '공고내용' in announcement:
                    if business_item in str(announcement['공고내용']):
                        score += 90
                        matching_reasons.append("사업아이템 매칭")
            
            if score > 0:
                recommendations.append({
                    'company_id': company_data.get('id'),
                    'company_name': company_data['name'],
                    'announcement_title': announcement.get('사업공고명', ''),
                    'announcement_source': 'K-스타트업',
                    'total_score': score,
                    'matching_reason': '; '.join(matching_reasons),
                    'application_start_date': announcement.get('공고접수시작일시', ''),
                    'application_end_date': announcement.get('공고접수종료일시', ''),
                    'detail_page_url': announcement.get('상세페이지 url', ''),
                    'announcement_details': announcement.get('공고내용', '')[:200] + '...' if len(str(announcement.get('공고내용', ''))) > 200 else announcement.get('공고내용', ''),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
        
        return recommendations
        
    except Exception as e:
        st.error(f"kstartup2 추천 생성 실패: {e}")
        return []

def deduplicate_and_sort_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """추천 결과 중복 제거 및 정렬"""
    try:
        # 중복 제거 (공고제목 기준)
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            key = (rec['company_id'], rec['announcement_title'])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        # 점수 기준으로 정렬
        unique_recommendations.sort(key=lambda x: x['total_score'], reverse=True)
        
        return unique_recommendations
        
    except Exception as e:
        st.error(f"추천 정렬 실패: {e}")
        return recommendations

def save_recommendations_to_supabase(company_id: int, recommendations: List[Dict], supabase: Client):
    """추천 결과를 Supabase에 저장"""
    try:
        for rec in recommendations:
            rec['company_id'] = company_id
            supabase.table('recommend2').insert(rec).execute()
        
        st.info(f"📊 {len(recommendations)}개 추천이 recommend2 테이블에 저장되었습니다.")
        
    except Exception as e:
        st.error(f"추천 저장 실패: {e}")

def initialize_notification_state(company_id: int, supabase: Client):
    """알림 상태 초기화"""
    try:
        notification_data = {
            'company_id': company_id,
            'last_seen_announcement_ids': [],
            'last_updated': datetime.now().isoformat()
        }
        
        supabase.table('notification_states').insert(notification_data).execute()
        st.info(f"🔔 알림 상태가 초기화되었습니다.")
        
    except Exception as e:
        st.error(f"알림 상태 초기화 실패: {e}")

def render_enhanced_company_management(supabase: Client):
    """향상된 회사 관리 탭 렌더링"""
    st.subheader("🏢 회사 관리")
    
    # 기존 회사 목록
    companies_df = load_companies()
    
    if not companies_df.empty:
        st.write("### 기존 회사 목록")
        
        # 회사 선택
        company_options = [f"{row['company_name']} ({row['industry']})" for _, row in companies_df.iterrows()]
        selected_company = st.selectbox("회사 선택", company_options, key="company_selector")
        
        if selected_company:
            # 선택된 회사 정보 표시
            company_name = selected_company.split(' (')[0]
            company_row = companies_df[companies_df['company_name'] == company_name].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**회사명**: {company_row['company_name']}")
                st.write(f"**업종**: {company_row['industry']}")
                st.write(f"**지역**: {company_row['region']}")
            
            with col2:
                st.write(f"**업력**: {company_row.get('years', 'N/A')}년")
                st.write(f"**성장단계**: {company_row.get('stage', 'N/A')}")
                st.write(f"**특화분야**: {company_row.get('keywords', 'N/A')}")
            
            # 회사 선택 시 세션 상태 업데이트
            if st.button("이 회사 선택", key="select_company_btn"):
                st.session_state['selected_company'] = company_row.to_dict()
                st.success(f"{company_name}이 선택되었습니다!")
                st.rerun()
    
    st.divider()
    
    # 신규 회사 추가 폼
    st.write("### 신규 회사 추가")
    
    with st.form("enhanced_new_company_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("회사명 *", key="enhanced_name")
            business_type = st.selectbox("사업자 유형", ["법인", "개인", "예비창업"], key="enhanced_business_type")
            region = st.text_input("지역 *", key="enhanced_region")
            industry = st.text_input("업종 *", key="enhanced_industry")
            years = st.number_input("업력 (년)", min_value=0, max_value=100, value=0, key="enhanced_years")
        
        with col2:
            stage = st.selectbox("성장단계", ["예비", "초기", "성장", "성숙"], key="enhanced_stage")
            keywords = st.text_input("특화분야/키워드 (쉼표로 구분) *", key="enhanced_keywords")
            preferred_uses = st.text_input("선호 지원용도 (쉼표로 구분)", key="enhanced_preferred_uses")
            preferred_budget = st.selectbox("선호 예산규모", ["소액", "중간", "대형"], key="enhanced_preferred_budget")
            description = st.text_area("사업아이템 설명", key="enhanced_description")
        
        # 추가 정보
        st.write("#### 추가 정보 (선택사항)")
        col3, col4 = st.columns(2)
        with col3:
            revenue = st.text_input("매출", key="enhanced_revenue")
            employees = st.text_input("고용인원", key="enhanced_employees")
        with col4:
            patents = st.text_input("특허 수", key="enhanced_patents")
            certifications = st.text_input("기업인증", key="enhanced_certifications")
        
        if st.form_submit_button("🚀 신규 회사 추가 및 자동 추천 생성"):
            if name and region and industry and keywords:
                company_data = {
                    'name': name,
                    'business_type': business_type,
                    'region': region,
                    'years': years,
                    'stage': stage,
                    'industry': industry,
                    'keywords': [k.strip() for k in keywords.split(',') if k.strip()],
                    'preferred_uses': [u.strip() for u in preferred_uses.split(',') if u.strip()] if preferred_uses else [],
                    'preferred_budget': preferred_budget,
                    'description': description,
                    '매출': revenue,
                    '고용': employees,
                    '특허': patents,
                    '인증': certifications
                }
                
                # 신규 회사 추가 및 자동 추천 생성
                if enhanced_save_company_with_recommendations(company_data, supabase):
                    st.success("🎉 신규 회사가 추가되고 맞춤 추천이 생성되었습니다!")
                    st.info("💡 이제 사이드바에서 새로 추가된 회사를 선택하여 추천 데이터를 확인할 수 있습니다.")
                    st.rerun()
            else:
                st.error("❌ 필수 항목(회사명, 지역, 업종, 특화분야)을 모두 입력해주세요.")

def load_companies():
    """회사 데이터 로드"""
    try:
        result = supabase.table('alpha_companies2').select('*').execute()
        df = pd.DataFrame(result.data)
        
        if not df.empty:
            # 기업명 추출
            if '사업아이템 한 줄 소개' in df.columns:
                df['company_name'] = df['사업아이템 한 줄 소개'].str.extract(r'^([^-]+) - ')[0].str.strip()
                df['company_name'] = df['company_name'].fillna(df['사업아이템 한 줄 소개'])
            
            # 컬럼명 매핑
            df = df.rename(columns={
                'No.': 'id',
                '기업형태': 'business_type',
                '소재지': 'region',
                '주업종 (사업자등록증 상)': 'industry',
                '특화분야': 'keywords'
            })
        
        return df
    except Exception as e:
        st.error(f"회사 데이터 로드 실패: {e}")
        return pd.DataFrame()



