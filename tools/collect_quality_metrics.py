#!/usr/bin/env python3
"""Collect quality metrics from local reports.

Reads:
- PIT mutations XML (default: target/pit-reports/mutations.xml)
- JaCoCo CSV or XML (default: target/site/jacoco/jacoco.csv then jacoco.xml)
- Idflakies outputs (best-effort search under target/**/idflakies)

Outputs a JSON summary to stdout.

Usage examples:
  python3 tools/collect_quality_metrics.py
  python3 tools/collect_quality_metrics.py --pit path/to/mutations.xml --jacoco path/to/jacoco.csv

This script is defensive: missing reports are reported as null in the output.
"""
import argparse
import csv
import json
import os
import sys
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


def parse_pit_mutations(pit_path: str, target_class: Optional[str] = None) -> Optional[dict]:
    """Parse PIT's mutations.xml and return counts and computed score.

    Score calculation: killed / (killed + survived) * 100 using only covered mutations.
    NO_COVERAGE mutations are excluded from the denominator.
    """
    if not os.path.isfile(pit_path):
        return None
    try:
        tree = ET.parse(pit_path)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"Failed to parse PIT XML '{pit_path}': {e}")

    killed = 0
    survived = 0
    no_coverage = 0
    total = 0
    target = target_class.lower() if target_class else None
    for m in root.findall('.//mutation'):
        # optionally filter by mutatedClass or sourceFile
        mutated = m.findtext('mutatedClass') or ''
        source_file = m.findtext('sourceFile') or ''
        include = True
        if target:
            mutated_simple = mutated.split('.')[-1].lower()
            source_simple = os.path.splitext(os.path.basename(source_file))[0].lower()
            if not (target == mutated.lower() or target == mutated_simple or target == source_simple):
                include = False
        if not include:
            continue

        total += 1
        status = m.get('status') or ''
        status = status.upper()
        if status == 'KILLED':
            killed += 1
        elif status == 'SURVIVED':
            survived += 1
        elif status == 'NO_COVERAGE':
            no_coverage += 1
        else:
            # if attribute missing or unknown, fallback to detected attr
            detected = m.get('detected')
            if detected and detected.lower() in ('true', 'yes'):
                killed += 1
            else:
                survived += 1

    covered_mutations = killed + survived
    score = None
    if covered_mutations > 0:
        score = killed / covered_mutations * 100.0

    return {
        'path': pit_path,
        'total': total,
        'killed': killed,
        'survived': survived,
        'no_coverage': no_coverage,
        'score_pct': round(score, 2) if score is not None else None,
    }


def parse_jacoco_csv(csv_path: str, target_class: Optional[str] = None) -> Optional[dict]:
    if not os.path.isfile(csv_path):
        return None

    inst_missed = 0
    inst_covered = 0
    line_missed = 0
    line_covered = 0

    target = target_class.lower() if target_class else None
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # optionally filter by CLASS / PACKAGE
            cls = (row.get('CLASS') or '').strip()
            pkg = (row.get('PACKAGE') or '').strip()
            include = True
            if target:
                full = (pkg + '.' + cls).strip('.')
                if not (cls.lower() == target or full.lower() == target or cls.lower().endswith('.' + target)):
                    include = False
            if not include:
                continue

            # header contains fields like INSTRUCTION_MISSED, INSTRUCTION_COVERED
            try:
                im = int(row.get('INSTRUCTION_MISSED', '0') or 0)
                ic = int(row.get('INSTRUCTION_COVERED', '0') or 0)
                lm = int(row.get('LINE_MISSED', '0') or 0)
                lc = int(row.get('LINE_COVERED', '0') or 0)
            except ValueError:
                # skip malformed rows
                continue
            inst_missed += im
            inst_covered += ic
            line_missed += lm
            line_covered += lc

    inst_total = inst_missed + inst_covered
    line_total = line_missed + line_covered
    inst_pct = round((inst_covered / inst_total * 100.0), 2) if inst_total > 0 else None
    line_pct = round((line_covered / line_total * 100.0), 2) if line_total > 0 else None

    return {
        'path': csv_path,
        'instruction_covered': inst_covered,
        'instruction_missed': inst_missed,
        'instruction_coverage_pct': inst_pct,
        'line_covered': line_covered,
        'line_missed': line_missed,
        'line_coverage_pct': line_pct,
    }


