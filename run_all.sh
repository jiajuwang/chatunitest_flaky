#!/bin/bash
set -e

echo "=== Running all tests (3 rounds) ==="

# for i in {1..3}; do
echo "--- Round $i ---"

# commons-cli tests
cd commons-cli

# temperature=0.2, phaseType=SYMPROMPT
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT

# temperature=0.8, phaseType=SYMPROMPT
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT

# temperature=0.2, phaseType=default
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default

# temperature=0.8, phaseType=default
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default

# temperature=0.2, phaseType=TESTPILOT
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT

# temperature=0.8, phaseType=TESTPILOT
tools/run_class_pipeline.sh CommandLine /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT
tools/run_class_pipeline.sh DefaultParser /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT
tools/run_class_pipeline.sh Option /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT
tools/run_class_pipeline.sh Options /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT
tools/run_class_pipeline.sh org/apache/commons/cli/HelpFormatter /tmp/chatunitest-info/commons-cli --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT

cd ..

# commons-csv tests
cd commons-csv

# CSVRecord - all combinations
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh CSVRecord /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT

# CSVParser - all combinations
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh CSVParser /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT

# CSVFormat - all combinations
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_SYMPROMPT
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=SYMPROMPT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_SYMPROMPT
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.2 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_default
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.8 --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_default
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.2 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.2_TESTPILOT
tools/run_class_pipeline.sh CSVFormat /tmp/chatunitest-info/commons-csv --temperature=0.8 --phaseType=TESTPILOT --backup-dir=/home/wangjeffrey4/CHATUNITEST_backups_0.8_TESTPILOT

cd ..
# done