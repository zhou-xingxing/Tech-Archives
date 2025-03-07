# 手动创建库
1. 进入你希望创建数据库的位置，然后执行以下命令
```shell
sqlite3 data.db
```
2. 创建表结构
```sql
CREATE TABLE table1 (
current_time number,
cpu_usage REAL,
mem_usage REAL
);
```
# 导入数据
## 手动导入csv

```shell
sqlite3 data.db

# 跳过表头（老版本）
.mode csv
.import '| tail -n +2 <csv>' <table>

# 跳过表头（3.32.2版本后才有）
.import --csv --skip 1 <csv> <table>
```
## Shell脚本导入
```shell
#!/bin/bash

# 数据库文件路径
DB_FILE="data.db"

# 创建表（如果表不存在）
sqlite3 $DB_FILE <<EOF
CREATE TABLE IF NOT EXISTS data (
    timestamp TEXT,
    value REAL
);
EOF

# CSV 文件目录
CSV_DIR="/path/to/csv/files"

# 导入所有 CSV 文件
for csv_file in $CSV_DIR/*.csv; do
    sqlite3 $DB_FILE <<EOF
.mode csv
.import $csv_file data
EOF
done
```
