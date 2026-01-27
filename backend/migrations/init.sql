-- Create tables
CREATE TABLE IF NOT EXISTS users (
	id INT AUTO_INCREMENT PRIMARY KEY,
	username VARCHAR(100) NOT NULL UNIQUE,
	email VARCHAR(100) NOT NULL,
	api_key_preview VARCHAR(64) NULL,
	u_status ENUM('active', 'pending', 'disabled') DEFAULT 'pending',
	u_type VARCHAR(20) DEFAULT 'basic' NOT NULL,
	isFederated BOOLEAN DEFAULT FALSE,
	-- Email verification fields
	email_verified BOOLEAN DEFAULT FALSE,
	verification_code VARCHAR(6) NULL,
	verification_code_expires TIMESTAMP NULL,
	verification_attempts INT DEFAULT 0,
	last_verification_sent TIMESTAMP NULL,
	-- Timestamps
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	-- Indexes
	INDEX idx_username (username),
	INDEX idx_email (email),
	INDEX idx_verification (username, verification_code, verification_code_expires)
);

-- Grant permissions to api_user
-- GRANT ALL PRIVILEGES ON user_db.* TO 'api_user'@'%';
-- FLUSH PRIVILEGES;
-- Note: Profiles table is not needed as we're using APISIX Consumer Groups
-- Consumer Groups configuration is managed entirely through APISIX