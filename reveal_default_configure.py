# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#


import os.path
import sys

sys.path.append(os.path.dirname(__file__))


__doc__ = ''' print out where the default config file is
'''
__author__ = 'zerodel'

import py.body.default_values


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(py.body.default_values._get_default_config_file_path())
    else:
        print(__doc__)