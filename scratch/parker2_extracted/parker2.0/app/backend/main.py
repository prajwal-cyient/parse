import os
import json
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Body
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from docx_parser import UniversalDocxParser
from ollama_client import OllamaClient
from excel_exporter import ExcelExporter
from history_manager import HistoryManager
from auth_manager import AuthManager
from db_manager import DBManager
from validation_engine import ValidationEngine
from applicability_engine import ApplicabilityEngine
from consolidation_engine import ConsolidationEngine
from signal_classifier import SignalClassifier, SignalDictionary

APP_DIR = r"c:\Users\pm89542\Desktop\parse\app"
UPLOADS_DIR = os.path.join(APP_DIR, "uploads")
OUTPUTS_DIR = os.path.join(APP_DIR, "ui_outputs")
CACHE_DIR = os.path.join(APP_DIR, "cache")
FRONTEND_DIR = os.path.join(APP_DIR, "frontend")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

app = FastAPI(title="DO-178C Verification Test Case Generator Engine", version="4.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Real PostgreSQL 15 'parker' Database Tables
AuthManager.initialize_db()

SESSION_STATE = {
    "parsed_data": None,
    "generated_tcs": [],
    "current_file_path": None,
    "current_file_name": None
}

def load_cached_testcases(base_name):
    """Loads all cached test cases from cache or output JSON files."""
    cache_path = os.path.join(CACHE_DIR, f"cache_{base_name}.json")
    output_path = os.path.join(OUTPUTS_DIR, f"{base_name}_generated_testcases.json")
    
    cached_map = {}
    
    # 1. Load from cache file if available
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as cf:
                data = json.load(cf)
                if isinstance(data, dict) and "test_cases" in data:
                    for tc in data["test_cases"]:
                        req_id = tc.get("requirement_id", "UNKNOWN")
                        cached_map.setdefault(req_id, []).append(tc)
                elif isinstance(data, list):
                    for tc in data:
                        req_id = tc.get("requirement_id", "UNKNOWN")
                        cached_map.setdefault(req_id, []).append(tc)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            cached_map[k] = v
        except Exception:
            cached_map = {}

    # 2. Fallback from outputs JSON file if cache was empty
    if not cached_map and os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as of:
                data = json.load(of)
                items = data if isinstance(data, list) else data.get("test_cases", [])
                for tc in items:
                    req_id = tc.get("requirement_id", "UNKNOWN")
                    if req_id not in cached_map:
                        cached_map[req_id] = []
                    existing_ids = {t.get("test_case_id") for t in cached_map[req_id]}
                    if tc.get("test_case_id") not in existing_ids:
                        cached_map[req_id].append(tc)
        except Exception:
            pass

    return cached_map

# ==========================================
# Real Authentication API Endpoints (PostgreSQL)
# ==========================================
@app.post("/api/auth/login")
async def login_user(payload: dict = Body(...)):
    username = payload.get("username", "")
    password = payload.get("password", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username/Email and Password are required.")

    res = AuthManager.authenticate_user(username, password)
    if not res["success"]:
        raise HTTPException(status_code=401, detail=res["message"])

    return {
        "status": "SUCCESS",
        "message": "Authentication successful against PostgreSQL 'parker' DB.",
        "user": res["user"]
    }

@app.post("/api/auth/register")
async def register_user(payload: dict = Body(...)):
    full_name = payload.get("full_name", "")
    email = payload.get("email", "")
    password = payload.get("password", "")

    if not full_name or not email or not password:
        raise HTTPException(status_code=400, detail="Full Name, Email, and Password are required.")

    res = AuthManager.register_user(full_name, email, password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])

    return {
        "status": "SUCCESS",
        "message": "Account registered successfully in PostgreSQL 'parker' DB.",
        "user": res["user"]
    }

@app.get("/api/status")
async def get_tunnel_status():
    tunnel_active = OllamaClient.check_ssh_tunnel()
    available_models = OllamaClient.get_available_models()
    return {
        "ssh_tunnel_online": tunnel_active,
        "endpoint": OllamaClient.OLLAMA_URL,
        "model": OllamaClient.MODEL_NAME,
        "available_models": available_models,
        "db_status": "Connected to PostgreSQL 15 (parker)",
        "message": f"Connected to {OllamaClient.MODEL_NAME}" if tunnel_active else "SSH Tunnel DISCONNECTED. Please connect SSH tunnel in terminal!"
    }

@app.get("/api/models")
async def get_available_models():
    models = OllamaClient.get_available_models()
    if "gpt-oss:latest" not in models:
        models.insert(0, "gpt-oss:latest")
    return {
        "active_model": OllamaClient.MODEL_NAME,
        "available_models": models
    }

@app.post("/api/set-model")
async def set_active_model(payload: dict = Body(...)):
    model_name = payload.get("model", "")
    if not model_name:
        raise HTTPException(status_code=400, detail="Model name is required.")
    
    success = OllamaClient.set_active_model(model_name)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid model name.")
        
    return {
        "status": "SUCCESS",
        "active_model": OllamaClient.MODEL_NAME,
        "message": f"Switched active LLM model to: {OllamaClient.MODEL_NAME}"
    }

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx Word documents are supported.")
    
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    parsed_res = await asyncio.to_thread(UniversalDocxParser.parse_document, file_path)
    
    req_count = parsed_res["total_requirements_found"]
    base_name = os.path.splitext(file.filename)[0]

    # Load existing cached test cases
    cached_map = load_cached_testcases(base_name)
    all_cached_tcs = []
    for req_id, tc_list in cached_map.items():
        all_cached_tcs.extend(tc_list)
    if not all_cached_tcs and parsed_res.get("requirements"):
        all_cached_tcs = []

    excel_out_path = os.path.join(OUTPUTS_DIR, f"{base_name}_Test_Cases.xlsx")
    json_out_path = os.path.join(OUTPUTS_DIR, f"{base_name}_generated_testcases.json")

    has_excel = os.path.exists(excel_out_path)
    has_json = os.path.exists(json_out_path)

    SESSION_STATE["current_file_path"] = file_path
    SESSION_STATE["current_file_name"] = file.filename
    SESSION_STATE["parsed_data"] = parsed_res
    SESSION_STATE["generated_tcs"] = all_cached_tcs
    
    return {
        "status": "SUCCESS",
        "file_name": file.filename,
        "total_paragraphs": parsed_res["total_paragraphs"],
        "total_tables": parsed_res["total_tables"],
        "requirements_found": req_count,
        "is_sample_1": parsed_res.get("is_sample_1", False),
        "requirements_preview": parsed_res["requirements"][:10],
        "cached_testcases_count": len(all_cached_tcs),
        "cached_testcases": all_cached_tcs,
        "excel_path": excel_out_path if has_excel else None,
        "json_path": json_out_path if has_json else None
    }

@app.get("/api/generate-stream")
async def generate_stream(force: bool = Query(False)):
    # 1. STRICT SSH / SERVER TUNNEL CHECK
    if not OllamaClient.check_ssh_tunnel():
        raise HTTPException(
            status_code=400,
            detail="Ollama / SSH Tunnel is NOT connected on http://localhost:11434. Please connect terminal tunnel first!"
        )

    parsed_data = SESSION_STATE.get("parsed_data")
    if not parsed_data:
        raise HTTPException(status_code=400, detail="No parsed document available. Upload a .docx file first.")

    requirements = parsed_data["requirements"]
    total_reqs = len(requirements)
    doc_tables = parsed_data.get("tables", [])
    full_text = "\n".join(r.get("text", "") for r in requirements)
    req_ids = [r["id"] for r in requirements]
    app_ctx = ApplicabilityEngine.build_context(
        tables=doc_tables, full_text=full_text, req_ids=req_ids)
    signal_dict = SignalDictionary.build(requirements, exclude_tokens=set(req_ids))
    file_name = SESSION_STATE["current_file_name"]
    base_name = os.path.splitext(file_name)[0]
    cache_file_path = os.path.join(CACHE_DIR, f"cache_{base_name}.json")

    # If force is True, clear cache to force 100% fresh AI generation for all requirements!
    if force:
        if os.path.exists(cache_file_path):
            try:
                os.remove(cache_file_path)
            except Exception:
                pass
        cached_map = {}
    else:
        cached_map = load_cached_testcases(base_name)

    async def event_generator():
        all_tcs = []
        seen_ids = set()

        if not force:
            # Pre-fill all_tcs from cache
            for req_id, tc_list in cached_map.items():
                for tc in tc_list:
                    if tc["test_case_id"] not in seen_ids:
                        seen_ids.add(tc["test_case_id"])
                        all_tcs.append(tc)

        for idx_offset, req in enumerate(requirements, 1):
            req_id = req["id"]
            req_text = req["text"]
            pct = round((idx_offset / total_reqs) * 100, 1)

            # AUTO-RESUME CHECK: If requirement is ALREADY in cache, send cached result instantly!
            if req_id in cached_map and len(cached_map[req_id]) > 0:
                cached_tcs = cached_map[req_id]
                progress_payload = {
                    "step": "PROGRESS",
                    "current_index": idx_offset,
                    "total_requirements": total_reqs,
                    "requirement_id": req_id,
                    "generated_count_for_req": len(cached_tcs),
                    "total_generated_so_far": len(all_tcs),
                    "percentage": pct,
                    "new_test_cases": cached_tcs,
                    "message": f"Loaded {len(cached_tcs)} test cases for {req_id} from auto-resume cache."
                }
                yield f"data: {json.dumps(progress_payload)}\n\n"
                await asyncio.sleep(0.01)
                continue

            # Send querying payload to UI
            start_payload = {
                "step": "QUERYING",
                "current_index": idx_offset,
                "total_requirements": total_reqs,
                "requirement_id": req_id,
                "percentage": pct,
                "message": f"Querying model '{OllamaClient.MODEL_NAME}' for Requirement {req_id} ({idx_offset}/{total_reqs})..."
            }
            yield f"data: {json.dumps(start_payload)}\n\n"
            await asyncio.sleep(0.01)

            try:
                # Launch query task with document tables and send SSE Keep-Alive ping
                query_task = asyncio.create_task(asyncio.to_thread(
                    OllamaClient.query_requirement,
                    req_id, req_text, 15, 1, doc_tables,
                    full_text, req_ids, app_ctx, signal_dict,
                ))
                while not query_task.done():
                    yield ": ping\n\n"
                    await asyncio.sleep(0.05)
                tcs = await query_task
            except Exception as err:
                print(f"Error querying requirement {req_id}: {err}")
                err_payload = {
                    "step": "WARNING",
                    "requirement_id": req_id,
                    "message": f"Skipping requirement {req_id} due to glitch: {str(err)}. Continuing remaining requirements!"
                }
                yield f"data: {json.dumps(err_payload)}\n\n"
                await asyncio.sleep(0.01)
                continue

            # Apply DO-178C Consolidation and Deduplication Engines
            consolidated = ConsolidationEngine.consolidate_multi_member_records(tcs or [], req_id, req_text)
            if consolidated:
                tcs = consolidated
            else:
                seq_cases = ConsolidationEngine.consolidate_sequential_steps(tcs or [], req_id, req_text)
                if seq_cases:
                    tcs = seq_cases

            # Apply 3-Tier Signal Classification and Sanitization
            members, _ = ApplicabilityEngine.applicable_members(req_text, app_ctx)
            sanitized_tcs = SignalClassifier.sanitize_test_cases(
                tcs or [], req_id, req_text, signal_dict, app_ctx, members=members
            )

            cleaned_tcs = []
            for tc in (sanitized_tcs or []):
                if not isinstance(tc, dict):
                    continue
                tc_id = tc.get("test_case_id", f"TC-{req_id}-{len(all_tcs)+1}")
                if tc_id in seen_ids:
                    tc_id = f"{tc_id}_v{len(all_tcs)+1}"
                seen_ids.add(tc_id)
                tc["test_case_id"] = tc_id
                tc["requirement_id"] = req_id
                tc["test_type"] = str(tc.get("test_type", "NORMAL")).upper()
                tc["related_requirements"] = tc.get("related_requirements", "")
                cleaned_tcs.append(tc)
                all_tcs.append(tc)

                # Send real-time live log update for each generated test case
                tc_log_payload = {
                    "step": "LOG",
                    "requirement_id": req_id,
                    "message": f"  [AI] Generated {tc_id} [{tc['test_type']}]: {str(tc.get('description', ''))[:70]}"
                }
                yield f"data: {json.dumps(tc_log_payload)}\n\n"
                await asyncio.sleep(0.01)

            # Save to incremental cache file immediately
            cached_map[req_id] = cleaned_tcs
            try:
                with open(cache_file_path, "w", encoding="utf-8") as cf:
                    json.dump(cached_map, cf, indent=2)
            except Exception as e:
                print(f"Cache write warning: {e}")

            progress_payload = {
                "step": "PROGRESS",
                "current_index": idx_offset,
                "total_requirements": total_reqs,
                "requirement_id": req_id,
                "generated_count_for_req": len(cleaned_tcs),
                "total_generated_so_far": len(all_tcs),
                "percentage": pct,
                "new_test_cases": cleaned_tcs
            }
            yield f"data: {json.dumps(progress_payload)}\n\n"
            await asyncio.sleep(0.01)

        # DO-178C Comprehensive Client Observations Validation and Sanitization Audit
        all_tcs, validation_report = ValidationEngine.validate_and_sanitize(
            all_tcs, requirements)
        audit_summary = ValidationEngine.audit_test_cases(
            all_tcs, requirements, validation_report)
        print(
            f"[DO-178C ValidationEngine] Audit Status: "
            f"{audit_summary.get('all_passed')} | "
            f"Summary: {json.dumps(audit_summary, indent=2)}"
        )

        SESSION_STATE["generated_tcs"] = all_tcs
        
        json_out_path = os.path.join(OUTPUTS_DIR, f"{base_name}_generated_testcases.json")
        with open(json_out_path, "w", encoding="utf-8") as f:
            json.dump({"file_name": SESSION_STATE["current_file_name"], "total_test_cases": len(all_tcs), "test_cases": all_tcs}, f, indent=2)

        excel_out_path = os.path.join(OUTPUTS_DIR, f"{base_name}_Test_Cases.xlsx")
        try:
            ExcelExporter.export_testcases(all_tcs, excel_out_path, title_text=f"DO-178C {base_name} VERIFICATION TEST CASES")
        except PermissionError:
            import time
            ts = int(time.time())
            excel_out_path = os.path.join(OUTPUTS_DIR, f"{base_name}_Test_Cases_{ts}.xlsx")
            ExcelExporter.export_testcases(all_tcs, excel_out_path, title_text=f"DO-178C {base_name} VERIFICATION TEST CASES")

        # Save to PostgreSQL 15 database 'parker'
        history_entry = HistoryManager.save_run(
            file_name=SESSION_STATE["current_file_name"],
            req_count=total_reqs,
            tc_count=len(all_tcs),
            excel_path=excel_out_path,
            json_path=json_out_path,
            test_cases_data=all_tcs
        )

        completed_payload = {
            "step": "COMPLETED",
            "total_test_cases": len(all_tcs),
            "total_requirements": total_reqs,
            "excel_path": excel_out_path,
            "json_path": json_out_path,
            "history": history_entry,
            "message": f"Successfully generated, exported & stored {len(all_tcs)} test cases using {OllamaClient.MODEL_NAME} into PostgreSQL database 'parker'!"
        }
        yield f"data: {json.dumps(completed_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/history")
async def get_history():
    return HistoryManager.load_history()

@app.post("/api/history-delete")
async def delete_history_item_post(payload: dict = Body(...)):
    run_id = payload.get("id") or payload.get("run_id")
    if not run_id:
        raise HTTPException(status_code=400, detail="Missing run ID in request body.")
    success = HistoryManager.delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"History item '{run_id}' not found.")
    return {"status": "SUCCESS", "message": f"Run {run_id} deleted successfully from PostgreSQL database 'parker'."}

@app.delete("/api/history/{run_id}")
async def delete_history_item_path(run_id: str):
    success = HistoryManager.delete_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"History item '{run_id}' not found.")
    return {"status": "SUCCESS", "message": f"Run {run_id} deleted successfully from PostgreSQL database 'parker'."}

@app.get("/api/download")
async def download_file(file_path: str = Query(...)):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=os.path.basename(file_path))

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
