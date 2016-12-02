# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#


import py.body.logger
import py.file_format.ciri_entry
import py.file_format.gtf

__doc__ = '''
'''
__author__ = 'zerodel'

__COMMENT_CHAR = "#"

_logger = py.body.logger.default_logger("SUMMARIZE_QUANTIFICATION_OUTPUT")

STRING_NA = 'n/a'


class raw_region(object):
    def __init__(self, str_junction=""):
        if str_junction:
            self.raw_str = str_junction
            junction_str = str_junction.split(".")[0].strip()
            self.chr, self.start, self.end = self.split_junction(junction_str)
        else:
            self.chr, self.start, self.end, self.raw_str= "", None, None, ""


    def split_junction(self, junction_str):
        chr, junction_info = junction_str.strip().split(":")
        junction_start, junction_end = junction_info.strip().split("|")
        return chr, int(junction_start), int(junction_end)

    def __str__(self):
#        return "%s:%d|%d" % (self.chr, self.start, self.end)
        return self.raw_str

    def is_overlap_with(self, other):
        on_the_same_chrome = self.chr == other.chr
        has_overlap = (self.start - other.end) * (self.end - other.start) < 0
        return on_the_same_chrome and has_overlap


def _make_a_cluster(list_of_junction_objs):
    starts = min((j.start for j in list_of_junction_objs))
    ends = max((j.end for j in list_of_junction_objs))
    chr = list_of_junction_objs[0].chr

    region_id = "Region_%s:%d|%d" % (chr, starts, ends)
    junction_ids = [str(obj) for obj in list_of_junction_objs]
    return region_id, junction_ids


def _insert_current_cluster(cluster, dict_transcripts_of_gene):
    cluster_id, junctions_in_cluster = _make_a_cluster(cluster)
    _logger.debug("insert cluster %s : %s" % (cluster_id, ", ".join(junctions_in_cluster)))
    dict_transcripts_of_gene[cluster_id] = junctions_in_cluster


def _sort_junctions_by_chrome(na_junctions):
    chromes = {}
    for j_str in na_junctions:
        j = raw_region(j_str)
        chromes.setdefault(j.chr, set()).add(j)
    return chromes


def arrange_na_locus(dict_transcripts_of_gene):
    if STRING_NA in dict_transcripts_of_gene:
        na_junctions = dict_transcripts_of_gene.pop(STRING_NA)
        chromes = _sort_junctions_by_chrome(na_junctions)

        for chr in chromes:
            junction_this_chrome = sorted(chromes[chr], key=lambda x: x.start)
            cluster = []
            for obj_j in junction_this_chrome:
                if len(cluster) == 0:
                    cluster.append(obj_j)
                else:
                    last_obj = cluster[-1]
                    if last_obj.is_overlap_with(obj_j):
                        cluster.append(obj_j)
                    else:
                        _insert_current_cluster(cluster, dict_transcripts_of_gene)
                        cluster = [obj_j]
            _insert_current_cluster(cluster, dict_transcripts_of_gene)
    return dict_transcripts_of_gene


def _get_trans_gene_mapping(file_contains_info, func_to_parse_single_line, dict_transcripts_of_gene=None):
    if not dict_transcripts_of_gene or not isinstance(dict_transcripts_of_gene, dict):
        dict_transcripts_of_gene = {}

    _logger.debug("updating 'transcripts_under_gene' using %s" % file_contains_info)

    with open(file_contains_info) as parser_this_file:
        for single_line in parser_this_file:
            if not single_line.strip().startswith(__COMMENT_CHAR):
                gene_entry, transcript_entry = func_to_parse_single_line(single_line)
                dict_transcripts_of_gene.setdefault(gene_entry, set()).add(transcript_entry)

    return dict_transcripts_of_gene


def _parse_single_line_as_gtf(single_line):
    entry = py.file_format.gtf.GTFitem(single_line.strip())
    gene_id = entry.get_gene_id()
    transcript_id = entry.get_transcript_id()
    return gene_id, transcript_id


def _parse_single_line_ciri(line):
    ciri_this_line = py.file_format.ciri_entry.CIRIEntry(line.strip())
    gene_id = ciri_this_line.gene_id
    transcript_id = ciri_this_line.id
    return gene_id, transcript_id


def get_mapping_info_from_gtf(gtf_file, gene_as_key=None):
    return _get_trans_gene_mapping(gtf_file, _parse_single_line_as_gtf, gene_as_key)


def get_mapping_info_from_ciri(ciri_file, gene_as_key=None):
    return _get_trans_gene_mapping(ciri_file, _parse_single_line_ciri, gene_as_key)


def is_this_id_circular(id_this):
    return str(id_this).startswith("chr") or (":" in str(id_this) and "|" in str(id_this))


def load_quantify_report(quantify_report_file):
    with open(quantify_report_file) as get_quant:
        header_parts = get_quant.readline().strip().split("\t")
        index_name = header_parts.index("Name")
        index_tpm = header_parts.index("TPM")

        quant_dict = {}
        for quant_line in get_quant:
            line_parts = quant_line.strip().split("\t")
            id_this = line_parts[index_name]
            tpm_this = line_parts[index_tpm]
            quant_dict[id_this] = tpm_this

    return quant_dict


def summarize_linear_and_circular_on_gene_level(quantify_of_transcript_level, transcripts_of_gene):
    genes_all = []
    tpm_linear_of_gene = {}
    tpm_circular_of_gene = {}
    for gene_id, trans_under_this_gene in transcripts_of_gene.items():
        genes_all.append(gene_id)
        tpm_linear_of_gene[gene_id] = 0.0
        tpm_circular_of_gene[gene_id] = 0.0

        for id_transcript in trans_under_this_gene:
            tpm_this_transcript = float(quantify_of_transcript_level.get(id_transcript, 0))
            if is_this_id_circular(id_transcript):
                tpm_circular_of_gene[gene_id] += tpm_this_transcript
            else:
                tpm_linear_of_gene[gene_id] += tpm_this_transcript
    return genes_all, tpm_linear_of_gene, tpm_circular_of_gene


def export_gene_level_output(summary_quantify, genes_all, tpm_linear_of_gene, tpm_circular_of_gene):
    with open(summary_quantify, "w") as output_summary:
        output_summary.write("gene\tlinear\tcircular\n")
        for gene_id in genes_all:
            output_summary.write(
                "%s\t%s\t%s\n" % (gene_id, str(tpm_linear_of_gene[gene_id]), str(tpm_circular_of_gene[gene_id])))


def summarize_quantify(quant_sf, file_summary_quantify, gtf_this, ciri_output=""):
    transcripts_of_gene = {}

    transcripts_of_gene = get_mapping_info_from_gtf(gtf_this, transcripts_of_gene)

    _logger.debug("loading GTF is OK, %d gene in memory" % len(transcripts_of_gene))

    if ciri_output:
        transcripts_of_gene = get_mapping_info_from_ciri(ciri_output, transcripts_of_gene)
        _logger.debug("loading CIRI output is ok")

    quantify_of_transcript_level = load_quantify_report(quant_sf)

    genes_all, tpm_linear, tpm_circular = summarize_linear_and_circular_on_gene_level(quantify_of_transcript_level,
                                                                                      transcripts_of_gene)

    _logger.debug("dump those data to %s" % file_summary_quantify)

    export_gene_level_output(file_summary_quantify, genes_all, tpm_linear, tpm_circular)
