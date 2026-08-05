from __future__ import annotations

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "luoyi_esg_dev.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


KPI_ROWS = [
    ("E01", "E", "环境监测超标", "环境监测超标项", 2, None, "项", 1),
    ("E02", "E", "未闭环环保问题", "当前未闭环环保问题事项数", 5, None, "项", 2),
    ("E03", "E", "未闭环水保问题", "当前未闭环水保问题事项数", 7, None, "项", 3),
    ("E04", "E", "项目累计碳排放", "项目累计碳排放", 12856, None, "tCO₂e", 4),
    ("S01", "S", "连续安全生产天数", "连续安全生产天数", 368, None, "天", 1),
    ("S02", "S", "在管较大及以上安全风险点", "当前在管较大及以上安全风险点数", 6, None, "项", 2),
    ("S03", "S", "未办结劳务纠纷", "当前未办结劳务纠纷事项数", 4, None, "项", 3),
    ("S04", "S", "未办结群众诉求", "当前未办结群众诉求事项数", 3, None, "项", 4),
    ("G01", "G", "未完成报批报建", "当前未完成法定报批报建事项数", 5, None, "项", 1),
    ("G02", "G", "许可临期及逾期", "当前临期及逾期许可事项数", 5, None, "项", 2),
    ("G03", "G", "未关闭整改事项", "当前未关闭整改事项数", 6, None, "项", 3),
    ("G04", "G", "待补齐合规资料", "当前待补齐合规资料项数", 4, None, "项", 4),
]


LEADER_HOME = {
    "E01": 2,
    "E02": 5,
    "E03": 7,
    "E04": 12856,
    "S01": 368,
    "S02": 6,
    "S03": 4,
    "S04": 3,
    "G01": 5,
    "G02": 5,
    "G03": 6,
    "G04": 4,
}


MODAL_S01 = {
    "projectStartDate": "2025-07-10",
    "currentDate": "2026-07-13",
    "continuousDays": 368,
    "currentStage": "主体工程施工",
    "currentStageDetail": "路基｜桥梁｜隧道并行施工",
    "countingStatus": "continuous",
    "updateTime": "2026-07-13 10:30",
    "timeline": {
        "startLabel": "开工日期",
        "startDate": "2025-07-10",
        "message": "本轮连续周期内无事故中断",
        "endLabel": "当前",
        "endDate": "2026-07-13",
        "months": [
            "2025-07",
            "2025-08",
            "2025-09",
            "2025-10",
            "2025-11",
            "2025-12",
            "2026-01",
            "2026-02",
            "2026-03",
            "2026-04",
            "2026-05",
            "2026-06",
            "2026-07",
        ],
    },
    "constructionStages": [
        {"id": "preparation", "name": "施工准备", "status": "completed"},
        {
            "id": "main-construction",
            "name": "主体工程施工",
            "status": "current",
            "detail": "路基｜桥梁｜隧道并行施工",
        },
        {"id": "pavement", "name": "路面及附属工程", "status": "not_started"},
        {"id": "handover", "name": "交工验收", "status": "not_started"},
    ],
    "conclusion": "项目开工以来，未发生导致连续安全生产记录中断的事故，当前已连续安全生产368天。",
}


UPLOAD_TASKS = [
    ("t1", "2026年7月水保监测月报", "E", "环境环保", "2026-07（月度）", "月度", "2026-08-10 18:00", 5, 7, "待上传", "开始办理", "张建国", "安全环保部", "HIGH"),
    ("t2", "高风险作业审批资料", "S", "社会责任", "2026-07（月度）", "月度", "2026-08-11 18:00", 3, 6, "待补正", "继续补正", "李安全", "工程管理部", "HIGH"),
    ("t3", "施工人员工资支付资料", "S", "社会责任", "2026-06（月度）", "月度", "2026-07-30 18:00", 4, 5, "待提交", "提交", "王佳", "财务管理部", "URGENT"),
    ("t4", "NCR整改关闭资料", "G", "治理合规", "2026-07（月度）", "月度", "2026-08-12 18:00", 2, 4, "待补正", "开始办理", "陈质量", "工程管理部", "HIGH"),
    ("t5", "临时用地合规资料", "G", "治理合规", "2026-07（一次性）", "一次性", "2026-08-15 18:00", 1, 3, "待上传", "开始办理", "刘工", "工程管理部", "NORMAL"),
    ("t6", "碳排放活动数据填报", "E", "环境环保", "2026-Q2（季度）", "季度", "2026-08-20 18:00", 6, 6, "待提交", "提交", "赵环保", "安全环保部", "NORMAL"),
    ("t7", "安全教育培训记录", "S", "社会责任", "2026-07（月度）", "月度", "2026-08-18 18:00", 0, 3, "待上传", "开始办理", "李安全", "安全环保部", "NORMAL"),
    ("t8", "环保设施运行台账", "E", "环境环保", "2026-07（月度）", "月度", "2026-08-25 18:00", 2, 4, "待补正", "继续补正", "周丽娟", "安全环保部", "NORMAL"),
    ("t9", "质量体系内审报告", "G", "治理合规", "2026-08（月度）", "月度", "2026-09-01 18:00", 8, 8, "审核中", "查看进度", "吴浩", "工程管理部", "NORMAL"),
    ("t10", "职业健康体检资料", "S", "社会责任", "2026年度（年度）", "年度", "2026-09-10 18:00", 10, 10, "已完成", "查看详情", "郑晓燕", "安全环保部", "NORMAL"),
    ("t11", "汛期水保专项检查记录", "E", "环境环保", "2026-07（一次性）", "一次性", "2026-08-05 18:00", 3, 3, "已完成", "查看详情", "张建国", "安全环保部", "NORMAL"),
    ("t12", "农民工工资保证金缴纳凭证", "S", "社会责任", "2026-Q2（季度）", "季度", "2026-07-15 18:00", 2, 2, "已归档", "查看档案", "王佳", "财务管理部", "NORMAL"),
]


