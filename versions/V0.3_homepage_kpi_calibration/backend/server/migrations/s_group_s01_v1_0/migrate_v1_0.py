"""migrate_v1_0.py - S01 连续安全生产天数 V1.0 增量迁移执行器
========================================================

职责:
  - 按版本号顺序扫描并执行 SQL 迁移文件
  - 计算每个 SQL 文件的 SHA-256 校验和
  - 使用 esg_schema_migration_history 表追踪执行状态
  - 生成唯一 execution_id
  - 校验和冲突时失败（防止已修改文件被误执行）
  - 已成功且校验和一致的版本跳过（幂等）
  - V1_0_000 门禁 GATE_FAIL 时停止后续迁移
  - V1_0_001 在首次执行前自动 bootstrap migration_history 表（如不存在）

用法:
  python -m server.migrations.s_group_s01_v1_0.migrate_v1_0
  或
  cd server && python -m migrations.s_group_s01_v1_0.migrate_v1_0
"""

import hashlib
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pymysql
from pymysql.constants import CLIENT

try:
    from server.mysql_db import MYSQL_CONFIG
except ImportError:
    from mysql_db import MYSQL_CONFIG

MIGRATION_DIR = Path(__file__).resolve().parent

SQL_FILE_PATTERN = re.compile(r'^V(\d+)_(\d+)_(\d+)__(.+)\.sql$', re.IGNORECASE)

SKIP_VERSIONS = {"V1_0_000", "V1_0_001"}
GATE_VERSION = "V1_0_000"
BOOTSTRAP_VERSION = "V1_0_001"


def _parse_version_key(filename: str) -> Optional[Tuple[int, int, int]]:
    m = SQL_FILE_PATTERN.match(filename)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _extract_version_key(filename: str) -> str:
    m = SQL_FILE_PATTERN.match(filename)
    if not m:
        raise ValueError(f"Cannot extract version key from '{filename}'")
    return f"V{m.group(1)}_{m.group(2)}_{m.group(3)}"


def _compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _discover_sql_files(directory: Path) -> List[Path]:
    files = []
    for entry in sorted(directory.iterdir()):
        if not entry.is_file() or entry.suffix.lower() != ".sql":
            continue
        version = _parse_version_key(entry.name)
        if version is None:
            print(f"[WARN] Skipping non-matching file: {entry.name}")
            continue
        files.append((version, entry))
    files.sort(key=lambda x: x[0])
    return [f for _, f in files]


def _generate_execution_id() -> str:
    return f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:12]}"


def _get_connection():
    config = dict(MYSQL_CONFIG)
    config["autocommit"] = False
    config["client_flag"] = int(config.get("client_flag", 0)) | CLIENT.MULTI_STATEMENTS
    return pymysql.connect(**config)


def _close_connection(conn) -> None:
    close = getattr(conn, "close", None)
    if callable(close):
        close()


