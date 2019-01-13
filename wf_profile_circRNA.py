# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import argparse
import copy
import os
import shutil

import pysrc.being.linc
import pysrc.body.cli_opts
import pysrc.body.config
import pysrc.body.logger
import pysrc.body.option_check
import pysrc.body.utilities
import pysrc.body.worker
import pysrc.file_format.bsj_gtf
import pysrc.file_format.ciri_as_to_gtf
import pysrc.file_format.ciri_entry
import pysrc.file_format.fa
import pysrc.sub_module.summary_quant
import pysrc.wrapper.gffread
import pysrc.wrapper.sailfish
import pysrc.wrapper.salmon
from pysrc.body.cli_opts import catch_one

_SUB_DIR_PROFILE_RESULT = "profile_result"

_SUB_DIR_INDEX_FINAL = "index_final"

_OPT_CIRI_AS_OUTPUT_PREFIX = "ciri_as_prefix"

_OPT_VALUE_SAILFISH = "sailfish"

_OPT_KEY_QUANTIFIER = "quantifier"

_OPT_KEY_ADDITIONAL_CIRC_REF = "additional_circ_ref"
_OPT_KEY_ADDITIONAL_LINEAR_REF = "additional_linear_ref"

_OPT_KEY_ADDITIONAL_ANNOTATION = "additional_annotation"

_OPT_KEY_USE_LINC_EXPLICITLY = "flag_use_linc_explicitly"

_OPT_KEY_REJECT_LINEAR = "flag_reject_linear"

_QUANTIFIER_BACKEND_OF = {"sailfish": pysrc.wrapper.sailfish,
                          "salmon": pysrc.wrapper.salmon}

__doc__ = '''
'''

__author__ = 'zerodel'

SECTION_PROFILE_CIRCULAR_RNA = "CIRC_PROFILE"

_logger = pysrc.body.logger.default_logger(SECTION_PROFILE_CIRCULAR_RNA)


def __cli_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_file", help="file path to a configuration file of detection job")
    parser.add_argument("-l", "--log_file", help="logging file path", default="")
    parser.add_argument("-f", "--force", help="forced refresh", action="store_true")
    return parser


