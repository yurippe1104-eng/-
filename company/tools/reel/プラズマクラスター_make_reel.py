import subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
U = '/root/.claude/uploads/9d075f31-d237-53b4-b8b2-c8963c2f70e1/'
OUT = '/home/user/-/company/videos/プラズマクラスター_2090円_リール.mp4'
MARU = 'maru-ja.ttf'
NAVY, BLUE, RED = (24, 40, 110), (40, 110, 230), (225, 20, 50)
PINK, DPINK, TXT = (110, 180, 255), (20, 110, 230), (30, 50, 95)

def heart(d, cx, cy, s, fill):
    r = s * 0.3
    d.ellipse((cx - 2 * r, cy - r * 1.4, cx, cy + r * 0.6), fill=fill)
    d.ellipse((cx, cy - r * 1.4, cx + 2 * r, cy + r * 0.6), fill=fill)
    d.polygon([(cx - 1.95 * r, cy - 0.1 * r), (cx + 1.95 * r, cy - 0.1 * r), (cx, cy + 2.1 * r)], fill=fill)

def sparkle(d, cx, cy, s, fill):
    d.polygon([(cx, cy - s), (cx + s * .25, cy - s * .25), (cx + s, cy), (cx + s * .25, cy + s * .25), (cx, cy + s), (cx - s * .25, cy + s * .25), (cx - s, cy), (cx - s * .25, cy - s * .25)], fill=fill)



def load(p):
    return Image.open(p).convert('RGB')


def fit_with_blur_bg(img):
    """縦長画面に収め、余白はぼかした同じ写真で埋める"""
    bg = img.copy()
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1))
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new('RGB', (W, H), (0, 0, 0)), 0.25)
    s = min(W / img.width, H / img.height)
    fg = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


DELA = 'dela-ja.ttf'

def bubble(lines, size=70, accent=None):
    """aiboのときと同じ、白い吹き出しのテロップ（accent の行は赤で大きく）"""
    f = ImageFont.truetype(MARU, size)
    fa = ImageFont.truetype(MARU, int(size * 1.35))
    fn = ImageFont.truetype(DELA, int(size * 1.75))
    import re as _re
    fonts = [fn if _re.search(r'[0-9０-９]', t) else (fa if i == accent else f) for i, t in enumerate(lines)]
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    sizes = [d0.textbbox((0, 0), t, font=fo) for t, fo in zip(lines, fonts)]
    tw = max(b[2] - b[0] for b in sizes)
    lh = [b[3] - b[1] for b in sizes]
    gap = int(size * 0.35)
    bw = min(W - 60, tw + 110)
    bh = sum(lh) + gap * (len(lines) - 1) + 90
    im = Image.new('RGBA', (bw + 30, bh + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12, 18, bw + 12, bh + 18), radius=46, fill=(0, 0, 0, 70))
    d.rounded_rectangle((6, 6, bw + 6, bh + 6), radius=56, fill=(255, 255, 255, 250),
                        outline=PINK, width=9)
    d.rounded_rectangle((20, 20, bw - 8, bh - 8), radius=44, outline=(255, 215, 230), width=3)
    y = 6 + 45
    for t, fo, b, h_ in zip(lines, fonts, sizes, lh):
        x = 6 + (bw - (b[2] - b[0])) // 2 - b[0]
        if fo is fn:
            d.text((x, y - b[1]), t, font=fo, fill=RED, stroke_width=3, stroke_fill=(255, 255, 255))
        else:
            d.text((x, y - b[1]), t, font=fo, fill=DPINK if fo is fa else TXT)
        y += h_ + gap
    sparkle(d, bw - 4, 22, 30, (255, 190, 0))
    sparkle(d, 30, bh - 4, 18, (255, 225, 120))
    return im


