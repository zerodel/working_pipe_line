# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import argparse

import py.wrapper.bwa
import py.wrapper.ciri
import py.wrapper.knife

import py.body.cli_opts
import py.body.config
import py.body.default_values
import py.body.logger
import py.wrapper.ciri_as


__doc__ = ''' top level interface of detecting circular isoform
'''
__author__ = 'zerodel'

available_tools = {
    "ciri_as": py.wrapper.ciri_as,
}

WORK_FLOW_NAME = "workflow_circRNA_isoform_detection"

_logger = py.body.logger.default_logger(WORK_FLOW_NAME)


_OPT_KEY_ISOFORM_DETECTOR = "isoform_detector"


def __cli_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_file", help="file path to a configuration file of isoform detection")
    parser.add_argument("-l", "--log_file", help="logging file path", default="")
    return parser


def main(cfg):
    _logger.debug("configure is a {} , and content is {}".format(type(cfg), str(cfg)))

    user_config = py.body.config.config(cfg) if cfg else py.body.default_values.load_default_value()

    detector_name = user_config[py.body.config.SECTION_GLOBAL][_OPT_KEY_ISOFORM_DETECTOR]

    _logger.debug("using %s as isoform detector " % detector_name)

    _do_detect_circular_isoform(detector_name, user_config)


def _do_detect_circular_isoform(name_of_detector, user_config):
    if name_of_detector not in available_tools:
        raise KeyError("Error: no such circular RNA detection tool : {}".format(name_of_detector))

    detector = available_tools[name_of_detector]
    if detector.SECTION_DETECT not in user_config:
        raise KeyError(
            "Error@config file: no config part %s for detector %s" % (detector.SECTION_DETECT, name_of_detector))

    config_detector = dict(user_config[detector.SECTION_DETECT])
    _logger.debug("content of detector is =====\n{}\n".format(str(config_detector)))

    detector.detect(config_detector)


if __name__ == "__main__":
    arg_parser = __cli_arg_parser()
    args = arg_parser.parse_args()
    _logger = py.body.logger.set_logger_file(_logger, args.log_file)
    main(args.cfg_file)
