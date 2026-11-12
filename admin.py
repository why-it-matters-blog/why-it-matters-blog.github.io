#!/usr/bin/env python3
"""Why It Matters - local dashboard + static site generator (Python 3, no extra installs)."""
import base64, datetime, hashlib, hmac, html, io, json, mimetypes, os, re, secrets, sys, threading, time, webbrowser, zipfile
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)
ARTS, PUB, IMGS = P('data', 'articles'), P('public'), P('public', 'images', 'posts')
SLUG = re.compile(r'^[a-z0-9][a-z0-9-]{0,80}$')
COLORS = ['pink', 'yellow', 'mint', 'lavender']
CARD = {'pink': 'c1', 'yellow': 'c2', 'mint': 'c3', 'lavender': 'c4'}
DEFAULTS = {
    'contact_email': 'hello@whyitmatters.com',
    'hero_title': 'Understand why it matters.',
    'hero_text': 'Plain-language guides that explain why everyday topics matter, and what you can do about them.',
    'blog_intro': 'Clear, practical guides on topics that matter in everyday life. Pick a topic and start reading.',
    'about_intro': 'We explain why things matter, in simple language, so you can make better decisions with confidence.',
    'about_text': "# Why we exist\n\nMany topics affect our daily lives, from staying safe online to looking after our health and managing money. Yet the information about them is often scattered, technical or overwhelming. Why It Matters was created to make these topics easy to understand.\n\n# Our approach\n\nEvery article follows one idea: explain what the topic is, show why it matters, and describe what you can do about it. We keep adding new topics, so there is always something new to learn.",
}

# ---------- storage ----------
def read_json(path, default):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except Exception: return default

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def settings():
    s = dict(DEFAULTS); s.update(read_json(P('data', 'settings.json'), {})); return s

def articles():
    out = []
    for fn in os.listdir(ARTS) if os.path.isdir(ARTS) else []:
        if fn.endswith('.json'):
            a = read_json(os.path.join(ARTS, fn), None)
            if a and SLUG.match(a.get('slug', '')): out.append(a)
    return sorted(out, key=lambda a: (a.get('date', ''), a['slug']), reverse=True)

def clean(a):
    s = str(a.get('slug', '')).strip().lower()
    if not SLUG.match(s): raise ValueError('Slug sirf small letters, numbers aur - se banta hai.')
    if not str(a.get('title', '')).strip(): raise ValueError('Title zaroori hai.')
    try: datetime.date.fromisoformat(a.get('date', ''))
    except Exception: a['date'] = datetime.date.today().isoformat()
    blocks = []
    for b in a.get('blocks', []):
        t = b.get('t')
        if t in ('h2', 'p'): blocks.append({'t': t, 'text': str(b.get('text', ''))})
        elif t in ('ul', 'ol'): blocks.append({'t': t, 'items': [str(i) for i in b.get('items', []) if str(i).strip()]})
        elif t == 'img': blocks.append({'t': 'img', 'src': str(b.get('src', '')), 'alt': str(b.get('alt', '')), 'caption': str(b.get('caption', ''))})
    return {
        'slug': s, 'title': str(a['title']).strip(), 'category': str(a.get('category', '')).strip(),
        'excerpt': str(a.get('excerpt', '')).strip(), 'date': a['date'],
        'status': 'draft' if a.get('status') == 'draft' else 'published',
        'color': a.get('color') if a.get('color') in COLORS else 'pink',
        'image': str(a.get('image', '')), 'image_alt': str(a.get('image_alt', '')), 'image_caption': str(a.get('image_caption', '')),
        'blocks': blocks,
        'faq': [{'q': str(f.get('q', '')).strip(), 'a': str(f.get('a', '')).strip()} for f in a.get('faq', []) if str(f.get('q', '')).strip()],
        'takeaway': str(a.get('takeaway', '')).strip(),
    }

# ---------- login ----------
AUTH, SESS, FAIL = P('data', 'auth.json'), {}, {'n': 0, 'until': 0}
SESSION_SECONDS = 12 * 3600
def hash_pw(pw, salt): return hashlib.pbkdf2_hmac('sha256', pw.encode(), bytes.fromhex(salt), 200_000).hex()
def set_auth(user, pw):
    salt = secrets.token_hex(16); write_json(AUTH, {'user': user, 'salt': salt, 'hash': hash_pw(pw, salt)})
