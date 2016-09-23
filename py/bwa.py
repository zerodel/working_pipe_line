# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import copy
import os
import os.path

import py.body.cli_opts
import py.body.utilities
import py.body.worker
from py.body.cli_opts import transform_input_general

_DESC_READS = "sequence reads files "

_DESC_BWA_INDEX = "path to genomic fasta database file for BWA indexing"

_DESC_BWA_IN_FASTA_INDEX = "genomic fasta database file for BWA indexing"

_DESC_BWA_BIN = "BWA binary file path"

__doc__ = '''
'''
__author__ = 'zerodel'

INDEX_SECTION = "BWA_INDEX"
ALIGN_SECTION = "BWA_ALIGN"

_SUFFIX_INDEX = [
    ".bwt",
    ".amb",
    ".ann",
    ".pac",
    ".sa",
]


def index(para_config=None, **kwargs):
    opts_of_index_phase_raw = py.body.cli_opts.merge_parameters(kwargs, para_config, INDEX_SECTION)

    opts_of_index_phase = copy.copy(opts_of_index_phase_raw)
    _option_check_index_phrase(opts_of_index_phase)

    dir_index = get_index_path(opts_of_index_phase)

    if not is_path_contain_index(dir_index):
        cmd_index = _get_cmd_index(opts_of_index_phase)
        py.body.worker.run(cmd_index)
    else:
        print("Report: already have a BWA index in {}".format(dir_index))

    return opts_of_index_phase_raw


def _option_check_index_phrase(opts_index):
    with py.body.cli_opts.OptionChecker(opts_index) as opt_check:
        opt_check.must_have("bwa_bin", py.body.utilities.which,
                            FileNotFoundError("Error: bwa binary not found"), _DESC_BWA_BIN)
        opt_check.must_have("in_fasta", os.path.exists,
                            FileNotFoundError("Error: no reference fasta file in {}".format(opts_index["in_fasta"])),
                            _DESC_BWA_IN_FASTA_INDEX)


def align(para_config=None, **kwargs):
    align_phrase_options_raw = py.body.cli_opts.merge_parameters(kwargs, para_config, ALIGN_SECTION)

    align_phrase_options = copy.copy(align_phrase_options_raw)
    _option_check_align_phrase(align_phrase_options)

    cmd, output = _get_cmd_align_with_target_file(align_phrase_options)

    if output:
        with open(output, "w") as alignment_file:
            bwa_cmd = py.body.worker.Cmd(cmd, target_file=alignment_file)
            bwa_cmd.run()
    else:
        bwa_cmd = py.body.worker.Cmd(cmd)
        bwa_cmd.run()

    return align_phrase_options_raw


def _option_check_align_phrase(opt_align):
    with py.body.cli_opts.OptionChecker(opt_align) as check_align_opts:
        check_align_opts.must_have("bwa_bin", py.body.utilities.which,
                                   FileNotFoundError("Error: bwa binary not found"), _DESC_BWA_BIN)

        check_align_opts.must_have("bwa_index", is_path_contain_index,
                                   FileNotFoundError("Error: no bwa index in {}".format(opt_align["bwa_index"])),
                                   _DESC_BWA_INDEX)

        check_align_opts.must_have("read_file", py.body.cli_opts.check_if_these_files_exist,
                                   FileNotFoundError(
                                       "Error: incorrect reads file provided for bwa : {}".format(opt_align["read_file"])),
                                   _DESC_READS)


def _get_cmd_align_with_target_file(opt_align):
    cmd_corp = "{bwa_bin} mem {align_options} {bwa_index} {read_file}"

    bwa_bin = opt_align.pop("bwa_bin")
    bwa_index = opt_align.pop("bwa_index")
    read_file = opt_align.pop("read_file")

    output = opt_align.pop("output") if "output" in opt_align else ""

    other_align_option = py.body.cli_opts.enum_all_opts(opt_align)

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
        paths = transform_input_general(input_files)
        return {"read_file": paths}
    else:
        return {}


def get_index_path(opts_dict):
    return opts_dict["prefix"]


def _get_cmd_index(opts_index):
    cmd_corp = "{bwa_bin} index {index_options} {in_fasta}"

    bwa_bin = opts_index.pop("bwa_bin")
    in_fasta = opts_index.pop("in_fasta")

    index_options = py.body.cli_opts.cat_options_no_replace(["-p", "-a"],
                                                            opts_index)

    cmd = cmd_corp.format(bwa_bin=bwa_bin,
                          index_options=index_options,
                          in_fasta=in_fasta)

    return cmd


def is_map_result_already_exists(align_file_path):
    return os.path.exists(align_file_path)


def get_align_result_path(para_config=None, **kwargs):
    align_phrase_options_raw = py.body.cli_opts.merge_parameters(kwargs, para_config, ALIGN_SECTION)
    cmd, output = _get_cmd_align_with_target_file(align_phrase_options_raw)

    return output

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
