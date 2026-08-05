/**
 * 首页驾驶舱 KPI 正式名称目录（V1.0 现场调研优化）
 * 仅改口径文案与追溯元数据，不改卡片布局。
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
    label: '连续安全生产天数',
    fullName: '连续安全生产天数',
    unit: '天',
    source: 'S01 确认批次',
    caliber: '保持原逻辑',
  },
  S02: {
    label: '重大风险源管控',
    fullName: '重大风险源管控',
    unit: '项',
    source: 'S02 安全风险点台账',
    caliber: '在管重大/较大风险源（未销号）',
  },
  S03: {
    label: '农民工权益保障',
    fullName: '农民工权益保障',
    unit: '%',
    source: '劳务纠纷/工资支付台账',
    caliber: '未办结劳务权益相关事项（工资、纠纷等）',
  },
  S04: {
    label: '群众诉求闭环',
    fullName: '群众诉求闭环',
    unit: '项',
    source: '群众诉求台账',
    caliber: '未办结投诉、信访、征拆协调等诉求',
  },
  G01: {
    label: '合规审批事项',
    fullName: '合规审批事项',
    unit: '项',
    source: '法定报批报建/合规手续台账',
    caliber: '未完成合规审批手续事项',
  },
  G02: {
    label: '许可及施工管控',
    fullName: '许可及施工管控',
    unit: '项',
    source: '证照许可台账',
    caliber: '临期/逾期许可及施工管控事项（首页展示临期+逾期合计）',
  },
  G03: {
    label: '设计变更管理',
    fullName: '设计变更管理',
    unit: '项',
    source: 'biz_design_change',
    caliber: '设计变更数量/审批/实施/异常；Demo 契约固定为设计变更，不绑定整改',
  },
  G04: {
    label: '内控与廉洁',
    fullName: '内控与廉洁',
    unit: '项',
    source: 'biz_internal_control_issue',
    caliber: '内控廉洁问题、证据状态和关闭；不绑定合规资料缺失',
  },
} as const

export type KpiHomeCode = keyof typeof KPI_HOME_CATALOG
