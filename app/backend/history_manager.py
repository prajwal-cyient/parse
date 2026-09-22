from db_manager import DBManager

class HistoryManager:
    """
    Wrapper for history & test case storage using PostgreSQL 15 'parker' database.
    """
    @classmethod
    def load_history(cls):
        return DBManager.load_history()

    @classmethod
    def save_run(cls, file_name, req_count, tc_count, excel_path, json_path, test_cases_data=None):
        return DBManager.save_execution_run(file_name, req_count, tc_count, excel_path, json_path, test_cases_data)

    @classmethod
    def get_run(cls, run_id):
        return DBManager.get_run_details(run_id)

    @classmethod
    def delete_run(cls, run_id):
        return DBManager.delete_run(run_id)

    @classmethod
    def clear_all(cls):
        # Clears all rows in execution_history table in PostgreSQL
        conn = DBManager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE execution_history CASCADE;")
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
