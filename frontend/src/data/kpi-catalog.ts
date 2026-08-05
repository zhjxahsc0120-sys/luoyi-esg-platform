/**
 * 首页驾驶舱 KPI 展示名称目录（V0.4.5：S/G 口径校正 + G 槽位重映射）
 * 仅覆盖首页卡片 label / 展示槽位；编码 / API / 计算口径不变。
 * fullName 供首页 overlay 与详情等非计算场景使用。
 */
export const KPI_HOME_CATALOG = {
  E01: {
    label: '环保风险预警',
    fullName: '环保风险预警',
    unit: '项',
    source: 'E01 环境监测点 / 超标异常台账',
    caliber: '监测点异常与未闭环事项（演示可 mock）',
  },
  E02: {
    label: '水保风险预警',
    fullName: '水保风险预警',
    unit: '处',
    source: 'E02 水保对象台账（弃土场/临时用地/表土剥离/边坡复绿）',
    caliber: '水保管控对象数量（演示）',
  },
  E03: {
    label: '生态保护管控',
    fullName: '生态保护管控',
    unit: '处',
    source: 'E03 生态敏感区域与生态保护对象',
    caliber: '敏感区 + 保护对象数量（演示）',
  },
  E04: {
    label: '文物保护管控',
    fullName: '文物保护管控',
    unit: '处',
    source: 'E04 文物保护对象台账 biz_cultural_relic_object',
    caliber: '文物保护对象数量；0 对象时展示调查已完成 / 风险正常',
  },
  S01: {
    label: '安全生产天数',
    fullName: '安全生产天数',
    unit: '天',
    source: 'S01 确认批次',
    caliber: '连续安全生产天数（展示短名）',
  },
  S02: {
    label: '重大风险源',
    fullName: '重大风险源',
    unit: '项',
    source: 'safety_risk_point / S02 安全风险点台账',
    caliber: '风险对象数量（在管重大/较大风险源）',
  },
  S03: {
    label: '工资按时发放率',
    fullName: '工资按时发放率',
    unit: '%',
    source: 'biz_worker_payment_summary / 工资支付汇总事实',
    caliber: '首页展示工资按时发放率（百分比）；数值来自 API/事实表',
  },
  S04: {
    label: '群众诉求闭环',
    fullName: '群众诉求闭环',
    unit: '项',
    source: '群众诉求台账',
    caliber: '群众诉求处理情况（未办结投诉、信访、征拆协调等）',
  },
  G01: {
    label: '合规审批与许可',
    fullName: '合规审批与许可',
    /** 空串：不覆盖 API 单位（完成率 %） */
    unit: '',
    source: 'API 实时聚合 compliance_procedure + permit_record',
    caliber:
      'V0.4：已完成/应完成 = 两表分别计数后相加（禁止 12/12+2/2 字符串拼接）。审批完成=status已完成；许可完成=非临期/逾期。',
  },
  G02: {
    label: '重大风险专项方案',
    fullName: '重大风险专项方案',
    unit: '',
    source: 'API 实时聚合 safety_risk_point → special_plan_approval',
    caliber:
      'V0.4：应完成=在管重大/较大风险源；已完成=对应专项方案审批通过且关联审批文件。不再读取 biz_night_construction_record / 旧许可统计。',
  },
  G03: {
    label: '设计变更管理',
    fullName: '设计变更管理',
    unit: '项',
    source: 'biz_design_change',
    caliber: '设计变更数量/审批/实施/异常；Demo 契约固定为设计变更，不绑定整改',
  },
  G04: {
    label: '合规管理天数',
    fullName: '合规管理天数',
    unit: '天',
    source: '前端演示配置 G04_HOME_DEMO_DISPLAY（非 S01、非 API 计算）',
    caliber:
      'V0.4.6：首页仅展示「合规管理天数 / XX天」。API/DB 仍可能返回状态词「正常」；首页 overlay 用前端 Demo 起算日生成天数，不复用 S01 接口。',
  },
} as const

export type KpiHomeCode = keyof typeof KPI_HOME_CATALOG

/**
 * 首页隐藏的 KPI 编码（API/DB 编码仍保留）。
 * V0.4.5：撤销 V0.4.4 对 G02 的隐藏，首页恢复 12 卡（E4+S4+G4）。
 */
export const KPI_HOME_HIDDEN_KEYS: ReadonlySet<KpiHomeCode> = new Set()

/**
 * G04 首页演示展示配置（V0.4.6）。
 * - 仅用于首页卡片 overlay，不调用 S01、不改 API/DB。
 * - 起算日语义：合规管理起算日（可与项目开工日相同数值，但是独立配置）。
 * - asOfDate 对齐当前 Demo period_end=2026-08-04。
 */
export const G04_HOME_DEMO_DISPLAY = {
  managementStartDate: '2026-05-08',
  asOfDate: '2026-08-04',
  hint: '演示：自合规管理起算日起累计管理天数（前端适配，非 API 发布值）',
} as const

/** Calendar days inclusive: asOf - start + 1（与演示统计截止日对齐）。 */
export function computeG04HomeDemoDays(
  startDate = G04_HOME_DEMO_DISPLAY.managementStartDate,
  asOfDate = G04_HOME_DEMO_DISPLAY.asOfDate,
): number {
  const start = new Date(`${startDate}T00:00:00`)
  const asOf = new Date(`${asOfDate}T00:00:00`)
  const ms = asOf.getTime() - start.getTime()
  if (Number.isNaN(ms)) return 0
  return Math.floor(ms / 86_400_000) + 1
}
