"""Parts shared by the wide drawings, in box units: x 0..18 right, y 0..18 down (see train/wide.py).

Families made here by rule: faces (term-rest's one-colour face parts, put
in the box and extended), clock faces, moon phases, people as pictograms
from the angles of their limbs, busts, hands, framed text, arrows.
"""
import math

import term_rest
from wide import L, A, C, D, S, F, R, RR, B, RB, K, P, star, heart, drop, move, text, from_cell  # noqa: F401

LO, HI = 1.5, 16.5                 # ink stays inside x and y 1.5..16.5


def bounds(shapes):
    xs, ys = [], []
    for sh in shapes:
        if sh[0] == "cut":
            continue
        if sh[0] == "seg":
            r = sh[5]
            xs += [sh[1] - r, sh[1] + r, sh[3] - r, sh[3] + r]
            ys += [sh[2] - r, sh[2] + r, sh[4] - r, sh[4] + r]
        else:
            xs += [p[0] for p in sh[1]]
            ys += [p[1] for p in sh[1]]
    return min(xs), min(ys), max(xs), max(ys)


def fit(shapes, lo=LO, hi=HI, centre=True):
    """Scale the shapes down about their middle until they fit lo..hi both ways, and centre them."""
    x0, y0, x1, y1 = bounds(shapes)
    s = min(1.0, (hi - lo) / max(x1 - x0, 1e-9), (hi - lo) / max(y1 - y0, 1e-9))
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    tx, ty = ((lo + hi) / 2, (lo + hi) / 2) if centre else (min(max(mx, lo + (x1 - x0) * s / 2), hi - (x1 - x0) * s / 2),
                                                            min(max(my, lo + (y1 - y0) * s / 2), hi - (y1 - y0) * s / 2))
    return move(shapes, dx=tx - mx, dy=ty - my, s=s, cx=mx, cy=my)


# ---------------------------------------------------------------- faces

FACE_K = 15.8                      # box units for one cell unit of term_rest's faces: a head 7.6 units in radius
FC = (9.0, 9.0)                    # the middle of a face in the box


def _from_rest(shapes, cx=FC[0], cy=FC[1], k=FACE_K):
    """term_rest shapes (cell units, a head at (0.5, 0.975)) in the box, the head at (cx, cy)."""
    return from_cell(shapes, k, cx - 0.5 * k, cy - 0.975 * k)


def rest_face(spec):
    """One of term_rest's faces: (eyes, mouth, brows, extras) in its own vocabulary, fitted to the box."""
    return fit(_from_rest(term_rest.face(spec)))


def head(r=7.4, cx=9.0, cy=9.0):
    return C(cx, cy, r - 0.95, 1.9)


def features(spec, cx=9.0, cy=9.0, s=1.0):
    """Eyes, brows, mouth and the inside extras of term_rest, about a head at (cx, cy) of the box, scaled by s."""
    return _from_rest(term_rest._features(spec, 5.0, 9.75, 1.0), cx, cy, FACE_K * s)


def face(eyes="dot", mouth="smile", brows=None, extras=(), add=(), r=7.4):
    """A round face: the ring, term_rest's features, then any shapes of add (box units)."""
    return head(r) + features((eyes, mouth, brows, tuple(extras))) + list(add)


def fitted(shapes):
    return fit(shapes)


# Parts of faces that term_rest has not, about a head at (9, 9) radius 7.4.

def eye_dot(x, y=7.2, r=1.0):
    return D(x, y, r)


def mouth_line(y=12.2, w=1.4, x0=6.2, x1=11.8):
    return L((x0, y), (x1, y), w=w)


def mouth_arc(up=True, y=11.0, rx=3.2, ry=2.2, w=1.4):
    return A(9, y, rx, ry, 20, 160, w) if up else A(9, y + 3, rx, ry, 200, 340, w)


def hand_by_face(x=12.8, y=13.6, s=1.0):
    """A small raised hand, a mitten with a thumb, beside the mouth."""
    return move(RR(-1.8, -1.6, 1.8, 2.4, 1.2) + L((-1.8, 0.4), (-3.0, -1.0), w=1.4), dx=x, dy=y, s=s, cx=0, cy=0)


