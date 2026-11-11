"""Check the advance table and the drawing file train/pack.py makes
against the C library.

usage: python3 tests/check_advances.py LIB.so NET.json

Writes an advances file, packs it by itself and in a drawing file with
the net, and opens both through the library. The steps the library reads
must be the ones written, its pixels must be pack.pixels(), and a line of
text must measure as the sum of its characters. The packer must also
refuse what the library would refuse.
"""
import ctypes
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
import pack  # noqa: E402

if len(sys.argv) != 3:
    raise SystemExit(__doc__)
lib = ctypes.CDLL(os.path.abspath(sys.argv[1]))
lib.neuronte_open.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_close.argtypes = [ctypes.c_void_p]
lib.neuronte_advances.argtypes = [ctypes.c_void_p]
lib.neuronte_nets.argtypes = [ctypes.c_void_p]
lib.neuronte_advance_steps.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
lib.neuronte_advance.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int]
lib.neuronte_advance_scalar.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
lib.neuronte_advance_scalar.restype = ctypes.c_uint32
lib.neuronte_text_width.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]

failed = False


def fail(msg):
    global failed
    print("FAIL", msg)
    failed = True


# The example in the format note, byte for byte.
EXAMPLE = bytes.fromhex(
    "4e4555524f4e5445" "040000000a000000" "0a00000002000000" "030000003f000000"
    "200000001e001e00" "3f00000037003e00" "262000005a006000")
if pack.advances({0x20: (30, 30), 0x3F: (55, 62), 0x2026: (90, 96)}) != EXAMPLE:
    fail("the packer does not make the format note's example")

# Every printable ASCII character and the ellipsis, every advance from
# 1.0 to 20.0 among them, written the two ways a line may name a character.
want = {}
lines = ["# Made by tests/check_advances.py. Not a face.", "#", ""]
for i, v in enumerate(list(range(0x20, 0x7F)) + [0x2026]):
    reg, bold = 10 + (i * 37) % 191, 200 - (i * 53) % 191
    want[v] = (reg, bold)
    name = chr(v) if 0x21 <= v <= 0x7E and chr(v) not in "#U" and i % 2 else f"U+{v:04X}"
    lines.append(f"{name} {reg / 10:.1f} {bold // 10}.{bold % 10}")
TEXT = "Start … ~{}?"


def check(handle, name, nets):
    if lib.neuronte_advances(handle) != len(want) or lib.neuronte_nets(handle) != nets:
        fail(f"{name}: {lib.neuronte_advances(handle)} advances and {lib.neuronte_nets(handle)} nets")
    for v, steps in want.items():
        for bold in (0, 1):
            if lib.neuronte_advance_steps(handle, v, bold) != steps[bold]:
                fail(f"{name}: U+{v:04X} weight {bold} is not {steps[bold]} steps")
            for em in (10, 11, 16):
                if lib.neuronte_advance(handle, v, bold, em) != pack.pixels(steps[bold], em):
                    fail(f"{name}: U+{v:04X} weight {bold} at {em} px is not {pack.pixels(steps[bold], em)}")
    for v in (0x07, 0x7F, 0xE9, 0x2025, 0x10FFFF):
        if lib.neuronte_advance_scalar(handle, v) != 0x3F or lib.neuronte_advance_steps(handle, v, 0) != want[0x3F][0]:
            fail(f"{name}: U+{v:04X}, which has no line, is not measured as ?")
    raw = TEXT.encode()
    for bold in (0, 1):
        for em in (10, 11):
            total = sum(pack.pixels(want[ord(c)][bold], em) for c in TEXT)
            if lib.neuronte_text_width(handle, raw, len(raw), bold, em) != total:
                fail(f"{name}: text weight {bold} at {em} px is not {total} px wide")


def opened(path):
    handle = ctypes.c_void_p()
    rc = lib.neuronte_open_file(path.encode(), ctypes.byref(handle))
    return rc, handle


def refused(args, what):
    """The packer, run as a command, must stop with a message and write nothing."""
    out = os.path.join(tmp, "refused.nrt")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "train", "pack.py")] + args + [out],
                       capture_output=True, text=True)
    if r.returncode == 0 or os.path.exists(out) or "Traceback" in r.stderr:
        fail(f"the packer did not refuse {what}")
        if os.path.exists(out):
            os.remove(out)


def text(name, body):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