def check_auth(user, pw):
    a = read_json(AUTH, None)
    return bool(a) and hmac.compare_digest(a['user'].encode(), user.encode()) and hmac.compare_digest(a['hash'].encode(), hash_pw(pw, a['salt']).encode())
def cookie(tok, age=SESSION_SECONDS): return {'Set-Cookie': f'wim_session={tok}; HttpOnly; SameSite=Strict; Path=/; Max-Age={age}'}

# ---------- pasted text -> article ----------
LBL = re.compile(r'^([A-Z][^.:?!]{2,60}):\s+(\S.*)$', re.S)

def to_blocks(bl):
    out, flag = [], False
    def add(kind, txt):
        if out and out[-1]['t'] == kind: out[-1]['items'].append(txt)
        else: out.append({'t': kind, 'items': [txt]})
    for b in bl:
        n = re.match(r'^\d+\.\s+(.*)$', b, re.S)
        bu = re.match(r'^[-•*]\s+(.*)$', b, re.S)
        if n: add('ol', n.group(1)); flag = False
        elif bu: add('ul', bu.group(1)); flag = False
        elif LBL.match(b) and not b.endswith(':'): add('ul', b); flag = False
        elif flag and len(b) <= 70: add('ul', b)
        else: out.append({'t': 'p', 'text': b}); flag = b.endswith(':')
    return out

def parse_text(t):
    bl = [b.strip() for b in re.split(r'\n\s*\n', t.replace('\r', '')) if b.strip()]
    a = {'title': '', 'excerpt': '', 'slug': '', 'category': '', 'blocks': [], 'faq': [], 'takeaway': ''}
    if not bl: return a
    a['title'] = bl.pop(0).lstrip('# ').strip()
    marked = any(b.startswith('# ') for b in bl)
    secs, flag = [[None, []]], False
    for i, b in enumerate(bl):
        nxt = bl[i + 1] if i + 1 < len(bl) else None
        head = b[2:].strip() if b.startswith('# ') else None
        kw = re.match(r'(?i)(frequently asked|faq\b|final thoughts|conclusion|seo details)', b) and '\n' not in b and len(b) <= 60
        if head is None and kw: head = b
        elif head is None and not marked and not flag and '\n' not in b and len(b) <= 90 and nxt \
           and not re.search(r'[.:;,!]$', b) and not re.match(r'^(\d+\.|[-•*])\s', b) and not LBL.match(b) \
           and not b.startswith('**') and not (secs[-1][0] or '').lower().startswith(('frequently', 'faq')):
            head = b
        if head is not None: secs.append([head, []]); flag = False
        else: secs[-1][1].append(b); flag = b.endswith(':') or (flag and len(b) <= 70)
    for head, bs in secs:
        low = (head or '').lower()
        if low.startswith('seo'):
            for b in bs:
                k, _, v = b.partition(':'); k = k.strip().lower(); v = v.strip()
                if k == 'meta description': a['excerpt'] = v
                elif k == 'url slug': a['slug'] = v
                elif k == 'primary keyword': a['category'] = v
        elif low.startswith(('frequently', 'faq')):
            for j in range(0, len(bs) - 1, 2): a['faq'].append({'q': bs[j].strip('*').strip(), 'a': bs[j + 1]})
        elif low.startswith(('final thoughts', 'conclusion')):
            a['blocks'].append({'t': 'h2', 'text': 'Final thoughts'})
            if len(bs) > 1: a['blocks'] += to_blocks(bs[:-1]); a['takeaway'] = bs[-1]
            else: a['takeaway'] = bs[0] if bs else ''
            if a['blocks'][-1]['t'] == 'h2': a['blocks'].pop()
        else:
            if head: a['blocks'].append({'t': 'h2', 'text': head})
            a['blocks'] += to_blocks(bs)
    return a

# ---------- html generation ----------
def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    return re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+|mailto:[^)\s]+|#[\w-]+)\)', r'<a href="\2">\1</a>', s)

