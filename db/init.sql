-- Korean Reading Comprehension System Database Schema
-- PostgreSQL 15+ with JSONB support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');
CREATE TYPE task_type AS ENUM ('paragraph', 'article');
CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard', 'advanced');
CREATE TYPE reading_level AS ENUM ('beginner', 'intermediate', 'advanced', 'expert');
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE generation_method AS ENUM ('rule_based', 'llm_gpt4', 'llm_claude', 'llm_kogpt', 'hybrid');

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'student',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

-- Student Profiles
CREATE TABLE student_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    grade_level INT NOT NULL CHECK (grade_level BETWEEN 1 AND 3),
    school VARCHAR(255),
    reading_level reading_level DEFAULT 'intermediate',
    preferences JSONB DEFAULT '{}',
    learning_style VARCHAR(50),
    total_study_time INT DEFAULT 0, -- in seconds
    streak_days INT DEFAULT 0,
    last_study_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content Items (Enhanced)
CREATE TABLE content_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    legacy_id VARCHAR(100) UNIQUE, -- For backward compatibility with existing JSON files
    task_type task_type NOT NULL,
    content_data JSONB NOT NULL,
    difficulty difficulty_level NOT NULL DEFAULT 'medium',
    tags TEXT[],
    topic VARCHAR(255),
    keywords TEXT[],
    generation_method generation_method DEFAULT 'rule_based',
    llm_model VARCHAR(100),
    llm_prompt_template TEXT,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    usage_count INT DEFAULT 0,
    avg_completion_time INT, -- in seconds
    avg_score DECIMAL(5,2),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for content_items
CREATE INDEX idx_content_items_task_type ON content_items(task_type);
CREATE INDEX idx_content_items_difficulty ON content_items(difficulty);
CREATE INDEX idx_content_items_topic ON content_items(topic);
CREATE INDEX idx_content_items_tags ON content_items USING GIN(tags);
CREATE INDEX idx_content_items_active ON content_items(is_active);
CREATE INDEX idx_content_items_created_at ON content_items(created_at DESC);

-- Student Submissions
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    submission_data JSONB NOT NULL,
    time_spent INT, -- in seconds
    submitted_at TIMESTAMP DEFAULT NOW(),
    processing_status processing_status DEFAULT 'pending',
    processed_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    session_id VARCHAR(255)
);

-- Create indexes for submissions
CREATE INDEX idx_submissions_user_id ON submissions(user_id);
CREATE INDEX idx_submissions_content_id ON submissions(content_id);
CREATE INDEX idx_submissions_status ON submissions(processing_status);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at DESC);
CREATE UNIQUE INDEX idx_submissions_user_content ON submissions(user_id, content_id, submitted_at);

-- Grading Results
CREATE TABLE grading_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    mcq_score DECIMAL(5,2),
    mcq_details JSONB, -- detailed MCQ results
    free_text_similarity DECIMAL(5,4),
    pos_requirements_met BOOLEAN,
    keyword_matches TEXT[],
    feedback_text TEXT,
    feedback_type VARCHAR(50), -- 'auto', 'manual', 'ai_generated'
    detailed_analysis JSONB,
    graded_at TIMESTAMP DEFAULT NOW(),
    grading_method generation_method DEFAULT 'rule_based',
    grader_id UUID REFERENCES users(id) -- for manual grading
);

-- Create indexes for grading_results
CREATE INDEX idx_grading_results_submission_id ON grading_results(submission_id);
CREATE INDEX idx_grading_results_graded_at ON grading_results(graded_at DESC);

-- Learning Progress
CREATE TABLE learning_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    attempt_count INT DEFAULT 1,
    best_score DECIMAL(5,2),
    last_score DECIMAL(5,2),
    time_spent_total INT DEFAULT 0, -- cumulative in seconds
    completed BOOLEAN DEFAULT false,
    mastery_level DECIMAL(5,2), -- 0-100 scale
    last_attempt_at TIMESTAMP DEFAULT NOW(),
    first_attempt_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    UNIQUE(user_id, content_id)
);

-- Create indexes for learning_progress
CREATE INDEX idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX idx_learning_progress_content_id ON learning_progress(content_id);
CREATE INDEX idx_learning_progress_completed ON learning_progress(completed);
CREATE INDEX idx_learning_progress_last_attempt ON learning_progress(last_attempt_at DESC);

