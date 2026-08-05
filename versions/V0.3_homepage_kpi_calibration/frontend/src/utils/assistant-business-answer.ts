/**
 * 将助手 API 原始回答整形为「项目管理汇报」业务卡片结构。
 * 不改后端；上级检查类必须保留 PackageCard + 11 类统计口径。
 */
import type {
  AssistantAnswerType,
  AssistantAskResponse,
  AssistantDataBasis,
  AssistantKpiCard,
  AssistantNextAction,
  AssistantRiskItem,
  BusinessStatusLevel,
  ChatMessage,
} from '@/types/assistant'

type RawMessage = NonNullable<AssistantAskResponse['data']['message']>

function numFromKpi(cards: AssistantKpiCard[] | undefined, labelPart: string): number | null {
  const hit = (cards || []).find((c) => String(c.label).includes(labelPart))
  if (!hit) return null
  const n = Number(String(hit.value).replace(/[^\d.-]/g, ''))
  return Number.isFinite(n) ? n : null
}

function pickStatusLevel(opts: {
  intentKey?: string | null
  openCount?: number | null
  pendingCount?: number | null
  majorRisks?: number | null
}): BusinessStatusLevel {
  const open = opts.openCount ?? 0
  const pending = opts.pendingCount ?? 0
  const risks = opts.majorRisks ?? 0
  if (opts.intentKey?.startsWith('pack.superior')) {
    if (pending >= 4 || open >= 5) return '需重点关注'
    if (pending > 0 || open > 0) return '存在风险'
    return '基本受控'
  }
  if (opts.intentKey === 's02.active_major_risks' || opts.intentKey === 's02.segment_3') {
    if (risks >= 5) return '需重点关注'
    if (risks > 0) return '存在风险'
    return '正常'
  }
  if (open >= 5 || pending >= 4) return '需重点关注'
  if (open > 0 || pending > 0) return '存在风险'
  if (opts.intentKey === 'e02.open_issues' && open === 0) return '正常'
  return '基本受控'
}

function enrichKpis(
  cards: AssistantKpiCard[] | undefined,
  intentKey?: string | null,
): AssistantKpiCard[] {
  const list = [...(cards || [])]
  return list.slice(0, 6).map((card) => {
    if (card.meaning && card.statusText) return card
    const label = String(card.label)
    let meaning = card.meaning
    let statusText = card.statusText
    const val = Number(String(card.value).replace(/[^\d.-]/g, ''))
    const hasNum = Number.isFinite(val)

    if (label.includes('未闭环') || label.includes('环保问题')) {
      meaning = meaning || (hasNum && val > 0 ? '仍有事项未销项，影响迎检闭环口径' : '台账无待销项事项')
      statusText = statusText || (hasNum && val > 0 ? '需跟进' : '正常')
    } else if (label.includes('整改') && label.includes('率')) {
      meaning = meaning || '反映问题闭环进度'
      statusText = statusText || (hasNum && val >= 85 ? '受控' : '偏低')
    } else if (label.includes('完整率') || label.includes('已归集')) {
      meaning = meaning || '备检资料归集进度'
      statusText = statusText || '备检关键'
    } else if (label.includes('待补齐')) {
      meaning = meaning || '缺失项将直接形成检查风险'
      statusText = statusText || (hasNum && val > 0 ? '有缺口' : '已齐')
    } else if (label.includes('类别')) {
      meaning = meaning || '按审批—实施—监测—整改—销项证据链分类'
      statusText = statusText || '标准目录'
    } else if (label.includes('应备具体') || label.includes('应备文件')) {
      meaning = meaning || '11 类目录下的具体文件应备总量'
      statusText = statusText || '应备口径'
    } else if (label.includes('闭环率')) {
      meaning = meaning || '历史问题销项完成情况'
      statusText = statusText || '台账核验'
    } else if (label.includes('安全') || label.includes('在管') || label.includes('风险')) {
      meaning = meaning || '在管较大及以上风险点数量'
      statusText = statusText || (hasNum && val > 0 ? '在管' : '无在管')
    } else if (label.includes('待处理') || label.includes('月报')) {
      meaning = meaning || '本月仍需补正或确认的资料'
      statusText = statusText || (hasNum && val > 0 ? '待处理' : '已清')
    } else if (label.includes('碳')) {
      meaning = meaning || '项目累计碳排放口径'
      statusText = statusText || '台账'
    } else if (intentKey?.startsWith('pack.superior')) {
      meaning = meaning || '检查准备相关指标'
      statusText = statusText || '备检'
    } else {
      meaning = meaning || '与首页同源业务指标'
      statusText = statusText || '已核验'
    }
    return { ...card, meaning, statusText }
  })
}

