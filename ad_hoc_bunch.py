# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#

import os

import copy

import py.body.worker
import py.body.config
import py.body.cli_opts
import wf_detect_circRNA as work_flow
import py.body.default_values
import py.body.logger

__doc__ = ''' python ad_hoc_bunch.py result_folder_path sra_files_pat
'''
__author__ = 'zerodel'

# TODO: here, we assume all sra file are pair-end . how about single-end ?

own_cfg = {
    "CIRI": {
        #"-T": "10",
        "--in": "",
        "--seqs": "",
        "--out": "",
        "-P": None,
    },
    "GLOBAL": {
        "detector": "ciri",
    },
    "CIRC_PROFILE": {
        "quantifier": "salmon",
        #        "--annotation": "",
        #        "--genomic_seqs_fasta": "",
        "-o": "",
        "-k": "",
        #        "--mll": ""
    },
    "KNIFE": {
        "dataset_name": "knife",
        "read_directory": "",
        "alignment_parent_directory": ""
    }

}
#
# [GLOBAL]
# detector = knife
# [KNIFE]
# read_directory = /home/zerodel/zData/parts_blood/profile_sra/ERR335312/fq
# alignment_parent_directory = /home/zerodel/zData/parts_blood/profile_sra/ERR335312/detection_report
# dataset_name = knife


JOB_ID_SECTION = "jobs"
WORKING_PATH_SECTION = "working_path"

_logger = py.body.logger.default_logger("BUNCH_FOR_SRA")

def make_parameters_for_this_job(para_dict, job_id, tap_root):
    par = copy.copy(para_dict)
    abs_path_up_level = os.path.abspath(tap_root)

    def _put_it_under(x):
        return os.path.join(abs_path_up_level, x(job_id))

    par["CIRI"]["--in"] = os.path.join(_put_it_under(_bwa_sam_path), "pe.sam")
    par["CIRI"]["--out"] = os.path.join(_put_it_under(_detection_report_path), "ciri.out")

    path_to_fq_files = os.listdir(_put_it_under(_fq_path))
    fq1 = [f for f in path_to_fq_files if f.endswith("1.fastq") or f.endswith("1.fq")][0]
    fq2 = [f for f in path_to_fq_files if f.endswith("2.fastq") or f.endswith("2.fq")][0]

    par["CIRI"]["--seqs"] = " ".join([os.path.join(_put_it_under(_fq_path), fq1),
                                      os.path.join(_put_it_under(_fq_path), fq2)])

    par["CIRC_PROFILE"]["-o"] = _put_it_under(_quantify_result_path)
    par["CIRC_PROFILE"]["-k"] = 31

    par["KNIFE"]["read_directory"] = _put_it_under(_fq_path)
    par["KNIFE"]["alignment_parent_directory"] = _put_it_under(_detection_report_path)

    _logger.debug("paramters: %s" % str(par))

    return par


def main(tap_root, sra_root):
    sra_ids = get_sra_ids(sra_root)

    temp_dict = own_cfg

    for sra_id in sra_ids:

        _logger.debug("staring %s" % str(sra_id))

        prepare_sub_path_for(sra_id, tap_root)

        _logger.debug("extract sra %s ...." % sra_id)
        extract_fq(sra_id, tap_root, sra_root)

        para_this_job = make_parameters_for_this_job(temp_dict, sra_id, tap_root)

        _logger.debug("final parameter is : %s" % str(para_this_job))
        work_flow.main(para_this_job)


def get_sra_ids(sra_path):
    return [x.split(".")[0] for x in os.listdir(sra_path) if x.endswith(".sra")]


def _get_sra_file_path(sra, sra_root):
    return os.path.join(os.path.abspath(sra_root), sra + ".sra")


def extract_fq(sra_id, up_level_path, sra_root):
    fq_path = os.path.join(up_level_path, _fq_path(sra_id))
    sra_path = _get_sra_file_path(sra_id, sra_root)

    default_setting = py.body.default_values.load_default_value()
    fastq_dump_bin = default_setting["META"]["fastq_dump_bin"] if "fastq_dump_bin" in default_setting[
        "META"] else "fastq-dump"

    if not _is_paired_end_fq_extracted(sra_id, fq_path):
        py.body.worker.run("{fq_dump_bin} --split-3 {sra} -O {fq}".format(fq_dump_bin=fastq_dump_bin,
                                                                          sra=sra_path,
                                                                          fq=fq_path))


def _is_paired_end_fq_extracted(sra_id, path_fq):
    fqs = [f for f in os.listdir(path_fq) if f.endswith(".fq") or f.endswith(".fastq")]
    this_sra_fq = [f.strip().split(".")[0] for f in fqs if f.startswith(sra_id)]

    mate1ok = any([f.endswith("1") for f in this_sra_fq])
    mate2ok = any([f.endswith("2") for f in this_sra_fq])
    return mate1ok and mate2ok


def prepare_sub_path_for(job_id, up_level_path):
    abs_path_up_level = os.path.abspath(up_level_path)

    def prepare_folder(x):
        _make_it_exist(os.path.join(abs_path_up_level, x))

    prepare_folder(job_id)
    prepare_folder(_fq_path(job_id))
    prepare_folder(_bwa_sam_path(job_id))
    prepare_folder(_detection_report_path(job_id))
    prepare_folder(_quantify_result_path(job_id))


def _make_it_exist(path_to):
    if not os.path.exists(path_to):
        os.mkdir(path_to)


def _fq_path(sra):
    return os.path.join(sra, "fq")


def _bwa_sam_path(sra):
    return os.path.join(sra, "sam")


def _detection_report_path(sra):
    return os.path.join(sra, "detection_report")


def _quantify_result_path(sra):
    return os.path.join(sra, "quantify_result")


def get_sra_id_in_config(cfg):
    if py.body.config.GLOBAL_SECTION in cfg:
        job_ids = [x.strip() for x in cfg[py.body.config.GLOBAL_SECTION][JOB_ID_SECTION].strip().split(" ")
                   if x]
        return job_ids
    else:
        raise KeyError("Error@bunch_work: no GLOBAL section in configuration file")


def _get_tap_root_from_cfg(cfg):
    if py.body.config.GLOBAL_SECTION in cfg:

        part_global = cfg[py.body.config.GLOBAL_SECTION]
        if WORKING_PATH_SECTION in part_global:
            return part_global[WORKING_PATH_SECTION]
        else:
            raise KeyError("Error@'GLOBAL' in configure : WORKING_PATH not found ")
    else:
        raise KeyError("Error@ConfigureFIle: no 'GLOBAL' part in configure file. ")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
    else:
        main(sys.argv[-2], sys.argv[-1])
