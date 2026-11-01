import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

// Install Playwright locally, or point PLAYWRIGHT_MODULE at an existing package.
const { chromium } = process.env.PLAYWRIGHT_MODULE
  ? await import(pathToFileURL(resolve(process.env.PLAYWRIGHT_MODULE)).href)
  : await import('playwright');
const url = process.argv[2] || 'http://127.0.0.1:5174/?capture=1';
const output = resolve(process.argv[3] || 'artifacts/prototype.png');
await mkdir(dirname(output), { recursive: true });
const errors = [], warnings = [];
const browser = await chromium.launch({
  headless: true,
  channel: process.env.CHROME_PATH ? undefined : 'chrome',
  executablePath: process.env.CHROME_PATH || undefined,
  args: ['--enable-webgl', '--ignore-gpu-blocklist', '--use-angle=d3d11', '--no-first-run'],
});
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
    if (message.type() === 'warning') warnings.push(message.text());
  });
  page.on('requestfailed', (request) => errors.push(`${request.url()}: ${request.failure()?.errorText}`));
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForFunction(() => window.__flightTest?.ready || document.querySelector('#error:not([hidden])'), { timeout: 60000 });
  await page.waitForTimeout(1800);
  const status = await page.evaluate(() => ({ ready: window.__flightTest?.ready, state: window.__flightTest?.state, sightline: window.__flightTest?.pick(), error: document.querySelector('#error:not([hidden])')?.textContent }));
  await page.screenshot({ path: output, fullPage: false });
  await writeFile(output.replace(/\.png$/i, '.json'), JSON.stringify({ url, browser: await browser.version(), resolution: [1600, 1000], ...status, errors, warnings }, null, 2));
  console.log(JSON.stringify({ image: output, ...status, errors, warnings }, null, 2));
  if (!status.ready || errors.length) process.exitCode = 1;
} finally {
  await browser.close();
}