def find_idflakies_reports(root: str):
    """Return a list of candidate idflakies report files under root/target.
    The script will attempt to parse json or xml files found.
    """
    candidates = []
    for dirpath, dirs, files in os.walk(root):
        low = dirpath.lower()
        if 'idflakies' in low or 'flakies' in low or 'flaky' in low:
            for f in files:
                if f.lower().endswith(('.json', '.xml', '.txt')):
                    candidates.append(os.path.join(dirpath, f))

    # also look for common target/idflakies locations
    t = os.path.join(root, 'target')
    for dirpath, dirs, files in os.walk(t) if os.path.isdir(t) else []:
        for f in files:
            if 'idflakies' in f.lower() or 'flaky' in f.lower():
                candidates.append(os.path.join(dirpath, f))

    # unique
    return sorted(set(candidates))


def parse_idflakies_candidates(paths, target_class: Optional[str] = None) -> Optional[dict]:
    """Try best-effort parsing of idflakies outputs.

    We attempt to detect JSON structures or XML with counts. If none parseable,
    return None.
    """
    total_flaky = 0
    total_tests = 0
    parsed_any = False

    target = target_class.lower() if target_class else None
    for p in paths:
        try:
            if p.lower().endswith('.json'):
                with open(p, 'r', encoding='utf-8') as fh:
                    j = json.load(fh)
                # heuristics: look for numeric fields
                if isinstance(j, dict):
                    # try common keys
                    if not target and 'flakyTests' in j and 'totalTests' in j:
                        parsed_any = True
                        total_flaky += int(j.get('flakyTests', 0))
                        total_tests += int(j.get('totalTests', 0))
                    elif not target and 'flaky' in j and isinstance(j['flaky'], list):
                        parsed_any = True
                        total_flaky += len(j['flaky'])
                        # total tests unknown
                    else:
                        # If target specified, try to find entries mentioning the class
                        if target:
                            # search strings in JSON
                            txt = json.dumps(j).lower()
                            matches = txt.count(target)
                            if matches:
                                parsed_any = True
                                total_flaky += matches
                        else:
                            # try to count entries that look like tests
                            maybe_tests = 0
                            for v in j.values():
                                if isinstance(v, list):
                                    maybe_tests += len(v)
                            if maybe_tests:
                                parsed_any = True
                                total_tests += maybe_tests
                        
            elif p.lower().endswith('.xml'):
                try:
                    tree = ET.parse(p)
                    root = tree.getroot()
                    # count nodes named 'flaky' or tests with attribute flaky
                    flaky_nodes = root.findall('.//flaky')
                    if flaky_nodes and not target:
                        parsed_any = True
                        total_flaky += len(flaky_nodes)
                    # count tests
                    tests = root.findall('.//test') or root.findall('.//testcase')
                    if tests and not target:
                        parsed_any = True
                        total_tests += len(tests)
                    # if target specified, search for target text in XML
                    if target:
                        txt = ET.tostring(root, encoding='utf-8', method='xml').lower()
                        matches = txt.count(target.encode('utf-8'))
                        if matches:
                            parsed_any = True
                            total_flaky += matches
                except Exception:
                    continue
            else:
                # plain text: look for 'flaky' occurrences or test ids
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    txt = fh.read()
                # heuristic: lines containing 'flaky' or 'FLAKY'
                if target:
                    matches = txt.lower().count(target)
                    if matches:
                        parsed_any = True
                        total_flaky += matches
                else:
                    lines = [l for l in txt.splitlines() if 'flaky' in l.lower()]
                    if lines:
                        parsed_any = True
                        total_flaky += len(lines)
        except Exception:
            continue

    if not parsed_any:
        return None

    flaky_rate = None
    if total_tests > 0:
        flaky_rate = round(total_flaky / total_tests * 100.0, 2)

    return {
        'candidates': paths,
        'flaky_count': total_flaky,
        'total_tests': total_tests if total_tests > 0 else None,
        'flaky_rate_pct': flaky_rate,
    }


