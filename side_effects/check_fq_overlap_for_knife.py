# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os

import sys

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

import pysrc.sub_module.summary_quant

__doc__ = '''
'''

__author__ = 'zerodel'

if __name__ == "__main__":
    pysrc.sub_module.summary_quant.aggregate_isoform_quantify_result(quant_sf=sys.argv[-4],
                                                                     summarized_output=sys.argv[-3],
                                                                     gtf_annotation=sys.argv[-2],
                                                                     ciri_output=sys.argv[-1])
