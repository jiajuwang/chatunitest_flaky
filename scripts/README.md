# scripts/

This folder contains small helper scripts used to analyze and extract information
from run folders and CSV summaries in this workspace.

Requirements
- Python 3.8+ (scripts were written for CPython 3.8 and above)
- No additional third-party packages required (standard library only)

Scripts

- `annotate_csv_counts.py`
  - Purpose: Annotate `quality_summary - Copy.csv` with additional count columns:
    - `num_test_methods` — number of `@Test` occurrences under `chatunitest-tests`
    - `num_chatgpt_prompts` — number of prompt records in `records.json` history files
    - `num_test_files` — number of `.java` test files under `chatunitest-tests`
    - `num_class_methods` — number of methods for a target class (when available)
  - Behavior: Run from the workspace root. It reads `quality_summary - Copy.csv` and
    writes `quality_summary - Copy.with_counts.csv` next to it.
  - Usage example (from repo root):

    ```bash
    python3 scripts/annotate_csv_counts.py
    ```

  - Notes: The script attempts to map CSV rows to run folders either by lexical
    sort of run directories (folders with names like `YYYYMMDDTHHMMSSZ`) or by
    matching timestamps in the CSV to folder names. It strips Java comments
    before counting `@Test` annotations to avoid counting tests inside comments.

- `extract_error_messages.py`
  - Purpose: Extract and group error messages from `records.json` files listed
    in a CSV (non-recursive traversal). Groups entries by `(attempt, round)`.
  - Expected input CSV: a CSV with a header column named `path` where each row
    gives a directory path that contains `records.json` (i.e., `<path>/records.json`).
  - Usage example:

    ```bash
    # write grouped errors to grouped_errors.txt
    python3 scripts/extract_error_messages.py paths.csv -o grouped_errors.txt
    ```

  - Output: A text file with blocks per `records.json` file; each block contains
    `attempt=... round=...` groups followed by `errorType=...` and `message=...` lines.

- `find_error_attempt.py`
  - Purpose: Search a workspace for history folders that contain an `attempt4`
    subfolder (useful to locate runs with specific attempt directories).
  - Behavior: Walks immediate children of the given root and looks for
    `history*` directories either directly under each timestamp folder or
    nested under a package folder. When it finds `method*/attempt4`, it
    reports the `attempt4` path.
  - Usage examples:

    ```bash
    # Default: search the repository parent folder (scripts/..)
    python3 scripts/find_error_attempt.py

    # Search a specific root and print CSV (single column 'path') to a file
    python3 scripts/find_error_attempt.py /path/to/root -c -o attempts4.csv

    # JSON output
    python3 scripts/find_error_attempt.py /path/to/root -j
    ```

Tips
- Run `python3 -m pip install --user --upgrade pip` if you need to install packages,
  but these scripts only use the Python standard library.
- Many scripts expect to be run from the repository root (see each script's
  docstring). If you run them from elsewhere, provide absolute paths or cd to
  the repo root first.

Contributing
- If you add new helper scripts to `scripts/`, please update this README with
  a short description and usage examples.

License
- These helper scripts follow the repository's license (if present). If you
  copy them elsewhere, keep the attribution and any license headers.
