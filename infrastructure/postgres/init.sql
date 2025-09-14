-- PostgreSQL initialization script for Korean Reading JSON system

-- Create databases
CREATE DATABASE IF NOT EXISTS reading_json;
CREATE DATABASE IF NOT EXISTS reading_json_test;

-- Switch to main database
\c reading_json;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS content;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS grading;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Users table
CREATE TABLE IF NOT EXISTS users.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users.users(email);
CREATE INDEX idx_users_username ON users.users(username);
CREATE INDEX idx_users_role ON users.users(role);
CREATE INDEX idx_users_created_at ON users.users(created_at DESC);

-- Content items table (paragraphs and articles)
CREATE TABLE IF NOT EXISTS content.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('paragraph', 'article')),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    difficulty VARCHAR(50) DEFAULT 'medium',
    tags TEXT[],
    metadata JSONB NOT NULL,
    created_by UUID REFERENCES users.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1
);

-- Create indexes for content items
CREATE INDEX idx_items_item_id ON content.items(item_id);
CREATE INDEX idx_items_task_type ON content.items(task_type);
CREATE INDEX idx_items_difficulty ON content.items(difficulty);
CREATE INDEX idx_items_tags ON content.items USING gin(tags);
CREATE INDEX idx_items_created_at ON content.items(created_at DESC);
CREATE INDEX idx_items_metadata ON content.items USING gin(metadata);

-- Questions table
CREATE TABLE IF NOT EXISTS content.questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES content.items(id) ON DELETE CASCADE,
    question_type VARCHAR(100) NOT NULL,
    question_text TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT,
    evaluation_criteria JSONB,
    points INTEGER DEFAULT 10,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for questions
CREATE INDEX idx_questions_item_id ON content.questions(item_id);
CREATE INDEX idx_questions_type ON content.questions(question_type);

-- Student submissions table
CREATE TABLE IF NOT EXISTS grading.submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES content.items(id) ON DELETE CASCADE,
    submission_data JSONB NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by UUID REFERENCES users.users(id),
    feedback TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for submissions
CREATE INDEX idx_submissions_student_id ON grading.submissions(student_id);
CREATE INDEX idx_submissions_item_id ON grading.submissions(item_id);
CREATE INDEX idx_submissions_status ON grading.submissions(status);
CREATE INDEX idx_submissions_submitted_at ON grading.submissions(submitted_at DESC);

-- Grading results table
CREATE TABLE IF NOT EXISTS grading.results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID REFERENCES grading.submissions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES content.questions(id) ON DELETE CASCADE,
    student_answer TEXT,
    is_correct BOOLEAN,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2),
    similarity_score DECIMAL(5,4),
    feedback TEXT,
    evaluation_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for results
CREATE INDEX idx_results_submission_id ON grading.results(submission_id);
CREATE INDEX idx_results_question_id ON grading.results(question_id);

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users.users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for analytics
CREATE INDEX idx_events_user_id ON analytics.events(user_id);
CREATE INDEX idx_events_type ON analytics.events(event_type);
CREATE INDEX idx_events_created_at ON analytics.events(created_at DESC);
CREATE INDEX idx_events_session_id ON analytics.events(session_id);

-- Performance statistics table
CREATE TABLE IF NOT EXISTS analytics.performance_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
    period_type VARCHAR(50) NOT NULL, -- daily, weekly, monthly
    period_start DATE NOT NULL,
    total_submissions INTEGER DEFAULT 0,
    total_score DECIMAL(10,2) DEFAULT 0,
    max_possible_score DECIMAL(10,2) DEFAULT 0,
    average_score DECIMAL(5,2),
    completion_rate DECIMAL(5,2),
    strongest_topics TEXT[],
    weakest_topics TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, period_type, period_start)
);

-- Create indexes for performance stats
CREATE INDEX idx_performance_student_id ON analytics.performance_stats(student_id);
CREATE INDEX idx_performance_period ON analytics.performance_stats(period_type, period_start DESC);

-- Sessions table for authentication
CREATE TABLE IF NOT EXISTS users.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for sessions
CREATE INDEX idx_sessions_user_id ON users.sessions(user_id);
CREATE INDEX idx_sessions_token_hash ON users.sessions(token_hash);
CREATE INDEX idx_sessions_expires_at ON users.sessions(expires_at);

-- Create update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON content.items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON content.questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to calculate user statistics
CREATE OR REPLACE FUNCTION calculate_user_statistics(p_user_id UUID)
RETURNS TABLE(
    total_submissions BIGINT,
    average_score NUMERIC,
    completion_rate NUMERIC,
    last_activity TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_submissions,
        AVG(total_score)::NUMERIC as average_score,
        (COUNT(CASE WHEN status = 'completed' THEN 1 END)::NUMERIC / NULLIF(COUNT(*)::NUMERIC, 0) * 100) as completion_rate,
        MAX(submitted_at) as last_activity
    FROM grading.submissions
    WHERE student_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Create materialized view for leaderboard
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.leaderboard AS
SELECT 
    u.id as user_id,
    u.username,
    u.full_name,
    COUNT(DISTINCT s.id) as total_submissions,
    AVG(s.total_score) as average_score,
    SUM(s.total_score) as total_points,
    COUNT(DISTINCT DATE(s.submitted_at)) as active_days,
    MAX(s.submitted_at) as last_activity
FROM users.users u
LEFT JOIN grading.submissions s ON u.id = s.student_id
WHERE u.role = 'student' AND u.is_active = true
GROUP BY u.id, u.username, u.full_name
ORDER BY average_score DESC NULLS LAST;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_leaderboard_user_id ON analytics.leaderboard(user_id);

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA users TO reading_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA content TO reading_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA grading TO reading_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO reading_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA users TO reading_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA content TO reading_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA grading TO reading_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO reading_admin;