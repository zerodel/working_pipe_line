# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import argparse
import os

import py.body.logger
from py.body import default_values

__doc__ = '''
'''
__author__ = 'zerodel'

_module_logger = py.body.logger.default_logger("commandline_option")


def drop1(dict_para, key, template):
    return template.format(dict_para.pop(key))


def option_and_value(key, dict_para):
    if dict_para[key]:
        return "{} {}".format(key, dict_para[key])
    else:
        return key


def drop_key(key, dict_para):
    if dict_para[key]:
        return "{} {}".format(key, dict_para.pop(key))
    else:
        return key


def cat_options_no_replace(options, opts_value_dict):
    return " ".join([drop_key(key, opts_value_dict)
                     for key in options
                     if key in opts_value_dict])


def cat_options(options, opts_value_dict):
    return " ".join([option_and_value(key, opts_value_dict)
                    for key in options
                    if key in opts_value_dict])


def all_options(options):
    return " ".join([option_and_value(key, options) for key in options])


def enum_all_opts(opts_value_dict):
    return " ".join([option_and_value(key, opts_value_dict) for key in opts_value_dict])


def update_parameters(para_default, para_cli, para_conf):
    import copy
    tmp_para = copy.copy(para_default)
    tmp_para.update(para_cli)
    tmp_para.update(para_conf)
    return tmp_para




def merge_parameters(kwargs, para_config, config_section):
    load_setting = default_values.load_default_value()
    updated_para = dict(load_setting[config_section]) if config_section in load_setting else {}

    if para_config:
        updated_para = update_parameters(updated_para,
                                         para_config,
                                         kwargs)
    return updated_para


def chain_map(*args):
    result = {}
    for single_map in args:
        result.update(single_map)
    return result


def check_if_these_files_exist(filename_str):
    single_paths = [x for x in filename_str.split() if x]
    for fa in single_paths:
        if not os.path.exists(fa):
            return False
    return True


def is_suitable_path_with_prefix(path_prefix):
    raw_path, prefix = os.path.split(path_prefix)
    return os.path.exists(raw_path) and os.path.isdir(raw_path)


def transform_input_general(input_files):
    if isinstance(input_files, list):
        paths = " ".join(input_files)
    elif isinstance(input_files, str):
        paths = input_files
    else:
        raise TypeError("Error: only list and string are allowed in assign input_files")
    return paths


def simple_arg_parser_only_config_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help=("specify the config file for this align job"))

    return parser
