# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import copy
import os
import os.path

import py.body.cli_opts
import py.body.worker
import py.ciri
import py.body.logger

__doc__ = '''
'''
__author__ = 'zerodel'

DETECT_SECTION = "CIRI_AS"

_ESSENTIAL_ARGUMENTS = ["--sam", "--ciri", "--out", ]

_logger = py.body.logger.default_logger(DETECT_SECTION)


def detect(whole_config=None, **kwargs):
    para_config = whole_config[DETECT_SECTION]
    opts_raw = py.body.cli_opts.merge_parameters(kwargs, para_config, DETECT_SECTION)

    _logger.debug("ciri-as args: %s" % str(opts_raw))

    opts = copy.copy(opts_raw)
    _check_opts(opts)

    cmd_detect = _get_detect_cmd(opts)

    _logger.debug("ciri-as command is : %s" % cmd_detect)

    py.body.worker.run(cmd_detect)

    return opts_raw


def _check_opts(opts):
    with py.body.cli_opts.OptionChecker(opts) as opt_checker:
        opt_checker.must_have("--sam", os.path.exists,
                              FileNotFoundError(
                                  "Error : unable to find CIRI-AS input sam file: {--sam}".format(**opts)))

        opt_checker.must_have("--ciri", os.path.exists,
                              FileNotFoundError("Error : unable to find CIRI output file in : {--ciri}".format(**opts)))

        opt_checker.must_have("--out", py.body.cli_opts.is_suitable_path_with_prefix,
                              FileNotFoundError("Error: incorrect output file for CIRI-AS"))

        opt_checker.one_and_only_one(["--ref_dir", "--ref_file"], py.ciri.check_ref,
                                     FileNotFoundError("Error: unable to find ref-file for CIRI-AS"))

        opt_checker.forbid_these_args("--help", "-H")


def _get_detect_cmd(opts):
    cmd_as = "perl {ciri_as_path}".format(ciri_as_path=opts.pop("ciri_as_path"))
    cmd_as = " ".join([cmd_as, py.body.cli_opts.enum_all_opts(opts)])
    return cmd_as.strip()


def to_bed():
    pass


def interpret_seq_files():
    pass


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
