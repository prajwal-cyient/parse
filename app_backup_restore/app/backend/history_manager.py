import json
import os
from datetime import datetime

class HistoryManager:
    """
    Manages execution history of past document parsing and test case generation runs.
    Stores metadata in app/history.json.
    """
    HISTORY_FILE = r"c:\Users\pm89542\Desktop\parse\app\history.json"

    @classmethod
    def load_history(cls):
        if not os.path.exists(cls.HISTORY_FILE):
            return []
        try:
            with open(cls.HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def save_run(cls, file_name, req_count, tc_count, excel_path, json_path):
        history = cls.load_history()
        run_entry = {
            "id": f"RUN-{len(history) + 1:04d}",
            "file_name": file_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "requirements_count": req_count,
            "test_cases_count": tc_count,
            "excel_path": excel_path,
            "json_path": json_path,
            "status": "COMPLETED"
        }
        history.insert(0, run_entry) # Most recent first
        os.makedirs(os.path.dirname(cls.HISTORY_FILE), exist_ok=True)
        with open(cls.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[:50], f, indent=2) # Store last 50 runs
        return run_entry