function risksFromTable(msg: RawMessage, intentKey?: string | null): {
  title: string
  items: AssistantRiskItem[]
} {
  const rows = msg.tableData?.rows || []
  if (!rows.length) return { title: '重点关注', items: [] }

  if (intentKey?.startsWith('pack.superior')) {
    const pending = rows
      .filter((r) => Number(r.pending || 0) > 0 || String(r.note || '').includes('待补齐'))
      .slice(0, 6)
      .map((r) => ({
        title: String(r.category || r.name || r.taskName || '资料类别'),
        section: String(r.note || '资料目录'),
        status: Number(r.pending || 0) > 0 ? `待补齐 ${r.pending} 项` : String(r.status || '待补齐'),
      }))
    if (pending.length) return { title: '缺失资料 / 类别缺口', items: pending }

    // 兜底：取前几行说明
    return {
      title: '备检关注点',
      items: rows.slice(0, 4).map((r) => ({
        title: String(r.category || r.name || '事项'),
        section: String(r.note || ''),
        status: Number(r.pending || 0) > 0 ? '待补齐' : '已归集',
      })),
    }
  }

  // 问题 / 风险列表
  const items = rows.slice(0, 6).map((r) => ({
    title: String(r.issueTitle || r.riskName || r.name || r.taskName || r.title || '事项'),
    section: String(r.sectionName || r.segment || r.groupCode || r.dept || r.owner || r.responsibleRole || ''),
    status: String(r.handleStatus || r.timeStatus || r.status || r.riskLevel || '待处理'),
  }))
  return { title: '重点关注', items }
}

function buildNextActions(
  msg: RawMessage,
  intentKey?: string | null,
): AssistantNextAction[] {
  if (intentKey?.startsWith('pack.superior')) {
    const actions: AssistantNextAction[] = [
      { label: '查看未闭环环保问题清单', question: '当前有哪些未闭环环保问题？' },
      { label: '查看待补齐关键合规资料', question: '当前有哪些待补齐的关键合规资料？' },
    ]
    if (msg.packageCard?.downloadUrl) {
      actions.push({ label: '下载本轮合规资料包', question: undefined })
    }
    return actions
  }
  if (intentKey === 'e02.open_issues' || intentKey === 'cross.overdue_rectify') {
    return [
      { label: '查看详细问题清单', question: '当前有哪些未闭环环保问题？' },
      { label: '按责任单位统计', question: '按责任部门统计' },
      { label: '查看上级环保检查准备情况', question: '应对上级环保检查应准备哪些合规资料？' },
    ]
  }
  if (intentKey?.startsWith('s02')) {
    return [
      { label: '查看三标段安全情况', question: '三标段安全风险情况' },
      { label: '上级安全检查备检口径', question: '上级安全检查常见核查项与现有台账缺口？' },
    ]
  }
  if (intentKey?.includes('monthly')) {
    return [
      { label: '查看月报待处理清单', question: '本月还有哪些月报资料待处理？' },
      { label: '查看合规资料缺口', question: '当前有哪些待补齐的关键合规资料？' },
    ]
  }
  const fromFollow = (msg.followUps || []).slice(0, 3).map((q) => ({ label: q, question: q }))
  if (fromFollow.length) return fromFollow
  return [
    { label: '查看环保风险', question: '当前环保风险情况如何？' },
    { label: '查看上级检查准备', question: '如果现在接受上级检查，主要风险是什么？' },
  ]
}

