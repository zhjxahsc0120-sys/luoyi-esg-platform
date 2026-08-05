import { chromium } from 'playwright-core'

const edge = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const browser = await chromium.launch({
  executablePath: edge,
  headless: true,
  args: ['--use-angle=swiftshader'],
})
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } })
const logs = []
page.on('console', (msg) => logs.push(`[${msg.type()}] ${msg.text()}`))
page.on('pageerror', (err) => logs.push(`[pageerror] ${err.message}`))
page.on('requestfailed', (req) => logs.push(`[reqfail] ${req.url()} ${req.failure()?.errorText}`))

await page.goto('http://127.0.0.1:5173/#/', { waitUntil: 'networkidle' })
await page.waitForTimeout(8000)
const html = await page.content()
const bodyText = await page.locator('body').innerText().catch(() => '')
console.log('TITLE', await page.title())
console.log('BODY_TEXT_LEN', bodyText.length)
console.log('BODY_SNIP', bodyText.slice(0, 500))
console.log('HAS_CESIUM', html.includes('cesium') || html.includes('traffic-gis'))
console.log('LOGS_COUNT', logs.length)
logs.slice(0, 40).forEach((l) => console.log(l))
await browser.close()
