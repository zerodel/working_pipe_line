# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import os
import os.path
import copy
import re
import logging


import py.body.worker
import py.body.cli_opts
import py.file_format.fq
import py.body.utilities
import py.body.logger

_OPT_BASH_BIN = "bash_bin"

_OPT_KNIFE_SCRIPT = "knife_script"

_OPT_INDEX_PATH = "index_path"

_OPT_JUNCTION_OVERLAP = "junction_overlap"

_OPT_DATA_SET_NAME = "dataset_name"

_OPT_ALIGNMENT_PARENT_DIRECTORY = "alignment_parent_directory"

_OPT_READ_ID_STYLE = "read_id_style"

_OPT_READ_DIRECTORY = "read_directory"

_READ_ID_STYLE_SINGE_END_OR_IDENTICAL = "complete"

_READ_ID_STYLE_PAIRED_END_UN_EQUAL = "appended"

__doc__ = ''' this is a wrapper for KNIFE(Known and Novel IsoForm Explorer)
'''
__author__ = 'zerodel'

DETECT_SECTION = "KNIFE"


_logger = py.body.logger.default_logger(DETECT_SECTION)



def detect(par_dict=None, **kwargs):
    opts_of_index_phase_raw = py.body.cli_opts.merge_parameters(kwargs, par_dict, DETECT_SECTION)
    opts = copy.copy(opts_of_index_phase_raw)

    opts = _predict_id_style_and_overlap_length(opts)

    _check_opts(opts)

    cmd_detect = _get_detect_cmd(opts)

    py.body.worker.run(cmd_detect)
    return opts_of_index_phase_raw


def _check_opts(opts):
    temp_error = "Error@KNIFE: %s"
    with py.body.cli_opts.OptionChecker(opts) as opt_check:
        opt_check.must_have(_OPT_BASH_BIN, py.body.utilities.which,
                            FileNotFoundError(temp_error % "bash binary not found"),
                            "abs path to bash binary")

        opt_check.must_have(_OPT_KNIFE_SCRIPT, os.path.exists,
                            FileNotFoundError(temp_error % "incorrect KNIFE script path given "),
                            "knife_script: absolute path to KNIFE executive script")

        opt_check.must_have(_OPT_READ_DIRECTORY, _check_valid_read_directory,
                            FileNotFoundError(temp_error % "incorrect read_directory"),
                            """absolute path to directory containing fastq files for alignment. Paired-end reads (PE) must have read1 and read2 in separate files.""")

        opt_check.may_need(_OPT_READ_ID_STYLE, lambda x: x.strip() in ["appended", "complete"],
                           KeyError(temp_error % "incorrect read_id_type given"),
                           """read_id_style, complete|appended (use complete for single end).""")

        opt_check.must_have(_OPT_ALIGNMENT_PARENT_DIRECTORY, _is_this_folder_existing,
                            NotADirectoryError(temp_error % "must have a directory for all result "),
                            """alignment_parent_directory: absolute path to directory where the dataset analysis output and log files will be stored. This directory must already exist, and a directory named dataset_name (see below) will be created under this directory for all output files.""")

        opt_check.must_have(_OPT_DATA_SET_NAME, lambda x: True,
                            NotADirectoryError(temp_error % "incorrect dataset_name given"),
                            """string identifier for this dataset. A folder of this name will be created under alignment_parent_directory (see above) and all output for this run will be stored in this directory.""")

        opt_check.must_have(_OPT_JUNCTION_OVERLAP, lambda x: x.isdecimal(),
                            KeyError(temp_error % "junction_overlap should be a integer"),
                            """minimum number of bases in the read which must be on each side of the junction to consider that the read is overlapping the junction. Values that have empirically worked well are 8 for paired-end (PE) reads of length < 70, 13 for longer PE, and 10 for single-end (SE) reads of length < 70, 15 for longer SE reads.""")

        opt_check.may_need(_OPT_INDEX_PATH, _is_this_folder_existing,
                           NotADirectoryError(temp_error % "incorrect KNIFE pre-fabricated index path"),
                           """index_path: a path to KNIFE index directory. """)


