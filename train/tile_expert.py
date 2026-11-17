"""Train the tile nets of a tiled member with split_expert.py's own loop.

usage: python3 train/tile_expert.py COLUMNSxROWS DIR [split_expert.py's train options]
       e.g. tile_expert.py 1x6 teachers/tblkhex --budget 96 --steps 120000 --seeds 0,1

split_expert.py's spatial mode trains one net for each tile of a grid: the
net sees its tile of every character of the set, stretched to the whole
cell, and is given the character's own scalar. It lists a few square
grids. This runs the same code, unchanged and imported, on a grid of
COLUMNS by ROWS equal tiles, for sets whose parts lie in such a grid
(train/term_blocks.py TILE_GRID). The tile nets are assembled into one
tiled (version 6) member by train/tile_member.py.

--budget is shared equally: each tile net is budget / (COLUMNS x ROWS) wide.
MIT licence; see LICENSE.
"""
import sys

import split_expert


def main():
    if len(sys.argv) < 3 or "x" not in sys.argv[1]:
        raise SystemExit(__doc__)
    columns, rows = (int(v) for v in sys.argv[1].split("x"))
    if not (1 <= columns <= 16 and 1 <= rows <= 16):
        raise SystemExit("a tiled net has 1 to 16 columns and rows")
    count = columns * rows
    split_expert.GRIDS = {count: (columns, rows)}
    sys.argv = [sys.argv[0], "train", sys.argv[2], "--mode", "spatial", "--parts", str(count)] + sys.argv[3:]
    split_expert.main()


if __name__ == "__main__":
    main()
