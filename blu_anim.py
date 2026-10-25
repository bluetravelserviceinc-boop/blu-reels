#!/usr/bin/env python3
"""Blu 2.0: modern hard-shell suitcase mascot, animated with Pillow + numpy.

Palette comes from the Blue Travel site: navy #002143, blue #2C80BF, gold #F2B544.
usage:
  blu_anim.py --audio voice.wav --out frames_dir [--fps 30]     # frames synced to audio
  blu_anim.py --still out.png                                    # one still frame
"""
import argparse, math, os, wave, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

CW, CH = 460, 560
SS = 2
W, H = CW * SS, CH * SS
PIVOT = (230 * SS, 508 * SS)

NAVY = (0, 33, 67)
DEEP = (0, 23, 47)
BLUE = (44, 128, 191)
BLUE_L = (96, 174, 230)
BLUE_D = (28, 92, 150)
GOLD = (242, 181, 68)
GOLD_L = (250, 208, 112)
GOLD_D = (214, 150, 38)


def S(v):
    return int(round(v * SS))


def grad(size, c1, c2, angle=90.0):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle)
    proj = (xx - w / 2) * math.cos(a) + (yy - h / 2) * math.sin(a)
    span = abs(w * math.cos(a)) + abs(h * math.sin(a))
    t = np.clip(proj / span + 0.5, 0, 1)[..., None]
    c1 = np.array(c1, np.float32); c2 = np.array(c2, np.float32)
    arr = (c1 * (1 - t) + c2 * t).astype(np.uint8)
    alpha = np.full((h, w, 1), 255, np.uint8)
    return Image.fromarray(np.concatenate([arr, alpha], axis=2), "RGBA")


