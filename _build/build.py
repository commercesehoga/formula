#!/usr/bin/env python3
"""Builds the static library pages from _build/formulas.json.
Run from the project root:  python3 _build/build.py
The header, footer, CSS and scripts are copied from about.html, so editing about.html updates every generated page.
Generated: formula.html, formula/<slug>.html, <subject>-formulas.html, how-it-works.html, examples.html,
hi.html, status.html, sitemap.xml, plus the page lists in llms.txt and llms-full.txt."""
import json, re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://formula.thunderstudy.indevs.in'
TODAY = '2026-10-03'
TODAY_LONG = '3 October 2026'
OG_ALT = "ThunderStudy AI logo with the headline Turn any formula into a story you&#x27;ll never forget, and a Formula Story Mode badge on a light purple card"
E = html.escape
DATA = json.load(open(ROOT / '_build' / 'formulas.json', encoding='utf-8'))
SUBJECTS = {
    'physics':   ('Physics',   'physics-formulas'),
    'chemistry': ('Chemistry', 'chemistry-formulas'),
    'maths':     ('Maths',     'maths-formulas'),
    'biology':   ('Biology',   'biology-formulas'),
}
ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>'
ICONS = {
    'bolt':  '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    'book':  '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>',
    'chat':  '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'list':  '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
}
def icon(n):
    return '<div class="card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg></div>' % ICONS[n]

