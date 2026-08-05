/// <reference types="vite/client" />

declare const CESIUM_BASE_URL: string

interface ImportMetaEnv {
  readonly VITE_TRAFFIC_API_BASE?: string
  readonly VITE_TRAFFIC_BASEMAP_URL?: string
  readonly VITE_TRAFFIC_TERRAIN_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