# ---------------------------------------------------------------- clocks and moons

def clock(hour, minute, r=7.2):
    """A clock face: a ring, a dot in the middle, the hour hand and the minute hand."""
    cx = cy = 9.0
    ah = math.radians(30 * (hour % 12) + minute / 2 - 90)
    am = math.radians(6 * minute - 90)
    out = C(cx, cy, r - 1.0, 2.0) + D(cx, cy, 1.1)
    out += L((cx, cy), (cx + 3.3 * math.cos(ah), cy + 3.3 * math.sin(ah)), w=2.0)
    out += L((cx, cy), (cx + 4.9 * math.cos(am), cy + 4.9 * math.sin(am)), w=1.4)
    return out


def moon(dark, bulge):
    """term_rest's moon phase, in the box."""
    return fit(_from_rest(term_rest.moon(dark, bulge)))


# ---------------------------------------------------------------- people

LIMB = 2.2                         # arms and legs
TORSO = 3.2


def _at(p, ang, length):
    a = math.radians(ang)
    return (p[0] + length * math.sin(a), p[1] - length * math.cos(a))


def figure(neck=(9, 6.2), lean=0.0, hip_len=5.0, arms=((200, 160), (160, 200)), legs=((180, 180), (180, 180)),
           head_r=1.9, upper=2.9, lower=2.9, thigh=3.0, shin=3.0, w=LIMB, tw=TORSO):
    """A pictogram person. Angles in degrees from straight up, clockwise (90 points right, 180 down).

    lean turns the trunk; arms and legs are (upper, lower) angles for the left then the right limb as seen."""
    hip = _at(neck, 180 + lean, hip_len)
    top = _at(neck, lean, 0.6)
    hd = _at(neck, lean, 1.0 + head_r + 0.6)
    out = D(hd[0], hd[1], head_r) + L(top, hip, w=tw)
    sh = _at(neck, 180 + lean, 0.5)
    for a_up, a_lo in arms:
        e = _at(sh, a_up, upper)
        out += L(sh, e, _at(e, a_lo, lower), w=w)
    for a_up, a_lo in legs:
        k = _at(hip, a_up, thigh)
        out += L(hip, k, _at(k, a_lo, shin), w=w)
    return out


def person(**kw):
    """A pictogram person fitted to the box."""
    return fit(figure(**kw))


def bust(cx=9.0, hair=None, r=3.4, shoulders=6.6, top=2.4, extra=()):
    """Head and shoulders: a head disc and a rounded body, with a cut between them; hair is a style name."""
    hy = top + r
    out = []
    body = RR(cx - shoulders, hy + r + 1.2, cx + shoulders, 18.6, 3.2)
    out += body
    out += K(D(cx, hy, r + 1.0))
    out += D(cx, hy, r)
    if hair == "long":        # hair down to the shoulders: a cap and two locks
        out += K(R(cx - r - 1.0, hy - 0.2, cx + r + 1.0, hy + r + 2.0)) + D(cx, hy, r)
        out += S(cx, hy, r + 0.9, r + 0.9, 180, 360) + R(cx - r - 0.9, hy - 0.2, cx - r + 0.6, hy + r + 1.4) + \
            R(cx + r - 0.6, hy - 0.2, cx + r + 0.9, hy + r + 1.4)
    elif hair == "short":
        out += S(cx, hy - 0.3, r + 0.5, r + 0.5, 190, 350)
    elif hair == "bun":
        out += D(cx, hy - r - 0.6, 1.4)
    out += list(extra)
    return out


# ---------------------------------------------------------------- hands

