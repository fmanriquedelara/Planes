import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';

const uncapped = process.argv.includes('--uncapped');
const flags = ['--enable-webgl', '--ignore-gpu-blocklist', '--use-angle=d3d11'];
if (uncapped) flags.push('--disable-frame-rate-limit', '--disable-gpu-vsync');
const browser = await chromium.launch({ headless: true, channel: 'chrome', args: flags });
const results = [];
const errors = [];
await mkdir('artifacts', { recursive: true });
try {
  for (const test of [
    { quality: 'high', width: 1920, height: 1080 },
    { quality: 'performance', width: 1920, height: 1080 },
    { quality: 'performance', width: 3840, height: 2160 },
  ]) {
    const page = await browser.newPage({ viewport: { width: test.width, height: test.height }, deviceScaleFactor: 1 });
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(`http://127.0.0.1:5174/?capture=1&quality=${test.quality}`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.__flightTest?.ready);
    // Flying workload, not only a cheap frozen screenshot. Same weather/cover.
    await page.evaluate(() => window.__flightTest.pause(false));
    await page.waitForTimeout(test.width > 1920 ? 12000 : 6500);
    const result = await page.evaluate(async () => {
      const samples = [], scales = [];
      window.__flightTest.beginTimingCapture();
      const start = performance.now(); let previous = null;
      await new Promise(resolve => {
        function tick(now) {
          if (previous !== null && now > previous) samples.push(now - previous);
          previous = now;
          scales.push(window.__flightTest.getPixelRatio());
          if (now - start < 9000) requestAnimationFrame(tick); else resolve();
        }
        requestAnimationFrame(tick);
      });
      const raw = window.__flightTest.endTimingCapture();
      const cpu = raw.filter(sample => sample.kind === 'cpu').map(sample => sample.ms);
      const gpu = raw.filter(sample => sample.kind === 'gpu').map(sample => sample.ms);
      const mean = list => list.length ? list.reduce((a,b)=>a+b,0)/list.length : null;
      const percentile = (list,p) => list.length ? [...list].sort((a,b)=>a-b)[Math.min(list.length-1,Math.floor(list.length*p))] : null;
      const overBudget = list => list.length ? list.filter(value => value > 1000/120).length / list.length * 100 : null;
      const gl = document.querySelector('canvas').getContext('webgl2');
      const debug = gl.getExtension('WEBGL_debug_renderer_info');
      return {
        frames: samples.length, durationMs: performance.now()-start,
        meanFrameMs: mean(samples), p95FrameMs: percentile(samples,.95), p99FrameMs: percentile(samples,.99), maxFrameMs: Math.max(...samples), frameIntervalsOverBudgetPercent: overBudget(samples),
        observedHeadlessFPS: 1000/mean(samples),
        cpuActiveMeanMs: mean(cpu), cpuActiveP95Ms: percentile(cpu,.95), gpuDrawMeanMs: mean(gpu), gpuDrawP95Ms: percentile(gpu,.95), gpuDrawP99Ms: percentile(gpu,.99), gpuSamplesOverBudgetPercent: overBudget(gpu), cpuSampleCount: cpu.length, gpuSampleCount: gpu.length,
        minPixelRatio: Math.min(...scales), maxPixelRatio: Math.max(...scales),
        gpu: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : 'Unavailable',
        finalState: window.__flightTest.state,
      };
    });
    await page.screenshot({ path: `artifacts/benchmark-${test.quality}-${test.width}.png` });
    results.push({ ...test, ...result });
    console.log(JSON.stringify({ quality: test.quality, resolution: `${test.width}x${test.height}`, fps: result.observedHeadlessFPS, gpuMs: result.gpuDrawMeanMs, cpuMs: result.cpuActiveMeanMs, scale: result.finalState.pixelRatio }));
    await page.close();
  }
  const report = {
    mode: uncapped ? 'uncapped headless throughput; NOT physical display refresh' : 'normal headless scheduling; NOT physical display refresh',
    browser: await browser.version(), flags, targetBudgetMs: 1000/120, results, errors,
    limits: 'Short local flying runs on this GPU only. Not a sustained native 120 Hz display test. CPU active update/render and GPU measurements overlap and must not be added together. Raw GPU/CPU samples collected once each, not averages of rolling estimates. Warm-up/disjoint periods are excluded from draw timings but remain in frame intervals.',
  };
  const path = `artifacts/benchmark-${uncapped ? 'uncapped' : 'normal'}.json`;
  await writeFile(path, JSON.stringify(report, null, 2));
  console.log(path);
  if (errors.length) { console.error(errors); process.exitCode = 1; }
} finally { await browser.close(); }