def endcard():
    im = Image.new('RGB', (W, H))
    g = np.linspace(0, 1, H)[:, None]
    arr = (np.array([70, 150, 255]) * (1 - g) + np.array([20, 70, 200]) * g)
    im = Image.fromarray(np.repeat(arr[:, None, :], W, 1).astype(np.uint8).reshape(H, W, 3))
    d = ImageDraw.Draw(im)
    for i in range(0, 360, 12):
        a = np.deg2rad(i)
        d.polygon([(W / 2, 700), (W / 2 + 2000 * np.cos(a), 700 + 2000 * np.sin(a)),
                   (W / 2 + 2000 * np.cos(a + 0.09), 700 + 2000 * np.sin(a + 0.09))],
                  fill=(255, 255, 255))
    im = Image.blend(im, Image.fromarray(np.repeat(arr[:, None, :], W, 1).astype(np.uint8).reshape(H, W, 3)), 0.85)
    return im



DELA = 'dela-ja.ttf'

def big_text(text, size, grad=((255, 255, 235), (255, 225, 50), (255, 160, 0)), outline=(215, 40, 40)):
    f = ImageFont.truetype(DELA, size)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    b = d0.textbbox((0, 0), text, font=f, stroke_width=int(size * 0.16))
    w, h = b[2] - b[0] + 20, b[3] - b[1] + 30
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    o = (10 - b[0], 10 - b[1])
    d = ImageDraw.Draw(im)
    d.text((o[0] + 4, o[1] + 10), text, font=f, fill=(0, 0, 0, 90), stroke_width=int(size * .16), stroke_fill=(0, 0, 0, 90))
    d.text(o, text, font=f, fill=(255, 255, 255, 255), stroke_width=int(size * .16), stroke_fill=(255, 255, 255, 255))
    d.text(o, text, font=f, fill=outline, stroke_width=int(size * .09), stroke_fill=outline)
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text(o, text, font=f, fill=255)
    g = np.linspace(0, 1, h)[:, None]
    c0, c1, c2 = [np.array(c, float) for c in grad]
    col = np.where(g < .5, c0 + (c1 - c0) * (g / .5), c1 + (c2 - c1) * ((g - .5) / .5))
    gi = Image.fromarray(np.repeat(col[:, None, :], w, 1).reshape(h, w, 3).astype(np.uint8))
    im.paste(gi, (0, 0), m)
    return im

def pill(text, size, bg, fg, pad=(60, 26), icon=False):
    f = ImageFont.truetype(MARU, size)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    b = d0.textbbox((0, 0), text, font=f)
    iw = int(size * 1.2) if icon else 0
    w, h = b[2] - b[0] + pad[0] * 2 + iw, b[3] - b[1] + pad[1] * 2
    im = Image.new('RGBA', (w + 20, h + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 16, w + 8, h + 16), radius=h // 2, fill=(0, 0, 0, 80))
    d.rounded_rectangle((4, 4, w + 4, h + 4), radius=h // 2, fill=bg, outline=(255, 255, 255), width=6)
    x = 4 + pad[0]
    if icon:
        cy = 4 + h // 2; r = size * .48
        d.rounded_rectangle((x, cy - r, x + r * 2.1, cy + r * .8), radius=int(r * .5), fill=fg)
        d.polygon([(x + r * .5, cy + r * .7), (x + r * .3, cy + r * 1.25), (x + r * 1.0, cy + r * .75)], fill=fg)
        for k in range(3):
            d.ellipse((x + r * (.45 + .6 * k) - 5, cy - r * .1 - 5, x + r * (.45 + .6 * k) + 5, cy - r * .1 + 5), fill=bg)
        x += iw
    d.text((x - b[0], 4 + pad[1] - b[1]), text, font=f, fill=fg)
    return im

def pop(t, t0, dur=0.35):
    k = (t - t0) / dur
    if k <= 0: return 0.0
    if k >= 1: return 1.0
    c = 1.70158; k -= 1
    return 1 + (c + 1) * k ** 3 + c * k ** 2   # ease-out-back

def place(fr, el, cx, cy, sc):
    if sc <= 0.01: return
    e = el.resize((max(1, int(el.width * sc)), max(1, int(el.height * sc))), Image.LANCZOS)
    if sc < 1:
        a = np.array(e); a[..., 3] = (a[..., 3] * min(1, sc)).astype(np.uint8); e = Image.fromarray(a)
    fr.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))

