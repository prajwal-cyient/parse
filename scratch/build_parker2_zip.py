import os
import zipfile

dest_dir = r"c:\Users\pm89542\Desktop\parse"
zip_filename = os.path.join(dest_dir, "parker2.0.zip")

readme_content = """# Parker DO-178C Level B Verification Engine 2.0

Automated, auditor-compliant DO-178C Level B test case generation, qualification matrix expansion, and verification audit platform.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11)
- (Optional) Ollama running locally or via SSH tunnel with model `gpt-oss:latest` on port `11434`

### 2. Installation & Run (One-Click)

#### Windows:
Double-click `start_server.bat` or run in PowerShell/CMD:
```cmd
start_server.bat
```

#### Linux / macOS:
```bash
chmod +x start_server.sh
./start_server.sh
```

---

## Web Interface

Once started, open your browser and navigate to:
**http://localhost:8080**

- **Default Username**: `admin`
- **Default Password**: `password123` (or register a new user in the UI)

---

## Project Structure

- `app/backend/` : Core DO-178C generation & audit engine:
  - `main.py` : FastAPI server & SSE streaming endpoint
  - `ollama_client.py` : LLM communication & generic DO-178C synthesizer
  - `docx_parser.py` : Universal .docx & table extractor
  - `signal_classifier.py` : 3-tier grammar data-flow separator
  - `applicability_engine.py` : Pin-strap & cross-product matrix generator
  - `consolidation_engine.py` : Sequence clubbing & multi-member consolidation
  - `db_manager.py` : PostgreSQL database manager
  - `history_manager.py` : Audit history manager
- `app/frontend/` : Responsive dark-mode web workspace (HTML/CSS/JS)
- `app/outputs/` : Pre-generated, approved master verification workbooks:
  - `SW_Requirements_Sample_1_Test_Cases_PERFECTED_APPROVED.xlsx` (180 TCs)
  - `SW_Requirements_Sample_4_Test_Cases.xlsx` (26 TCs)
  - `sample 2.xlsx`, `sample 3.xlsx`, `sample 4.xlsx`, `samples.xlsx`
- `app/uploads/` : Sample requirement specifications

---

## DO-178C Level B Compliance Features

1. **3-Tier Data Flow Separation**: Preconditions in *Initial Conditions*, Stimuli in *Test Inputs*, Assertions in *Expected Results*.
2. **Discrete State Enumeration**: Comprehensive coverage of all discrete states and truth conditions.
3. **Boundary Value Analysis (BVA)**: Min, Nominal, Max evaluation for all numeric thresholds.
4. **Combinatorial Pin-Strapping**: Full matrix expansion across all valid hardware dimensions.
5. **Multi-Step Consolidation**: Cohesive clubbing of sub-step sequences without coverage loss.
6. **Complete Traceability**: Bi-directional requirement-to-test mapping.
7. **Robustness & Negative Testing**: Comprehensive fault injection and out-of-range coverage.
8. **Zero Placeholders**: 100% concrete engineering values with realistic avionics units.
"""

start_bat_content = """@echo off
title Parker DO-178C Verification Platform 2.0
echo ===================================================
echo   Starting Parker DO-178C Platform 2.0
echo ===================================================

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10 or 3.11.
    pause
    exit /b 1
)

echo [2/3] Installing/Verifying dependencies...
pip install -r requirements.txt

echo [3/3] Launching FastAPI Web Application...
cd app\\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
pause
"""

start_sh_content = """#!/usr/bin/env bash
echo "==================================================="
echo "  Starting Parker DO-178C Platform 2.0"
echo "==================================================="

echo "[1/3] Checking Python installation..."
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 not found. Please install Python 3.10+."; exit 1; }

echo "[2/3] Installing dependencies..."
pip install -r requirements.txt

echo "[3/3] Launching server on http://localhost:8080..."
cd app/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
"""

requirements_content = """fastapi>=0.100.0
uvicorn>=0.23.0
python-docx>=0.8.11
openpyxl>=3.1.2
httpx>=0.24.0
pydantic>=2.0.0
python-multipart>=0.0.6
passlib>=1.7.4
bcrypt>=4.0.0
psycopg2-binary>=2.9.6
"""

# Write bundle staging files
with open(os.path.join(dest_dir, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_content)
with open(os.path.join(dest_dir, "start_server.bat"), "w", encoding="utf-8") as f:
    f.write(start_bat_content)
with open(os.path.join(dest_dir, "start_server.sh"), "w", encoding="utf-8") as f:
    f.write(start_sh_content)
with open(os.path.join(dest_dir, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write(requirements_content)

print(f"Creating zip package: {zip_filename}...")
include_dirs = ["app"]
include_files = [
    "README.md", "start_server.bat", "start_server.sh", "requirements.txt",
    "sample 2.xlsx", "sample 3.xlsx", "sample 4.xlsx", "samples.xlsx"
]

with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add root files
    for root_file in include_files:
        full_p = os.path.join(dest_dir, root_file)
        if os.path.exists(full_p):
            zipf.write(full_p, arcname=os.path.join("parker2.0", root_file))
            print(f"  Added file: {root_file}")
    
    # Add app directory recursively
    for inc_dir in include_dirs:
        dir_path = os.path.join(dest_dir, inc_dir)
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache", ".git"]]
            for file in files:
                if file.startswith("~$") or file.endswith(".pyc") or file.endswith(".tmp"):
                    continue
                file_full = os.path.join(root, file)
                rel_path = os.path.relpath(file_full, dest_dir)
                try:
                    zipf.write(file_full, arcname=os.path.join("parker2.0", rel_path))
                except Exception as e:
                    print(f"  Skipping locked/inaccessible file {file}: {e}")

zip_size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
print(f"SUCCESS: Created {zip_filename} ({zip_size_mb:.2f} MB)")
