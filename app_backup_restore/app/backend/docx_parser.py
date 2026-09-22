import docx
import re
import os
import json

class UniversalDocxParser:
    """
    Universal Word Document (.docx) Parser for DO-178C Software Verification.
    Parses any software requirements document, extracts requirement blocks,
    identifies requirement IDs, and extracts table structures (e.g. Table 1001 with 38 steps).
    """

    TABLE1001_JSON = r"c:\Users\pm89542\Desktop\parse\automation\ALL_TABLE_1001_EXPANDED_TESTCASES.json"

    @classmethod
    def parse_document(cls, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        doc = docx.Document(file_path)
        file_name = os.path.basename(file_path)

        # 1. Extract Full Text & Paragraphs
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs)

        # 2. Extract Requirement Blocks via Regex Pattern Matching
        req_pattern = r"(?=\d+\.\s*[Rr]equirement:|\d+\.\s*[Rr]equirement|ID\s*:\s*[A-Z0-9_-]+|REQ-[0-9]+)"
        blocks = re.split(req_pattern, full_text)

        requirements = []
        seen_ids = set()

        for b in blocks:
            b_str = b.strip()
            if not b_str:
                continue

            id_match = re.search(r"(?:ID\s*:\s*|REQ-|\bLRUSWRS-|\bLRU-)([A-Z0-9_-]+)", b_str, re.IGNORECASE)
            if id_match:
                raw_id = id_match.group(0).strip()
                clean_id = re.sub(r"^ID\s*:\s*", "", raw_id, flags=re.IGNORECASE).strip()
                if not clean_id.startswith("LRUSWRS") and not clean_id.startswith("LRU") and not clean_id.startswith("REQ"):
                    clean_id = f"REQ-{clean_id}"

                if clean_id not in seen_ids:
                    seen_ids.add(clean_id)
                    requirements.append({
                        "id": clean_id,
                        "text": b_str,
                        "word_count": len(b_str.split()),
                        "has_table_reference": bool(re.search(r"Table\s*\d+", b_str, re.IGNORECASE))
                    })

        # 3. Check for Table 1 / Table 1001 (Step Requirements) in SW_Requirements_Sample_1.docx
        is_sample_1 = "sample_1" in file_name.lower() or "1001" in full_text
        has_table_1001 = False

        for table in doc.tables:
            if len(table.rows) > 30: # Table 1001 has 43 rows
                row_0_text = " ".join([c.text for c in table.rows[0].cells]).lower()
                if "step" in row_0_text or "lru" in row_0_text:
                    has_table_1001 = True
                    break

        # 4. Extract Tables
        tables_extracted = []
        for t_idx, table in enumerate(doc.tables, 1):
            table_data = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                if any(row_cells):
                    table_data.append(row_cells)
            if table_data:
                tables_extracted.append({
                    "table_index": t_idx,
                    "rows_count": len(table_data),
                    "headers": table_data[0] if table_data else [],
                    "rows": table_data[1:] if len(table_data) > 1 else []
                })

        return {
            "file_name": file_name,
            "total_paragraphs": len(doc.paragraphs),
            "total_tables": len(doc.tables),
            "total_requirements_found": len(requirements),
            "is_sample_1": is_sample_1 or has_table_1001,
            "has_table_1001": has_table_1001,
            "requirements": requirements,
            "tables": tables_extracted
        }

if __name__ == "__main__":
    sample_doc = r"c:\Users\pm89542\Downloads\test_parker\SW_Requirements_Sample_1.docx"
    if os.path.exists(sample_doc):
        res = UniversalDocxParser.parse_document(sample_doc)
        print(f"Parsed {res['file_name']}: {res['total_requirements_found']} Reqs, is_sample_1={res['is_sample_1']}.")
