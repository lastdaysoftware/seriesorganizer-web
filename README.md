# Series Organizer+ website

Static website for Series Organizer+ by LastDay Software.

## Pages

- `index.html`
- `privacy.html`
- `account-deletion.html`
- `support.html`

## Brand assets

The site uses the production SVG assets from `iconsAndLogos.zip` wherever practical:

- `assets/brand/series-organizer-plus-full-dark.svg` — homepage hero
- `assets/brand/series-organizer-plus-mark-dark.svg` — header/footer
- `assets/brand/icon_master.svg` — favicon
- PNG variants are retained for social/platform fallback use.

All supplied light/dark, wordmark, mark and monochrome variants are preserved under `assets/brand/`.

## Screenshots

Current app screenshots are under `assets/screenshots/`.

## History

Historical Series Organizer screenshots are under `assets/history/`.

## Publication checklist still open

Before Google Play / OAuth publication:

1. Complete and test the authenticated in-app account-deletion workflow.
2. Confirm the Google Play target-audience selections match the published children wording.
3. Add an approved TMDB logo alongside the required attribution notice.
4. Production domain: `https://seriesorganizer.com`. Keep the existing `workers.dev` address available temporarily during migration verification.
5. Verify `privacy.html`, `support.html`, and `account-deletion.html` open directly after deployment.

The site remains static. JavaScript is limited to approved integrations such as website analytics/consent and Giscus comments on News articles.


## Production deployment

- Canonical production URL: `https://seriesorganizer.com`
- `www.seriesorganizer.com` should permanently redirect to the equivalent apex-domain path while preserving query strings.
- The existing `seriesorganizer-web.lastdaysoftware.workers.dev` address may remain available temporarily during migration verification.
- Cloudflare Worker custom-domain, DNS, redirect, and certificate changes are managed outside this repository and must be verified separately.


## News, RSS, and comments

News posts are authored as Markdown files under `content/news/` and generated into static pages.

To publish a post:

1. Copy an existing file in `content/news/` and update its `title`, `date`, `slug`, `summary`, and body.
2. From the repository root, run:

   ```powershell
   python scripts/build-news.py
   ```

3. Preview `news/` locally, then commit the Markdown source and generated files together.

The build script updates `news/index.html`, `news/posts/*.html`, `feed.xml`, and the generated News section in `sitemap.xml`.

Comments use Giscus backed by the repository's GitHub Discussions `Announcements` category. Each article maps to its own discussion by URL pathname.

News articles are English-only for now. The Portuguese navigation links to the same News section.
