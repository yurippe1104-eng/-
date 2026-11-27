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


# ---- 素材 ----
cover = load(U + '786cfc3b-image.png').resize((W, H), Image.LANCZOS)
shelf = fit_with_blur_bg(load(U + 'e1e6d950-image.jpg'))
close_src = load(U + '49e01062-image.jpg')
close = fit_with_blur_bg(close_src)
sold = fit_with_blur_bg(load('sold_blur.jpg'))
calc = fit_with_blur_bg(load(U + '991801a5-image.jpg'))
end = endcard()

# 写真の上での注目点（画面座標）: ズームの中心
def to_screen(src_size, pt):
    sw, sh = src_size
    s = min(W / sw, H / sh)
    return ((W - sw * s) / 2 + pt[0] * s, (H - sh * s) / 2 + pt[1] * s)

shelf_c = to_screen((1122, 1459), (660, 560))     # カゴの中のキティ
tag_c = to_screen((1449, 1449), (520, 1150))      # 値札
kitty_c = to_screen((1449, 1449), (900, 720))     # キティの服
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
    (10.5, 13.0, sold, 1.0, 1.12, (W/2, H/2), sold_c,
        bubble(['5,980円で', 'お嫁に行きました'], 70, accent=0), 1360),
    (13.0, 15.5, calc, 1.0, 1.15, (W/2, H/2), calc_c,
        bubble(['手数料・送料を引いても', '利益 4,892円'], 64, accent=1)),
    (15.5, 18.0, end, 1.0, 1.0, (W/2, H/2), (W/2, H/2),
        bubble(['売れるキティの見つけ方', 'これからも発信します', 'フォローして', '次の仕入れも見てね'], 62, accent=2)),
]
TOTAL = 18.0
XF = 0.18  # 切り替えのクロスフェード秒

def ease(t):
    return 0.5 - 0.5 * np.cos(np.pi * min(max(t, 0), 1))

def render_seg(seg, t):
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
