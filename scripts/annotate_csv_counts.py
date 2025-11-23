#!/usr/bin/env python3
"""
Annotate CSV rows with two new columns:
 - num_test_methods: number of occurrences of '@Test' under chatunitest-tests
 - num_chatgpt_prompts: total number of records in history records.json files

Usage: run from the workspace root. It reads `quality_summary - Copy.csv` in the
same directory and writes `quality_summary - Copy.with_counts.csv` next to it.
"""

# python3 annotate_csv_counts.py
import csv
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_IN = ROOT / 'quality_summary - Copy.csv'
CSV_OUT = ROOT / 'quality_summary - Copy.with_counts.csv'

TEST_ANNOT_RE = re.compile(r"@(?:[A-Za-z0-9_]+\.)*Test\b")

def _strip_java_comments(source: str) -> str:
    """Remove /* ... */ block comments and // line comments from Java source.
    This is not a full Java parser but is sufficient to avoid counting @Test inside
    comments in generated test files.
    """
    # remove block comments
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    # remove line comments
    source = re.sub(r"//.*?$", "", source, flags=re.MULTILINE)
    return source


def timestamp_to_folder(ts: str) -> str:
    # Example ts: 2025-10-24T03:06:18.276201Z
    if ts is None:
        return ''
    s = ts.strip()
    if s.endswith('Z'):
        s = s[:-1]
    # remove fractional seconds if present
    if '.' in s:
        s = s.split('.', 1)[0]
    # remove non-digit chars except the 'T'
    # produce YYYYMMDDTHHMMSSZ
    parts = s.split('T')
    if len(parts) != 2:
        return ''
    date, time = parts
    datep = date.replace('-', '')
    timep = time.replace(':', '')
    return f"{datep}T{timep}Z"


def count_tests(test_dir: Path) -> int:
    if not test_dir.exists():
        return 0
    total = 0
    for p in test_dir.rglob('*.java'):
        try:
            text = p.read_text(errors='ignore')
            # strip comments to avoid counting @Test inside comments
            text_nocomment = _strip_java_comments(text)
            # count occurrences per file (more robust than a single pass)
            matches = TEST_ANNOT_RE.findall(text_nocomment)
            total += len(matches)
        except Exception:
            continue
    return total


def count_test_files(test_dir: Path) -> int:
    """Count number of .java files under test_dir."""
    if not test_dir.exists():
        return 0
    return sum(1 for _ in test_dir.rglob('*.java'))


def count_prompts(history_dir: Path) -> int:
    # history_dir may be None or a Path; if missing or not existing, return 0.
    if history_dir is None:
        return 0
    if not history_dir.exists():
        return 0
    total = 0
    # For each records.json file, prefer counting individual messages inside the
    # `prompt` array of each record (more accurate). If records are plain arrays
    # without `prompt` fields, fall back to counting top-level items. Also handle
    # NDJSON (one JSON per line) by reading line-by-line.
    for p in history_dir.rglob('records.json'):
        try:
            text = p.read_text()
        except Exception:
            continue

        counted_for_file = 0
        # Try to parse as a JSON array/object first
        try:
            data = json.loads(text)
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and 'prompt' in entry and isinstance(entry['prompt'], list):
                        counted_for_file += len(entry['prompt'])
                    else:
                        # no prompt array: count this record as 1
                        counted_for_file += 1
            elif isinstance(data, dict):
                # single object: if it has a prompt array, count its length; else count 1
                if 'prompt' in data and isinstance(data['prompt'], list):
                    counted_for_file += len(data['prompt'])
                else:
                    counted_for_file += 1
            total += counted_for_file
            continue
        except Exception:
            # not a single JSON array/object; try NDJSON (one JSON per line)
            pass

        # NDJSON fallback: parse each non-empty line as JSON
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and 'prompt' in obj and isinstance(obj['prompt'], list):
                    total += len(obj['prompt'])
                else:
                    total += 1
            except Exception:
                # ignore malformed lines
                continue
    return total


def count_tokens(history_dir: Path, max_tokens: dict) -> tuple:
    """Count total promptToken and responseToken from all records.json files.
    
    Args:
        history_dir: The history directory containing records.json files
        max_tokens: Dictionary with 'prompt' and 'response' keys to track maximums
    
    Returns:
        Tuple of (total_prompt_tokens, total_response_tokens)
    """
    if history_dir is None or not history_dir.exists():
        return (0, 0)
    
    total_prompt_tokens = 0
    total_response_tokens = 0
    for p in history_dir.rglob('records.json'):
        try:
            text = p.read_text()
            data = json.loads(text)
            
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        pt = entry.get('promptToken', 0)
                        rt = entry.get('responseToken', 0)
                        max_tokens['prompt'] = max(pt, max_tokens['prompt'])
                        max_tokens['response'] = max(rt, max_tokens['response'])
                        total_prompt_tokens += pt
                        total_response_tokens += rt
        except Exception as e:
            print(e)
            continue
    
    return (total_prompt_tokens, total_response_tokens)


