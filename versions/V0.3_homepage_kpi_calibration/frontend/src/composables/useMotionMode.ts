// ─────────────────────────────────────────────
// 母版动画模式控制（/ui-master/dashboard 专用）
// motion=off 或 prefers-reduced-motion: reduce 时关闭所有动画
// ─────────────────────────────────────────────

import { ref } from 'vue'

/** 全局动画关闭标志，所有母版组件共享 */
export const motionOff = ref(false)

let _initialized = false

function detectMotionOff(): boolean {
  // 1. URL query: motion=off
  //    hash router → #/ui-master/dashboard?motion=off
  //    也兼容常规 search params
  const hash = window.location.hash || ''
  const qIdx = hash.indexOf('?')
  if (qIdx >= 0) {
    const params = new URLSearchParams(hash.slice(qIdx + 1))
    if (params.get('motion') === 'off') return true
  }
  if (new URLSearchParams(window.location.search).get('motion') === 'off') {
    return true
  }

  // 2. prefers-reduced-motion: reduce
  if (
    typeof window.matchMedia === 'function' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    return true
  }

  return false
}

/** 在页面 setup 中调用一次，初始化全局动画模式 */
export function initMotionMode(): void {
  if (_initialized) return
  _initialized = true
  motionOff.value = detectMotionOff()
}
