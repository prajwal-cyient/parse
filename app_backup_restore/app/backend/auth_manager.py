from db_manager import DBManager

class AuthManager:
    """
    Wrapper for authentication transactions using PostgreSQL 15 'parker' database.
    """
    @classmethod
    def initialize_db(cls):
        DBManager.initialize_db()

    @classmethod
    def authenticate_user(cls, username_or_email: str, password: str) -> dict:
        return DBManager.authenticate_user(username_or_email, password)

    @classmethod
    def register_user(cls, full_name: str, email: str, password: str) -> dict:
        return DBManager.register_user(full_name, email, password)