def _execute_sql_file(conn, file_path: Path) -> None:
    sql_content = file_path.read_text(encoding="utf-8")
    cursor = conn.cursor()
    try:
        cursor.execute(sql_content)
        nextset = getattr(cursor, "nextset", None)
        if callable(nextset):
            while nextset():
                pass
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def _bootstrap_migration_history_if_needed(conn) -> bool:
    """Check if esg_schema_migration_history exists; if not, execute V1_0_001 DDL.
    Returns True if bootstrap was performed."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = DATABASE() "
            "AND table_name = 'esg_schema_migration_history' "
            "AND table_type = 'BASE TABLE'"
        )
        exists = cursor.fetchone() is not None
    finally:
        cursor.close()

    if exists:
        return False

    bootstrap_path = MIGRATION_DIR / f"{BOOTSTRAP_VERSION}__migration_history_bootstrap.sql"
    if not bootstrap_path.is_file():
        raise RuntimeError(
            f"Bootstrap required but {bootstrap_path.name} not found. "
            f"Cannot proceed without migration history table."
        )

    print(f"[BOOTSTRAP] esg_schema_migration_history does not exist. "
          f"Executing {bootstrap_path.name}...")
    _execute_sql_file(conn, bootstrap_path)
    print("[BOOTSTRAP] migration history table created.")
    return True


def _extract_gate_result(conn, gate_path: Path) -> Optional[str]:
    """Execute the gate SQL and extract the gate_result.
    Returns 'GATE_PASS' or 'GATE_FAIL (...)' or None if extraction fails."""
    sql_content = gate_path.read_text(encoding="utf-8")
    cursor = conn.cursor()
    try:
        cursor.execute(sql_content)
        nextset = getattr(cursor, "nextset", None)
        if callable(nextset):
            while nextset():
                pass
        conn.commit()
        cursor.execute("SELECT @gate_failures")
        row = cursor.fetchone()
        failures = next(iter(row.values())) if isinstance(row, dict) else row[0]
        conn.rollback()
        if failures == 0:
            return "GATE_PASS"
        return f"GATE_FAIL ({failures} issue(s))"
    except Exception as e:
        conn.rollback()
        return None
    finally:
        cursor.close()


def _record_migration(conn, version_key, description, file_name,
                      checksum, execution_id, status, error_message=None,
                      executed_by=None) -> None:
    sql = """INSERT INTO esg_schema_migration_history
        (version_key, description, file_name, checksum_sha256,
         execution_id, executed_at, finished_at, status,
         error_message, executed_by)
    VALUES (%s, %s, %s, %s, %s, NOW(6), NOW(6), %s, %s, %s)"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (version_key, description, file_name,
                            checksum, execution_id, status,
                            error_message, executed_by))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def _get_last_successful_checksum(conn, version_key: str) -> Optional[str]:
    sql = """SELECT checksum_sha256
    FROM esg_schema_migration_history
    WHERE version_key = %s AND status = 'SUCCESS'
    ORDER BY executed_at DESC LIMIT 1"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (version_key,))
        row = cursor.fetchone()
        if not row:
            return None
        return row.get("checksum_sha256") if isinstance(row, dict) else row[0]
    finally:
        cursor.close()


def run_migration(migration_dir: Optional[Path] = None, dry_run: bool = False,
                  executed_by: Optional[str] = None) -> int:
    if migration_dir is None:
        migration_dir = MIGRATION_DIR

    sql_files = _discover_sql_files(migration_dir)
    if not sql_files:
        print("[INFO] No migration SQL files found.")
        return 0

    print(f"[INFO] Found {len(sql_files)} migration files:")
    for f in sql_files:
        print(f"  - {f.name}")

    execution_id = _generate_execution_id()
    print(f"[INFO] Execution ID: {execution_id}")

    conn = _get_connection()
    if conn is None:
        print("[INFO] No database connection configured. Dry-run mode.")
        for f in sql_files:
            print(f"  [DRY-RUN] {f.name}")
        return 0

    # --- Bootstrap phase ---
    _bootstrap_migration_history_if_needed(conn)

    # --- Gate phase ---
    gate_path = migration_dir / f"{GATE_VERSION}__environment_gate.sql"
    if gate_path.is_file():
        print(f"[GATE] Running environment gate: {gate_path.name}")
        gate_result = _extract_gate_result(conn, gate_path)
        if gate_result is None:
            print("[GATE] ERROR: Failed to execute gate SQL.")
            _close_connection(conn)
            return 1
        if not gate_result.startswith("GATE_PASS"):
            print(f"[GATE] BLOCKED: {gate_result}")
            print("[GATE] Migration stopped. Fix the issues above and retry.")
            _record_migration(
                conn, GATE_VERSION, "environment gate",
                gate_path.name, _compute_sha256(gate_path),
                execution_id, "GATE_BLOCKED",
                error_message=gate_result, executed_by=executed_by,
            )
            _close_connection(conn)
            return 1
        print("[GATE] PASSED. Proceeding with migration.")
        _record_migration(
            conn, GATE_VERSION, "environment gate",
            gate_path.name, _compute_sha256(gate_path),
            execution_id, "SUCCESS", executed_by=executed_by,
        )

    # --- Migration phase ---
    has_error = False
    for file_path in sql_files:
        version_key = _extract_version_key(file_path.name)
        if version_key in SKIP_VERSIONS:
            continue

        checksum = _compute_sha256(file_path)
        description = file_path.stem.split("__", 1)[1].replace("_", " ")
        print(f"[PROC] {file_path.name} (sha256={checksum[:16]}...)")

        last_checksum = _get_last_successful_checksum(conn, version_key)
        if last_checksum is not None:
            if last_checksum == checksum:
                print(f"  [SKIP] {version_key} already succeeded with same checksum.")
                continue
            else:
                msg = (f"Checksum conflict: {version_key} last={last_checksum[:16]}... "
                       f"current={checksum[:16]}...")
                print(f"  [FAIL] {msg}")
                _record_migration(conn, version_key, description, file_path.name,
                                  checksum, execution_id, "FAILED",
                                  error_message=msg, executed_by=executed_by)
                has_error = True
                break

        if dry_run:
            print(f"  [DRY-RUN] Would execute {file_path.name}")
            continue

        try:
            _execute_sql_file(conn, file_path)
            _record_migration(conn, version_key, description, file_path.name,
                              checksum, execution_id, "SUCCESS", executed_by=executed_by)
            print(f"  [OK] {file_path.name}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"  [FAIL] {file_path.name}: {error_msg}")
            try:
                _record_migration(conn, version_key, description, file_path.name,
                                  checksum, execution_id, "FAILED",
                                  error_message=error_msg, executed_by=executed_by)
            except Exception:
                pass
            has_error = True
            break

    print(f"{'='*60}")
    if has_error:
        print("[RESULT] Migration completed with errors.")
        _close_connection(conn)
        return 1
    print("[RESULT] All migrations successful.")
    _close_connection(conn)
    return 0


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    print("=" * 60)
    print("S组 S01 V1.0 Incremental Migration Executor")
    print(f"Directory: {MIGRATION_DIR}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print(f"Mode: {'DRY-RUN' if dry_run else 'LIVE'}")
    print("=" * 60)
    sys.exit(run_migration(dry_run=dry_run))


if __name__ == "__main__":
    main()