def li(txt):
    m = re.match(r'^([^:.]{2,60}):\s+(\S.*)$', txt, re.S)
    return f'<li><b>{html.escape(m.group(1), quote=False)}:</b> {inline(m.group(2))}</li>' if m and '**' not in txt else f'<li>{inline(txt)}</li>'

def safe_src(s): return html.escape(s, quote=True) if re.match(r'^(images/|https?://)', s) else ''
def pretty(d):
    try: return datetime.date.fromisoformat(d).strftime('%d %b %Y').lstrip('0')
    except Exception: return ''

def simple(text):
    out = []
    for b in [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]:
        out.append(f'<h2>{inline(b[2:])}</h2>' if b.startswith('# ') else f'<p>{inline(b)}</p>')
    return '\n'.join(out)

def card(a):
    img = f'<img src="{safe_src(a["image"])}" alt="" loading="lazy">' if safe_src(a['image']) else ''
    tag = f'<span class="tag">{html.escape(a["category"])}</span>' if a['category'] else ''
    return (f'<a class="card {CARD[a["color"]]}" href="#{a["slug"]}">{img}<div>{tag}<h3>{html.escape(a["title"])}</h3>'
            f'<p>{html.escape(a["excerpt"])}</p></div><b>Read article</b></a>')

def article_page(a):
    body = []
    for i, b in enumerate(a['blocks']):
        t = b['t']
        if t == 'h2': body.append(f'<h2>{inline(b["text"])}</h2>')
        elif t == 'p': body.append(f'<p class="lead">{inline(b["text"])}</p>' if i == 0 else f'<p>{inline(b["text"])}</p>')
        elif t in ('ul', 'ol'): body.append(f'<{t}>' + ''.join(li(x) for x in b['items']) + f'</{t}>')
        elif t == 'img' and safe_src(b['src']):
            cap = f'<figcaption>{html.escape(b["caption"])}</figcaption>' if b['caption'] else ''
            body.append(f'<figure class="inpost"><img src="{safe_src(b["src"])}" alt="{html.escape(b["alt"])}" loading="lazy">{cap}</figure>')
    if a['faq']:
        body.append('<h2>Frequently asked questions</h2>')
        body += [f'<details><summary>{inline(f["q"])}</summary><p>{inline(f["a"])}</p></details>' for f in a['faq']]
    if a['takeaway']: body.append(f'<div class="take">{inline(a["takeaway"])}</div>')
    meta = ' · '.join(x for x in [html.escape(a['category']), pretty(a['date'])] if x)
    fig = ''
    if safe_src(a['image']):
        cap = f'<p>{html.escape(a["image_caption"])}</p>' if a['image_caption'] else ''
        fig = f'<div class="figure"><img src="{safe_src(a["image"])}" alt="{html.escape(a["image_alt"])}">{cap}</div>'
    desc = f'<p>{html.escape(a["excerpt"])}</p>' if a['excerpt'] else ''
    return (f'<article id="{a["slug"]}" class="a-{a["color"]}"><section style="display:contents">'
            f'<div class="top"><div class="wrap"><a href="#home">&larr; All articles</a><h1 style="margin-top:14px">{html.escape(a["title"])}</h1>{desc}'
            f'<div class="meta">{meta}</div></div></div>{fig}<div class="body">' + '\n'.join(body) + '</div></section></article>')

