import type { MonthlyReadiness, MonthlyReadinessStatus } from '@/types/monthly-report'

const MONTHLY_READINESS_STATUSES: MonthlyReadinessStatus[] = [
  '待提交',
  '待确认',
  '待补正',
  '校验通过',
  '不适用（已确认）',
]

export function validateMonthlyReadiness(data: MonthlyReadiness): string[] {
  const errors: string[] = []
  const calculatedExact = data.denominator > 0
    ? data.numerator / data.denominator * 100
    : 0
  const statusTotal = MONTHLY_READINESS_STATUSES.reduce(
    (total, status) => total + data.statusCounts[status],
    0,
  )
  const nonPassedTotal = statusTotal - data.statusCounts['校验通过']

  if (data.numerator > data.denominator) {
    errors.push(`numerator(${data.numerator})不得大于denominator(${data.denominator})`)
  }
  if (data.progress !== Math.round(calculatedExact)) {
    errors.push(`progress(${data.progress})与计算值(${Math.round(calculatedExact)})不一致`)
  }
  if (Math.abs(data.exactProgress - calculatedExact) > 0.1000001) {
    errors.push(`exactProgress(${data.exactProgress})与计算值(${calculatedExact.toFixed(1)})误差超过0.1`)
  }
  if (statusTotal !== 22) {
    errors.push(`statusCounts总数应为22，当前为${statusTotal}`)
  }
  if (nonPassedTotal !== data.exceptionTasks.length) {
    errors.push(`非校验通过状态数(${nonPassedTotal})与exceptionTasks数量(${data.exceptionTasks.length})不一致`)
  }
  if (data.deadlineStart > data.deadlineEnd) {
    errors.push(`deadlineStart(${data.deadlineStart})不得晚于deadlineEnd(${data.deadlineEnd})`)
  }
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(data.reportPeriod)) {
    errors.push(`reportPeriod(${data.reportPeriod})必须为YYYY-MM格式`)
  }

  return errors
}
