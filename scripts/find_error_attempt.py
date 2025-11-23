#!/usr/bin/env python3
"""Find folders under history*/ that contain an 'attempts4' subfolder.

This script walks each immediate child folder of the given root directory,
looks for subfolders whose name starts with 'history', and within each
history tree searches for directories that contain an 'attempts4' subfolder.

Output is printed to stdout; use --json for structured JSON output.
"""

import os
import argparse
import sys
import json
import csv
#!/usr/bin/env python3
"""Find folders under history*/ that contain an 'attempt4' subfolder.

This script walks each immediate child folder of the given root directory,
looks for subfolders whose name starts with 'history', and within each
history tree searches for directories that contain an 'attempt4' subfolder.

Output is printed to stdout; use --json for structured JSON output.
"""

# usage: python3 scripts/find_error_attempt.py /home/wangjeffrey4/chatunitest_backups -c -o attempts4.csv

import os
import argparse
import sys
import json
import csv
from typing import List, Dict


def find_attempts_in_history(root: str) -> List[Dict[str, str]]:
	"""Search the workspace for method folders that contain an exact 'attempt4' folder.

	The expected structure is:
		ROOT/<timestamp>/<package>/history*/class*/method*/attempt4
	"""

	root = os.path.abspath(root)
	results: List[Dict[str, str]] = []

	if not os.path.isdir(root):
		raise ValueError(f"Root path is not a directory: {root}")

	for entry in sorted(os.listdir(root)):
		entry_path = os.path.join(root, entry)
		if not os.path.isdir(entry_path):
			continue

		# Two cases: history* may be directly under the timestamp folder, or
		# nested under a package folder like 'commons-csv' or 'commons-cli'.
		# First, check direct children for history*
		candidates = []
		for child in sorted(os.listdir(entry_path)):
			child_path = os.path.join(entry_path, child)
			if not os.path.isdir(child_path):
				continue
			if child.startswith('history'):
				candidates.append((child, child_path, None))

		# Also check one level deeper (packages)
		for pkg in sorted(os.listdir(entry_path)):
			pkg_path = os.path.join(entry_path, pkg)
			if not os.path.isdir(pkg_path):
				continue
			for child in sorted(os.listdir(pkg_path)):
				if not child.startswith('history'):
					continue
				hist_path = os.path.join(pkg_path, child)
				if os.path.isdir(hist_path):
					candidates.append((child, hist_path, pkg_path))

		# Now for each history path look for class*/method*/attempt4
		for hist_name, hist_path, pkg_path in candidates:
			# Load class name mapping if available
			class_mapping = {}
			if pkg_path:
				mapping_file = os.path.join(pkg_path, 'classMapping.json')
				if os.path.isfile(mapping_file):
					try:
						with open(mapping_file, 'r') as f:
							class_mapping = json.load(f)
					except Exception:
						pass
			
			try:
				for class_name in sorted(os.listdir(hist_path)):
					if not class_name.startswith('class'):
						continue
					class_path = os.path.join(hist_path, class_name)
					if not os.path.isdir(class_path):
						continue

					# Get actual class name from mapping
					actual_class_name = class_name
					if class_name in class_mapping:
						actual_class_name = class_mapping[class_name].get('className', class_name)

					for method_name in sorted(os.listdir(class_path)):
						if not method_name.startswith('method'):
							continue
						method_path = os.path.join(class_path, method_name)
						if not os.path.isdir(method_path):
							continue

						# look specifically for 'attempt4' only
						attempts4_path = os.path.join(method_path, 'attempt4')
						if os.path.isdir(attempts4_path):
							results.append({
								'top_level': entry,
								'package': os.path.basename(os.path.dirname(hist_path)),
								'history': hist_name,
								'class': class_name,
								'class_name': actual_class_name,
								'method': method_name,
								'attempt_dir': os.path.abspath(attempts4_path),
							})
			except PermissionError:
				continue

	return results


def main() -> None:
	parser = argparse.ArgumentParser(
		description=(
			"Search each immediate child of ROOT for 'history*' folders, "
			"then find directories that contain an 'attempt4' subfolder."
		)
	)
	default_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
	parser.add_argument('root', nargs='?', default=default_root, help=f"Root directory to search (default: {default_root})")
	parser.add_argument('-j', '--json', action='store_true', help='Output JSON')
	parser.add_argument('-c', '--csv', action='store_true', help='Output CSV (single column: path)')
	parser.add_argument('-o', '--out', default=None, help='Write output to file instead of stdout (used with --csv)')
	args = parser.parse_args()
	try:
		results = find_attempts_in_history(args.root)
	except Exception as e:
		print(f"Error: {e}")
		raise

	# CSV output: columns 'path' and 'class_name'
	if args.csv:
		if args.out:
			with open(args.out, 'w', newline='') as f:
				writer = csv.writer(f)
				writer.writerow(['path', 'class_name'])
				for r in results:
					writer.writerow([r['attempt_dir'], r['class_name']])
		else:
			writer = csv.writer(sys.stdout)
			writer.writerow(['path', 'class_name'])
			for r in results:
				writer.writerow([r['attempt_dir'], r['class_name']])
		return

	if args.json:
		print(json.dumps(results, indent=2))
		return

	if not results:
		print("No directories containing matching attempt folders found.")
		return

	for r in results:
		# human readable fallback
		print(f"{r['attempt_dir']}  (top: {r['top_level']}/ package: {r.get('package')} history: {r['history']} class: {r['class']} ({r['class_name']}) method: {r['method']})")


if __name__ == '__main__':
	main()