def build():
    s, arts = settings(), [a for a in articles() if a.get('status') != 'draft']
    cards = ''.join(card(a) for a in arts) or '<p class="empty">No articles yet.</p>'
    home = ''.join(card(a) for a in arts[:3]) or '<p class="empty">No articles yet.</p>'
    more = '<div class="more"><a class="btn" href="#blog">View all articles</a></div>' if len(arts) > 3 else ''
    e = html.escape
    main = f'''<main>
<section id="home">
<div class="hero"><span class="blob b1"></span><span class="blob b2"></span><span class="blob b3"></span>
<div class="wrap"><h1>{e(s['hero_title'])}</h1><p>{e(s['hero_text'])}</p><a class="btn" href="#articles">Start reading</a></div></div>
<div class="wrap grid" id="articles"><h2 class="t">Latest articles</h2>{home}</div>{more}
</section>
<section id="blog"><div class="top"><div class="wrap"><h1>Blog</h1><p>{e(s['blog_intro'])}</p></div></div>
<div class="wrap grid blog-grid">{cards}</div></section>
<section id="about"><div class="top"><div class="wrap"><h1>About us</h1><p>{e(s['about_intro'])}</p></div></div>
<div class="body">{simple(s['about_text'])}<p><a class="btn" href="#blog">Read the blog</a></p></div></section>
<section id="contact"><div class="top"><div class="wrap"><h1>Contact us</h1><p>Have a question, a topic idea or feedback? Send us a message.</p></div></div>
<div class="body"><form action="mailto:{e(s['contact_email'], quote=True)}" method="post" enctype="text/plain">
<label>Your name<input type="text" name="name" autocomplete="name" required></label>
<label>Email address<input type="email" name="email" autocomplete="email" required></label>
<label>Message<textarea name="message" required></textarea></label>
<button class="btn" type="submit">Send message</button></form></div></section>
{chr(10).join(article_page(a) for a in arts)}
</main>'''
    head = open(P('templates', 'head.html'), encoding='utf-8').read()
    tail = open(P('templates', 'tail.html'), encoding='utf-8').read()
    with open(os.path.join(PUB, 'index.html'), 'w', encoding='utf-8') as f: f.write(head + main + tail)
    return len(arts)

