# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import copy
import os
import os.path

import pysrc.body.cli_opts
import pysrc.body.logger
import pysrc.body.option_check
import pysrc.body.utilities
import pysrc.body.worker
import pysrc.file_format.fa
import pysrc.wrapper.bwa

__doc__ = ''' this is the wrapper of CIRI version 1, it contains one phase: detection
'''

__author__ = 'zerodel'

_OPT_ANNOTATION = "--anno"

_OPT_INPUT = "--in"

_OPT_OUTPUT = "--out"

_OPT_REF_DIR_IN_CIRI_1 = "--ref-dir"
_OPT_REF_FILE_IN_CIRI_1 = "--ref-file"

_ESSENTIAL_ARGUMENTS = [_OPT_INPUT, _OPT_OUTPUT, _OPT_REF_FILE_IN_CIRI_1, _OPT_ANNOTATION]


class CIRIEntry(object):
    def __init__(self, string_line_in_ciri_output_format=""):
        """ construct an empty ciri entry or from a string.
        :param string_line_in_ciri_output_format: optional, a single string line in CIRI output file, except file header
        """
        if string_line_in_ciri_output_format:
            self._parse_line(string_line_in_ciri_output_format)
        else:
            self.id = ""
            self.chr = ""
            self.start = ""
            self.end = ""
            self.circRNA_type = ""
            self.gene_id = ""
            self.junction_reads = []

    def _parse_line(self, string_ciri):
        """:param string_ciri: a CIRI output file formatted string, except file header
        :return :None , set up your CIRIEntry object"""
        elements = string_ciri.strip().split("\t")
        self.junction_reads = elements.pop().split(",")
        self.gene_id = elements.pop()
        self.circRNA_type = elements.pop()
        self.id = elements.pop(0)
        self.chr = elements.pop(0)
        self.start = elements.pop(0)
        self.end = elements.pop(0)

    def __str__(self):
        return 'id:%s\nchr:%s\nstart:%s\nend:%s\ntype:%s\ngene:%s\n' % (
            self.id, self.chr, self.start, self.end, self.circRNA_type, self.gene_id
        )

    def to_dot_bed_string(self, remove_chr=False):
        """transfer this object into a .bed file string
        :param remove_chr :  boolean, since chr1 in UCSC is just 1 in Ensembl,
            this option decide whether should "chr" be removed
        """
        if remove_chr:
            chromosome_id = self.chr[3:]
        else:
            chromosome_id = self.chr

        return "\t".join([chromosome_id, self.start, self.end, self.id]).strip()


def _is_sam_file_path_valid(sam_file):
    sub_dir, sam = os.path.split(sam_file)
    if os.path.isdir(sub_dir) and os.path.exists(sub_dir):
        if sam.endswith(".sam"):
            return True
    else:
        return False


def _is_a_bwa_sam_file(path_sam):
    return os.path.exists(path_sam) and path_sam.endswith(".sam") and _is_alignment_from_bwa(path_sam)


def _is_alignment_from_bwa(align_sam):
    with open(align_sam) as sr:
        for line in sr:
            if line.strip().startswith("@"):
                if line.strip().startswith("@PG"):
                    parts = line.strip().split()
                    for part in parts:
                        if part.startswith("ID:"):
                            return part.split(":")[-1].lower() == "bwa"
            elif len(line.strip()) > 2:
                return False


def is_fasta(ref_path):
    basename, extension_with_dot = os.path.splitext(ref_path)
    if extension_with_dot not in pysrc.file_format.fa.FASTA_FILE_EXTENSION:
        raise FileNotFoundError("Error: CIRI need fasta file(s) as ref")
    return True


def _is_this_path_contains_valid_folder(path):
    folder, out_file = os.path.split(path)
    if out_file:
        return os.path.exists(folder) and os.path.isdir(folder)
    else:
        raise FileNotFoundError("Error: CIRI output should be a file")


def to_bed(ciri_opts, output_bed_file="", path_transcript_gene_mapping=""):  # redundancy : ciri_entry .transform to bed
    ciri_output_file = ciri_opts[_OPT_OUTPUT]
    abs_ciri_dir = os.path.abspath(ciri_output_file)
    main_part_ciri_path = os.path.splitext(abs_ciri_dir)[0]
    if not output_bed_file:
        output_bed_file = ".".join([main_part_ciri_path, "bed"])

    if not path_transcript_gene_mapping:
        path_transcript_gene_mapping = ".".join([main_part_ciri_path, "mapping"])

    with open(ciri_output_file) as ciri_file:
        ciri_file.readline()  # file head should be skipped

        with open(output_bed_file, "w") as exporter:
            with open(path_transcript_gene_mapping, "w") as mapping_file:
                for line in ciri_file:
                    ciri_line_entry = CIRIEntry(line.strip())

                    new_bed_line = ciri_line_entry.to_dot_bed_string()
                    mapping_string = _export_mapping_of_circular_isoform(ciri_line_entry)

                    if new_bed_line and mapping_string:
                        exporter.write(new_bed_line + "\n")
                        mapping_file.write(mapping_string + "\n")
                    else:
                        pass


