# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os

__doc__ = '''
'''
__author__ = 'zerodel'


def _convert_naive_report(naive_report):
    res = []
    with open(naive_report) as nr:
        nr.readline()
        nr.readline()
        for line in nr:
            _process_line(line, res, _is_this_naive_bsj_positive)
    return res


def _safe_split_knife_report_file_line(line):
    return line.strip("\n").split("\t")


def _convert_glm_report(glm_report):
    res = []
    with open(glm_report) as nr:
        nr.readline()
        for line in nr:
            _process_line(line, res, _is_this_glm_bsj_positive)
    return res


def _process_line(line_in_file, processed_result_list, func_check_positive):
    parts = _safe_split_knife_report_file_line(line_in_file)
    if parts:
        if func_check_positive(parts):
            line_bed = _bsj_junction_to_bed(parts[0])
            if line_bed:
                processed_result_list.append(line_bed)
    else:

        pass


def _is_this_naive_bsj_positive(parts):
    try:
        r_circ, r_decoy, r_pv = parts[5], parts[6], parts[7]

    except Exception as e:

        raise e

    try:
        circ, decoy, pv = int(r_circ), int(r_decoy), float(r_pv)
    except ValueError:

        return False

    # this is from KNIFE github page
    return pv >= 0.9 and decoy < circ * 0.1


def _is_this_glm_bsj_positive(parts):
    pv = float(parts[2])
    return pv >= 0.9  # this is also from KNIFE github page


def _bsj_junction_to_bed(info_str):
    """junction: chr|gene1_symbol:splice_position|gene2_symbol:splice_position|junction_type|strand
        junction types are reg (linear),
        rev (circle formed from 2 or more exons),
        or dup (circle formed from single exon)
    """

    seq_name, gene_splice_1, gene_splice_2, junction_type, strand = info_str.strip().split("|")
    if junction_type == "reg":
        return None
    else:
        gene1, splice_1 = gene_splice_1.strip().split(":")
        gene2, splice_2 = gene_splice_2.strip().split(":")

        start_point = splice_1 if int(splice_1) < int(splice_2) else splice_2
        end_point = splice_2 if int(splice_1) < int(splice_2) else splice_1

        # name_bsj = "{chr}_{start}_{end}_{gene_from}_{gene_to}".format(chr=seq_name,
        #                                                               start=start_point,
        #                                                               end=end_point,
        #                                                               gene_from=gene1,
        #                                                               gene_to=gene2)

        name_bsj = info_str.strip()
        return "\t".join([seq_name, start_point, end_point, name_bsj, "0", strand])


def extract_bed_from_knife_report_path(output_bed_file_path, path_of_knife_result):
    report_path = os.path.join(path_of_knife_result, "circReads")
    naive_report_folder = os.path.join(report_path, "reports")
    annotated_junction_report_folder = os.path.join(report_path, "glmReports")

    all_bed_lines = []
    for report in os.listdir(naive_report_folder):
        all_bed_lines.extend(_convert_naive_report(os.path.join(naive_report_folder, report)))

    for report in os.listdir(annotated_junction_report_folder):
        all_bed_lines.extend(_convert_glm_report(os.path.join(annotated_junction_report_folder, report)))

    with open(output_bed_file_path, "w") as op:
        for line in all_bed_lines:
            op.write("{}\n".format(line.strip()))
