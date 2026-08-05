<script setup lang="ts">
import { Layers, Camera, Scale } from 'lucide-vue-next'
</script>

<template>
  <div class="satellite-compare-card">
    <div class="compare-title">卫星 / 无人机时序影像对比</div>
    <div class="compare-images">
      <div class="compare-image before">
        <div class="terrain-bg">
          <svg viewBox="0 0 100 60" preserveAspectRatio="none" style="width:100%;height:100%;">
            <defs>
              <linearGradient id="skyBefore" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#3a4a3a" />
                <stop offset="100%" stop-color="#2a3528" />
              </linearGradient>
            </defs>
            <rect width="100" height="60" fill="url(#skyBefore)" />
            <path d="M0 35 Q20 28 40 33 T80 30 T100 36 L100 60 L0 60 Z" fill="#4a5a3a" opacity="0.7" />
            <path d="M0 45 Q25 38 50 43 T100 40 L100 60 L0 60 Z" fill="#3d4a2e" opacity="0.8" />
            <path d="M10 32 L90 30" stroke="#6b5a3a" stroke-width="1.5" opacity="0.6" />
            <path d="M15 45 L85 42" stroke="#5a4a2a" stroke-width="1" opacity="0.5" />
            <circle cx="30" cy="38" r="2" fill="#6b5a3a" opacity="0.6" />
            <circle cx="65" cy="35" r="2.5" fill="#6b5a3a" opacity="0.6" />
            <circle cx="50" cy="48" r="3" fill="#5a4a2a" opacity="0.5" />
            <path d="M20 50 Q40 48 60 52 T100 50" stroke="#4a5a3a" stroke-width="0.5" opacity="0.6" fill="none" />
          </svg>
        </div>
        <span class="compare-label">施工前 2026-03</span>
      </div>
      <div class="compare-image after">
        <div class="terrain-bg">
          <svg viewBox="0 0 100 60" preserveAspectRatio="none" style="width:100%;height:100%;">
            <defs>
              <linearGradient id="skyAfter" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#2d4a5a" />
                <stop offset="100%" stop-color="#1e3540" />
              </linearGradient>
            </defs>
            <rect width="100" height="60" fill="url(#skyAfter)" />
            <path d="M0 35 Q20 28 40 33 T80 30 T100 36 L100 60 L0 60 Z" fill="#3a5a6a" opacity="0.5" />
            <path d="M0 45 Q25 38 50 43 T100 40 L100 60 L0 60 Z" fill="#2d4a5a" opacity="0.6" />
            <path d="M8 32 L92 30" stroke="#69e36f" stroke-width="1.8" opacity="0.85" filter="drop-shadow(0 0 1px #69e36f)" />
            <path d="M12 46 L88 43" stroke="#00e5ff" stroke-width="1.2" opacity="0.7" filter="drop-shadow(0 0 1px #00e5ff)" />
            <circle cx="30" cy="37" r="2.5" fill="#00e5ff" opacity="0.7" filter="drop-shadow(0 0 2px #00e5ff)" />
            <circle cx="65" cy="34" r="3" fill="#69e36f" opacity="0.7" filter="drop-shadow(0 0 2px #69e36f)" />
            <circle cx="50" cy="47" r="3.5" fill="#2f9cff" opacity="0.6" filter="drop-shadow(0 0 2px #2f9cff)" />
            <path d="M20 50 Q40 48 60 52 T100 50" stroke="#69e36f" stroke-width="0.4" opacity="0.5" fill="none" />
            <rect x="45" y="27" width="10" height="4" fill="#00e5ff" opacity="0.35" rx="0.5" />
            <rect x="70" y="40" width="8" height="3" fill="#69e36f" opacity="0.3" rx="0.5" />
          </svg>
        </div>
        <span class="compare-label">施工后 2026-06</span>
      </div>
    </div>
    <div class="compare-controls">
      <div class="ctrl-item"><Layers :size="12" /><span>图层</span></div>
      <div class="ctrl-item"><Camera :size="12" /><span>影像</span></div>
      <div class="ctrl-item"><Scale :size="12" /><span>对比</span></div>
      <div class="ctrl-slider">
        <span>透明度</span>
        <input type="range" min="0" max="100" value="60" />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.satellite-compare-card {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 280px;
  background: rgba(2, 11, 24, 0.88);
  border: 1px solid var(--border-blue-dim);
  border-radius: var(--panel-radius);
  padding: 8px 10px;
  z-index: 10;
  backdrop-filter: blur(4px);

  .compare-title {
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 6px;
    color: var(--text-main);
    letter-spacing: 1px;
  }

  .compare-images {
    display: flex;
    gap: 6px;
    margin-bottom: 6px;

    .compare-image {
      flex: 1;
      height: 72px;
      border-radius: 4px;
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.08);

      .terrain-bg {
        width: 100%;
        height: 100%;
      }

      .compare-label {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 2px 4px;
        font-size: 10px;
        color: #fff;
        background: rgba(0, 0, 0, 0.55);
        text-align: center;
      }

      &.before {
        .terrain-bg {
          filter: saturate(0.7) brightness(0.85);
        }
      }

      &.after {
        .terrain-bg {
          filter: saturate(1.1) brightness(0.95);
        }
      }
    }
  }

  .compare-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 10px;
    color: var(--text-muted);
    gap: 4px;

    .ctrl-item {
      display: flex;
      align-items: center;
      gap: 3px;
      opacity: 0.7;
    }

    .ctrl-slider {
      display: flex;
      align-items: center;
      gap: 4px;
      margin-left: auto;

      input[type='range'] {
        width: 50px;
        height: 3px;
        appearance: none;
        background: rgba(143, 169, 200, 0.25);
        border-radius: 2px;
        outline: none;

        &::-webkit-slider-thumb {
          appearance: none;
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: var(--cyan);
          box-shadow: 0 0 4px var(--cyan);
          cursor: pointer;
        }
      }
    }
  }
}
</style>
