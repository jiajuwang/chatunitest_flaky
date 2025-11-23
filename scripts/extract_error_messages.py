#!/usr/bin/env python3
"""
Extract and group error messages from records.json files listed in a CSV,
WITHOUT recursion (iterative stack-based traversal).

Features:
- Reads a CSV with a 'path' column; for each row, expects <path>/records.json
- Groups errors by (attempt, round)
- Prints PATH header, then attempt/round blocks with errorType + message lines
- Avoids duplicate extraction by:
  * tracking visited containers (dict/list) with a `seen` set
  * skipping descent into an 'errorMsg' child when we already extracted from it

Usage:
  python extract_grouped_errors_iter.py paths.csv -o grouped_errors.txt
  # CSV example:
  # path
  # runs/run1
  # runs/run2
  # python3 scripts/extract_error_messages.py attempts4.csv -o extracted_errors.txt
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple, Set

AttemptRound = Tuple[Optional[int], Optional[int]]
ErrorEntry = Tuple[str, str]  # (errorType, message)


def _iter_strings(x: Any) -> Iterable[str]:
    """Yield strings from x if it's a string or a list of strings."""
    if isinstance(x, str):
        yield x
    elif isinstance(x, list):
        for it in x:
            if isinstance(it, str):
                yield it


def collect_errors_iterative(
    root: Any,
    sink: Dict[AttemptRound, List[ErrorEntry]],
) -> None:
    """
    Iteratively traverse `root`, grouping (errorType, message) into `sink`
    under the nearest (attempt, round) context.
    """
    # Stack holds: (node, attempt, round)
    stack: List[Tuple[Any, Optional[int], Optional[int]]] = [(root, None, None)]
    seen: Set[int] = set()

    while stack:
        node, att, rnd = stack.pop()

        oid = id(node)
        if oid in seen:
            continue
        seen.add(oid)

        if isinstance(node, dict):
            # Update context when present on this node
            if isinstance(node.get("attempt"), int):
                att = node["attempt"]
            if "round" in node and (isinstance(node["round"], int) or node["round"] is None):
                rnd = node["round"]

            # Prefer explicit errorMsg container if present
            extracted_from_errmsg_child = False
            errmsg_child = node.get("errorMsg")
            if isinstance(errmsg_child, dict):
                etype = errmsg_child.get("errorType")
                msgs = errmsg_child.get("errorMessage")
                if isinstance(etype, str) and msgs is not None:
                    for s in _iter_strings(msgs):
                        sink[(att, rnd)].append((etype, s))
                    extracted_from_errmsg_child = True

            # Fallback: direct errorType/errorMessage on this dict (only if we didn't use errorMsg)
            if not extracted_from_errmsg_child:
                etype = node.get("errorType")
                msgs = node.get("errorMessage")
                if isinstance(etype, str) and msgs is not None:
                    for s in _iter_strings(msgs):
                        sink[(att, rnd)].append((etype, s))

            # Push children, but skip errorMsg child if already extracted from it
            for k, v in node.items():
                if extracted_from_errmsg_child and k == "errorMsg":
                    continue
                stack.append((v, att, rnd))

        elif isinstance(node, list):
            # Push list items with current context
            for item in node:
                stack.append((item, att, rnd))
        # Scalars are ignored


def extract_grouped_errors(records_path: str) -> Dict[AttemptRound, List[ErrorEntry]]:
    """
    Return:
      {(attempt, round): [(errorType, message), ...], ...}
    for a single records.json file.
    """
    grouped: Dict[AttemptRound, List[ErrorEntry]] = defaultdict(list)
    if not os.path.isfile(records_path):
        return grouped
    try:
        with open(records_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Warning: failed to load {records_path}: {e}", file=sys.stderr)
        return grouped

    collect_errors_iterative(data, grouped)
    return grouped


def _sort_key(k: AttemptRound):
    """Sort (attempt, round) with None values last."""
    a, r = k
    big = 10**9
    return (
        1 if a is None else 0, a if a is not None else big,
        1 if r is None else 0, r if r is not None else big
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extract grouped error messages by attempt/round from records.json paths in a CSV (iterative traversal)"
    )
    ap.add_argument("csv", help='CSV with a header column "path"')
    ap.add_argument("-o", "--out", default="error_messages.txt", help="Output txt file (default: error_messages.txt)")
    ap.add_argument("--no-blank", dest="blank", action="store_false", help="Do not insert blank lines between path groups")
    args = ap.parse_args()

    if not os.path.isfile(args.csv):
        print(f"CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(2)

    paths: List[str] = []
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "path" not in reader.fieldnames:
            print(f"CSV missing 'path' header: {args.csv}", file=sys.stderr)
            sys.exit(2)
        for row in reader:
            p = (row.get("path") or "").strip()
            if p:
                paths.append(p)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    total_msgs = 0
    with open(args.out, "w", encoding="utf-8") as out_f:
        for idx, base in enumerate(paths):
            records_json = os.path.join(base, "records.json")
            grouped = extract_grouped_errors(records_json)

            # Header per file path
            out_f.write(f"PATH: {records_json}\n")

            # Write sorted attempt/round groups
            for ar, entries in sorted(grouped.items(), key=_sort_key):
                attempt, round_ = ar
                out_f.write(f"attempt={attempt} round={round_}\n")
                for etype, msg in entries:
                    out_f.write(f"errorType={etype}\n")
                    msg_clean = str(msg).replace("\r", "")
                    out_f.write(f"message={msg_clean}\n\n")
                    total_msgs += 1

            if args.blank and idx != len(paths) - 1:
                out_f.write("\n")

    print(f"Wrote {total_msgs} error messages (grouped by attempt/round) to {args.out}")


if __name__ == "__main__":
    main()
