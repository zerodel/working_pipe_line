# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os
import copy


import py.body.logger
import py.file_format.gtf

__doc__ = ''' transform CIRI-ASv1.2 output file into gtf file
'''
__author__ = 'zerodel'

ciri_as_file_head = """circRNA_id      chr     start   end     strand  #junction_reads PCC(MS_SM_SMS)  #non_junction_reads     junction_reads_ratio    circRNA_type    gene_id cirexon_id      cirexon_start   cirexon_end     #start_supporting_BSJ_read      #end_supporting_BSJ_read        sequencing_depth_median if_ICF"""

as_event_file = "circRNA_id	alternatively_spliced_exon	AS_type	psi_estimation_without_correction	psi_estimation_after_correction"

_logger = py.body.logger.default_logger("transform_ciri_as_to_gtf")


def _get_ciri_as_file_path_of_alternative_splicing_events(ciri_as_file_prefix):
    return "_".join([ciri_as_file_prefix, "AS.list"])


def _get_ciri_path_file_path(ciri_as_file_prefix):
    return "_".join([ciri_as_file_prefix, "path.output"])


def _get_ciri_log2_file_path(ciri_as_file_prefix):
    return ".".join([ciri_as_file_prefix, "log2"])


def _get_ciri_as_file_path_of_exon_list(ciri_as_file_prefix):
    return ".".join([ciri_as_file_prefix, "list"])


def _load_ciri_exons_from_exon_file_to_gtf_entries(file_path_exon_file):
    gtf_entry_of_circ_exon = {}

    with open(file_path_exon_file) as exon_table:
        header = exon_table.readline().strip().split("\t")
        pos_index_circRNA_id = header.index("circRNA_id")
        pos_index_chr = header.index("chr")

        pos_index_cirexon_start = header.index("cirexon_start")
        pos_index_cirexon_end = header.index("cirexon_end")
        pos_index_strand_this_exon = header.index("strand")
        pos_index_gene_id_this_exon = header.index("gene_id")

        for line in exon_table:
            parts = line.strip().split("\t")
            id_circ_rna = parts[pos_index_circRNA_id]

            chr = parts[pos_index_chr]
            gene_id = parts[pos_index_gene_id_this_exon]
            start_exon = parts[pos_index_cirexon_start]
            end_exon = parts[pos_index_cirexon_end]
            strand_unique = parts[pos_index_strand_this_exon]

            unique_id = "%s=>%s:%s" % (id_circ_rna,
                                       start_exon,
                                       end_exon)

            gtf_entry_of_circ_exon[unique_id] = _make_gtf_entry_exon(
                start=start_exon,
                end=end_exon,
                gene_id=gene_id,
                circRNA_id=id_circ_rna,
                chr=chr,
                strand=strand_unique
            )

    return gtf_entry_of_circ_exon


def _make_gtf_entry_exon(start, end, gene_id, circRNA_id, chr, strand):
    artificial_exon = py.file_format.gtf.GTFitem()
    artificial_exon.set_start(int(start))
    artificial_exon.set_end(int(end))
    artificial_exon.set_gene_id(gene_id)
    artificial_exon.set_transcript_id(circRNA_id)
    artificial_exon.set_seqname(chr)
    artificial_exon.set_source("ciri")
    artificial_exon.set_feature("exon")
    artificial_exon.set_strand(strand)
    artificial_exon.set_frame(".")
    return artificial_exon


def transform_as_path_to_gtf(ciri_as_file_prefix, gtf_file):
    path_to_ciri_exon_file = _get_ciri_as_file_path_of_exon_list(ciri_as_file_prefix)
    isoform_file_path = _get_ciri_path_file_path(ciri_as_file_prefix)
    isoform_file_path = isoform_file_path if os.path.exists(isoform_file_path) else _get_ciri_log2_file_path(
        ciri_as_file_prefix)

    if not os.path.exists(isoform_file_path):
        raise FileNotFoundError("no enough information file .. make sure you are exporting all details of CIRI-AS")

    if not os.path.exists(path_to_ciri_exon_file):
        raise FileNotFoundError("no ciri-as result file as %s" % path_to_ciri_exon_file)

    gtf_entries_of_exon = _load_ciri_exons_from_exon_file_to_gtf_entries(path_to_ciri_exon_file)

    exons_circular = []
    circ_junction = ""
    count_isoform_same_junction = 0
    with open(isoform_file_path) as as_out:
        for line in as_out:
            if "->path" in line and "=>" in line:
                parts = line.strip().split("\t")
                circ_rna = parts[0].strip().split("->")[0]
                if not circ_rna == circ_junction:
                    circ_junction = circ_rna
                    count_isoform_same_junction = 0
                else:
                    count_isoform_same_junction += 1

                id_isoform_this_junction = "%s.%d" % (circ_junction, count_isoform_same_junction)

                exon_ranges = [x.strip().split("=>")[-1] for x in parts[1].strip().split(",") if x]

                for exon_range in exon_ranges:
                    unique_exon_id = "%s=>%s" % (circ_rna, exon_range)
                    exon_get = gtf_entries_of_exon.get(unique_exon_id, None)

                    if exon_get is not None:
                        exon_to_export = copy.copy(exon_get)

                        exon_to_export.set_transcript_id(id_isoform_this_junction)
                        exons_circular.append(str(exon_to_export))

    with open(gtf_file, "w") as output_gtf:
        output_gtf.write("\n".join(exons_circular))
