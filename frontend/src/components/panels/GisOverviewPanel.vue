<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import PanelCard from '@/components/layout/PanelCard.vue'
import { MapPin, Crosshair, ZoomIn, ZoomOut, Maximize2, RotateCcw } from 'lucide-vue-next'

const mapContainer = ref<HTMLDivElement | null>(null)
const zoom = ref(12)

function zoomIn() {
  zoom.value++
}

function zoomOut() {
  zoom.value = Math.max(8, zoom.value - 1)
}

function resetView() {
  zoom.value = 12
}

function fullscreen() {
  if (mapContainer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      mapContainer.value.requestFullscreen()
    }
  }
}

onMounted(() => {
})

onUnmounted(() => {
})
</script>

<template>
  <PanelCard title="项目现场一张图" :icon="MapPin" theme="g">
    <div class="gis-panel-content">
      <div ref="mapContainer" class="map-container">
        <div class="map-overlay">
          <div class="map-grid" />
          <div class="map-center-marker">
            <Crosshair class="marker-icon" />
          </div>
        </div>
        <div class="map-controls">
          <button class="control-btn" @click="zoomIn" title="放大">
            <ZoomIn class="control-icon" />
          </button>
          <div class="zoom-display">{{ zoom }}</div>
          <button class="control-btn" @click="zoomOut" title="缩小">
            <ZoomOut class="control-icon" />
          </button>
          <div class="control-divider" />
          <button class="control-btn" @click="resetView" title="重置视角">
            <RotateCcw class="control-icon" />
          </button>
          <button class="control-btn" @click="fullscreen" title="全屏">
            <Maximize2 class="control-icon" />
          </button>
        </div>
        <div class="map-legend">
          <div class="legend-item">
            <div class="legend-dot" style="background: var(--green)" />
            <span>已完成</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot" style="background: var(--cyan)" />
            <span>进行中</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot" style="background: var(--amber)" />
            <span>待开工</span>
          </div>
          <div class="legend-item">
            <div class="legend-dot" style="background: var(--red)" />
            <span>风险区</span>
          </div>
        </div>
        <div class="map-stats">
          <div class="stat-item">
            <span class="stat-label">路段长度</span>
            <span class="stat-value">45.8 km</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">桥梁数量</span>
            <span class="stat-value">12 座</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">隧道数量</span>
            <span class="stat-value">3 座</span>
          </div>
        </div>
      </div>
    </div>
  </PanelCard>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.gis-panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;

  .map-container {
    flex: 1;
    border-radius: 6px;
    background: var(--bg-card);
    border: 1px solid var(--border-faint);
    position: relative;
    overflow: hidden;
    min-height: 300px;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--cyan), transparent);
      opacity: 0;
      transition: opacity 0.3s ease;
    }

    &:hover::before {
      opacity: 1;
    }

    .map-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(8, 40, 69, 0.3) 0%, rgba(8, 40, 69, 0.8) 100%);

      .map-grid {
        position: absolute;
        inset: 0;
        background-image:
          linear-gradient(rgba(37, 185, 255, 0.1) 1px, transparent 1px),
          linear-gradient(90deg, rgba(37, 185, 255, 0.1) 1px, transparent 1px);
        background-size: 40px 40px;
        animation: gridMove 20s linear infinite;
      }

      .map-center-marker {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;

        .marker-icon {
          width: 32px;
          height: 32px;
          color: var(--cyan);
          filter: drop-shadow(0 0 10px var(--cyan));
          animation: pulse 3s ease-in-out infinite;
        }
      }
    }

    .map-controls {
      position: absolute;
      top: 10px;
      right: 10px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      background: rgba(8, 40, 69, 0.9);
      border-radius: 6px;
      padding: 6px;
      border: 1px solid var(--border-faint);

      .control-btn {
        width: 32px;
        height: 32px;
        border: none;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.05);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;

        &:hover {
          background: rgba(37, 185, 255, 0.2);
          border-color: var(--border-glow-cyan);
        }

        .control-icon {
          width: 16px;
          height: 16px;
          color: var(--text-secondary);
        }
      }

      .zoom-display {
        font-size: var(--fs-caption);
        color: var(--text-muted);
        text-align: center;
        padding: 4px 0;
        font-family: var(--font-num);
      }

      .control-divider {
        height: 1px;
        background: var(--border-faint);
        margin: 4px 0;
      }
    }

    .map-legend {
      position: absolute;
      bottom: 10px;
      left: 10px;
      display: flex;
      gap: 16px;
      background: rgba(8, 40, 69, 0.9);
      border-radius: 6px;
      padding: 8px 12px;
      border: 1px solid var(--border-faint);

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: var(--fs-caption);
        color: var(--text-muted);

        .legend-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          box-shadow: 0 0 6px currentColor;
        }
      }
    }

    .map-stats {
      position: absolute;
      top: 10px;
      left: 10px;
      display: flex;
      gap: 16px;
      background: rgba(8, 40, 69, 0.9);
      border-radius: 6px;
      padding: 10px 16px;
      border: 1px solid var(--border-faint);

      .stat-item {
        display: flex;
        flex-direction: column;
        gap: 2px;

        .stat-label {
          font-size: var(--fs-caption);
          color: var(--text-muted);
        }

        .stat-value {
          font-size: var(--fs-body);
          font-weight: 600;
          color: var(--cyan);
          font-family: var(--font-num);
          text-shadow: 0 0 8px rgba(37, 185, 255, 0.5);
        }
      }
    }
  }
}

@keyframes gridMove {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 40px 40px;
  }
}

@keyframes pulse {
  0%, 100% {
    filter: drop-shadow(0 0 10px var(--cyan));
    transform: scale(1);
  }
  50% {
    filter: drop-shadow(0 0 20px var(--cyan));
    transform: scale(1.1);
  }
}
</style>
