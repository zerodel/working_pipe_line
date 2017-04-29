# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import copy
import os
import os.path

import pysrc.body.cli_opts
import pysrc.body.option_check
import pysrc.body.utilities
import pysrc.body.worker


__doc__ = ''' this is the wrapper of BWA aligner , it contains two phase: 1. index 2. align
'''
__author__ = 'zerodel'

# # begin of helper functions and misc variables and constants

_DESC_READS = "sequence reads files "

_DESC_BWA_INDEX = "path to genomic fasta database file for BWA indexing"

_DESC_BWA_IN_FASTA_INDEX = "genomic fasta database file for BWA indexing"

_DESC_BWA_BIN = "BWA binary file path"

_SUFFIX_INDEX = [
    ".bwt",
    ".amb",
    ".ann",
    ".pac",
    ".sa",
]


def _get_cmd_align_with_target_file(opt_align):
    cmd_corp = "{bwa_bin} mem {align_options} {bwa_index} {read_file}"

    bwa_bin = opt_align.pop("bwa_bin")
    bwa_index = opt_align.pop("bwa_index")
    read_file = opt_align.pop("read_file")

    output = opt_align.pop("output") if "output" in opt_align else ""

    other_align_option = pysrc.body.cli_opts.enum_all_opts(opt_align)

    cmd = cmd_corp.format(bwa_bin=bwa_bin,
                          align_options=other_align_option,
                          bwa_index=bwa_index,
                          read_file=read_file,
                          )

    return cmd, output


def is_path_contain_index(prefix_reference):
    files = [prefix_reference + suffix for suffix in _SUFFIX_INDEX]
    return all([os.path.exists(refer_file) for refer_file in files])


def interpret_index_path(given_index_path_prefix):
    if given_index_path_prefix:
        return {"in_fasta": given_index_path_prefix}
    else:
        return {}


def interpret_seq_files(input_files):
    if input_files:
        paths = pysrc.body.cli_opts.transform_input_general(input_files)
        return {"read_file": paths}
    else:
        return {}


def get_index_path(opts_dict):
    return opts_dict["prefix"]


def _get_cmd_index(opts_index):
    cmd_corp = "{bwa_bin} index {index_options} {in_fasta}"

    bwa_bin = opts_index.pop("bwa_bin")
    in_fasta = opts_index.pop("in_fasta")

    index_options = pysrc.body.cli_opts.cat_options_no_replace(["-p", "-a"],
                                                               opts_index)

    cmd = cmd_corp.format(bwa_bin=bwa_bin,
                          index_options=index_options,
                          in_fasta=in_fasta)

    return cmd


def is_map_result_already_exists(align_file_path):
    return os.path.exists(align_file_path)


def get_align_result_path(para_config=None, **kwargs):
    align_phrase_options_raw = pysrc.body.cli_opts.merge_parameters(kwargs, para_config, SECTION_ALIGN)
    cmd, output = _get_cmd_align_with_target_file(align_phrase_options_raw)

    return output


# # end of helper functions  #########


SECTION_INDEX = "BWA_INDEX"
SECTION_ALIGN = "BWA_ALIGN"


def _option_check_align_phrase(opt_align=None):
    check_align_opts = pysrc.body.option_check.OptionChecker(opt_align, name=SECTION_ALIGN)
    check_align_opts.must_have("bwa_bin", pysrc.body.utilities.which,
                               FileNotFoundError("Error: bwa binary not found"), _DESC_BWA_BIN)

    check_align_opts.must_have("bwa_index", is_path_contain_index,
                               FileNotFoundError("Error: incorrect bwa index "),
                               _DESC_BWA_INDEX)

    check_align_opts.must_have("read_file", pysrc.body.cli_opts.check_if_these_files_exist,
                               FileNotFoundError(
                                   "Error: incorrect reads file provided for bwa"),
                               _DESC_READS)
    return check_align_opts


def _option_check_index_phrase(opts_index=None):
    opt_check = pysrc.body.option_check.OptionChecker(opts_index, name=SECTION_INDEX)
    opt_check.must_have("bwa_bin", pysrc.body.utilities.which,
                        FileNotFoundError("Error: bwa binary not found"), _DESC_BWA_BIN)
    opt_check.must_have("in_fasta", os.path.exists,
                        FileNotFoundError("Error: no reference fasta files"),
                        _DESC_BWA_IN_FASTA_INDEX)
    return opt_check


opt_checker_index = _option_check_index_phrase()
opt_checker_align = _option_check_align_phrase()

OPTION_CHECKERS = [opt_checker_index, opt_checker_align]


def index(para_config=None, **kwargs):
    opts_of_index_phase_raw = pysrc.body.cli_opts.merge_parameters(kwargs, para_config, SECTION_INDEX)

    opts_of_index_phase = copy.copy(opts_of_index_phase_raw)
    # _option_check_index_phrase(opts_of_index_phase).check()

    opt_checker_index.check(opts_of_index_phase)

    dir_index = get_index_path(opts_of_index_phase)

    if not is_path_contain_index(dir_index):
        cmd_index = _get_cmd_index(opts_of_index_phase)
        pysrc.body.worker.run(cmd_index)
    else:
        print("Report: already have a BWA index in {}".format(dir_index))

    return opts_of_index_phase_raw


def align(para_config=None, **kwargs):
    align_phrase_options_raw = pysrc.body.cli_opts.merge_parameters(kwargs, para_config, SECTION_ALIGN)

    align_phrase_options = copy.copy(align_phrase_options_raw)
    # _option_check_align_phrase(align_phrase_options)
    opt_checker_align.check(align_phrase_options)

    cmd, output = _get_cmd_align_with_target_file(align_phrase_options)

    if output:
        with open(output, "w") as alignment_file:
            bwa_cmd = pysrc.body.worker.Cmd(cmd, target_file=alignment_file)
            bwa_cmd.run()
    else:
        bwa_cmd = pysrc.body.worker.Cmd(cmd)
        bwa_cmd.run()

    return align_phrase_options_raw


if __name__ == "__main__":
    print(__doc__)
    print(opt_checker_index)
    print(opt_checker_align)
