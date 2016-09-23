# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os

import py.knife


__doc__ = '''
'''
__author__ = 'zerodel'


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        py.knife.extract_bed_from_knife_report_path(sys.argv[-2], sys.argv[-1])