def ray_bg(c_top=(70, 150, 255), c_bot=(15, 60, 190), center=(W / 2, 760)):
    g = np.linspace(0, 1, H)[:, None]
    arr = np.array(c_top) * (1 - g) + np.array(c_bot) * g
    base = Image.fromarray(np.repeat(arr[:, None, :], W, 1).astype(np.uint8).reshape(H, W, 3))
    rays = base.copy(); d = ImageDraw.Draw(rays)
    for i in range(0, 360, 12):
        a = np.deg2rad(i)
        d.polygon([center, (center[0] + 2500 * np.cos(a), center[1] + 2500 * np.sin(a)),
                   (center[0] + 2500 * np.cos(a + .1), center[1] + 2500 * np.sin(a + .1))], fill=(255, 255, 255))
    return Image.blend(rays, base, .86)

def polka(c_top=(238, 247, 255), c_bot=(190, 222, 255)):
    g = np.linspace(0, 1, H)[:, None]
    arr = np.array(c_top) * (1 - g) + np.array(c_bot) * g
    im = Image.fromarray(np.repeat(arr[:, None, :], W, 1).astype(np.uint8).reshape(H, W, 3))
    d = ImageDraw.Draw(im)
    for row, y in enumerate(range(-40, H + 80, 110)):
        for x in range(-40 + (55 if row % 2 else 0), W + 80, 110):
            d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, 255, 255))
    return im

PROFIT_BG = polka()
CARD_ROWS = [('売れた値段', '12,800円', TXT), ('仕入れ', '−2,090円', RED), ('送料', '−750円', RED), ('手数料（10%）', '−1,280円', RED)]
TITLE_P = pill('さて、利益はいくら？', 62, RED, (255, 255, 255))
LABEL_P = pill('利益', 62, (255, 255, 255), RED, pad=(70, 18))
STAMP = None

def make_stamp():
    im = Image.new('RGBA', (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 350, 350), fill=(255, 255, 255, 245), outline=RED, width=14)
    d.ellipse((34, 34, 326, 326), outline=PINK, width=4)
    f1 = ImageFont.truetype(MARU, 54); f2 = ImageFont.truetype(DELA, 96)
    d.text((180, 120), '利益率', font=f1, fill=RED, anchor='mm')
    d.text((180, 220), '68%', font=f2, fill=RED, anchor='mm')
    return im.rotate(-12, resample=Image.BICUBIC)
STAMP = make_stamp()

def profit_frame(t):
    fr = PROFIT_BG.copy().convert('RGBA')
    place(fr, TITLE_P, W / 2, 330, pop(t, 0.0))
    # white card
    card_s = pop(t, 0.15)
    if card_s > 0:
        card = Image.new('RGBA', (900, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, 899, 559), radius=48, fill=(255, 255, 255, 250), outline=PINK, width=8)
        f = ImageFont.truetype(MARU, 54)
        fv = ImageFont.truetype(DELA, 66)
        for i, (lab, val, col) in enumerate(CARD_ROWS):
            a = min(1, max(0, (t - (0.35 + 0.28 * i)) / 0.2))
            if a <= 0: continue
            y = 80 + i * 118
            c = tuple(int(255 + (cc - 255) * a) for cc in col)
            cl = tuple(int(255 + (cc - 255) * a) for cc in (130, 100, 115))
            d.text((60, y), lab, font=f, fill=cl, anchor='lm')
            d.text((840, y), val, font=fv, fill=c, anchor='rm')
            if i < 3:
                d.line((60, y + 59, 840, y + 59), fill=(225, 225, 232), width=3)
        place(fr, card, W / 2, 780, card_s)
    # profit number count-up
    k = min(1, max(0, (t - 1.45) / 0.75))
    if t > 1.35:
        place(fr, LABEL_P, W / 2, 1165, pop(t, 1.35))
        val = int(round(8680 * (1 - (1 - k) ** 3)))
        place(fr, big_text(f'{val:,}円', 190), W / 2, 1370, pop(t, 1.45, .3))
    if t > 2.3:
        place(fr, STAMP, 880, 1150, pop(t, 2.3, .3) * 0.85)
    return fr.convert('RGB')

