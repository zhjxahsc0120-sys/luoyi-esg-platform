<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import type { RoutePoint } from '@/types/dashboard'

const store = useDashboardStore()
const hoverPoint = ref<RoutePoint | null>(null)
const mousePos = ref({ x: 0, y: 0 })

const statusColors: Record<string, string> = {
  normal: '#69e36f',
  warning: '#ffb347',
  risk: '#ff4f5e',
}

const pointColors: Record<string, string> = {
  compliance: '#2f9cff',
  carbon: '#69e36f',
  risk: '#ff4f5e',
  sensitive: '#ffb347',
  station: '#00e5ff',
}

const showRoute = computed(() => {
  const l = store.activeLayers
  return l.includes('all') || l.includes('section1') || l.includes('section2') || l.length === 0
})

const showEnvironment = computed(() => {
  return store.activeLayers.includes('environment')
})

const showRisk = computed(() => {
  return store.activeLayers.includes('risk')
})

const showUav = computed(() => {
  return store.activeLayers.includes('uav')
})

const visiblePoints = computed(() => {
  const layers = store.activeLayers
  const showAll = layers.includes('all') || layers.length === 0
  return store.points.filter((p) => {
    if (p.type === 'station') return showAll || layers.includes('section1') || layers.includes('section2')
    if (p.type === 'carbon') return showEnvironment.value
    if (p.type === 'sensitive') return showEnvironment.value
    if (p.type === 'risk') return showRisk.value
    if (p.type === 'compliance') return showAll || layers.includes('section1') || layers.includes('section2')
    return false
  })
})

