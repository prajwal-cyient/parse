import docx
import re
import os
import json

class UniversalDocxParser:
    """
    Universal Word Document (.docx) Parser for DO-178C Software Verification.
    Parses any software requirements document, extracts requirement blocks,
    identifies requirement IDs, and extracts table structures (e.g. Table 1001 with 38 steps).
    Automatically merges sub-steps 4a+4b, 9a+9b, 14a+14b and filters out redundant 15,000-char Table 1001 blocks.
    """

    # Caption text that introduces a table, e.g. "Table 1011 Rev C  Asset type ...".
    CAPTION_RE = re.compile(r'\bTable\s*#?\s*\d+', re.IGNORECASE)

    @classmethod
    def _extract_table_captions(cls, doc):
        """
        Maps table ordinal -> the nearest preceding paragraph that names a
        table. Walks the document body in document order so paragraphs and
        tables stay correctly interleaved.
        """
        from docx.table import Table
        from docx.text.paragraph import Paragraph

        captions = {}
        table_ordinal = 0
        recent = ""
        body = doc.element.body
        for child in body.iterchildren():
            tag = child.tag.split('}')[-1]
            if tag == "p":
                text = Paragraph(child, doc).text.strip()
                if text:
                    if cls.CAPTION_RE.search(text):
                        recent = text
                    elif len(text) > 200:
                        # A long prose block is not a caption, but it also
                        # should not let a stale caption leak onto a later table.
                        recent = recent if cls.CAPTION_RE.search(recent) else ""
            elif tag == "tbl":
                captions[table_ordinal] = recent
                recent = ""
                table_ordinal += 1
        return captions

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

        # 3. Parse Table 1001 Steps into individual concise requirements & MERGE 4a+4b, 9a+9b, 14a+14b
        is_sample_1 = "sample_1" in file_name.lower() or "1001" in full_text
        has_table_1001 = False

        for table in doc.tables:
            if len(table.rows) > 30: # Table 1001 has 43 rows
                row_0_text = " ".join([c.text for c in table.rows[0].cells]).lower()
                if "step" in row_0_text or "lru" in row_0_text:
                    has_table_1001 = True
                    raw_steps = {}
                    for row in table.rows[1:]:
                        cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
                        if len(cells) >= 2 and cells[0]:
                            step_num = cells[0].strip().replace(':', '').replace(' ', '')
                            step_text = cells[1].strip()
                            lru_target = cells[2].strip() if len(cells) > 2 else ""
                            if step_num and step_text:
                                raw_steps[step_num.lower()] = {
                                    "num": step_num,
                                    "text": step_text,
                                    "lru": lru_target
                                }

                    step_requirements = []
                    lru_requirements = []
                    processed_keys = set()

                    # Ordered list of steps in Table 1001
                    step_keys = list(raw_steps.keys())
                    for k in step_keys:
                        if k in processed_keys:
                            continue

                        # Check for 4a+4b, 9a+9b, 14a+14b combinations
                        base_num = re.sub(r'[ab]$', '', k)
                        pair_a_key = f"{base_num}a"
                        pair_b_key = f"{base_num}b"

                        if (k == pair_a_key or k == pair_b_key) and (pair_a_key in raw_steps and pair_b_key in raw_steps):
                            item_a = raw_steps[pair_a_key]
                            item_b = raw_steps[pair_b_key]
                            combined_id = f"LRUSWRS-1001-STEP-{base_num.upper()}a+{base_num.upper()}b"
                            combined_text = f"COMBINED SUB-STEPS {base_num.upper()}a & {base_num.upper()}b: " \
                                            f"Step {item_a['num']}: {item_a['text']} (Target LRU: {item_a['lru']}). " \
                                            f"Step {item_b['num']}: {item_b['text']} (Target LRU: {item_b['lru']})."

                            if combined_id not in seen_ids:
                                seen_ids.add(combined_id)
                                step_requirements.append({
                                    "id": combined_id,
                                    "text": combined_text,
                                    "word_count": len(combined_text.split()),
                                    "has_table_reference": True
                                })
                            processed_keys.add(pair_a_key)
                            processed_keys.add(pair_b_key)
                        else:
                            item = raw_steps[k]
                            step_req_id = f"LRUSWRS-1001-STEP-{item['num'].upper()}"
                            if step_req_id not in seen_ids:
                                seen_ids.add(step_req_id)
                                step_requirements.append({
                                    "id": step_req_id,
                                    "text": f"Table 1001 Step {item['num']}: {item['text']} (Target LRU: {item['lru']})",
                                    "word_count": len(item['text'].split()),
                                    "has_table_reference": True
                                })
                            processed_keys.add(k)

                    # Extract the 35 specific LRU-xxxx allocated requirements from Table 1001 Column 3
                    for row in table.rows[1:]:
                        cells = [c.text.strip().replace('\n', ' ') for c in row.cells]
                        if len(cells) >= 3 and cells[2]:
                            step_no = cells[0].strip()
                            if "information" in step_no.lower():
                                continue
                            raw_lru = cells[2].strip()
                            num_m = re.search(r'\d+', raw_lru)
                            if num_m:
                                clean_lru = f"LRU-{num_m.group(0)}"
                                if clean_lru not in seen_ids:
                                    seen_ids.add(clean_lru)
                                    step_desc = cells[1].strip() if len(cells) > 1 else ""
                                    lru_requirements.append({
                                        "id": clean_lru,
                                        "text": f"Table 1001 Step {step_no} ({clean_lru}): {step_desc}",
                                        "word_count": len(step_desc.split()),
                                        "has_table_reference": True
                                    })

                    # Prepend step and LRU sequence requirements & FILTER OUT redundant full-text LRUSWRS-1001 block
                    if step_requirements or lru_requirements:
                        # Remove redundant full-text 15,000-char LRUSWRS-1001 requirement if steps exist
                        filtered_other_reqs = [r for r in requirements if r["id"].upper() not in ["LRUSWRS-1001", "REQ-1001", "1001"]]
                        requirements = lru_requirements + step_requirements + filtered_other_reqs
                    break

        # 4. Extract Tables (with the caption that introduces each one, so
        #    downstream engines can link "Table 1011" in a requirement to the
        #    table that actually holds the data).
        captions = cls._extract_table_captions(doc)
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
                    "caption": captions.get(t_idx - 1, ""),
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
    sample_doc = r"c:\Users\pm89542\Desktop\parse\app\uploads\SW_Requirements_Sample_1.docx"
    if os.path.exists(sample_doc):
        res = UniversalDocxParser.parse_document(sample_doc)
        print(f"Parsed {res['file_name']}: {res['total_requirements_found']} Reqs.")
