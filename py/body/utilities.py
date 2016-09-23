# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

__doc__ = ''' utilities
'''
__author__ = 'zerodel'


# a function copied from  http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

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


class Bunch(dict):
    def __int__(self, *args, **kwargs):
        super(Bunch, self).__init__(*args, **kwargs)
        self.__dict__ = self


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        pass