def float_hearts(fr, t, seed=0):
    d = ImageDraw.Draw(fr); rng = np.random.default_rng(seed)
    for k in range(9):
        x = rng.uniform(60, W - 60); sp = rng.uniform(60, 120); ph = rng.uniform(0, H)
        y = (ph - t * sp) % (H + 100) - 50; sz = rng.uniform(28, 52)
        heart(d, x + 15 * np.sin(t * 2 + k), y, sz, (120, 190, 255, 210) if k % 2 else (255, 255, 255, 230))

AHA_BG = None
def aha_frame(t):
    global AHA_BG
    if AHA_BG is None: AHA_BG = polka()
    fr = AHA_BG.copy().convert('RGBA')
    float_hearts(fr, t, 2)
    place(fr, AHA_1, W / 2, 470, pop(t, 0.0))
    place(fr, AHA_2, W / 2, 640, pop(t, 0.15))
    place(fr, AHA_3, W / 2, 900, pop(t, 0.9))
    place(fr, AHA_4, W / 2, 1110, pop(t, 1.05) * (1 + 0.04 * np.sin(max(0, t - 1.4) * 9)))
    if t > 1.3:
        d = ImageDraw.Draw(fr)
        for k, (x, y) in enumerate([(170, 1000), (910, 1010), (220, 1220), (860, 1210)]):
            sc = pop(t, 1.3 + .08 * k) * (1 + .15 * np.sin(t * 8 + k))
            sparkle(d, x, y, 34 * sc, (255, 210, 60))
    return fr.convert('RGB')

def open_frame(t):
    z = 1.0 + 0.10 * ease(t / 1.5)
    cw, ch = W / z, H / z
    cx, cy = shelf_c
    l = min(max(cx - cw / 2, 0), W - cw); tp = min(max(cy - ch / 2, 0), H - ch)
    fr = shelf.resize((W, H), Image.BICUBIC, box=(l, tp, l + cw, tp + ch)).convert('RGBA')
    place(fr, OPEN_STORE, W / 2, 210, pop(t, 0.0, .25))
    place(fr, OPEN_A, W / 2, 370, pop(t, 0.05, .25))
    place(fr, OPEN_A2, W / 2, 520, pop(t, 0.1, .25))
    k = (t - 0.30) / 0.45
    bump = 1 + 0.18 * np.sin(np.pi * k) if 0 <= k <= 1 else 1.0
    place(fr, OPEN_B, W / 2, 1300, pop(t, 0.25, .3) * bump)
    place(fr, OPEN_B2, W / 2, 1480, pop(t, 0.35, .3))
    if 0.45 <= t <= 1.5:
        d = ImageDraw.Draw(fr)
        for j, (dx, dy, d0) in enumerate([(-420, -110, .45), (430, -90, .6), (400, 110, .75)]):
            a = (t - d0) / .5
            if 0 <= a <= 1: sparkle(d, W / 2 + dx, 1300 + dy, 50 * np.sin(np.pi * a), (255, 240, 120))
    return fr.convert('RGB')

def end_frame(t):
    fr = END_BG.copy().convert('RGBA')
    float_hearts(fr, t, 1)
    place(fr, END_T1, W / 2, 430, pop(t, 0.0))
    place(fr, END_T2, W / 2, 600, pop(t, 0.15))
    bob = 8 * np.sin(t * 5)
    place(fr, END_PILL, W / 2, 815 + bob, pop(t, 0.45))
    place(fr, END_FACE, W / 2, 1120, pop(t, 0.7))
    pulse = 1 + 0.035 * np.sin(max(0, t - 1.2) * 7)
    place(fr, END_FOLLOW, W / 2, 1440, pop(t, 1.0) * (pulse if t > 1.35 else 1))
    place(fr, END_NAME, W / 2, 1545, pop(t, 1.2))
    return fr.convert('RGB')


