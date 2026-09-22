# Parker DO-178C Level B Verification Engine 2.0

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
