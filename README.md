# Runtime Configuration:

Apache Maven 3.6.3
Maven home: /usr/share/maven
Java version: 1.8.0_452, vendor: Private Build, runtime: /usr/lib/jvm/java-8-openjdk-amd64/jre
Default locale: en, platform encoding: UTF-8
OS name: "linux", version: "6.6.87.2-microsoft-standard-wsl2", arch: "amd64", family: "unix"

# Running Instruction:

1. Copy run_all.sh in ~ folder (cp run_all.sh /home/shanto/)
2. cd "/home/shanto/"
3. clone project repo (e.g., git clone https://github.com/apache/commons-csv)
4. Copy tools/ directory in each project's folder (e.g., cp -r tools/ ~/commons-csv/)
5. Need to modify pom.xml (Shanto will automate this process later), [do not introduce anything unlicensed files or dir]
6. Run run_all.sh script to create folders for generated tests and history log in ~ () 

5. These folders will be named with timestamp
6. Put scripts/ in timestamp folders
7. Inside the timestamp folders, run python3 scripts/annotate_csv_counts.py to generate a summary CSV (need to copy the existing CSV inside the timestamp folder first)
8. The result csv's name is quality_summary - Copy.with_counts.csv
