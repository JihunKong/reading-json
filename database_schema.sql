-- Korean Reading Comprehension Learning Analytics Database Schema
-- Production-ready schema with Google OAuth integration support
-- Database: PostgreSQL 14+ recommended

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- =====================================================
-- USERS AND AUTHENTICATION
-- =====================================================

-- Users table (integrated with Google OAuth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    profile_picture TEXT,
    role VARCHAR(50) DEFAULT 'student' CHECK (role IN ('student', 'teacher', 'admin', 'parent')),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'deleted')),
    language_preference VARCHAR(10) DEFAULT 'ko',
    timezone VARCHAR(50) DEFAULT 'Asia/Seoul',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);

-- User sessions for authentication
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- =====================================================
-- EDUCATIONAL STRUCTURE
-- =====================================================

-- Schools/Organizations
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    type VARCHAR(50) DEFAULT 'high_school',
    address TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_schools_code ON schools(code);

-- Classes/Groups
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    school_id UUID REFERENCES schools(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    grade_level INTEGER CHECK (grade_level BETWEEN 1 AND 12),
    academic_year VARCHAR(20),
    semester VARCHAR(20),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'pending')),
    max_students INTEGER DEFAULT 40,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,
    end_date DATE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_classes_school_id ON classes(school_id);
CREATE INDEX idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX idx_classes_code ON classes(code);
CREATE INDEX idx_classes_status ON classes(status);

-- Student-Class enrollment
CREATE TABLE class_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'dropped', 'completed', 'transferred')),
    final_grade DECIMAL(5,2),
    attendance_rate DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, student_id)
);

CREATE INDEX idx_class_enrollments_class_id ON class_enrollments(class_id);
CREATE INDEX idx_class_enrollments_student_id ON class_enrollments(student_id);
CREATE INDEX idx_class_enrollments_status ON class_enrollments(status);

-- =====================================================
-- LEARNING CONTENT
-- =====================================================

-- Task items (reading comprehension tasks)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,  -- Maps to JSON file ID
    task_type VARCHAR(50) NOT NULL CHECK (task_type IN ('paragraph', 'article')),
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    topic VARCHAR(255),
    tags TEXT[],
    content_hash VARCHAR(64),  -- SHA256 hash for deduplication
    paragraph_text TEXT,
    article_text TEXT,
    questions JSONB NOT NULL,  -- Store all question data
    embeddings VECTOR(768),  -- For similarity search (requires pgvector)
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_external_id ON tasks(external_id);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_difficulty ON tasks(difficulty);
CREATE INDEX idx_tasks_topic ON tasks(topic);
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_questions ON tasks USING GIN(questions);

-- =====================================================
-- STUDENT LEARNING DATA
-- =====================================================

-- Learning sessions
CREATE TABLE learning_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    tasks_attempted INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4),
    avg_response_time_seconds DECIMAL(10,2),
    focus_score DECIMAL(3,2) CHECK (focus_score >= 0 AND focus_score <= 1),
    device_type VARCHAR(50),
    ip_address INET,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_learning_sessions_student_id ON learning_sessions(student_id);
CREATE INDEX idx_learning_sessions_class_id ON learning_sessions(class_id);
CREATE INDEX idx_learning_sessions_start_time ON learning_sessions(start_time);
CREATE INDEX idx_learning_sessions_accuracy ON learning_sessions(accuracy);

-- Task submissions/attempts
CREATE TABLE task_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES learning_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE SET NULL,
    question_type VARCHAR(50) NOT NULL,
    submitted_answer TEXT,
    correct_answer TEXT,
    is_correct BOOLEAN,
    similarity_score DECIMAL(5,4),
    response_time_seconds DECIMAL(10,2),
    attempt_number INTEGER DEFAULT 1,
    hints_used INTEGER DEFAULT 0,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_task_submissions_session_id ON task_submissions(session_id);
