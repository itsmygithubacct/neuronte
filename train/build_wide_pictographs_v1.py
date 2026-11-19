"""Rebuild neuronte-wide-pictographs-v1 (sets twdp0..twdp4), drawn for a box of two cells (see train/wide_build.py).

usage: python3 train/build_wide_pictographs_v1.py [--files]
"""
import sys

import wide_build

NAME = 'neuronte-wide-pictographs-v1'

# (training set, group) retrained as two halves
HALVED = (('twdp0', 0), ('twdp0', 1), ('twdp0', 3), ('twdp0', 5), ('twdp0', 8), ('twdp0', 9), ('twdp1', 0), ('twdp1', 1), ('twdp1', 4), ('twdp1', 7), ('twdp2', 1), ('twdp2', 3), ('twdp2', 4), ('twdp2', 5), ('twdp2', 6), ('twdp2', 7), ('twdp2', 8), ('twdp2', 9), ('twdp3', 0), ('twdp3', 1), ('twdp3', 3), ('twdp3', 4), ('twdp3', 5), ('twdp3', 6), ('twdp3', 8), ('twdp4', 1), ('twdp4', 2), ('twdp4', 4), ('twdp4', 5), ('twdp4', 7),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {
    ('twdp3r4', 0): 'failed the declared gates with both seeds, as half of a group that had failed',
    ('twdp3r4', 1): 'failed the declared gates with both seeds, as half of a group that had failed',
}

# {(set, group): why} halves that failed the gates again, in the bundle by the owner's word
FAILED_SHIPPED = {
    ('twdp0r1', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp0r1', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp0r8', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp0r8', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp0r9', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp1r0', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp1r4', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp1r7', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp1r7', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r1', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r1', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r3', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r5', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r5', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r8', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp2r9', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r0', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r1', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r3', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r3', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r5', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp3r8', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp4r1', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp4r1', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp4r2', 0): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp4r5', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
    ('twdp4r7', 1): 'failed the declared gates; shipped by the owner\'s word after looking at the sheet of failed halves (2026-11-18): the owner\'s choice "Within 25%", every failed half whose lower-error seed misses its limits by at most 25%; described as failed',
}

BUNDLE = wide_build.Bundle(NAME, HALVED, LEFT_OUT, FAILED_SHIPPED)

if __name__ == '__main__':
    sys.exit(BUNDLE.main(sys.argv[1:]))
