-- Add password recovery columns
ALTER TABLE users 
ADD COLUMN recovery_token VARCHAR(128) NULL,
ADD COLUMN recovery_token_expires TIMESTAMP NULL,
ADD COLUMN recovery_attempts INT DEFAULT 0,
ADD COLUMN last_recovery_sent TIMESTAMP NULL;

-- Index to speed up recovery token validations
CREATE INDEX idx_users_recovery 
ON users(email, recovery_token, recovery_token_expires);
