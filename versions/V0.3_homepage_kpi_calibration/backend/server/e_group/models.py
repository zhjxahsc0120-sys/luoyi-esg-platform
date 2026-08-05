"""
E组公共闭环 & E01 V1.1 表描述元数据模块

采用"表描述元数据"模式，为全部 28 张表提供字段名、类型、约束的
Python 描述，供服务层代码生成和测试使用。不引入 SQLAlchemy 或其他 ORM。

每个表使用 TableDef 数据类描述，包含 ColumnDef、IndexDef、CheckDef。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# 元数据数据类
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnDef:
    """数据库列描述。"""

    name: str
    python_type: type  # int, str, float, Decimal, datetime, bool
    db_type: str  # 'BIGINT', 'VARCHAR(80)', 'DATETIME(6)', etc.
    nullable: bool
    default: Optional[str] = None  # SQL default expression
    is_pk: bool = False
    is_unique: bool = False
    is_fk: bool = False
    fk_ref: Optional[str] = None  # 'table(column)'


@dataclass(frozen=True)
class IndexDef:
    """数据库索引描述。"""

    name: str
    columns: tuple[str, ...]
    unique: bool = False


@dataclass(frozen=True)
class CheckDef:
    """CHECK 约束描述。"""

    name: str
    expression: str  # SQL CHECK expression


@dataclass(frozen=True)
class TableDef:
    """数据库表描述。"""

    table_name: str
    columns: tuple[ColumnDef, ...]
    indexes: tuple[IndexDef, ...] = ()
    checks: tuple[CheckDef, ...] = ()


# ===========================================================================
# 公共快捷方式
# ===========================================================================

def _pk(name: str, db_type: str = "BIGINT") -> ColumnDef:
    return ColumnDef(
        name=name,
        python_type=int,
        db_type=db_type,
        nullable=False,
        default=None,
        is_pk=True,
    )


def _col(
    name: str,
    python_type: type,
    db_type: str,
    nullable: bool = True,
    default: Optional[str] = None,
    is_unique: bool = False,
    is_fk: bool = False,
    fk_ref: Optional[str] = None,
) -> ColumnDef:
    return ColumnDef(
        name=name,
        python_type=python_type,
        db_type=db_type,
        nullable=nullable,
        default=default,
        is_unique=is_unique,
        is_fk=is_fk,
        fk_ref=fk_ref,
    )


# ===========================================================================
# 表定义：共 28 张表
# ===========================================================================


# ---------------------------------------------------------------------------
# 1. esg_schema_migration_history — 迁移历史记录表
# ---------------------------------------------------------------------------
T_ESG_SCHEMA_MIGRATION_HISTORY = TableDef(
    table_name="esg_schema_migration_history",
    columns=(
        _pk("id"),
        _col("version_key", str, "VARCHAR(64)", nullable=False),
        _col("description", str, "VARCHAR(255)", nullable=False),
        _col("file_name", str, "VARCHAR(255)", nullable=False),
        _col("checksum_sha256", str, "CHAR(64)", nullable=False),
        _col("execution_id", str, "VARCHAR(64)", nullable=False),
        _col("executed_at", datetime, "DATETIME(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("finished_at", datetime, "DATETIME(6)", nullable=True),
        _col("status", str, "VARCHAR(30)", nullable=False),
        _col("error_message", str, "TEXT", nullable=True),
        _col("executed_by", str, "VARCHAR(128)", nullable=True),
    ),
    indexes=(
        IndexDef("uk_migration_version_execution", ("version_key", "execution_id"), unique=True),
        IndexDef("idx_migration_version_status", ("version_key", "status"), unique=False),
    ),
)

# ---------------------------------------------------------------------------
# 2. e01_monitor_point — 监测点位
# ---------------------------------------------------------------------------
T_E01_MONITOR_POINT = TableDef(
    table_name="e01_monitor_point",
    columns=(
        _pk("id"),
        _col("point_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("point_name", str, "VARCHAR(160)", nullable=False),
        _col("source_point_name", str, "VARCHAR(255)", nullable=True),
        _col("chainage", str, "VARCHAR(60)", nullable=True),
        _col("segment_code", str, "VARCHAR(80)", nullable=True),
        _col("segment_name", str, "VARCHAR(160)", nullable=True),
        _col("engineering_object_type", str, "VARCHAR(80)", nullable=True),
        _col("engineering_object_id", str, "VARCHAR(100)", nullable=True),
        _col("engineering_object_name", str, "VARCHAR(255)", nullable=True),
        _col("longitude", Decimal, "DECIMAL(11,8)", nullable=True),
        _col("latitude", Decimal, "DECIMAL(10,8)", nullable=True),
        _col("coordinate_system", str, "VARCHAR(40)", nullable=True),
        _col("coordinate_source_type", str, "VARCHAR(30)", nullable=False, default="'NONE'"),
        _col("coordinate_source_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("coordinate_verification_status", str, "VARCHAR(30)", nullable=False, default="'NOT_PROVIDED'"),
        _col("coordinate_verified_at", datetime, "DATETIME(6)", nullable=True),
        _col("coordinate_verified_by", int, "BIGINT", nullable=True),
        _col("coordinate_accuracy", Decimal, "DECIMAL(10,3)", nullable=True),
        _col("gis_feature_id", str, "VARCHAR(96)", nullable=True,
             is_fk=True, fk_ref="gis_feature(id)"),
        _col("effective_from", datetime, "DATETIME(6)", nullable=True),
        _col("effective_to", datetime, "DATETIME(6)", nullable=True),
        _col("active_status", str, "VARCHAR(20)", nullable=False, default="'ACTIVE'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_point_code", ("point_code",), unique=True),
        IndexDef("idx_e01_point_gis", ("gis_feature_id",), unique=False),
    ),
    checks=(
        CheckDef("ck_e01_point_longitude", "longitude IS NULL OR longitude BETWEEN -180 AND 180"),
        CheckDef("ck_e01_point_latitude", "latitude IS NULL OR latitude BETWEEN -90 AND 90"),
        CheckDef("ck_e01_point_coordinate_pair",
                 "(longitude IS NULL AND latitude IS NULL) OR (longitude IS NOT NULL AND latitude IS NOT NULL)"),
        CheckDef("ck_e01_point_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_point_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 3. e01_monitor_plan — 监测计划
# ---------------------------------------------------------------------------
T_E01_MONITOR_PLAN = TableDef(
    table_name="e01_monitor_plan",
    columns=(
        _pk("id"),
        _col("plan_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("plan_year", int, "SMALLINT", nullable=False),
        _col("quarter_code", str, "CHAR(7)", nullable=False),
        _col("frequency_code", str, "VARCHAR(30)", nullable=False, default="'QUARTERLY'"),
        _col("testing_provider_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("testing_provider_name", str, "VARCHAR(160)", nullable=False),
        _col("owner_department_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("owner_department_name", str, "VARCHAR(160)", nullable=False),
        _col("plan_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("version_no", str, "VARCHAR(30)", nullable=False),
        _col("plan_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_plan_code", ("plan_code",), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_plan_quarter", "quarter_code REGEXP '^[0-9]{4}-Q[1-4]$'"),
        CheckDef("ck_e01_plan_year_quarter", "CAST(LEFT(quarter_code,4) AS UNSIGNED)=plan_year"),
        CheckDef("ck_e01_plan_frequency",
                 "frequency_code IN ('CONTINUOUS','DAILY','WEEKLY','MONTHLY','QUARTERLY','EVENT_TRIGGERED')"),
        CheckDef("ck_e01_plan_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_plan_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 4. e01_monitor_plan_item — 监测计划条目
# ---------------------------------------------------------------------------
T_E01_MONITOR_PLAN_ITEM = TableDef(
    table_name="e01_monitor_plan_item",
    columns=(
        _pk("id"),
        _col("plan_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_plan(id)"),
        _col("point_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_point(id)"),
        _col("monitor_category", str, "VARCHAR(20)", nullable=False),
        _col("planned_sample_at", datetime, "DATETIME(6)", nullable=True),
        _col("planned_factor_scope", str, "VARCHAR(1000)", nullable=True),
        _col("execution_status", str, "VARCHAR(30)", nullable=False, default="'PENDING'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_plan_item", ("plan_id", "point_id", "monitor_category"), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_plan_item_category", "monitor_category IN ('WATER','AIR','NOISE')"),
        CheckDef("ck_e01_plan_item_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_plan_item_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 5. e01_monitor_batch — 监测批次
# ---------------------------------------------------------------------------
T_E01_MONITOR_BATCH = TableDef(
    table_name="e01_monitor_batch",
    columns=(
        _pk("id"),
        _col("batch_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("plan_id", int, "BIGINT", nullable=True, is_fk=True, fk_ref="e01_monitor_plan(id)"),
        _col("quarter_code", str, "CHAR(7)", nullable=False),
        _col("report_no", str, "VARCHAR(120)", nullable=True),
        _col("testing_provider_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("testing_provider_name", str, "VARCHAR(160)", nullable=False),
        _col("sample_start_at", datetime, "DATETIME(6)", nullable=False),
        _col("sample_end_at", datetime, "DATETIME(6)", nullable=False),
        _col("report_issued_at", datetime, "DATETIME(6)", nullable=True),
        _col("received_at", datetime, "DATETIME(6)", nullable=True),
        _col("source_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("source_file_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="file_asset(id)"),
        _col("ingestion_job_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="data_ingestion_job(id)"),
        _col("batch_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("idempotency_key", str, "VARCHAR(160)", nullable=False, is_unique=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_batch_code", ("batch_code",), unique=True),
        IndexDef("uk_e01_batch_idempotency", ("idempotency_key",), unique=True),
        IndexDef("idx_e01_batch_quarter", ("quarter_code", "effective_status", "data_nature"), unique=False),
    ),
    checks=(
        CheckDef("ck_e01_batch_quarter", "quarter_code REGEXP '^[0-9]{4}-Q[1-4]$'"),
        CheckDef("ck_e01_batch_time", "sample_start_at<=sample_end_at"),
        CheckDef("ck_e01_batch_status",
                 "batch_status IN ('DRAFT','PARSED','VALIDATED','PENDING_REVIEW','EFFECTIVE','REJECTED','INVALID')"),
        CheckDef("ck_e01_batch_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_batch_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 6. e01_monitor_sample — 监测样品
# ---------------------------------------------------------------------------
T_E01_MONITOR_SAMPLE = TableDef(
    table_name="e01_monitor_sample",
    columns=(
        _pk("id"),
        _col("sample_code", str, "VARCHAR(100)", nullable=False, is_unique=True),
        _col("batch_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_batch(id)"),
        _col("plan_item_id", int, "BIGINT", nullable=True, is_fk=True, fk_ref="e01_monitor_plan_item(id)"),
        _col("point_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_point(id)"),
        _col("monitor_category", str, "VARCHAR(20)", nullable=False),
        _col("sampled_at", datetime, "DATETIME(6)", nullable=False),
        _col("sample_end_at", datetime, "DATETIME(6)", nullable=True),
        _col("planned_sample_at_snapshot", datetime, "DATETIME(6)", nullable=True),
        _col("planned_actual_variance_minutes", int, "INT", nullable=True),
        _col("sample_no", str, "VARCHAR(100)", nullable=True),
        _col("idempotency_key", str, "VARCHAR(180)", nullable=False, is_unique=True),
        _col("sample_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("void_reason", str, "VARCHAR(500)", nullable=True),
        _col("duplicate_of_sample_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e01_monitor_sample(id)"),
        _col("raw_record_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_sample_code", ("sample_code",), unique=True),
        IndexDef("uk_e01_sample_idempotency", ("idempotency_key",), unique=True),
        IndexDef("idx_e01_sample_kpi",
                 ("sampled_at", "monitor_category", "sample_status", "effective_status", "data_nature", "is_demo"),
                 unique=False),
    ),
    checks=(
        CheckDef("ck_e01_sample_category", "monitor_category IN ('WATER','AIR','NOISE')"),
        CheckDef("ck_e01_sample_status", "sample_status IN ('VALID','PENDING_REVIEW','VOID','DUPLICATE')"),
        CheckDef("ck_e01_sample_time", "sample_end_at IS NULL OR sampled_at<=sample_end_at"),
        CheckDef("ck_e01_sample_duplicate",
                 "(sample_status='DUPLICATE' AND duplicate_of_sample_id IS NOT NULL) OR sample_status<>'DUPLICATE'"),
        CheckDef("ck_e01_sample_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_sample_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 7. e01_factor_definition — 因子定义
# ---------------------------------------------------------------------------
T_E01_FACTOR_DEFINITION = TableDef(
    table_name="e01_factor_definition",
    columns=(
        _pk("id"),
        _col("factor_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("factor_name", str, "VARCHAR(160)", nullable=False),
        _col("monitor_category", str, "VARCHAR(20)", nullable=False),
        _col("default_unit", str, "VARCHAR(60)", nullable=True),
        _col("effective_from", datetime, "DATETIME(6)", nullable=True),
        _col("effective_to", datetime, "DATETIME(6)", nullable=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
    ),
    indexes=(
        IndexDef("uk_e01_factor_code", ("factor_code",), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_factor_category", "monitor_category IN ('WATER','AIR','NOISE')"),
        CheckDef("ck_e01_factor_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_factor_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 8. e01_standard_version — 标准版本
# ---------------------------------------------------------------------------
T_E01_STANDARD_VERSION = TableDef(
    table_name="e01_standard_version",
    columns=(
        _pk("id"),
        _col("standard_code", str, "VARCHAR(100)", nullable=False),
        _col("standard_name", str, "VARCHAR(255)", nullable=False),
        _col("version_no", str, "VARCHAR(80)", nullable=False),
        _col("issuing_authority", str, "VARCHAR(255)", nullable=True),
        _col("applicable_from", datetime, "DATETIME(6)", nullable=True),
        _col("applicable_to", datetime, "DATETIME(6)", nullable=True),
        _col("source_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
    ),
    indexes=(
        IndexDef("uk_e01_standard_version", ("standard_code", "version_no"), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_standard_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_standard_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 9. e01_standard_limit — 标准限值
# ---------------------------------------------------------------------------
T_E01_STANDARD_LIMIT = TableDef(
    table_name="e01_standard_limit",
    columns=(
        _pk("id"),
        _col("standard_version_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_standard_version(id)"),
        _col("factor_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_factor_definition(id)"),
        _col("applicable_scene", str, "VARCHAR(255)", nullable=True),
        _col("limit_operator", str, "VARCHAR(10)", nullable=False),
        _col("limit_value_raw", str, "VARCHAR(100)", nullable=False),
        _col("limit_value_num", Decimal, "DECIMAL(24,10)", nullable=True),
        _col("unit", str, "VARCHAR(60)", nullable=False),
        _col("period_description", str, "VARCHAR(255)", nullable=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
    ),
    indexes=(
        IndexDef("idx_e01_limit_standard_factor", ("standard_version_id", "factor_id"), unique=False),
    ),
    checks=(
        CheckDef("ck_e01_limit_operator", "limit_operator IN ('<','<=','=','>=','>')"),
        CheckDef("ck_e01_limit_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_limit_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 10. e_closure_case — 闭环案件
# ---------------------------------------------------------------------------
T_E_CLOSURE_CASE = TableDef(
    table_name="e_closure_case",
    columns=(
        _pk("id"),
        _col("case_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("case_domain", str, "VARCHAR(30)", nullable=False),
        _col("source_table", str, "VARCHAR(80)", nullable=False),
        _col("source_record_id", int, "BIGINT", nullable=False),
        _col("source_business_key", str, "VARCHAR(160)", nullable=True),
        _col("source_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("title", str, "VARCHAR(255)", nullable=False),
        _col("location_text", str, "VARCHAR(255)", nullable=True),
        _col("gis_feature_id", str, "VARCHAR(96)", nullable=True,
             is_fk=True, fk_ref="gis_feature(id)"),
        _col("current_status", str, "VARCHAR(40)", nullable=False, default="'DISCOVERED'"),
        _col("current_status_history_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e_case_status_history(id)"),
        _col("priority", str, "VARCHAR(30)", nullable=True),
        _col("severity", str, "VARCHAR(30)", nullable=True),
        _col("deadline", datetime, "DATETIME(6)", nullable=True),
        _col("discovery_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("responsible_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("review_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("close_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("opened_at", datetime, "DATETIME(6)", nullable=False),
        _col("closed_at", datetime, "DATETIME(6)", nullable=True),
        _col("reopened_at", datetime, "DATETIME(6)", nullable=True),
        _col("closure_reason", str, "VARCHAR(500)", nullable=True),
        _col("merged_into_case_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e_closure_case(id)"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("row_version", int, "INT", nullable=False, default="0"),
        _col("created_by", int, "BIGINT", nullable=True),
        _col("updated_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e_case_code", ("case_code",), unique=True),
        IndexDef("uk_e_case_source_key", ("case_domain", "source_business_key"), unique=True),
        IndexDef("idx_e_case_open",
                 ("case_domain", "current_status", "effective_status", "data_nature", "is_demo"),
                 unique=False),
    ),
    checks=(
        CheckDef("ck_e_case_domain", "case_domain IN ('E01_EXCEED','E02_ENV','E03_WATER')"),
        CheckDef("ck_e_case_status",
                 "current_status IN ('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW',"
                 "'PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')"),
        CheckDef("ck_e_case_formal_source",
                 "data_nature<>'formal' OR source_business_key IS NOT NULL"),
        CheckDef("ck_e_case_closed_fields",
                 "current_status<>'CLOSED' OR (closed_at IS NOT NULL AND closure_reason IS NOT NULL)"),
        CheckDef("ck_e_case_merged_fields",
                 "current_status<>'MERGED' OR merged_into_case_id IS NOT NULL"),
        CheckDef("ck_e_case_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e_case_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 11. e_case_status_history — 案件状态变更历史（仅追加）
# ---------------------------------------------------------------------------
T_E_CASE_STATUS_HISTORY = TableDef(
    table_name="e_case_status_history",
    columns=(
        _pk("id"),
        _col("case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("sequence_no", int, "INT", nullable=False),
        _col("from_status", str, "VARCHAR(40)", nullable=True),
        _col("to_status", str, "VARCHAR(40)", nullable=False),
        _col("action_code", str, "VARCHAR(60)", nullable=False),
        _col("transition_result", str, "VARCHAR(30)", nullable=False, default="'SUCCESS'"),
        _col("action_at", datetime, "DATETIME(6)", nullable=False),
        _col("operator_id", int, "BIGINT", nullable=True),
        _col("operator_name", str, "VARCHAR(100)", nullable=True),
        _col("operator_org_id", int, "BIGINT", nullable=True),
        _col("operator_org_name", str, "VARCHAR(160)", nullable=True),
        _col("comment", str, "VARCHAR(1000)", nullable=True),
        _col("source_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("client_request_id", str, "VARCHAR(100)", nullable=False),
        _col("correction_of_history_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e_case_status_history(id)"),
        # 注意：e_case_status_history 无 effective_status 字段
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e_case_history_sequence", ("case_id", "sequence_no"), unique=True),
        IndexDef("uk_e_case_history_request", ("case_id", "client_request_id"), unique=True),
        IndexDef("idx_e_case_history_correction", ("case_id", "correction_of_history_id"), unique=False),
    ),
    checks=(
        CheckDef("ck_e_case_history_from",
                 "from_status IS NULL OR from_status IN "
                 "('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW',"
                 "'PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')"),
        CheckDef("ck_e_case_history_to",
                 "to_status IN ('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW',"
                 "'PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')"),
        CheckDef("ck_e_case_history_result",
                 "transition_result IN ('SUCCESS','REJECTED','RETURNED','CORRECTION')"),
        CheckDef("ck_e_case_history_correction",
                 "(action_code='CORRECT_HISTORY' AND correction_of_history_id IS NOT NULL "
                 "AND transition_result='CORRECTION') "
                 "OR (action_code<>'CORRECT_HISTORY' AND correction_of_history_id IS NULL)"),
        CheckDef("ck_e_case_history_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
    ),
)

# ---------------------------------------------------------------------------
# 12. e_case_party — 案件参与方
# ---------------------------------------------------------------------------
T_E_CASE_PARTY = TableDef(
    table_name="e_case_party",
    columns=(
        _pk("id"),
        _col("case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("party_role", str, "VARCHAR(30)", nullable=False),
        _col("org_id", int, "BIGINT", nullable=True, is_fk=True, fk_ref="org_unit(id)"),
        _col("org_name", str, "VARCHAR(160)", nullable=True),
        _col("user_id", int, "BIGINT", nullable=True),
        _col("user_name", str, "VARCHAR(100)", nullable=True),
        _col("valid_from", datetime, "DATETIME(6)", nullable=False),
        _col("valid_to", datetime, "DATETIME(6)", nullable=True),
        _col("is_current", bool, "TINYINT(1)", nullable=False, default="1"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("idx_e_case_party_case", ("case_id", "party_role", "is_current"), unique=False),
    ),
    checks=(
        CheckDef("ck_e_case_party_role",
                 "party_role IN ('DISCOVERER','RESPONSIBLE','HANDLER','REVIEWER','CLOSER','TEST_PROVIDER')"),
        CheckDef("ck_e_case_party_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
    ),
)

# ---------------------------------------------------------------------------
# 13. e_case_evidence — 案件证据
# ---------------------------------------------------------------------------
T_E_CASE_EVIDENCE = TableDef(
    table_name="e_case_evidence",
    columns=(
        _pk("id"),
        _col("case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("status_history_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e_case_status_history(id)"),
        _col("document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("file_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="file_asset(id)"),
        _col("evidence_role", str, "VARCHAR(40)", nullable=False),
        _col("version_no", int, "INT", nullable=False, default="1"),
        _col("is_current", bool, "TINYINT(1)", nullable=False, default="1"),
        _col("validity_status", str, "VARCHAR(20)", nullable=False, default="'VALID'"),
        _col("verification_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("created_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("idx_e_case_evidence_case", ("case_id", "evidence_role", "is_current"), unique=False),
    ),
    checks=(
        CheckDef("ck_e_case_evidence_source", "document_id IS NOT NULL OR file_id IS NOT NULL"),
        CheckDef("ck_e_case_evidence_role",
                 "evidence_role IN ('FORMAL_NOTICE','INITIAL_REPORT','RAW_RECORD',"
                 "'RECTIFICATION_MATERIAL','RETEST_REPORT','REVIEW_OPINION',"
                 "'CLOSURE_DOCUMENT','CANCELLATION_DOCUMENT')"),
        CheckDef("ck_e_case_evidence_validity",
                 "validity_status IN ('VALID','SUPERSEDED','INVALID')"),
        CheckDef("ck_e_case_evidence_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
    ),
)

# ---------------------------------------------------------------------------
# 14. e_case_relation — 案件关联关系
# ---------------------------------------------------------------------------
T_E_CASE_RELATION = TableDef(
    table_name="e_case_relation",
    columns=(
        _pk("id"),
        _col("from_case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("to_case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("relation_type", str, "VARCHAR(30)", nullable=False),
        _col("reason", str, "VARCHAR(500)", nullable=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e_case_relation", ("from_case_id", "to_case_id", "relation_type"), unique=True),
    ),
    checks=(
        CheckDef("ck_e_case_relation_self", "from_case_id<>to_case_id"),
        CheckDef("ck_e_case_relation_type",
                 "relation_type IN ('RELATED','DUPLICATE_OF','MERGED_INTO','SAME_TASK')"),
        CheckDef("ck_e_case_relation_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
    ),
)

# ---------------------------------------------------------------------------
# 15. e_rectification_task — 整改任务
# ---------------------------------------------------------------------------
T_E_RECTIFICATION_TASK = TableDef(
    table_name="e_rectification_task",
    columns=(
        _pk("id"),
        _col("task_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("title", str, "VARCHAR(255)", nullable=False),
        _col("responsible_org_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="org_unit(id)"),
        _col("deadline", datetime, "DATETIME(6)", nullable=True),
        _col("task_status", str, "VARCHAR(30)", nullable=False, default="'PENDING'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e_rect_task_code", ("task_code",), unique=True),
    ),
    checks=(
        CheckDef("ck_e_rect_task_status",
                 "task_status IN ('PENDING','IN_PROGRESS','SUBMITTED','REVIEWED','COMPLETED','CANCELLED')"),
        CheckDef("ck_e_rect_task_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e_rect_task_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 16. e_case_rectification_link — 案件-整改任务关联
# ---------------------------------------------------------------------------
T_E_CASE_RECTIFICATION_LINK = TableDef(
    table_name="e_case_rectification_link",
    columns=(
        _pk("id"),
        _col("case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("task_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_rectification_task(id)"),
        _col("link_role", str, "VARCHAR(30)", nullable=False, default="'PRIMARY'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'EFFECTIVE'"),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e_case_rect_link", ("case_id", "task_id"), unique=True),
    ),
    checks=(
        CheckDef("ck_e_case_rect_link_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e_case_rect_link_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 17. e01_exceed_event — 超标事件（含生成列 active_original_result_id）
# ---------------------------------------------------------------------------
T_E01_EXCEED_EVENT = TableDef(
    table_name="e01_exceed_event",
    columns=(
        _pk("id"),
        _col("event_code", str, "VARCHAR(100)", nullable=False, is_unique=True),
        _col("case_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e_closure_case(id)"),
        _col("original_result_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_factor_result(id)"),
        _col("first_exceeded_at", datetime, "DATETIME(6)", nullable=False),
        _col("event_category", str, "VARCHAR(20)", nullable=False),
        _col("current_retest_round", int, "INT", nullable=False, default="0"),
        _col("latest_retest_outcome", str, "VARCHAR(30)", nullable=False, default="'NOT_TESTED'"),
        _col("closure_confirmed_at", datetime, "DATETIME(6)", nullable=True),
        _col("closure_confirmed_by", int, "BIGINT", nullable=True),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        # 生成列：GENERATED ALWAYS AS ... STORED
        _col("active_original_result_id", int, "BIGINT", nullable=True, is_unique=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_event_code", ("event_code",), unique=True),
        IndexDef("uk_e01_event_case", ("case_id",), unique=True),
        IndexDef("uk_e01_event_active_result", ("active_original_result_id",), unique=True),
        IndexDef("idx_e01_event_open",
                 ("effective_status", "data_nature", "is_demo", "current_retest_round"),
                 unique=False),
    ),
    checks=(
        CheckDef("ck_e01_event_category", "event_category IN ('WATER','AIR','NOISE')"),
        CheckDef("ck_e01_event_retest_round", "current_retest_round>=0"),
        CheckDef("ck_e01_event_retest_outcome",
                 "latest_retest_outcome IN ('NOT_TESTED','COMPLIANT','STILL_EXCEEDED','NO_JUDGEMENT')"),
        CheckDef("ck_e01_event_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_event_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 18. e01_rectification_round — 整改轮次
# ---------------------------------------------------------------------------
T_E01_RECTIFICATION_ROUND = TableDef(
    table_name="e01_rectification_round",
    columns=(
        _pk("id"),
        _col("event_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_exceed_event(id)"),
        _col("round_no", int, "INT", nullable=False),
        _col("task_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="e_rectification_task(id)"),
        _col("started_at", datetime, "DATETIME(6)", nullable=True),
        _col("submitted_at", datetime, "DATETIME(6)", nullable=True),
        _col("rectification_summary", str, "VARCHAR(1000)", nullable=True),
        _col("review_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_rect_round", ("event_id", "round_no"), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_rect_round_no", "round_no>0"),
        CheckDef("ck_e01_rect_round_time",
                 "submitted_at IS NULL OR started_at IS NULL OR started_at<=submitted_at"),
        CheckDef("ck_e01_rect_round_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_rect_round_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 19. e01_retest_round — 复测轮次
# ---------------------------------------------------------------------------
T_E01_RETEST_ROUND = TableDef(
    table_name="e01_retest_round",
    columns=(
        _pk("id"),
        _col("event_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_exceed_event(id)"),
        _col("round_no", int, "INT", nullable=False),
        _col("retest_batch_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_monitor_batch(id)"),
        _col("requested_at", datetime, "DATETIME(6)", nullable=True),
        _col("planned_sample_at", datetime, "DATETIME(6)", nullable=True),
        _col("actual_sample_at", datetime, "DATETIME(6)", nullable=True),
        _col("report_document_id", int, "BIGINT", nullable=True,
             is_fk=True, fk_ref="document_record(id)"),
        _col("outcome", str, "VARCHAR(30)", nullable=False),
        _col("review_status", str, "VARCHAR(30)", nullable=False, default="'PENDING_REVIEW'"),
        _col("reviewed_at", datetime, "DATETIME(6)", nullable=True),
        _col("reviewed_by", int, "BIGINT", nullable=True),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_retest_round", ("event_id", "round_no"), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_retest_round_no", "round_no>0"),
        CheckDef("ck_e01_retest_outcome",
                 "outcome IN ('COMPLIANT','STILL_EXCEEDED','NO_JUDGEMENT')"),
        CheckDef("ck_e01_retest_review",
                 "review_status IN ('PENDING_REVIEW','PASSED','REJECTED')"),
        CheckDef("ck_e01_retest_round_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_retest_round_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 20. e01_retest_result_link — 复测结果关联
# ---------------------------------------------------------------------------
T_E01_RETEST_RESULT_LINK = TableDef(
    table_name="e01_retest_result_link",
    columns=(
        _pk("id"),
        _col("event_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_exceed_event(id)"),
        _col("retest_round_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_retest_round(id)"),
        _col("factor_result_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_factor_result(id)"),
        _col("original_result_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_factor_result(id)"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("effective_at", datetime, "DATETIME(6)", nullable=True),
        _col("effective_by", int, "BIGINT", nullable=True),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_retest_link_round_result", ("retest_round_id", "factor_result_id"), unique=True),
        IndexDef("uk_e01_retest_link_result", ("factor_result_id",), unique=True),
    ),
    checks=(
        CheckDef("ck_e01_retest_link_distinct", "factor_result_id<>original_result_id"),
        CheckDef("ck_e01_retest_link_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_retest_link_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
    ),
)

# ---------------------------------------------------------------------------
# 21. e01_legacy_record_mapping — 历史记录映射（无 data_nature/is_demo）
# ---------------------------------------------------------------------------
T_E01_LEGACY_RECORD_MAPPING = TableDef(
    table_name="e01_legacy_record_mapping",
    columns=(
        _pk("id"),
        _col("legacy_table", str, "VARCHAR(80)", nullable=False),
        _col("legacy_record_id", int, "BIGINT", nullable=False),
        _col("target_table", str, "VARCHAR(80)", nullable=True),
        _col("target_record_id", int, "BIGINT", nullable=True),
        _col("mapping_status", str, "VARCHAR(40)", nullable=False),
        _col("reconciliation_class", str, "VARCHAR(60)", nullable=False),
        _col("difference_reason", str, "VARCHAR(1000)", nullable=True),
        _col("migration_version", str, "VARCHAR(64)", nullable=False),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_legacy_mapping",
                 ("legacy_table", "legacy_record_id", "target_table", "target_record_id", "migration_version"),
                 unique=True),
    ),
    checks=(
        CheckDef("ck_e01_legacy_status",
                 "mapping_status IN ('MAPPED','AGGREGATE_ONLY','UNMAPPABLE','EXCLUDED')"),
        CheckDef("ck_e01_legacy_class",
                 "reconciliation_class IN ('TOTAL_MATCH','ROW_MAPPABLE','AGGREGATE_MAPPABLE',"
                 "'UNMAPPABLE','EXPECTED_DIFFERENCE_DEMO_EXCLUDED','EXPECTED_DIFFERENCE_INVALID_EXCLUDED')"),
    ),
)

# ---------------------------------------------------------------------------
# 22. e01_factor_result — 因子检测结果（V1.1 新建表）
# ---------------------------------------------------------------------------
# V1.1 设计草案将其定义为新增表，DDL 位于 V1_1_012。
T_E01_FACTOR_RESULT = TableDef(
    table_name="e01_factor_result",
    columns=(
        _pk("id"),
        _col("result_code", str, "VARCHAR(255)", nullable=False, is_unique=True),
        _col("sample_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_monitor_sample(id)"),
        _col("factor_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_factor_definition(id)"),
        _col("standard_version_id", int, "BIGINT", nullable=False,
             is_fk=True, fk_ref="e01_standard_version(id)"),
        _col("test_stage", str, "VARCHAR(30)", nullable=False),
        _col("judgement", str, "VARCHAR(30)", nullable=True),
        _col("result_validity", str, "VARCHAR(20)", nullable=True),
        _col("detected_value_raw", str, "VARCHAR(100)", nullable=True),
        _col("limit_value_raw", str, "VARCHAR(100)", nullable=True),
        _col("standard_name_snapshot", str, "VARCHAR(255)", nullable=True),
        _col("reported_factor_name", str, "VARCHAR(160)", nullable=True),
        _col("reported_unit", str, "VARCHAR(60)", nullable=True),
        _col("judgement_source", str, "VARCHAR(30)", nullable=True),
        _col("effective_status", str, "VARCHAR(30)", nullable=False, default="'DRAFT'"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False, default="0"),
        _col("created_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
        _col("updated_at", datetime, "TIMESTAMP(6)", nullable=False, default="CURRENT_TIMESTAMP(6)"),
    ),
    indexes=(
        IndexDef("uk_e01_factor_result_code", ("result_code",), unique=True),
        IndexDef("idx_e01_factor_result_sample",
                 ("sample_id", "test_stage", "data_nature", "is_demo"), unique=False),
        IndexDef("idx_e01_factor_result_kpi",
                 ("test_stage", "judgement", "result_validity",
                  "effective_status", "data_nature", "is_demo"), unique=False),
        IndexDef("idx_e01_factor_result_factor",
                 ("factor_id", "standard_version_id"), unique=False),
    ),
    checks=(
        CheckDef("ck_e01_factor_result_stage",
                 "test_stage IN ('INITIAL','RETEST','SUPPLEMENTARY')"),
        CheckDef("ck_e01_factor_result_judgement",
                 "judgement IS NULL OR judgement IN ('EXCEEDED','COMPLIANT','NO_JUDGEMENT')"),
        CheckDef("ck_e01_factor_result_validity",
                 "result_validity IS NULL OR result_validity IN ('VALID','VOID','PENDING')"),
        CheckDef("ck_e01_factor_result_effective",
                 "effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')"),
        CheckDef("ck_e01_factor_result_nature",
                 "(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)"),
        CheckDef("ck_e01_factor_result_judgement_source",
                 "judgement_source IS NULL OR judgement_source IN ('AUTO_LIMIT','MANUAL','IMPORTED')"),
    ),
)


# ---------------------------------------------------------------------------
# 23-28. 项目空间/时间维度与监测频次
# ---------------------------------------------------------------------------
T_PROJECT_SECTION = TableDef(
    table_name="project_section",
    columns=(
        _pk("id"), _col("project_id", str, "VARCHAR(64)", nullable=False),
        _col("section_code", str, "VARCHAR(30)", nullable=False, is_unique=True),
        _col("section_name", str, "VARCHAR(160)", nullable=False),
        _col("chainage_start", str, "VARCHAR(30)", nullable=False),
        _col("chainage_end", str, "VARCHAR(30)", nullable=False),
        _col("start_km", Decimal, "DECIMAL(10,3)", nullable=False),
        _col("end_km", Decimal, "DECIMAL(10,3)", nullable=False),
        _col("section_type", str, "VARCHAR(30)", nullable=False),
        _col("active_status", str, "VARCHAR(20)", nullable=False),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
)

T_PROJECT_PHASE_PERIOD = TableDef(
    table_name="project_phase_period",
    columns=(
        _pk("id"), _col("project_id", str, "VARCHAR(64)", nullable=False),
        _col("phase_code", str, "VARCHAR(64)", nullable=False, is_unique=True),
        _col("phase_name", str, "VARCHAR(160)", nullable=False),
        _col("phase_type", str, "VARCHAR(40)", nullable=False),
        _col("start_at", datetime, "DATETIME(6)", nullable=False),
        _col("end_at", datetime, "DATETIME(6)", nullable=False),
        _col("phase_status", str, "VARCHAR(20)", nullable=False),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
)

T_PROJECT_ENGINEERING_OBJECT = TableDef(
    table_name="project_engineering_object",
    columns=(
        _pk("id"), _col("project_id", str, "VARCHAR(64)", nullable=False),
        _col("section_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="project_section(id)"),
        _col("object_code", str, "VARCHAR(80)", nullable=False, is_unique=True),
        _col("object_name", str, "VARCHAR(200)", nullable=False),
        _col("object_type", str, "VARCHAR(60)", nullable=False),
        _col("chainage_start", str, "VARCHAR(30)"), _col("chainage_end", str, "VARCHAR(30)"),
        _col("longitude", Decimal, "DECIMAL(11,8)"), _col("latitude", Decimal, "DECIMAL(10,8)"),
        _col("gis_feature_id", str, "VARCHAR(96)"),
        _col("active_status", str, "VARCHAR(20)", nullable=False),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
)

T_ENGINEERING_OBJECT_PHASE = TableDef(
    table_name="engineering_object_phase",
    columns=(
        _pk("id"),
        _col("object_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="project_engineering_object(id)"),
        _col("phase_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="project_phase_period(id)"),
        _col("process_code", str, "VARCHAR(80)", nullable=False),
        _col("process_name", str, "VARCHAR(200)", nullable=False),
        _col("process_start_at", datetime, "DATETIME(6)", nullable=False),
        _col("process_end_at", datetime, "DATETIME(6)", nullable=False),
        _col("process_status", str, "VARCHAR(20)", nullable=False),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
)

T_MONITOR_POINT_OBJECT_RELATION = TableDef(
    table_name="monitor_point_object_relation",
    columns=(
        _pk("id"), _col("relation_code", str, "VARCHAR(100)", nullable=False, is_unique=True),
        _col("point_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_point(id)"),
        _col("section_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="project_section(id)"),
        _col("object_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="project_engineering_object(id)"),
        _col("phase_id", int, "BIGINT", nullable=True, is_fk=True, fk_ref="project_phase_period(id)"),
        _col("object_phase_id", int, "BIGINT", nullable=True, is_fk=True, fk_ref="engineering_object_phase(id)"),
        _col("relation_role", str, "VARCHAR(30)", nullable=False),
        _col("valid_from", datetime, "DATETIME(6)", nullable=False),
        _col("valid_to", datetime, "DATETIME(6)"),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
)

T_MONITOR_FREQUENCY_RULE = TableDef(
    table_name="monitor_frequency_rule",
    columns=(
        _pk("id"), _col("rule_code", str, "VARCHAR(100)", nullable=False, is_unique=True),
        _col("plan_item_id", int, "BIGINT", nullable=False, is_fk=True, fk_ref="e01_monitor_plan_item(id)"),
        _col("frequency_code", str, "VARCHAR(30)", nullable=False),
        _col("interval_value", int, "INT"), _col("interval_unit", str, "VARCHAR(20)"),
        _col("schedule_expression", str, "VARCHAR(255)"),
        _col("aggregation_granularity", str, "VARCHAR(30)"),
        _col("trigger_event", str, "VARCHAR(160)"),
        _col("effective_from", datetime, "DATETIME(6)", nullable=False),
        _col("effective_to", datetime, "DATETIME(6)"),
        _col("active_status", str, "VARCHAR(20)", nullable=False),
        _col("data_nature", str, "VARCHAR(20)", nullable=False),
        _col("is_demo", bool, "TINYINT(1)", nullable=False),
    ),
    checks=(CheckDef("ck_monitor_frequency_code",
                     "frequency_code IN ('CONTINUOUS','DAILY','WEEKLY','MONTHLY','QUARTERLY','EVENT_TRIGGERED')"),),
)


# ===========================================================================
# 全部表定义注册表
# ===========================================================================

ALL_TABLE_DEFS: dict[str, TableDef] = {
    t.table_name: t
    for t in (
        T_ESG_SCHEMA_MIGRATION_HISTORY,
        T_E01_MONITOR_POINT,
        T_E01_MONITOR_PLAN,
        T_E01_MONITOR_PLAN_ITEM,
        T_E01_MONITOR_BATCH,
        T_E01_MONITOR_SAMPLE,
        T_E01_FACTOR_DEFINITION,
        T_E01_STANDARD_VERSION,
        T_E01_STANDARD_LIMIT,
        T_E_CLOSURE_CASE,
        T_E_CASE_STATUS_HISTORY,
        T_E_CASE_PARTY,
        T_E_CASE_EVIDENCE,
        T_E_CASE_RELATION,
        T_E_RECTIFICATION_TASK,
        T_E_CASE_RECTIFICATION_LINK,
        T_E01_EXCEED_EVENT,
        T_E01_RECTIFICATION_ROUND,
        T_E01_RETEST_ROUND,
        T_E01_RETEST_RESULT_LINK,
        T_E01_LEGACY_RECORD_MAPPING,
        T_E01_FACTOR_RESULT,
        T_PROJECT_SECTION,
        T_PROJECT_PHASE_PERIOD,
        T_PROJECT_ENGINEERING_OBJECT,
        T_ENGINEERING_OBJECT_PHASE,
        T_MONITOR_POINT_OBJECT_RELATION,
        T_MONITOR_FREQUENCY_RULE,
    )
}
