-- Supabase 데이터베이스 스키마
-- 정부지원사업 맞춤 추천 시스템

-- 회사 테이블
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    business_type VARCHAR(50),
    region VARCHAR(100),
    years INTEGER DEFAULT 0,
    stage VARCHAR(50),
    industry VARCHAR(100),
    keywords TEXT[],
    preferred_uses TEXT[],
    preferred_budget VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 공고 테이블
CREATE TABLE announcements (
    id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    agency VARCHAR(255),
    source VARCHAR(100),
    region VARCHAR(100),
    stage VARCHAR(50),
    due_date DATE,
    info_session_date DATE,
    amount_krw BIGINT,
    amount_text TEXT,
    allowed_uses TEXT[],
    keywords TEXT[],
    budget_band VARCHAR(50),
    update_type VARCHAR(50),
    url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 추천 결과 테이블
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    announcement_id VARCHAR(50) REFERENCES announcements(id) ON DELETE CASCADE,
    rank INTEGER,
    score DECIMAL(5,2),
    reason TEXT,
    start_date DATE,
    end_date DATE,
    remaining_days INTEGER,
    amount_krw BIGINT,
    amount_text TEXT,
    allowed_uses TEXT[],
    status VARCHAR(50),
    year INTEGER,
    month INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 알림 상태 테이블
CREATE TABLE notification_states (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    last_seen_announcement_ids TEXT[],
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_companies_stage ON companies(stage);
CREATE INDEX idx_companies_region ON companies(region);
CREATE INDEX idx_announcements_due_date ON announcements(due_date);
CREATE INDEX idx_announcements_agency ON announcements(agency);
CREATE INDEX idx_announcements_source ON announcements(source);
CREATE INDEX idx_recommendations_company_id ON recommendations(company_id);
CREATE INDEX idx_recommendations_announcement_id ON recommendations(announcement_id);
CREATE INDEX idx_recommendations_rank ON recommendations(rank);
CREATE INDEX idx_notification_states_company_id ON notification_states(company_id);

-- RLS (Row Level Security) 설정
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE announcements ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_states ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기/쓰기 가능하도록 설정 (실제 운영시에는 인증 기반으로 변경)
CREATE POLICY "Enable all operations for all users" ON companies FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON announcements FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON recommendations FOR ALL USING (true);
CREATE POLICY "Enable all operations for all users" ON notification_states FOR ALL USING (true);
