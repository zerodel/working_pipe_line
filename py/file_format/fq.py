# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os
import Bio.SeqIO as bo


__doc__ = '''
'''
__author__ = 'zerodel'

FASTQ_FILE_EXTENSION = [".fastq", ".fq"]


def is_pair_end_fastq_id_identical(fq1_path, fq2_path):
    num_id = 3
    counter = 0
    fq_entries = zip(bo.parse(fq1_path, "fastq"), bo.parse(fq2_path, "fastq"))

    for r1, r2 in fq_entries:
        counter += 1
        if counter > num_id:
            return True
        if (r1.id != r2.id) or (str(r1.description).strip() != str(r2.description).strip()):
            return False

    if 0 == counter:
        raise KeyError("Error@fq_checking_id_style: empty fastq files or wrong file format.")
    else:
        return True


def get_read_length(fq):
    fq_parser = bo.parse(fq, "fastq")
    one_read_entry = next(fq_parser)
    return len(one_read_entry.seq)



if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass