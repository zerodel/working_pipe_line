# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os
import os.path

import pysrc.body.config

__doc__ = '''
'''
__author__ = 'zerodel'

__PATH_DEFAULT_CONFIG = "./default.cfg"


def throw_out_where_the_default_config_is():
    return _get_default_config_file_path()


def _get_default_config_file_path(file_temp=__PATH_DEFAULT_CONFIG):
    pwd = os.path.dirname(__file__)
    file_tmp = os.path.split(file_temp)[-1]
    return os.path.join(pwd, file_tmp)


def load_default_value(path_config_file=""):
    if not path_config_file:
        path_config_file = _get_default_config_file_path(__PATH_DEFAULT_CONFIG)

    config_loaded = pysrc.body.config.single_config(path_config_file)

    if pysrc.body.config.SECTION_GLOBAL in config_loaded and pysrc.body.config.SECTION_META in config_loaded:
        pass
    else:
        raise KeyError(
            "Error@loading_default_setting: must have 'META' and 'GLOBAL' section in {}".format(path_config_file))

    return config_loaded


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass
