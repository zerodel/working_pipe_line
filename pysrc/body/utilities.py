# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import os

import pysrc.body.logger
from pysrc.file_format.fa import _logger

__doc__ = ''' utilities
'''
__author__ = 'zerodel'

_logger = pysrc.body.logger.default_logger("UTILITIES")


def is_num_like(x):
    try:
        float(x)
    except ValueError:
        return False
    else:
        return True


def is_ratio_like(x):
    if is_num_like(x):
        if abs(float(x)) <= 1:
            return True
    return False


# a function copied from  http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os

    def is_exe(path_file):
        return os.path.isfile(path_file) and os.access(path_file, os.X_OK)

    file_path, file_name = os.path.split(program)

    if file_path:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def check_binary_executable(program_bin):
    if not which(program_bin):
        raise FileNotFoundError("Error@checking_binary_exe: NO EXECUTABLE BINARY FILE AS {}".format(program_bin))


def core_numbers_of_cpu():
    try:
        import multiprocessing
    except ImportError as e:
        raise e

    return multiprocessing.cpu_count()


def is_thread_num_less_than_core_number(x):
    return int(x) <= core_numbers_of_cpu()


# todo : implement a real detect function, now we only assume sample is paired end
def is_paired(bam_file):
    # import pysam
    #
    # pysam.index(bam_file)
    #
    # bam_obj = pysam.AlignmentFile(bam_file)
    # nums = 0
    # for i in bam_obj.fetch():
    #     nums += 1
    #     if nums >=2:
    #         break
    #     read = i
    # bam_obj.close()
    # return read.is_paired()
    #
    return True


# a function from http://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta
# and I use a simplified version

def is_path_creatable(pathname: str) -> bool:
    """`True` if the current user has sufficient permissions to create the passed
    pathname; `False` otherwise.
    """
    # Parent directory of the passed path. If empty, we substitute the current
    # working directory (CWD) instead.
    dir_name = os.path.dirname(pathname) or os.getcwd()
    return os.access(dir_name, os.W_OK)


def is_path_exists_or_creatable(path_to_somewhere):

    try:
        return os.path.exists(path_to_somewhere) or is_path_creatable(path_to_somewhere)

    except OSError:
        return False


class Bunch(dict):
    def __int__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self


def do_merge_files(file_output, *args):
    with open(file_output, "a") as output_lines:
        for file_name in args:
            if file_name == file_output:
                _logger.info("seems this file will append itself: %s" % file_name)
            else:
                with open(file_name) as read1:
                    _logger.info("now adding file: {origin} -> {target} ".format(origin=file_name,
                                                                                  target=file_output))
                    line_count = 0
                    for line in read1:
                        output_lines.write("%s\n" % line.strip())
                        line_count += 1
                    _logger.info("finish adding {origin} -> {target}, lines:{line_num}".format(
                        origin=file_name,
                        target=file_output,
                        line_num=line_count))