# Quality metrics collector (tools/collect_quality_metrics.py)

This small helper parses local test/report artifacts produced by Maven plugins and writes a concise summary.

Supported reports (auto-detected under the project `target/` by default):

- PIT mutation testing: `target/pit-reports/mutations.xml`
- JaCoCo coverage: `target/site/jacoco/jacoco.csv` (preferred) or `target/site/jacoco/jacoco.xml`
- Idflakies: best-effort search for idflakies/flaky reports under `target/` (JSON, XML or plain text)

What the script produces
- JSON summary printed to stdout (or written with `--output`) containing the parsed metrics.
- Optional CSV one-line summary when `--csv` is provided. The CSV contains the following columns:
  - project_root
  - line_coverage_pct
  - mutation_score_pct
  - flaky_count
  - total_generated_tests
  - flaky_rate_pct
  - pit_path
  - jacoco_path
  - idflakies_candidates

By default the script will print the JSON summary. Use `--csv /path/to/file.csv` to append/write a one-line CSV.

Usage

Run from the repository root (or pass `--root`):

```bash
python3 tools/collect_quality_metrics.py --root /path/to/repo
```

Write a JSON summary to file:

```bash
python3 tools/collect_quality_metrics.py --root /path/to/repo --output /tmp/summary.json
```

Write a one-line CSV summary (will create directories if needed):

```bash
python3 tools/collect_quality_metrics.py --root /path/to/repo --csv tools/quality_summary.csv
```

Notes about CSV behavior
- If the CSV file already exists it will be overwritten by the current script (one-line csv). If you prefer appending historical rows, run the script and then append the recorded values yourself or use the CSV file produced in a tool that supports appending.

Per-class metrics
- The script currently computes project-level metrics by aggregating JaCoCo CSV and PIT `mutations.xml` counters.
- For class-level metrics (single-class mutation score / coverage) you can:
  - supply a class-specific JaCoCo CSV that only contains the class rows and pass it via `--jacoco /path/to/jacoco.csv`, and
  - supply a PIT `mutations.xml` filtered to the class (or pass the full PIT XML and post-filter by `sourceFile` in a simple script).

Planned improvements
- Append mode for `tools/quality_summary.csv` (keep historical rows) — can be added on request.
- Built-in `--class` filter to compute class-scoped metrics automatically. If you'd like this, tell me the exact class name format you want (e.g. `org.apache.commons.cli.DefaultParser`) and I'll add the option.

Contact / changes
- The script is in `tools/collect_quality_metrics.py`. If you want the README extended (append examples, change CSV format, or add class-level filtering) I can update both the script and this README.

Example quick run (from repo root):

```bash
python3 tools/collect_quality_metrics.py --csv tools/quality_summary.csv
```

Examples
--------

1) Whole-project summary

From the repository root this collects all available reports (PIT + JaCoCo) and writes a one-line CSV into `tools/quality_summary.csv`:

```bash
python3 tools/collect_quality_metrics.py --root . --csv tools/quality_summary.csv
```

This will auto-detect `target/pit-reports/mutations.xml` and `target/site/jacoco/jacoco.csv` and include their metrics.

2) Class-scoped example — DefaultParser

If you want metrics for a single class (for example `org.apache.commons.cli.DefaultParser`) you can filter the existing reports down to the rows/elements that reference that class, then pass the filtered files to the script with `--pit` and `--jacoco`.

Below are two ways to produce filtered inputs for `DefaultParser`.

a) Using `xmlstarlet` (recommended if available)

