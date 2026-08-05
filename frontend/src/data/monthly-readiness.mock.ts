import type { MonthlyReadiness } from '@/types/monthly-report'

export const monthlyReadinessMock: MonthlyReadiness = {
  metricName: '月报资料归集率',
  reportPeriod: '2026-07',
  numerator: 18,
  denominator: 22,
  exactProgress: 81.8,
  progress: 82,
  deadlineStart: '2026-08-02',
  deadlineEnd: '2026-08-05',
  statusCounts: {
    待提交: 1,
    待确认: 1,
    待补正: 2,
    校验通过: 18,
    '不适用（已确认）': 0,
  },
  exceptionTasks: [
    {
      taskCode: 'MR-G-007',
      taskName: '合规资料补齐材料',
      responsibleUnit: '缺口责任单位',
      deadline: '2026-08-05',
      monthlyStatus: '待提交',
    },
    {
      taskCode: 'MR-G-011',
      taskName: '资料目录台账及档案检查记录',
      responsibleUnit: '档案/工程管理部门',
      deadline: '2026-08-04',
      monthlyStatus: '待确认',
    },
    {
      taskCode: 'MR-E-010',
      taskName: '月度工程计量资料',
      responsibleUnit: '工程/计量部门',
      deadline: '2026-08-04',
      monthlyStatus: '待补正',
    },
    {
      taskCode: 'MR-G-004',
      taskName: '许可证及许可变更文件有效性确认',
      responsibleUnit: '许可责任部门',
      deadline: '2026-08-04',
      monthlyStatus: '待补正',
    },
  ],
}

export function createMonthlyReadinessMock(): MonthlyReadiness {
  return {
    ...monthlyReadinessMock,
    statusCounts: { ...monthlyReadinessMock.statusCounts },
    exceptionTasks: monthlyReadinessMock.exceptionTasks.map((task) => ({ ...task })),
  }
}
