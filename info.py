# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import py.body.default_values
import py.bwa
import py.ciri
import py.ciri_as
import py.knife
import py.rsem
import py.sailfish
import py.salmon
import py.star
import wf_profile_circRNA

__doc__ = '''
'''
__author__ = 'zerodel'

_tool_wrapper = {}
_tool_description = {}


def show_it(tool_name):
    try:
        wrapper_tool = _tool_wrapper[tool_name]
    except KeyError as e:
        print("no such tool as %s" % tool_name)
        raise e

    module_desc =  wrapper_tool.__doc__
    module_desc = "\n".join(["# %s" % line for line in module_desc.strip().split('\n')])
    print(module_desc)

    default_config = py.body.default_values.load_default_value()
    for checker in wrapper_tool.OPTION_CHECKERS:
        default_this_section = dict(default_config[checker.name]) if checker.name in default_config else {}
        checker.dict_opt = default_this_section
        print(checker)


def reveal():
    print("\nthis pipeline now has following wrappers, choose one to see more information \n")
    keys = sorted([k for k in _tool_description])
    for key in keys:
        if key in _tool_description:
            print("%s \t-\t %s " % (key, _tool_description[key]))

    print("\n")
    print(r""" you could use 'grep -v "^#\ " | grep -v "^$" to filter out the options and use it directly in your config file """)

def _add_tool(name, wrapper, description):
    _tool_wrapper[name] = wrapper
    _tool_description[name] = description


_add_tool("bwa", py.bwa, "BWA and BWA MEM ")
_add_tool("ciri", py.ciri, "CIRI : a circular RNA detection tool ")
_add_tool("ciri_as", py.ciri_as, "CIRI-AS: circular RNA Alternative Splicing Event detection tool")
_add_tool("knife", py.knife, "KNIFE: a circular RNA detection tool ")
_add_tool("rsem", py.rsem, "RSEM : a RNA seq quantification tool")
_add_tool("sailfish", py.sailfish, "Sailfish: a RNA-seq quantification tool based on k-mer")
_add_tool("salmon", py.salmon, "Salmon: a RNA-seq quantification tool based on fragment ")
_add_tool("star", py.star, "STAR : a junction sensitive aligner")
_add_tool("profile_circRNA", wf_profile_circRNA, "home made pipeline for profiling the circRNA ")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        reveal()
    else:
        show_it(sys.argv[-1])