def count_class_methods(run_dir: Path, project_name: str = None, target_class: str = None) -> int:
    """Count number of methods in the specific target class's class.json file.
    
    Args:
        run_dir: The run directory (e.g., 20251024T050124Z)
        project_name: The project name (e.g., commons-cli)
        target_class: The target class name (e.g., CommandLine, DefaultParser)
    
    Returns:
        Number of methods in the target class's methodSigs, or 0 if not found
    """
    if not run_dir.exists() or not target_class:
        return 0
    
    # Look for class-info directory inside run_dir/project_name/class-info
    class_info_dir = None
    if project_name:
        candidate = run_dir / os.path.basename(project_name) / 'class-info'
        if candidate.exists() and candidate.is_dir():
            class_info_dir = candidate
    
    # Fallback: search for class-info directly under run_dir
    if class_info_dir is None:
        for p in run_dir.iterdir():
            if p.is_dir():
                candidate = p / 'class-info'
                if candidate.exists() and candidate.is_dir():
                    class_info_dir = candidate
                    break
    
    if class_info_dir is None:
        return 0
    
    # Search for the specific target class's class.json file
    # The pattern is: class-info/.../TargetClassName/class.json
    for class_json_path in class_info_dir.rglob('class.json'):
        # Check if this is the target class by checking parent directory name
        if class_json_path.parent.name == target_class:
            try:
                with class_json_path.open('r') as f:
                    data = json.load(f)
                    # Count entries in methodSigs dictionary
                    if 'methodSigs' in data and isinstance(data['methodSigs'], dict):
                        return len(data['methodSigs'])
            except Exception:
                continue
    
    return 0


def find_history_dir(run_dir: Path, project_name: str = None) -> Path:
    # look for any subdirectory starting with 'history'
    # If project_name is provided, prefer run_dir/project_name/history*
    if not run_dir.exists():
        return None

    # First look inside run_dir/<project_name>/ if project_name given
    if project_name:
        candidate = run_dir / os.path.basename(project_name)
        if candidate.exists() and candidate.is_dir():
            for p in candidate.iterdir():
                if p.is_dir() and p.name.startswith('history'):
                    return p

    # Fall back to searching directly under run_dir
    for p in run_dir.iterdir():
        if p.is_dir() and p.name.startswith('history'):
            return p
    return None


def count_public_methods(history_dir: Path, target_class: str = None) -> int:
    """Count number of method folders for the target class in history directory.
    
    Args:
        history_dir: The history directory containing class folders
        target_class: The target class name to find
    
    Returns:
        Number of method folders under the target class's folder, or 0 if not found
    """
    if history_dir is None or not history_dir.exists() or not target_class:
        return 0
    
    # Look for class folders and match against target_class
    # Need to check classMapping.json to map class folder names to actual class names
    class_mapping = {}
    parent_dir = history_dir.parent
    mapping_file = parent_dir / 'classMapping.json'
    
    if mapping_file.exists():
        try:
            with mapping_file.open('r') as f:
                class_mapping = json.load(f)
        except Exception:
            pass
    
    # Find the class folder that matches target_class
    for class_folder in history_dir.iterdir():
        if not class_folder.is_dir() or not class_folder.name.startswith('class'):
            continue
        
        # Check if this class folder matches the target class
        actual_class_name = class_folder.name
        if class_folder.name in class_mapping:
            actual_class_name = class_mapping[class_folder.name].get('className', class_folder.name)
        
        if actual_class_name == target_class:
            # Count method folders in this class folder
            method_count = sum(1 for p in class_folder.iterdir() 
                             if p.is_dir() and p.name.startswith('method'))
            return method_count
    
    return 0


