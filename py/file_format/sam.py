# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
# todo: need to convert sam to fastq

import py.body.logger

__doc__ = '''
'''
__author__ = 'zerodel'


_logger = py.body.logger.default_logger("sam")

try:
    import pysam
except ImportError:
    _logger.warning("ImportERROR: unable to load pysam module")


class sam(object):
    def __init__(self, str_sam):
        pass


# def pysam_parse(sam_file):
#     with open(sam_file) as sam_file:
#         for line in sam_file:
#             if line.startswith("@"):
#                 continue
#             else:
#                 yield sam(line.strip())


part_path = "/Users/zerodel/projects/Pipeline/test/part.sam"

sam = pysam.AlignmentFile(part_path)

a = next(sam)

a.get_cigar_stats()

b = next(sam)

a.get_reference_positions()