# ---------- template taken from about.html ----------
t = (ROOT / 'about.html').read_text(encoding='utf-8').replace('\r\n', '\n')
ld_start = t.index('<script type="application/ld+json">')
ld_end = t.index('</script>', ld_start)
BASE_GRAPH = json.loads(t[ld_start + len('<script type="application/ld+json">'):ld_end])['@graph'][:2]  # Organization, WebSite
REST_HEAD = t[ld_end + len('</script>'):t.index('<main')]
POST_MAIN = t[t.index('</main>') + len('</main>'):]
REST_HEAD = REST_HEAD.replace('<a href="/about" class="active" aria-current="page">About</a>', '<a href="/about">About</a>')
REST_HEAD = REST_HEAD.replace('<a href="/about" class="active">About</a>', '<a href="/about">About</a>')
EXTRA_CSS = """<style id="page-additions">
.formula-box{margin:18px 0 6px;padding:22px 20px;text-align:center;font-size:clamp(20px,4.5vw,30px);font-weight:700;color:var(--primary);background:var(--canvas);border-radius:var(--radius-sm);box-shadow:inset 4px 4px 10px var(--clay-dark),inset -4px -4px 10px var(--clay-light);overflow-wrap:anywhere}
.var-list{list-style:none;margin:16px 0 0;padding:0;display:grid;gap:10px}
.var-list li{display:flex;gap:14px;align-items:baseline;font-size:15.5px;line-height:1.5;color:var(--body-c)}
.var-list b{flex:0 0 76px;color:var(--ink)}
a.link-card{display:block;color:inherit;transition:transform .2s ease}
a.link-card:hover,a.link-card:focus-visible{transform:translateY(-3px)}
.tag-row{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.tag{display:inline-block;padding:4px 12px;border-radius:var(--radius-pill);background:var(--primary-soft);color:var(--primary);font-size:12.5px;font-weight:700}
.card .formula-line{margin:10px 0 0;font-weight:700;color:var(--primary);font-size:17px;overflow-wrap:anywhere}
.card .go{display:inline-flex;align-items:center;gap:10px;margin-top:16px;color:var(--primary);font-weight:700;font-size:14.5px;text-decoration:none}
.card .go svg{flex:none;width:30px;height:30px;padding:7px;box-sizing:border-box;border-radius:50%;background:var(--surface);color:var(--primary);box-shadow:3px 3px 8px var(--clay-dark),-3px -3px 8px var(--clay-light);transition:background .2s,color .2s,transform .2s}
a.link-card:hover .go svg,a.link-card:focus-visible .go svg,.card .go:hover svg{background:var(--primary);color:#fff;transform:translateX(3px)}
.steps{list-style:none;margin:0;padding:0;display:grid;gap:24px;counter-reset:step}
.steps li{counter-increment:step;position:relative;padding-left:0}
.steps li .card::before{content:counter(step);display:flex;align-items:center;justify-content:center;width:40px;height:40px;margin-bottom:14px;border-radius:50%;background:var(--primary-soft);color:var(--primary);font-weight:700}
.status-row{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:14px 0;border-bottom:1px solid var(--hairline)}
.status-row:last-child{border-bottom:none}
.status-row span:first-child{color:var(--ink);font-weight:600}
.status-pill{display:inline-flex;align-items:center;gap:8px;padding:5px 14px;border-radius:var(--radius-pill);background:var(--primary-soft);color:var(--ink);font-size:13.5px;font-weight:600}
.status-pill::before{content:"";width:9px;height:9px;border-radius:50%;background:var(--muted)}
.status-pill.ok::before{background:#22c55e}
.status-pill.bad::before{background:#dc2626}
.lang-link{display:inline-flex;align-items:center;gap:6px}
.dock{position:fixed;left:50%;bottom:calc(14px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);z-index:60;display:flex;align-items:center;gap:14px;padding:12px 22px;border-radius:999px;background:color-mix(in srgb,var(--surface) 78%,transparent);box-shadow:8px 8px 22px var(--clay-dark),-8px -8px 22px var(--clay-light);border:1px solid var(--hairline);backdrop-filter:blur(16px) saturate(160%);-webkit-backdrop-filter:blur(16px) saturate(160%)}
.dock a{position:relative;display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:50%;color:var(--muted);text-decoration:none;transition:transform .25s ease,color .2s,background .2s,box-shadow .25s}
.dock a svg{width:26px;height:26px;flex:none;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.dock a:hover,.dock a:focus-visible{color:var(--primary);transform:translateY(-3px)}
.dock a.active{width:66px;height:66px;margin:-14px 6px;color:#fff;background:linear-gradient(145deg,#7d63ff,var(--primary));box-shadow:0 10px 26px rgba(87,58,252,.55),inset 2px 2px 6px rgba(255,255,255,.25)}
.dock a.active svg{width:30px;height:30px}
.dock a.active:hover{transform:translateY(-3px)}
body{padding-bottom:96px}
@media(max-width:420px){.dock{gap:8px;padding:10px 14px}.dock a{width:44px;height:44px}.dock a.active{width:60px;height:60px;margin:-12px 4px}}
.lib-tools{display:flex;justify-content:flex-end;max-width:1100px;margin:0 auto 14px}
.lib-tools button{font:inherit;font-weight:700;font-size:13.5px;padding:8px 16px;border:none;border-radius:999px;cursor:pointer;color:var(--primary);background:var(--surface);box-shadow:3px 3px 8px var(--clay-dark),-3px -3px 8px var(--clay-light)}
.lib-acc{display:grid;gap:18px;max-width:1100px;margin:0 auto}
details.acc{background:var(--canvas);border-radius:32px;border:1px solid var(--hairline);box-shadow:8px 8px 20px var(--clay-dark),-8px -8px 20px var(--clay-light);overflow:hidden}
details.acc summary{list-style:none;display:flex;align-items:center;gap:12px;padding:20px 24px;cursor:pointer;font-weight:800;font-size:clamp(17px,2.4vw,20px);text-transform:uppercase;letter-spacing:.3px;color:var(--acc,var(--primary))}
details.acc summary::-webkit-details-marker{display:none}
details.acc summary:focus-visible{outline:2px solid var(--primary);outline-offset:-4px;border-radius:32px}
.acc-ico{width:26px;height:26px;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.acc-count{margin-left:auto;min-width:34px;height:30px;padding:0 10px;display:inline-flex;align-items:center;justify-content:center;border-radius:999px;background:var(--primary-soft);color:var(--primary);font-size:14px;font-weight:700}
.acc-chev{width:20px;height:20px;flex:none;fill:none;stroke:var(--muted);stroke-width:2;stroke-linecap:round;stroke-linejoin:round;transition:transform .25s}
details.acc[open] .acc-chev{transform:rotate(180deg)}
.acc-body,.fgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px}
.acc-body{padding:0 18px 20px}
.fgrid{max-width:1100px;margin:0 auto}
.fcard{position:relative;display:block;min-height:96px;padding:16px 46px 18px 18px;border-radius:20px;background:var(--surface);box-shadow:4px 4px 12px var(--clay-dark),-4px -4px 12px var(--clay-light);color:inherit;text-decoration:none;transition:transform .2s ease}
.fcard b{display:block;color:var(--ink);font-size:16px;line-height:1.3}
.fcard .sub{display:block;margin-top:5px;color:var(--muted);font-size:13px;line-height:1.45;overflow-wrap:anywhere}
.fcard .arr{position:absolute;right:14px;bottom:14px;width:18px;height:18px;fill:none;stroke:var(--muted);stroke-width:2;stroke-linecap:round;stroke-linejoin:round;transition:transform .2s,stroke .2s}
.fcard:hover,.fcard:focus-visible{transform:translateY(-3px)}
.fcard:hover .arr,.fcard:focus-visible .arr{stroke:var(--primary);transform:translate(2px,-2px)}
.fcard.all b{color:var(--primary)}
</style>
"""

def dock_html(active=None):
    items = [('/index', 'Home', '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/>', 'home'),
             ('/app', 'Make', '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>', 'make'),
             ('/formula', 'Library', '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5"/>', 'lib')]
    out = '<nav class="dock" aria-label="Quick dock">'
    for href, lbl, svg, k in items:
        cur = ' class="active" aria-current="page"' if k == active else ''
        out += '<a href="%s"%s aria-label="%s" title="%s"><svg viewBox="0 0 24 24" aria-hidden="true">%s</svg></a>' % (href, cur, lbl, lbl, svg)
    return out + '</nav>\n'

