-- Database initialization for Korean Reading Comprehension System
-- PostgreSQL schema

-- Create database if not exists
-- CREATE DATABASE reading_db;

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    user_level FLOAT DEFAULT 0.5,
    total_tasks INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Responses table for tracking all answers
CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    answer TEXT,
    score FLOAT,
    time_spent INTEGER, -- in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_sessions(user_id) ON DELETE CASCADE
);

-- Learning progress table
CREATE TABLE IF NOT EXISTS learning_progress (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    tasks_completed INTEGER DEFAULT 0,
    average_score FLOAT,
    total_time INTEGER, -- in minutes
    difficulty_level VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date),
    FOREIGN KEY (user_id) REFERENCES user_sessions(user_id) ON DELETE CASCADE
);

-- Achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    achievement_type VARCHAR(100) NOT NULL,
    achievement_name VARCHAR(255),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_type),
    FOREIGN KEY (user_id) REFERENCES user_sessions(user_id) ON DELETE CASCADE
);

-- Summary practice table
CREATE TABLE IF NOT EXISTS summary_practice (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    strategy_type VARCHAR(50), -- micro, macro, gist, reciprocal
    original_text TEXT,
    user_summary TEXT,
    model_summary TEXT,
    similarity_score FLOAT,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_sessions(user_id) ON DELETE CASCADE
);

-- Highlights and annotations table
CREATE TABLE IF NOT EXISTS annotations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    text_selection TEXT,
    annotation_type VARCHAR(50), -- keyword, main_idea, supporting, question
    note TEXT,
    position_start INTEGER,
    position_end INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_sessions(user_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id);
CREATE INDEX IF NOT EXISTS idx_responses_task_id ON responses(task_id);
CREATE INDEX IF NOT EXISTS idx_responses_created_at ON responses(created_at);
CREATE INDEX IF NOT EXISTS idx_progress_user_date ON learning_progress(user_id, date);
CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_summary_user ON summary_practice(user_id);
CREATE INDEX IF NOT EXISTS idx_annotations_user_task ON annotations(user_id, task_id);

-- Create views for analytics
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    u.user_id,
    u.user_level,
    u.total_tasks,
    u.streak,
    COUNT(DISTINCT r.task_id) as unique_tasks,
    AVG(r.score) as average_score,
    COUNT(DISTINCT DATE(r.created_at)) as active_days,
    MAX(r.created_at) as last_activity
FROM user_sessions u
LEFT JOIN responses r ON u.user_id = r.user_id
GROUP BY u.user_id, u.user_level, u.total_tasks, u.streak;

CREATE OR REPLACE VIEW daily_performance AS
SELECT 
    user_id,
    DATE(created_at) as date,
    COUNT(*) as tasks_completed,
    AVG(score) as average_score,
    SUM(time_spent) / 60.0 as total_minutes
FROM responses
GROUP BY user_id, DATE(created_at)
ORDER BY date DESC;

-- Function to update user level
CREATE OR REPLACE FUNCTION update_user_level()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_sessions
    SET 
        user_level = CASE
            WHEN (SELECT AVG(score) FROM responses WHERE user_id = NEW.user_id AND created_at > NOW() - INTERVAL '7 days') > 0.8 
                THEN LEAST(user_level + 0.05, 1.0)
            WHEN (SELECT AVG(score) FROM responses WHERE user_id = NEW.user_id AND created_at > NOW() - INTERVAL '7 days') < 0.5
                THEN GREATEST(user_level - 0.05, 0.1)
            ELSE user_level
        END,
        total_tasks = total_tasks + 1,
        last_activity = NOW(),
        updated_at = NOW()
    WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update user level
CREATE TRIGGER trigger_update_user_level
AFTER INSERT ON responses
FOR EACH ROW
EXECUTE FUNCTION update_user_level();

-- Function to check and award achievements
CREATE OR REPLACE FUNCTION check_achievements()
RETURNS TRIGGER AS $$
DECLARE
    task_count INTEGER;
    avg_score FLOAT;
    streak_days INTEGER;
BEGIN
    -- Get user statistics
    SELECT COUNT(*) INTO task_count FROM responses WHERE user_id = NEW.user_id;
    SELECT AVG(score) INTO avg_score FROM responses WHERE user_id = NEW.user_id;
    
    -- Check task-based achievements
    IF task_count >= 10 AND NOT EXISTS (
        SELECT 1 FROM achievements 
        WHERE user_id = NEW.user_id AND achievement_type = 'first_steps'
    ) THEN
        INSERT INTO achievements (user_id, achievement_type, achievement_name)
        VALUES (NEW.user_id, 'first_steps', '첫 걸음 - 10개 과제 완료');
    END IF;
    
    IF task_count >= 50 AND NOT EXISTS (
        SELECT 1 FROM achievements 
        WHERE user_id = NEW.user_id AND achievement_type = 'consistent_learner'
    ) THEN
        INSERT INTO achievements (user_id, achievement_type, achievement_name)
        VALUES (NEW.user_id, 'consistent_learner', '꾸준한 학습자 - 50개 과제 완료');
    END IF;
    
    IF task_count >= 100 AND NOT EXISTS (
        SELECT 1 FROM achievements 
        WHERE user_id = NEW.user_id AND achievement_type = 'reading_expert'
    ) THEN
        INSERT INTO achievements (user_id, achievement_type, achievement_name)
        VALUES (NEW.user_id, 'reading_expert', '읽기 전문가 - 100개 과제 완료');
    END IF;
    
    -- Check performance-based achievements
    IF avg_score >= 0.9 AND task_count >= 20 AND NOT EXISTS (
        SELECT 1 FROM achievements 
        WHERE user_id = NEW.user_id AND achievement_type = 'perfect_scorer'
    ) THEN
        INSERT INTO achievements (user_id, achievement_type, achievement_name)
        VALUES (NEW.user_id, 'perfect_scorer', '완벽주의자 - 평균 90% 이상');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to check achievements
CREATE TRIGGER trigger_check_achievements
AFTER INSERT ON responses
FOR EACH ROW
EXECUTE FUNCTION check_achievements();

-- Sample data for testing (optional)
-- INSERT INTO user_sessions (user_id) VALUES ('test_user_001');