import sys
import json
import re
from docx import Document
from parser_engine import ParsingPipeline

def extract_from_docx(path):
    doc = Document(path)
    raw_data = []
    
    # 1. Extract requirements using regex matching
    _ID_RE = re.compile(r"^id\s*:\s*(.+)$", re.IGNORECASE)
    _REQTYPE_RE = re.compile(r"^req\s*type\s*:\s*(.*)$", re.IGNORECASE)
    _NOTE_RE = re.compile(r"^\s*note\b", re.IGNORECASE)
    
    current_req = None
    
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    # Iterate through all elements in the body
    last_table_id = "Table 1"
    last_table_title = "Extracted Table"
    
    _TABLE_RE = re.compile(r"^(Table\s+\d+)", re.IGNORECASE)
    
    merged_tables_count = 0

    def finalize_req():
        if current_req:
            # Check if it's a non-requirement
            req_type = current_req.get("req_type", "").lower()
            if req_type != "non-requirement":
                raw_data.append(current_req)

    for child in doc.element.body:
        if isinstance(child, CT_P):
            para = Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                continue
                
            m_id = _ID_RE.match(text)
            if m_id:
                finalize_req()
                current_req = {
                    "req_id": m_id.group(1).strip(),
                    "text": "",
                    "notes": [],
                    "req_type": ""
                }
                continue
                
            if current_req:
                m_type = _REQTYPE_RE.match(text)
                if m_type:
                    current_req["req_type"] = m_type.group(1).strip()
                    continue
                    
                if _NOTE_RE.match(text):
                    current_req["notes"].append(text)
                else:
                    low_text = text.lower()
                    if low_text.startswith("safety impact"):
                        # Extract safety impact
                        parts = text.split(":", 1)
                        if len(parts) > 1:
                            current_req["safety_impact"] = parts[1].strip()
                    elif low_text.startswith("safety rationale"):
                        # Extract safety rationale
                        parts = text.split(":", 1)
                        if len(parts) > 1:
                            current_req["safety_rationale"] = parts[1].strip()
                    else:
                        current_req["text"] += text + "\n"
                        
            # Check if this paragraph contains a Table ID (usually right before a table)
            m_table = _TABLE_RE.match(text)
            if m_table:
                last_table_id = m_table.group(1)
                last_table_title = text
                
        elif isinstance(child, CT_Tbl):
            table = Table(child, doc)
            headers = []
            rows = []
            for j, row in enumerate(table.rows):
                row_data = [cell.text.strip() for cell in row.cells]
                if j == 0:
                    headers = row_data
                else:
                    rows.append(row_data)
                    
            # Check if it's a continuation of the previous table
            is_continuation = False
            if raw_data and raw_data[-1].get("type") == "table":
                prev_table = raw_data[-1]
                if prev_table["table_id"] == last_table_id or "(continued)" in last_table_title.lower():
                    is_continuation = True
                    
            if is_continuation:
                # Merge rows into the previous table
                raw_data[-1]["rows"].extend(rows)
                merged_tables_count += 1
            else:
                raw_data.append({
                    "type": "table",
                    "table_id": last_table_id,
                    "title": last_table_title,
                    "headers": headers,
                    "rows": rows
                })
            
    finalize_req()
        
    return raw_data, merged_tables_count

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_pipeline.py <input.docx> <output.json>")
        sys.exit(1)
        
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    
    raw_data, merged_count = extract_from_docx(in_path)
    
    pipeline = ParsingPipeline()
    final_output = pipeline.process(raw_data)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
        
    # Analyze final output for validation report
    reqs = final_output.get("requirements", [])
    tables = final_output.get("tables", {})
        
    step_tables_count = sum(1 for t in tables.values() if t.get("classification") == "STEP_TABLE")
    register_tables_count = sum(1 for t in tables.values() if t.get("classification") == "REGISTER_TABLE")
    pin_tables_count = sum(1 for t in tables.values() if t.get("classification") == "PIN_CONFIGURATION")
        
    print("\n===========================================================")
    print("VALIDATION REPORT")
    print("===========================================================")
    print(f"Requirements extracted           : {len(reqs)}")
    print(f"Unique tables stored globally    : {len(tables)}")
    print(f"Merged tables (pages combined)   : {merged_count}")
    print(f"Procedural step tables           : {step_tables_count}")
    print(f"Register tables                  : {register_tables_count}")
    print(f"Pin configuration tables         : {pin_tables_count}")
    
    # Let's count how many tables were extracted initially in raw_data
    total_raw_tables = sum(1 for item in raw_data if item.get("type") == "table")
    print(f"Total separate tables mapped     : {total_raw_tables}")
    print("Incorrect requirements removed   : YES (Non-requirement types filtered)")
    print(f"JSON generated successfully      : YES ({out_path})")
    print("===========================================================\n")

