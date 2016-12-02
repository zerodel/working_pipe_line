# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import os.path
import sys

sys.path.append(os.path.dirname(__file__))
import py.body.config
import py.body.worker
import py.body.default_values
import py.align
from py import quantify, align

__doc__ = '''
'''
__author__ = 'zerodel'

_OPT_KEY_QUANTIFIER = "quantifier"

_OPT_KEY_MAPPER = "mapper"


def main(path_config=""):
    user_config_whole = py.body.config.config(
        path_config) if path_config else py.body.default_values.load_default_value()

    aligner_name = get_value_from_GLOBAL_section(user_config_whole, _OPT_KEY_MAPPER)
    quantifier = get_value_from_GLOBAL_section(user_config_whole, _OPT_KEY_QUANTIFIER)

    align.work(user_config_whole, aligner_name)
    quantify.work(user_config_whole, quantifier)


def get_value_from_GLOBAL_section(user_config_whole, key_name):
    if key_name in user_config_whole[py.body.config.SECTION_GLOBAL]:
        return user_config_whole[py.body.config.SECTION_GLOBAL][key_name]
    else:
        raise KeyError("Error@config_global_section: {} must be in GLOBAL section".format(key_name))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        main()
    else:
        main(sys.argv[-1])
