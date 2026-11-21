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

- **Header search box:** removed. It needed the WordPress database.
- **Contact form (Contact Us):** replaced by an email button (info@eqlit.ca) and the phone number.
- **Events calendar** (Modern Events Calendar plugin): the sidebar widget is removed and the Calendar page points to the Facebook page for upcoming events.
- **Newsletter signup form:** replaced by a button to the hosted Mailchimp form (eepurl.com/hyc81X).
- **Sliders:** rotate with a few lines of plain JavaScript instead of the plugin. A small script also opens the mobile menu.
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