CREATE INDEX idx_task_submissions_student_id ON task_submissions(student_id);
CREATE INDEX idx_task_submissions_task_id ON task_submissions(task_id);
CREATE INDEX idx_task_submissions_class_id ON task_submissions(class_id);
CREATE INDEX idx_task_submissions_question_type ON task_submissions(question_type);
CREATE INDEX idx_task_submissions_is_correct ON task_submissions(is_correct);
CREATE INDEX idx_task_submissions_submitted_at ON task_submissions(submitted_at);

-- =====================================================
-- ANALYTICS AND METRICS
-- =====================================================

-- Student skill assessments
CREATE TABLE skill_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    current_level DECIMAL(5,2) CHECK (current_level >= 0 AND current_level <= 100),
    previous_level DECIMAL(5,2),
    trend VARCHAR(20) CHECK (trend IN ('improving', 'stable', 'declining')),
    assessment_count INTEGER DEFAULT 0,
    last_assessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, skill_name)
);

CREATE INDEX idx_skill_assessments_student_id ON skill_assessments(student_id);
CREATE INDEX idx_skill_assessments_skill_name ON skill_assessments(skill_name);
CREATE INDEX idx_skill_assessments_current_level ON skill_assessments(current_level);
CREATE INDEX idx_skill_assessments_trend ON skill_assessments(trend);

-- Learning milestones and achievements
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50),
    category VARCHAR(50),
    points INTEGER DEFAULT 0,
    requirements JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_achievements_category ON achievements(category);

-- Student achievements (earned)
CREATE TABLE student_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(student_id, achievement_id)
);

CREATE INDEX idx_student_achievements_student_id ON student_achievements(student_id);
CREATE INDEX idx_student_achievements_achievement_id ON student_achievements(achievement_id);
CREATE INDEX idx_student_achievements_earned_at ON student_achievements(earned_at);

-- =====================================================
-- LEARNING PATHS AND RECOMMENDATIONS
-- =====================================================

-- Personalized learning paths
CREATE TABLE learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    name VARCHAR(255),
    description TEXT,
    goal_period_days INTEGER,
    current_level DECIMAL(5,2),
    target_level DECIMAL(5,2),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'abandoned')),
    weekly_goals JSONB,
    recommended_topics TEXT[],
    practice_schedule JSONB,
    milestones JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,
    end_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_learning_paths_student_id ON learning_paths(student_id);
CREATE INDEX idx_learning_paths_status ON learning_paths(status);
CREATE INDEX idx_learning_paths_created_at ON learning_paths(created_at);

-- Task recommendations
CREATE TABLE task_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    reason VARCHAR(255),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    viewed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(student_id, task_id)
);

CREATE INDEX idx_task_recommendations_student_id ON task_recommendations(student_id);
CREATE INDEX idx_task_recommendations_task_id ON task_recommendations(task_id);
CREATE INDEX idx_task_recommendations_priority ON task_recommendations(priority);
CREATE INDEX idx_task_recommendations_expires_at ON task_recommendations(expires_at);

-- =====================================================
-- FEEDBACK AND COMMUNICATIONS
-- =====================================================

-- Feedback from teachers
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    submission_id UUID REFERENCES task_submissions(id) ON DELETE CASCADE,
    feedback_type VARCHAR(50) CHECK (feedback_type IN ('general', 'task_specific', 'skill_specific')),
    content TEXT NOT NULL,
    sentiment VARCHAR(20) CHECK (sentiment IN ('positive', 'neutral', 'constructive', 'critical')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_feedback_student_id ON feedback(student_id);
CREATE INDEX idx_feedback_teacher_id ON feedback(teacher_id);
CREATE INDEX idx_feedback_submission_id ON feedback(submission_id);
CREATE INDEX idx_feedback_created_at ON feedback(created_at);
CREATE INDEX idx_feedback_is_read ON feedback(is_read);

-- =====================================================
-- REPORTS AND EXPORTS
-- =====================================================

-- Generated reports
CREATE TABLE generated_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) CHECK (format IN ('html', 'pdf', 'excel', 'json')),
    scope VARCHAR(50) CHECK (scope IN ('student', 'class', 'school', 'comparative')),
    entity_id UUID,  -- Can reference student, class, or school
    file_path TEXT,
    file_size_bytes BIGINT,
    parameters JSONB,
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_generated_reports_report_type ON generated_reports(report_type);
CREATE INDEX idx_generated_reports_entity_id ON generated_reports(entity_id);
CREATE INDEX idx_generated_reports_generated_by ON generated_reports(generated_by);
CREATE INDEX idx_generated_reports_generated_at ON generated_reports(generated_at);

