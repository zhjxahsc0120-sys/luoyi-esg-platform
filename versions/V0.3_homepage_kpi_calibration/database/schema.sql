-- 罗宜高速 ESG 本地联调数据库 Schema V1.1
-- 说明：本 schema 是面向当前前端联调的 SQLite 开发镜像库。
-- 正式 MySQL 设计仍以数据库成果包中的 schema/constraints/views 为准。

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS indicator_result (
  indicator_code TEXT PRIMARY KEY,
  group_code TEXT NOT NULL,
  label TEXT NOT NULL,
  full_name TEXT NOT NULL,
  value REAL NOT NULL,
  value_text TEXT,
  unit TEXT NOT NULL,
  display_order INTEGER NOT NULL,
  calculated_at TEXT NOT NULL,
  published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS indicator_snapshot (
  snapshot_type TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  published_at TEXT NOT NULL,
  PRIMARY KEY (snapshot_type, snapshot_date)
);

CREATE TABLE IF NOT EXISTS safety_production (
  project_id INTEGER PRIMARY KEY,
  project_start_date TEXT NOT NULL,
  current_date TEXT NOT NULL,
  current_stage TEXT NOT NULL,
  current_stage_detail TEXT NOT NULL,
  counting_status TEXT NOT NULL,
  update_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS construction_stage (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  detail TEXT,
  sequence_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS upload_task (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  module_code TEXT NOT NULL,
  module_name TEXT NOT NULL,
  cycle TEXT NOT NULL,
  cycle_type TEXT NOT NULL,
  deadline TEXT NOT NULL,
  progress_current INTEGER NOT NULL,
  progress_total INTEGER NOT NULL,
  status TEXT NOT NULL,
  next_step TEXT NOT NULL,
  assignee TEXT,
  assignee_dept TEXT,
  priority_code TEXT
);

CREATE TABLE IF NOT EXISTS task_document_requirement (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  name TEXT NOT NULL,
  required INTEGER NOT NULL,
  format_rule TEXT NOT NULL,
  status TEXT NOT NULL,
  template_available INTEGER NOT NULL,
  sequence_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS task_candidate_document (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  name TEXT NOT NULL,
  cycle TEXT NOT NULL,
  unit_name TEXT NOT NULL,
  link_count INTEGER NOT NULL,
  match_rate INTEGER NOT NULL,
  sequence_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS task_review_timeline (
  id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  event_time TEXT NOT NULL,
  action_text TEXT NOT NULL,
  sequence_no INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_summary (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  current_todo INTEGER NOT NULL,
  pending_upload INTEGER NOT NULL,
  pending_correction INTEGER NOT NULL,
  pending_submit INTEGER NOT NULL,
  under_review INTEGER NOT NULL,
  due_soon INTEGER NOT NULL,
  completed INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS document_summary (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  document_total INTEGER NOT NULL,
  month_new INTEGER NOT NULL,
  pending_archive INTEGER NOT NULL,
  expiring_soon INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS document_record (
  id TEXT PRIMARY KEY,
  document_name TEXT NOT NULL,
  document_type TEXT NOT NULL,
  module_code TEXT NOT NULL,
  period_value TEXT NOT NULL,
  version_no TEXT NOT NULL,
  source_name TEXT NOT NULL,
  relation_count INTEGER NOT NULL,
  validity_status TEXT NOT NULL,
  uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_record (
  id TEXT PRIMARY KEY,
  task_name TEXT NOT NULL,
  module_code TEXT NOT NULL,
  module_name TEXT NOT NULL,
  submit_time TEXT NOT NULL,
  status TEXT NOT NULL,
  reviewer TEXT,
  comment_summary TEXT,
  next_step TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_parse_item (
  id TEXT PRIMARY KEY,
  file_name TEXT NOT NULL,
  file_size TEXT NOT NULL,
  progress INTEGER NOT NULL,
  status TEXT NOT NULL
);