```bash
# create a jacoco CSV containing only the header + DefaultParser rows
head -n 1 target/site/jacoco/jacoco.csv > tools/jacoco_DefaultParser.csv
grep "DefaultParser" target/site/jacoco/jacoco.csv >> tools/jacoco_DefaultParser.csv

# extract PIT mutations that mention DefaultParser and wrap in a top-level <mutations> element
xmlstarlet sel -t -c "/mutations/mutation[contains(mutatedClass,'DefaultParser')]" target/pit-reports/mutations.xml \
  | sed '1s/^/<mutations>\n/;$a</mutations>' > tools/pit_DefaultParser.xml

# run the collector against the filtered files
python3 tools/collect_quality_metrics.py --pit tools/pit_DefaultParser.xml \
  --jacoco tools/jacoco_DefaultParser.csv --csv tools/quality_summary.csv
```

b) Using a small Python filter (no external XML tools required)

```bash
# filter jacoco CSV (header + rows containing the class name)
python3 -c "import csv,sys
with open('target/site/jacoco/jacoco.csv') as r, open('tools/jacoco_DefaultParser.csv','w') as w:
    hdr = r.readline(); w.write(hdr)
    w.writelines(l for l in r if 'DefaultParser' in l)
"

# filter PIT mutations.xml for DefaultParser (produces tools/pit_DefaultParser.xml)
python3 - <<'PY'
import xml.etree.ElementTree as ET
tree = ET.parse('target/pit-reports/mutations.xml')
root = ET.Element('mutations')
for m in ET.parse('target/pit-reports/mutations.xml').getroot().findall('mutation'):
    mc = m.find('mutatedClass')
    if mc is not None and 'DefaultParser' in (mc.text or ''):
        root.append(m)
ET.ElementTree(root).write('tools/pit_DefaultParser.xml', encoding='utf-8', xml_declaration=True)
PY

# run the collector
python3 tools/collect_quality_metrics.py --pit tools/pit_DefaultParser.xml \
  --jacoco tools/jacoco_DefaultParser.csv --csv tools/quality_summary.csv
```

Notes
- Filtering is best-effort: ensure the filtered PIT XML is a valid XML file with a root `<mutations>` element (the examples above create that wrapper).
- If you run the class-scoped commands multiple times they will overwrite the `tools/jacoco_DefaultParser.csv` and `tools/pit_DefaultParser.xml` files — adjust paths if you want to preserve them.

If you'd like I can add a `--class` argument to `collect_quality_metrics.py` that performs these filtering steps automatically (you'd pass `--class org.apache.commons.cli.DefaultParser`) and the script would write/append a history row to `tools/quality_summary.csv` with a timestamp. Say the word and I'll implement it.

Automated pipeline script
------------------------

There's a helper script `tools/run_class_pipeline.sh` which executes the sequence of Maven commands you requested for a given class, runs the metrics collector, and copies `chatunitest` artifacts into a timestamped folder under your home directory.

Usage:

```bash
# make it executable once
chmod +x tools/run_class_pipeline.sh

# run pipeline for class Example and optionally provide the extra Linux path to copy
# The extra path should be a Linux-style path (for example: /tmp/chatunitest-info/commons-cli/history2025_10_23_22_12_27)
tools/run_class_pipeline.sh Example /tmp/chatunitest-info/commons-cli/history2025_10_23_22_12_27
```

What the script does
- Runs these commands (in repo root):
  - mvn chatunitest:class -DselectClass=<Class>
  - mvn chatunitest:copy
  - mvn clean test
  - mvn idflakies:detect -Ddt.detector.original_order.all_must_pass=false
  - mvn test jacoco:report "-DtestFailureIgnore=true"
  - mvn test-compile org.pitest:pitest-maven:mutationCoverage
  - python3 tools/collect_quality_metrics.py --root . --target-class <Class> --csv tools/quality_summary.csv

- Copies any directories matching `*chatunitest*` under the project into a timestamped folder under `$HOME/chatunitest_backups/<timestamp>`.
- If you provide an extra path (please use a Linux-style path like `/tmp/chatunitest-info/...`) the script will attempt to copy it as well.

Notes
- The script prints progress and continues on non-fatal errors (it doesn't abort the whole backup on a single failed copy).
- You can change the CSV path by editing the command in the script or passing a different `--csv` to the collector invocation inside the script.
