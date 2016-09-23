# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
# todo: need to convert sam to fastq


__doc__ = '''
'''
__author__ = 'zerodel'


class sam():
    def __init__(self, str):
        pass


def parse(sam_file):
    with open(sam_file) as sam_file:
        for line in sam_file:
            if line.startswith("@"):
                continue
            else:
                yield sam(line.strip())







if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass