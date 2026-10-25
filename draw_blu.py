from PIL import Image, ImageDraw
import os

OUT = os.path.dirname(os.path.abspath(__file__))
S = 4  # supersampling
W, H = 520, 620

BLUE = (55, 138, 221)
DARK = (24, 95, 165)
NAVY = (12, 45, 79)
DEEP = (12, 68, 124)
GOLD = (250, 199, 117)
GOLD_D = (186, 117, 23)
WHITE = (255, 255, 255)
CHEEK = (244, 192, 209)
TONGUE = (226, 100, 120)


def s(v):
    return int(v * S)


def rr(d, box, r, **kw):
    d.rounded_rectangle([s(box[0]), s(box[1]), s(box[2]), s(box[3])], radius=s(r), **kw)


def ell(d, box, **kw):
    d.ellipse([s(box[0]), s(box[1]), s(box[2]), s(box[3])], **kw)


def draw(open_mouth, name):
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # handle
    rr(d, (190, 40, 330, 110), 30, outline=DARK, width=s(16))
    # arms
    d.arc([s(40), s(250), s(140), s(350)], 180, 270, fill=DARK, width=s(16))
    d.arc([s(380), s(250), s(480), s(350)], 270, 360, fill=DARK, width=s(16))
    # body
    rr(d, (90, 100, 430, 520), 50, fill=BLUE)
    # band
    d.rectangle([s(90), s(330), s(430), s(352)], fill=DARK)
    # wheels
    ell(d, (130, 520, 180, 570), fill=DEEP)
    ell(d, (340, 520, 390, 570), fill=DEEP)
    ell(d, (146, 536, 164, 554), fill=BLUE)
    ell(d, (356, 536, 374, 554), fill=BLUE)
    # eyes
    ell(d, (150, 190, 238, 278), fill=WHITE)
    ell(d, (282, 190, 370, 278), fill=WHITE)
    ell(d, (176, 214, 222, 260), fill=NAVY)
    ell(d, (298, 214, 344, 260), fill=NAVY)
    ell(d, (192, 220, 206, 234), fill=WHITE)
    ell(d, (314, 220, 328, 234), fill=WHITE)
    # cheeks
    ell(d, (118, 288, 160, 312), fill=CHEEK)
    ell(d, (360, 288, 402, 312), fill=CHEEK)
    # mouth
    if open_mouth:
        ell(d, (216, 290, 304, 354), fill=NAVY)
        ell(d, (232, 322, 288, 352), fill=TONGUE)
    else:
        d.arc([s(214), s(268), s(306), s(340)], 20, 160, fill=NAVY, width=s(10))
    # luggage tag
    rr(d, (205, 400, 315, 470), 12, fill=GOLD)
    d.polygon([(s(260), s(414)), (s(284), s(435)), (s(260), s(456)), (s(236), s(435))], fill=GOLD_D)

    img = img.resize((W, H), Image.LANCZOS)
    img.save(os.path.join(OUT, name))
    print("saved", name, img.size)


draw(False, "blu_closed.png")
draw(True, "blu_open.png")