-- =====================================================
-- AUDIT AND LOGGING
-- =====================================================

-- Activity log for audit trail
CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_entity_type ON activity_logs(entity_type);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at);

-- Performance metrics for monitoring
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20,4),
    dimensions JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);
CREATE INDEX idx_performance_metrics_dimensions ON performance_metrics USING GIN(dimensions);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Student progress overview
CREATE VIEW student_progress_view AS
SELECT 
    u.id AS student_id,
    u.name,
    u.email,
    COUNT(DISTINCT ls.id) AS total_sessions,
    COUNT(DISTINCT ts.id) AS total_submissions,
    AVG(ts.is_correct::int) * 100 AS overall_accuracy,
    AVG(ts.response_time_seconds) AS avg_response_time,
    MAX(ls.start_time) AS last_active
FROM users u
LEFT JOIN learning_sessions ls ON u.id = ls.student_id
LEFT JOIN task_submissions ts ON u.id = ts.student_id
WHERE u.role = 'student'
GROUP BY u.id, u.name, u.email;

-- Class performance summary
CREATE VIEW class_performance_view AS
SELECT 
    c.id AS class_id,
    c.name AS class_name,
    COUNT(DISTINCT ce.student_id) AS total_students,
    AVG(ts.is_correct::int) * 100 AS avg_accuracy,
    COUNT(DISTINCT ts.id) AS total_submissions,
    COUNT(DISTINCT ls.id) AS total_sessions
FROM classes c
LEFT JOIN class_enrollments ce ON c.id = ce.class_id
LEFT JOIN task_submissions ts ON ce.student_id = ts.student_id AND c.id = ts.class_id
LEFT JOIN learning_sessions ls ON ce.student_id = ls.student_id AND c.id = ls.class_id
GROUP BY c.id, c.name;

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skill_assessments_updated_at BEFORE UPDATE ON skill_assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate session duration
CREATE OR REPLACE FUNCTION calculate_session_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.end_time IS NOT NULL AND NEW.start_time IS NOT NULL THEN
        NEW.duration_seconds = EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_session_duration_trigger
    BEFORE INSERT OR UPDATE ON learning_sessions
    FOR EACH ROW EXECUTE FUNCTION calculate_session_duration();

-- Function to update skill assessments after submission
CREATE OR REPLACE FUNCTION update_skill_assessment()
RETURNS TRIGGER AS $$
DECLARE
    skill_name_var VARCHAR(100);
    current_level_var DECIMAL(5,2);
    alpha DECIMAL(3,2) := 0.2;  -- Learning rate
