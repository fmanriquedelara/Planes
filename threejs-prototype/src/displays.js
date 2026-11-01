import * as THREE from 'three';

export function createFlightDisplay(mode = 0) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 512;
  const ctx = canvas.getContext('2d');
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.flipY = false;
  texture.anisotropy = 4;
  const material = new THREE.MeshBasicMaterial({ map: texture, color: '#a6d8a4', toneMapped: false });
  material.name = `Prototype live flight display ${mode}`;
  let lastUpdate = -Infinity;
  function update(time, flight = {}) {
    if (time - lastUpdate < .25 && time >= lastUpdate) return;
    lastUpdate = time;
    ctx.fillStyle = '#030b08'; ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#5baf7b'; ctx.fillStyle = '#79ce93'; ctx.lineWidth = 2;
    ctx.font = '17px monospace';
    ctx.fillText(mode % 2 ? 'FLIGHT / SYSTEMS' : 'NAV / ROUTE 01', 24, 30);
    ctx.fillStyle = '#3f7d58'; ctx.fillRect(23, 42, 466, 1);
    if (mode % 2 === 0) {
      ctx.save(); ctx.translate(256, 254);
      ctx.strokeStyle = '#234a33';
      for (let r = 65; r <= 205; r += 65) { ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.stroke(); }
      ctx.beginPath(); ctx.moveTo(-205, 0); ctx.lineTo(205, 0); ctx.moveTo(0, -205); ctx.lineTo(0, 205); ctx.stroke();
      ctx.strokeStyle = '#62976b'; ctx.lineWidth = 2;
      ctx.beginPath();
      for (let i = 0; i < 100; i++) { const y = -250 + i * 5; const x = Math.sin(i * .065 + time * .003) * 82 + i * .3; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); }
      ctx.stroke();
      ctx.strokeStyle = '#badc9b'; ctx.setLineDash([8, 7]); ctx.beginPath(); ctx.moveTo(0, 150); ctx.lineTo(44, -160); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = '#addeb2'; ctx.beginPath(); ctx.moveTo(0, -16); ctx.lineTo(12, 13); ctx.lineTo(0, 8); ctx.lineTo(-12, 13); ctx.closePath(); ctx.fill();
      ctx.restore();
      ctx.fillStyle = '#93c89c'; ctx.fillText('N', 249, 70); ctx.fillText('RNG  20 NM', 24, 474); ctx.fillText('WPT 03', 364, 474);
    } else {
      const speed = Math.round((flight.speed || 100) * 3.6);
      const altitude = Math.round(flight.position?.y || 1800);
      ctx.font = '22px monospace';
      [['AIR SPEED', `${speed} KM/H`], ['ALTITUDE', `${altitude} M`], ['FUEL', '2 450 KG'], ['ENGINE', '92.3 %'], ['TEMPERATURE', '640 C']].forEach(([label, value], i) => {
        ctx.fillStyle = '#47775b'; ctx.fillText(label, 28, 95 + i * 70); ctx.fillStyle = '#98d29b'; ctx.fillText(value, 293, 95 + i * 70);
        ctx.strokeStyle = '#173625'; ctx.strokeRect(28, 109 + i * 70, 450, 8); ctx.fillStyle = '#437556'; ctx.fillRect(30, 111 + i * 70, 280 + i * 15, 4);
      });
      ctx.font = '15px monospace'; ctx.fillStyle = '#7fac7d'; ctx.fillText('SYS NORM      FLIGHT STUDY', 28, 485);
    }
    texture.needsUpdate = true;
  }
  update(0);
  return { material, update };
}
