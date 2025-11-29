#Command: bash parsing_result_for_chatunit_test.sh "CHATUNITEST_backups_0.2_SYMPROMPT"
#$1="CHATUNITEST_backups_0.2_default"
if [[ $1 == "" ]]; then
  echo "give arg (e.g., CHATUNITEST_backups_0.2_default)"
  exit
fi
cp -r scripts/ /home/shanto/$1
#CHATUNITEST_backups_0.2_default
cd /home/shanto/$1
#CHATUNITEST_backups_0.2_default
cp "quality_summary.csv" "quality_summary - Copy.csv"
python3 scripts/annotate_csv_counts.py
