# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import argparse
import copy
import os
import shutil


import py.body.cli_opts
import py.body.config
import py.body.default_values
import py.body.logger
import py.body.option_check
import py.body.worker
import py.file_format.bsj_gtf
import py.file_format.ciri_as_to_gtf
import py.file_format.ciri_entry
import py.file_format.fa
import py.summary_quant
import py.wrapper.sailfish
import py.wrapper.salmon
import py.wrapper.gffread

_OPT_CIRI_AS_OUTPUT_PREFIX = "--ciri_as_prefix"

_OPT_VALUE_SAILFISH = "sailfish"

_OPT_KEY_QUANTIFIER = "quantifier"

_QUANTIFIER_BACKEND_OF = {"sailfish": py.wrapper.sailfish,
                          "salmon": py.wrapper.salmon}

__doc__ = '''
'''

__author__ = 'zerodel'

SECTION_PROFILE_CIRCULAR_RNA = "CIRC_PROFILE"

_logger = py.body.logger.default_logger(SECTION_PROFILE_CIRCULAR_RNA)


def __cli_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_file", help="file path to a configuration file of detection job")
    parser.add_argument("-l", "--log_file", help="logging file path", default="")
    parser.add_argument("-f", "--force", help="forced refresh", action="store_true")
    return parser


def _option_check_main_interface(opts=None):
    oc = py.body.option_check.OptionChecker(opts, name=SECTION_PROFILE_CIRCULAR_RNA)

    oc.must_have(_OPT_KEY_QUANTIFIER, lambda x: x in ["sailfish", "salmon"],
                 KeyError("Error@circular_RNA_profiling: incorrect quantifier back-end"),
                 "the back end quantifier: sailfish or salmon")

    oc.one_and_only_one(["-g", "--genomic_seqs_fasta"], os.path.exists,
                        FileNotFoundError("Error@circular_RNA_profiling: incorrect genomic reference fa file"),
                        "path to genomic sequence fasta file")

    oc.one_and_only_one(["-a", "--annotation"], os.path.exists,
                        FileNotFoundError("Error@circular_RNA_profiling: incorrect genome annotation file"),
                        "path to gene annotation file, ie, .gtf or .gff files")

    oc.one_and_only_one(["-c", "--ciri_bsj", "--bed"], os.path.exists,
                        FileNotFoundError("Error@circular_RNA_profiling: can not find circular report file "),
                        "path to  circRNA detection report to specify circular RNA")

    oc.may_need(_OPT_CIRI_AS_OUTPUT_PREFIX, py.body.cli_opts.is_suitable_path_with_prefix,
                FileNotFoundError("Error@circular_RNA_profiling: incorrect circular Alternative Splice file prefix"),
                "path prefix to CIRI-AS report of circular exons")

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
    return oc


option_checker = _option_check_main_interface()
OPTION_CHECKERS = [option_checker]

# dummy implement
_seq_extractor = py.wrapper.gffread
_gtf_operator = py.file_format.bsj_gtf


