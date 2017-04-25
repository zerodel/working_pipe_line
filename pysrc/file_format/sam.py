# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
# todo: need to convert sam to fastq

import pysrc.body.logger

__doc__ = '''
'''
__author__ = 'zerodel'

_logger = pysrc.body.logger.default_logger("sam")

try:
    import pysam
except ImportError:
    _logger.error("ImportERROR: unable to load pysam module")
    raise ImportError("unable to load pysam")


class AlignEntry(object):
    def __init__(self, str_line_sam):
        pass
