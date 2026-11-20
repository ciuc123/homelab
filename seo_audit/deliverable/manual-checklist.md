# Manual checklist

What `seo_audit` can't see from the site's HTML. Every one of these was a real finding on ciuculescu.com (the "Client Zero" series), and each is cheap to check. Record ✅ / ❌ / n/a plus one line of evidence.

## Leads & conversion

**M1 · The contact form delivers.** Submit a real test inquiry with an address you control, and confirm it arrives within 5 minutes, with the reply-to set to the sender.
*Why:* a form can show "Thanks!" and send nothing. ciuculescu.com's did for years.

**M2 · Analytics sees the lead.** Is there a measurable event for a submitted form (and for CTA clicks) in their analytics? Open the tool and find the test submission from M1.
*Why:* without it, no SEO result can be tied to business.

## Speed & weight

**M3 · Lighthouse, mobile, 3 runs.** Run it on the home page, the top landing page and one article, and take the median. Record the performance score, first and largest contentful paint, total blocking time, weight, and the render-blocking third-party files.
```bash
npx lighthouse@12 https://client.example/ --only-categories=performance --output=json --output-path=run1.json --quiet --chrome-flags="--headless=new"
```

**M4 · Weight after load.** Measure the bytes a first visit downloads at load, 5 s, 10 s and 20 s, across all frames, with [visit-weight.js](visit-weight.js) (Playwright).
*Why:* popups, chat widgets, consent banners and their reCAPTCHA often load after Lighthouse stops measuring. On ciuculescu.com a newsletter popup added about 550 KB at 5 s.

## Findability

**M5 · Hosting-specific paths.** Do platform defaults put extra pages on the domain?
- *GitHub Pages user site with a custom domain:* every Pages-enabled project of the account is served at `domain/<repo>/`. List them with `gh api users/OWNER/repos --paginate --jq '.[]|select(.has_pages)|.name'` and request each path. Look for full copies (200) and http:// redirects.
- *Netlify/Vercel:* preview and branch deploys that are indexable (`*.netlify.app`, `*.vercel.app` without `noindex`).
- *WordPress:* `/?s=`, attachment pages, `/author/` and tag archives that are thin or duplicated.

**M6 · Redirects.** Check http → https, www ↔ apex and trailing slashes: one hop, a 301, ending on the canonical URL. `curl -sIL http://client.example/ | grep -iE '^(HTTP|location)'`. For any redirect nobody set up, read which server answered (`server:`, `x-github-request-id`, `x-vercel-id`, `cf-ray`).

**M7 · Search Console / Bing coverage** (only with access). Compare indexed and not-indexed counts and the reasons, sitemap status, and manual actions.

## Search appearance

**M8 · Real snippets.** Search `site:client.example`. Are the results' titles and descriptions the ones the site sets, or did the search engine rewrite them? Note the top 5 rewrites.

**M9 · Share preview.** Paste the home page and one article into a LinkedIn post composer (don't publish) or a preview tool. Is the image right, and are the title and description readable?

## AI answers & entity

**M10 · AI panel, short.** Ask 5 buyer questions ("who can do X in Y", "how do I fix Z") and 2 brand questions ("who is …", "what does … offer") in ChatGPT, Perplexity, Gemini and Claude. Record whether the client is mentioned or cited, the competitors named, and whether the brand answers are factually right.

**M11 · Off-site entity.** Are the name, role, location and links the same across LinkedIn, GitHub, Google Business Profile, Clutch and other directories? Do the site's `sameAs` links point at all of them?

## Content (sample of 10 pages)

**M12 · Thin and stale content.** Pages under about 300 words with no unique value, posts whose commands or prices no longer work, and a past year in a title.

**M13 · Answer-first.** Do the top landing pages answer the main question in their first two sentences? Is there at least one heading phrased as the question a buyer asks?

## Honest limits

Note what wasn't checked and why, for example: "no analytics access (M2)" or "no Search Console access (M7)".
