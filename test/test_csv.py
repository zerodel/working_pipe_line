# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#



__doc__ = '''
'''
__author__ = 'zerodel'

from collections import namedtuple
import csv
import re
import py.file_format.gtf

header_tmp = """circRNA_id      chr     start   end     strand  #junction_reads PCC(MS_SM_SMS)  #non_junction_reads     junction_reads_ratio    circRNA_type    gene_id cirexon_id      cirexon_start   cirexon_end     #start_supporting_BSJ_read      #end_supporting_BSJ_read        sequencing_depth_median if_ICF"""



def _remove_bracket(str_header):
    import re
    return re.sub("\([A-Za-z0-9\_\-]+\)", "", str_header)


def _remove_sharp(str_header):
    import re
    return re.sub("#", "", str_header)


def load_cirias_list(ciri_as_list, sep="\t"):
    with open(ciri_as_list) as f:
        header = next(f)
        header = _remove_bracket(header)
        header = _remove_sharp(header)
        header_name = namedtuple("as_row", [x for x in header.strip().split(sep)])

        rdr = csv.reader(f, delimiter=sep)
        for line in rdr:
            row = header_name(*line)
            yield row

exons_of = {}

for row in load_cirias_list(path_to_as_output):
    exons_of.setdefault(row.circRNA_id, []).append(row)

for circ_id in exons_of:
    exons_of[circ_id] = sorted(exons_of[circ_id], key=lambda x: x.cirexon_start)

k, v = exons_of.popitem()
print(k)


def make_gtf_entry(cir_exon):
    artificial_exon = py.file_format.gtf.GTFitem()
    artificial_exon.set_start(int(cir_exon.cirexon_start))
    artificial_exon.set_end(int(cir_exon.cirexon_end))
    artificial_exon.set_gene_id(cir_exon.gene_id)
    artificial_exon.set_transcript_id(cir_exon.circRNA_id)
    artificial_exon.set_seqname(cir_exon.chr)
    artificial_exon.set_source("ciri")
    artificial_exon.set_feature("exon")
    artificial_exon.set_strand(cir_exon.strand)
    artificial_exon.set_frame(".")
    return artificial_exon


for exon in v:
    print('\n')
    print(exon)
    print("gtf line: ")
    x = make_gtf_entry(exon)
    print(x)