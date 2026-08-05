import type { ChatSession, QuickCategory, ChatMessage } from '@/types/assistant'



export const quickCategories: QuickCategory[] = [

  { key: 'E', name: '环境 E', desc: '环保风险与问题处理', color: 'green', icon: 'E' },

  { key: 'S', name: '社会 S', desc: '安全风险与标段管控', color: 'blue', icon: 'S' },

  { key: 'G', name: '治理 G', desc: '合规资料与迎检准备', color: 'purple', icon: 'G' },

  { key: 'CARBON', name: '碳专题', desc: '碳排放与低碳措施', color: 'cyan', icon: 'C' },

  { key: 'MONTHLY', name: '月报专题', desc: '月报资料缺口', color: 'orange', icon: 'M' },

]



export const recentSessions: ChatSession[] = [

  { id: '1', title: '当前环保风险情况如何？', lastTime: '今天', active: true },

  { id: '2', title: '如果现在接受上级检查，主要风险是什么？', lastTime: '今天' },

  { id: '3', title: '当前重大安全风险有哪些？', lastTime: '今天' },

  { id: '4', title: '本月ESG月报还有哪些资料缺口？', lastTime: '昨天' },

  { id: '5', title: '三个标段安全情况如何？', lastTime: '昨天' },

  { id: '6', title: '应对上级环保检查应准备哪些合规资料？', lastTime: '今天' },

]



/** 业务化推荐问题（按主题）；检查类必须保留且可落到资料包意图 */

export const welcomeQuestionGroups: Array<{ group: string; questions: string[] }> = [

  {

    group: '环境',

    questions: ['当前环保风险情况如何？', '当前有哪些环保问题需要处理？'],

  },

  {

    group: '安全',

    questions: ['当前重大安全风险有哪些？', '三个标段安全情况如何？'],

  },

  {

    group: '检查',

    questions: [

      '如果现在接受上级检查，主要风险是什么？',

      '当前环保资料准备情况如何？',

      '应对上级环保检查应准备哪些合规资料？',

    ],

  },

  {

    group: '月报',

    questions: ['本月ESG月报还有哪些资料缺口？'],

  },

]



export const welcomeQuestions = welcomeQuestionGroups.flatMap((g) => g.questions)



/**

 * 业务问句 → API questionId（后端路由不变时由前端映射）

 * 检查类全部落到 C03/C04/C05，保证同答资料包。

 */

export const welcomeQuestionRoutes: Record<string, { questionId: string }> = {

  '当前环保风险情况如何？': { questionId: 'Q01' },

  '当前有哪些环保问题需要处理？': { questionId: 'Q01' },

  '当前有哪些未闭环环保问题？': { questionId: 'Q01' },

  '当前重大安全风险有哪些？': { questionId: 'Q02' },

  '当前较大及以上安全风险点有多少？': { questionId: 'Q02' },

  '三个标段安全情况如何？': { questionId: 'Q08' },

  '三标段安全风险情况': { questionId: 'Q08' },

  '如果现在接受上级检查，主要风险是什么？': { questionId: 'C03' },

  '当前环保资料准备情况如何？': { questionId: 'C03' },

  '应对上级环保检查应准备哪些合规资料？': { questionId: 'C03' },

  '上级安全检查常见核查项与现有台账缺口？': { questionId: 'C04' },

  '请给出本轮上级检查可用的合规资料包': { questionId: 'C05' },

  '本月ESG月报还有哪些资料缺口？': { questionId: 'Q04' },

  '本月还有哪些月报资料待处理？': { questionId: 'Q04' },

  '项目累计碳排放是多少？': { questionId: 'Q03' },

}



/** V1.1 验收用：3 个示例业务回答（结构示意；线上优先走 API 再经业务整形） */

