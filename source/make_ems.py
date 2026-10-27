"""Derive Eight Mile Sans from the Outfit Glyphs source (SIL OFL 1.1).

Changes, applied per master so the variable font stays compatible:
  1. Taller x-height (lowercase stretched between baseline and x-height,
     ascenders kept, dots/accents lifted rigidly).
  2. Slightly wider lowercase, so bowls stay round at the new height.
  3. Lowercase weight compensated (interpolated a little toward the lighter
     master) so the stretch doesn't make lowercase heavier than caps.
  4. More open spacing across letters, figures and punctuation.
  5. Outfit's own "outfit" wordmark ligatures removed; family renamed.

Usage: python3 make_ems.py <in.glyphs> <out.glyphs>
"""
import sys
import unicodedata
import glyphsLib
from glyphsLib.types import Point

SRC, OUT = sys.argv[1], sys.argv[2]

K_XH = 1.06        # x-height multiplier
W_LC = 1.035       # lowercase width multiplier
SPACE = 7          # units added to each side bearing (all spacing glyphs)
COMP = 0.05        # fraction of stem weight to remove from lowercase
OVS = 20           # overshoot allowance above x-height

font = glyphsLib.GSFont(SRC)
masters = {m.id: m for m in font.masters}
mlist = sorted(font.masters, key=lambda m: m.axes[0])
orig_xh = {m.id: m.xHeight for m in font.masters}
orig_asc = {m.id: m.ascender for m in font.masters}

# ---------- classification ----------
def base_name(n):
    return n.split('.')[0]

def is_lower(g):
    n = base_name(g.name)
    if g.name.startswith('o_u_t_f_i_t'):
        return True
    parts = n.split('_') if '_' in n else [n]
    ok = []
    for p in parts:
        pg = font.glyphs[p]
        u = None
        if pg is not None and pg.unicode:
            u = pg.unicode
        elif g.unicode and p == n:
            u = g.unicode
        if u:
            try:
                ok.append(unicodedata.category(chr(int(u, 16))) == 'Ll')
            except Exception:
                ok.append(False)
        else:
            ok.append(p in ('dotlessi', 'idotless', 'dotlessj', 'jdotless'))
    return bool(ok) and all(ok)

def is_mark(name):
    g = font.glyphs[name]
    if g is None:
        return False
    if g.name.endswith('comb') or '.case' in g.name and 'comb' in g.name:
        return True
    return any(a.name.startswith('_') for l in g.layers for a in l.anchors)

lower = {g.name for g in font.glyphs if is_lower(g)}
marks = {g.name for g in font.glyphs if is_mark(g.name)}

def spacing_glyph(g):
    if g.name in marks or g.name in ('.notdef',):
        return False
    lay = [l for l in g.layers if l.layerId == l.associatedMasterId]
    return any(l.width > 0 for l in lay)

# ---------- geometry ----------
def fy(y, mid):
    xh, asc = orig_xh[mid], orig_asc[mid]
    T, A = xh + OVS, asc + OVS
    if y <= 0:
        return y
    if y <= T:
        return y * K_XH
    if y <= A:
        return T * K_XH + (y - T) * (A - T * K_XH) / (A - T)
    return y

def lift(mid):
    return (orig_xh[mid] + OVS) * (K_XH - 1)

def master_of(layer):
    return layer.associatedMasterId

def stems():
    out = {}
    for m in font.masters:
        b = font.glyphs['l'].layers[m.id].bounds
        out[m.id] = b.size.width
    return out
STEM = stems()

def lighter(mid):
    i = [m.id for m in mlist].index(mid)
    return mlist[i - 1].id if i > 0 else None

def compatible(a, b):
    if len(a.paths) != len(b.paths):
        return False
    return all(len(p.nodes) == len(q.nodes) for p, q in zip(a.paths, b.paths))

