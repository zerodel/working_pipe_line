# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import copy
import csv
from collections import namedtuple

import py.body.logger
import py.file_format.gtf

__doc__ = ''' transform CIRI-AS output file into gtf file
'''
__author__ = 'zerodel'

ciri_as_file_head = """circRNA_id      chr     start   end     strand  #junction_reads PCC(MS_SM_SMS)  #non_junction_reads     junction_reads_ratio    circRNA_type    gene_id cirexon_id      cirexon_start   cirexon_end     #start_supporting_BSJ_read      #end_supporting_BSJ_read        sequencing_depth_median if_ICF"""

as_event_file = "circRNA_id	alternatively_spliced_exon	AS_type	psi_estimation_without_correction	psi_estimation_after_correction"

_logger = py.body.logger.default_logger("transform_ciri_as_to_gtf")


def _exons_showing_a5ss_of_one_circRNA(sorted_exons, a5ss_event):  # a5ss means 5' splice site change
    start, end = a5ss_event.alternatively_spliced_exon.strip().split(":")
    output_exons = []
    for exon in sorted_exons:
        if exon.cirexon_start == start and exon.cirexon_end != end:
            continue
        output_exons.append(exon)
    return output_exons


def _exons_showing_a3ss_of_one_circRNA(sorted_exons, a3ss_event):
    start, end = a3ss_event.alternatively_spliced_exon.strip().split(":")
    output_exons = []
    for exon in sorted_exons:
        if exon.cirexon_start != start and exon.cirexon_end == end:
            continue
        output_exons.append(exon)
    return output_exons


def _exons_showing_es_of_one_circRNA(sorted_exons, es_event):
    start, end = es_event.alternatively_spliced_exon.strip().split(":")
    output_exons = []
    for exon in sorted_exons:
        if exon.cirexon_start == start and exon.cirexon_end == end:
            continue
        output_exons.append(exon)
    return output_exons


def _exons_showing_ir_of_one_circRNA(sorted_exons, ir_event):  # todo: not knowing how to deal with it
    return copy.copy(sorted_exons)


def _remove_bracket(str_header):
    import re
    return re.sub("\([A-Za-z0-9\_\-]+\)", "", str_header)


def _remove_sharp(str_header):
    import re
    return re.sub("#", "", str_header)


def parse_ciri_as_list_as_named_tuples(ciri_as_output_file, sep="\t"):
    with open(ciri_as_output_file) as f:
        header = next(f)
        header = _remove_bracket(header)
        header = _remove_sharp(header)
        header_name = namedtuple("as_row", [x for x in header.strip().split(sep)])

        rdr = csv.reader(f, delimiter=sep)
        for line in rdr:
            yield (header_name(*line))


def _make_gtf_entry_from_ciri_as_list_entry(cir_exon):
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


def transform_as_output_to_gtf(ciri_as_file_prefix, gtf_file):
    exons_of = _load_circular_exon_list_as_dict(_get_ciri_as_file_path_of_exon_list(ciri_as_file_prefix))

    gtf_entries = [_make_gtf_entry_from_ciri_as_list_entry(exon) for circRNA_id in exons_of for exon in
                   exons_of[circRNA_id]]

    with open(gtf_file, "w") as write_it:
        write_it.write("\n".join([str(entry) for entry in gtf_entries]))


def _load_circular_exon_list_as_dict(as_file):
    exons_of = {}
    for row in parse_ciri_as_list_as_named_tuples(as_file):
        exons_of.setdefault(row.circRNA_id, []).append(row)
    for circ_id in exons_of:  # sort exons
        exons_of[circ_id] = sorted(exons_of[circ_id], key=lambda x: x.cirexon_start)
    return exons_of


def _load_alternative_splice_events_to_dict(as_file):
    alter_splice_of = {}
    for row in parse_ciri_as_list_as_named_tuples(as_file):
        alter_splice_of.setdefault(row.circRNA_id, []).append(row)
    return alter_splice_of


deal_with_as_event = {"A5SS": _exons_showing_a5ss_of_one_circRNA,
                      "A3SS": _exons_showing_a3ss_of_one_circRNA,
                      "ES": _exons_showing_es_of_one_circRNA,
                      "IR": _exons_showing_ir_of_one_circRNA
                      }


def _exons_showing_as_event(exons, event):
    as_type = str(event.AS_type).strip().strip(",")
    return deal_with_as_event[as_type](exons, event)


def _get_ciri_as_file_path_of_alternative_splicing_events(ciri_as_file_prefix):
    return "_".join([ciri_as_file_prefix, "AS.list"])


def _get_ciri_as_file_path_of_exon_list(ciri_as_file_prefix):
    return ".".join([ciri_as_file_prefix, "list"])


def transform_as_to_gtf_showing_as_event(ciri_as_file_prefix, gtf_file):
    exons_of = _load_circular_exon_list_as_dict(_get_ciri_as_file_path_of_exon_list(ciri_as_file_prefix))

    splice_events_of = _load_alternative_splice_events_to_dict(
        _get_ciri_as_file_path_of_alternative_splicing_events(ciri_as_file_prefix))

    _logger.debug("there is %d transcripts have as events " % sum([1 for x in splice_events_of]))

    output_gtf_entries = []
    for circ_id in exons_of:
        exons_this = exons_of[circ_id]

        if circ_id in splice_events_of:
            isoform_count = 0
            for event in splice_events_of[circ_id]:

                exons_this_event = _exons_showing_as_event(exons_this, event)
                gtf_of_this_event = [_make_gtf_entry_from_ciri_as_list_entry(exon) for exon in exons_this_event]

                for exon in gtf_of_this_event:
                    exon.set_transcript_id("%s.%d" % (circ_id, isoform_count))

                output_gtf_entries.extend(gtf_of_this_event)
                isoform_count += 1
        else:
            output_gtf_entries.extend([_make_gtf_entry_from_ciri_as_list_entry(exon) for exon in exons_this])

    with open(gtf_file, "w") as write_gtf_file:
        write_gtf_file.write("\n".join([str(gtf_entry) for gtf_entry in output_gtf_entries]))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        transform_as_output_to_gtf(sys.argv[-2], sys.argv[-1])
