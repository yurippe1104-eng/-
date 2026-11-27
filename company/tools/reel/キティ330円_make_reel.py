import subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
U = '/root/.claude/uploads/9d075f31-d237-53b4-b8b2-c8963c2f70e1/'
OUT = '/home/user/-/company/videos/キティ_オフハウス330円_リール.mp4'
MARU = 'maru-ja.ttf'
NAVY, BLUE, RED = (24, 40, 110), (40, 110, 230), (225, 20, 50)


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


def bubble(lines, size=70, accent=None):
    """aiboのときと同じ、白い吹き出しのテロップ（accent の行は赤で大きく）"""
    f = ImageFont.truetype(MARU, size)
    fa = ImageFont.truetype(MARU, int(size * 1.35))
    fonts = [fa if i == accent else f for i in range(len(lines))]
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
    d.rounded_rectangle((6, 6, bw + 6, bh + 6), radius=46, fill=(255, 255, 255, 250),
                        outline=BLUE, width=10)
    y = 6 + 45
    for t, fo, b, h_ in zip(lines, fonts, sizes, lh):
        x = 6 + (bw - (b[2] - b[0])) // 2 - b[0]
        d.text((x, y - b[1]), t, font=fo, fill=RED if fo is fa else NAVY)
        y += h_ + gap
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

def big_text(text, size, grad=((255, 250, 210), (255, 220, 40), (255, 150, 0)), outline=RED):
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

PROFIT_BG = ray_bg()
CARD_ROWS = [('売れた値段', '5,980円', NAVY), ('仕入れ', '−330円', RED), ('送料', '−160円', RED), ('手数料（10%）', '−598円', RED)]
TITLE_P = pill('結局いくら残った？', 64, RED, (255, 255, 255))
LABEL_P = pill('利益', 62, (255, 255, 255), NAVY, pad=(70, 18))
STAMP = None

def make_stamp():
    im = Image.new('RGBA', (360, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 350, 350), fill=(255, 255, 255, 245), outline=RED, width=14)
    d.ellipse((34, 34, 326, 326), outline=RED, width=4)
    f1 = ImageFont.truetype(MARU, 54); f2 = ImageFont.truetype(DELA, 96)
    d.text((180, 120), '利益率', font=f1, fill=RED, anchor='mm')
    d.text((180, 220), '82%', font=f2, fill=RED, anchor='mm')
    return im.rotate(-12, resample=Image.BICUBIC)
STAMP = make_stamp()

def profit_frame(t):
    fr = PROFIT_BG.copy().convert('RGBA')
    place(fr, TITLE_P, W / 2, 330, pop(t, 0.0))
    # white card
    card_s = pop(t, 0.15)
    if card_s > 0:
        card = Image.new('RGBA', (900, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, 899, 559), radius=40, fill=(255, 255, 255, 250))
        f = ImageFont.truetype(MARU, 54)
        for i, (lab, val, col) in enumerate(CARD_ROWS):
            a = min(1, max(0, (t - (0.35 + 0.28 * i)) / 0.2))
            if a <= 0: continue
            y = 80 + i * 118
            c = tuple(int(255 + (cc - 255) * a) for cc in col)
            cl = tuple(int(255 + (cc - 255) * a) for cc in (80, 80, 90))
            d.text((60, y), lab, font=f, fill=cl, anchor='lm')
            d.text((840, y), val, font=f, fill=c, anchor='rm')
            if i < 3:
                d.line((60, y + 59, 840, y + 59), fill=(225, 225, 232), width=3)
        place(fr, card, W / 2, 780, card_s)
    # profit number count-up
    k = min(1, max(0, (t - 1.45) / 0.75))
    if t > 1.35:
        place(fr, LABEL_P, W / 2, 1165, pop(t, 1.35))
        val = int(round(4892 * (1 - (1 - k) ** 3)))
        place(fr, big_text(f'{val:,}円', 190), W / 2, 1370, pop(t, 1.45, .3))
    if t > 2.3:
        place(fr, STAMP, 880, 1150, pop(t, 2.3, .3) * 0.85)
    return fr.convert('RGB')

def end_frame(t):
    fr = END_BG.copy().convert('RGBA')
    place(fr, END_T1, W / 2, 430, pop(t, 0.0))
    place(fr, END_T2, W / 2, 600, pop(t, 0.15))
    bob = 8 * np.sin(t * 5)
    place(fr, END_PILL, W / 2, 815 + bob, pop(t, 0.45))
    place(fr, END_FACE, W / 2, 1120, pop(t, 0.7))
    pulse = 1 + 0.035 * np.sin(max(0, t - 1.2) * 7)
    place(fr, END_FOLLOW, W / 2, 1440, pop(t, 1.0) * (pulse if t > 1.35 else 1))
    place(fr, END_NAME, W / 2, 1545, pop(t, 1.2))
    return fr.convert('RGB')