def compensate(g, layer):
    mid = master_of(layer)
    if layer.layerId != mid:
        return
    lid = lighter(mid)
    if lid is None or not layer.paths:
        return
    ref = g.layers[lid]
    if not compatible(layer, ref):
        print('  skip comp (incompatible):', g.name)
        return
    t = COMP * STEM[mid] / (STEM[mid] - STEM[lid])
    for p, q in zip(layer.paths, ref.paths):
        for n, r in zip(p.nodes, q.nodes):
            n.position = Point(n.position.x + t * (r.position.x - n.position.x),
                               n.position.y + t * (r.position.y - n.position.y))
    ra = {a.name: a for a in ref.anchors}
    for a in layer.anchors:
        if a.name in ra:
            r = ra[a.name].position
            a.position = Point(a.position.x + t * (r.x - a.position.x),
                               a.position.y + t * (r.y - a.position.y))
    layer.width = layer.width + t * (ref.width - layer.width)

def transform_point(x, y, mid, lc):
    if lc:
        return x * W_LC + SPACE, fy(y, mid)
    return x + SPACE, y

def transform_paths(layer, lc):
    mid = master_of(layer)
    for p in layer.paths:
        ys = [n.position.y for n in p.nodes]
        rigid = lc and min(ys) > orig_xh[mid] + OVS
        for n in p.nodes:
            x, y = n.position.x, n.position.y
            if rigid:
                nx, _ = transform_point(x, y, mid, lc)
                n.position = Point(nx, y + lift(mid))
            else:
                n.position = Point(*transform_point(x, y, mid, lc))

def attach_anchor(mark_layer):
    for a in mark_layer.anchors:
        if a.name.startswith('_'):
            return a
    return None

def transform_components(g, layer, lc):
    mid = master_of(layer)
    for c in layer.components:
        px, py = c.position.x, c.position.y
        if c.name in marks:
            mg = font.glyphs[c.name]
            ml = mg.layers[mid] if mg is not None else None
            att = attach_anchor(ml) if ml is not None else None
            ax, ay = (att.position.x, att.position.y) if att else (0, 0)
            P = (px + ax, py + ay)
            nx, ny = transform_point(P[0], P[1], mid, lc)
            c.position = Point(nx - ax, ny - ay)
        else:
            c.position = Point(px * W_LC if lc else px, py)

def transform_anchors(layer, lc):
    mid = master_of(layer)
    for a in layer.anchors:
        x, y = a.position.x, a.position.y
        a.position = Point(*transform_point(x, y, mid, lc))

# ---------- apply ----------
count = 0
for g in font.glyphs:
    if not spacing_glyph(g):
        continue
    lc = g.name in lower
    for layer in g.layers:
        if layer.associatedMasterId not in masters:
            continue
        # backup layers (named, not master/brace/bracket) are not exported; skip
        is_master = layer.layerId == layer.associatedMasterId
        is_special = layer.name and ('[' in layer.name or '{' in layer.name)
        if not (is_master or is_special):
            continue
        if lc and is_master:
            compensate(g, layer)
        transform_paths(layer, lc)
        transform_components(g, layer, lc)
        transform_anchors(layer, lc)
        layer.width = round(layer.width * W_LC + 2 * SPACE) if lc else layer.width + 2 * SPACE
        for p in layer.paths:
            for n in p.nodes:
                n.position = Point(round(n.position.x), round(n.position.y))
        for a in layer.anchors:
            a.position = Point(round(a.position.x), round(a.position.y))
        for c in layer.components:
            c.position = Point(round(c.position.x), round(c.position.y))
    count += 1
print('transformed glyphs:', count, 'lowercase:', len(lower))

# ---------- metrics ----------
for m in font.masters:
    old = m.xHeight
    new = round(old * K_XH)
    m.xHeight = new
    for z in m.alignmentZones:
        if z.position == old:
            z.position = new
    print('master', m.name, 'x-height', old, '->', new)

# ---------- add Azerbaijani schwa (ə U+0259, Ə U+018F) ----------
from glyphsLib.classes import GSGlyph, GSLayer, GSPath, GSNode

def e_paths(mid, scale):
    """e outlines rotated 180 degrees, scaled about the baseline."""
    lay = font.glyphs['e'].layers[mid]
    b = lay.bounds
    cx = b.origin.x + b.size.width / 2
    cy = b.origin.y + b.size.height / 2
    out = []
    for p in lay.paths:
        q = GSPath()
        q.closed = p.closed
        for n in p.nodes:
            x = 2 * cx - n.position.x
            y = 2 * cy - n.position.y
            q.nodes.append(GSNode(Point(x, y * scale), n.type, n.smooth))
        out.append(q)
    return out, lay.width, b

