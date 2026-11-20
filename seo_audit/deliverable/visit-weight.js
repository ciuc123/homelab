// Bytes downloaded by a real mobile visit at load, 5 s, 10 s, 20 s (all frames, incl. iframes).
// Usage: npm i playwright && npx playwright install chromium && node visit-weight.js https://site/ [more urls]
// Set CHROME_PATH to use a separate Chromium. "popup request at ms" = first request matching POPUP_RE (default: a MailerLite popup; set it for other widgets).
const { chromium, devices } = require('playwright');
const POPUP_RE = new RegExp(process.env.POPUP_RE || 'mailerlite\\.com/jsonp/\\d+/forms/[^/?]+\\?');
(async () => {
  const b = await chromium.launch(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {});
  for (const url of process.argv.slice(2)) {
    const ctx = await b.newContext({ ...devices['Pixel 5'] });
    const byHost = {}; const t0 = Date.now(); let firstMl = null;
    ctx.on('requestfinished', async r => { try { const s = await r.sizes(); const h = new URL(r.url()).host;
      byHost[h] = (byHost[h]||0) + s.responseBodySize + s.responseHeadersSize;
      if (!firstMl && POPUP_RE.test(r.url())) firstMl = Date.now() - t0; } catch(e){} });
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load' });
    const snap = () => Math.round(Object.values(byHost).reduce((a,b)=>a+b,0)/1024);
    const marks = { load: snap() };
    for (const t of [5, 10, 20]) { await page.waitForTimeout(t*1000 - (Date.now()-t0)); marks['t'+t] = snap(); }
    console.log(url, JSON.stringify(marks), 'popup request at ms:', firstMl);
    console.log('  KB by host @20s:', JSON.stringify(Object.fromEntries(Object.entries(byHost).sort((a,b)=>b[1]-a[1]).map(([k,v])=>[k,Math.round(v/1024)]))));
    await ctx.close();
  }
  await b.close();
})();