def nav_for(active):
    head = REST_HEAD
    if active:
        head = re.sub(r'<a href="%s">([^<]+)</a>' % re.escape(active),
                      r'<a href="%s" class="active" aria-current="page">\1</a>' % active, head, count=1)
        head = re.sub(r'(<a href="%s")>([^<]+)</a>' % re.escape(active),
                      r'\1 class="active">\2</a>', head, count=1)
    return head

def jl(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False, indent=2) + '\n</script>'

def crumbs(path, items):
    return {"@type": "BreadcrumbList", "@id": SITE + path + "#breadcrumb",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}

def faq_node(path, qas, lang='en-IN'):
    return {"@type": "FAQPage", "@id": SITE + path + "#faq", "inLanguage": lang,
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qas]}

def faq_html(qas):
    return '<div class="faq-list">\n' + '\n'.join(
        '<details class="faq"><summary>%s</summary><div class="faq-a">%s</div></details>' % (E(q), E(a)) for q, a in qas) + '\n</div>'

def page_meta(extra=''):
    return '<div class="wrap"><p class="page-meta">Last updated: <time datetime="%s">%s</time>. ThunderStudy is owned and maintained by <a href="/about">Wondermayank</a>, a solo student developer who has been building free educational tools since 2018.%s</p></div>' % (TODAY, TODAY_LONG, extra)

def hero(badge, h1, p, buttons):
    return ('<section class="page-hero">\n  <div class="blob blob-1"></div>\n  <div class="blob blob-2"></div>\n  <div class="wrap">\n'
            '    <div class="error-badge"><span class="error-dot"></span>%s</div>\n    <h1>%s</h1>\n    <p>%s</p>\n    <div class="error-actions">\n%s\n    </div>\n  </div>\n</section>\n') % (E(badge), h1, p, buttons)

def btn(href, label, primary=True, arrow=True):
    return '      <a href="%s" class="%s">%s%s</a>' % (href, 'primary-btn' if primary else 'secondary-btn', label, (' ' + ARROW) if arrow and primary else '')

ARR_UP = '<svg class="arr" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17 17 7"/><path d="M8 7h9v9"/></svg>'
SUBJ_STYLE = {
    'physics':   ('#8B5CF6', '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>'),
    'chemistry': ('#22C55E', '<path d="M9 3h6"/><path d="M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2.2h12.4a1.5 1.5 0 0 0 1.3-2.2L14 9V3"/><path d="M7.5 15h9"/>'),
    'maths':     ('#3B82F6', '<path d="M4 7h6M7 4v6"/><path d="M14 4l6 6M20 4l-6 6"/><path d="M4 18h6"/><path d="M14 16h6M14 20h6"/>'),
    'biology':   ('#F59E0B', '<path d="M12 21c-5 0-8-3.5-8-8 4 0 8 1.5 8 8Z"/><path d="M12 21c5 0 8-3.5 8-8-4 0-8 1.5-8 8Z"/><path d="M12 21V8"/><path d="M12 8c0-3 1.5-5 4-5 0 3-1.5 5-4 5Z"/>'),
}
def fcard(d, href=None):
    sub = '%s · %s' % (d['formula'], ', '.join(d['exams'][:2]))
    return '<a class="fcard" href="%s"><b>%s</b><span class="sub">%s</span>%s</a>' % (href or '/formula/' + d['slug'], E(d['name']), E(sub), ARR_UP)
def all_card(sname, spath, n):
    return '<a class="fcard all" href="/%s"><b>All %s formulas</b><span class="sub">Open the %s page · %d formulas</span>%s</a>' % (spath, E(sname), E(sname), n, ARR_UP)

def link_card(href, title, formula, text, go='Read the story'):
    return ('<a class="card link-card" href="%s"><h3>%s</h3><p class="formula-line">%s</p><p>%s</p><span class="go">%s %s</span></a>'
            % (href, E(title), E(formula), E(text), go, ARROW))

def cta_card(h2='Need a story for a different formula?', p='Type any formula or topic into the free ThunderStudy AI tool and get a story, a real-life analogy or a memory trick.'):
    return '<section class="section"><div class="card narrow"><h2>%s</h2><p>%s</p><div class="btn-row">%s</div></div></section>' % (E(h2), E(p), btn('/app', 'Open the free tool'))