def main(path_config, forced_refresh=False):
    circ_profile_config = _load_to_update_default_options(path_config)

    _logger.debug("profile config dict is : %s" % str(circ_profile_config))

    option_checker.check(copy.copy(circ_profile_config))  # check your options

    quantifier = _confirm_quantifier(circ_profile_config)

    genomic_annotation = _catch_one(circ_profile_config, "-a", "--annotation")
    genome_fa = _catch_one(circ_profile_config, "-g", "--genomic_seqs_fasta")
    circ_detection_report = _catch_one(circ_profile_config, "-c", "--bed", "--ciri_bsj")

    output_path = _catch_one(circ_profile_config, "-o")

    spliced_linear_reference = os.path.join(output_path, "ref_linear.fa")
    circular_rna_gtf = os.path.join(output_path, "circ_only.gtf")
    circ_reference = os.path.join(output_path, "circ_only.fa")

    if "-k" in circ_profile_config and circ_profile_config['-k']:
        k = int(circ_profile_config["-k"])
    else:
        k = 21

    # 1st, extract the linear sequence
    if not os.path.exists(spliced_linear_reference) or forced_refresh:
        _prepare_linear_transcriptome(genome_fa, genomic_annotation, spliced_linear_reference)

    # 2nd, get the circular RNA gtf sequences

    if not os.path.exists(circular_rna_gtf) or forced_refresh:
        _prepare_circular_rna_annotation(circ_detection_report, circ_profile_config, circular_rna_gtf,
                                         genomic_annotation)

    # 3rd, extracts circular RNA sequence
    _seq_extractor.do_extract_circular_transcript(gff=circular_rna_gtf,
                                                  fasta=genome_fa,
                                                  output=circ_reference)

    # 4th, do operations on circular RNA reference .
    # add adapter
    py.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference,
                                                   fa_out=circ_reference,
                                                   convert_fun=py.file_format.fa.make_adapter(k))

    if "--mll" in circ_profile_config and circ_profile_config[{"--mll"}]:
        mean_library_length = int(circ_profile_config["--mll"])

        py.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference,
                                                       fa_out=circ_reference,
                                                       convert_fun=py.file_format.fa.pad_for_effective_length(
                                                           mean_library_length))

    # 5th , combined those two fasta file

    final_refer = os.path.join(output_path, "final.fa")
    py.file_format.fa.do_combine_files(spliced_linear_reference,
                                       circ_reference,
                                       final_refer)

    # 6th , make index for quantifier

    path_to_quantifier_index = os.path.join(output_path, "index_final")

    index_parameters = {"--kmerSize": str(k),
                        "--transcripts": final_refer,
                        "--out": path_to_quantifier_index
                        } if quantifier is py.wrapper.sailfish else {
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

    _summarize_quant_to_gene_level(genomic_annotation=genomic_annotation, circular_gtf=circular_rna_gtf,
                                   transcript_level_quant=os.path.join(path_to_quantify_result, "quant.sf"),
                                   gene_level_target_path=os.path.join(path_to_quantify_result, "summarized.quant"))


def _summarize_quant_to_gene_level(genomic_annotation, circular_gtf, transcript_level_quant, gene_level_target_path):
    transcript_of_gene = py.summary_quant.get_mapping_info_from_gtf(circular_gtf,
                                                                    py.summary_quant.get_mapping_info_from_gtf(
                                                                        genomic_annotation))

    transcript_of_gene = py.summary_quant.arrange_na_locus(transcript_of_gene)

    quant_transcript_level = py.summary_quant.load_quantify_report(transcript_level_quant)

    genes, tpm_linear, tpm_circular = py.summary_quant.summarize_linear_and_circular_on_gene_level(
        quant_transcript_level, transcript_of_gene)

    py.summary_quant.export_gene_level_output(gene_level_target_path, genes, tpm_linear, tpm_circular)


def _prepare_circular_rna_annotation(circ_detection_report, circ_profile_config, circular_rna_gtf, genomic_annotation):
    folder_gtf, gtf_base_name = os.path.split(circular_rna_gtf)

    if _OPT_CIRI_AS_OUTPUT_PREFIX in circ_profile_config:
        circ_as_file_prefix = _catch_one(circ_profile_config, _OPT_CIRI_AS_OUTPUT_PREFIX)
        isoform_gtf = os.path.join(folder_gtf, "isoform_" + gtf_base_name)
        bsj_has_isoform = py.file_format.ciri_as_to_gtf.transform_as_path_to_gtf_and_return_bsj_junctions(
            circ_as_file_prefix, isoform_gtf)

        bed_this = os.path.join(folder_gtf, "detection_raw.bed")

        if not circ_detection_report.endswith(".bed"):
            py.file_format.ciri_entry.transform_ciri_to_bed(circ_detection_report, bed_this)
        else:
            shutil.copy(circ_detection_report, bed_this)

        bed_filtered = os.path.join(folder_gtf, "ambiguous.bed")
        with open(bed_filtered, "w") as to_bed:
            with open(bed_this) as from_bed:
                for line in from_bed:
                    id_this_line = line.strip().split("\t")[3].strip()
                    if id_this_line not in bsj_has_isoform:
                        to_bed.write("%s\n" % line.strip())

        tmp_gtf = os.path.join(folder_gtf, "ambiguous.gtf")
        _gtf_operator.do_make_gtf_for_circular_prediction_greedy(circular_candidate_regions=bed_filtered,
                                                                 gff_db=genomic_annotation,
                                                                 output_gtf_path_name=tmp_gtf)

        combine_two_into_one(circular_rna_gtf, isoform_gtf, tmp_gtf)

    else:
        _gtf_operator.do_make_gtf_for_circular_prediction_greedy(circular_candidate_regions=circ_detection_report,
                                                                 gff_db=genomic_annotation,
                                                                 output_gtf_path_name=circular_rna_gtf)


def combine_two_into_one(output, file1, file2):
    with open(output, "w") as final_combination:
        with open(file2) as ambiguous_gtf:
            with open(file1) as file1:
                for line in ambiguous_gtf:
                    final_combination.write("%s\n" % line.strip())
                for line in file1:
                    final_combination.write("%s\n" % line.strip())


def _prepare_linear_transcriptome(genome_fa, genomic_annotation, spliced_linear_reference):
    _seq_extractor.do_extract_classic_linear_transcript(gff=genomic_annotation,
                                                        fasta=genome_fa,
                                                        output=spliced_linear_reference)


def _load_to_update_default_options(path_config):
    user_config = py.body.config.config(path_config) if path_config else py.body.default_values.load_default_value()

    if SECTION_PROFILE_CIRCULAR_RNA not in user_config:
        raise KeyError(
            "ERROR@Config_file: should have a section with the name :{}".format(SECTION_PROFILE_CIRCULAR_RNA))

    circ_profile_config = dict(user_config[SECTION_PROFILE_CIRCULAR_RNA])
    default_profile = py.body.cli_opts.default_values.load_default_value()

    if SECTION_PROFILE_CIRCULAR_RNA in default_profile:
        default_profile_config = dict(default_profile[SECTION_PROFILE_CIRCULAR_RNA])
        default_profile_config.update(circ_profile_config)
        circ_profile_config = default_profile_config

    return circ_profile_config


def _confirm_quantifier(circ_profile_config):
    str_quantifier = circ_profile_config.get(_OPT_KEY_QUANTIFIER, "%s" % _OPT_VALUE_SAILFISH)
    quantifier = _QUANTIFIER_BACKEND_OF[str_quantifier]
    _logger.debug("using %s as quantification backend" % str_quantifier)
    return quantifier


def _catch_one(opts_dict, *args):
    for arg in args:
        if arg in opts_dict:
            return opts_dict.get(arg)
    else:
        raise KeyError("Error: no such key %s in option %s" % ("/".join(args), opts_dict))


if __name__ == "__main__":
    arg_parser = __cli_arg_parser()
    args = arg_parser.parse_args()
    _logger = py.body.logger.set_logger_file(_logger, args.log_file)
    main(args.cfg_file, forced_refresh=args.force)
