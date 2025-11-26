cp -r scripts/ /home/shanto/CHATUNITEST_backups_0.2_default
cd /home/shanto/CHATUNITEST_backups_0.2_default
cp "quality_summary.csv" "quality_summary - Copy.csv"
python3 scripts/annotate_csv_counts.py