BEGIN
    -- Map question type to skill
    CASE NEW.question_type
        WHEN 'keywords' THEN skill_name_var := 'keyword_identification';
        WHEN 'center_sentence' THEN skill_name_var := 'center_sentence';
        WHEN 'center_paragraph' THEN skill_name_var := 'center_paragraph';
        WHEN 'topic' THEN skill_name_var := 'topic_comprehension';
        ELSE skill_name_var := NULL;
    END CASE;
    
    IF skill_name_var IS NOT NULL THEN
        -- Get current skill level or initialize
        SELECT current_level INTO current_level_var
        FROM skill_assessments
        WHERE student_id = NEW.student_id AND skill_name = skill_name_var;
        
        IF current_level_var IS NULL THEN
            current_level_var := 50.0;  -- Default starting level
        END IF;
        
        -- Update skill level using exponential moving average
        current_level_var := (1 - alpha) * current_level_var + 
                            alpha * (CASE WHEN NEW.is_correct THEN 100.0 ELSE 0.0 END);
        
        -- Upsert skill assessment
        INSERT INTO skill_assessments (
            student_id, skill_name, current_level, previous_level, 
            trend, assessment_count, last_assessed_at
        ) VALUES (
            NEW.student_id, skill_name_var, current_level_var, current_level_var,
            'stable', 1, CURRENT_TIMESTAMP
        )
        ON CONFLICT (student_id, skill_name) 
        DO UPDATE SET
            previous_level = skill_assessments.current_level,
            current_level = current_level_var,
            trend = CASE 
                WHEN current_level_var > skill_assessments.current_level + 5 THEN 'improving'
                WHEN current_level_var < skill_assessments.current_level - 5 THEN 'declining'
                ELSE 'stable'
            END,
            assessment_count = skill_assessments.assessment_count + 1,
            last_assessed_at = CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_skill_assessment_trigger
    AFTER INSERT ON task_submissions
    FOR EACH ROW EXECUTE FUNCTION update_skill_assessment();

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Composite indexes for common queries
CREATE INDEX idx_task_submissions_student_task ON task_submissions(student_id, task_id);
CREATE INDEX idx_task_submissions_student_correct ON task_submissions(student_id, is_correct);
CREATE INDEX idx_learning_sessions_student_time ON learning_sessions(student_id, start_time DESC);
CREATE INDEX idx_skill_assessments_student_level ON skill_assessments(student_id, current_level DESC);

-- =====================================================
-- INITIAL DATA AND PERMISSIONS
-- =====================================================

-- Insert default achievements
INSERT INTO achievements (name, description, icon, category, points, requirements) VALUES
('첫 걸음', '첫 문제를 완료했습니다', '👣', 'milestone', 10, '{"submissions": 1}'::jsonb),
('일주일 연속 학습', '7일 연속 학습했습니다', '🔥', 'streak', 50, '{"streak_days": 7}'::jsonb),
('첫 만점', '처음으로 만점을 받았습니다', '💯', 'accuracy', 25, '{"perfect_score": true}'::jsonb),
('10문제 연속 정답', '10문제를 연속으로 맞혔습니다', '🎯', 'accuracy', 100, '{"consecutive_correct": 10}'::jsonb),
('학습 마스터', '모든 영역에서 80점 이상 달성', '👑', 'mastery', 200, '{"all_skills_above": 80}'::jsonb),
('빠른 학습자', '평균 응답 시간 30초 이하', '⚡', 'speed', 75, '{"avg_response_time": 30}'::jsonb),
('꾸준한 학습자', '30일 동안 꾸준히 학습', '📚', 'consistency', 150, '{"active_days": 30}'::jsonb);

-- Create read-only role for analytics
CREATE ROLE analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;

-- Create application role with appropriate permissions
CREATE ROLE app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT DELETE ON task_submissions, learning_sessions, task_recommendations TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- =====================================================
-- MAINTENANCE QUERIES
-- =====================================================

-- Query to clean up old sessions
-- DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Query to archive old learning data
-- INSERT INTO archived_submissions SELECT * FROM task_submissions 
-- WHERE submitted_at < CURRENT_TIMESTAMP - INTERVAL '1 year';

-- Query to update class completion status
-- UPDATE class_enrollments SET status = 'completed' 
-- WHERE class_id IN (SELECT id FROM classes WHERE end_date < CURRENT_DATE);

-- =====================================================
-- MONITORING QUERIES
-- =====================================================

-- Active users in last 24 hours
-- SELECT COUNT(DISTINCT student_id) FROM learning_sessions 
-- WHERE start_time > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Average accuracy by difficulty
-- SELECT t.difficulty, AVG(ts.is_correct::int) * 100 as accuracy
-- FROM task_submissions ts
-- JOIN tasks t ON ts.task_id = t.id
-- GROUP BY t.difficulty;

-- Most problematic tasks
-- SELECT t.external_id, t.topic, 
--        COUNT(ts.id) as attempts, 
--        AVG(ts.is_correct::int) * 100 as success_rate
-- FROM tasks t
-- JOIN task_submissions ts ON t.id = ts.task_id
-- GROUP BY t.id, t.external_id, t.topic
-- HAVING COUNT(ts.id) > 10
-- ORDER BY success_rate ASC
-- LIMIT 20;