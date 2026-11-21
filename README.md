# com-glit — eqlit.ca (Eastern Quebec Literacy Council)

Static copy of eqlit.ca, migrated off WordPress on 2026-11-21. It has the same theme, images, text and PDFs, with no database, PHP or plugins.

## Contents

| Path | What it is |
|---|---|
| `index.html` | Home page |
| `<slug>/index.html` | The other 23 pages (about-2, calendar, contact-us, reports, …), same URLs as WordPress |
| `wp-content/uploads/` | Images, PDFs (reports, newsletters) and videos, at their original WordPress paths so existing links keep working |
| `wp-content/themes/`, `wp-content/plugins/` | Theme and page-builder CSS and fonts only (no PHP, no scripts) |
| `tools/build.py` | Script that produced the site from the raw browser mirror (in git history, commit "Mirror eqlit.ca batch …") |
| `.nojekyll` | Tells GitHub Pages to serve `wp-content/` as-is |

## What changed from WordPress

All of these keep the original look:
- **Header search box:** searches eqlit.ca through DuckDuckGo, in a new tab.
- **Contact form:** same fields. Send opens the visitor's email program with the message addressed to info@eqlit.ca.
- **Newsletter form:** same fields. It posts straight to the Mailchimp list (gaspelit.us1.list-manage.com), so new subscribers land in Mailchimp as before.
- **Calendar page:** the same month grid, built in the browser for the current month, plus a link to the Facebook page for upcoming events.
- **Sidebar events widget:** now reads "Upcoming events: see our Facebook page".
- **Menus, sliders and the mobile menu:** run on CSS or a few lines of plain JavaScript.
- **Removed:** all WordPress tracking, feeds and plugin scripts.

## Publish

1. Settings → Pages → Source: *Deploy from a branch* → `main` / `(root)`.
2. The site is then live at `https://adamnormand.github.io/com-glit/`. All links are relative, so it works there and on the domain.

## Domain cutover (later)

There is no `CNAME` file yet. Add it, containing `eqlit.ca`, only when eqlit.ca should point here. Then, in DNS:

```
@    A     185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153
@    AAAA  2606:50c0:8000::153 / 8001::153 / 8002::153 / 8003::153
www  CNAME adamnormand.github.io
```

Remove any old A, AAAA or CNAME records on `@` and `www`. Leave MX, TXT/SPF and DKIM untouched. Then enable *Enforce HTTPS* in Settings → Pages.
