import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import mysql.connector
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'backups/elearning_db_pre_phase7_{ts}.sql'
os.makedirs('backups', exist_ok=True)

conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
cur = conn.cursor()

tables = ['users', 'courses', 'learners', 'enrollments', 'activities']
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(f'-- Database Backup for elearning_db before Phase 7\n-- Generated: {datetime.now().isoformat()}\n\n')
    for tbl in tables:
        cur.execute(f'SHOW CREATE TABLE `{tbl}`')
        create_stmt = cur.fetchone()[1]
        f.write(f'{create_stmt};\n\n')
        cur.execute(f'SELECT * FROM `{tbl}`')
        rows = cur.fetchall()
        if rows:
            col_names = [desc[0] for desc in cur.description]
            cols_str = ', '.join([f'`{c}`' for c in col_names])
            f.write(f'INSERT INTO `{tbl}` ({cols_str}) VALUES\n')
            val_strs = []
            for r in rows:
                formatted_vals = []
                for v in r:
                    if v is None:
                        formatted_vals.append('NULL')
                    elif isinstance(v, (int, float)):
                        formatted_vals.append(str(v))
                    else:
                        val_escaped = str(v).replace('\\', '\\\\').replace("'", "\\'")
                        formatted_vals.append(f"'{val_escaped}'")
                inner = ', '.join(formatted_vals)
                val_strs.append(f"({inner})")
            f.write(',\n'.join(val_strs) + ';\n\n')

print(f'Backup created successfully: {backup_file} ({os.path.getsize(backup_file)} bytes)')
cur.close()
conn.close()
