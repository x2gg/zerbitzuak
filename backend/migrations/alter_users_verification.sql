-- Drop and recreate the columns to ensure clean state
ALTER TABLE users 
DROP COLUMN IF EXISTS email_verified,
DROP COLUMN IF EXISTS verification_code,
DROP COLUMN IF EXISTS verification_code_expires,
DROP COLUMN IF EXISTS verification_attempts,
DROP COLUMN IF EXISTS last_verification_sent;

-- Add the columns
ALTER TABLE users 
ADD COLUMN email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN verification_code VARCHAR(6) NULL,
ADD COLUMN verification_code_expires TIMESTAMP NULL,
ADD COLUMN verification_attempts INT DEFAULT 0,
ADD COLUMN last_verification_sent TIMESTAMP NULL;

-- Add index for verification queries
CREATE INDEX IF NOT EXISTS idx_users_verification 
ON users(username, verification_code, verification_code_expires);