DOCUMENTS = [
    ("d1", "弃渣场巡查记录_2026-07.pdf", "监测报告", "E", "2026-07", "V2", "ESG智能入库", 3, "有效", "2026-08-10 18:00"),
    ("d2", "2026年7月水保监测月报.pdf", "监测报告", "E", "2026-07", "V1", "用户上传", 2, "有效", "2026-08-06 09:30"),
    ("d3", "高风险作业审批资料.pdf", "审批资料", "S", "2026-07", "V1", "用户上传", 1, "有效", "2026-08-07 09:15"),
    ("d4", "施工人员工资支付资料.pdf", "审批资料", "S", "2026-06", "V2", "用户上传", 2, "即将失效", "2026-08-06 16:40"),
    ("d5", "NCR整改关闭资料.pdf", "审批资料", "G", "2026-07", "V1", "用户上传", 2, "有效", "2026-08-12 09:20"),
    ("d6", "临时用地合规资料.pdf", "审批资料", "G", "2026-07", "V1", "ESG智能入库", 1, "有效", "2026-08-15 10:00"),
    ("d7", "碳排放活动数据填报.xlsx", "台账记录", "E", "2026-Q2", "V1", "用户上传", 1, "有效", "2026-08-20 18:00"),
    ("d8", "安全教育培训记录.pdf", "台账记录", "S", "2026-07", "V1", "用户上传", 1, "有效", "2026-08-18 18:00"),
    ("d9", "植被恢复现场照片.zip", "影像资料", "E", "2026-07", "V1", "用户上传", 1, "有效", "2026-08-09 15:30"),
    ("d10", "环保设施验收报告.pdf", "审批资料", "E", "2026-06", "V1", "ESG智能入库", 2, "已失效", "2026-07-28 10:00"),
]

TASK_DOCUMENT_REQUIREMENTS = [
    ("td1", "*", "水保监测实施方案", 1, "PDF，≤50MB", "已关联", 1, 1),
    ("td2", "*", "本月水保监测记录", 1, "Excel，≤20MB", "已关联", 1, 2),
    ("td3", "*", "水保监测月报", 1, "PDF，≤50MB", "已关联", 1, 3),
    ("td4", "*", "扰动面积变化表", 1, "Excel，≤20MB", "已关联", 1, 4),
    ("td5", "*", "弃渣场巡查记录", 1, "PDF，≤20MB", "格式异常", 1, 5),
    ("td6", "*", "复绿恢复统计表", 0, "Excel，≤20MB", "已关联", 1, 6),
    ("td7", "*", "审核确认单", 1, "PDF，≤10MB", "缺失", 1, 7),
]

TASK_CANDIDATE_DOCUMENTS = [
    ("c1", "*", "弃渣场巡查记录_2026-07.pdf", "2026-07", "水保监测单位", 2, 96, 1),
    ("c2", "*", "水保监测记录_2026-07.xlsx", "2026-07", "水保监测单位", 1, 92, 2),
    ("c3", "*", "水保监测实施方案_2026.pdf", "2026年度", "水保监测单位", 3, 88, 3),
    ("c4", "*", "复绿恢复统计表_2026-07.xlsx", "2026-07", "工程管理部", 0, 85, 4),
    ("c5", "*", "扰动面积变化表_2026-07.xlsx", "2026-07", "工程管理部", 1, 82, 5),
]