# ---------- server ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def out(self, code, body, ct='application/json', hdr=None):
        if not isinstance(body, bytes): body = (json.dumps(body, ensure_ascii=False) if ct == 'application/json' else body).encode('utf-8')
        self.send_response(code); self.send_header('Content-Type', ct + ('; charset=utf-8' if ct.startswith('text') or ct == 'application/json' else ''))
        self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control', 'no-store')
        for k, v in (hdr or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)
    def local(self): return self.headers.get('Host', '').split(':')[0] in ('127.0.0.1', 'localhost')
    def token(self):
        c = SimpleCookie(self.headers.get('Cookie', '')); return c['wim_session'].value if 'wim_session' in c else ''
    def authed(self):
        t = self.token(); return bool(t) and SESS.get(t, 0) > time.time()
    def do_GET(self):
        if not self.local(): return self.out(403, {'error': 'forbidden'})
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == '/api/status': return self.out(200, {'setup': not os.path.exists(AUTH), 'authed': self.authed()})
        if u.path == '/': return self.out(200, open(P('dashboard', 'index.html' if self.authed() else 'login.html'), 'rb').read(), 'text/html')
        if u.path.startswith('/api/') and not self.authed(): return self.out(401, {'error': 'Login zaroori hai.'})
        if u.path == '/api/articles': return self.out(200, articles())
        if u.path == '/api/settings': return self.out(200, settings())
        if u.path == '/api/zip':
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
                for d, _, fs in os.walk(PUB):
                    for fn in fs: z.write(os.path.join(d, fn), os.path.relpath(os.path.join(d, fn), PUB))
            return self.out(200, buf.getvalue(), 'application/zip', {'Content-Disposition': 'attachment; filename="why-it-matters-site.zip"'})
        if u.path.startswith('/site/'):
            rel = u.path[6:] or 'index.html'
            f = os.path.realpath(os.path.join(PUB, rel))
            if f.startswith(os.path.realpath(PUB) + os.sep) and os.path.isfile(f):
                return self.out(200, open(f, 'rb').read(), mimetypes.guess_type(f)[0] or 'application/octet-stream')
        self.out(404, {'error': 'not found'})
    def do_POST(self):
        if not self.local() or self.headers.get('X-Admin') != '1': return self.out(403, {'error': 'forbidden'})
        try:
            d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            path = urlparse(self.path).path
            if path == '/api/login':
                if time.time() < FAIL['until']: raise ValueError(f"Bahut zyada galat koshish. {int(FAIL['until'] - time.time()) + 1} second baad try karo.")
                if check_auth(str(d.get('username', '')), str(d.get('password', ''))):
                    FAIL['n'] = 0; tok = secrets.token_urlsafe(32); SESS[tok] = time.time() + SESSION_SECONDS
                    return self.out(200, {'ok': True}, hdr=cookie(tok))
                FAIL['n'] += 1; time.sleep(0.7)
                if FAIL['n'] >= 5: FAIL['until'] = time.time() + min(300, 30 * FAIL['n'])
                raise ValueError('Username ya password galat hai.')
            if path == '/api/setup':
                if os.path.exists(AUTH): raise ValueError('Login pehle se bana hua hai.')
                u_, p_ = str(d.get('username', '')).strip(), str(d.get('password', ''))
                if len(u_) < 3: raise ValueError('Username kam se kam 3 characters ka rakho.')
                if len(p_) < 8: raise ValueError('Password kam se kam 8 characters ka rakho.')
                set_auth(u_, p_); tok = secrets.token_urlsafe(32); SESS[tok] = time.time() + SESSION_SECONDS
                return self.out(200, {'ok': True}, hdr=cookie(tok))
            if not self.authed(): return self.out(401, {'error': 'Login zaroori hai.'})
            if path == '/api/logout':
                SESS.pop(self.token(), None); return self.out(200, {'ok': True}, hdr=cookie('', 0))
            if path == '/api/password':
                a = read_json(AUTH, {})
                if not check_auth(a.get('user', ''), str(d.get('old', ''))): raise ValueError('Purana password galat hai.')
                if len(str(d.get('new', ''))) < 8: raise ValueError('Naya password kam se kam 8 characters ka rakho.')
                set_auth(a['user'], str(d['new'])); keep = self.token(); SESS.clear(); SESS[keep] = time.time() + SESSION_SECONDS
                return self.out(200, {'ok': True})
            if path == '/api/article':
                a = clean(d['article']); old = d.get('old_slug', '')
                if a['slug'] != old and os.path.exists(os.path.join(ARTS, a['slug'] + '.json')): raise ValueError('Is slug ka article pehle se hai.')
                write_json(os.path.join(ARTS, a['slug'] + '.json'), a)
                if old and old != a['slug'] and SLUG.match(old) and os.path.exists(os.path.join(ARTS, old + '.json')): os.remove(os.path.join(ARTS, old + '.json'))
                return self.out(200, {'ok': True, 'live': build(), 'slug': a['slug']})
            if path == '/api/delete':
                s = d.get('slug', '')
                if SLUG.match(s) and os.path.exists(os.path.join(ARTS, s + '.json')): os.remove(os.path.join(ARTS, s + '.json'))
                return self.out(200, {'ok': True, 'live': build()})
            if path == '/api/settings':
                write_json(P('data', 'settings.json'), {k: str(d.get(k, DEFAULTS[k])) for k in DEFAULTS}); return self.out(200, {'ok': True, 'live': build()})
            if path == '/api/parse': return self.out(200, parse_text(d.get('text', '')))
            if path == '/api/build': return self.out(200, {'ok': True, 'live': build()})
            if path == '/api/upload':
                ext = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/webp': 'webp', 'image/gif': 'gif', 'image/svg+xml': 'svg'}
                m = re.match(r'^data:([\w/+.-]+);base64,(.+)$', d.get('data', ''), re.S)
                if not m or m.group(1) not in ext: raise ValueError('Sirf png, jpg, webp, gif ya svg image allowed hai.')
                raw = base64.b64decode(m.group(2))
                if len(raw) > 8_000_000: raise ValueError('Image 8 MB se badi hai.')
                os.makedirs(IMGS, exist_ok=True)
                base = re.sub(r'[^a-z0-9-]+', '-', os.path.splitext(str(d.get('name', 'image')))[0].lower()).strip('-')[:40] or 'image'
                fn = f'{base}-{int(time.time())}.{ext[m.group(1)]}'
                with open(os.path.join(IMGS, fn), 'wb') as f: f.write(raw)
                return self.out(200, {'path': 'images/posts/' + fn})
            self.out(404, {'error': 'not found'})
        except Exception as ex:
            self.out(400, {'error': str(ex)})

def main():
    os.makedirs(ARTS, exist_ok=True); build()
    for port in range(8000, 8011):
        try: srv = ThreadingHTTPServer(('127.0.0.1', port), H); break
        except OSError: continue
    else: sys.exit('Koi port free nahi mila (8000-8010).')
    url = f'http://localhost:{port}/'
    print(f'\n  Dashboard chal raha hai: {url}\n  Band karne ke liye is window mein Ctrl+C dabayein.\n')
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: print('\n  Dashboard band.')

if __name__ == '__main__': main()
