// Run with Playwright installed: node tools/check-ui.cjs
// Optional: PLAYWRIGHT_MODULE, CHROME_PATH, UI_SCREENSHOT_DIR.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
const server = http.createServer((req, res) => {
  const file = path.resolve(root, '.' + new URL(req.url, 'http://localhost').pathname);
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
    res.writeHead(404); res.end(); return;
  }
  res.setHeader('Content-Type', (mime[path.extname(file)] || 'text/plain') + '; charset=utf-8');
  fs.createReadStream(file).pipe(res);
});
let browser;
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({ headless: true, ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(base + '/stage-1.html');
  await page.locator('[data-done-id="s1-1"]').click();
  assert.equal(await page.locator('[data-stage-label="1"]').textContent(), '1 / 4');
  assert.equal(await page.locator('[data-stage-bar="1"]').evaluate(el => el.style.width), '25%');
  await page.reload();
  assert.equal(await page.locator('[data-stage-bar="1"]').evaluate(el => el.style.width), '25%');
  for (let n = 2; n <= 4; n++) await page.locator(`[data-done-id="s1-${n}"]`).click();
  assert.equal(await page.locator('[data-stage-bar="1"]').evaluate(el => el.style.width), '100%');
  await page.locator('[data-done-id="s1-1"]').click();
  assert.equal(await page.locator('[data-stage-bar="1"]').evaluate(el => el.style.width), '75%');
  console.log('PASS progress: mark, undo, complete and reload');

  await page.goto(base + '/index.html');
  await page.evaluate(() => localStorage.setItem('dsh-handbook:v1', '{}'));
  await page.reload();
  assert.equal(await page.locator('[data-resume]').textContent(), '开始阅读');
  assert.equal(await page.locator('[data-resume]').getAttribute('href'), 'stage-1.html#s1-1');
  await page.goto(base + '/stage-2.html#s2-1');
  await page.waitForFunction(() => JSON.parse(localStorage.getItem('dsh-handbook:v1'))._lastRead === 's2-1');
  await page.goto(base + '/index.html');
  assert.equal(await page.locator('[data-resume]').getAttribute('href'), 'stage-2.html#s2-1');
  assert((await page.locator('[data-resume]').textContent()).startsWith('继续阅读：2.1'));
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'resume overflow at ' + width);
  }
  await page.goto(base + '/stage-2.html#s2-1');
  await page.locator('[data-done-id="s2-1"]').click();
  await page.goto(base + '/index.html');
  assert.equal(await page.locator('[data-resume]').getAttribute('href'), 'stage-1.html#s1-1');
  await page.evaluate(() => {
    const complete = Object.fromEntries(JSON.parse(document.getElementById('resume-lessons').textContent).map(x => [x.id, true]));
    localStorage.setItem('dsh-handbook:v1', JSON.stringify(complete));
  });
  await page.reload();
  assert.equal(await page.locator('[data-resume]').textContent(), '全部完成 · 回顾章节');
  assert.equal(await page.locator('[data-resume]').getAttribute('href'), 'contents.html');
  await page.evaluate(() => localStorage.setItem('dsh-handbook:v1', '{"s1-999":true,"_lastRead":"javascript:bad"}'));
  await page.reload();
  assert.equal(await page.locator('[data-mini-text]').textContent(), '0/33');
  assert.equal(await page.locator('[data-resume]').textContent(), '开始阅读');
  console.log('PASS resume: new reader, previous unfinished, next unfinished, all done and invalid records');

  const blockedContext = await browser.newContext({ reducedMotion: 'reduce' });
  await blockedContext.addInitScript(() => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (...args) {
      if (!window.allowProgressSave) throw new DOMException('Full', 'QuotaExceededError');
      return original.apply(this, args);
    };
  });
  const blocked = await blockedContext.newPage();
  await blocked.goto(base + '/stage-1.html');
  await blocked.locator('[data-done-id="s1-1"]').click();
  assert((await blocked.locator('[data-storage-notice]').textContent()).includes('本次进度未保存'));
  assert.equal(await blocked.locator('#s1-1 [data-progress-note]').textContent(), '仅本次有效 · 进度未保存');
  await blocked.reload();
  assert.equal(await blocked.locator('[data-stage-label="1"]').textContent(), '0 / 4');
  await blocked.evaluate(() => { window.allowProgressSave = true; });
  await blocked.locator('[data-done-id="s1-1"]').click();
  assert.equal(await blocked.locator('[data-storage-notice]').isVisible(), false);
  await blocked.reload();
  assert.equal(await blocked.locator('[data-stage-label="1"]').textContent(), '1 / 4');
  await blockedContext.close();
  console.log('PASS storage: quota failure remains visible, no false persistence, recovery saves progress');

  let lessons = 0, warnings = 0;
  for (let stage = 1; stage <= 6; stage++) {
    await page.goto(base + `/stage-${stage}.html`);
    const count = await page.locator('.lesson').count();
    lessons += count;
    assert.equal(await page.locator('.lesson-meta .status[href^="audit.html#audit-"]').count(), count);
    assert.equal(await page.locator('.lesson-audit time[datetime="2026-10"]').count(), count);
    assert.equal(await page.locator('.footer a[href="LICENSE"]').count(), 1);
    assert.equal(await page.locator('.footer a[href="LICENSE-CONTENT.md"]').count(), 1);
    warnings += await page.locator('.lesson:has(.status.todo) .lesson-audit[open]').count();
    for (const width of [320, 390, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      assert.equal(await page.locator('.mobile-toc').isVisible(), width < 1024);
      assert.equal(await page.locator('.toc').isVisible(), width >= 1024);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow: stage ${stage}, width ${width}`);
    }
  }
  assert.equal(lessons, 33); assert.equal(warnings, 3);
  await page.goto(base + '/audit.html');
  assert.equal(await page.locator('tr[id^="audit-s"]').count(), 33);
  console.log('PASS audit: 33 dated records, 3 expanded uncertainties; responsive layouts at 5 widths');

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base + '/stage-3.html');
  await page.locator('.mobile-toc summary').focus();
  await page.keyboard.press('Enter');
  assert.equal(await page.locator('.mobile-toc details').getAttribute('open'), '');
  await page.locator('.mobile-toc a[href="#s3-5"]').click();
  await page.waitForFunction(() => location.hash === '#s3-5' && document.querySelector('.mobile-toc a[href="#s3-5"]').getAttribute('aria-current') === 'location');
  assert.equal(await page.locator('.mobile-toc details').getAttribute('open'), null);
  assert.equal(await page.evaluate(() => document.activeElement.id), 's3-5');
  assert(await page.locator('#s3-5').evaluate(el => el.getBoundingClientRect().top >= 108));
  await page.evaluate(() => document.getElementById('s3-6').scrollIntoView());
  await page.waitForFunction(() => document.querySelector('.mobile-toc a[href="#s3-6"]').getAttribute('aria-current') === 'location');
  await page.reload();
  // Reload restores the reading position, which can differ from the URL fragment.
  await page.waitForFunction(() => document.querySelector('[data-toc-current]').textContent.startsWith('3.6 '));
  await page.goto(base + '/index.html');
  await page.goto(base + '/stage-3.html#s3-5');
  await page.waitForFunction(() => document.querySelector('[data-toc-current]').textContent.startsWith('3.5 '));
  async function toggleVisibleDirectory() {
    // A visible sticky control needs no locator-induced scrollIntoView.
    const box = await page.locator('.mobile-toc summary').boundingBox();
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  }
  const lessonTop = await page.locator('#s3-5').evaluate(el => el.getBoundingClientRect().top);
  await toggleVisibleDirectory();
  assert.equal(await page.locator('#s3-5').evaluate(el => el.getBoundingClientRect().top), lessonTop);
  assert((await page.locator('[data-toc-current]').textContent()).startsWith('3.5 '));
  await toggleVisibleDirectory();
  if (process.env.UI_SCREENSHOT_DIR) {
    fs.mkdirSync(process.env.UI_SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({ path: path.join(process.env.UI_SCREENSHOT_DIR, 'mobile-lesson.png') });
    await toggleVisibleDirectory();
    await page.screenshot({ path: path.join(process.env.UI_SCREENSHOT_DIR, 'mobile-directory.png') });
    await toggleVisibleDirectory();
  }
  console.log('PASS mobile directory: keyboard, navigation, focus, scroll tracking and deep link');

  await page.goto(base + '/stage-3.html#s3-1');
  const code = await page.locator('#s3-1-code-1').textContent();
  const plugin = await import('data:text/javascript,' + encodeURIComponent(code));
  assert.equal(plugin.name, 'study-plugin');
  assert.equal(typeof plugin.apply, 'function');
  plugin.apply();
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', { configurable: true, value: {
    writeText: async text => { window.copiedCode = text; }
  } }));
  await page.locator('[data-copy="s3-1-code-1"]').click();
  await page.waitForFunction(() => document.querySelector('.toast').textContent === '代码已复制');
  assert.equal(await page.evaluate(() => window.copiedCode), code);
  await page.evaluate(() => {
    navigator.clipboard.writeText = async () => { throw new Error('Denied'); };
    document.execCommand = () => false;
  });
  await page.locator('[data-copy="s3-1-code-1"]').click();
  await page.waitForFunction(() => document.querySelector('.toast').textContent.includes('自动复制失败'));
  assert.equal(await page.evaluate(() => getSelection().toString()), code);
  await page.evaluate(() => { document.execCommand = () => true; });
  await page.locator('[data-copy="s3-1-code-1"]').click();
  await page.waitForFunction(() => document.querySelector('.toast').textContent === '代码已复制');
  if (process.env.UI_SCREENSHOT_DIR) {
    await page.locator('#s3-1-code-1').evaluate(el => el.closest('.code-example').scrollIntoView({ block: 'center' }));
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await page.screenshot({ path: path.join(process.env.UI_SCREENSHOT_DIR, 'mobile-example.png') });
  }
  console.log('PASS examples: plugin syntax, exact clipboard text, legacy fallback and manual selection');

  await page.goto(base + '/search.html?q=STUDY_GATEWAY_KEY');
  assert.equal(await page.locator('.search-result').count(), 1);
  assert.equal(await page.locator('.search-result').getAttribute('href'), 'stage-2.html#s2-1');

  await page.goto(base + '/search.html?keep=1&q=插件#main');
  assert(await page.locator('.search-result').count() > 0);
  await page.locator('#search-q').fill('');
  assert.equal(new URL(page.url()).searchParams.has('q'), false);
  assert.equal(new URL(page.url()).searchParams.get('keep'), '1');
  assert.equal(new URL(page.url()).hash, '#main');
  await page.reload();
  assert.equal(await page.locator('#search-q').inputValue(), '');
  assert(await page.locator('#search-idle').isVisible());
  await page.locator('#search-q').fill('不存在的关键词xyz');
  assert(await page.locator('#search-empty').isVisible());

  // A known 33-hit fixture checks truncation, overlapping terms, entities and regex characters.
  const title = 'markdown <img src=x> & (工具)';
  const fixture = { count: 33, generated: 'test', lessons: Array.from({ length: 33 }, (_, i) => ({
    title, stage: 1, url: 'stage-1.html#s1-1', sentences: [{ k: '要点', t: title }]
  })) };
  await page.route('**/assets/search-index.js', route => route.fulfill({ contentType: 'text/javascript', body: 'window.__DSH_INDEX__ = ' + JSON.stringify(fixture) }));
  await page.goto(base + '/search.html');
  for (const query of ['markdown mark', '<img &', '(工具)', 'markdown markdown']) {
    await page.locator('#search-q').fill(query);
    assert.equal(await page.locator('.search-result').count(), 33);
    assert.equal(await page.locator('#search-count').textContent(), '33 节 · 展示 33 条摘要');
    assert.equal(await page.locator('.sr-title').first().textContent(), title);
    assert.equal(await page.locator('.search-results img, .search-results mark mark').count(), 0);
    assert.equal(await page.locator('.sr-title mark').first().textContent(), query.split(' ')[0]);
  }
  assert.deepEqual(errors, []);
  console.log('PASS search: real index, clear/reload, empty state, 33 hits, safe overlapping highlights');

  const offline = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  const plain = await offline.newPage();
  await plain.goto(pathToFileURL(path.join(root, 'stage-1.html')).href);
  assert.equal(await plain.locator('[data-copy]:visible').count(), 0);
  assert((await plain.locator('#s1-2-code-1').textContent()).includes('npx @deepseek-ai/dsh web'));
  await plain.locator('.mobile-toc summary').click();
  await plain.locator('.mobile-toc a[href="#s1-2"]').click();
  assert.equal(new URL(plain.url()).hash, '#s1-2');
  await offline.close();
  const filePage = await context.newPage();
  await filePage.goto(pathToFileURL(path.join(root, 'search.html')).href);
  await filePage.locator('#search-q').fill('沙箱');
  assert(await filePage.locator('.search-result').count() > 0);
  console.log('PASS direct file opening: directory without JS and offline search');
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(async () => {
  if (browser) await browser.close();
  server.close();
});
