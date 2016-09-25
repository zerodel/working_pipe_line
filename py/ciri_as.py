# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import copy
import os
import os.path

import py.body.cli_opts
import py.body.option_check
import py.body.worker
import py.ciri
import py.body.logger

__doc__ = '''this is the wrapper of CIRI-AS
'''
__author__ = 'zerodel'

SECTION_DETECT = "CIRI_AS"

_ESSENTIAL_ARGUMENTS = ["--sam", "--ciri", "--out", ]

_logger = py.body.logger.default_logger(SECTION_DETECT)



def _check_opts(opts=None):
    opt_checker = py.body.option_check.OptionChecker(opts, name=SECTION_DETECT)
    opt_checker.must_have("--sam", os.path.exists,
                          FileNotFoundError(
                              "Error : unable to find CIRI-AS input sam file"),
                          "input sam file , should be the same as the CIRI used")

    opt_checker.must_have("--ciri", os.path.exists,
                          FileNotFoundError("Error : unable to find CIRI output file"),
                          "CIRI output file , should be the same version with CIRI AS")

    opt_checker.must_have("--out", py.body.cli_opts.is_suitable_path_with_prefix,
                          FileNotFoundError("Error: incorrect output file for CIRI-AS"),
                          "output file path for CIRI-AS")

    opt_checker.one_and_only_one(["--ref_dir", "--ref_file"], py.ciri.check_ref,
                                 FileNotFoundError("Error: unable to find ref-file for CIRI-AS"),
                                 "genomic reference file")

    opt_checker.forbid_these_args("--help", "-H")
    return opt_checker


opt_checker = _check_opts() # set up the opt_checker

def detect(whole_config=None, **kwargs):
    para_config = whole_config[SECTION_DETECT]
    opts_raw = py.body.cli_opts.merge_parameters(kwargs, para_config, SECTION_DETECT)

    _logger.debug("ciri-as args: %s" % str(opts_raw))

    opts = copy.copy(opts_raw)
    opt_checker.check(copy.copy(opts_raw))

    cmd_detect = _get_detect_cmd(opts)

    _logger.debug("ciri-as command is : %s" % cmd_detect)

    py.body.worker.run(cmd_detect)

    return opts_raw


def _get_detect_cmd(opts):
    cmd_as = "perl {ciri_as_path}".format(ciri_as_path=opts.pop("ciri_as_path"))
    cmd_as = " ".join([cmd_as, py.body.cli_opts.enum_all_opts(opts)])
    return cmd_as.strip()


def to_bed():
    pass


def interpret_seq_files():
    pass


if __name__ == "__main__":
    print(__doc__)
    print(opt_checker)