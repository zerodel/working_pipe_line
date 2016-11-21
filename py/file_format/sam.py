# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
# todo: need to convert sam to fastq


__doc__ = '''
'''
__author__ = 'zerodel'

import py.body.logger

_logger = py.body.logger.default_logger("sam")

try:
    import pysam
except ImportError:
    _logger.warning("ImportERROR: unable to load pysam module")


class sam():
    def __init__(self, str):
        pass


# def pysam_parse(sam_file):
#     with open(sam_file) as sam_file:
#         for line in sam_file:
#             if line.startswith("@"):
#                 continue
#             else:
#                 yield sam(line.strip())


def pysam_parse(sam_file):
    pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
