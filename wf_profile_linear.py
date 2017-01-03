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

_QUANTIFIERS_DO_NOT_NEED_EXTERNAL_MAPPER = ["sailfish"]


def main(path_config=""):
    user_config_whole = py.body.config.config(
        path_config) if path_config else py.body.default_values.load_default_value()

    quantifier = get_value_from_GLOBAL_section(user_config_whole, _OPT_KEY_QUANTIFIER)

    if _is_this_quantifier_need_external_mapper(quantifier):
        align.work(user_config_whole, get_value_from_GLOBAL_section(user_config_whole, _OPT_KEY_MAPPER))

    quantify.work(user_config_whole, quantifier)


def _is_this_quantifier_need_external_mapper(name_quantifier):
    # now we simple assume that sailfish do not need external mapper
    return name_quantifier.strip() not in _QUANTIFIERS_DO_NOT_NEED_EXTERNAL_MAPPER


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