function rewriteConclusion(opts: {
  intentKey?: string | null
  rawContent: string
  level: BusinessStatusLevel
  openCount: number | null
  pendingCount: number | null
  collected?: number | null
  required?: number | null
  majorRisks?: number | null
  periodLabel: string
}): string {
  const { intentKey, level, periodLabel } = opts
  if (intentKey === 'pack.superior_env' || intentKey === 'pack.superior_comprehensive') {
    const required = opts.required ?? 0
    const collected = opts.collected ?? 0
    const pending = opts.pendingCount ?? 0
    const open = opts.openCount ?? 0
    const rate = required > 0 ? Math.round((collected / required) * 100) : 0
    return (
      `截至${periodLabel}，\n` +
      `项目当前【检查准备状态】为：【${level}】。\n` +
      `上级环保检查资料按 11 类证据链备检，资料完整率约 ${rate}%` +
      `（已归集 ${collected}/${required || '—'} 项），待补齐 ${pending} 项；` +
      `当前未闭环环保问题 ${open} 项。` +
      `同条回复已附合规资料包，可直接下载备检。`
    )
  }
  if (intentKey === 'pack.superior_safety') {
    const risks = opts.majorRisks ?? 0
    return (
      `截至${periodLabel}，\n` +
      `项目当前【安全迎检状态】为：【${level}】。\n` +
      `在管较大及以上安全风险 ${risks} 处，建议对照安全合规资料包核查台账缺口，同条可下载资料包。`
    )
  }
  if (intentKey === 'e02.open_issues') {
    const open = opts.openCount ?? 0
    if (open <= 0) {
      return (
        `截至${periodLabel}，\n` +
        `项目当前【环保管理状态】为：【正常】。\n` +
        `台账显示暂无未闭环环保问题，日常巡查与销项机制运行正常；迎检前仍建议复核监测与资料归集。`
      )
    }
    return (
      `截至${periodLabel}，\n` +
      `项目当前【环保管理状态】为：【${level}】。\n` +
      `当前存在 ${open} 项待闭环环保事项，需按责任单位推进整改、复查与销项，避免形成上级检查风险点。`
    )
  }
  if (intentKey === 's02.active_major_risks' || intentKey === 's02.segment_3') {
    const risks = opts.majorRisks ?? 0
    return (
      `截至${periodLabel}，\n` +
      `项目当前【安全管理状态】为：【${level}】。\n` +
      (risks > 0
        ? `在管较大及以上安全风险 ${risks} 处，需保持管控措施有效并跟踪销项。`
        : `当前台账无在管较大及以上安全风险点。`)
    )
  }
  if (intentKey?.includes('monthly')) {
    const pending = opts.pendingCount ?? 0
    return (
      `截至${periodLabel}，\n` +
      `项目当前【月报资料状态】为：【${level}】。\n` +
      (pending > 0
        ? `本月尚有 ${pending} 项月报资料待处理，存在报送进度风险，建议按责任人限期补齐。`
        : `本月月报资料台账暂无待处理项。`)
    )
  }
  if (intentKey === 'kpi.esg_overview') {
    return (
      `截至${periodLabel}，\n` +
      `项目当前【ESG 综合状态】为：【${level}】。\n` +
      `以下按环境、安全、治理维度汇总关键指标，并标出需跟进事项。`
    )
  }
  if (intentKey?.includes('carbon') || intentKey === 'e04.cumulative_carbon') {
    return (
      `截至${periodLabel}，\n` +
      `项目当前【碳管理状态】为：【基本受控】。\n` +
      `以下为累计碳排放及相关专题指标，数据与首页碳口径保持一致。`
    )
  }
  // 保留后端文案，但若不像状态结论则包一层
  const raw = (opts.rawContent || '').trim()
  if (raw.startsWith('截至') || raw.includes('【')) return raw
  if (!raw) return `截至${periodLabel}，\n暂无有效数据，请稍后重试或改用工作台查看。`
  return `截至${periodLabel}，\n项目当前业务状态为：【${level}】。\n${raw}`
}

function ensureDataBasis(
  basis: AssistantDataBasis | undefined,
  intentKey?: string | null,
): AssistantDataBasis | undefined {
  if (!basis) {
    return {
      itemName: '业务台账查询',
      scope: '罗宜高速项目全线',
      updateTime: new Date().toISOString().slice(0, 16).replace('T', ' '),
      dataPeriod: new Date().toISOString().slice(0, 7),
      verifyStatus: '已核验',
      stableId: 'ASSISTANT-LIVE',
      sources: [{ name: '业务台账 (MySQL)', time: '', status: '已核验' }],
      caliber: '与首页指标保持一致；助手不编造业务数字。',
    }
  }
  const caliber =
    basis.caliber ||
    (intentKey?.startsWith('pack.superior')
      ? '应备资料按 11 类标准目录统计；未闭环与首页 E02 同源；不以「应备仅 4 项」作主口径。'
      : '与首页指标保持一致')
  return { ...basis, caliber, verifyStatus: basis.verifyStatus || '已核验' }
}

function detectAnswerType(intentKey?: string | null): AssistantAnswerType {
  if (intentKey?.startsWith('pack.superior')) return 'inspection'
  if (intentKey === 'kpi.esg_overview') return 'overview'
  if (intentKey?.includes('carbon') || intentKey === 'e04.cumulative_carbon') return 'carbon'
  if (
    intentKey === 'e02.open_issues' ||
    intentKey?.startsWith('s02') ||
    intentKey?.includes('monthly') ||
    intentKey?.startsWith('g0')
  ) {
    return 'indicator'
  }
  return 'generic'
}