def rrect_mask(box, r, size=(W, H)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([S(box[0]), S(box[1]), S(box[2]), S(box[3])], radius=S(r), fill=255)
    return m


def paste_grad(img, box, r, c1, c2, angle):
    mask = rrect_mask(box, r)
    img.paste(grad((W, H), c1, c2, angle), (0, 0), mask)
    return mask


def soft_layer(draw_fn, blur):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    return layer.filter(ImageFilter.GaussianBlur(S(blur)))


def clip_to(layer, mask):
    a = ImageChops.multiply(layer.split()[3], mask)
    layer.putalpha(a)
    return layer


def star(d, cx, cy, r, fill):
    k = 0.26
    pts = [(cx, cy - r), (cx + r * k, cy - r * k), (cx + r, cy), (cx + r * k, cy + r * k),
           (cx, cy + r), (cx - r * k, cy + r * k), (cx - r, cy), (cx - r * k, cy - r * k)]
    d.polygon([(S(x), S(y)) for x, y in pts], fill=fill)


# ---------------------------------------------------------------- static base
def build_base():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # telescopic handle (behind body)
    for x in (150, 296):
        d.rounded_rectangle([S(x), S(92), S(x + 14), S(150)], radius=S(5), fill=(11, 53, 96, 255))
        d.rounded_rectangle([S(x + 2), S(92), S(x + 6), S(150)], radius=S(2), fill=(60, 120, 180, 255))
    paste_grad(img, (132, 66, 328, 96), 15, (28, 80, 130), (6, 38, 76), 90)
    d.rounded_rectangle([S(146), S(70), S(314), S(76)], radius=S(3), fill=(120, 175, 225, 120))

    # body
    body = (80, 128, 380, 502)
    bmask = paste_grad(img, body, 66, BLUE_L, BLUE_D, 62)

    # inner edge shading for volume
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle([S(80), S(128), S(380), S(502)], radius=S(66), outline=(0, 33, 67, 150), width=S(14))
    edge = clip_to(edge.filter(ImageFilter.GaussianBlur(S(9))), bmask)
    img.alpha_composite(edge)

    # ribs on the lower shell
    for i, x in enumerate((122, 170, 218, 266, 314)):
        d.rounded_rectangle([S(x), S(352), S(x + 9), S(478)], radius=S(4), fill=(0, 33, 67, 105))
        d.rounded_rectangle([S(x + 9), S(354), S(x + 12), S(476)], radius=S(2), fill=(120, 190, 240, 70))

    # gold travel badge with plane
    badge = (178, 392, 282, 452)
    paste_grad(img, badge, 18, GOLD_L, GOLD_D, 80)
    d.rounded_rectangle([S(178), S(392), S(282), S(452)], radius=S(18), outline=(255, 235, 180, 160), width=S(2))
    plane = [(214, 436), (222, 424), (206, 414), (212, 410), (236, 418), (250, 410), (254, 414), (242, 424),
             (250, 438), (244, 440), (234, 430), (222, 436)]
    d.polygon([(S(x + 10), S(y - 2)) for x, y in plane], fill=NAVY)

    # bottom bumper
    paste_grad(img, (116, 484, 344, 510), 12, (14, 62, 108), (0, 33, 67), 90)

    # glossy highlight (soft, clipped to shell)
    hl = soft_layer(lambda g: g.ellipse([S(96), S(150), S(176), S(360)], fill=(255, 255, 255, 84)), 16)
    img.alpha_composite(clip_to(hl, bmask))
    hl2 = soft_layer(lambda g: g.ellipse([S(330), S(160), S(366), S(330)], fill=(255, 255, 255, 46)), 8)
    img.alpha_composite(clip_to(hl2, bmask))

    # face panel
    panel = (110, 172, 350, 336)
    pmask = paste_grad(img, panel, 52, (10, 52, 96), DEEP, 90)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([S(110), S(172), S(350), S(336)], radius=S(52), outline=(88, 160, 215, 200), width=S(3))
    sheen = soft_layer(lambda g: g.polygon([(S(118), S(178)), (S(236), S(178)), (S(150), S(330)), (S(112), S(330))],
                                           fill=(255, 255, 255, 38)), 4)
    img.alpha_composite(clip_to(sheen, pmask))
    return img


# ------------------------------------------------------------- per-frame bits
def eyes_and_mouth(img, mouth, blink, look, shape=0.5):
    d = ImageDraw.Draw(img)
    ex = look * 6
    ey = 246 - 1.5 * mouth
    open_h = max(0.12, 1 - 0.9 * blink)
    for cx in (186, 274):
        cx += ex
        hh = 27 * open_h
        glow = soft_layer(lambda g: g.ellipse([S(cx - 26), S(ey - hh - 8), S(cx + 26), S(ey + hh + 8)],
                                              fill=(120, 225, 255, 150)), 9)
        img.alpha_composite(glow)
        eye = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).ellipse([S(cx - 20), S(ey - hh), S(cx + 20), S(ey + hh)], fill=255)
        eye.paste(grad((W, H), (255, 255, 255), (130, 226, 255), 90), (0, 0), m)
        img.alpha_composite(eye)
        d = ImageDraw.Draw(img)
        if open_h > 0.5:
            d.ellipse([S(cx - 9 + look * 2), S(ey - hh + 6), S(cx + 1 + look * 2), S(ey - hh + 18)], fill=(255, 255, 255, 255))

    # cheeks
    ch = soft_layer(lambda g: (g.ellipse([S(138), S(284), S(176), S(308)], fill=(255, 128, 150, 120)),
                               g.ellipse([S(284), S(284), S(322), S(308)], fill=(255, 128, 150, 120))), 5)
    img.alpha_composite(ch)

    d = ImageDraw.Draw(img)
    cx, cy = 230 + look * 3, 292
    if mouth < 0.12:
        d.arc([S(cx - 24), S(cy - 16), S(cx + 24), S(cy + 12)], 22, 158, fill=(232, 251, 255, 255), width=S(5))
    else:
        w = (12 + 18 * shape) + 6 * mouth
        h = 5 + (22 + 14 * (1 - shape)) * mouth
        d.ellipse([S(cx - w), S(cy - h * 0.45), S(cx + w), S(cy + h * 0.75)], fill=(255, 122, 147, 255))
        d.ellipse([S(cx - w * 0.62), S(cy + h * 0.12), S(cx + w * 0.62), S(cy + h * 0.75)], fill=(201, 58, 94, 255))
        d.arc([S(cx - w), S(cy - h * 0.45), S(cx + w), S(cy + h * 0.75)], 200, 340, fill=(232, 251, 255, 255), width=S(3))


