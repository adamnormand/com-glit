#!/usr/bin/env python3
"""Rebuild eqlit.ca as a static site from the raw browser mirror in _mirror/.

Run from the repo root:  python3 tools/build.py
- assets go back to their original WordPress paths (wp-content/...)
- each page becomes <slug>/index.html (home -> index.html)
- WordPress scripts, feeds, search, contact form and event widgets are removed
- every eqlit.ca link becomes relative, so the site works on github.io and on the domain
"""
import os, re, shutil, posixpath
from urllib.parse import urlparse, unquote
from bs4 import BeautifulSoup, Comment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(ROOT, '_mirror')
HOST_RE = re.compile(r'(?:https?:)?//(?:www\.)?eqlit\.ca', re.I)
FACEBOOK = 'https://www.facebook.com/eqliteracy'
EMAIL = 'info@eqlit.ca'

pages = {}   # slug -> raw html
for name in sorted(os.listdir(MIRROR)):
    src = os.path.join(MIRROR, name)
    if name.startswith('PAGE__'):
        slug = name[len('PAGE__'):-len('.html')]
        pages['' if slug == 'home' else slug] = open(src, encoding='utf-8').read()
    else:
        dst = os.path.join(ROOT, *name.split('__'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)

SLUGS = set(pages)
missing = set()


def page_out(slug):
    return 'index.html' if slug == '' else f'{slug}/index.html'


def local_target(path):
    """Map a site path (/x/y) to a repo-relative target, or None."""
    p = unquote(path).lstrip('/')
    slug = p.rstrip('/')
    if slug in SLUGS:
        return (slug + '/') if slug else ''
    if p and os.path.isfile(os.path.join(ROOT, p)):
        return p
    # resized WordPress rendition missing -> fall back to the original
    orig = re.sub(r'-(\d+)x(\d+)(\.\w+)$', r'\3', p)
    if orig != p and os.path.isfile(os.path.join(ROOT, orig)):
        return orig
    orig2 = re.sub(r'-e\d{10,}(\.\w+)$', r'\1', orig)
    if orig2 != orig and os.path.isfile(os.path.join(ROOT, orig2)):
        return orig2
    return None


def rewrite(url, base_dir):
    """Rewrite one URL. base_dir = directory of the output file, repo-relative."""
    if not url:
        return url
    u = url.strip()
    if u.startswith('chrome-extension://') or 'chrome-extension://' in u:
        u = u[u.find('https://eqlit.ca'):] if 'https://eqlit.ca' in u else u
    if not (HOST_RE.match(u) or (u.startswith('/') and not u.startswith('//'))):
        return url
    pu = urlparse(HOST_RE.sub('', u) if HOST_RE.match(u) else u)
    tgt = local_target(pu.path or '/')
    if tgt is None:
        missing.add(pu.path)
        return 'https://eqlit.ca' + (pu.path or '/')
    rel = posixpath.relpath(tgt or '.', base_dir or '.')
    if tgt == '' or tgt.endswith('/'):
        rel = rel.rstrip('/') + '/'
        if rel == './':
            rel = './'
    frag = ('#' + pu.fragment) if pu.fragment else ''
    return rel + frag


URL_IN_CSS = re.compile(r'url\(\s*([\'"]?)([^\'")]+)\1\s*\)')


def rewrite_css(text, base_dir):
    return URL_IN_CSS.sub(lambda m: f"url({m.group(1)}{rewrite(m.group(2), base_dir)}{m.group(1)})", text)


def rewrite_srcset(val, base_dir):
    out = []
    for part in val.split(','):
        bits = part.strip().split()
        if not bits:
            continue
        p = urlparse(HOST_RE.sub('', bits[0])).path
        if local_target(p) and local_target(p) == unquote(p).lstrip('/'):
            out.append(' '.join([rewrite(bits[0], base_dir)] + bits[1:]))
    return ', '.join(out)


CONTACT_BLOCK = f'''<div class="eqlc-contact" style="text-align:center;margin:1.5em 0 2em">
<p style="margin-bottom:1em">Send us your questions, comments or ideas by email or leave us a message by phone.</p>
<p><a class="eqlc-btn" href="mailto:{EMAIL}" style="display:inline-block;background:#00a19a;color:#fff;padding:14px 32px;border-radius:30px;font-weight:700;text-decoration:none">Email {EMAIL}</a></p>
<p style="margin-top:1em"><a href="tel:+14183685611">418-368-5611</a></p>
</div>'''

CALENDAR_BLOCK = f'''<div class="eqlc-calendar" style="text-align:center;margin:2em 0">
<p style="font-size:1.2em;margin-bottom:1em">Our upcoming programs, workshops and events are posted on our Facebook page.</p>
<p><a href="{FACEBOOK}" target="_blank" rel="noopener" style="display:inline-block;background:#24205c;color:#fff;padding:14px 32px;border-radius:30px;font-weight:700;text-decoration:none">See upcoming events on Facebook</a></p>
<p style="margin-top:1em">Questions? <a href="mailto:{EMAIL}">{EMAIL}</a> or <a href="tel:+14183685611">418-368-5611</a></p>
</div>'''

MENU_JS = '''<script>
document.addEventListener('DOMContentLoaded',function(){var p=document.getElementById('pull');if(p){p.addEventListener('click',function(e){e.preventDefault();document.body.classList.toggle('mobile-menu-active');});}
document.querySelectorAll('.sow-slider-images').forEach(function(s){var f=[].slice.call(s.children).filter(function(c){return c.classList.contains('sow-slider-image')});f.forEach(function(x,i){x.style.display=i?'none':'block'});if(f.length<2)return;var i=0;setInterval(function(){f[i].style.display='none';i=(i+1)%f.length;f[i].style.display='block'},6000);});});
</script>'''

NEWSLETTER_BLOCK = '<p style="text-align:center;margin:1.5em 0"><a href="http://eepurl.com/hyc81X" target="_blank" rel="noopener" style="display:inline-block;background:#8e2a8c;color:#fff;padding:14px 32px;border-radius:30px;font-weight:700;text-decoration:none">Subscribe to the newsletter</a></p>'

STATIC_CSS = '''<style id="static-fixes">
.sow-slider-base ul.sow-slider-images li.sow-slider-image{min-height:inherit}
.sow-slider-base ul.sow-slider-images li.sow-slider-image .sow-slider-image-container{min-height:inherit;position:relative;z-index:1}
</style>'''

DROP_LINK_RELS = {'pingback', 'alternate', 'profile', 'dns-prefetch', 'preconnect', 'EditURI',
                  'shortlink', 'https://api.w.org/', 'wlwmanifest', 'prefetch', 'modulepreload'}

for slug, html in pages.items():
    out = page_out(slug)
    base_dir = posixpath.dirname(out)
    soup = BeautifulSoup(html, 'html5lib')

    for t in soup.find_all(['script']):
        t.decompose()
    for t in soup.find_all('noscript'):
        t.unwrap()
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in soup.find_all('meta', attrs={'name': 'generator'}):
        t.decompose()
    for t in soup.find_all('link'):
        rel = set(t.get('rel') or [])
        if rel & DROP_LINK_RELS or 'wp-json' in (t.get('href') or ''):
            t.decompose()
    # dead plugin styles (events calendar, contact form, LMS)
    for t in soup.find_all('link', rel='stylesheet'):
        h = t.get('href', '')
        if any(k in h for k in ('modern-events-calendar', 'contact-form-7', '/tutor/')):
            t.decompose()

    # header search box
    for f in soup.find_all('form', attrs={'role': 'search'}):
        w = f.find_parent(class_='widget-header') or f
        w.decompose()
    # contact form -> email / phone
    for f in soup.select('.wp-block-contact-form-7-contact-form-selector, .wpcf7'):
        if f.parent is not None:
            f.replace_with(BeautifulSoup(CONTACT_BLOCK, 'lxml').div)
    # events calendar: sidebar widgets dropped, page content replaced
    first = True
    for m in soup.select('.mec-wrap'):
        if m.parent is None:
            continue
        in_sidebar = m.find_parent('aside') is not None
        holder = m.find_parent(class_='widget') or m
        if in_sidebar:
            holder.decompose()
        elif first:
            m.replace_with(BeautifulSoup(CALENDAR_BLOCK, 'lxml').div)
            first = False
        else:
            m.decompose()
    # SiteOrigin sliders/heroes are hidden until their JS runs: show them statically
    for base in soup.select('.sow-slider-base'):
        if base.has_attr('style'):
            base['style'] = re.sub(r'display:\s*none;?', '', base['style'])
        if len(base.select('li.sow-slider-image')) < 2:
            for nav in base.select('.sow-slider-pagination, .sow-slide-nav'):
                nav.decompose()
    for v in soup.select('video.sow-full-element'):
        v['style'] = 'opacity:1;width:100%;height:auto;display:block'
    # Mailchimp signup form posts to WordPress -> point to the hosted Mailchimp form if present
    for f in soup.select('form#mc_signup_form, .mc_signup_form'):
        f.replace_with(BeautifulSoup(NEWSLETTER_BLOCK, 'html.parser'))

    # URLs
    for tag in soup.find_all(True):
        for attr in ('href', 'src', 'poster', 'data-src', 'action'):
            if tag.has_attr(attr):
                tag[attr] = rewrite(tag[attr], base_dir)
        if tag.has_attr('srcset'):
            v = rewrite_srcset(tag['srcset'], base_dir)
            if v:
                tag['srcset'] = v
            else:
                del tag['srcset']
                if tag.has_attr('sizes'):
                    del tag['sizes']
        if tag.has_attr('style'):
            tag['style'] = rewrite_css(tag['style'], base_dir)
        if tag.has_attr('onclick') and tag['onclick'].strip() == 'return true':
            del tag['onclick']
    for st in soup.find_all('style'):
        if st.string:
            st.string = rewrite_css(st.string, base_dir)
    # strip WordPress cache-busting queries from local asset URLs
    for tag in soup.find_all(['link', 'img', 'source']):
        for attr in ('href', 'src'):
            v = tag.get(attr)
            if v and not v.startswith('http') and '?' in v:
                tag[attr] = v.split('?')[0]

    soup.head.append(BeautifulSoup(STATIC_CSS, 'html.parser'))
    soup.body.append(BeautifulSoup(MENU_JS, 'html.parser'))
    dst = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as fh:
        fh.write('<!DOCTYPE html>\n' + str(soup.html))

# CSS files: make eqlit.ca absolute URLs relative
for dp, _, fs in os.walk(os.path.join(ROOT, 'wp-content')):
    for f in fs:
        if f.endswith('.css'):
            p = os.path.join(dp, f)
            rel_dir = os.path.relpath(dp, ROOT).replace(os.sep, '/')
            txt = open(p, encoding='utf-8', errors='replace').read()
            new = URL_IN_CSS.sub(lambda m: f"url({m.group(1)}{rewrite(m.group(2), rel_dir) if HOST_RE.match(m.group(2)) else m.group(2)}{m.group(1)})", txt)
            if new != txt:
                open(p, 'w', encoding='utf-8').write(new)

print('pages:', len(pages))
print('unresolved eqlit.ca paths:', len(missing))
for m in sorted(missing):
    print('  ', m)