def _export_mapping_of_circular_isoform(some_ciri_entry):
    if some_ciri_entry.id and some_ciri_entry.gene_id:
        return "\t".join([some_ciri_entry.id, some_ciri_entry.gene_id])
    else:
        return ""


def get_alignment(opts):
    if _OPT_INPUT in opts:
        return opts[_OPT_INPUT]
    else:
        raise KeyError("Error: no input file specified for CIRI")


def check_ref(ref_path):
    if os.path.isdir(ref_path) and os.path.exists(ref_path):
        return any([is_fasta(part) for part in os.listdir(ref_path)])

    elif os.path.isfile(ref_path) and os.path.exists(ref_path):
        return is_fasta(ref_path)

    else:
        raise FileNotFoundError("Error: not a valid fasta file  :{}".format(ref_path))


def _is_there_alignment_already(opts):
    is_there_alignments = _OPT_INPUT in opts and os.path.exists(opts[_OPT_INPUT])
    return is_there_alignments


# # end of helper functions . ###################################


is_general_aligner_needed = False

SECTION_DETECT = "CIRI"

"""ciri heavily depends on BWA aligner....but RSEM prefers bowtie/STAR,
and here we adopt the long-format arguments
"""

_logger = pysrc.body.logger.default_logger(SECTION_DETECT)


def _check_opts(args_dict=None):
    your_opt_checker = pysrc.body.option_check.OptionChecker(args_dict, name=SECTION_DETECT)
    your_opt_checker.may_need("bwa_bin", pysrc.body.utilities.which,
                              FileNotFoundError("ERROR@CIRI: incorrect bwa binary path for bwa"),
                              "binary file path of BWA aligner")

    your_opt_checker.may_need("bwa_index", os.path.exists,
                              FileNotFoundError("ERROR@CIRI: incorrect bwa index path"),
                              "index path for BWA aligner")

    your_opt_checker.must_have("ciri_path", os.path.exists,
                               FileNotFoundError("Error@CIRI: no ciri script "),
                               "file path to ciri script")

    your_opt_checker.may_need("--seqs", pysrc.body.cli_opts.check_if_these_files_exist,
                              FileNotFoundError("ERROR@CIRI: incorrect reads files provided "),
                              "sequence reads files need analysis")

    your_opt_checker.may_need(_OPT_ANNOTATION, os.path.exists,
                              FileNotFoundError("ERROR@CIRI: incorrect annotation file "),
                              "genomic annotation file")

    your_opt_checker.at_most_one(["--thread_num", "-T"], lambda x: x.isdecimal(),
                                 ValueError("Error@CIRI: thread num should be a number"),
                                 "thread number.")

    your_opt_checker.must_have(_OPT_INPUT, _is_sam_file_path_valid,
                               FileNotFoundError("Error : unable to find CIRI input file"),
                               "path to alignments in SAM file type")

    your_opt_checker.must_have(_OPT_OUTPUT, _is_this_path_contains_valid_folder,
                               FileNotFoundError("Error : incorrect CIRI output file"),
                               "CIRI detection report file")

    your_opt_checker.one_and_only_one([_OPT_REF_DIR_IN_CIRI_1, _OPT_REF_FILE_IN_CIRI_1], check_ref,
                                      FileNotFoundError("Error: incorrect CIRI ref file"),
                                      "reference file for CIRI")

    your_opt_checker.forbid_these_args("--help", "-H")

    def _ciri_input_check(opts):
        no_sam_for_ciri = not _is_a_bwa_sam_file(opts[_OPT_INPUT])
        if no_sam_for_ciri:
            if "bwa_bin" not in opts or not pysrc.body.utilities.which(opts["bwa_bin"]):
                raise KeyError("ERROR@CIRI@NO_SAM: incorrect BWA binary file provided")

            if "bwa_index" not in opts or not os.path.exists(opts["bwa_index"]):
                raise KeyError("ERROR@CIRI@NO_SAM: incorrect BWA index file provided")

            if "--seqs" not in opts or not pysrc.body.cli_opts.check_if_these_files_exist(opts["--seqs"]):
                raise KeyError("ERROR@CIRI@NO_SAM: incorrect sequence reads for BWA alignment ")

    your_opt_checker.custom_condition(_ciri_input_check, "check the options when no sam file for CIRI")

    return your_opt_checker


