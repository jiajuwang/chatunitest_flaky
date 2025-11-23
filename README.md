# Runtime Configuration:

Apache Maven 3.6.3
Maven home: /usr/share/maven
Java version: 1.8.0_452, vendor: Private Build, runtime: /usr/lib/jvm/java-8-openjdk-amd64/jre
Default locale: en, platform encoding: UTF-8
OS name: "linux", version: "6.6.87.2-microsoft-standard-wsl2", arch: "amd64", family: "unix"

# Running Instruction:

1. Put run_all.sh in ~ folder
2. Put all tested projects in ~ folder
3. Put tools/ in each project's folder
4. Run run_all.sh script will create folders for generated tests and generation history in ~
5. These folders will be named with timestamp
6. Put scripts/ in timestamp folders
7. Inside the timestamp folders, run python3 scripts/annotate_csv_counts.py to generate a summary CSV (need to copy the existing CSV inside the timestamp folder first)
8. The result csv's name is quality_summary - Copy.with_counts.csv