-- Analytics Events
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50),
    event_data JSONB,
    page_url TEXT,
    referrer TEXT,
    session_id VARCHAR(255),
    client_info JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for analytics_events
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_events_created_at ON analytics_events(created_at DESC);
CREATE INDEX idx_analytics_events_session ON analytics_events(session_id);

-- Learning Paths
CREATE TABLE learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    target_grade_level INT,
    difficulty_progression difficulty_level[],
    content_sequence UUID[],
    prerequisites JSONB,
    estimated_hours INT,
    completion_criteria JSONB,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for learning_paths
CREATE INDEX idx_learning_paths_grade_level ON learning_paths(target_grade_level);
CREATE INDEX idx_learning_paths_active ON learning_paths(is_active);
CREATE INDEX idx_learning_paths_public ON learning_paths(is_public);

-- User Learning Path Enrollment
CREATE TABLE learning_path_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    current_position INT DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(user_id, path_id)
);

-- Adaptive Learning Rules
CREATE TABLE adaptive_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    condition_type VARCHAR(100), -- 'score_threshold', 'time_based', 'attempt_based'
    condition_params JSONB,
    action_type VARCHAR(100), -- 'adjust_difficulty', 'recommend_content', 'provide_hint'
    action_params JSONB,
    priority INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Achievements and Badges
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url TEXT,
    criteria JSONB NOT NULL,
    points INT DEFAULT 0,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Achievements
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- Study Sessions
CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration INT, -- in seconds
    content_items_studied UUID[],
    submissions_made INT DEFAULT 0,
    correct_answers INT DEFAULT 0,
    session_data JSONB
);

-- Create indexes for study_sessions
CREATE INDEX idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX idx_study_sessions_started_at ON study_sessions(started_at DESC);

-- Teacher Assignments
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content_items UUID[],
    assigned_to UUID[], -- array of student user_ids
    due_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Feedback Templates
CREATE TABLE feedback_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    condition_type VARCHAR(100),
    condition_params JSONB,
    feedback_text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'ko',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create materialized view for user statistics
CREATE MATERIALIZED VIEW user_statistics AS
SELECT 
    u.id as user_id,
    u.username,
    sp.grade_level,
    sp.reading_level,
    COUNT(DISTINCT s.content_id) as unique_content_attempted,
    COUNT(s.id) as total_submissions,
    AVG(gr.mcq_score) as avg_mcq_score,
    AVG(gr.free_text_similarity) as avg_similarity_score,
    SUM(s.time_spent) as total_time_spent,
    MAX(s.submitted_at) as last_activity
FROM users u
LEFT JOIN student_profiles sp ON u.id = sp.user_id
LEFT JOIN submissions s ON u.id = s.user_id
LEFT JOIN grading_results gr ON s.id = gr.submission_id
WHERE u.role = 'student'
GROUP BY u.id, u.username, sp.grade_level, sp.reading_level;

-- Create index on materialized view
CREATE INDEX idx_user_statistics_user_id ON user_statistics(user_id);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_user_statistics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_statistics;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_profiles_updated_at BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_items_updated_at BEFORE UPDATE ON content_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated_at BEFORE UPDATE ON learning_paths
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_adaptive_rules_updated_at BEFORE UPDATE ON adaptive_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to update content usage statistics
CREATE OR REPLACE FUNCTION update_content_usage_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE content_items
    SET usage_count = usage_count + 1
    WHERE id = NEW.content_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_content_usage AFTER INSERT ON submissions
    FOR EACH ROW EXECUTE FUNCTION update_content_usage_stats();

-- Initial data insertions
INSERT INTO achievements (name, description, criteria, points, category) VALUES
('첫 걸음', '첫 문제를 풀어보았습니다', '{"type": "first_submission"}', 10, 'milestone'),
('연속 학습 3일', '3일 연속으로 학습했습니다', '{"type": "streak", "days": 3}', 30, 'streak'),
('연속 학습 7일', '7일 연속으로 학습했습니다', '{"type": "streak", "days": 7}', 70, 'streak'),
('완벽주의자', '한 문제에서 100점을 받았습니다', '{"type": "perfect_score"}', 50, 'performance'),
('꾸준한 학습자', '총 10시간 학습했습니다', '{"type": "study_time", "hours": 10}', 100, 'dedication');

-- Create default admin user (password: admin123)
INSERT INTO users (email, username, password_hash, role, email_verified) VALUES
('admin@reading-json.local', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY3ppjf.8.XjIIO', 'admin', true);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;