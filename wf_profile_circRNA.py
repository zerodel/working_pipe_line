# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import sys
import os
import argparse

import py.body.default_values
import py.body.config
import py.body.cli_opts
import py.body.worker
import py.sailfish
import py.gffread
import py.bsj_gtf
import py.file_format.fa
import py.salmon
import py.body.logger

_CONFIG_VALUE_SAILFISH = "sailfish"

_CONFIG_KEY_QUANTIFIER = "quantifier"

__doc__ = '''
'''

__author__ = 'zerodel'

SEQ_SECTION = "CIRC_PROFILE"

_logger = py.body.logger.default_logger(SEQ_SECTION)


def _cli_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_file", help="file path to a configuration file of detection job")
    parser.add_argument("-l", "--log_file", help="logging file path", default="")
    return parser


def main(path_config):
    user_config = py.body.config.ini(path_config) if path_config else py.body.default_values.load_default_value()

    if SEQ_SECTION not in user_config:
        raise KeyError("ERROR@Config_file: should have a section with the name :{}".format(SEQ_SECTION))

    circ_profile_config = dict(user_config[SEQ_SECTION])

    default_profile = py.body.cli_opts.default_values.load_default_value()
    if SEQ_SECTION in default_profile:
        default_profile_config = dict(default_profile[SEQ_SECTION])
        default_profile_config.update(circ_profile_config)
        circ_profile_config = default_profile_config

    _logger.debug("profile config dict is : %s" % str(circ_profile_config))

    _option_check_main_interface(circ_profile_config)

    str_quantifier = circ_profile_config.pop(
        _CONFIG_KEY_QUANTIFIER) if _CONFIG_KEY_QUANTIFIER in circ_profile_config else (
        "%s" % _CONFIG_VALUE_SAILFISH)
    quantifier = py.sailfish if str_quantifier == _CONFIG_VALUE_SAILFISH else py.salmon

    _logger.debug("using %s as quantification backend" % str_quantifier)

    # dummy implement
    seq_extractor = py.gffread
    gtf_operator = py.bsj_gtf

    genomic_annotation = _catch_one(circ_profile_config, "-a", "--annotation")
    genome_fa = _catch_one(circ_profile_config, "-g", "--genomic_seqs_fasta")
    circ_detection_report = _catch_one(circ_profile_config, "-c", "--bed", "--ciri_bsj")

    output_path = _catch_one(circ_profile_config, "-o")

    spliced_linear_reference = os.path.join(output_path, "ref_linear.fa")
    circular_rna_gtf = os.path.join(output_path, "circ_only.gtf")
    circ_reference = os.path.join(output_path, "circ_only.fa")

    # 1st, extract the linear sequence
    seq_extractor.do_extract_classic_linear_transcript(gff=genomic_annotation,
                                                       fasta=genome_fa,
                                                       output=spliced_linear_reference)

    # 2nd, get the circular RNA gtf sequences
    gtf_operator.do_make_gtf_for_circular_prediction_greedy(circular_candidate_regions=circ_detection_report,
                                                            gff_db=genomic_annotation,
                                                            output_gtf_path_name=circular_rna_gtf)

    # 3rd, extracts circular RNA sequence
    seq_extractor.do_extract_circular_transcript(gff=circular_rna_gtf,
                                                 fasta=genome_fa,
                                                 output=circ_reference)

    # 4th, do operations on circular RNA reference .
    # add adapter
    if "-k" in circ_profile_config and circ_profile_config['-k']:
        k = int(circ_profile_config["-k"])
    else:
        k = 21

    py.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference,
                                                   fa_out=circ_reference,
                                                   convert_fun=py.file_format.fa.make_adapter(k))

    if "--mll" in circ_profile_config and circ_profile_config[{"--mll"}]:
        mean_library_length = int(circ_profile_config["--mll"])

        py.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference,
                                                       fa_out=circ_reference,
                                                       convert_fun=py.file_format.fa.pad_for_effective_length(
                                                           mean_library_length))

    # 5th , combined those two seq file

    final_refer = os.path.join(output_path, "final.fa")
    py.file_format.fa.do_combine_files(spliced_linear_reference,
                                       circ_reference,
                                       final_refer)

    # 6th , make index for quantifier

    path_to_quantifier_index = os.path.join(output_path, "index_final")

    index_parameters = {"--kmerSize": str(k),
                        "--transcripts": final_refer,
                        "--out": path_to_quantifier_index
                        } if quantifier is py.sailfish else {
        "--kmerLen": str(k),
        "--transcripts": final_refer,
        "--index": path_to_quantifier_index,
    }

    quantifier.index(para_config=index_parameters)

    # 7th , do quantification!
    path_to_quantify_result = os.path.join(output_path, "profile_result")
    if not os.path.exists(path_to_quantify_result):
        os.mkdir(path_to_quantify_result)

    opts_quantifier = dict()

    opts_quantifier["--index"] = path_to_quantifier_index
    if "-1" and "-2" in circ_profile_config:
        opts_quantifier["--mates1"] = circ_profile_config["-1"]
        opts_quantifier["--mates2"] = circ_profile_config["-2"]
        opts_quantifier["--libType"] = 'IU'
    elif "-r" in circ_profile_config:
        opts_quantifier["--unmatedReads"] = circ_profile_config["-r"]
        opts_quantifier["--libType"] = 'U'

    opts_quantifier["--output"] = path_to_quantify_result

    quantifier.quantify(para_config=opts_quantifier)