def build_page(path, title, desc, main, active=None, nodes=None, robots='index, follow', og_type='website', lang='en-IN', locale='en_IN', alternates=None, extra_head=''):
    url = SITE + path
    alt = ''.join('<link rel="alternate" hreflang="%s" href="%s">\n' % (h, SITE + u) for h, u in (alternates or []))
    canon = '' if robots.startswith('noindex') else '<link rel="canonical" href="%s">\n' % url
    head = ('<!DOCTYPE html>\n<html lang="%s">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n<meta name="robots" content="%s">\n%s%s'
            '<meta name="author" content="Wondermayank">\n<meta property="og:type" content="%s">\n<meta property="og:site_name" content="ThunderStudy AI">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n<meta property="og:url" content="%s">\n'
            '<meta property="og:image" content="%s/assets/og-image.png">\n<meta property="og:image:type" content="image/png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            '<meta property="og:image:alt" content="%s">\n<meta property="og:locale" content="%s">\n<meta name="twitter:card" content="summary_large_image">\n'
            '<meta name="twitter:title" content="%s">\n<meta name="twitter:description" content="%s">\n<meta name="twitter:image" content="%s/assets/og-image.png">\n'
            '<meta name="twitter:image:alt" content="%s">\n<meta name="twitter:site" content="@wondermayank">\n<meta name="twitter:creator" content="@wondermayank">\n'
            ) % (lang, E(title), E(desc), robots, canon, alt, og_type, E(title), E(desc), url, SITE, OG_ALT, locale, E(title), E(desc), SITE, OG_ALT)
    graph = BASE_GRAPH + (nodes or [])
    ld = jl({"@context": "https://schema.org", "@graph": graph})
    rest = nav_for(active).replace('</head>', EXTRA_CSS + '</head>', 1)
    out = head + ld + rest + '<main class="page-main">\n' + main + '\n</main>' + POST_MAIN.replace('</footer>', '</footer>\n\n<!-- DOCK -->\n' + dock_html('lib' if active == '/formula' else None), 1)
    if lang != 'en-IN':
        out = out.replace('<html lang="en-IN">', '<html lang="%s">' % lang)
    return out

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

def webpage(path, name, desc, kind='WebPage', lang='en-IN', extra=None):
    n = {"@type": kind, "@id": SITE + path + "#webpage", "url": SITE + path, "name": name, "description": desc, "inLanguage": lang,
         "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": SITE + "/#organization"}, "breadcrumb": {"@id": SITE + path + "#breadcrumb"},
         "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "/assets/og-image.png", "width": 1200, "height": 630},
         "dateModified": TODAY}
    n.update(extra or {})
    return n

def trim(s, n):
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0].rstrip(',.;:') + '.'

sitemap = []  # (path, priority)
by_subject = {k: [d for d in DATA if d['subject'] == k] for k in SUBJECTS}

# ---------- formula pages ----------
for d in DATA:
    sname, spath = SUBJECTS[d['subject']]
    path = '/formula/' + d['slug']
    title = '%s %s: Story and Memory Trick' % (d['name'], d['kind'].title())
    if len(title) > 60: title = '%s: Story and Memory Trick' % d['name']
    desc = trim('%s %s: %s. Learn it with a short story, a real-life analogy, a memory trick and an exam tip. Free from ThunderStudy AI.' % (d['name'], d['kind'], d['formula']), 155)
    qas = [("What is the %s %s?" % (d['name'], d['kind']), "%s. %s" % (d['formula'], d['summary'])),
           ("How do I remember the %s %s?" % (d['name'], d['kind']), d['trick']),
           ("What should I watch out for in exams with %s?" % d['name'], d['tip'])]
    related = [x for x in by_subject[d['subject']] if x['slug'] != d['slug']]
    main = hero('%s %s' % (sname, d['kind']), '%s %s:<br>story, analogy and memory trick' % (E(d['name']), d['kind']),
                E('The %s %s is %s. %s' % (d['name'], d['kind'], d['formula'], d['summary'])),
                btn('/app', 'Make my own story') + '\n' + btn('/' + spath, 'All %s formulas' % sname, False))
    main += '<div class="wrap">\n<section class="section"><div class="card narrow">\n<div class="tag-row">%s</div>\n<h2>The %s %s</h2>\n<div class="formula-box">%s</div>\n<ul class="var-list">%s</ul>\n</div></section>\n' % (
        ''.join('<span class="tag">%s</span>' % E(x) for x in [sname] + d['exams']), E(d['name']), d['kind'], E(d['formula']),
        ''.join('<li><b>%s</b><span>%s</span></li>' % (E(a), E(b)) for a, b in d['vars']))
    main += '<section class="section"><div class="grid">\n'
    for ic, h, k in [('book', 'The story', 'story'), ('chat', 'Real-life analogy', 'analogy'), ('bolt', 'Memory trick', 'trick'), ('check', 'Exam tip', 'tip')]:
        main += '<div class="card">%s<h3>%s</h3><p>%s</p></div>\n' % (icon(ic), h, E(d[k]))
    main += '</div></section>\n<section class="section"><div class="section-head"><div class="error-badge"><span class="error-dot"></span>FAQ</div><h2>Questions about %s</h2></div>\n<div class="narrow">%s</div></section>\n' % (E(d['name']), faq_html(qas))
    main += '<section class="section"><div class="section-head"><h2>More %s formulas</h2></div><div class="grid">%s</div></section>\n' % (
        E(sname), ''.join(link_card('/formula/' + r['slug'], r['name'], r['formula'], r['summary']) for r in related))
    main += cta_card() + '\n</div>\n' + page_meta(' AI and summary notes can contain mistakes, so check important formulas against your textbook.')
    nodes = [webpage(path, title, desc, 'WebPage', extra={"mainEntity": {"@id": SITE + path + "#resource"}}),
             {"@type": ["LearningResource", "Article"], "@id": SITE + path + "#resource", "headline": title, "name": '%s %s' % (d['name'], d['kind']),
              "description": d['summary'], "inLanguage": "en-IN", "learningResourceType": "mnemonic and worked explanation", "educationalLevel": ", ".join(d['exams']),
              "teaches": d['formula'], "about": {"@type": "Thing", "name": sname}, "isAccessibleForFree": True, "datePublished": TODAY, "dateModified": TODAY,
              "author": {"@id": SITE + "/about#wondermayank"}, "publisher": {"@id": SITE + "/#organization"}, "image": SITE + "/assets/og-image.png"},
             crumbs(path, [('Home', '/'), ('Formula library', '/formula'), (sname + ' formulas', '/' + spath), (d['name'], path)]),
             faq_node(path, qas)]
    write('formula/%s.html' % d['slug'], build_page(path, title, desc, main, '/formula', nodes))
    sitemap.append((path, '0.7'))

