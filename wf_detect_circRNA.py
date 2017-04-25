# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import argparse

import pysrc.body.cli_opts
import pysrc.body.config
import pysrc.body.default_values
import pysrc.body.logger

import pysrc.wrapper.ciri_as
import pysrc.wrapper.bwa
import pysrc.wrapper.ciri
import pysrc.wrapper.knife

from pysrc.body.logger import set_logger_file

GLOBAL_KEY_NAME = "detector"

__TOOL_KNIFE = "knife"

__TOOL_CIRI_AS = "ciri_as"

__TOOL_CIRI = "ciri"  # todo : need a wrapper for CIRI 2

__TOOL_BWA = "bwa"

available_tools = {
    __TOOL_BWA: pysrc.wrapper.bwa,
    __TOOL_CIRI: pysrc.wrapper.ciri,
    __TOOL_CIRI_AS: pysrc.wrapper.ciri_as,
    __TOOL_KNIFE: pysrc.wrapper.knife
}

__doc__ = ''' top level interface of circRNA detection workflow.\n
association:  '{key_global}' in section [GLOBAL]\n
usable value : {usable_values}
'''.format(key_global=GLOBAL_KEY_NAME,
           usable_values=", ".join([x for x in available_tools]))

__author__ = 'zerodel'

WORK_FLOW_NAME = "workflow_circRNA_detection"

_logger = pysrc.body.logger.default_logger(WORK_FLOW_NAME)


def __cli_arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cfg_file", help="file path to a configuration file of detection job")
    parser.add_argument("-l", "--log_file", help="logging file path", default="")
    return parser


def main(cfg):
    _logger.info("circRNA Detecting starting")
    _logger.info("configure is a {} , and content is {}".format(type(cfg), str(cfg)))

    user_config = pysrc.body.config.config(cfg) if cfg else pysrc.body.default_values.load_default_value()

    detector_name = user_config[pysrc.body.config.SECTION_GLOBAL][GLOBAL_KEY_NAME]

    _logger.info("using %s as detector" % detector_name)

    _do_detect_circ(detector_name, user_config)


def _do_detect_circ(name_of_detector, user_config, seqs=""):
    if name_of_detector not in available_tools:
        raise KeyError("Error: no such circular RNA detection tool : {}".format(name_of_detector))

    detector = available_tools[name_of_detector]
    if detector.SECTION_DETECT not in user_config:
        raise KeyError(
            "Error@config file: no config part %s for detector %s" % (detector.SECTION_DETECT, name_of_detector))

    config_detector = dict(user_config[detector.SECTION_DETECT])

    _logger.info("content of detector is =====\n{}\n".format(str(config_detector)))

    detector.detect(config_detector)


if __name__ == "__main__":
    arg_parser = __cli_arg_parser()
    args = arg_parser.parse_args()
    _logger = set_logger_file(_logger, args.log_file)

    main(args.cfg_file)
