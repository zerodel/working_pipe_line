# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import argparse
import os
import sys

upper_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

sys.path.append(upper_root)

import pysrc.sub_module.summary_quant as sq

parser = argparse.ArgumentParser()
parser.add_argument("anno", help="path to annotation file", default="", nargs="+")
parser.add_argument("-o", help="output file location", default="")

__doc__ = ''' summarize the host gene information from 
'''

__author__ = 'zerodel'

if __name__ == "__main__":
    args = parser.parse_args()
    if args.o and args.anno:
        isoform_ownership = sq.TranscriptOwnership()
        for single_anno in args.anno:
            if os.path.isfile(single_anno):
                isoform_ownership.parse_gtf(single_anno)
            else:
                print("a wrong path is given : {}".format(single_anno))
                continue
        with open(args.o, "w") as dump_it:
            for line in isoform_ownership.to_text_table_lines():
                dump_it.write("{}\n".format(line.strip()))
