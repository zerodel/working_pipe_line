# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

__doc__ = ''' read .ini format config file ,
'''

__author__ = 'zerodel'

SECTION_META = "META"
SECTION_GLOBAL = "GLOBAL"


def _get_parser(is_case_sensitive=True, **kwargs):
    my_parser = configparser.ConfigParser(allow_no_value=True,
                                          interpolation=configparser.ExtendedInterpolation(), **kwargs)

    if is_case_sensitive:
        my_parser.optionxform = str
    return my_parser


def single_config(path_config="", **kwargs):
    my_parser = _get_parser(**kwargs)
    my_parser.read(path_config)
    return my_parser


def config(cfg, **kwargs):
    my_parser = _get_parser(**kwargs)
    if isinstance(cfg, str):
        if not os.path.exists(cfg):
            my_parser.read_string(cfg)
        else:
            my_parser.read(cfg)
    elif isinstance(cfg, list):
        if all([os.path.exists(x) for x in cfg]):
            my_parser.read(cfg)
        else:
            raise FileNotFoundError("Error: these config file : "
                                    + " ".join([x for x in cfg if not os.path.exists(x)])
                                    + "Not Found !")
    elif isinstance(cfg, dict):
        my_parser.read_dict(cfg)

    return my_parser


def cfg2dict(config_object):
    dd = {}
    for section in config_object:
        dd[section] = dict(config_object[section])
    return dd


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