TASK_REVIEW_TIMELINE = [
    ("rt1", "*", "2026-08-05 18:00", "提交上传（张建国 提交任务）", 1),
    ("rt2", "*", "2026-08-05 18:05", "完整性校验（系统校验通过，共5/7项资料完整）", 2),
]


REVIEWS = [
    ("r1", "高风险作业审批资料", "S", "社会责任", "2026-08-07 09:15", "已退回", "李安全", "审批签章页缺失，附件日期与资料周期不一致", "查看意见并补正"),
    ("r2", "施工人员工资支付资料", "S", "社会责任", "2026-08-06 16:40", "已退回", "王财务", "工资表需加盖公章，部分附件清晰度不足", "查看意见并补正"),
    ("r3", "临时用地合规资料", "G", "治理合规", "2026-08-06 10:20", "已退回", "陈质量", "土地权属证明不完整，需补充用地批复文件", "查看意见并补正"),
    ("r4", "水保监测月报（2026年7月）", "E", "环境环保", "2026-08-06 09:30", "待审核", "-", "", "查看进度"),
    ("r5", "安全教育培训记录（2026年7月）", "S", "社会责任", "2026-08-05 17:25", "待审核", "-", "", "查看进度"),
    ("r6", "碳排放活动数据填报（2026-Q2）", "E", "环境环保", "2026-08-04 18:00", "已通过", "赵环保", "资料完整，符合填报要求", "查看结果"),
    ("r7", "能源消耗统计表（2026年7月）", "E", "环境环保", "2026-08-03 16:10", "已通过", "赵环保", "资料完整，符合填报要求", "查看结果"),
]


AI_PARSE = [
    ("p1", "水保监测记录_2026-07.xlsx", "1.25MB", 100, "解析完成"),
    ("p2", "弃渣场巡查记录_2026-07.pdf", "2.18MB", 96, "匹配中 96%"),
    ("p3", "安全培训签到表.jpg", "0.98MB", 0, "待确认"),
]


