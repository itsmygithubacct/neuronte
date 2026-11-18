"""Rebuild neuronte-wide-pictographs2-v1 (sets twdp5..twdp9: the second file of the pictographs, see FILE_SPLIT in train/wide.py), drawn for a box of two cells (see train/wide_build.py).

usage: python3 train/build_wide_pictographs2_v1.py [--files]
"""
import sys

import wide_build

NAME = 'neuronte-wide-pictographs2-v1'

# (training set, group) retrained as two halves
HALVED = (('twdp5', 0), ('twdp5', 9), ('twdp6', 5), ('twdp6', 6), ('twdp6', 8), ('twdp6', 9), ('twdp7', 0), ('twdp7', 2), ('twdp7', 3), ('twdp7', 4), ('twdp7', 6), ('twdp7', 7), ('twdp7', 8), ('twdp7', 9), ('twdp8', 0), ('twdp8', 1), ('twdp8', 2), ('twdp8', 4), ('twdp8', 5), ('twdp8', 6), ('twdp8', 7), ('twdp8', 8), ('twdp9', 4),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {
    ('twdp7r3', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdp7r7', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdp8r1', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdp8r6', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdp8r7', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
}

# {(set, group): why} halves that failed the gates again, in the bundle by the owner's word
FAILED_SHIPPED = {
    ('twdp5r9', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp5r9', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp6r6', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp6r6', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp6r9', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp6r9', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp7r2', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp7r8', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r0', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r1', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r2', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r5', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r5', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r8', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp8r8', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp9r4', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
}

BUNDLE = wide_build.Bundle(NAME, HALVED, LEFT_OUT, FAILED_SHIPPED)

if __name__ == '__main__':
    sys.exit(BUNDLE.main(sys.argv[1:]))