def _catch_one(opts_dict, *args):
    for arg in args:
        if arg in opts_dict:
            return opts_dict.get(arg)


def _option_check_main_interface(opts):
    with py.body.cli_opts.OptionChecker(opts) as oc:
        oc.one_and_only_one(["-g", "--genomic_seqs_fasta"], os.path.exists,
                            FileNotFoundError("Error@circular_RNA_profiling: incorrect genomic reference fa file"),
                            "path to genomic sequence fasta file")

        oc.one_and_only_one(["-a", "--annotation"], os.path.exists,
                            FileNotFoundError("Error@circular_RNA_profiling: incorrect genome annotation file"),
                            "path to gene annotation file, ie, .gtf or .gff files")

        oc.one_and_only_one(["-c", "--ciri_bsj", "--bed"], os.path.exists,
                            FileNotFoundError("Error@circular_RNA_profiling: can not find circular report file "),
                            "path to  circRNA detection report to specify circular RNA")

        oc.must_have("-o", os.path.exists,
                     FileNotFoundError("Error@circular_RNA_profiling: no place for output"),
                     "output folder that contains the index built by sailfish and quantification results")

        oc.may_need("--mll", lambda x: x.isdigit(),
                    TypeError("Error@circular_RNA_profiling: mean library length should be a integer"),
                    "mean library length, this option is to fix up the effective length.")

        oc.may_need("-k", lambda x: x.isdigit(),
                    TypeError("Error@circular_RNA_profiling: k in k mer should be integer"),
                    "k-mer size used by sailfish to built index. default is 21")

        oc.may_need("-1", os.path.exists,
                    FileNotFoundError("Error@circular_RNA_profiling: no mate1 input seq file"),
                    "path to raw pair-end reads, mate 1")
        oc.may_need("-2", os.path.exists,
                    FileNotFoundError("Error@circular_RNA_profiling: no mate2 input seq file"),
                    "path to raw pair-end reads, mate 2")
        oc.may_need("-r", os.path.exists,
                    FileNotFoundError("Error@circular_RNA_profiling: no single end sequence input file"),
                    "path to single-end raw sequencing reads file.")

        oc.forbid_these_args("-h", "--help")


if __name__ == "__main__":
    arg_parser = _cli_arg_parser()
    args = arg_parser.parse_args()
    _logger = py.body.logger._set_logger_file(_logger, args.log_file)
    main(args.cfg_file)