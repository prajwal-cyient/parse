import os
import re
import json

def find_json_objects(text):
    results = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] in '{[':
            start = i
            stack = [text[i]]
            i += 1
            in_string = False
            escape = False
            while i < n and stack:
                ch = text[i]
                if escape:
                    escape = False
                elif ch == '\\' and in_string:
                    escape = True
                elif ch == '"':
                    in_string = not in_string
                elif not in_string:
                    if ch in '{[':
                        stack.append(ch)
                    elif ch == '}' and stack[-1] == '{':
                        stack.pop()
                    elif ch == ']' and stack[-1] == '[':
                        stack.pop()
                i += 1
            if not stack:
                candidate = text[start:i]
                try:
                    obj = json.loads(candidate, strict=False)
                    results.append((start, i, obj))
                except Exception:
                    cleaned = re.sub(r'[\r\n]+', ' ', candidate)
                    try:
                        obj = json.loads(cleaned, strict=False)
                        results.append((start, i, obj))
                    except Exception:
                        pass
        else:
            i += 1
    return results

def parse_file_content(filename, content):
    pattern = re.compile(r'(?:\r?\n|^)\s*(\d+)\s*\.\s*requirement\b', re.IGNORECASE)
    matches = list(pattern.finditer(content))
    
    parsed_reqs = []
    
    for idx, m in enumerate(matches):
        req_num = m.group(1)
        start_pos = m.start()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        block = content[start_pos:end_pos]
        
        # 1. ID
        id_match = re.search(r'ID\s*:\s*([^\r\n]+)', block)
        req_id = id_match.group(1).strip() if id_match else 'N/A'
        
        # 2. Req Type
        type_match = re.search(r'Req\s+Type\s*:\s*([^\r\n]+)', block, re.IGNORECASE)
        req_type = type_match.group(1).strip() if type_match else 'N/A'
        
        # 3. Safety Impact
        safety_impact_match = re.search(r'Safety\s+Impact\s*:\s*([^\r\n]+)', block, re.IGNORECASE)
        safety_impact = safety_impact_match.group(1).strip() if safety_impact_match else 'N/A'
        
        # 4. Safety Rationale
        safety_rat_match = re.search(r'Safety\s+Rationale\s*:\s*([^\r\n]+)', block, re.IGNORECASE)
        safety_rat = safety_rat_match.group(1).strip() if safety_rat_match else 'N/A'
        
        # 5. Extract JSON test cases & ranges
        json_objs = find_json_objects(block)
        test_cases = []
        json_ranges = []
        for j_start, j_end, obj in json_objs:
            json_ranges.append((j_start, j_end))
            if isinstance(obj, dict) and 'test_cases' in obj:
                test_cases.extend(obj['test_cases'])
            elif isinstance(obj, list):
                test_cases.extend(obj)
                
        # Slice out JSON substrings from block to leave only pure text & metadata
        non_json_block = ""
        last_idx = 0
        for j_start, j_end in sorted(json_ranges):
            non_json_block += block[last_idx:j_start]
            last_idx = j_end
        non_json_block += block[last_idx:]
        
        # 6. Extract Requirement Text and Notes
        lines = non_json_block.splitlines()
        clean_lines = []
        notes = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'^\d+\s*\.\s*requirement\b', stripped, re.IGNORECASE) or stripped.lower() == 'requirement:':
                continue
            if re.match(r'^ID\s*:', stripped, re.IGNORECASE):
                continue
            if re.match(r'^Req\s+Type\s*:', stripped, re.IGNORECASE):
                continue
            if re.match(r'^Safety\s+Impact\s*:', stripped, re.IGNORECASE):
                continue
            if re.match(r'^Safety\s+Rationale\s*:', stripped, re.IGNORECASE):
                continue
            if stripped.startswith('```'):
                continue
            if re.match(r'^(NOTE|Note)\s*:', stripped, re.IGNORECASE):
                notes.append(stripped)
                continue
            clean_lines.append(line)
            
        req_text = "\n".join(clean_lines).strip()
        notes_text = "\n".join(notes).strip()
        
        parsed_reqs.append({
            'source_file': filename,
            'req_num': req_num,
            'req_id': req_id,
            'req_text': req_text,
            'notes': notes_text,
            'req_type': req_type,
            'safety_impact': safety_impact,
            'safety_rationale': safety_rat,
            'test_cases': test_cases
        })
        
    return parsed_reqs
