# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import py.body.cli_opts
import py.body.config
import py.bwa
import py.star


__doc__ = '''
'''
__author__ = 'zerodel'

available_tools = {
    "star": py.star,
    "bwa": py.bwa
}

ALIGNER_SECTION = "mapper"


def work(whole_config_content=None, aligner_name=None, ref_path=None, input_files=None):
    aligner = available_tools[aligner_name]

    setting_index = dict(whole_config_content[aligner.INDEX_SECTION])
    setting_align = dict(whole_config_content[aligner.ALIGN_SECTION])
    # get index
    index_path = aligner.get_index_path(_prepare_index(setting_index, aligner, ref_path))
    # do index
    align_result = _do_align(setting_align, aligner, index_path, input_files)

    return align_result


def _prepare_index(index_config, aligner, ref_path):
    index_config = py.body.cli_opts.chain_map(index_config,
                                              aligner.interpret_index_path(ref_path))

    return aligner.index(index_config)


def _do_align(align_config, aligner, aligner_ref, input_files):
    align_config = py.body.cli_opts.chain_map(align_config,
                                              aligner.interpret_index_path(aligner_ref),
                                              aligner.interpret_seq_files(input_files))

    return aligner.align(align_config)


def main(config_file):
    config_latter = py.body.config.config(config_file)
    align_name = config_latter[py.body.config.GLOBAL_SECTION][ALIGNER_SECTION]
    work(config_latter, align_name)


if __name__ == "__main__":
    par_parser = py.body.cli_opts.simple_arg_parser_only_config_option()
    par = par_parser.parse_args()
    main(par.config)
