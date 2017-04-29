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

import pysrc.body.logger


__doc__ = ''' read .ini format config file,
'''

__author__ = 'zerodel'

SECTION_META = "META"
SECTION_GLOBAL = "GLOBAL"

__PATH_DEFAULT_CONFIG = "./default.cfg"

_logger = pysrc.body.logger.default_logger("CONFIG_OPERATION")


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


def load_or_update_option_section(cfg, your_section):
    section_user = None
    section_default = None

    if cfg:
        user_config = config(cfg)
        if your_section in user_config:
            section_user = dict(user_config[your_section])
    else:
        _logger.warning(
            "this section: {section} is empty in your configure file: {cfg_file}".format(
                section=your_section,
                cfg_file=cfg))

    default_config = load_default_value()
    if your_section in default_config:
        section_default = dict(default_config[your_section])

    if section_user and section_default:
        section_default.update(section_user)
        _logger.debug("section updated by user config: {}".format(your_section))
        return section_default
    else:
        if section_user:
            _logger.debug("using only user config: {}".format(your_section))
            return section_user
        elif section_default:
            _logger.debug("using only default config: {}".format(your_section))
            return section_default
        else:
            raise ValueError(
                "can not find this section :{},  in both default and user config files".format(your_section))


def throw_out_where_the_default_config_is():
    return get_default_config_file_path()


def get_default_config_file_path(file_temp=__PATH_DEFAULT_CONFIG):
    pwd = os.path.dirname(__file__)
    file_tmp = os.path.split(file_temp)[-1]
    return os.path.join(pwd, file_tmp)


def load_default_value(path_config_file=""):
    if not path_config_file:
        path_config_file = get_default_config_file_path(__PATH_DEFAULT_CONFIG)

    config_loaded = single_config(path_config_file)

    if SECTION_GLOBAL in config_loaded and SECTION_META in config_loaded:
        pass
    else:
        raise KeyError(
            "Error@loading_default_setting: must have 'META' and 'GLOBAL' section in {}".format(path_config_file))

    return config_loaded
