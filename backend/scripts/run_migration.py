#!/usr/bin/env python3
import mysql.connector
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def check_column_exists(cursor, table_name, column_name):
	"""Check if a column exists in a table."""
	query = """
	SELECT COUNT(*) 
	FROM INFORMATION_SCHEMA.COLUMNS 
	WHERE TABLE_SCHEMA = %s 
	AND TABLE_NAME = %s 
	AND COLUMN_NAME = %s
	"""
	cursor.execute(query, (settings.DB_NAME, table_name, column_name))
	result = cursor.fetchone()
	return result[0] > 0

def run_migration():
	"""Run email verification migration."""
	try:
		conn = mysql.connector.connect(
			host=settings.DB_HOST,
			database=settings.DB_NAME,
			user=settings.DB_USER,
			password=settings.DB_PASSWORD
		)
		
		cursor = conn.cursor()
		
		# Check if columns already exist
		columns_to_add = [
			('email_verified', 'BOOLEAN DEFAULT FALSE'),
			('verification_code', 'VARCHAR(6) NULL'),
			('verification_code_expires', 'TIMESTAMP NULL'),
			('verification_attempts', 'INT DEFAULT 0'),
			('last_verification_sent', 'TIMESTAMP NULL')
		]
		
		columns_added = []
		columns_skipped = []
		
		for column_name, column_definition in columns_to_add:
			if not check_column_exists(cursor, 'users', column_name):
				try:
					alter_query = f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"
					cursor.execute(alter_query)
					columns_added.append(column_name)
					print(f"✓ Added column: {column_name}")
				except mysql.connector.Error as e:
					print(f"✗ Error adding column {column_name}: {e}")
					raise
			else:
				columns_skipped.append(column_name)
				print(f"→ Column already exists: {column_name}")
		
		# Add index if it doesn't exist
		try:
			cursor.execute("""
				CREATE INDEX idx_users_verification 
				ON users(username, verification_code, verification_code_expires)
			""")
			print("✓ Created index: idx_users_verification")
		except mysql.connector.Error as e:
			if "Duplicate key name" in str(e):
				print("→ Index already exists: idx_users_verification")
			else:
				print(f"✗ Error creating index: {e}")
				raise
		
		conn.commit()
		
		print("\nMigration Summary:")
		print(f"- Columns added: {len(columns_added)}")
		print(f"- Columns skipped: {len(columns_skipped)}")
		print("\nMigration completed successfully!")
		
	except mysql.connector.Error as e:
		print(f"\nMigration failed: {e}")
		if conn:
			conn.rollback()
		sys.exit(1)
	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()

if __name__ == "__main__":
	run_migration()