def add_glyph(name, uni, build, rgroup):
    g = GSGlyph(name)
    g.unicode = uni
    g.rightKerningGroup = rgroup
    font.glyphs.append(g)
    for m in font.masters:
        layer = GSLayer()
        layer.layerId = m.id
        layer.associatedMasterId = m.id
        paths, width = build(m)
        layer.paths = paths
        layer.width = width
        g.layers.append(layer)

def lower_schwa(m):
    paths, width, _ = e_paths(m.id, 1.0)
    return paths, width

def upper_schwa(m):
    # scale e up to cap height, then pull the stroke weight back toward
    # the neighbouring master so the stems match the capitals
    s = m.capHeight / m.xHeight
    idx = [x.id for x in mlist].index(m.id)
    ref = mlist[idx - 1] if idx > 0 else mlist[1]
    stem = STEM[m.id]
    ps, w, b = e_paths(m.id, s)
    pr, wr, br = e_paths(ref.id, ref.capHeight / ref.xHeight)
    # bring both scaled shapes to the same horizontal scale as height
    def hscale(paths, bb, sc):
        cx = bb.origin.x
        for p in paths:
            for n in p.nodes:
                n.position = Point(cx + (n.position.x - cx) * sc, n.position.y)
    hscale(ps, b, s * 0.94)
    hscale(pr, br, (ref.capHeight / ref.xHeight) * 0.94)
    stem_s, stem_r = STEM[m.id] * s, STEM[ref.id] * (ref.capHeight / ref.xHeight)
    t = (stem_s - stem) / (stem_s - stem_r)
    for p, q in zip(ps, pr):
        for n, r in zip(p.nodes, q.nodes):
            n.position = Point(round(n.position.x + t * (r.position.x - n.position.x)),
                               round(n.position.y + t * (r.position.y - n.position.y)))
    xs = [n.position.x for p in ps for n in p.nodes]
    lsb = font.glyphs['O'].layers[m.id].bounds.origin.x
    shift = lsb - min(xs)
    for p in ps:
        for n in p.nodes:
            n.position = Point(n.position.x + shift, n.position.y)
    width = round(max(xs) + shift + lsb)
    return ps, width

add_glyph('schwa', '0259', lower_schwa, 'o')
add_glyph('Schwa', '018F', upper_schwa, 'O')
print('added schwa, Schwa')

# ---------- drop the Outfit wordmark ligatures ----------
for name in [g.name for g in font.glyphs if g.name.startswith('o_u_t_f_i_t')]:
    del font.glyphs[name]
for fe in font.features:
    fe.code = '\n'.join(l for l in fe.code.split('\n') if 'o_u_t_f_i_t' not in l)
for cls in font.classes:
    cls.code = ' '.join(t for t in cls.code.split() if not t.startswith('o_u_t_f_i_t'))

# ---------- naming ----------
font.familyName = 'Eight Mile Sans'
font.versionMajor, font.versionMinor = 1, 0
font.save(OUT)

text = open(OUT, encoding='utf-8').read()
subs = [
    ('value = "Copyright 2021 The Outfit Project Authors (https://github.com/Outfitio/Outfit-Fonts)";',
     'value = "Copyright 2021 The Outfit Project Authors (https://github.com/Outfitio/Outfit-Fonts). '
     'Copyright 2026 Eight Mile Services Ltd (modified version: Eight Mile Sans)";'),
    ('value = "Rodrigo Fuenzalida";', 'value = "Rodrigo Fuenzalida (Outfit); Eight Mile Services Ltd";'),
    ('value = fragTYPE;', 'value = "Eight Mile Services Ltd";'),
    ('value = www.fragtypefoundry.xyz;', 'value = "https://eightmile.co.uk";'),
    ('value = www.rfuenzalida.com;', 'value = "https://eightmile.co.uk";'),
    ('key = vendorID;\nvalue = frag;', 'key = vendorID;\nvalue = EMSL;'),
]
for a, b in subs:
    if a not in text:
        print('WARN naming pattern not found:', a[:50])
    text = text.replace(a, b)
open(OUT, 'w', encoding='utf-8').write(text)
print('saved', OUT)
