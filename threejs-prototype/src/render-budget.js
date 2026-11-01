const average = values => values.length ? values.reduce((sum, x) => sum + x, 0) / values.length : null;
const percentile = (values, p) => values.length ? [...values].sort((a, b) => a - b)[Math.min(values.length - 1, Math.floor(values.length * p))] : null;

export class RenderBudget {
  constructor(gl, onScale) {
    this.gl = gl;
    this.ext = gl.getExtension('EXT_disjoint_timer_query_webgl2');
    this.onScale = onScale;
    this.pending = [];
    this.active = null;
    this.cpu = []; this.gpu = []; this.intervals = [];
    this.targetFPS = 120;
    this.captureSamples = false;
    this.records = [];
    this.enabled = false;
    this.scale = 1;
    this.lastAdjustment = performance.now();
    this.warmUntil = performance.now() + 5000;
  }
  configure(enabled, scale) {
    this.enabled = enabled; this.scale = scale;
    this.cpu.length = this.gpu.length = this.intervals.length = 0;
    this.warmUntil = performance.now() + 3500;
    this.lastAdjustment = performance.now();
    this.clearQueries();
  }
  push(list, value) {
    if (Number.isFinite(value) && value >= 0) {
      list.push(value); if (list.length > 180) list.shift();
      if (this.captureSamples && (list === this.cpu || list === this.gpu)) this.records.push({ kind: list === this.gpu ? 'gpu' : 'cpu', ms: value });
    }
  }
  beginCapture() { this.records.length = 0; this.captureSamples = true; }
  endCapture() { this.captureSamples = false; return this.records.splice(0); }
  begin() {
    const { gl, ext } = this;
    if (!ext) return;
    if (gl.getParameter(ext.GPU_DISJOINT_EXT)) { this.clearQueries(); return; }
    while (this.pending.length && gl.getQueryParameter(this.pending[0], gl.QUERY_RESULT_AVAILABLE)) {
      const query = this.pending.shift();
      if (performance.now() > this.warmUntil) this.push(this.gpu, gl.getQueryParameter(query, gl.QUERY_RESULT) / 1e6);
      gl.deleteQuery(query);
    }
    if (this.pending.length >= 8) return;
    this.active = gl.createQuery();
    gl.beginQuery(ext.TIME_ELAPSED_EXT, this.active);
  }
  end(cpuMs, intervalMs) {
    if (this.active) {
      this.gl.endQuery(this.ext.TIME_ELAPSED_EXT);
      this.pending.push(this.active); this.active = null;
    }
    const now = performance.now();
    if (now < this.warmUntil || document.hidden) return;
    this.push(this.cpu, cpuMs);
    this.push(this.intervals, intervalMs);
    if (!this.enabled || now - this.lastAdjustment < 1500 || this.cpu.length < 45) return;
    // ANGLE may publish timer results slowly. Waiting for 30 results can leave
    // a heavy 4K workload at native resolution for many seconds.
    if (this.ext && this.gpu.length < 6) return;
    // Never infer GPU load from rAF: a 60 Hz display alone produces 16.7 ms
    // callbacks. Prefer asynchronous GPU timing, with active CPU work as fallback.
    const measured = this.ext ? percentile(this.gpu, .65) : average(this.cpu);
    let next = this.scale;
    if (measured > 7.8) next = Math.max(.6, this.scale - .2, this.scale * Math.sqrt(7 / measured));
    else if (measured < 5.4) next = Math.min(Math.min(devicePixelRatio, 1), this.scale + .05);
    this.lastAdjustment = now;
    if (Math.abs(next - this.scale) > .005) {
      this.scale = Math.round(next * 100) / 100;
      this.onScale(this.scale);
      this.cpu.length = this.gpu.length = this.intervals.length = 0;
      this.warmUntil = now + 1000;
    }
  }
  snapshot() {
    return {
      targetFPS: this.enabled ? this.targetFPS : null,
      adaptive: this.enabled, scale: this.scale, minScale: .6,
      measurement: this.ext ? 'asynchronous GPU timer + active CPU work' : 'active CPU work only; GPU timer unavailable',
      cpuMeanMs: average(this.cpu), cpuP95Ms: percentile(this.cpu, .95),
      gpuMeanMs: average(this.gpu), gpuP95Ms: percentile(this.gpu, .95),
      frameMeanMs: average(this.intervals), frameP95Ms: percentile(this.intervals, .95),
      cpuSamples: this.cpu.length, gpuSamples: this.gpu.length,
    };
  }
  clearQueries() {
    if (this.active) { this.gl.endQuery(this.ext.TIME_ELAPSED_EXT); this.gl.deleteQuery(this.active); this.active = null; }
    for (const query of this.pending) this.gl.deleteQuery(query);
    this.pending.length = 0;
  }
}
