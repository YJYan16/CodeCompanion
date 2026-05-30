import os
import sys
import shutil
from pathlib import Path

script_dir = Path(__file__).parent
backend_dir = script_dir / "backend"
output_file = script_dir / "clear_output.txt"

output_lines = []

def log(msg):
    output_lines.append(msg)

log("=" * 60)
log("开始清除批改数据...")
log("=" * 60)

# 1. 清除数据库中的grades表数据
db_path = backend_dir / "app.db"
log(f"[D] 检查数据库文件: {db_path}")
log(f"[D] 数据库文件存在: {db_path.exists()}")

if db_path.exists():
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("DELETE FROM grades")
        conn.commit()
        log("[OK] 已清除 grades 表中的所有数据")

        cursor.execute("DELETE FROM student_drafts")
        conn.commit()
        log("[OK] 已清除 student_drafts 表中的所有数据")

        conn.close()
        log("[OK] 数据库清理完成")

    except Exception as e:
        log(f"[ERROR] 数据库清理失败: {e}")
        import traceback
        traceback.print_exc()
else:
    log(f"[WARN] 数据库文件不存在: {db_path}")

# 2. 清除日志文件
logs_dir = backend_dir / "logs"
log(f"[D] 日志目录: {logs_dir}")
log(f"[D] 日志目录存在: {logs_dir.exists()}")

if logs_dir.exists():
    grade_log = logs_dir / "grade.log"
    if grade_log.exists():
        try:
            with open(grade_log, 'w', encoding='utf-8') as f:
                f.write("")
            log("[OK] 已清空 grade.log 文件")
        except Exception as e:
            log(f"[ERROR] 清空 grade.log 失败: {e}")

    app_log = logs_dir / "app.log"
    if app_log.exists():
        try:
            with open(app_log, 'w', encoding='utf-8') as f:
                f.write("")
            log("[OK] 已清空 app.log 文件")
        except Exception as e:
            log(f"[ERROR] 清空 app.log 失败: {e}")

    log("[OK] 日志清理完成")
else:
    log(f"[WARN] 日志目录不存在: {logs_dir}")

# 3. 清除缓存目录
cache_dirs = [
    backend_dir / "cache",
]

log("\n[X] 清除缓存目录...")
for cache_dir in cache_dirs:
    if cache_dir.exists() and cache_dir.is_dir():
        try:
            shutil.rmtree(cache_dir)
            log(f"[OK] 已删除缓存目录: {cache_dir}")
        except Exception as e:
            log(f"[ERROR] 删除缓存目录失败 {cache_dir}: {e}")

# 4. 清除__pycache__目录
pycache_dirs = list(backend_dir.rglob("__pycache__"))
log(f"\n[X] 清除 {len(pycache_dirs)} 个__pycache__目录...")
for cache_dir in pycache_dirs:
    if cache_dir.is_dir():
        try:
            shutil.rmtree(cache_dir)
            log(f"[OK] 已删除: {cache_dir}")
        except Exception as e:
            log(f"[ERROR] 删除失败 {cache_dir}: {e}")

log("\n" + "=" * 60)
log("完成！所有批改数据清除完成！")
log("=" * 60)

# 写入输出文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(output_lines))

print(f"Output written to: {output_file}")