def auto_detect_reports(root: str) -> Tuple[Optional[str], Optional[str], list]:
    pit = os.path.join(root, 'target', 'pit-reports', 'mutations.xml')
    # prefer jacoco.csv if available
    jacoco_csv = os.path.join(root, 'target', 'site', 'jacoco', 'jacoco.csv')
    jacoco_xml = os.path.join(root, 'target', 'site', 'jacoco', 'jacoco.xml')

    idflakies_candidates = find_idflakies_reports(root)

    pit_path = pit if os.path.isfile(pit) else None
    jacoco_path = jacoco_csv if os.path.isfile(jacoco_csv) else (jacoco_xml if os.path.isfile(jacoco_xml) else None)

    return pit_path, jacoco_path, idflakies_candidates


def main(argv=None):
    p = argparse.ArgumentParser(description='Collect quality metrics from PIT, JaCoCo and Idflakies reports')
    p.add_argument('--root', default='.', help='project root (defaults to current dir)')
    p.add_argument('--pit', help='path to PIT mutations.xml')
    p.add_argument('--jacoco', help='path to JaCoCo CSV or XML')
    p.add_argument('--idflakies', help='path to idflakies report or directory (optional)')
    p.add_argument('--target-class', help='optional class name to scope metrics (simple name or package.ClassName)')
    p.add_argument('--output', help='optional path to write JSON output (defaults to stdout)')
    p.add_argument('--csv', help='optional path to write one-line CSV summary')
    args = p.parse_args(argv)

    root = os.path.abspath(args.root)

    pit_path = args.pit
    jacoco_path = args.jacoco
    idflakies_input = args.idflakies

    if not pit_path or not os.path.isfile(pit_path):
        detected_pit, detected_j, detected_id = auto_detect_reports(root)
        pit_path = pit_path or detected_pit
        if not jacoco_path:
            jacoco_path = detected_j
        if not idflakies_input:
            idflakies_input = detected_id

    # normalize target class input to support several forms:
    # - fully-qualified with dots: org.apache.commons.cli.HelpFormatter
    # - path-like with slashes: org/apache/commons/cli/HelpFormatter
    # - simple class name: HelpFormatter
    target_raw = args.target_class
    if target_raw:
        t = target_raw.strip()
        # accept windows backslashes and convert to slashes first
        t = t.replace('\\', '/')
        # convert path separators to dots
        t = t.replace('/', '.')
        # strip .java or .class suffixes if present
        if t.lower().endswith('.java') or t.lower().endswith('.class'):
            t = t.rsplit('.', 1)[0]
        # remove any leading/trailing dots
        t = t.strip('.')
        args.target_class = t

    result = {'project_root': root}

    # PIT
    try:
        pit_metrics = parse_pit_mutations(pit_path, target_class=args.target_class) if pit_path else None
    except Exception as e:
        pit_metrics = {'error': str(e), 'path': pit_path}
    result['pit'] = pit_metrics

    # JaCoCo
    jacoco_metrics = None
    if jacoco_path:
        if jacoco_path.endswith('.csv'):
            try:
                jacoco_metrics = parse_jacoco_csv(jacoco_path, target_class=args.target_class)
            except Exception as e:
                jacoco_metrics = {'error': str(e), 'path': jacoco_path}
        else:
            # jacoco XML could be parsed for counters; try to parse instruction/line counters
            try:
                if os.path.isfile(jacoco_path):
                    tree = ET.parse(jacoco_path)
                    root_el = tree.getroot()
                    inst_cov = 0
                    inst_miss = 0
                    line_cov = 0
                    line_miss = 0
                    # If target_class requested, XML parsing per-class is harder; fall back to CSV match
                    for counter in root_el.findall('.//counter'):
                        t = counter.get('type')
                        cov = int(counter.get('covered', '0'))
                        miss = int(counter.get('missed', '0'))
                        if t == 'INSTRUCTION':
                            inst_cov += cov
                            inst_miss += miss
                        if t == 'LINE':
                            line_cov += cov
                            line_miss += miss
                    inst_total = inst_cov + inst_miss
                    line_total = line_cov + line_miss
                    jacoco_metrics = {
                        'path': jacoco_path,
                        'instruction_covered': inst_cov,
                        'instruction_missed': inst_miss,
                        'instruction_coverage_pct': round(inst_cov / inst_total * 100.0, 2) if inst_total else None,
                        'line_covered': line_cov,
                        'line_missed': line_miss,
                        'line_coverage_pct': round(line_cov / line_total * 100.0, 2) if line_total else None,
                    }
            except Exception as e:
                jacoco_metrics = {'error': str(e), 'path': jacoco_path}
    result['jacoco'] = jacoco_metrics

    # Idflakies
    idf_metrics = None
    if idflakies_input:
        if isinstance(idflakies_input, (list, tuple)):
            candidates = idflakies_input
        elif os.path.isdir(idflakies_input):
            candidates = [os.path.join(idflakies_input, f) for f in os.listdir(idflakies_input)]
        else:
            candidates = [idflakies_input]

        candidates = [c for c in candidates if os.path.exists(c)]
        if candidates:
            idf_metrics = parse_idflakies_candidates(candidates, target_class=args.target_class)
        else:
            idf_metrics = None
    else:
        # try auto-detected candidates
        candidates = find_idflakies_reports(root)
        idf_metrics = parse_idflakies_candidates(candidates, target_class=args.target_class) if candidates else None

    result['idflakies'] = idf_metrics

    # Writing to .dtfixingtools is disabled to avoid modifying the repository/workspace.
    # Previous behavior wrote flaky counts to .dtfixingtools/detection-results/flaky-lists.json.
    # To re-enable, restore the original write logic or add a command-line flag/env var guard.

    # Print JSON
    out = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as fh:
            fh.write(out)
        print(f"Wrote summary to {args.output}")
    else:
        print(out)

    # optional CSV summary (append mode). Default to tools/quality_summary.csv if not provided
    csv_path = args.csv if getattr(args, 'csv', None) else os.path.join(root, 'tools', 'quality_summary.csv')
    try:
        write_csv_summary(result, csv_path, target_class=args.target_class)
        print(f"Appended CSV summary to {csv_path}")
    except Exception as e:
        print(f"Failed to write CSV summary to {csv_path}: {e}", file=sys.stderr)


