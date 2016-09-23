# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#


import os.path
import sys

sys.path.append(os.path.dirname(__file__))


__doc__ = ''' this command will give you a copy of default configuration file at given path,
you can change it with your editor
'''
__author__ = 'zerodel'

import py.body.default_values


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:

        path_to_config_default = py.body.default_values._get_default_config_file_path()
        if not os.path.exists(path_to_config_default):
            raise FileNotFoundError("Error: unable to find default config file at {}".format(path_to_config_default))

        import shutil
        shutil.copy2(path_to_config_default, sys.argv[-1])