opt_checker = _check_opts()

OPTION_CHECKERS = [opt_checker]


def _get_detect_cmd(opts_raw):
    opts = copy.copy(opts_raw)
    cmd_corp = "perl {ciri_path}".format(ciri_path=opts.pop("ciri_path"))
    cmd_main = " ".join([pysrc.body.cli_opts.drop_key(key, opts) for key in _ESSENTIAL_ARGUMENTS])
    cmd_latter = pysrc.body.cli_opts.enum_all_opts(opts)
    return " ".join([cmd_corp, cmd_main, cmd_latter])


def detect(par_dict=None, **kwargs):
    opts_of_index_phase_raw = pysrc.body.cli_opts.merge_parameters(kwargs, par_dict, SECTION_DETECT)

    opts = copy.copy(opts_of_index_phase_raw)

    bwa_bin_path = __extract_and_check(opts, entry_name="bwa_bin")

    bwa_index_path = __extract_and_check(opts, entry_name="bwa_index")

    reads = __extract_and_check(opts, "--seqs")

    if _is_there_alignment_already(opts):
        _logger.debug("already have alignment file at {path_to_align_file}".format(path_to_align_file=opts.get(
            _OPT_INPUT, "")))
    else:
        if reads:
            try:
                map_job_setting = {
                    "bwa_bin": bwa_bin_path,
                    "bwa_index": bwa_index_path,
                    "read_file": reads,
                    "sam": opts[_OPT_INPUT],
                }
                _logger.info("bwa mapping with parameter: %s" % str(map_job_setting))

                _optional_mapping_using_bwa(map_job_setting)  # perform the mapping using bwa
            except Exception as e:
                _logger.error(" ERROR occurs during preparing the SAM file for CIRI")
                raise e  # no idea how to handle it

        else:
            _logger.error("no SAM file and no Reads")
            raise FileNotFoundError("Error@CIRI: no reads for BWA mapping")

    opt_checker.check(copy.copy(opts_of_index_phase_raw))

    cmd_detect = _get_detect_cmd(opts)

    _logger.debug("raw command for CIRI is : %s" % cmd_detect)
    pysrc.body.worker.run(cmd_detect)  # perform the CIRI job here

    return opts_of_index_phase_raw


def __extract_and_check(opts, entry_name):
    bwa_bin_path = opts.pop(entry_name, "")
    if entry_name in opts:
        raise KeyError(
            "ERROR@PYTHON: unable to remove {this_entry} in a dict using dict.pop".format(this_entry=entry_name))
    return bwa_bin_path


def _optional_mapping_using_bwa(meta_setting, **kwargs):
    try:
        bwa_bin = meta_setting["bwa_bin"] if "bwa_bin" in meta_setting else kwargs.pop("bwa_bin")
    except KeyError:
        raise KeyError("Error@CIRI: no binary file for BWA aligner")

    try:
        index_bwa = meta_setting["bwa_index"] if "bwa_index" in meta_setting else kwargs.pop("bwa_index")
    except KeyError:
        raise KeyError("Error@CIRI: no index file for BWA ")

    try:
        read_file = meta_setting["read_file"] if "read_file" in meta_setting else kwargs.pop("read_file")
    except KeyError:
        raise KeyError("Error@CIRI: no sequence reads file for BWA")

    try:
        sam = meta_setting["sam"] if "sam" in meta_setting else kwargs.pop("sam")
    except KeyError:
        raise KeyError("Error@CIRI: no sam output for BWA")

    if not pysrc.wrapper.bwa.is_path_contain_index(index_bwa):
        pysrc.wrapper.bwa.index(para_config={"bwa_bin": bwa_bin, "in_fasta": index_bwa, "-a": "bwtsw"})

    pysrc.wrapper.bwa.align(para_config={
        "bwa_bin": bwa_bin,
        "read_file": read_file,
        "bwa_index": index_bwa,
        "-T": "19",
        "-t": str(int(pysrc.body.utilities.core_numbers_of_cpu()) - 4),  # cpu core numbers
    }, output=sam)


if __name__ == "__main__":
    print(__doc__)
    print(opt_checker)