def _is_this_folder_existing(x):
    return os.path.exists(x) and os.path.isdir(x)


def _check_valid_read_directory(some_path):
    if os.path.exists(some_path) and os.path.isdir(some_path):
        def is_fq(x):
            f_name, f_suffix = os.path.splitext(x)
            if f_name and f_suffix and f_suffix in [".fastq", ".fq.gz", "fq"]:
                return True
            else:
                return False

        files = os.listdir(some_path)
        fqs = [f for f in files if is_fq(f)]

        base_names = [os.path.splitext(f)[0] for f in fqs]
        samples = set([base_name[:-1] for base_name in base_names])
        if samples:
            at_least_a_pair = False
            for sample in samples:
                sample1 = "%s1" % sample
                sample2 = "%s2" % sample
                if (sample1 in base_names) != (sample2 in base_names):
                    return False
                if (sample1 in base_names) and (sample2 in base_names):
                    at_least_a_pair = True
            else:
                return at_least_a_pair

    return False


def _get_detect_cmd(para_dict):
    opts = copy.copy(para_dict)

    priority_order = [_OPT_BASH_BIN, _OPT_KNIFE_SCRIPT, _OPT_READ_DIRECTORY, _OPT_READ_ID_STYLE,
                      _OPT_ALIGNMENT_PARENT_DIRECTORY,
                      _OPT_DATA_SET_NAME, _OPT_JUNCTION_OVERLAP, _OPT_INDEX_PATH]

    command_string_must_have = " ".join([opts.pop(key, "") for key in priority_order])
    command_latter_part = " ".join([opts[key] for key in opts])

    if command_latter_part:
        command_string_must_have = command_string_must_have + " " + command_latter_part

    return command_string_must_have


def _predict_id_style_and_overlap_length(opts):
    directory_fqs = opts[_OPT_READ_DIRECTORY]
    files_in_reads_folder = os.listdir(directory_fqs)
    mate1, mate2 = _get_mate_files(files_in_reads_folder)

    mate1 = os.path.join(directory_fqs, mate1) if mate1 else ""
    mate2 = os.path.join(directory_fqs, mate2) if mate2 else ""

    opts[_OPT_READ_ID_STYLE] = _predict_reads_id_type_for_fq_files(mate1, mate2)
    opts[_OPT_JUNCTION_OVERLAP] = _pick_suitable_overlap(mate1, mate2)

    return opts


def _pick_suitable_overlap(mate1, mate2):
    if not mate1:
        raise FileNotFoundError("Error@picking_suitable_overlap_parameter: seems not fastq file")
    is_single_end = not mate2
    read_length = py.file_format.fq.get_read_length(mate1)
    threshold_length_read = 70
    if is_single_end:
        overlap_len = 10 if read_length < threshold_length_read else 15
    else:
        overlap_len = 8 if read_length < threshold_length_read else 13

    return str(overlap_len)


def _predict_reads_id_type_for_fq_files(mate1, mate2):
    if (not mate2) or py.file_format.fq.is_pair_end_fastq_id_identical(mate1, mate2):
        return _READ_ID_STYLE_SINGE_END_OR_IDENTICAL
    else:
        return _READ_ID_STYLE_PAIRED_END_UN_EQUAL