export const demoBusinessAnswers: Record<string, Omit<ChatMessage, 'id' | 'time'>> = {

  '当前环保风险情况如何？': {

    role: 'assistant',

    content:

      '截至2026-07，\n项目当前【环保管理状态】为：【存在风险】。\n当前存在待闭环环保事项，需重点关注整改销项与资料补充。',

    statusLevel: '存在风险',

    statusConclusion:

      '截至2026-07，\n项目当前【环保管理状态】为：【存在风险】。\n当前存在待闭环环保事项，需重点关注整改销项与资料补充。',

    answerType: 'indicator',

    kpiCards: [

      { label: '环保问题', value: 5, unit: '项', color: 'red', meaning: '未闭环事项影响迎检销项口径', statusText: '需跟进' },

      { label: '整改中', value: 3, unit: '项', color: 'blue', meaning: '正在落实整改措施', statusText: '推进中' },

      { label: '待复查/销项', value: 2, unit: '项', color: 'orange', meaning: '待现场复核或销项确认', statusText: '临近' },

    ],

    riskSectionTitle: '重点关注',

    riskItems: [

      { title: '水保边坡防护整改', section: '一标段', status: '整改中' },

      { title: '施工区洒水抑尘台账补记', section: '二标段', status: '待复查' },

      { title: '沉淀池清理闭环确认', section: '三标段', status: '待销项' },

    ],

    dataBasis: {

      itemName: 'E02 环保问题台账',

      scope: '罗宜高速项目全线',

      updateTime: '2026-07-27 11:00',

      dataPeriod: '2026-07',

      verifyStatus: '已核验',

      stableId: 'DEMO-E02',

      sources: [{ name: 'E02环保问题台账', time: '2026-07', status: '已核验' }],

      caliber: '与首页 E02 指标保持一致',

    },

    nextActions: [

      { label: '查看详细问题清单', question: '当前有哪些未闭环环保问题？' },

      { label: '查看责任单位', question: '按责任部门统计' },

      { label: '查看上级环保检查准备', question: '应对上级环保检查应准备哪些合规资料？' },

    ],

  },

  '应对上级环保检查应准备哪些合规资料？': {

    role: 'assistant',

    content:

      '截至2026-07，\n项目当前【检查准备状态】为：【需重点关注】。\n按 11 类证据链备检，资料完整率约 91%，待补齐 4 项；同条已附合规资料包。',

    statusLevel: '需重点关注',

    statusConclusion:

      '截至2026-07，\n项目当前【检查准备状态】为：【需重点关注】。\n按 11 类证据链备检，资料完整率约 91%，待补齐 4 项；同条已附合规资料包。',

    answerType: 'inspection',

    kpiCards: [

      { label: '资料完整率', value: 91, unit: '%', color: 'green', meaning: '已归集占 11 类应备文件比例', statusText: '较好' },

      { label: '应备资料类别', value: 11, unit: '类', color: 'cyan', meaning: '审批—实施—监测—整改—销项', statusText: '标准目录' },

      { label: '应备具体文件', value: 46, unit: '项', color: 'blue', meaning: '目录内具体文件总量', statusText: '应备口径' },

      { label: '待补齐', value: 4, unit: '项', color: 'orange', meaning: '缺失项将形成检查风险', statusText: '有缺口' },

      { label: '当前未闭环问题', value: 5, unit: '项', color: 'red', meaning: '与首页 E02 同源', statusText: '需跟进' },

    ],

    riskSectionTitle: '缺失资料 / 类别缺口',

    riskItems: [

      { title: '05_施工期环境监测', section: '环境监测季报等', status: '待补齐 2 项' },

      { title: '08_固废危废及应急管理', section: '应急演练记录', status: '待补齐 1 项' },

      { title: '10_环保月报及阶段总结', section: '合规性评价报告', status: '待补齐 1 项' },

    ],

    packageCard: {

      packageId: 'PACK-SUPERIOR-ENV-202607',

      title: '上级环保检查 · 合规资料包',

      inspectionType: 'env',

      nature: 'formal',

      files: [],

      downloadUrl: '/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607.zip',

      requiredCount: 46,

      updatedAt: '2026-07',

      stats: {

        categoryCount: 11,

        requiredFileCount: 46,

        collectedCount: 42,

        pendingCount: 4,

        openIssueCount: 5,

        closureRate: '1/6',

      },

    },

    dataBasis: {

      itemName: '上级环保检查合规口径',

      scope: '罗宜高速项目全线',

      updateTime: '2026-07-27 11:00',

      dataPeriod: '2026-07',

      verifyStatus: '已核验',

      stableId: 'PACK-SUPERIOR-ENV',

      sources: [{ name: '合规资料目录 + E02/G04 台账', time: '2026-07', status: '已核验' }],

      caliber: '11 类标准目录统计；未闭环与首页 E02 同源；不以「应备仅 4 项」作主口径',

    },

    nextActions: [

      { label: '查看未闭环环保问题', question: '当前有哪些未闭环环保问题？' },

      { label: '查看待补齐关键合规资料', question: '当前有哪些待补齐的关键合规资料？' },

      { label: '下载本轮合规资料包' },

    ],

  },

  '当前重大安全风险有哪些？': {

    role: 'assistant',

    content:

      '截至2026-07，\n项目当前【安全管理状态】为：【存在风险】。\n在管较大及以上安全风险需保持管控措施有效并跟踪销项。',

    statusLevel: '存在风险',

    statusConclusion:

      '截至2026-07，\n项目当前【安全管理状态】为：【存在风险】。\n在管较大及以上安全风险需保持管控措施有效并跟踪销项。',

    answerType: 'indicator',

    kpiCards: [

      { label: '在管较大及以上', value: 8, unit: '处', color: 'orange', meaning: '需现场持续管控的风险点', statusText: '在管' },

      { label: '高风险点', value: 3, unit: '处', color: 'red', meaning: '优先督办对象', statusText: '重点' },

      { label: '已落实管控', value: 8, unit: '处', color: 'green', meaning: '均已配置管控措施', statusText: '受控中' },

    ],

    riskSectionTitle: '重点关注',

    riskItems: [

      { title: '高边坡作业风险', section: '一标段', status: '管控中' },

      { title: '临边防护完善', section: '二标段', status: '整改中' },

      { title: '特种设备检审跟踪', section: '三标段', status: '待复核' },

    ],

    dataBasis: {

      itemName: 'S02 安全风险台账',

      scope: '罗宜高速项目全线',

      updateTime: '2026-07-27 11:00',

      dataPeriod: '2026-07',

      verifyStatus: '已核验',

      stableId: 'DEMO-S02',

      sources: [{ name: 'S02安全风险台账', time: '2026-07', status: '已核验' }],

      caliber: '与首页 S02 指标保持一致',

    },

    nextActions: [

      { label: '查看三标段安全情况', question: '三个标段安全情况如何？' },

      { label: '上级安全检查备检', question: '上级安全检查常见核查项与现有台账缺口？' },

    ],

  },

}


