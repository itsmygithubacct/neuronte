"""Rebuild neuronte-wide-supplement-v1, drawn for a box of two cells (see train/wide_build.py).

usage: python3 train/build_wide_supplement_v1.py [--files]
"""
import sys

import wide_build

NAME = 'neuronte-wide-supplement-v1'

# (training set, group) retrained as two halves
HALVED = (('twdu0', 1), ('twdu0', 3), ('twdu0', 4), ('twdu0', 5), ('twdu0', 6), ('twdu0', 9), ('twdu1', 2), ('twdu1', 6), ('twdu1', 7), ('twdu1', 8), ('twdu1', 9), ('twdu2', 0), ('twdu2', 1), ('twdu2', 3), ('twdu2', 4), ('twdu2', 5), ('twdu2', 6), ('twdu2', 7), ('twdu3', 2), ('twdu3', 3), ('twdu3', 4), ('twdu3', 7), ('twdu3', 8), ('twdu3', 9), ('twdu4', 1), ('twdu4', 3), ('twdu4', 4), ('twdu4', 6), ('twdu4', 7), ('twdu4', 9), ('twdu5', 0), ('twdu5', 1), ('twdu5', 3), ('twdu5', 8), ('twdu5', 9),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {
    ('twdu0r1', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu0r5', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu0r6', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu0r9', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu0r9', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu2r1', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu2r1', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu2r3', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu2r4', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu2r4', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu2r5', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu2r6', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu2r6', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu3r2', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu3r2', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu3r7', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu3r7', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu3r8', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu3r8', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu4r1', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu4r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu4r7', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu4r9', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu5r0', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdu5r1', 0): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu5r1', 1): 'one seed failed the declared gates, as half of a group that had failed',
    ('twdu5r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
}

# {(set, group): why} halves that failed the gates again, in the bundle by the owner's word
FAILED_SHIPPED = {}

BUNDLE = wide_build.Bundle(NAME, HALVED, LEFT_OUT, FAILED_SHIPPED)

if __name__ == '__main__':
    sys.exit(BUNDLE.main(sys.argv[1:]))