def hand(fingers=(1, 1, 1, 1), thumb=1, lengths=(4.6, 5.4, 5.0, 4.0), fw=2.0, gap=0.8, palm=(5.2, 8.0, 13.4, 15.6)):
    """An open hand as seen palm on, fingers up: a palm, four fingers (1 up, 0 folded) and a thumb at the left.

    Fingers are strokes fw wide with gaps between them."""
    x0, y0, x1, y1 = palm
    out = RR(x0, y0, x1, y1, 1.6)
    step = fw + gap
    start = x1 - fw / 2 - 3 * step
    for i, up in enumerate(fingers):
        x = start + i * step
        if up:
            out += L((x, y0 + 1.0), (x, y0 - lengths[i] + fw / 2), w=fw)
        else:
            out += L((x, y0 + 1.0), (x, y0 - 0.2), w=fw)
    if thumb == 1:
        out += L((x0 + 0.6, y1 - 3.2), (x0 - 2.0, y0 + 0.6), w=fw + 0.2)
    elif thumb == 2:              # thumb up beside the fingers
        out += L((x0 + 0.6, y0 + 2.0), (x0 - 0.4, y0 - 3.4), w=fw + 0.2)
    return out


def fist():
    """A fist seen from the front: a block of four folded fingers and a thumb across."""
    out = RR(4.2, 4.6, 13.8, 14.6, 2.4)
    for x in (6.6, 9.0, 11.4):
        out += K(L((x, 4.0), (x, 8.4), w=0.7))
    out += K(L((4.0, 10.0), (11.0, 10.0), w=0.8))
    return out


def pointing(direction=0):
    """A hand pointing up (0), right (90), down (180) or left (270): the index finger out, the rest folded."""
    out = RR(5.4, 9.0, 13.2, 16.2, 2.0) + L((7.0, 9.6), (7.0, 2.6), w=2.2)
    out += K(L((9.6, 8.6), (9.6, 12.0), w=0.7)) + K(L((11.6, 8.6), (11.6, 12.0), w=0.7))
    out += L((5.6, 13.0), (4.0, 10.8), w=2.0)
    return fit(move(out, rot=direction))


def thumb(up=True):
    out = RR(6.0, 8.0, 14.6, 16.2, 2.0) + L((8.2, 8.6), (8.2, 2.6), w=2.6)
    for y in (10.6, 13.0):
        out += K(L((10.0, y), (15.0, y), w=0.7))
    out = fit(out)
    return out if up else move(out, my=True)


# ---------------------------------------------------------------- framed things

def squared(s, inverse=False, h=None, frame_r=2.6):
    """Letters in a rounded square: drawn in a square outline, or cut out of a solid square."""
    n = len(s)
    hh = h or (7.0 if n <= 2 else 5.6 if n == 3 else 4.6)
    t = text(s, 9, 9.3, hh, w=12.4, pen=1.5)
    if inverse:
        return RR(1.5, 1.5, 16.5, 16.5, frame_r) + K(t)
    return RB(1.5, 1.5, 16.5, 16.5, frame_r, 1.6) + t


def circled(shapes, r=7.4, w=1.6):
    return C(9, 9, r - w / 2, w) + list(shapes)


def arrow(x0, y0, x1, y1, w=2.0, head_len=3.4, head_w=3.6):
    """A stroke with a filled head at (x1, y1)."""
    a = math.atan2(y1 - y0, x1 - x0)
    c, s = math.cos(a), math.sin(a)
    bx, by = x1 - head_len * c, y1 - head_len * s
    return L((x0, y0), (bx + 0.3 * c, by + 0.3 * s), w=w) + F((x1, y1), (bx - head_w * s, by + head_w * c), (bx + head_w * s, by - head_w * c))


def no_sign(inner, w=2.0):
    """A thing under a prohibition sign: the ring and the bar, with clear space around them."""
    ring = C(9, 9, 7.3 - w / 2, w)
    bar = L((4.0, 4.0), (14.0, 14.0), w=w)
    return list(inner) + K(C(9, 9, 7.3 - w / 2, w + 1.6)) + K(L((4.0, 4.0), (14.0, 14.0), w=w + 1.6)) + ring + bar


def ring_poly(cx, cy, r_out, r_in):
    return D(cx, cy, r_out) + K(D(cx, cy, r_in))
