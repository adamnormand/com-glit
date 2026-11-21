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
function eqlcMail(f){var g=function(n){var e=f.querySelector('[name="'+n+'"]');return e?e.value:''};var c=f.querySelector('input[type=checkbox]');if(c&&!c.checked){alert('Please check the consent box.');return false}var body=g('your-message')+'\\n\\n'+g('your-name')+'\\n'+g('your-email');location.href='mailto:'+'info@eqlit.ca?subject='+encodeURIComponent(g('Subject')||'Message from eqlit.ca')+'&body='+encodeURIComponent(body);return false}
document.addEventListener('DOMContentLoaded',function(){var p=document.getElementById('pull');if(p){p.addEventListener('click',function(e){e.preventDefault();document.body.classList.toggle('mobile-menu-active');});}
var cal=document.querySelector('[data-eqlc-cal]');if(cal){var M=['January','February','March','April','May','June','July','August','September','October','November','December'],D=['SU','MO','TU','WE','TH','FR','SA'],now=new Date(),cy=now.getFullYear(),cm=now.getMonth();var nav=document.querySelector('[data-eqlc-nav]');function draw(){var first=new Date(cy,cm,1).getDay(),n=new Date(cy,cm+1,0).getDate(),prevN=new Date(cy,cm,0).getDate();var h='<div class="mec-month-container mec-month-container-selected"><div class="mec-calendar-table-head">'+D.map(function(d){return '<div class="mec-calendar-day-head">'+d+'</div>'}).join('')+'</div>';var cells=[];for(var i=first-1;i>=0;i--)cells.push('<dt class="mec-table-nullday">'+(prevN-i)+'</dt>');for(var d=1;d<=n;d++){var t=(cy===now.getFullYear()&&cm===now.getMonth()&&d===now.getDate());cells.push('<dt class="mec-calendar-day'+(t?' mec-selected-day':'')+'">'+d+'</dt>')}var k=1;while(cells.length%7)cells.push('<dt class="mec-table-nullday">'+(k++)+'</dt>');for(var r=0;r<cells.length;r+=7)h+='<dl class="mec-calendar-row">'+cells.slice(r,r+7).join('')+'</dl>';var sd=(cy===now.getFullYear()&&cm===now.getMonth())?now.getDate():1;h+='<div class="mec-calendar-events-sec" style="display:block"><h6 class="mec-table-side-title">Events for <span class="mec-color mec-table-side-day"> '+sd+'</span> '+M[cm]+'</h6><article class="mec-event-article"><div class="mec-event-detail">Upcoming events are posted on our <a href="'+'https://www.facebook.com/eqliteracy" target="_blank" rel="noopener">Facebook page</a>.</div></article></div>';cal.innerHTML=h+'</div>';if(nav){nav.querySelector('.mec-calendar-header h2').textContent=M[cm]+' '+cy;var b=nav.querySelectorAll('button.mec-load-month-link');b[0].innerHTML='<i class="mec-sl-angle-left" aria-hidden="true"></i> '+M[(cm+11)%12];b[1].innerHTML=M[(cm+1)%12]+' <i class="mec-sl-angle-right" aria-hidden="true"></i>';}}if(nav){var b=nav.querySelectorAll('button.mec-load-month-link');b[0].onclick=function(){cm--;if(cm<0){cm=11;cy--}draw()};b[1].onclick=function(){cm++;if(cm>11){cm=0;cy++}draw()};}draw();}
document.querySelectorAll('.sow-slider-images').forEach(function(s){var f=[].slice.call(s.children).filter(function(c){return c.classList.contains('sow-slider-image')});f.forEach(function(x,i){x.style.display=i?'none':'block'});if(f.length<2)return;var i=0;setInterval(function(){f[i].style.display='none';i=(i+1)%f.length;f[i].style.display='block'},6000);});});
</script>'''

NEWSLETTER_BLOCK = '<p style="text-align:center;margin:1.5em 0"><a href="http://eepurl.com/hyc81X" target="_blank" rel="noopener" style="display:inline-block;background:#8e2a8c;color:#fff;padding:14px 32px;border-radius:30px;font-weight:700;text-decoration:none">Subscribe to the newsletter</a></p>'

MC_U = '784bb386b8b75ce4e66387c66'
MC_ID = '197414fd22'
MC_ACTION = 'https://gaspelit.us1.list-manage.com/subscribe/post'

STATIC_CSS = '''<style id="static-fixes">
.sow-slider-base ul.sow-slider-images li.sow-slider-image{min-height:inherit}
@media screen and (min-width:866px){#navigation ul li:hover>ul,#navigation ul li:focus-within>ul{display:block;opacity:1;left:auto}#navigation ul ul li:hover>ul,#navigation ul ul li:focus-within>ul{left:188px}}
@media screen and (max-width:865px){#navigation ul ul{display:block}#navigation ul ul a{padding-left:40px!important;font-weight:400}}
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
    # header search box: same look, searches eqlit.ca through DuckDuckGo
    for f in soup.find_all('form', attrs={'role': 'search'}):
        f['action'] = 'https://duckduckgo.com/'
        f['target'] = '_blank'
        inp = f.find('input', attrs={'name': 's'})
        if inp:
            inp['name'] = 'q'
        h = soup.new_tag('input', attrs={'type': 'hidden', 'name': 'sites', 'value': 'eqlit.ca'})
        f.append(h)
    # contact form: same form, sends through the visitor's email app
    for f in soup.select('form.wpcf7-form'):
        for fs in f.select('fieldset.hidden-fields-container'):
            fs.decompose()
        f['action'] = 'mailto:' + EMAIL
        f['class'] = f.get('class', []) + ['eqlc-mailto-form']
        f['onsubmit'] = 'return eqlcMail(this)'
        del f['novalidate']
        note = BeautifulSoup('<p style="font-size:.85em;color:#777">Clicking Send opens your email program with your message ready to send to ' + EMAIL + '.</p>', 'html.parser')
        f.append(note)
    # Mailchimp signup: same form, posts directly to the Mailchimp list
    for f in soup.select('form.mc_signup_form'):
        f['action'] = MC_ACTION
        f['method'] = 'post'
        f['target'] = '_blank'
        for i in f.select('input[type=hidden], input[name=mailchimp_sf_alt_email]'):
            if i.get('name') == 'mailchimp_sf_alt_email':
                (i.find_parent(class_=lambda c: c and 'mc_alt' in c) or i.find_parent('div') or i).decompose()
            else:
                i.decompose()
        for i in f.select('input[name=mc_mv_EMAIL]'):
            i['name'] = 'EMAIL'; i['type'] = 'email'; i['required'] = ''
        for i in f.select('input[name=mc_mv_FNAME]'):
            i['name'] = 'FNAME'
        f.append(soup.new_tag('input', attrs={'type': 'hidden', 'name': 'u', 'value': MC_U}))
        f.append(soup.new_tag('input', attrs={'type': 'hidden', 'name': 'id', 'value': MC_ID}))
    # events: sidebar widget keeps its slot; calendar page keeps the month grid
    for m in soup.select('aside .mec-wrap .mec-skin-grid-events-container'):
        m.clear()
        m.append(BeautifulSoup('<a href="' + FACEBOOK + '" target="_blank" rel="noopener">Upcoming events: see our Facebook page</a>', 'html.parser'))
    for t in soup.select('#content .mec-wrap .mec-calendar-table'):
        t.clear()
        t['data-eqlc-cal'] = '1'
        wrap = t.find_parent(class_='mec-wrap')
    for nav in soup.select('#content .mec-month-navigator'):
        nav['data-eqlc-nav'] = '1'
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