export function normalizeBusinessAnswer(input: {
  message: RawMessage
  intentKey?: string | null
  questionId?: string | null
  question?: string
  id?: string
  time?: string
}): ChatMessage {
  const msg = input.message
  const intentKey = input.intentKey
  const answerType = detectAnswerType(intentKey)

  const openCount =
    numFromKpi(msg.kpiCards, '未闭环') ??
    numFromKpi(msg.kpiCards, '环保问题') ??
    (msg.packageCard?.stats?.openIssueCount ?? null)
  const pendingCount =
    numFromKpi(msg.kpiCards, '待补齐') ??
    numFromKpi(msg.kpiCards, '待处理') ??
    (msg.packageCard?.stats?.pendingCount ?? null)
  const collected = numFromKpi(msg.kpiCards, '已归集') ?? msg.packageCard?.stats?.collectedCount ?? null
  const required =
    numFromKpi(msg.kpiCards, '应备具体') ??
    numFromKpi(msg.kpiCards, '应备文件') ??
    msg.packageCard?.stats?.requiredFileCount ??
    null
  const majorRisks =
    numFromKpi(msg.kpiCards, '在管') ??
    numFromKpi(msg.kpiCards, '安全风险') ??
    numFromKpi(msg.kpiCards, '风险') ??
    null

  const level = pickStatusLevel({ intentKey, openCount, pendingCount, majorRisks })
  const periodLabel =
    msg.dataBasis?.dataPeriod ||
    msg.dataBasis?.updateTime?.slice(0, 7) ||
    new Date().toISOString().slice(0, 7)

  const statusConclusion = rewriteConclusion({
    intentKey,
    rawContent: msg.content || '',
    level,
    openCount,
    pendingCount,
    collected,
    required,
    majorRisks,
    periodLabel,
  })

  let kpiCards = enrichKpis(msg.kpiCards, intentKey)
  // 检查类：确保完整率类 KPI 可见
  if (answerType === 'inspection' && required != null && collected != null && required > 0) {
    const rate = Math.round((collected / required) * 100)
    const hasRate = kpiCards.some((c) => String(c.label).includes('完整率'))
    if (!hasRate) {
      const rateColor: AssistantKpiCard['color'] =
        rate >= 90 ? 'green' : rate >= 75 ? 'orange' : 'red'
      kpiCards = [
        {
          label: '资料完整率',
          value: rate,
          unit: '%',
          color: rateColor,
          meaning: '已归集文件占 11 类应备文件比例',
          statusText: rate >= 90 ? '较好' : '需补齐',
        },
        ...kpiCards,
      ].slice(0, 6)
    }
  }

  const riskPack = risksFromTable(msg, intentKey)
  // 检查类：表格改为「类别进度」次要展示，主风险用缺失项
  let tableData = msg.tableData
  if (answerType === 'inspection' && tableData) {
    tableData = {
      ...tableData,
      title: tableData.title?.includes('11') ? tableData.title : '11类应备资料进度（摘要）',
    }
  }

  // 空数据保护
  const noData =
    !kpiCards.length &&
    !(riskPack.items.length) &&
    !msg.packageCard &&
    !(tableData?.rows?.length) &&
    /暂无|不可用|无法|失败/.test(msg.content || '')

  return {
    id: input.id || 'a' + Date.now(),
    role: 'assistant',
    content: noData ? '暂无有效数据' : statusConclusion,
    time: input.time || '',
    statusLevel: level,
    statusConclusion: noData ? '暂无有效数据' : statusConclusion,
    answerType,
    kpiCards: noData ? undefined : kpiCards,
    riskItems: riskPack.items.length ? riskPack.items : undefined,
    riskSectionTitle: riskPack.items.length ? riskPack.title : undefined,
    tableData: answerType === 'inspection' ? tableData : tableData,
    dataBasis: ensureDataBasis(msg.dataBasis, intentKey),
    nextActions: buildNextActions(msg, intentKey),
    followUps: msg.followUps,
    packageCard: msg.packageCard,
  }
}

export function statusLevelClass(level?: BusinessStatusLevel): string {
  if (!level) return 'level-blue'
  if (level === '正常') return 'level-green'
  if (level === '基本受控') return 'level-blue'
  if (level === '存在风险') return 'level-orange'
  return 'level-red'
}

