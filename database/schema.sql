-- Users table to track GitHub users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    github_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    display_name TEXT,
    email TEXT,
    avatar_url TEXT,
    is_enabled BOOLEAN DEFAULT 1,
    is_admin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME,
    model_count INTEGER DEFAULT 0
);

-- Models table to track created models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id TEXT UNIQUE NOT NULL,
    bbox TEXT NOT NULL,
    parameters TEXT NOT NULL,
    preview_url TEXT,
    stl_url TEXT,
    scad_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_models_user_id ON models(user_id);
CREATE INDEX IF NOT EXISTS idx_models_job_id ON models(job_id);
CREATE INDEX IF NOT EXISTS idx_users_github_id ON users(github_id);

-- Create admin user (you'll need to update the github_id after first login)
-- INSERT INTO users (github_id, username, display_name, is_admin) 
-- VALUES ('YOUR_GITHUB_ID', 'YOUR_USERNAME', 'Admin User', 1);