def wheels(img, t):
    d = ImageDraw.Draw(img)
    for cx in (136, 324):
        cy = 520
        d.ellipse([S(cx - 21), S(cy - 21), S(cx + 21), S(cy + 21)], fill=(0, 23, 47, 255))
        d.ellipse([S(cx - 15), S(cy - 15), S(cx + 15), S(cy + 15)], fill=(24, 84, 140, 255))
        a = t * 9.0
        d.ellipse([S(cx - 15), S(cy - 15), S(cx + 15), S(cy + 15)], outline=(120, 185, 235, 255), width=S(2))
        d.ellipse([S(cx + 9 * math.cos(a) - 2.5), S(cy + 9 * math.sin(a) - 2.5),
                   S(cx + 9 * math.cos(a) + 2.5), S(cy + 9 * math.sin(a) + 2.5)], fill=(235, 246, 255, 255))
        d.ellipse([S(cx - 5), S(cy - 5), S(cx + 5), S(cy + 5)], fill=(14, 62, 108, 255))


def transform(img, sx, sy, ang, dy):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    # forward: out = R * S * (in - p) + p + d ; PIL needs the inverse (out -> in)
    m = np.array([[ca * sx, -sa * sy], [sa * sx, ca * sy]])
    inv = np.linalg.inv(m)
    p = np.array(PIVOT, float)
    off = p - inv @ (p + np.array([0, S(dy)]))
    return img.transform((W, H), Image.AFFINE,
                         (inv[0, 0], inv[0, 1], off[0], inv[1, 0], inv[1, 1], off[1]), resample=Image.BICUBIC)


def render_frame(base, t, mouth=0.0, blink=0.0, look=0.0, shape=0.5):
    cyc = 2 * math.pi * t / 1.7
    lift = 0.5 + 0.5 * math.sin(cyc)               # 0 ground .. 1 top
    dy = -14 * lift - 8 * mouth
    sy = 1.0 + 0.030 * (1 - lift) - 0.012 * lift
    sx = 1.0 / sy
    ang = 2.2 * math.sin(2 * math.pi * t / 2.6) + 1.5 * (mouth - 0.3) * math.sin(t * 9)

    body = base.copy()
    eyes_and_mouth(body, mouth, blink, look, shape)
    wheels(body, t)
    body = transform(body, sx, sy, ang, dy)

    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    k = 1 - 0.18 * lift
    sh = soft_layer(lambda g: g.ellipse([S(230 - 128 * k), S(520), S(230 + 128 * k), S(548)], fill=(0, 19, 39, 120)), 8)
    out.alpha_composite(sh)
    out.alpha_composite(body)

    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sp)
    for (x, y, r, ph) in ((398, 132, 17, 0.0), (426, 214, 10, 1.7), (52, 176, 12, 3.1), (70, 112, 8, 4.4)):
        v = max(0.0, math.sin(t * 3.4 + ph))
        if v > 0.02:
            star(sd, x, y - 6 * v, r * v, (GOLD[0], GOLD[1], GOLD[2], int(255 * min(1, v * 1.6))))
    out.alpha_composite(sp)
    return out.resize((CW, CH), Image.LANCZOS)


