// Render the PiP card (overlay.html?mode=pip) to a seamless 24 s MP4 loop for iPad.
// Usage: node render_pip.js [lang] [code] [pip|strip]   -> traxa_pip_<lang>.mp4 / traxa_strip_<lang>.mp4
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const lang = process.argv[2] || 'bm', code = process.argv[3] || 'ZIQFX', mode = process.argv[4] || 'pip';
  const H = mode === 'strip' ? 400 : 720;
  const FPS = 30, SECS = 24, out = path.join(__dirname, `traxa_${mode}_${lang}.mp4`);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: H } });
  await p.goto('file://' + path.join(__dirname, 'overlay.html') + `?mode=${mode}&capture=1&lang=${lang}&code=${code}`);
  await p.evaluate(() => document.fonts.ready);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-profile:v', 'main', '-pix_fmt', 'yuv420p', '-crf', '21', '-preset', 'slow', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < FPS * SECS; i++) {
    await p.evaluate(t => renderAt(t), i / FPS);
    ff.stdin.write(await p.screenshot({ type: 'jpeg', quality: 92 }));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
  console.log('wrote', out);
})();