# ---------- subject pages ----------
for k, (sname, spath) in SUBJECTS.items():
    items = by_subject[k]
    path = '/' + spath
    title = '%s Formulas: Stories and Memory Tricks' % sname
    desc = trim('%d important %s formulas for Class 9 to 12, JEE, NEET, SSC and Banking, each explained with a short story and a memory trick. Free to read.' % (len(items), sname), 155)
    intro = '%s formulas are easier to remember as stories. This free library covers %s, each with its formula, a short story, a real-life analogy, a memory trick and an exam tip for students preparing for school exams, JEE, NEET, SSC and Banking.' % (sname, ', '.join(x['name'] for x in items))
    main = hero('%s library' % sname, '%s formulas,<br>explained as stories' % E(sname), E(intro), btn('/app', 'Make my own story') + '\n' + btn('/formula', 'Full library', False))
    main += '<div class="wrap">\n<section class="section"><div class="fgrid">%s</div></section>\n%s\n</div>\n%s' % (
        ''.join(fcard(x) for x in items), cta_card(), page_meta())
    nodes = [webpage(path, title, desc, 'CollectionPage', extra={"mainEntity": {"@id": SITE + path + "#list"}}),
             {"@type": "ItemList", "@id": SITE + path + "#list", "name": title, "numberOfItems": len(items),
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": x['name'], "url": SITE + '/formula/' + x['slug']} for i, x in enumerate(items)]},
             crumbs(path, [('Home', '/'), ('Formula library', '/formula'), (sname + ' formulas', path)])]
    write(spath + '.html', build_page(path, title, desc, main, '/formula', nodes))
    sitemap.append((path, '0.7'))

# ---------- library hub ----------
path = '/formula'
title = 'Free Formula Library: Physics, Chemistry, Maths, Biology'
desc = trim('A free formula library with %d formulas for Physics, Chemistry, Maths and Biology. Each has a story, an analogy, a memory trick and an exam tip.' % len(DATA), 155)
main = hero('Formula library', 'The free formula library,<br>one story per formula', E('Browse %d formulas across Physics, Chemistry, Maths and Biology for Class 9 to 12, JEE, NEET, SSC and Banking. Each page has the formula, a short story, a real-life analogy, a memory trick and an exam tip. Reading is free and uses none of your daily AI stories.' % len(DATA)), btn('/app', 'Make my own story'))
main += '<div class="wrap">\n<section class="section"><div class="lib-tools"><button type="button" id="accToggle">Expand all</button></div><div class="lib-acc">\n'
CHEV = '<svg class="acc-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
for n_, (k, (sname, spath)) in enumerate(SUBJECTS.items()):
    col, ic = SUBJ_STYLE[k]
    main += ('<details class="acc" style="--acc:%s"%s><summary><svg class="acc-ico" viewBox="0 0 24 24" aria-hidden="true">%s</svg><span>%s</span><span class="acc-count">%d</span>%s</summary>'
             '<div class="acc-body">%s%s</div></details>\n') % (col, ' open' if n_ == 0 else '', ic, E(sname), len(by_subject[k]), CHEV,
                 ''.join(fcard(x) for x in by_subject[k]), all_card(sname, spath, len(by_subject[k])))
main += '</div></section>\n<script>(function(){var b=document.getElementById("accToggle"),d=document.querySelectorAll("details.acc");if(!b)return;function sync(){var all=[].every.call(d,function(x){return x.open});b.textContent=all?"Collapse all":"Expand all"}b.addEventListener("click",function(){var all=[].every.call(d,function(x){return x.open});[].forEach.call(d,function(x){x.open=!all});sync()});[].forEach.call(d,function(x){x.addEventListener("toggle",sync)});sync()})();</script>\n'
main += cta_card('Not here yet?', 'More formulas are added regularly. If yours is missing, generate a story for it with the free AI tool.') + '\n</div>\n' + page_meta()
nodes = [webpage(path, title, desc, 'CollectionPage', extra={"mainEntity": {"@id": SITE + path + "#list"}}),
         {"@type": "ItemList", "@id": SITE + path + "#list", "name": title, "numberOfItems": len(DATA),
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": x['name'], "url": SITE + '/formula/' + x['slug']} for i, x in enumerate(DATA)]},
         crumbs(path, [('Home', '/'), ('Formula library', path)])]
write('formula.html', build_page(path, title, desc, main, '/formula', nodes))
sitemap.append((path, '0.8'))

# ---------- how it works ----------
path = '/how-it-works'
title = 'How ThunderStudy AI Works: Formula to Story'
desc = 'See how ThunderStudy AI turns any formula into a story, analogy or memory trick in four steps. Free, no account, with PDF export and a daily limit.'
steps = [('Type a topic or formula', 'Enter anything you want to remember, such as Ohm\'s law, the quadratic formula or photosynthesis.'),
         ('Choose a style', 'Pick Story Mode, Real-Life Analogy or Memory Trick, depending on how you like to remember things.'),
         ('Read and save it', 'Read the result, then save it as a PDF, copy the text or regenerate it. Saved stories stay on your own device.'),
         ('Use the free library', 'Browse ready-made formula pages any time. They do not use any of your daily AI stories.')]
qas = [('Is ThunderStudy AI free?', 'Yes. It is free, with no account or card. A fair-use limit of 5 AI stories a day and 15 a week keeps it free for everyone.'),
       ('Where is my data stored?', 'Saved stories and your usage count are kept in your own browser. There is no sign-up.'),
       ('Can the AI make mistakes?', 'Yes. Always check important formulas against your textbook or official exam material.')]
main = hero('How it works', 'From formula to story<br>in four steps', 'ThunderStudy AI takes a formula or topic, asks an AI model to explain it as a story, a real-life analogy or a memory trick, and lets you save the result as a PDF. It is free, needs no account and keeps your saved stories on your own device.', btn('/app', 'Try it now') + '\n' + btn('/examples', 'See examples', False))
main += '<div class="wrap">\n<section class="section"><ol class="steps">%s</ol></section>\n<section class="section"><div class="section-head"><div class="error-badge"><span class="error-dot"></span>FAQ</div><h2>Quick answers</h2></div><div class="narrow">%s</div></section>\n%s\n</div>\n%s' % (
    ''.join('<li><div class="card"><h3>%s</h3><p>%s</p></div></li>' % (E(a), E(b)) for a, b in steps), faq_html(qas), cta_card(), page_meta())
nodes = [webpage(path, title, desc),
         {"@type": "HowTo", "@id": SITE + path + "#howto", "name": "How to turn a formula into a story with ThunderStudy AI", "inLanguage": "en-IN",
          "totalTime": "PT1M", "tool": [{"@type": "HowToTool", "name": "ThunderStudy AI"}],
          "step": [{"@type": "HowToStep", "position": i + 1, "name": a, "text": b} for i, (a, b) in enumerate(steps)]},
         crumbs(path, [('Home', '/'), ('How it works', path)]), faq_node(path, qas)]
write('how-it-works.html', build_page(path, title, desc, main, None, nodes))
sitemap.append((path, '0.6'))

# ---------- examples ----------
path = '/examples'
title = 'Formula Story Examples: Story, Analogy, Memory Trick'
desc = 'See example stories, analogies and memory tricks for Ohm\'s law, the quadratic formula and photosynthesis, in the format ThunderStudy AI uses.'
pick = [('ohms-law', 'story', 'Story Mode'), ('quadratic-formula', 'analogy', 'Real-Life Analogy'), ('photosynthesis-equation', 'trick', 'Memory Trick')]
byslug = {d['slug']: d for d in DATA}
main = hero('Examples', 'Three ways to remember<br>one formula', 'These examples show the three styles ThunderStudy AI uses: a story, a real-life analogy and a memory trick. Results you generate yourself with the AI will differ, and every example links to its full library page.', btn('/app', 'Make my own') + '\n' + btn('/formula', 'Browse the library', False))
main += '<div class="wrap">\n<section class="section"><div class="grid">'
for slug, key, label in pick:
    d = byslug[slug]
    main += '<div class="card"><div class="tag-row"><span class="tag">%s</span></div><h3>%s</h3><p class="formula-line">%s</p><p>%s</p><a class="go" href="/formula/%s">Full page %s</a></div>' % (E(label), E(d['name']), E(d['formula']), E(d[key]), slug, ARROW)
main += '</div></section>\n' + cta_card() + '\n</div>\n' + page_meta(' Examples are written in the style of the tool and can contain mistakes.')
nodes = [webpage(path, title, desc, 'CollectionPage'), crumbs(path, [('Home', '/'), ('Examples', path)])]
write('examples.html', build_page(path, title, desc, main, None, nodes))
sitemap.append((path, '0.6'))

# ---------- status (noindex, not in sitemap) ----------
path = '/status'
title = 'Status | ThunderStudy AI'
desc = 'Live status of ThunderStudy AI: website, AI service and offline support, checked from your browser.'
main = hero('Status', 'Is ThunderStudy AI<br>working right now?', 'These checks run in your browser when you open this page. They tell you whether the website and the AI service are reachable.', btn('/app', 'Open the tool'))
main += '''<div class="wrap"><section class="section"><div class="card narrow">
<div class="status-row"><span>Website</span><span class="status-pill ok">Online</span></div>
<div class="status-row"><span>AI service</span><span class="status-pill" id="stApi">Checking...</span></div>
<div class="status-row"><span>AI key configured</span><span class="status-pill" id="stKey">Checking...</span></div>
<div class="status-row"><span>Offline support</span><span class="status-pill" id="stSw">Checking...</span></div>
<p>Checked at <span id="stTime">...</span>. If the AI service is down, try again later, or read the <a class="inline" href="/formula">free formula library</a>, which keeps working.</p>
</div></section></div>
<script>
(function(){
  function set(id,text,cls){var e=document.getElementById(id);e.textContent=text;e.className='status-pill'+(cls?' '+cls:'');}
  document.getElementById('stTime').textContent=new Date().toLocaleString();
  fetch('/api/generate',{cache:'no-store'}).then(function(r){return r.json();}).then(function(j){
    set('stApi','Online','ok'); set('stKey',j.configured?'Yes':'No',j.configured?'ok':'bad');
  }).catch(function(){set('stApi','Not reachable','bad');set('stKey','Unknown','');});
  if('serviceWorker' in navigator){navigator.serviceWorker.getRegistration().then(function(r){set('stSw',r?'Enabled':'Not installed yet',r?'ok':'');});}else{set('stSw','Not supported','');}
})();
</script>'''
write('status.html', build_page(path, title, desc, main, None, [webpage(path, title, desc)], robots='noindex, nofollow'))

# ---------- Hindi landing page ----------
path = '/hi'
title = 'फ़ॉर्मूले को कहानी बनाकर याद रखें | ThunderStudy AI'
desc = 'ThunderStudy AI किसी भी फ़ॉर्मूले को कहानी, रोज़मर्रा की मिसाल या याद रखने की ट्रिक में बदलता है। भौतिकी, रसायन, गणित और जीव विज्ञान के लिए मुफ़्त।'
hi_qas = [('क्या ThunderStudy AI मुफ़्त है?', 'हाँ, यह पूरी तरह मुफ़्त है। कोई अकाउंट या कार्ड नहीं चाहिए। बस रोज़ 5 और हफ़्ते में 15 AI कहानियों की सीमा है।'),
          ('यह किन विषयों के लिए है?', 'यह भौतिकी, रसायन, गणित और जीव विज्ञान के लिए है, और JEE, NEET, SSC, NTA व बैंकिंग की तैयारी में काम आता है।'),
          ('क्या AI की बनाई कहानियाँ हमेशा सही होती हैं?', 'नहीं। AI से ग़लती हो सकती है, इसलिए ज़रूरी फ़ॉर्मूले अपनी किताब या आधिकारिक सामग्री से मिला लें।')]
main = hero('हिंदी', 'किसी भी फ़ॉर्मूले को<br>कहानी बनाकर याद रखें', 'ThunderStudy AI एक मुफ़्त टूल है जो किसी भी फ़ॉर्मूले को कहानी, रोज़मर्रा की मिसाल या याद रखने की ट्रिक में बदल देता है। यह भौतिकी, रसायन, गणित और जीव विज्ञान के विद्यार्थियों और JEE, NEET, SSC, NTA व बैंकिंग की तैयारी करने वालों के लिए है। इसे Wondermayank ने बनाया है।', btn('/app', 'मुफ़्त टूल खोलें') + '\n' + btn('/formula', 'फ़ॉर्मूला लाइब्रेरी', False))
main += '<div class="wrap">\n<section class="section"><div class="section-head"><h2>तीन तरीक़े, एक फ़ॉर्मूला</h2></div><div class="grid">'
for ic, h, p in [('book', 'कहानी मोड', 'फ़ॉर्मूले को एक छोटी, यादगार कहानी में बदलता है।'), ('chat', 'असल ज़िंदगी की मिसाल', 'फ़ॉर्मूले की तुलना रोज़ की किसी चीज़ से करता है।'), ('bolt', 'याद रखने की ट्रिक', 'फ़ॉर्मूला जल्दी याद रखने के लिए एक छोटा सा हुक देता है।')]:
    main += '<div class="card">%s<h3>%s</h3><p>%s</p></div>' % (icon(ic), h, p)
main += '</div></section>\n<section class="section"><div class="card narrow"><h2>कैसे इस्तेमाल करें</h2><ul><li>विषय या फ़ॉर्मूला लिखें।</li><li>कहानी, मिसाल या ट्रिक चुनें।</li><li>नतीजा PDF में सेव करें या कॉपी करें।</li></ul><p>रोज़ 5 और हफ़्ते में 15 AI कहानियाँ मुफ़्त हैं। तैयार फ़ॉर्मूला लाइब्रेरी पढ़ने की कोई सीमा नहीं है। टूल का इंटरफ़ेस अभी अंग्रेज़ी में है।</p></div></section>\n'
main += '<section class="section"><div class="section-head"><div class="error-badge"><span class="error-dot"></span>अक्सर पूछे जाने वाले सवाल</div></div><div class="narrow">%s</div></section>\n</div>\n' % faq_html(hi_qas)
main += '<div class="wrap"><p class="page-meta">अंतिम अपडेट: <time datetime="%s">3 अक्टूबर 2026</time>। ThunderStudy का मालिक और संचालक <a href="/about">Wondermayank</a> है, जो एक अकेला विद्यार्थी डेवलपर है और 2018 से मुफ़्त शैक्षिक टूल बना रहा है।</p></div>' % TODAY
alts = [('en-IN', '/'), ('hi-IN', '/hi'), ('x-default', '/')]
nodes = [webpage(path, title, desc, 'WebPage', lang='hi-IN'), crumbs(path, [('होम', '/'), ('हिंदी', path)]), faq_node(path, hi_qas, 'hi-IN')]
write('hi.html', build_page(path, title, desc, main, None, nodes, lang='hi-IN', locale='hi_IN', alternates=alts))
sitemap.append((path, '0.7'))

# ---------- hreflang on the English landing page ----------
ix = (ROOT / 'index.html').read_text(encoding='utf-8')
if 'hreflang' not in ix:
    ix = re.sub(r'(<link rel="canonical" href="[^"]*">\r?\n)', lambda m: m.group(1) + ''.join('<link rel="alternate" hreflang="%s" href="%s">\n' % (h, SITE + u) for h, u in alts), ix, count=1)
    (ROOT / 'index.html').write_text(ix, encoding='utf-8')

# ---------- sitemap.xml ----------
core = [('/', '1.0'), ('/app', '0.9'), ('/about', '0.6'), ('/faq', '0.6'), ('/new', '0.5')]
seen, rows = set(), []
for p, pr in core + sitemap:
    if p in seen: continue
    seen.add(p)
    extra = ''
    if p in ('/', '/hi'):
        extra = ''.join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (h, SITE + u) for h, u in alts)
    rows.append('  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n    <priority>%s</priority>%s\n  </url>' % (SITE, p if p != '/' else '/', TODAY, pr, extra))
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(rows) + '\n</urlset>\n')