def _get_mate_files(files_in_reads_folder):
    _PATTERN_SAMPLE = ".*(?=[-_]?[12]\.f.{0,5}q$)"
    sample_reo = re.compile(_PATTERN_SAMPLE)
    fqs_samples = [sample_reo.findall(x) for x in files_in_reads_folder if sample_reo.match(x)]
    samples_id = list(set([fq[0] for fq in fqs_samples if fq[0]]))
    # here we only support one-sample-one-folder
    if len(samples_id) < 1:
        raise FileNotFoundError("Error@predict_fq_read_id_type: seems you do not have fastq files")
    if len(samples_id) > 1:
        raise FileExistsError("Error@predict_fq_read_id_type: multiple sample in a single folder is not supported ")
    ss_id = samples_id[0]
    pattern_mate1_this_sample = "%s[-_]?1\.f.{1,5}$" % ss_id
    pattern_mate2_this_sample = "%s[-_]?2\.f.{1,5}$" % ss_id
    mate1 = [x for x in files_in_reads_folder if re.findall(pattern_mate1_this_sample, x)]
    mate2 = [x for x in files_in_reads_folder if re.findall(pattern_mate2_this_sample, x)]

    mate1_f = mate1[0] if mate1 else ""
    mate2_f = mate2[0] if mate2 else ""

    if not (mate1_f or mate2_f):
        raise FileNotFoundError("Error@finding mate files : seems no mate file ....")

    return mate1_f, mate2_f


def to_bed(knife_opts_dict, output_bed_file_path, gene_mapping_file=""):
    # use combined-report as primary source
    path_of_knife_result = os.path.join(knife_opts_dict[_OPT_ALIGNMENT_PARENT_DIRECTORY],
                                        knife_opts_dict[_OPT_DATA_SET_NAME])

    extract_bed_from_knife_report_path(output_bed_file_path, path_of_knife_result)


def extract_bed_from_knife_report_path(output_bed_file_path, path_of_knife_result):
    report_path = os.path.join(path_of_knife_result, "circReads")
    naive_report_folder = os.path.join(report_path, "reports")
    annotated_junction_report_folder = os.path.join(report_path, "glmReports")

    _logger.debug("naive report path: %s" % naive_report_folder)
    _logger.debug("glm report path : %s" % annotated_junction_report_folder)

    all_bed_lines = []
    for report in os.listdir(naive_report_folder):
        all_bed_lines.extend(_convert_naive_report(os.path.join(naive_report_folder, report)))

    for report in os.listdir(annotated_junction_report_folder):
        all_bed_lines.extend(_convert_glm_report(os.path.join(annotated_junction_report_folder, report)))

    with open(output_bed_file_path, "w") as op:
        for line in all_bed_lines:
            op.write("{}\n".format(line.strip()))


def _convert_naive_report(naive_report):

    _logger.debug("converting naive report : %s" % naive_report)

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

    _logger.debug("converting glm report : %s" % glm_report)
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
        _logger.debug("an empty line...")


def _is_this_naive_bsj_positive(parts):
    try:
        r_circ, r_decoy, r_pv = parts[5], parts[6], parts[7]

    except Exception as e:
        _logger.error(str(parts))
        raise e

    try:
        circ, decoy, pv = int(r_circ), int(r_decoy), float(r_pv)
    except ValueError:
        _logger.log(0, "meet a - at %s" % "\t".join(parts))
        return False

    # this is from KNIFE github page
    return pv >= 0.9 and decoy < circ * 0.1


def _is_this_glm_bsj_positive(parts):
    pv = float(parts[2])
    return pv >= 0.9    # this is also from KNIFE github page


def _bsj_junction_to_bed(info_str):
    """junction: chr|gene1_symbol:splice_position|gene2_symbol:splice_position|junction_type|strand
        junction types are reg (linear), rev (circle formed from 2 or more exons), or dup (circle formed from single exon)
    """

    seq_name, gene_splice_1, gene_splice_2, junction_type, strand = info_str.split("|")
    if junction_type == "reg":
        return None
    else:
        gene1, splice_1 = gene_splice_1.strip().split(":")
        gene2, splice_2 = gene_splice_2.strip().split(":")

        start_point = splice_1 if int(splice_1) < int(splice_2) else splice_2
        end_point = splice_2 if int(splice_1) < int(splice_2) else splice_1

        name_bsj = "{chr}_{start}_{end}_{gene_from}_{gene_to}".format(chr=seq_name,
                                                                      start=start_point,
                                                                      end=end_point,
                                                                      gene_from=gene1,
                                                                      gene_to=gene2)

        return "\t".join([seq_name, start_point, end_point, name_bsj, "0", strand])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
