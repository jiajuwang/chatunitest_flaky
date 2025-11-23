#!/usr/bin/env bash
# Run test/mutation/flake pipeline for a given class and record outputs
# Usage: tools/run_class_pipeline.sh <ClassName> [extra-linux-path] [--temperature=X] [--phaseType=Y]
# With both parameters
# #tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT

# # With temperature only
# tools/run_class_pipeline.sh DefaultParser --temperature=0.5

# # With phaseType only
# tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --phaseType=SYMPROMPT

# # Without optional parameters (works as before)
# tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <ClassName> [optional-linux-path-to-copy] [--temperature=X] [--phaseType=Y] [--backup-dir=PATH]"
  exit 2
fi

CLASS="$1"
shift
EXTRA_PATH=""
TEMPERATURE=""
PHASE_TYPE=""
BACKUP_BASE=""

# Parse remaining args
for arg in "$@"; do
  case "$arg" in
    --temperature=*)
      TEMPERATURE="${arg#*=}"
      ;;
    --phaseType=*)
      PHASE_TYPE="${arg#*=}"
      ;;
    --backup-dir=*)
      BACKUP_BASE="${arg#*=}"
      ;;
    *)
      # assume it's the extra path if not a flag
      if [ -z "$EXTRA_PATH" ]; then
        EXTRA_PATH="$arg"
      fi
      ;;
  esac
done
ROOT_DIR="$(pwd)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
# Use custom backup dir if specified, otherwise default to $HOME/chatunitest_backups
if [ -z "$BACKUP_BASE" ]; then
  BACKUP_BASE="$HOME/chatunitest_backups"
fi
BACKUP_DIR="$BACKUP_BASE/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "Running pipeline for class: $CLASS"

run_cmd() {
  echo "\n--- RUN: $* ---"
  if ! "$@"; then
    echo "Command failed: $*" >&2
  fi
}

# 1) install project (may compile and run default lifecycle)
run_cmd mvn install

# 2) generate chatunitest class with optional temperature and phaseType
CHAT_OPTS="-DselectClass=$CLASS"
if [ -n "$TEMPERATURE" ]; then
  CHAT_OPTS="$CHAT_OPTS -Dtemperature=$TEMPERATURE"
fi
if [ -n "$PHASE_TYPE" ]; then
  CHAT_OPTS="$CHAT_OPTS -DphaseType=$PHASE_TYPE"
fi
run_cmd mvn chatunitest:class $CHAT_OPTS

# 2) copy chatunitest artifacts
run_cmd mvn chatunitest:copy

# 3) run full tests (clean)
# 4) run full tests (clean)
run_cmd mvn clean test

# 4) detect flaky tests
run_cmd mvn idflakies:detect -Ddt.detector.original_order.all_must_pass=false || true

# 5) run tests and jacoco report (ignore test failures flag as requested)
# 6) run tests and jacoco report (ignore test failures flag as requested)
run_cmd mvn test jacoco:report "-DtestFailureIgnore=true" || true

# 6) run PIT mutation coverage
# 7) run PIT mutation coverage
run_cmd mvn test-compile org.pitest:pitest-maven:mutationCoverage || true

# 7) run the collector script to compute metrics for the target class and append CSV
PYCOLLECTOR="tools/collect_quality_metrics.py"
QUALITY_CSV="tools/quality_summary.csv"
if [ ! -f "$PYCOLLECTOR" ]; then
  echo "Collector script not found at $PYCOLLECTOR" >&2
else
  # Record line count before running collector
  LINE_COUNT_BEFORE=0
  if [ -f "$QUALITY_CSV" ]; then
    LINE_COUNT_BEFORE=$(wc -l < "$QUALITY_CSV")
  fi
  
  run_cmd python3 "$PYCOLLECTOR" --root "$ROOT_DIR" --target-class "$CLASS" --csv "$QUALITY_CSV" || true
  
  # Copy the new entry (last line) to backup base folder (not timestamp subfolder)
  if [ -f "$QUALITY_CSV" ]; then
    LINE_COUNT_AFTER=$(wc -l < "$QUALITY_CSV")
    if [ "$LINE_COUNT_AFTER" -gt "$LINE_COUNT_BEFORE" ]; then
      echo "Appending latest quality metrics entry to backup base folder CSV"
      # CSV goes in backup base folder, shared across all runs
      BACKUP_CSV="$BACKUP_BASE/quality_summary.csv"
      # Copy just the header (first line) if backup CSV doesn't exist
      if [ ! -f "$BACKUP_CSV" ]; then
        head -n 1 "$QUALITY_CSV" > "$BACKUP_CSV" || true
      fi
      # Append the new entry (last line)
      tail -n 1 "$QUALITY_CSV" >> "$BACKUP_CSV" || true
    fi
  fi
fi

echo "Collecting chatunitest-related directories into $BACKUP_DIR"
# find chatunitest-info directories in repo
while IFS= read -r d; do
  dest="$BACKUP_DIR/$(basename "$d")"
  echo "Copying $d -> $dest"
  cp -r "$d" "$dest" || true
done < <(find . -type d -iname '*chatunitest*' -print 2>/dev/null || true)

# If an extra path is supplied, accept Windows/UNC or Linux formats and try to map WSL UNC paths
if [ -n "$EXTRA_PATH" ]; then
  # normalize backslashes to slashes
  wpath="${EXTRA_PATH//\\//}"
  # If it looks like a WSL UNC path (contains wsl.localhost), strip the leading host/distro and use the remainder
  if echo "$wpath" | grep -qi 'wsl.localhost'; then
    # remove everything up to and including the distro name: e.g. //wsl.localhost/Ubuntu-20.04/tmp/... -> /tmp/...
    mapped=$(echo "$wpath" | sed -E 's#.*wsl.localhost/[^/]+##')
    # ensure leading slash
    if [ "${mapped:0:1}" != "/" ]; then
      mapped="/$mapped"
    fi
    EXTRA_PATH_LINUX="$mapped"
  else
    EXTRA_PATH_LINUX="$wpath"
  fi

  if [ -d "$EXTRA_PATH_LINUX" ]; then
    echo "Copying extra path $EXTRA_PATH_LINUX to backup dir"
    cp -r "$EXTRA_PATH_LINUX" "$BACKUP_DIR/" || true
  else
    echo "Extra path '$EXTRA_PATH' (mapped to '$EXTRA_PATH_LINUX') not found or not a directory; skipping" >&2
  fi
fi

# delete .dtfixingtools directory in project root if present
if [ -d "$ROOT_DIR/.dtfixingtools" ]; then
  echo "Removing $ROOT_DIR/.dtfixingtools"
  rm -rf "$ROOT_DIR/.dtfixingtools" || true
fi

echo "Running chatunitest profile install/clean"
# run install with chatunitest profile and then chatunitest:clean
run_cmd mvn -Pchatunitest install || true
run_cmd mvn -Pchatunitest chatunitest:clean || true

echo "Pipeline finished. Backup stored in: $BACKUP_DIR"
