"""A face cut into nets: a drawing file of one bundle and an advance table.

usage: python3 tests/check_face_bundle.py LIB.so

Two copies of one shipped face net, each labelled with half of the face,
make a bundle whose router sends each half to its own copy. Packed with
train/pack.py --drawing-bundle, the file must be what pack.face_bundle()
and pack.py --drawing of the packed bundle and the face make; it must
route each character to the copy that knows it; it must pass
tests/check_reference.py --drawing-bundle, every character exactly the
face's pixels; and every character must draw byte for byte as the face's
own drawing file draws it. The packer must refuse a bundle beside another
net or another bundle, and a bundle member that is cut short.
"""
import ctypes
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
import pack  # noqa: E402

EM = 8
NET = os.path.join(ROOT, "weights", f"neuronte-ui{EM}-v0.json")
FACE = os.path.join(ROOT, "font", f"ui-{EM}.txt")
SHIPPED = os.path.join(ROOT, "weights", f"neuronte-ui{EM}-v0.nrt")
HALVES = ("U+0020..U+004F", "U+0050..U+007E U+2026")
failed = False


def fail(msg):
    global failed
    print("FAIL", msg)
    failed = True


lib_path = os.path.abspath(sys.argv[1])
py = [sys.executable, os.path.join(ROOT, "train", "pack.py")]
with tempfile.TemporaryDirectory() as tmp:
    with open(NET) as fh:
        doc = json.load(fh)
    halves = []
    for i, labelled in enumerate(HALVES):
        doc["training"]["labelled"] = labelled
        path = os.path.join(tmp, f"half{i}.json")
        with open(path, "w") as fh:
            json.dump(doc, fh)
        halves.append(path)
    out = os.path.join(tmp, "face.nrt")
    subprocess.run(py + ["--drawing-bundle", out, FACE] + halves, check=True, stdout=subprocess.DEVNULL)
    with open(out, "rb") as fh:
        data = fh.read()
    made, ranges = pack.face_bundle(FACE, halves)
    if data != made:
        fail("--drawing-bundle is not what pack.face_bundle() makes")
    if ranges != [[0x20, 0x4F, 0], [0x50, 0x7E, 1], [0x2026, 0x2026, 1]]:
        fail(f"ranges {ranges}")
    bundle = os.path.join(tmp, "bundle.nrt")
    subprocess.run(py + ["--bundle", bundle] + halves, check=True, stdout=subprocess.DEVNULL)
    again = os.path.join(tmp, "again.nrt")
    subprocess.run(py + ["--drawing", again, bundle, FACE], check=True, stdout=subprocess.DEVNULL)
    with open(again, "rb") as fh:
        if fh.read() != data:
            fail("--drawing of the packed bundle and the face differs from --drawing-bundle")

    lib = ctypes.CDLL(lib_path)
    P = ctypes.c_void_p
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_nets.argtypes = [P]
    lib.neuronte_advances.argtypes = [P]
    lib.neuronte_route.argtypes = [P, ctypes.c_uint32]
    lib.neuronte_set_binary.argtypes = [P, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = [P, P] + [ctypes.c_int] * 7 + [ctypes.c_char_p, ctypes.c_size_t,
                                                                    ctypes.c_uint32]
    handles = []
    for path in (out, SHIPPED):
        h = P()
        if lib.neuronte_open_file(path.encode(), ctypes.byref(h)) != 0:
            raise SystemExit(f"FAIL {path} does not open")
        handles.append(h)
    face, shipped = handles
    if lib.neuronte_nets(face) != 2 or lib.neuronte_advances(face) != lib.neuronte_advances(shipped):
        fail("the face bundle has the wrong nets or advances")
    chars = [chr(c) for c in range(0x20, 0x7F)] + ["…"]
    for c in chars:
        want = 0 if ord(c) <= 0x4F else 1
        if lib.neuronte_route(face, ord(c)) != want:
            fail(f"U+{ord(c):04X} routed to {lib.neuronte_route(face, ord(c))}, want {want}")
    drawn = 0
    for binary in (1, 0):
        for h in handles:
            lib.neuronte_set_binary(h, binary)
        for bold in (0, 1):
            for c in chars + ["Hello, world…"]:
                t = c.encode()
                W, H = 16 * len(c) + 8, 2 * EM + 4
                bufs, rcs = [], []
                for h in handles:
                    buf = (ctypes.c_uint32 * (W * H))()
                    rcs.append(lib.neuronte_draw_text(h, ctypes.cast(buf, P), W, W, H, 2, 2, EM, bold, t, len(t),
                                                      0xFFFFFFFF))
                    bufs.append(bytes(buf))
                drawn += 1
                if rcs[0] != rcs[1] or bufs[0] != bufs[1]:
                    fail(f"{c!r} binary {binary} bold {bold} is not drawn as the face's own file draws it")
    for h in handles:
        lib.neuronte_close(h)

    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "check_reference.py"), lib_path,
                        "--drawing-bundle", out, FACE] + halves, capture_output=True, text=True)
    if r.returncode != 0 or "192 binary letters" not in r.stdout:
        fail("check_reference --drawing-bundle:\n" + r.stdout + r.stderr)

    cut = os.path.join(tmp, "cut.nrt")
    with open(bundle, "rb") as fh, open(cut, "wb") as gh:
        gh.write(fh.read()[:-1])
    for members, what in (([bundle, halves[0]], "a bundle and a net"),
                          ([halves[0], bundle], "a net and a bundle"),
                          ([bundle, bundle], "two bundles"),
                          ([cut, FACE], "a bundle cut short")):
        refused = os.path.join(tmp, "refused.nrt")
        r = subprocess.run(py + ["--drawing", refused] + members, capture_output=True, text=True)
        if r.returncode == 0 or os.path.exists(refused) or "Traceback" in r.stderr:
            fail(f"the packer did not refuse {what}")

print(f"check_face_bundle: {drawn} texts drawn as the face's own file, check_reference passed, 4 refusals"
      if not failed else "check_face_bundle: FAILED")
sys.exit(1 if failed else 0)