function pathFromPoints(points: [number, number][]) {
  if (points.length === 0) return ''
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0]} ${p[1]}`).join(' ')
}

function onPointEnter(point: RoutePoint, e: MouseEvent) {
  hoverPoint.value = point
  updateMouse(e)
}

function onPointMove(e: MouseEvent) {
  updateMouse(e)
}

function onPointLeave() {
  hoverPoint.value = null
}

function updateMouse(e: MouseEvent) {
  const rect = (e.currentTarget as SVGGElement)?.closest('svg')?.getBoundingClientRect()
  if (!rect) return
  mousePos.value = {
    x: ((e.clientX - rect.left) / rect.width) * 100,
    y: ((e.clientY - rect.top) / rect.height) * 100,
  }
}
</script>

<template>
  <div class="gis-map-wrapper">
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" style="width: 100%; height: 100%;">
      <defs>
        <pattern id="terrainGrid" width="4" height="4" patternUnits="userSpaceOnUse">
          <path d="M 4 0 L 0 0 0 4" fill="none" stroke="rgba(0,174,255,0.04)" stroke-width="0.08" />
        </pattern>

        <pattern id="noise" width="100" height="100" patternUnits="userSpaceOnUse">
          <circle cx="20" cy="30" r="0.3" fill="rgba(255,255,255,0.03)" />
          <circle cx="60" cy="45" r="0.2" fill="rgba(255,255,255,0.02)" />
          <circle cx="80" cy="70" r="0.25" fill="rgba(255,255,255,0.025)" />
          <circle cx="45" cy="85" r="0.35" fill="rgba(255,255,255,0.02)" />
          <circle cx="15" cy="65" r="0.2" fill="rgba(255,255,255,0.03)" />
          <circle cx="70" cy="20" r="0.15" fill="rgba(255,255,255,0.02)" />
        </pattern>

        <radialGradient id="mapGlow" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stop-color="#0d2d4a" stop-opacity="0.95" />
          <stop offset="40%" stop-color="#071a30" stop-opacity="0.8" />
          <stop offset="75%" stop-color="#041224" stop-opacity="0.5" />
          <stop offset="100%" stop-color="#020b18" stop-opacity="0" />
        </radialGradient>

        <linearGradient id="routeGlowGreen" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#69e36f" stop-opacity="0" />
          <stop offset="50%" stop-color="#69e36f" stop-opacity="1" />
          <stop offset="100%" stop-color="#69e36f" stop-opacity="0" />
        </linearGradient>

        <linearGradient id="routeGlowCyan" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0" />
          <stop offset="50%" stop-color="#00e5ff" stop-opacity="1" />
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0" />
        </linearGradient>

        <filter id="strongGlow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="0.8" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        <filter id="softBlur">
          <feGaussianBlur stdDeviation="0.5" />
        </filter>

        <radialGradient id="radarGradient" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.35" />
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0" />
        </radialGradient>

        <pattern id="diagonalHatch" width="3" height="3" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
          <line x1="0" y1="0" x2="0" y2="3" stroke="#ffb347" stroke-width="0.5" stroke-opacity="0.5" />
        </pattern>

        <radialGradient id="riskGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#ff4f5e" stop-opacity="0.5" />
          <stop offset="100%" stop-color="#ff4f5e" stop-opacity="0" />
        </radialGradient>
      </defs>

      <rect width="100" height="100" fill="url(#mapGlow)" />
      <rect width="100" height="100" fill="url(#terrainGrid)" />
      <rect width="100" height="100" fill="url(#noise)" />

      <g class="terrain-contours">
        <path d="M 0 85 Q 25 78 50 82 T 100 76 L 100 100 L 0 100 Z" fill="rgba(20,50,40,0.15)" />
        <path d="M 0 72 Q 30 65 60 68 T 100 62 L 100 100 L 0 100 Z" fill="rgba(25,60,50,0.1)" />
        <path d="M 0 58 Q 20 52 45 56 T 85 50" fill="none" stroke="rgba(105,227,111,0.06)" stroke-width="0.15" />
        <path d="M 0 45 Q 35 38 65 42 T 100 36" fill="none" stroke="rgba(105,227,111,0.05)" stroke-width="0.12" />
        <path d="M 10 28 Q 40 22 70 26" fill="none" stroke="rgba(105,227,111,0.04)" stroke-width="0.1" />
      </g>

      <g class="river-lines">
        <path d="M 5 55 Q 25 50 45 54 T 80 48 T 100 52" fill="none" stroke="rgba(47,156,255,0.12)" stroke-width="0.3" />
        <path d="M 20 70 Q 40 65 60 68 T 90 62" fill="none" stroke="rgba(47,156,255,0.08)" stroke-width="0.2" />
      </g>

      <g v-if="showUav" class="uav-terrain">
        <path
          d="M 0 70 Q 15 55 28 62 T 55 50 T 80 58 T 100 48 L 100 100 L 0 100 Z"
          fill="rgba(30,60,40,0.25)"
          stroke="rgba(105,227,111,0.15)"
          stroke-width="0.15"
        />
        <path
          d="M 0 78 Q 20 68 38 74 T 70 64 T 100 70 L 100 100 L 0 100 Z"
          fill="rgba(20,50,35,0.2)"
        />
        <path
          d="M 10 30 Q 30 22 50 28 T 90 24"
          fill="none"
          stroke="rgba(105,227,111,0.12)"
          stroke-width="0.2"
          stroke-dasharray="1 1.5"
        />
        <path
          d="M 5 45 Q 25 38 48 44 T 85 40"
          fill="none"
          stroke="rgba(105,227,111,0.1)"
          stroke-width="0.15"
          stroke-dasharray="0.8 1.2"
        />
      </g>

      <g class="admin-boundaries">
        <path
          d="M 8 15 Q 25 8 45 14 T 85 10 T 98 20"
          fill="none"
          stroke="rgba(47,156,255,0.25)"
          stroke-width="0.25"
          stroke-dasharray="1.5 1"
        />
        <path
          d="M 5 35 Q 20 28 40 34 T 75 30 T 95 40"
          fill="none"
          stroke="rgba(47,156,255,0.2)"
          stroke-width="0.2"
          stroke-dasharray="1.2 1"
        />
        <path
          d="M 10 60 Q 30 52 55 58 T 92 55"
          fill="none"
          stroke="rgba(47,156,255,0.18)"
          stroke-width="0.2"
          stroke-dasharray="1 1.2"
        />
        <text x="15" y="20" fill="rgba(143,169,200,0.35)" font-size="2">武穴市</text>
        <text x="55" y="28" fill="rgba(143,169,200,0.3)" font-size="1.8">蕲春县</text>
        <text x="70" y="62" fill="rgba(143,169,200,0.3)" font-size="1.8">黄梅县</text>
      </g>

      <g v-if="showEnvironment" class="sensitive-areas">
        <polygon
          v-for="area in store.areas"
          :key="area.id"
          :points="area.polygon.map((p) => p.join(',')).join(' ')"
          fill="url(#diagonalHatch)"
          stroke="#ffb347"
          stroke-width="0.25"
          stroke-opacity="0.7"
        />
        <text
          v-for="area in store.areas"
          :key="'label-' + area.id"
          :x="area.polygon[0][0]"
          :y="area.polygon[0][1] - 1"
          fill="#ffb347"
          font-size="1.8"
          opacity="0.85"
        >
          {{ area.name }}
        </text>
      </g>

      <g v-if="showRisk" class="risk-zones">
        <circle cx="52" cy="38" r="5" fill="url(#riskGlow)" class="risk-pulse" />
        <circle cx="52" cy="38" r="2.5" fill="none" stroke="#ff4f5e" stroke-width="0.2" opacity="0.6" />
        <circle cx="72" cy="28" r="4" fill="url(#riskGlow)" class="risk-pulse" style="animation-delay: 1s" />
        <circle cx="72" cy="28" r="2" fill="none" stroke="#ff4f5e" stroke-width="0.15" opacity="0.5" />
      </g>

      <g v-if="showRoute" class="route-lines">
        <path
          v-for="(seg, idx) in store.segments"
          :key="'shadow-' + seg.id"
          :d="pathFromPoints(seg.points)"
          fill="none"
          :stroke="statusColors[seg.status]"
          stroke-width="2.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.12"
          filter="url(#softBlur)"
        />

        <path
          v-for="(seg, idx) in store.segments"
          :key="'outer-' + seg.id"
          :d="pathFromPoints(seg.points)"
          fill="none"
          :stroke="statusColors[seg.status]"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.25"
        />

        <path
          v-for="(seg, idx) in store.segments"
          :key="'main-' + seg.id"
          :d="pathFromPoints(seg.points)"
          fill="none"
          :stroke="statusColors[seg.status]"
          stroke-width="0.9"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.95"
          filter="url(#strongGlow)"
        />

        <path
          v-for="(seg, idx) in store.segments"
          :key="'flow-' + seg.id"
          :d="pathFromPoints(seg.points)"
          fill="none"
          stroke="#ffffff"
          stroke-width="0.3"
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-dasharray="2 6"
          class="route-flow"
          :style="{ animationDelay: idx * 0.3 + 's' }"
        />
      </g>

      <g v-if="showRoute" transform="translate(38, 45)">
        <circle r="5.5" fill="url(#radarGradient)" class="radar-pulse" />
        <circle r="3" fill="none" stroke="#00e5ff" stroke-width="0.25" opacity="0.7" class="radar-spin" />
        <circle r="1.3" fill="#00e5ff" filter="url(#strongGlow)" />
        <text y="-6.5" text-anchor="middle" fill="#00e5ff" font-size="1.8" opacity="0.9">项目中心</text>
      </g>

      <g v-if="showRoute" class="mileage-markers">
        <g transform="translate(12, 56)">
          <line y1="0" y2="2" x1="0" x2="0" stroke="#8fa9c8" stroke-width="0.15" opacity="0.5" />
          <text y="4" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="1.8">K12+000</text>
        </g>
        <g transform="translate(34, 44)">
          <line y1="0" y2="2" x1="0" x2="0" stroke="#8fa9c8" stroke-width="0.15" opacity="0.5" />
          <text y="4" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="1.8">K24+000</text>
        </g>
        <g transform="translate(58, 34)">
          <line y1="0" y2="2" x1="0" x2="0" stroke="#8fa9c8" stroke-width="0.15" opacity="0.5" />
          <text y="4" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="1.8">K48+000</text>
        </g>
        <g transform="translate(78, 26)">
          <line y1="0" y2="2" x1="0" x2="0" stroke="#8fa9c8" stroke-width="0.15" opacity="0.5" />
          <text y="4" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="1.8">K61+500</text>
        </g>
      </g>

      <g v-if="visiblePoints.length > 0" class="map-points">
        <g
          v-for="point in visiblePoints"
          :key="point.id"
          :transform="`translate(${point.x}, ${point.y})`"
          class="map-point"
          @mouseenter="onPointEnter(point, $event)"
          @mousemove="onPointMove($event)"
          @mouseleave="onPointLeave"
        >
          <circle v-if="point.type === 'station'" r="2" :fill="pointColors[point.type]" filter="url(#strongGlow)" />
          <circle v-else r="1.3" :fill="pointColors[point.type]" filter="url(#strongGlow)" />
          <circle v-if="point.type === 'station'" r="3.2" fill="none" :stroke="pointColors[point.type]" stroke-width="0.2" opacity="0.5" />
          <circle v-else r="2.2" fill="none" :stroke="pointColors[point.type]" stroke-width="0.15" opacity="0.4" />
        </g>
      </g>
    </svg>

    <div class="compass">
      <svg viewBox="0 0 40 40" width="100%" height="100%">
        <circle cx="20" cy="20" r="18" fill="none" stroke="rgba(143,169,200,0.3)" stroke-width="0.5" />
        <circle cx="20" cy="20" r="14" fill="none" stroke="rgba(143,169,200,0.2)" stroke-width="0.3" />
        <polygon points="20,5 23,18 20,16 17,18" fill="#ff4f5e" opacity="0.85" />
        <polygon points="20,35 23,22 20,24 17,22" fill="rgba(143,169,200,0.6)" />
        <text x="20" y="8" text-anchor="middle" fill="#e8f3ff" font-size="3.5" font-weight="bold">N</text>
        <text x="20" y="38" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="3">S</text>
        <text x="6" y="22" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="3">W</text>
        <text x="34" y="22" text-anchor="middle" fill="rgba(143,169,200,0.6)" font-size="3">E</text>
      </svg>
    </div>

    <div
      v-if="hoverPoint"
      class="gis-tooltip"
      :style="{ left: `${mousePos.x}%`, top: `${mousePos.y}%` }"
    >
      <div class="tooltip-name">{{ hoverPoint.name }}</div>
      <div class="tooltip-type">{{ hoverPoint.type }}</div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.gis-tooltip {
  position: absolute;
  transform: translate(-50%, -120%);
  background: rgba(2, 11, 24, 0.92);
  border: 1px solid var(--border-blue);
  border-radius: 4px;
  padding: 6px 10px;
  pointer-events: none;
  z-index: 20;
  font-size: 12px;
  box-shadow: 0 0 12px rgba(0, 174, 255, 0.25);
  white-space: nowrap;

  .tooltip-name {
    color: var(--text-main);
    font-weight: 600;
  }

  .tooltip-type {
    color: var(--text-muted);
    font-size: 11px;
    margin-top: 2px;
    text-transform: capitalize;
  }
}

.map-point {
  cursor: pointer;
  transition: transform 0.2s ease;

  &:hover {
    transform: scale(1.4);
  }
}

.radar-pulse {
  animation: radarPulse 2.5s ease-out infinite;
  transform-origin: center;
}

.radar-spin {
  animation: radarSpin 6s linear infinite;
  transform-origin: center;
}

.route-flow {
  animation: flowDash 2.5s linear infinite;
}

.risk-pulse {
  animation: riskPulse 2s ease-out infinite;
  transform-origin: center;
}

@keyframes radarPulse {
  0% {
    transform: scale(0.5);
    opacity: 0.8;
  }
  100% {
    transform: scale(2.2);
    opacity: 0;
  }
}

@keyframes radarSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes flowDash {
  from {
    stroke-dashoffset: 0;
  }
  to {
    stroke-dashoffset: -16;
  }
}

@keyframes riskPulse {
  0% {
    transform: scale(0.6);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.8);
    opacity: 0;
  }
}

.compass {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 48px;
  height: 48px;
  z-index: 10;
  opacity: 0.85;
}
</style>
