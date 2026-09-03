# 🚀 DO-178C AI Parker Test Case Generator Tool (v4.7)
### Automated Aerospace Software Verification Engine — Level B Certified Rules

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (3-Step Installation)](#quick-start-3-step-installation)
4. [Detailed Installation Procedure](#detailed-installation-procedure)
5. [Running the Application](#running-the-application)
6. [Generating DO-178C Test Cases](#generating-do-178c-test-cases)
7. [Client Observation Verification Compliance](#client-observation-verification-compliance)
8. [Troubleshooting & Support](#troubleshooting--support)

---

## ℹ️ Overview
The **Parker AI Verification Tool** is a specialized aerospace engineering application designed to parse Word requirement specifications (`.docx`), query local or remote LLM models (`gpt-oss:latest` via SSH tunnel), and automatically generate DO-178C Level B compliant software verification test cases exported directly into professional Excel catalogs (`.xlsx`).

---

## 💻 Prerequisites

Before setting up the tool on your machine (Usha, Kiran, or Team Lead), ensure you have:

1. **Operating System**: Windows 10 / 11 (64-bit).
2. **Python**: Python **3.10** or higher installed (ensure `"Add Python to PATH"` was checked during Python installation).
   - Verify in terminal: `python --version`
3. **Network & SSH Access**: Access to the remote Ollama server (`172.19.64.35`) via SSH for `gpt-oss:latest` LLM model access.

---

## ⚡ Quick Start (3-Step Installation)

If Python is already installed on your system:

1. **Extract ZIP File**: Extract `Parker_AI_Verification_Tool_v4.7.zip` to your Desktop or preferred directory (e.g. `C:\Parker_Tool`).
2. **Install Dependencies**: Double-click `install_dependencies.bat` (or run `pip install -r requirements.txt`).
3. **Launch Application**: Double-click `start_parker_app.bat`. Open your browser at:
   👉 **http://localhost:8080**

---

## 🔧 Detailed Installation Procedure

### Step 1: Extract the Package
Extract the entire `Parker_AI_Verification_Tool_v4.7.zip` archive into a folder on your computer.

### Step 2: Install Python Packages
Open Command Prompt or PowerShell in the extracted directory and run:
```bash
pip install -r requirements.txt
```

### Step 3: Establish the Remote SSH LLM Tunnel
To access the `gpt-oss:latest` model on the remote GPU server (`172.19.64.35`):

1. Open Command Prompt or PowerShell.
2. Run the SSH tunnel command:
   ```bash
   ssh -L 11434:localhost:11434 root1@172.19.64.35
   ```
3. Enter password: `root1`
4. Keep this SSH terminal window **OPEN** in the background during your test generation session.

---

## 🌐 Running the Application

### Method A: Web UI Mode (Recommended)
1. Double-click `start_parker_app.bat` OR run:
   ```bash
   cd app\backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8080
   ```
2. Open your web browser at: **http://localhost:8080**
3. Verify the top status badge shows: 🟢 **`SSH Tunnel: ONLINE (gpt-oss:latest)`**
4. Drag and drop any requirement specification (`.docx`), click **Start Test Case Generation**, and download the generated Excel catalog directly!

### Method B: Offline / Batch Script Mode
To process requirement steps via terminal script:
```bash
python process_all_steps_ollama.py
```
This generates `LRUSWRS-1001_grouped_step_testcases.json` and updates your Excel catalog.

---

## ✅ Client Observation Verification Compliance

The tool comes pre-configured with all 8 DO-178C client observation rules:
1. **Explicit Hardware Enumeration**: Automatically enumerates `LRU_1` to `LRU_7` and `ATYPE_1` to `ATYPE_3`. Formats Test Case IDs to match `.tst` test execution script filenames (`SWVCP_AAP_TC_ELECTRONIC_RIGGING_1_001`..`095`).
2. **Strict Column Classification**: Places dynamic stimulus ONLY in `Test Inputs`, setup states ONLY in `Initial Condition(s)`, and output signals ONLY in `Expected Result(s)`.
3. **Single Static Numerical Values**: Replaces placeholder strings (e.g. `[average from step above]`) with explicit static values (`100.0`).
4. **Explicit Boolean False Assertions**: Explicitly asserts `Expand_Stop_Collection_Complete = False` for negative condition tests.
5. **Sequence Step Clubbing**: Clubs multi-step fault sequences (Steps 3/4A/4B into Contract Fault; Steps 8/9A/9B into Expand Fault).
6. **Consolidated PSR Data Members**: Consolidates `LRUSWRS-1000` into 1 single test case with `IVT_Mode_ModeLgc = True` & `Harmonizing_Active_STL = True`.
7. **LRUSWRS-1003 & 1002 Fixes**: Places `IVT_Mode_ModeLgc` in `Test Inputs`, and inherits valid non-blank inputs from `SWRS-1004`.
8. **Decision Coverage**: Explicitly generates separate test cases for `IVT_Mode_ModeLgc = True` AND `IVT_Mode_ModeLgc = False`.

---

## 🛠️ Troubleshooting & Support

- **Issue: `SSH Tunnel: CLOSED` (Red Badge)**
  - *Fix*: Re-run `ssh -L 11434:localhost:11434 root1@172.19.64.35` in your terminal and refresh your browser page (`F5`).
- **Issue: `bind [127.0.0.1]:11434: Permission denied`**
  - *Fix*: An existing SSH tunnel or Ollama process is already using port 11434. Simply close extra terminal windows or proceed directly to **http://localhost:8080**.
- **Issue: `ModuleNotFoundError`**
  - *Fix*: Re-run `pip install -r requirements.txt`.
