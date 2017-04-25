# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import os

import pysrc.body.logger

__doc__ = '''
'''
__author__ = 'zerodel'

_logger = pysrc.body.logger.default_logger("CIRI_ENTRY")

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

        bed_id_showing_gene_host = "%s@%s" % (self.id, self.gene_id)
        return "\t".join([chromosome_id, self.start, self.end, bed_id_showing_gene_host]).strip()


def transform_ciri_to_bed(ciri_output_file, output_bed_file=""):
    abs_ciri_dir = os.path.abspath(ciri_output_file)
    main_part_ciri_path = os.path.splitext(abs_ciri_dir)[0]
    if not output_bed_file:
        output_bed_file = ".".join([main_part_ciri_path, "bed"])

    with open(ciri_output_file) as ciri_file:
        ciri_file.readline()  # file head should be skipped

        with open(output_bed_file, "w") as exporter:

                for line in ciri_file:
                    ciri_line_entry = CIRIEntry(line.strip())

                    new_bed_line = ciri_line_entry.to_dot_bed_string()

                    if new_bed_line:
                        exporter.write(new_bed_line + "\n")
                    else:
                        _logger.warning("encounter a null entry at %s" % line.strip())


def export_mapping_of_circular_isoform(some_ciri_entry):
    if some_ciri_entry.id and some_ciri_entry.gene_id:
        return "\t".join([some_ciri_entry.id, some_ciri_entry.gene_id])
    else:
        return ""
