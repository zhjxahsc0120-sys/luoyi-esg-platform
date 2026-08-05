/** 标段展示统一：标段一 / 标段二 / …（兼容 TJ-1、一标段 等） */

const CN_ORD = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'] as const

function digitToCn(raw: string): string | null {
  if (/^[一二三四五六七八九十]+$/.test(raw)) return raw
  const n = Number(raw)
  if (Number.isFinite(n) && n >= 1 && n <= 10) return CN_ORD[n]
  return null
}

/** 规范为「标段X」；无法识别时原样兜底 */
export function formatSectionLabel(raw?: string | null): string {
  if (!raw) return '未分区'
  const s = String(raw).trim()
  if (!s) return '未分区'

  const tagged = s.match(/标段\s*([一二三四五六七八九十\d]+)/)
  if (tagged) {
    const ord = digitToCn(tagged[1])
    return ord ? `标段${ord}` : `标段${tagged[1]}`
  }

  const suffix = s.match(/^([一二三四五六七八九十\d]+)\s*标段$/)
  if (suffix) {
    const ord = digitToCn(suffix[1])
    return ord ? `标段${ord}` : `${suffix[1]}标段`
  }

  const tj = s.match(/(?:TJ-?|section-?)(\d+)/i)
  if (tj) {
    const ord = digitToCn(tj[1])
    if (ord) return `标段${ord}`
  }

  if (/^\d+$/.test(s)) {
    const ord = digitToCn(s)
    if (ord) return `标段${ord}`
  }

  return s.includes('标段') ? s : `${s}标段`
}

/** 从标题/位置文案中提取标段 */
export function extractSectionLabel(
  ...texts: Array<string | null | undefined>
): string | null {
  for (const text of texts) {
    if (!text) continue
    const hit = String(text).match(/标段[一二三四五六七八九十\d]+|TJ-?\d+(?:\s*标段)?/i)
    if (hit) return formatSectionLabel(hit[0])
  }
  return null
}

/** 去掉文案开头的标段前缀，避免与「类型 · 标段」行重复 */
export function stripSectionPrefix(text?: string | null): string {
  if (!text) return ''
  return String(text)
    .replace(/^\s*标段[一二三四五六七八九十\d]+\s*/u, '')
    .replace(/^\s*TJ-?\d+\s*标段?\s*/iu, '')
    .trim()
}

/** 列表首行：类型 · 标段 */
export function typeWithSection(typeLabel: string, section?: string | null): string {
  const sectionText = section || '未分区'
  const type = (typeLabel || '').trim() || '事项'
  return `${type} · ${sectionText}`
}