def main():
    if not CSV_IN.exists():
        print(f"Input CSV not found: {CSV_IN}")
        return 1

    rows = []
    with CSV_IN.open(newline='') as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames[:] if reader.fieldnames else []
        
        # Remove unwanted columns if they exist
        for col in ['total_generated_tests', 'flaky_rate_pct', 'pit_path', 'jacoco_path', 'idflakies_candidates']:
            if col in fieldnames:
                fieldnames.remove(col)
        
        # Add num_class_methods right after flaky_count if not present
        if 'num_class_methods' not in fieldnames:
            if 'flaky_count' in fieldnames:
                idx = fieldnames.index('flaky_count') + 1
                fieldnames.insert(idx, 'num_class_methods')
            else:
                fieldnames.append('num_class_methods')
        
        # Add backup_folder column right after timestamp if not present
        if 'backup_folder' not in fieldnames:
            if 'timestamp' in fieldnames:
                idx = fieldnames.index('timestamp') + 1
                fieldnames.insert(idx, 'backup_folder')
            else:
                fieldnames.insert(0, 'backup_folder')
        
        # Add other count columns at the end if not present
        if 'num_public_methods' not in fieldnames:
            fieldnames.append('num_public_methods')
        if 'num_test_files' not in fieldnames:
            fieldnames.append('num_test_files')
        if 'num_test_methods' not in fieldnames:
            fieldnames.append('num_test_methods')
        if 'num_chatgpt_prompts' not in fieldnames:
            fieldnames.append('num_chatgpt_prompts')
        if 'total_prompt_tokens' not in fieldnames:
            fieldnames.append('total_prompt_tokens')
        if 'total_response_tokens' not in fieldnames:
            fieldnames.append('total_response_tokens')
        
        for r in reader:
            rows.append(r)

    # Track max tokens across all rows
    max_tokens = {'prompt': 0, 'response': 0}
    max_public_methods = 0
    total_public_methods = 0

    # Prefer mapping CSV rows to run folders by lexical sort order when possible,
    # and print the mapping between CSV entry (timestamp) and folder name.
    candidate_runs = [p for p in ROOT.iterdir() if p.is_dir() and re.match(r'^\d{8}T\d{6}Z', p.name)]
    candidate_runs = sorted(candidate_runs, key=lambda p: p.name)

    if len(candidate_runs) == len(rows) and len(candidate_runs) > 0:
        print(f"Mapping CSV rows to {len(candidate_runs)} run folders by sorted order")
        for idx, r in enumerate(rows):
            run_dir = candidate_runs[idx]
            # print mapping (index, timestamp -> folder)
            print(f"Row {idx}: timestamp={r.get('timestamp','')} -> folder={run_dir.name}")

            test_dir = run_dir / 'chatunitest-tests'
            # prefer history inside the project's folder if project_root is provided
            project_root = r.get('project_root') if isinstance(r, dict) else None
            target_class = r.get('target_class') if isinstance(r, dict) else None
            history_dir = find_history_dir(run_dir, project_root)

            num_tests = count_tests(test_dir)
            num_prompts = count_prompts(history_dir)
            num_files = count_test_files(test_dir)
            num_class_methods = count_class_methods(run_dir, project_root, target_class)
            num_public_methods = count_public_methods(history_dir, target_class)
            prompt_tokens, response_tokens = count_tokens(history_dir, max_tokens)

            max_public_methods = max(max_public_methods, num_public_methods)
            total_public_methods += num_public_methods

            r['backup_folder'] = run_dir.name
            r['num_class_methods'] = str(num_class_methods)
            r['num_public_methods'] = str(num_public_methods)
            r['num_test_files'] = str(num_files)
            r['num_test_methods'] = str(num_tests)
            r['num_chatgpt_prompts'] = str(num_prompts)
            r['total_prompt_tokens'] = str(prompt_tokens)
            r['total_response_tokens'] = str(response_tokens)
    else:
        if candidate_runs:
            print(f"Candidate run folder count ({len(candidate_runs)}) != CSV rows ({len(rows)}); falling back to timestamp mapping")
        for r in rows:
            ts = r.get('timestamp', '')
            folder = timestamp_to_folder(ts)
            run_dir = ROOT / folder

            # fallback: if exact folder not exist, try to find folder that startswith timestamp prefix
            if not run_dir.exists():
                candidates = [p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith(folder.rstrip('Z'))]
                run_dir = candidates[0] if candidates else Path()

            print(f"Timestamp {ts} -> folder {run_dir.name if run_dir.exists() else run_dir}")

            test_dir = run_dir / 'chatunitest-tests'
            project_root = r.get('project_root') if isinstance(r, dict) else None
            target_class = r.get('target_class') if isinstance(r, dict) else None
            history_dir = find_history_dir(run_dir, project_root)

            num_tests = count_tests(test_dir)
            num_prompts = count_prompts(history_dir)
            num_files = count_test_files(test_dir)
            num_class_methods = count_class_methods(run_dir, project_root, target_class)
            num_public_methods = count_public_methods(history_dir, target_class)
            prompt_tokens, response_tokens = count_tokens(history_dir, max_tokens)

            max_public_methods = max(max_public_methods, num_public_methods)
            total_public_methods += num_public_methods

            r['backup_folder'] = run_dir.name if run_dir.exists() else ''
            r['num_class_methods'] = str(num_class_methods)
            r['num_public_methods'] = str(num_public_methods)
            r['num_test_files'] = str(num_files)
            r['num_test_methods'] = str(num_tests)
            r['num_chatgpt_prompts'] = str(num_prompts)
            r['total_prompt_tokens'] = str(prompt_tokens)
            r['total_response_tokens'] = str(response_tokens)

    with CSV_OUT.open('w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            # replace project_root with its basename (last folder) for compactness
            if r.get('project_root'):
                try:
                    r['project_root'] = os.path.basename(r['project_root'])
                except Exception:
                    pass
            # Remove fields that are not in fieldnames
            row_to_write = {k: v for k, v in r.items() if k in fieldnames}
            writer.writerow(row_to_write)

    print(f"Wrote annotated CSV to: {CSV_OUT}")
    print(f"max prompt token: {max_tokens['prompt']}")
    print(f"max response token: {max_tokens['response']}")
    print(f"max public methods: {max_public_methods}")
    print(f"total public methods: {total_public_methods}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