# ---------- llms.txt / llms-full.txt ----------
new_pages = [('Formula library', '/formula', 'All %d free formula pages for Physics, Chemistry, Maths and Biology.' % len(DATA))]
new_pages += [('%s formulas' % s, '/' + p, 'Formula stories and memory tricks for %s.' % s) for s, p in SUBJECTS.values()]
new_pages += [('How it works', '/how-it-works', 'The four steps from formula to story, with a short FAQ.'),
              ('Examples', '/examples', 'Example story, analogy and memory trick outputs.'),
              ('Hindi page', '/hi', 'Hindi introduction to ThunderStudy AI, for students who prefer Hindi.')]
lt = (ROOT / 'llms.txt').read_text(encoding='utf-8')
lt = re.sub(r'\n- \[(Formula library|Physics formulas|Chemistry formulas|Maths formulas|Biology formulas|How it works|Examples|Hindi page)\][^\n]*', '', lt)
block = ''.join('\n- [%s](%s%s): %s' % (n, SITE, u, dsc) for n, u, dsc in new_pages)
lt = lt.replace('\n\n## Optional', block + '\n\n## Optional', 1)
(ROOT / 'llms.txt').write_text(lt, encoding='utf-8')
lf = (ROOT / 'llms-full.txt').read_text(encoding='utf-8')
lf = re.split(r'\n## Library and guides', lf)[0].rstrip() + '\n'
lf += '\n## Library and guides\n\n' + '\n'.join('- %s: %s%s. %s' % (n, SITE, u, dsc) for n, u, dsc in new_pages) + '\n\n### Formula pages\n\n'
for d in DATA:
    lf += '- %s (%s): %s%s/formula/%s. %s is %s. %s\n' % (d['name'], SUBJECTS[d['subject']][0], '', SITE, d['slug'], d['name'], d['formula'], d['summary'])
(ROOT / 'llms-full.txt').write_text(lf, encoding='utf-8')
print('built', len(DATA), 'formula pages,', len(SUBJECTS), 'subject pages, hub, how-it-works, examples, status, hi,', len(rows), 'sitemap urls')