# ------------------------------------------------------------ audio -> mouth
def mouth_track(path, fps):
    with wave.open(path, "rb") as w:
        n, sr, ch = w.getnframes(), w.getframerate(), w.getnchannels()
        raw = w.readframes(n)
    vals = np.array(struct.unpack("<" + "h" * (len(raw) // 2), raw), np.float32)
    if ch > 1:
        vals = vals[::ch]
    dur = len(vals) / sr
    nf = int(math.ceil(dur * fps))
    hop = sr / fps
    rms = np.array([np.sqrt(np.mean(vals[int(i * hop):int((i + 1) * hop + hop * 0.5)] ** 2) + 1e-6) for i in range(nf)])
    ref = np.percentile(rms, 95) or 1.0
    # syllable-level envelope: 10 ms hop, contrast against the local 250 ms min/max
    h100 = sr / 100.0
    n100 = int(len(vals) / h100)
    r100 = np.array([np.sqrt(np.mean(vals[int(i * h100):int((i + 2) * h100)] ** 2) + 1e-6) for i in range(n100)])
    r100 = np.convolve(r100, np.ones(3) / 3, "same")
    win = np.lib.stride_tricks.sliding_window_view(np.pad(r100, (12, 12), mode="edge"), 25)
    loc = (r100 - win.min(axis=1)) / (win.max(axis=1) - win.min(axis=1) + 1e-6)
    level = np.clip((r100 / (np.percentile(r100, 95) or 1.0) - 0.12) / 0.88, 0, 1) ** 0.7
    m100 = level * (0.12 + 0.88 * loc)
    env = np.zeros(nf)
    for i in range(nf):
        a0 = int(i * 100 / fps)
        a1 = max(a0 + 1, int((i + 1) * 100 / fps))
        if a0 < n100:
            env[i] = m100[a0:a1].mean()
    env = np.clip(env * 1.3, 0, 1)
    out, cur = [], 0.0
    for e in env:                       # fast attack, quick release = lips close between syllables
        cur = cur + (e - cur) * (0.9 if e > cur else 0.65)
        out.append(min(1.0, cur))

    # vowel shape from spectral centroid: low = round (o/u), high = wide (a/e/i)
    shape, cs = [], 0.5
    for i in range(nf):
        seg = vals[int(i * hop):int((i + 1) * hop + hop * 0.5)]
        if len(seg) < 64 or out[i] < 0.12:
            target = cs
        else:
            mag = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            fr = np.fft.rfftfreq(len(seg), 1.0 / sr)
            band = (fr > 150) & (fr < 4000)
            cen = float((fr[band] * mag[band]).sum() / (mag[band].sum() + 1e-6))
            target = float(np.clip((cen - 450) / 1500, 0, 1))
        cs = cs + (target - cs) * 0.5
        shape.append(cs)
    lead = 1                            # lips open ~1 frame before the sound
    mouth_arr = np.array(out[lead:] + [0.0] * lead)
    shape_arr = np.array(shape[lead:] + [shape[-1]] * lead)
    return mouth_arr, shape_arr, dur


def blink_at(t):
    for bt in (1.1, 3.4, 5.2, 7.9, 10.3, 12.6, 15.0, 17.7, 20.2, 22.9, 25.4, 28.0):
        u = (t - bt) / 0.18
        if 0 <= u <= 1:
            return math.sin(math.pi * u)
    return 0.0


def frame_params(i, fps, mouth, shape):
    t = i / fps
    m = float(mouth[i]) if mouth is not None and i < len(mouth) else 0.0
    s = float(shape[i]) if shape is not None and i < len(shape) else 0.5
    return t, m, blink_at(t), 0.8 * math.sin(2 * math.pi * t / 3.3), s


_BASE = None


def _work(args):
    i, fps, mouth, shape, outdir = args
    t, m, b, lk, s = frame_params(i, fps, mouth, shape)
    render_frame(_BASE, t, m, b, lk, s).save(os.path.join(outdir, f"{i:04d}.png"))
    return i


def main():
    global _BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio"); ap.add_argument("--out"); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--still"); ap.add_argument("--mouth", type=float, default=0.0)
    ap.add_argument("--t", type=float, default=0.4)
    a = ap.parse_args()
    _BASE = build_base()
    if a.still:
        render_frame(_BASE, a.t, a.mouth, 0.0, 0.0).save(a.still)
        print("still", a.still); return
    mouth, shape, dur = mouth_track(a.audio, a.fps)
    os.makedirs(a.out, exist_ok=True)
    np.save(os.path.join(a.out, "mouth.npy"), np.stack([mouth, shape]))
    from multiprocessing import Pool
    jobs = [(i, a.fps, mouth, shape, a.out) for i in range(len(mouth))]
    with Pool(2) as p:
        for _ in p.imap_unordered(_work, jobs, chunksize=6):
            pass
    print(f"frames: {len(mouth)} ({dur:.1f}s) -> {a.out}")


if __name__ == "__main__":
    main()
