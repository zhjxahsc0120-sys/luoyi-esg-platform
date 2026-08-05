"""S02 安全风险点展示台账 V0.2：对齐甲方在管较大及以上口径 + GIS 挂接。

口径（甲方 7.14 / 领导首页需求）：
- 统计仍处于施工/监控/管控且等级为「较大」「重大」的风险点
- 同一工点多项分别统计；已销号/已解除不计
- 在管起点：开工后纳入专项清单之日（本库 control_start_date）
- 解除/降级/完工由建设单位评估确认（本库 control_status='已销号' + cancelled_date）
- UI 禁「演示/测试/未确认」；标签用「持续管控」「建设单位确认」

GIS：写入 gis_feature_business_relation，并与 mysql_api._S02_GIS_LINKS 对齐。
"""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402

PROJECT_ID = "LUOYI-ESG"

# id, risk_name, risk_level, control_status, control_measure, location,
# risk_type, control_start_date, cancelled_date, created_at
RISK_ROWS = [
    (
        430001,
        "隧道施工塌方风险",
        "重大",
        "持续管控",
        "超前地质预报、监控量测、短进尺弱爆破、应急预案演练",
        "2标段 K25+300 隧道出口",
        "隧道施工",
        "2026-05-08",
        None,
        "2026-05-08 09:00:00",
    ),
    (
        430002,
        "高边坡坍塌风险",
        "重大",
        "持续管控",
        "分级开挖、边坡监测、临时支护、雨季专项巡查",
        "2标段 K18+200 路基边坡",
        "高边坡",
        "2026-05-15",
        None,
        "2026-05-15 09:00:00",
    ),
    (
        430003,
        "桥梁吊装作业风险",
        "较大",
        "持续管控",
        "吊装专项方案审批、起重指挥旁站、索具检查",
        "3标段 K32+500 大桥",
        "起重吊装",
        "2026-07-01",
        None,
        "2026-07-01 09:00:00",
    ),
    (
        430004,
        "深基坑坍塌风险",
        "较大",
        "持续管控",
        "基坑支护、排水降水、位移监测、临边防护",
        "3标段 K32+500 大桥承台基坑",
        "深基坑",
        "2026-06-25",
        None,
        "2026-06-25 09:00:00",
    ),
    (
        430005,
        "爆破作业风险",
        "较大",
        "持续管控",
        "爆破审批交底、警戒疏散、专业持证作业、飞石防护",
        "2标段 K28+000 石方段",
        "爆破作业",
        "2026-06-10",
        None,
        "2026-06-10 09:00:00",
    ),
    (
        430006,
        "起重机械倾覆风险",
        "较大",
        "持续管控",
        "设备验收、地基承载力复核、限载作业、防倾覆监测",
        "2标段 K28+200 边坡作业面",
        "起重作业",
        "2026-06-20",
        None,
        "2026-06-20 09:00:00",
    ),
    (
        430007,
        "临边防护缺失风险",
        "较大",
        "已销号",
        "临边防护补强并经建设单位现场确认",
        "1标段 K10+200 通道",
        "临边作业",
        "2026-06-15",
        "2026-07-03",
        "2026-06-15 09:00:00",
    ),
    (
        430008,
        "模板支架稳定风险",
        "较大",
        "已销号",
        "支架复核验算加固，建设单位确认销号",
        "3标段 K30+100 小桥",
        "模板支架",
        "2026-06-18",
        "2026-07-09",
        "2026-06-18 09:00:00",
    ),
    (
        430009,
        "高墩施工坠落风险",
        "较大",
        "持续管控",
        "高处作业审批、安全带/爬梯验收、防坠落网、班前交底",
        "1标段 K12+600 高墩",
        "高墩施工",
        "2026-05-20",
        None,
        "2026-05-20 09:00:00",
    ),
    (
        430010,
        "临时交通导改风险",
        "较大",
        "持续管控",
        "导改方案审批、标志标牌、夜间照明、交通协管值守",
        "1标段 K8+500 便道导改",
        "临时交通导改",
        "2026-06-05",
        None,
        "2026-06-05 09:00:00",
    ),
]

# (feature_id, relation_code, relation_name, risk_level_int, source_id, summary)
# source_id 与业务码一致（S02-xxx），与现网 gis 业务链约定对齐
GIS_RELATIONS = [
    ("slope-1-1", "S02-001", "隧道施工塌方风险", 3, "S02-001", "2标隧道出口重大风险，挂接边坡监测点附近区段"),
    ("section-2-1", "S02-002", "高边坡坍塌风险", 3, "S02-002", "2标段高边坡重大风险主挂接"),
    ("section-3-1", "S02-003", "桥梁吊装作业风险", 2, "S02-003", "3标大桥吊装较大风险"),
    ("section-3-1", "S02-004", "深基坑坍塌风险", 2, "S02-004", "同工点承台基坑，分别统计"),
    ("waste-1-1", "S02-005", "爆破作业风险", 2, "S02-005", "石方爆破作业较大风险"),
    ("slope-2-1", "S02-006", "起重机械倾覆风险", 2, "S02-006", "边坡作业面起重倾覆风险主挂接"),
    ("section-3-1", "S02-006", "起重机械倾覆风险", 2, "S02-006", "辅挂 3 标段相关区段"),
    ("section-1-1", "S02-009", "高墩施工坠落风险", 2, "S02-009", "1标高墩较大风险"),
    ("section-1-1", "S02-010", "临时交通导改风险", 2, "S02-010", "1标便道导改较大风险"),
    ("eco-1-1", "S02-010", "临时交通导改风险", 2, "S02-010", "导改邻近生态敏感区辅挂接"),
]


def seed_risk_points(cur) -> None:
    cur.execute("DELETE FROM safety_risk_point WHERE id BETWEEN 430001 AND 430099")
    cur.executemany(
        """
        INSERT INTO safety_risk_point
        (id, risk_name, risk_level, control_status, control_measure, location,
         risk_type, control_start_date, cancelled_date, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        RISK_ROWS,
    )


def seed_gis_relations(cur) -> None:
    cur.execute(
        """
        DELETE FROM gis_feature_business_relation
        WHERE project_id = %s AND relation_type = 'safety_risk'
        """,
        (PROJECT_ID,),
    )
    cur.executemany(
        """
        INSERT INTO gis_feature_business_relation
          (project_id, feature_id, relation_type, relation_code, relation_name,
           relation_status, risk_level, source_table, source_id, summary)
        VALUES
          (%s, %s, 'safety_risk', %s, %s, '持续管控', %s, 'safety_risk_point', %s, %s)
        """,
        [
            (PROJECT_ID, feature_id, code, name, level, source_id, summary)
            for feature_id, code, name, level, source_id, summary in GIS_RELATIONS
        ],
    )


def main() -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            seed_risk_points(cur)
            seed_gis_relations(cur)
        conn.commit()

    active = sum(1 for r in RISK_ROWS if r[2] in ("重大", "较大") and r[3] != "已销号")
    major = sum(1 for r in RISK_ROWS if r[2] == "重大" and r[3] != "已销号")
    larger = sum(1 for r in RISK_ROWS if r[2] == "较大" and r[3] != "已销号")
    print(
        f"S02 V0.2 seed OK: active={active} (重大{major}/较大{larger}), "
        f"cancelled=2, gis_links={len(GIS_RELATIONS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
