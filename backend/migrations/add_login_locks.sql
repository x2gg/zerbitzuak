-- Create table to store active login locks per (username, ip)
CREATE TABLE IF NOT EXISTS user_db.login_locks (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(191) NOT NULL,
  ip VARCHAR(45) NOT NULL,
  locked_until DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uniq_user_ip (username, ip),
  INDEX idx_locked_until (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
