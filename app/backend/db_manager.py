import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os
import hashlib
import secrets
from datetime import datetime

class DBManager:
    """
    Manages connections and transactions with PostgreSQL 15 database 'parker'.
    Stores user credentials, execution history runs, and all generated test case data.
    """
    DB_CONFIG = {
        "dbname": "parker",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": 5432
    }

    @classmethod
    def get_connection(cls):
        return psycopg2.connect(**cls.DB_CONFIG)

    @classmethod
    def initialize_db(cls):
        """Creates required PostgreSQL tables and seeds default admin accounts if empty."""
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()

            # 1. Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(50) PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    full_name VARCHAR(255),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    pwd_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Execution History Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id VARCHAR(50) PRIMARY KEY,
                    file_name VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    requirements_count INT DEFAULT 0,
                    test_cases_count INT DEFAULT 0,
                    excel_path TEXT,
                    json_path TEXT,
                    status VARCHAR(50) DEFAULT 'COMPLETED'
                );
            """)

            # 3. Test Cases Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_cases (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR(50) REFERENCES execution_history(id) ON DELETE CASCADE,
                    test_case_id VARCHAR(100) NOT NULL,
                    requirement_id VARCHAR(100) NOT NULL,
                    description TEXT,
                    test_type VARCHAR(50),
                    initial_condition TEXT,
                    test_inputs TEXT,
                    expected_result TEXT,
                    pass_criteria TEXT,
                    related_requirements TEXT,
                    test_procedure_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()

            # Seed default admin accounts if empty
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            if user_count == 0:
                cls._seed_default_users(cursor)
                conn.commit()

        except Exception as e:
            print("PostgreSQL Database Initialization Error:", e)
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @classmethod
    def _hash_password(cls, password: str, salt: str = None) -> tuple:
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return pwd_hash, salt

    @classmethod
    def _seed_default_users(cls, cursor):
        admin_hash, admin_salt = cls._hash_password("admin123")
        eng_hash, eng_salt = cls._hash_password("engineer123")

        cursor.execute("""
            INSERT INTO users (id, username, full_name, email, pwd_hash, salt)
            VALUES 
            (%s, %s, %s, %s, %s, %s),
            (%s, %s, %s, %s, %s, %s);
        """, (
            "USR-0001", "admin", "System Administrator", "admin@aerospace.com", admin_hash, admin_salt,
            "USR-0002", "engineer", "Lead Test Engineer", "engineer@aerospace.com", eng_hash, eng_salt
        ))

    # ==========================================
    # Auth Methods
    # ==========================================
    @classmethod
    def authenticate_user(cls, username_or_email: str, password: str) -> dict:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            target = username_or_email.strip().lower()

            cursor.execute("""
                SELECT * FROM users 
                WHERE LOWER(username) = %s OR LOWER(email) = %s;
            """, (target, target))
            user = cursor.fetchone()

            if not user:
                return {"success": False, "message": "User account does not exist in 'parker' DB. Please register first."}

            pwd_hash, _ = cls._hash_password(password, user["salt"])
            if pwd_hash == user["pwd_hash"]:
                return {
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "email": user["email"]
                    }
                }
            else:
                return {"success": False, "message": "Invalid password."}

        except Exception as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    @classmethod
    def register_user(cls, full_name: str, email: str, password: str) -> dict:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            email_clean = email.strip().lower()
            username_clean = email_clean.split('@')[0]

            cursor.execute("SELECT id FROM users WHERE LOWER(email) = %s OR LOWER(username) = %s;", (email_clean, username_clean))
            if cursor.fetchone():
                return {"success": False, "message": "Account with this email already exists in 'parker' DB."}

            cursor.execute("SELECT COUNT(*) FROM users;")
            count = cursor.fetchone()["count"]
            user_id = f"USR-{count + 1:04d}"

            pwd_hash, salt = cls._hash_password(password)
            cursor.execute("""
                INSERT INTO users (id, username, full_name, email, pwd_hash, salt)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, username, full_name, email;
            """, (user_id, username_clean, full_name.strip(), email_clean, pwd_hash, salt))
            new_user = cursor.fetchone()
            conn.commit()

            return {"success": True, "user": new_user}

        except Exception as e:
            if conn:
                conn.rollback()
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            if conn:
                conn.close()

    # ==========================================
    # History & Test Cases Persistence
    # ==========================================
    @classmethod
    def save_execution_run(cls, file_name: str, req_count: int, tc_count: int, excel_path: str, json_path: str, test_cases_data: list = None) -> dict:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT COUNT(*) FROM execution_history;")
            count = cursor.fetchone()["count"]
            run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO execution_history (id, file_name, timestamp, requirements_count, test_cases_count, excel_path, json_path, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'COMPLETED')
                RETURNING *;
            """, (run_id, file_name, now_str, req_count, tc_count, excel_path, json_path))

            run_entry = cursor.fetchone()
            if isinstance(run_entry.get("timestamp"), datetime):
                run_entry["timestamp"] = run_entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

            # Save individual test cases into test_cases table
            if test_cases_data:
                for tc in test_cases_data:
                    cursor.execute("""
                        INSERT INTO test_cases (
                            run_id, test_case_id, requirement_id, description, test_type,
                            initial_condition, test_inputs, expected_result, pass_criteria,
                            related_requirements, test_procedure_notes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        run_id,
                        tc.get("test_case_id", ""),
                        tc.get("requirement_id", ""),
                        tc.get("description", ""),
                        tc.get("test_type", "NORMAL"),
                        tc.get("initial_condition", ""),
                        tc.get("test_inputs", ""),
                        tc.get("expected_result", ""),
                        tc.get("pass_criteria", ""),
                        tc.get("related_requirements", ""),
                        tc.get("test_procedure_notes", "")
                    ))

            conn.commit()
            return run_entry

        except Exception as e:
            print("Save execution run error:", e)
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def load_history(cls) -> list:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM execution_history ORDER BY timestamp DESC LIMIT 50;")
            rows = cursor.fetchall()
            for r in rows:
                if isinstance(r["timestamp"], datetime):
                    r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            return rows
        except Exception as e:
            print("Load history error:", e)
            return []
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_run_details(cls, run_id: str) -> dict:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            clean_id = str(run_id).strip()
            cursor.execute("SELECT * FROM execution_history WHERE id = %s;", (clean_id,))
            run = cursor.fetchone()
            if not run:
                return None
            if isinstance(run["timestamp"], datetime):
                run["timestamp"] = run["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("SELECT * FROM test_cases WHERE run_id = %s ORDER BY id ASC;", (clean_id,))
            tcs = cursor.fetchall()
            run["test_cases"] = tcs or []
            return run
        except Exception as e:
            print("Get run details error:", e)
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def delete_run(cls, run_id: str) -> bool:
        conn = None
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            clean_id = str(run_id).strip()
            cursor.execute("DELETE FROM execution_history WHERE id = %s;", (clean_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            print("Delete run error:", e)
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

