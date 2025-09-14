-- Initial database schema for Korean Reading Comprehension System
-- Migration: 001_initial_schema.sql

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    full_name VARCHAR(100),
    grade_level INTEGER,
    school VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Content items (reading passages and questions)
CREATE TABLE IF NOT EXISTS content_items (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(100) UNIQUE NOT NULL,
    task_type VARCHAR(20) NOT NULL, -- 'paragraph' or 'article'
    title VARCHAR(200),
    difficulty VARCHAR(20) DEFAULT 'medium',
    topic VARCHAR(100),
    tags TEXT[], -- Array of tags
    content JSONB NOT NULL, -- Full content JSON
    metadata JSONB, -- Additional metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(id),
    active BOOLEAN DEFAULT true
);

-- Student responses
CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    content_item_id INTEGER REFERENCES content_items(id),
    question_type VARCHAR(50) NOT NULL,
    question_key VARCHAR(100) NOT NULL,
    response_data JSONB NOT NULL,
    is_correct BOOLEAN,
    score DECIMAL(5,2),
    time_taken_seconds INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graded_at TIMESTAMP,
    feedback TEXT
);

-- Study sessions
CREATE TABLE IF NOT EXISTS study_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_name VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_time_seconds INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT false,
    session_data JSONB -- Configuration and state
);

-- Response analytics
CREATE TABLE IF NOT EXISTS response_analytics (
    id SERIAL PRIMARY KEY,
    content_item_id INTEGER REFERENCES content_items(id),
    question_type VARCHAR(50) NOT NULL,
    question_key VARCHAR(100) NOT NULL,
    total_responses INTEGER DEFAULT 0,
    correct_responses INTEGER DEFAULT 0,
    average_time_seconds DECIMAL(8,2),
    difficulty_score DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    total_time_seconds INTEGER DEFAULT 0,
    best_streak INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mastery_level DECIMAL(5,2) DEFAULT 0.0,
    UNIQUE(user_id, topic, difficulty)
);

-- Learning objectives and curriculum
CREATE TABLE IF NOT EXISTS learning_objectives (
    id SERIAL PRIMARY KEY,
    objective_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    grade_level INTEGER,
    category VARCHAR(100),
    difficulty VARCHAR(20),
    prerequisites TEXT[], -- Array of prerequisite objective codes
    active BOOLEAN DEFAULT true
);

-- Content mapping to learning objectives
CREATE TABLE IF NOT EXISTS content_objectives (
    id SERIAL PRIMARY KEY,
    content_item_id INTEGER REFERENCES content_items(id),
    objective_id INTEGER REFERENCES learning_objectives(id),
    coverage_weight DECIMAL(3,2) DEFAULT 1.0 -- How well this content covers the objective
);

-- Teacher/Admin data
CREATE TABLE IF NOT EXISTS classrooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    teacher_id INTEGER REFERENCES users(id),
    grade_level INTEGER,
    subject VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Student-classroom relationships
CREATE TABLE IF NOT EXISTS classroom_students (
    id SERIAL PRIMARY KEY,
    classroom_id INTEGER REFERENCES classrooms(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true,
    UNIQUE(classroom_id, student_id)
);

-- Assignments
CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    classroom_id INTEGER REFERENCES classrooms(id),
    teacher_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_items INTEGER[], -- Array of content item IDs
    due_date TIMESTAMP,
    time_limit_minutes INTEGER,
    max_attempts INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Assignment submissions
CREATE TABLE IF NOT EXISTS assignment_submissions (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER REFERENCES assignments(id),
    student_id INTEGER REFERENCES users(id),
    attempt_number INTEGER DEFAULT 1,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    total_score DECIMAL(5,2),
    time_taken_seconds INTEGER,
    completed BOOLEAN DEFAULT false,
    submission_data JSONB -- Detailed responses and scoring
);

-- System logs
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    message TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_content_items_item_id ON content_items(item_id);
CREATE INDEX IF NOT EXISTS idx_content_items_task_type ON content_items(task_type);
CREATE INDEX IF NOT EXISTS idx_content_items_difficulty ON content_items(difficulty);
CREATE INDEX IF NOT EXISTS idx_content_items_topic ON content_items(topic);
CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);
CREATE INDEX IF NOT EXISTS idx_responses_content_item_id ON responses(content_item_id);
CREATE INDEX IF NOT EXISTS idx_responses_submitted_at ON responses(submitted_at);
CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id ON study_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_started_at ON study_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_topic ON user_progress(topic);
CREATE INDEX IF NOT EXISTS idx_classroom_students_classroom_id ON classroom_students(classroom_id);
CREATE INDEX IF NOT EXISTS idx_classroom_students_student_id ON classroom_students(student_id);
CREATE INDEX IF NOT EXISTS idx_assignment_submissions_assignment_id ON assignment_submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_assignment_submissions_student_id ON assignment_submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_category ON system_logs(category);
CREATE INDEX IF NOT EXISTS idx_system_logs_created_at ON system_logs(created_at);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_content_items_content ON content_items USING GIN(content);
CREATE INDEX IF NOT EXISTS idx_content_items_tags ON content_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_responses_response_data ON responses USING GIN(response_data);
CREATE INDEX IF NOT EXISTS idx_system_logs_metadata ON system_logs USING GIN(metadata);

-- Create functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for cleaning expired sessions
CREATE OR REPLACE FUNCTION clean_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Initial data setup
INSERT INTO learning_objectives (objective_code, title, description, grade_level, category, difficulty) VALUES
('KR_RC_01', '사실적 읽기', '글에 나타난 정보를 정확하게 파악하여 읽는다', 9, '읽기', 'easy'),
('KR_RC_02', '추론적 읽기', '글에 드러나지 않은 정보를 추론하여 읽는다', 9, '읽기', 'medium'),
('KR_RC_03', '비판적 읽기', '글의 내용을 비판적으로 평가하며 읽는다', 9, '읽기', 'hard'),
('KR_RC_04', '창의적 읽기', '글을 읽고 창의적으로 재구성하거나 적용한다', 9, '읽기', 'hard'),
('KR_RC_05', '중심 내용 파악', '글의 중심 내용과 주제를 파악한다', 9, '읽기', 'medium'),
('KR_RC_06', '핵심어 추출', '글의 핵심어와 중요한 정보를 추출한다', 9, '읽기', 'easy'),
('KR_RC_07', '글의 구조 파악', '글의 전개 방식과 구조를 파악한다', 9, '읽기', 'medium'),
('KR_RC_08', '문맥적 의미', '문맥을 통해 단어나 문장의 의미를 파악한다', 9, '읽기', 'medium');

-- Create default admin user (password should be changed in production)
INSERT INTO users (username, email, password_hash, role, full_name) VALUES
('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvOcV0P8eLAD1zu', 'admin', 'System Administrator');

COMMIT;