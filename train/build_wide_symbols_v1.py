"""Rebuild neuronte-wide-symbols-v1, drawn for a box of two cells (see train/wide_build.py).

usage: python3 train/build_wide_symbols_v1.py [--files]
"""
import sys

import wide_build

NAME = 'neuronte-wide-symbols-v1'

# (training set, group) retrained as two halves
HALVED = (('twds0', 2), ('twds0', 3), ('twds0', 6), ('twds1', 1), ('twds1', 2), ('twds1', 3), ('twds1', 4), ('twds1', 5), ('twds1', 6), ('twds1', 7), ('twds1', 8), ('twds2', 0), ('twds2', 1), ('twds2', 2), ('twds2', 3), ('twds2', 4), ('twds2', 5), ('twds3', 3), ('twds3', 5), ('twds3', 7), ('twds3', 8), ('twds4', 0), ('twds4', 1), ('twds4', 2), ('twds4', 3), ('twds4', 4), ('twds4', 5), ('twds4', 8), ('twds5', 0), ('twds5', 1), ('twds5', 2), ('twds5', 3), ('twds5', 6),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {
    ('twds0r6', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds1r1', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r2', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r2', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r3', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r4', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r4', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r5', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r5', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r6', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r6', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r7', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r7', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r8', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds1r8', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r0', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r0', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r1', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r1', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r2', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r3', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds2r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r4', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r4', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds2r5', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds3r5', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds3r8', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r0', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds4r1', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r2', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r2', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds4r3', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r4', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r5', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r5', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds4r8', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds5r0', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twds5r1', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds5r1', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds5r2', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twds5r2', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
}

# {(set, group): why} halves that failed the gates again, in the bundle by the owner's word
FAILED_SHIPPED = {}

BUNDLE = wide_build.Bundle(NAME, HALVED, LEFT_OUT, FAILED_SHIPPED)

if __name__ == '__main__':
    sys.exit(BUNDLE.main(sys.argv[1:]))
