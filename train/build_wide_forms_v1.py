"""Rebuild neuronte-wide-forms-v1, drawn for a box of two cells (see train/wide_build.py).

usage: python3 train/build_wide_forms_v1.py [--files]
"""
import sys

import wide_build

NAME = 'neuronte-wide-forms-v1'

# (training set, group) retrained as two halves
HALVED = (('twdf0', 10),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {}

BUNDLE = wide_build.Bundle(NAME, HALVED, LEFT_OUT)

if __name__ == '__main__':
    sys.exit(BUNDLE.main(sys.argv[1:]))
