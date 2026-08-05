export const gisConfig = {
  /**
   * useRealGisOnDashboard:
   * true  = 首页默认采用 Cesium 在线底图 + 业务图层；
   * false = 应急回退到原 SVG 示意地图。
   *
   * 当前策略：
   * - 领导首页正式采用 Cesium 在线加载模式；
   * - SVG 仅作为应急回退入口保留，不作为默认底图；
   * - dashboardDataMode 默认使用 api，后端不可用时再由组件/页面 fallback。
   */
  useRealGisOnDashboard: true,
  dashboardDataMode: 'api' as 'mock' | 'shp' | 'api',
  projectId: 'LUOYI-ESG',
}
