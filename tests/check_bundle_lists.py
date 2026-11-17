"""Every bundle with a list was trained on exactly its list, and no two
bundles of the terminal family claim one character.

usage: python3 tests/check_bundle_lists.py build/libneuronte.so [WEIGHTS_DIR]

A bundle weights/NAME.nrt has a list when weights/NAME.list.txt is beside
it (the format train/standalone_bundle.py reads). For each such bundle:
its table holds the listed scalars and no other; the library routes every
listed scalar to the table's member and reports it trained; it reports
every scalar of the other bundles untrained. No listed scalar is in the
table of a bundle named in BESIDE, and no two lists share one. Adding a
bundle to the family is adding its two files; this check finds them.

The rules themselves are tried first on small bundles built here, so the
check means something before any listed bundle is shipped.
"""
import ctypes as C
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
import pack  # noqa: E402
import standalone_bundle as sb  # noqa: E402

# The bundles a listed bundle is opened beside.
BESIDE = ("neuronte-split-v9.nrt",)

lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
P = C.c_void_p
lib.neuronte_open.argtypes = [C.c_void_p, C.c_size_t, C.POINTER(P)]
lib.neuronte_close.argtypes = [P]
lib.neuronte_route.argtypes = [P, C.c_uint32]
lib.neuronte_untrained.argtypes = [P, C.c_uint32]


def problems(directory):
    """What is wrong with the listed bundles of a directory, and how many there are."""
    directory = Path(directory)
    wrong, claims = [], {}
    beside = {}
    for name in BESIDE:
        table = sb.read_table((ROOT / "weights" / name).read_bytes())
        assert table, name
        beside[name] = set(table)
    lists = sorted(directory.glob("*.list.txt"))
    for path in lists:
        name = path.name[:-len(".list.txt")]
        bundle = directory / (name + ".nrt")
        if not bundle.exists():
            wrong.append(f"{path.name}: no {bundle.name} beside it")
            continue
        listed = sb.read_list(str(path))
        data = bundle.read_bytes()
        table = sb.read_table(data)
        if table is None:
            wrong.append(f"{bundle.name}: has a list and no table")
            continue
        want, have = set(listed), set(table)
        if want != have:
            wrong.append(f"{bundle.name}: {len(want - have)} listed and not in the table, "
                         f"{len(have - want)} in the table and not listed")
        for other, scalars in beside.items():
            if want & scalars or have & scalars:
                wrong.append(f"{bundle.name}: shares {len((want | have) & scalars)} characters with {other}")
        for v in want | have:
            if v in claims:
                wrong.append(f"{bundle.name}: U+{v:04X} is also in {claims[v]}")
                break
        claims.update({v: bundle.name for v in want | have})
        h = P()
        assert lib.neuronte_open(data, len(data), C.byref(h)) == 0, bundle
        try:
            bad = [v for v in sorted(have) if lib.neuronte_route(h, v) != table[v] or lib.neuronte_untrained(h, v) != 0]
            if bad:
                wrong.append(f"{bundle.name}: the library does not send U+{bad[0]:04X} to its net as trained")
            others = set().union(*beside.values()) - have
            bad = [v for v in sorted(others) if lib.neuronte_untrained(h, v) != 1]
            if bad:
                wrong.append(f"{bundle.name}: reports U+{bad[0]:04X} of another bundle trained")
        finally:
            lib.neuronte_close(h)
    return wrong, len(lists)


def self_test():
    nets = [str(ROOT / f"weights/neuronte-tsymbol-v1-g{g}.json") for g in (0, 1)]
    owner = [sorted(pack.scalars(p)[1]) for p in nets]

    def write(directory, name, paths, listed):
        image, _ = sb.standalone(paths, [v for p in paths for v in sorted(pack.scalars(p)[1])])
        (directory / f"{name}.nrt").write_bytes(image)
        (directory / f"{name}.list.txt").write_text(" ".join(f"U+{v:04X}" for v in listed) + "\n")

    global BESIDE
    kept, BESIDE = BESIDE, ("neuronte-split-v8.nrt",)     # split-v8 has none of these symbols
    try:
        with tempfile.TemporaryDirectory(prefix="bundle-lists-") as tmp:
            d = Path(tmp)
            write(d, "a", nets[:1], owner[0])
            write(d, "b", nets[1:], owner[1])
            assert problems(d) == ([], 2), problems(d)
            write(d, "b", nets[1:], owner[1][:-1])
            assert any("in the table and not listed" in w for w in problems(d)[0])
            write(d, "b", nets[1:], owner[1] + [0x10FFFD])
            assert any("1 listed and not in the table" in w for w in problems(d)[0])
            write(d, "b", nets[:1], owner[0])
            assert any("is also in a.nrt" in w for w in problems(d)[0])
            (d / "b.nrt").unlink()
            assert any("no b.nrt beside it" in w for w in problems(d)[0])
        BESIDE = ("neuronte-split-v9.nrt",)               # split-v9 has all of them
        with tempfile.TemporaryDirectory(prefix="bundle-lists-") as tmp:
            d = Path(tmp)
            write(d, "a", nets[:1], owner[0])
            assert any("with neuronte-split-v9.nrt" in w for w in problems(d)[0])
    finally:
        BESIDE = kept


self_test()
wrong, count = problems(sys.argv[2] if len(sys.argv) > 2 else ROOT / "weights")
for w in wrong:
    print("FAIL", w)
if wrong:
    raise SystemExit(1)
print(f"bundle lists: the five rules hold on test bundles; {count} listed bundle{'s' * (count != 1)} in weights/, "
      f"each trained on exactly its list and apart from {', '.join(BESIDE)} and from each other")