def _option_check_main_interface(opts=None):
    oc = pysrc.body.option_check.OptionChecker(opts, name=SECTION_PROFILE_CIRCULAR_RNA)

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

    oc.may_need(_OPT_CIRI_AS_OUTPUT_PREFIX, pysrc.body.cli_opts.is_suitable_path_with_prefix,
                FileNotFoundError("Error@circular_RNA_profiling: incorrect circular Alternative Splice file prefix"),
                "path prefix to CIRI-AS report of circular exons")

    # make sure the path should be a folder
    def make_sure_there_is_a_folder(x):
        try:
            if not os.path.isdir(x):
                os.mkdir(x)
            if os.path.exists(x) and os.path.isdir(x):
                return True
        except Exception as e:
            return False
        return False

    oc.must_have("-o", make_sure_there_is_a_folder,
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

    oc.may_need(_OPT_KEY_ADDITIONAL_CIRC_REF, os.path.exists,
                FileNotFoundError("Error@circular_RNA_profiling: additional circular reference file not exist"),
                "path to additional circular RNA reference file (.fa), ")

    oc.may_need(_OPT_KEY_ADDITIONAL_ANNOTATION, os.path.exists,
                FileNotFoundError("Error@circular_RNA_profiling: additional annotation not exist"),
                "path to additional circular RNA annotation file in gtf format")

    oc.may_need(_OPT_KEY_ADDITIONAL_LINEAR_REF, os.path.exists,
                FileNotFoundError("Error@circular_RNA_profiling: additional linear reference file not exist"),
                "path to additional linear RNA reference file(.fa)")

    oc.may_need(_OPT_KEY_USE_LINC_EXPLICITLY, lambda x: x in ("T", "F", "True", "False", ""),
                KeyError("Error@circular_RNA_profiling: incorrect flag to specify whether linc should be explicit"),
                "flag to specify whether linc RNA should be include in quantification result")

    oc.may_need(_OPT_KEY_REJECT_LINEAR, lambda x: x in ("T", "F", "True", "False", ""),
                KeyError("""Error@circular_RNA_profiling: incorrect flag 
                to specify whether index should reject linear RNA"""),
                """flag to specify whether to reject linear RNA during quantification, for example for a RNase R  
                treated sample"""
                )

    oc.forbid_these_args("-h", "--help")
    return oc


# assign package-scale global objects
option_checker = _option_check_main_interface()
OPTION_CHECKERS = [option_checker]

# dummy implement
_seq_extractor = pysrc.wrapper.gffread
_gtf_operator = pysrc.file_format.bsj_gtf


def __determine_kmer_length(obj_circ_profile):
    if "-k" in obj_circ_profile and obj_circ_profile['-k']:
        kmer_length = int(obj_circ_profile["-k"])
    else:
        kmer_length = 21
    return kmer_length


def main(path_config, forced_refresh=False):
    circ_profile_config = _load_to_update_default_options(path_config)

    _logger.debug("profile config dict is : %s" % str(circ_profile_config))

    option_checker.check(copy.copy(circ_profile_config))  # check your options

    quantifier = _confirm_quantifier(circ_profile_config)

    genomic_annotation = catch_one(circ_profile_config, "-a", "--annotation")
    genome_fa = catch_one(circ_profile_config, "-g", "--genomic_seqs_fasta")
    circ_detection_report = catch_one(circ_profile_config, "-c", "--bed", "--ciri_bsj")

    output_path = catch_one(circ_profile_config, "-o")

    # additional options
    additional_circ_ref = circ_profile_config.get(_OPT_KEY_ADDITIONAL_CIRC_REF)
    additional_annotation = circ_profile_config.get(_OPT_KEY_ADDITIONAL_ANNOTATION)
    additional_linear_ref = circ_profile_config.get(_OPT_KEY_ADDITIONAL_LINEAR_REF)
    use_linc = _OPT_KEY_USE_LINC_EXPLICITLY in circ_profile_config
    reject_linear = _OPT_KEY_REJECT_LINEAR in circ_profile_config

    # assign file path
    spliced_linear_reference = os.path.join(output_path, "ref_linear.fa")
    circular_rna_gtf = os.path.join(output_path, "circ_only.gtf")
    circ_reference_seq = os.path.join(output_path, "circ_only.fa")

    linc_rna_gtf = os.path.join(output_path, "linc_only.gtf")
    linc_reference_seq = os.path.join(output_path, "linc_only.fa")

    k = __determine_kmer_length(circ_profile_config)

    # 1st, extract the linear sequence
    if not reject_linear:
        if not os.path.exists(spliced_linear_reference) or forced_refresh:
            _prepare_linear_transcriptome(genome_fa, genomic_annotation, spliced_linear_reference)

    # 2nd, get the circular RNA gtf sequences

    if not os.path.exists(circular_rna_gtf) or forced_refresh:
        _prepare_circular_rna_annotation(circ_detection_report, circ_profile_config, circular_rna_gtf,
                                         genomic_annotation)

    # 3rd, extracts circular RNA sequence
    _seq_extractor.do_extract_non_coding_transcript(gff=circular_rna_gtf,
                                                    path_ref_sequence_file=genome_fa,
                                                    output=circ_reference_seq)

    # 4th, do operations on circular RNA reference .lincRNA are treated as linear mRNA
    pysrc.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference_seq,
                                                      fa_out=circ_reference_seq,
                                                      convert_fun=pysrc.file_format.fa.make_adapter(k))

    # decorate sequence , we set the mean of effective length to 150.
    mean_library_length = int(circ_profile_config["--mll"]) if "--mll" in circ_profile_config and \
                                                               circ_profile_config[{"--mll"}] else 150

    pysrc.file_format.fa.convert_all_entries_in_fasta(fa_in=circ_reference_seq,
                                                      fa_out=circ_reference_seq,
                                                      convert_fun=pysrc.file_format.fa.pad_for_effective_length(
                                                          mean_library_length))

    # ###### ========================================================
    # process additional reference . including linc and custom circular RNA 18-12-21
    lst_reference_fa = [circ_reference_seq] if reject_linear else [spliced_linear_reference, circ_reference_seq]
    lst_annotation = [circular_rna_gtf] if reject_linear else [genomic_annotation, circular_rna_gtf]

    if additional_linear_ref and os.path.exists(additional_linear_ref):
        lst_reference_fa.append(additional_linear_ref)

    if additional_circ_ref:
        additional_circ_ref_decoded = os.path.join(output_path, "additional_circ_ref.fa")
        pysrc.file_format.fa.convert_all_entries_in_fasta(fa_in=additional_circ_ref,
                                                          fa_out=additional_circ_ref_decoded,
                                                          convert_fun=pysrc.file_format.fa.pad_for_effective_length(
                                                              mean_library_length))
        lst_reference_fa.append(additional_circ_ref_decoded)

    if additional_annotation:
        lst_annotation.append(additional_annotation)

    # Wednesday, 5 April 2017: add same procedure for lincRNA
    if use_linc:
        if not os.path.exists(linc_rna_gtf) or forced_refresh:
            pysrc.being.linc.prepare_linc_annotation(original_gff=genomic_annotation,
                                                     target_linc_annotation=linc_rna_gtf)

        if not os.path.exists(linc_reference_seq) or forced_refresh:
            pysrc.being.linc.prepare_linc_transcriptome_seq(linc_annotation=linc_rna_gtf,
                                                            genomic_seq=genome_fa,
                                                            target_fa=linc_reference_seq)
        lst_reference_fa.append(linc_reference_seq)

    # 5th , combined those fa files
    final_refer = os.path.join(output_path, "final.fa")
    pysrc.body.utilities.do_merge_files(final_refer, lst_reference_fa)

    # linc RNA is already in original gtf file
    final_annotation = os.path.join(output_path, "final.gtf")
    pysrc.body.utilities.do_merge_files(final_annotation, lst_annotation)

    # 6th , make index for quantifier

    path_to_quantifier_index = os.path.join(output_path, _SUB_DIR_INDEX_FINAL)

    index_parameters = {"--kmerSize": str(k),
                        "--transcripts": final_refer,
                        "--out": path_to_quantifier_index
                        } if quantifier is pysrc.wrapper.sailfish else {
        "--kmerLen": str(k),
        "--transcripts": final_refer,
        "--index": path_to_quantifier_index,
    }

    quantifier.index(para_config=index_parameters)

    # 7th , do quantification!
    path_to_quantify_result = os.path.join(output_path, _SUB_DIR_PROFILE_RESULT)
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
    opts_quantifier["--geneMap"] = final_annotation

    # # on salmon's bias model
    if quantifier is pysrc.wrapper.salmon:
        opts_quantifier["--seqBias"] = None
        opts_quantifier["--gcBias"] = None

    quantifier.quantify(para_config=opts_quantifier)

    # pysrc.sub_module.summary_quant.aggregate_isoform_quantify_result(
    #     quant_sf=os.path.join(path_to_quantify_result, "quant.sf"),
    #     summarized_output=os.path.join(path_to_quantify_result, "summarized.quant"),
    #     gtf_annotation=final_annotation)