# ---- 表紙の「売れた〇〇円」をポンと弾ませる（シリーズ共通） ----
def find_sold_pill(cover_img):
    """表紙の右下にある赤い「売れた」の枠を自動で見つけて切り抜く"""
    im = cv2.cvtColor(np.array(cover_img), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); Hh, Ss, Vv = [c.astype(int) for c in cv2.split(hsv)]
    red = (((Hh < 8) | (Hh > 172)) & (Ss > 150) & (Vv > 120)).astype(np.uint8)
    red[:int(H * 0.78)] = 0; red[:, :int(W * 0.5)] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(red, 8)
    if n < 2: return None
    i = 1 + np.argmax(st[1:, 4])
    m = (lab == i).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    f = np.zeros_like(m); cv2.drawContours(f, cnts, -1, 1, -1)
    f = cv2.dilate(f, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    x, y, w, h = cv2.boundingRect(f)
    rgba = np.dstack([np.array(cover_img), cv2.GaussianBlur(f * 255, (5, 5), 0)])
    return Image.fromarray(rgba[y:y + h, x:x + w].astype(np.uint8), 'RGBA'), (x + w / 2, y + h / 2)

def cover_pop(fr, t):
    """0.3秒でポンッと大きくなって戻り、キラッと光る"""
    if SOLD_PILL is None: return fr
    pill, (cx, cy) = SOLD_PILL
    k = (t - 0.30) / 0.45
    sc = 1 + 0.20 * np.sin(np.pi * k) if 0 <= k <= 1 else 1.0
    if sc > 1.001:
        e = pill.resize((int(pill.width * sc), int(pill.height * sc)), Image.LANCZOS)
        cx = min(cx, W - e.width / 2 - 6)
        sh = Image.new('RGBA', e.size, (0, 0, 0, 0)); sh.putalpha(e.split()[3].point(lambda v: v * 0.35))
        fr.alpha_composite(sh, (int(cx - e.width / 2) + 6, int(cy - e.height / 2) + 12))
        fr.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
    if 0.45 <= t <= 1.4:
        d = ImageDraw.Draw(fr); pw, ph = pill.size
        for j, (dx, dy, d0) in enumerate([(-0.42, -0.45, 0.45), (0.46, -0.30, 0.6), (0.40, 0.48, 0.75)]):
            a = (t - d0) / 0.5
            if 0 <= a <= 1:
                sparkle(d, cx + dx * pw, cy + dy * ph, 46 * np.sin(np.pi * a), (255, 240, 120))
    return fr

# ---- 素材 ----
cover = load(U + 'e67f51f0-image.png').resize((W, H), Image.LANCZOS)
SOLD_PILL = find_sold_pill(cover)
shelf = fit_with_blur_bg(load('plasma_shelf.jpg'))
close_src = load('plasma_shelf.jpg')
close = fit_with_blur_bg(close_src)
sold = fit_with_blur_bg(load('plasma_sold.jpg'))
calc = fit_with_blur_bg(load(U + 'cf6b2f03-image.jpg'))
tagimg = None
end = endcard()
_bg = close_src.resize((W, W)).resize((W, H)).filter(ImageFilter.GaussianBlur(30))
END_BG = Image.blend(_bg, polka(), 0.82)

END_T1 = pill('最初、なにに見えた？', 60, (255, 255, 255), TXT, pad=(50, 16))
END_T2 = big_text('電球？ ライト？', 120)
END_PILL = pill('コメントで教えてね', 62, (255, 255, 255), RED, icon=True)
_f = close_src.crop((235, 230, 935, 930)).resize((380, 380), Image.LANCZOS)
_m = Image.new('L', (380, 380), 0); ImageDraw.Draw(_m).ellipse((0, 0, 379, 379), fill=255)
END_FACE = Image.new('RGBA', (420, 420), (0, 0, 0, 0)); _d = ImageDraw.Draw(END_FACE)
_d.ellipse((0, 0, 419, 419), fill=PINK); _d.ellipse((10, 10, 409, 409), fill=(255, 255, 255)); END_FACE.paste(_f, (20, 20), _m)
END_FOLLOW = pill('フォローして次の仕入れも見てね', 50, RED, (255, 255, 255), pad=(56, 26))
_nf = ImageFont.truetype(MARU, 48)
END_NAME = Image.new('RGBA', (600, 90), (0, 0, 0, 0))
ImageDraw.Draw(END_NAME).text((300, 45), '◆ ジャンク姉さん ◆', font=_nf, fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=(215, 40, 40))
def fitw(im, mw=W - 70):
    return im if im.width <= mw else im.resize((mw, int(im.height * mw / im.width)), Image.LANCZOS)
OPEN_STORE = pill('リサイクルショップの家電コーナー', 50, (255, 255, 255), TXT, pad=(46, 14))
OPEN_A = big_text('2,090円', 190, grad=((255, 255, 255), (245, 245, 245), (220, 220, 220)), outline=TXT)
OPEN_A2 = pill('のこれ、なに？', 64, (255, 255, 255), TXT, pad=(50, 16))
OPEN_B = fitw(big_text('12,800円', 250, grad=((255, 235, 235), (240, 30, 50), (190, 0, 20)), outline=(255, 255, 255)))
OPEN_B2 = pill('で売れた！', 70, RED, (255, 255, 255), pad=(56, 18))
AHA_1 = pill('ぱっと見は ただの白い筒', 58, (255, 255, 255), TXT, pad=(50, 16))
AHA_2 = big_text('でも正体を知ってたら', 96, grad=((255, 255, 255), (240, 236, 225), (200, 190, 170)), outline=TXT)
AHA_3 = pill('2,090円が', 80, RED, (255, 255, 255), pad=(50, 16))
def _six():
    a = big_text('価値 約', 120)
    b = big_text('6', 300, grad=((230, 0, 30), (230, 0, 30), (230, 0, 30)), outline=(255, 255, 255))
    c = big_text('倍！', 150)
    gap = -6
    w = a.width + b.width + c.width + gap * 2
    h = b.height
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    base = int(h * 0.86)
    im.alpha_composite(a, (0, h - a.height - 22))
    im.alpha_composite(b, (a.width + gap, 0))
    im.alpha_composite(c, (a.width + b.width + gap * 2, h - c.height - 22))
    if w > W - 40:
        im = im.resize((W - 40, int(h * (W - 40) / w)), Image.LANCZOS)
    return im
AHA_4 = _six()

# 写真の上での注目点（画面座標）: ズームの中心
def to_screen(src_size, pt):
    sw, sh = src_size
    s = min(W / sw, H / sh)
    return ((W - sw * s) / 2 + pt[0] * s, (H - sh * s) / 2 + pt[1] * s)

shelf_c = to_screen((1170, 1170), (585, 560))     # 本体
tag_c = to_screen((1170, 1170), (590, 520))       # 値札
top_c = to_screen((1170, 1170), (560, 330))       # 口金（電球のねじ）
logo_c = to_screen((1170, 1170), (590, 850))      # SHARP ロゴ
sold_c = to_screen((1072, 1528), (536, 450))
calc_c = to_screen((1091, 1499), (546, 1300))

T_Y = 1180  # テロップの縦位置（画面の真ん中より少し下。Instagramの文字やボタンに隠れない）

# (開始秒, 終了秒, 画像, ズーム開始, ズーム終了, 中心開始, 中心終了, テロップ)
def money_label(num, sub):
    a = big_text(num, 210, grad=((255, 235, 235), (240, 30, 50), (190, 0, 20)), outline=(255, 255, 255))
    b = pill(sub, 66, RED, (255, 255, 255), pad=(54, 16))
    im = Image.new('RGBA', (max(a.width, b.width), a.height + b.height - 20), (0, 0, 0, 0))
    im.alpha_composite(a, ((im.width - a.width) // 2, 0))
    im.alpha_composite(b, ((im.width - b.width) // 2, a.height - 20))
    return fitw(im)
SOLD_LABEL = money_label('12,800円', '売れました！')

segs = [
    (0.0, 1.5, 'OPEN'),
    (1.5, 4.0, close, 1.3, 2.0, shelf_c, top_c,
        bubble(['上は電球のねじ…', 'でも', '電球じゃないんです'], 62, accent=2), 1420),
    (4.0, 6.2, close, 1.9, 2.4, tag_c, tag_c,
        bubble(['お値段は', '2,090円', '（税込）'], 64), 1420),
    (6.2, 8.8, close, 1.4, 1.9, logo_c, logo_c,
        bubble(['正体は', 'シャープの', '「プラズマクラスター」'], 62, accent=2), 1420),
    (8.8, 11.4, close, 1.9, 1.5, top_c, shelf_c,
        bubble(['電球のソケットに', 'つけるタイプなんです'], 64, accent=0), 1420),
    (11.4, 13.6, close, 1.5, 1.35, shelf_c, shelf_c,
        bubble(['この形を', '探している人がいて', '知らないと見逃しちゃう'], 58, accent=2), 1420),
    (13.6, 15.8, sold, 1.0, 1.12, (W/2, H/2), sold_c,
        SOLD_LABEL, 1330),
    (15.8, 19.2, 'PROFIT'),
    (19.2, 21.8, 'AHA'),
    (21.8, 25.2, 'END'),
]
TOTAL = 25.2
XF = 0.18  # 切り替えのクロスフェード秒

def ease(t):
    return 0.5 - 0.5 * np.cos(np.pi * min(max(t, 0), 1))

def render_seg(seg, t):
    if seg[2] == 'PROFIT': return np.array(profit_frame(t - seg[0]))
    if seg[2] == 'END': return np.array(end_frame(t - seg[0]))
    if seg[2] == 'OPEN': return np.array(open_frame(t - seg[0]))
    if seg[2] == 'AHA': return np.array(aha_frame(t - seg[0]))
    s0, s1, img, z0, z1, c0, c1, tel = seg[:8]
    ty = seg[8] if len(seg) > 8 else T_Y
    p = ease((t - s0) / (s1 - s0))
    z = z0 + (z1 - z0) * p
    cx = c0[0] + (c1[0] - c0[0]) * p
    cy = c0[1] + (c1[1] - c0[1]) * p
    cw, ch = W / z, H / z
    l = min(max(cx - cw / 2, 0), W - cw)
    tp = min(max(cy - ch / 2, 0), H - ch)
    fr = img.resize((W, H), Image.BICUBIC, box=(l, tp, l + cw, tp + ch))
    if img is cover:
        fr = cover_pop(fr.convert('RGBA'), t - s0).convert('RGB')
    if tel is not None:
        k = min(1, (t - s0) / 0.25)  # テロップは少しはずんで出る
        sc = 0.85 + 0.15 * ease(k)
        tl = tel.resize((int(tel.width * sc), int(tel.height * sc)), Image.LANCZOS)
        if k < 1:
            a = np.array(tl); a[..., 3] = (a[..., 3] * ease(k)).astype(np.uint8); tl = Image.fromarray(a)
        fr = fr.convert('RGBA')
        fr.alpha_composite(tl, ((W - tl.width) // 2, int(ty - tl.height // 2)))
        fr = fr.convert('RGB')
    if seg[2] is end:
        d = ImageDraw.Draw(fr)
        f = ImageFont.truetype(MARU, 54)
        d.text((W / 2, 1560), 'ジャンク姉さん', font=f, fill=(255, 255, 255), anchor='mm',
               stroke_width=4, stroke_fill=NAVY)
    return np.array(fr)

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                         '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                         '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                         '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                         '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = int(TOTAL * FPS)
for i in range(n):
    t = i / FPS
    idx = next(k for k, s in enumerate(segs) if s[0] <= t < s[1] or k == len(segs) - 1)
    fr = render_seg(segs[idx], t).astype(np.float32)
    s0 = segs[idx][0]
    if idx > 0 and t - s0 < XF:
        a = (t - s0) / XF
        prev = render_seg(segs[idx - 1], t).astype(np.float32)
        fr = prev * (1 - a) + fr * a
    proc.stdin.write(fr.astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait()
print(OUT)
