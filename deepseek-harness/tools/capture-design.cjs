// Local visual QA. Run after starting the static server on port 8765.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'design', 'qa');
const base = process.env.PREVIEW_URL || 'http://127.0.0.1:8765';
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
  try {
    const context = await browser.newContext({ viewport: { width: 1487, height: 1058 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    const page = await context.newPage();
    await page.goto(base + '/index.html');
    await page.evaluate(() => {
      const state = { _lastRead: 's2-5' };
      for (let chapter = 1; chapter <= 2; chapter++) for (let lesson = 1; lesson <= 4; lesson++) state[`s${chapter}-${lesson}`] = true;
      localStorage.setItem('dsh-handbook:v1', JSON.stringify(state));
    });
    await page.reload();
    assert.equal(await page.locator('[data-progress-count]').textContent(), '8');
    await page.screenshot({ path: path.join(out, 'home-desktop.png') });
    for (const route of ['index.html', 'stage-3.html', 'contents.html', 'search.html?q=插件', 'audit.html', 'about.html']) {
      for (const width of [390, 1440]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 1000 });
        await page.goto(base + '/' + route);
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), route + ': overflow at ' + width);
        await page.screenshot({ path: path.join(out, `${route.split('.')[0]}-${width}.png`) });
      }
    }
    const uri = file => 'data:image/png;base64,' + fs.readFileSync(file).toString('base64');
    const reference = uri(path.join(root, 'design', 'reference.png'));
    const implementation = uri(path.join(out, 'home-desktop.png'));
    await page.setViewportSize({ width: 2974, height: 1100 });
    await page.setContent(`<html><body style="margin:0;background:white;font:16px sans-serif"><div style="display:flex"><section style="width:1487px"><p style="margin:10px">Selected design</p><img width="1487" height="1058" src="${reference}"></section><section style="width:1487px"><p style="margin:10px">Implementation · 8/33 completed</p><img width="1487" height="1058" src="${implementation}"></section></div></body></html>`);
    await page.locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
    await page.screenshot({ path: path.join(out, 'comparison.png') });
    // Full scale crops preserve readable text for the typography/layout comparison.
    for (const [name, y, height] of [['opening', 130, 570], ['routes', 740, 300]]) {
      await page.setViewportSize({ width: 2974, height: height + 40 });
      await page.setContent(`<html><body style="margin:0;background:white;font:16px sans-serif"><div style="display:flex">${[reference, implementation].map((src, i) => `<section style="width:1487px"><p style="margin:8px">${i ? 'Implementation' : 'Selected design'}</p><div style="height:${height}px;overflow:hidden"><img width="1487" height="1058" src="${src}" style="transform:translateY(-${y}px)"></div></section>`).join('')}</div></body></html>`);
      await page.locator('img').evaluateAll(images => Promise.all(images.map(image => image.decode())));
      await page.screenshot({ path: path.join(out, `comparison-${name}.png`) });
    }
    console.log('PASS screenshots: matched 1487×1058 reference, 6 page types × desktop/mobile, combined comparisons');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