# ---- 素材 ----
cover = load('cover_fixed.png').resize((W, H), Image.LANCZOS)
shelf = fit_with_blur_bg(load(U + 'e1e6d950-image.jpg'))
close_src = load(U + '49e01062-image.jpg')
close = fit_with_blur_bg(close_src)
sold = fit_with_blur_bg(load('sold_blur.jpg'))
calc = fit_with_blur_bg(load(U + '991801a5-image.jpg'))
end = endcard()
_bg = close_src.resize((W, W)).resize((W, H)).filter(ImageFilter.GaussianBlur(30))
END_BG = Image.blend(_bg, Image.new('RGB', (W, H), (15, 35, 110)), 0.6)
_r = ray_bg(c_top=(40, 90, 200), c_bot=(10, 30, 110), center=(W / 2, 620))
END_BG = Image.blend(END_BG, _r, 0.35)
END_T1 = pill('あなたの地元の', 60, (255, 255, 255), NAVY, pad=(50, 16))
END_T2 = big_text('ご当地キティは？', 116)
END_PILL = pill('コメントで教えてね', 62, (255, 255, 255), NAVY, icon=True)
_f = close_src.crop((520, 280, 1220, 980)).resize((380, 380), Image.LANCZOS)
_m = Image.new('L', (380, 380), 0); ImageDraw.Draw(_m).ellipse((0, 0, 379, 379), fill=255)
END_FACE = Image.new('RGBA', (420, 420), (0, 0, 0, 0)); _d = ImageDraw.Draw(END_FACE)
_d.ellipse((0, 0, 419, 419), fill=(255, 255, 255)); END_FACE.paste(_f, (20, 20), _m)
END_FOLLOW = pill('フォローして次の仕入れも見てね', 50, RED, (255, 255, 255), pad=(56, 26))
_nf = ImageFont.truetype(MARU, 48)
END_NAME = Image.new('RGBA', (600, 90), (0, 0, 0, 0))
ImageDraw.Draw(END_NAME).text((300, 45), '◆ ジャンク姉さん ◆', font=_nf, fill=(255, 255, 255), anchor='mm', stroke_width=5, stroke_fill=NAVY)

# 写真の上での注目点（画面座標）: ズームの中心
def to_screen(src_size, pt):
    sw, sh = src_size
    s = min(W / sw, H / sh)
    return ((W - sw * s) / 2 + pt[0] * s, (H - sh * s) / 2 + pt[1] * s)

shelf_c = to_screen((1122, 1459), (660, 560))     # カゴの中のキティ
tag_c = to_screen((1449, 1449), (520, 1150))      # 値札
kitty_c = to_screen((1449, 1449), (900, 720))     # キティの服
gtag_c = to_screen((1449, 1449), (380, 960))      # GOTOCHI KITTY のタグ
sold_c = to_screen((1074, 1523), (540, 700))
calc_c = to_screen((1092, 1498), (546, 1300))     # 利益の行

T_Y = 1180  # テロップの縦位置（画面の真ん中より少し下。Instagramの文字やボタンに隠れない）

# (開始秒, 終了秒, 画像, ズーム開始, ズーム終了, 中心開始, 中心終了, テロップ)
segs = [
    (0.0, 1.0, cover, 1.00, 1.04, (W/2, H/2), (W/2, H/2), None),
    (1.0, 4.0, shelf, 1.00, 1.45, (W/2, H/2), shelf_c,
        bubble(['オフハウスの', 'ぬいぐるみのカゴで', 'わたし、うもれてたの'], 66), 1300),
    (4.0, 6.5, close, 1.6, 2.3, tag_c, tag_c,
        bubble(['お値段', '330円（税込）'], 70, accent=1), 1380),
    (6.5, 8.5, close, 1.05, 1.25, (W/2, H/2), kitty_c,
        bubble(['実はわたし', '函館の「イカ踊り」', 'ご当地キティなの'], 66, accent=1), 1380),
    (8.5, 10.5, close, 1.25, 1.35, kitty_c, kitty_c,
        bubble(['しかも', 'タグ付きの新品'], 70, accent=1), 1380),
    (10.5, 12.7, close, 1.35, 1.7, kitty_c, gtag_c,
        bubble(['キティはもともと大人気', 'しかもわたしは地域限定で', '今はもう売っていないの'], 56, accent=2), 1380),
    (12.7, 15.0, shelf, 1.25, 1.1, shelf_c, (W/2, H/2),
        bubble(['ご当地キーホルダーは', '安く置かれていることが多いけど', 'コレクターさんが探しているの'], 48, accent=2), 1300),
    (15.0, 17.5, sold, 1.0, 1.12, (W/2, H/2), sold_c,
        bubble(['5,980円で', 'お嫁に行きました'], 70, accent=0), 1360),
    (17.5, 18.7, calc, 1.0, 1.1, (W/2, H/2), calc_c,
        bubble(['利益計算アプリで', '計算してみると…'], 60), 1380),
    (18.7, 22.2, 'PROFIT'),
    (22.2, 26.0, 'END'),
]
TOTAL = 26.0
XF = 0.18  # 切り替えのクロスフェード秒

def ease(t):
    return 0.5 - 0.5 * np.cos(np.pi * min(max(t, 0), 1))

def render_seg(seg, t):
    if seg[2] == 'PROFIT': return np.array(profit_frame(t - seg[0]))
    if seg[2] == 'END': return np.array(end_frame(t - seg[0]))
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