def _safe_get(d: Optional[dict], *keys):
    """Return nested value or None if any missing."""
    if not d:
        return None
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur


def write_csv_summary(result: dict, csv_path: str, target_class: Optional[str] = None):
    """Write a one-row CSV with the requested metrics.

    Columns:
      project_root, line_coverage_pct, mutation_score_pct,
      flaky_count, total_generated_tests, flaky_rate_pct,
      pit_path, jacoco_path, idflakies_candidates
    """
    import csv

    project_root = result.get('project_root')
    line_cov = _safe_get(result.get('jacoco'), 'line_coverage_pct')
    mut_score = _safe_get(result.get('pit'), 'score_pct')
    # Prefer flaky counts from .dtfixingtools/detection-results/flaky-lists.json if available
    flaky_count = _safe_get(result.get('idflakies'), 'flaky_count')
    total_tests = _safe_get(result.get('idflakies'), 'total_tests')
    flaky_rate = _safe_get(result.get('idflakies'), 'flaky_rate_pct')
    try:
        project_root = result.get('project_root')
        flakes_file = os.path.join(project_root or '.', '.dtfixingtools', 'detection-results', 'flaky-lists.json')
        if os.path.isfile(flakes_file):
            with open(flakes_file, 'r', encoding='utf-8') as fh:
                j = json.load(fh)

            # Support two observed formats:
            # 1) legacy mapping: { "<classOrProject>": { 'flaky_count': ..., ... }, ... }
            # 2) idflakies-style list: { 'dts': [ { 'name': 'pkg.ClassTest#test...', ... }, ... ] }
            key = target_class or 'project'
            # legacy mapping
            if isinstance(j, dict) and any(k for k in j.keys() if k != 'dts'):
                entry = None
                if key in j:
                    entry = j.get(key)
                else:
                    # try simple class name fallback
                    if key and '.' in key:
                        simple = key.split('.')[-1]
                        entry = j.get(simple, None)
                if entry and isinstance(entry, dict):
                    flaky_count = entry.get('flaky_count', flaky_count)
                    # older format used total_generated_tests key name
                    total_tests = entry.get('total_generated_tests', total_tests) or entry.get('total_tests', total_tests)
                    flaky_rate = entry.get('flaky_rate_pct', flaky_rate)

            # dts list format: count entries (optionally filter by target_class)
            if isinstance(j, dict) and 'dts' in j and isinstance(j['dts'], list):
                dts = j['dts']
                if target_class:
                    t = target_class.lower()
                    simple = t.split('.')[-1]
                    matches = 0
                    for item in dts:
                        name = (item.get('name') or '').lower() if isinstance(item, dict) else str(item).lower()
                        if t in name or simple in name:
                            matches += 1
                    if matches:
                        flaky_count = matches
                else:
                    # project level: count all detected flaky entries
                    flaky_count = len(dts)
    except Exception:
        # ignore read errors and fall back to idflakies parsed values
        pass

    pit_path = _safe_get(result.get('pit'), 'path')
    jacoco_path = _safe_get(result.get('jacoco'), 'path')
    id_candidates = _safe_get(result.get('idflakies'), 'candidates')
    id_candidates_str = None
    if id_candidates:
        # join paths with semicolon
        id_candidates_str = ';'.join(id_candidates)

    header = [
        'timestamp',
        'project_root',
        'target_class',
        'line_coverage_pct',
        'mutation_score_pct',
        'flaky_count',
        'total_generated_tests',
        'flaky_rate_pct',
        'pit_path',
        'jacoco_path',
        'idflakies_candidates',
    ]

    import datetime
    ts = datetime.datetime.utcnow().isoformat() + 'Z'

    row = [
        ts,
        project_root,
        target_class or '',
        '' if line_cov is None else line_cov,
        '' if mut_score is None else mut_score,
        '' if flaky_count is None else flaky_count,
        '' if total_tests is None else total_tests,
        '' if flaky_rate is None else flaky_rate,
        '' if pit_path is None else pit_path,
        '' if jacoco_path is None else jacoco_path,
        '' if id_candidates_str is None else id_candidates_str,
    ]

    # ensure directory exists, but never create directories under .dtfixingtools
    d = os.path.dirname(csv_path)
    if d:
        abs_d = os.path.abspath(d)
        # if path is inside project's .dtfixingtools, do NOT create it; skip CSV write instead
        proj = os.path.abspath(project_root or '.')
        dt_path = os.path.join(proj, '.dtfixingtools')
        if abs_d.startswith(os.path.abspath(dt_path) + os.sep):
            # do not create directories under .dtfixingtools; fall back to default csv path
            print(f"CSV path '{csv_path}' is under .dtfixingtools and does not exist; skipping CSV write to avoid creating .dtfixingtools", file=sys.stderr)
            return
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

    write_header = not os.path.exists(csv_path)
    # append new row each run
    with open(csv_path, 'a', newline='', encoding='utf-8') as fh:
        writer = csv.writer(fh)
        if write_header:
            writer.writerow(header)
        writer.writerow(row)


if __name__ == '__main__':
    main()