def _prepare_circular_rna_annotation(circ_detection_report, circ_profile_config, circular_rna_gtf, genomic_annotation):
    folder_gtf, gtf_base_name = os.path.split(circular_rna_gtf)

    if _OPT_CIRI_AS_OUTPUT_PREFIX in circ_profile_config:
        circ_as_file_prefix = catch_one(circ_profile_config, _OPT_CIRI_AS_OUTPUT_PREFIX)
        isoform_gtf = os.path.join(folder_gtf, "isoform_" + gtf_base_name)
        bsj_has_isoform = pysrc.file_format.ciri_as_to_gtf.transform_as_path_to_gtf_and_return_bsj_junctions(
            circ_as_file_prefix, isoform_gtf)

        bed_this = os.path.join(folder_gtf, "detection_raw.bed")

        if not circ_detection_report.endswith(".bed"):
            _logger.info(" we treat circRNA identification report as a CIRI output : {file_circ_report}".format(
                file_circ_report=circ_detection_report))
            pysrc.file_format.ciri_entry.transform_ciri_to_bed(circ_detection_report, bed_this)
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
        pysrc.body.utilities.do_merge_files(circular_rna_gtf, (isoform_gtf, tmp_gtf))

    else:
        _gtf_operator.do_make_gtf_for_circular_prediction_greedy(circular_candidate_regions=circ_detection_report,
                                                                 gff_db=genomic_annotation,
                                                                 output_gtf_path_name=circular_rna_gtf)


def _prepare_linear_transcriptome(genome_fa, genomic_annotation, spliced_linear_reference):
    _seq_extractor.do_extract_classic_message_transcript(gff=genomic_annotation,
                                                         path_ref_sequence_file=genome_fa,
                                                         output=spliced_linear_reference)


def _load_to_update_default_options(path_config):
    user_config = pysrc.body.config.config(
        path_config) if path_config else pysrc.body.config.load_default_value()

    if SECTION_PROFILE_CIRCULAR_RNA not in user_config:
        raise KeyError(
            "ERROR@Config_file: should have a section with the name :{}".format(SECTION_PROFILE_CIRCULAR_RNA))

    user_option_section = dict(user_config[SECTION_PROFILE_CIRCULAR_RNA])
    default_config = pysrc.body.config.load_default_value()

    if SECTION_PROFILE_CIRCULAR_RNA in default_config:
        default_option_section = dict(default_config[SECTION_PROFILE_CIRCULAR_RNA])
        default_option_section.update(user_option_section)
        user_option_section = default_option_section

    return user_option_section


def _confirm_quantifier(circ_profile_config):
    str_quantifier = circ_profile_config.get(_OPT_KEY_QUANTIFIER, _OPT_VALUE_SAILFISH)
    quantifier = _QUANTIFIER_BACKEND_OF[str_quantifier]
    _logger.debug("using %s as quantification backend" % str_quantifier)
    return quantifier


if __name__ == "__main__":
    arg_parser = __cli_arg_parser()
    cl_args = arg_parser.parse_args()
    _logger = pysrc.body.logger.set_logger_file(_logger, cl_args.log_file)
    main(cl_args.cfg_file, forced_refresh=cl_args.force)