with tempfile.TemporaryDirectory() as tmp:
    adv = text("advances.txt", "\n".join(lines) + "\n")
    table, both = os.path.join(tmp, "table.nrt"), os.path.join(tmp, "drawing.nrt")
    py = [sys.executable, os.path.join(ROOT, "train", "pack.py")]
    subprocess.run(py + ["--advances", adv, table], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(py + ["--drawing", both, sys.argv[2], adv], check=True, stdout=subprocess.DEVNULL)
    with open(table, "rb") as fh:
        image = fh.read()
    if image != pack.advances(want) or len(image) != 32 + 8 * 96:
        fail("the table file is not what pack.advances() makes, or not 800 bytes")
    net = pack.pack(sys.argv[2])
    with open(both, "rb") as fh:
        if fh.read() != pack.drawing([sys.argv[2], adv])[0]:
            fail("the drawing file is not what pack.drawing() makes")
    for path, name, nets in ((table, "table", 0), (both, "drawing file", 1)):
        rc, handle = opened(path)
        if rc != 0:
            fail(f"{name}: neuronte_open_file returned {rc}")
        else:
            check(handle, name, nets)
            lib.neuronte_close(handle)

    # Members already packed are copied whole, and a colour net is not read.
    netfile = os.path.join(tmp, "net.nrt")
    with open(netfile, "wb") as fh:
        fh.write(net)
    colour = os.path.join(tmp, "colour.nrt")
    with open(colour, "wb") as fh:
        fh.write(b"NEURONTE" + (3).to_bytes(4, "little") + bytes(40))
    mixed = os.path.join(tmp, "mixed.nrt")
    subprocess.run(py + ["--drawing", mixed, colour, table, netfile], check=True, stdout=subprocess.DEVNULL)
    rc, handle = opened(mixed)
    if rc != 0:
        fail(f"drawing file of a colour net, a table and a net: open returned {rc}")
    else:
        check(handle, "drawing file of packed members", 1)
        lib.neuronte_close(handle)

    # --bold-add fills a line that has one number, and only such a line.
    short = text("short.txt", "U+0020 3.0\n? 5.5 6.0\nA 6.4\n")
    subprocess.run(py + ["--advances", short, mixed, "--bold-add", "0.7"], check=True, stdout=subprocess.DEVNULL)
    with open(mixed, "rb") as fh:
        if fh.read() != pack.advances({0x20: (30, 37), 0x3F: (55, 60), 0x41: (64, 71)}):
            fail("--bold-add 0.7 does not make bold the regular advance and 0.7")

    # Refusals.
    refused(["--advances", short], "a line with one advance and no --bold-add")
    for body, what in (("? 5.5 6.0\n? 5.5 6.0\n", "a character with two lines"),
                       ("? 5.5 6.0\nU+003F 5.5 6.0\n", "a character named twice, two ways"),
                       ("? 0.9 6.0\n", "an advance of 0.9"),
                       ("? 5.5 20.1\n", "an advance of 20.1"),
                       ("? 5.55 6.0\n", "an advance with two decimals"),
                       ("? 5.5 wide\n", "an advance that is not a number"),
                       ("? nan 6.0\n", "an advance of nan"),
                       ("? 5.5 6.0 7.0\n", "three advances"),
                       ("?? 5.5 6.0\n", "two characters on a line"),
                       ("U+D800 5.5 6.0\n? 5.5 6.0\n", "a surrogate"),
                       ("U+110000 5.5 6.0\n? 5.5 6.0\n", "a scalar above U+10FFFF"),
                       ("A 5.5 6.0\n", "a table with no line for the fallback"),
                       ("# nothing\n", "an empty table")):
        refused(["--advances", text("bad.txt", body)], what)
    refused(["--advances", adv, "--fallback-char", "U+00E9"], "a fallback with no line")
    refused(["--advances", adv, "--bold-add"], "--bold-add with no value")
    refused(["--drawing"], "a drawing file with no members")
    for members, what in (([adv, adv], "two advance tables"),
                          ([table, adv], "two advance tables, one packed"),
                          ([both], "a drawing file inside a drawing file"),
                          ([text("cut.nrt", "NEURONTE")], "a packed member with no version")):
        out = os.path.join(tmp, "refused.nrt")
        r = subprocess.run(py + ["--drawing", out] + members, capture_output=True, text=True)
        if r.returncode == 0 or os.path.exists(out) or "Traceback" in r.stderr:
            fail(f"the packer did not refuse {what}")
    cut = os.path.join(tmp, "cutnet.nrt")
    with open(cut, "wb") as fh:
        fh.write(net[:-1])
    r = subprocess.run(py + ["--drawing", os.path.join(tmp, "refused.nrt"), cut], capture_output=True, text=True)
    if r.returncode == 0 or "Traceback" in r.stderr:
        fail("the packer did not refuse a net one byte short")

print(f"check_advances: {len(want)} characters, a table and two drawing files")
print("check_advances: FAILED" if failed else "check_advances: passed")
sys.exit(1 if failed else 0)
