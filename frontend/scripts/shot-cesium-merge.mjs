import { chromium } from 'playwright-core'
import path from 'path'
import fs from 'fs'

const edge = process.env.EDGE_PATH
  || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

const outDir = 'C:\\ESG_Project\\docs\\frontend'
fs.mkdirSync(outDir, { recursive: true })

const browser = await chromium.launch({
  executablePath: edge,
  headless: true,
  args: ['--disable-gpu-sandbox', '--use-angle=swiftshader'],
})

async function shot(url, filename, waitMs = 12000) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
  page.setDefaultTimeout(60000)
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(waitMs)
  const out = path.join(outDir, filename)
  await page.screenshot({ path: out, fullPage: false })
  const st = fs.statSync(out)
  console.log(`OK ${filename} bytes=${st.size}`)
  await page.close()
}

try {
  await shot('http://127.0.0.1:5173/#/', 'cesium_map_merge_homepage_20260805.png', 15000)
  await shot('http://127.0.0.1:5173/#/gis-preview', 'cesium_map_merge_gis_preview_20260805.png', 15000)
} catch (e) {
  console.error('SHOT_FAIL', e)
  process.exitCode = 1
} finally {
  await browser.close()
}