def dump_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    conn.executemany(
        """
        INSERT INTO indicator_result
        (indicator_code, group_code, label, full_name, value, value_text, unit, display_order, calculated_at, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '2026-07-13 10:20:00', '2026-07-13 10:30:00')
        ON CONFLICT(indicator_code) DO UPDATE SET
          group_code=excluded.group_code,
          label=excluded.label,
          full_name=excluded.full_name,
          value=excluded.value,
          value_text=excluded.value_text,
          unit=excluded.unit,
          display_order=excluded.display_order,
          calculated_at=excluded.calculated_at,
          published_at=excluded.published_at
        """,
        KPI_ROWS,
    )

    conn.executemany(
        """
        INSERT INTO indicator_snapshot(snapshot_type, snapshot_date, payload_json, published_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(snapshot_type, snapshot_date) DO UPDATE SET
          payload_json=excluded.payload_json,
          published_at=excluded.published_at
        """,
        [
            ("LEADER_HOME", "2026-07-13", dump_json(LEADER_HOME), "2026-07-13 10:30:00"),
            ("MODAL_S01", "2026-07-13", dump_json(MODAL_S01), "2026-07-13 10:30:00"),
            (
                "UPLOAD_WORKBENCH",
                "2026-08-05",
                dump_json(
                    {
                        "currentTodo": 27,
                        "pendingUpload": 12,
                        "pendingCorrection": 3,
                        "pendingSubmit": 5,
                        "underReview": 3,
                        "dueSoon": 4,
                        "completed": 36,
                        "documentTotal": 368,
                        "monthNew": 24,
                        "pendingArchive": 6,
                        "expiringSoon": 4,
                    }
                ),
                "2026-08-05 10:30:00",
            ),
        ],
    )

    conn.execute(
        """
        INSERT INTO safety_production
        (project_id, project_start_date, current_date, current_stage, current_stage_detail, counting_status, update_time)
        VALUES (900001, '2025-07-10', '2026-07-13', '主体工程施工', '路基｜桥梁｜隧道并行施工', 'continuous', '2026-07-13 10:30')
        ON CONFLICT(project_id) DO UPDATE SET
          project_start_date=excluded.project_start_date,
          current_date=excluded.current_date,
          current_stage=excluded.current_stage,
          current_stage_detail=excluded.current_stage_detail,
          counting_status=excluded.counting_status,
          update_time=excluded.update_time
        """
    )

    conn.executemany(
        """
        INSERT INTO construction_stage(id, name, status, detail, sequence_no)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          status=excluded.status,
          detail=excluded.detail,
          sequence_no=excluded.sequence_no
        """,
        [
            ("preparation", "施工准备", "completed", None, 1),
            ("main-construction", "主体工程施工", "current", "路基｜桥梁｜隧道并行施工", 2),
            ("pavement", "路面及附属工程", "not_started", None, 3),
            ("handover", "交工验收", "not_started", None, 4),
        ],
    )

    conn.executemany(
        """
        INSERT INTO upload_task
        (id, name, module_code, module_name, cycle, cycle_type, deadline, progress_current, progress_total, status, next_step, assignee, assignee_dept, priority_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          module_code=excluded.module_code,
          module_name=excluded.module_name,
          cycle=excluded.cycle,
          cycle_type=excluded.cycle_type,
          deadline=excluded.deadline,
          progress_current=excluded.progress_current,
          progress_total=excluded.progress_total,
          status=excluded.status,
          next_step=excluded.next_step,
          assignee=excluded.assignee,
          assignee_dept=excluded.assignee_dept,
          priority_code=excluded.priority_code
        """,
        UPLOAD_TASKS,
    )

    conn.execute(
        """
        INSERT INTO workspace_summary
        (id, current_todo, pending_upload, pending_correction, pending_submit, under_review, due_soon, completed)
        VALUES (1, 27, 12, 3, 5, 3, 4, 36)
        ON CONFLICT(id) DO UPDATE SET
          current_todo=excluded.current_todo,
          pending_upload=excluded.pending_upload,
          pending_correction=excluded.pending_correction,
          pending_submit=excluded.pending_submit,
          under_review=excluded.under_review,
          due_soon=excluded.due_soon,
          completed=excluded.completed
        """
    )

    conn.execute(
        """
        INSERT INTO document_summary(id, document_total, month_new, pending_archive, expiring_soon)
        VALUES (1, 368, 24, 6, 4)
        ON CONFLICT(id) DO UPDATE SET
          document_total=excluded.document_total,
          month_new=excluded.month_new,
          pending_archive=excluded.pending_archive,
          expiring_soon=excluded.expiring_soon
        """
    )

    conn.executemany(
        """
        INSERT INTO document_record
        (id, document_name, document_type, module_code, period_value, version_no, source_name, relation_count, validity_status, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          document_name=excluded.document_name,
          document_type=excluded.document_type,
          module_code=excluded.module_code,
          period_value=excluded.period_value,
          version_no=excluded.version_no,
          source_name=excluded.source_name,
          relation_count=excluded.relation_count,
          validity_status=excluded.validity_status,
          uploaded_at=excluded.uploaded_at
        """,
        DOCUMENTS,
    )

    conn.executemany(
        """
        INSERT INTO task_document_requirement
        (id, task_id, name, required, format_rule, status, template_available, sequence_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          task_id=excluded.task_id,
          name=excluded.name,
          required=excluded.required,
          format_rule=excluded.format_rule,
          status=excluded.status,
          template_available=excluded.template_available,
          sequence_no=excluded.sequence_no
        """,
        TASK_DOCUMENT_REQUIREMENTS,
    )

    conn.executemany(
        """
        INSERT INTO task_candidate_document
        (id, task_id, name, cycle, unit_name, link_count, match_rate, sequence_no)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          task_id=excluded.task_id,
          name=excluded.name,
          cycle=excluded.cycle,
          unit_name=excluded.unit_name,
          link_count=excluded.link_count,
          match_rate=excluded.match_rate,
          sequence_no=excluded.sequence_no
        """,
        TASK_CANDIDATE_DOCUMENTS,
    )

    conn.executemany(
        """
        INSERT INTO task_review_timeline
        (id, task_id, event_time, action_text, sequence_no)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          task_id=excluded.task_id,
          event_time=excluded.event_time,
          action_text=excluded.action_text,
          sequence_no=excluded.sequence_no
        """,
        TASK_REVIEW_TIMELINE,
    )

    conn.executemany(
        """
        INSERT INTO review_record
        (id, task_name, module_code, module_name, submit_time, status, reviewer, comment_summary, next_step)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          task_name=excluded.task_name,
          module_code=excluded.module_code,
          module_name=excluded.module_name,
          submit_time=excluded.submit_time,
          status=excluded.status,
          reviewer=excluded.reviewer,
          comment_summary=excluded.comment_summary,
          next_step=excluded.next_step
        """,
        REVIEWS,
    )

    conn.executemany(
        """
        INSERT INTO ai_parse_item(id, file_name, file_size, progress, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          file_name=excluded.file_name,
          file_size=excluded.file_size,
          progress=excluded.progress,
          status=excluded.status
        """,
        AI_PARSE,
    )

    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")


if __name__ == "__main__":
    main()
