# !/usr/bin/env python
# -*- coding:utf-8 -*-
# author : zerodel
# Readme:
#
import itertools
import multiprocessing
import os

import gffutils

from py.file_format.gtf import GTFitem

__doc__ = '''
'''
__author__ = 'zerodel'

OVERLAP_WINDOW_WIDTH = 3


class PredictedCircularRegion(object):
    def __init__(self, args_tuple, **kwargs):
        if args_tuple:
            self.predict_id, self.seqid, self.start, self.end = args_tuple
            self.start = int(self.start)
            self.end = int(self.end)
        elif kwargs:
            self.seqid = kwargs.get("chromosome")
            self.start = int(kwargs.get("start"))
            self.end = int(kwargs.get("end"))
            self.predict_id = kwargs.get("given_id")
        else:
            raise NameError("Error: some wrong arguments happens")

    def is_flanking(self, gff_feature):
        return self.start <= int(gff_feature.start) and self.end >= int(gff_feature.end)

    def extract_flanked_linear_entries(self, gffutils_database):
        # extract all isoform part from some database of gtf file .
        # here we assume all exon has attribution of 'transcript_id'
        transcript_exon_dict = {}
        for linear_isoform in gffutils_database.region(seqid=self.seqid, start=self.start, end=self.end,
                                                       featuretype="transcript"):
            corresponding_circular_exons = [exon for exon in
                                            gffutils_database.children(linear_isoform.id, featuretype="exon",
                                                                       order_by="start",
                                                                       limit=(self.seqid, self.start, self.end),
                                                                       completely_within=True)]
            if corresponding_circular_exons:
                transcript_exon_dict.setdefault(linear_isoform.id, corresponding_circular_exons)

        return transcript_exon_dict

    @staticmethod
    def generate_exon_for_circular_isoform(host_seqname, start, end, host_gene_id, host_tran_id, strand="+", frame="."):
        artificial_exon = GTFitem()
        artificial_exon.set_start(int(start))
        artificial_exon.set_end(int(end))
        artificial_exon.set_gene_id(host_gene_id)
        artificial_exon.set_transcript_id(host_tran_id)
        artificial_exon.set_seqname(host_seqname)
        artificial_exon.set_source("ciri")
        artificial_exon.set_feature("exon")
        artificial_exon.set_strand(strand)
        artificial_exon.set_frame(frame)
        return artificial_exon

    def arrange_exons_the_naive_way(self, db):
        exons_raw = list(set([(exon.seqid, exon.source, exon.start, exon.end, exon.strand, exon.frame)
                              for exon in db.region(seqid=self.seqid,
                                                    start=int(self.start),
                                                    end=int(self.end),
                                                    featuretype="exon")]))

        exon_filtered = []   # start filter exon objects
        for exon in exons_raw:
            exon_seqid, exon_source, exon_start, exon_end, exon_strand, exon_frame = exon

            if exon_seqid == 'chrM':
                continue

            if exon_source not in ["processed_transcript", "protein_coding"]:
                continue

            if exon_start < self.start - OVERLAP_WINDOW_WIDTH:
                exon_start = self.start

            if exon_end > self.end + OVERLAP_WINDOW_WIDTH:
                exon_end = self.end

            exon_filtered.append((exon_seqid, exon_source, exon_start, exon_end, exon_strand, exon_frame))

        exon_filtered = sorted(exon_filtered, key = lambda x : x[2])

        artificial_exons = []

        if len(self.predict_id.split("@")) == 2:
            transcript_id, gene_id = self.predict_id.split("@")
        else:
            transcript_id = self.predict_id
            gene_id = "n/a"

        for exon_locus in exon_filtered:
            exon_seqid, exon_source, exon_start, exon_end, exon_strand, exon_frame = exon_locus

            artificial_exons.append(self.generate_exon_for_circular_isoform(host_seqname=exon_seqid,
                                                                            start=exon_start,
                                                                            end=exon_end,
                                                                            host_gene_id=gene_id,
                                                                            host_tran_id=transcript_id,
                                                                            strand=exon_strand,
                                                                            frame=exon_frame
                                                                            )
                                    )
        return artificial_exons

    def mark_extracted_exons(self, dict_transcript_exon):
        # this function is after the extract_flanked.... function

        marked_exons = []
        for transcript_id in dict_transcript_exon.keys():
            for exon in dict_transcript_exon[transcript_id]:
                neo_exon = self.simplify_this_feature(exon, new_source="circRNA",
                                                      new_transcript_id="%s@%s" % (self.predict_id, transcript_id))
                marked_exons.append(neo_exon)

        return marked_exons

    @staticmethod
    def simplify_this_feature(feature_from_gffutils_db, new_source="", new_transcript_id=""):
        artificial_exon = GTFitem(str(feature_from_gffutils_db))
        formal_gene_id = artificial_exon.get_gene_id()
        formal_trans_id = artificial_exon.get_transcript_id()
        artificial_exon.init_null_attribute()
        artificial_exon.set_gene_id(formal_gene_id)
        artificial_exon.set_transcript_id(formal_trans_id)

        if new_source:
            artificial_exon.set_source(new_source)
        if new_transcript_id:
            artificial_exon.set_transcript_id(new_transcript_id)

        return artificial_exon


def parse_bed_line(line):
    parts = line.strip().split()
    if len(parts) < 4:
        raise KeyError("Error: not right bed file type")
    chr_name, start, end, isoform_id = parts[:4]
    return isoform_id, chr_name, start, end


def parse_ciri_line(line):
    parts = line.strip().split("\t")
    if len(parts) < 4:
        raise KeyError("Error: not right ciri file type")
    isoform_id, chr_name, start, end = parts[:4]
    return isoform_id, chr_name, start, end


def parse_ciri_as_region(ciri_output):
    with open(ciri_output) as ciri_reader:
        ciri_reader.readline()
        for line in ciri_reader:
            yield PredictedCircularRegion(parse_ciri_line(line))


def parse_bed_as_region(bed_output_no_header):
    with open(bed_output_no_header) as read_bed:
        for line in read_bed:
            yield PredictedCircularRegion(parse_bed_line(line))


def get_gff_database(gtf_file):
    path_main, file_part = os.path.split(gtf_file)
    file_body_name, file_suffix = file_part.split(".")

    if "gtf" == file_suffix:
        db_file_path = os.path.join(path_main, ".".join([file_body_name, "db"]))
        if os.path.exists(db_file_path):
            db = gffutils.FeatureDB(db_file_path)
        else:
            # todo: here lies some trap
            #  due to difference between versions of .gtf file, binary database building process may be time exhausting
            db = gffutils.create_db(gtf_file, db_file_path)
    elif "db" == file_suffix:
        db = gffutils.FeatureDB(gtf_file)
    else:
        raise NameError
    return db


class SimpleMapReduce(object):
    def __init__(self, map_func, reduce_func, num_cores=None):
        self.map_func = map_func
        self.reduce_func = reduce_func
        self.pool = multiprocessing.Pool(num_cores)

    def __call__(self, inputs, chunk_size=1):
        map_response = self.pool.map(self.map_func, inputs)

        raw_list_gtf_items = itertools.chain(*map_response)
        reduced_values = self.reduce_func(raw_list_gtf_items)
        return reduced_values


def _get_exons(intervals_and_gff_path):
    regs, gff_path = intervals_and_gff_path
    db = get_gff_database(gff_path)
    res = []
    for reg in regs:
        res.extend(reg.arrange_exons_the_naive_way(db))
    return res


def _get_exons_with_isoforms(intervals_and_gff_path):
    regs, gff_path = intervals_and_gff_path
    gff_db = get_gff_database(gff_path)
    res = []
    for reg in regs:
        flanked_linear_entries = reg.extract_flanked_linear_entries(gff_db)
        exons_marked_circular = reg.mark_extracted_exons(flanked_linear_entries)
        res.extend(exons_marked_circular)
    return res


def _all_exons(exons):
    return [str(exon) for exon in exons]


def get_gtf_mp(path_bed, gff_path, is_structure_show=False, num_process=0):
    if path_bed.endswith('.bed'):
        get_regions = parse_bed_as_region
    else:
        get_regions = parse_ciri_as_region

    regs = [x for x in get_regions(path_bed)]

    reg_parts = equal_divide(regs, num_process)

    gff_paths = [gff_path] * num_process if num_process else [gff_path]

    if is_structure_show:
        a = SimpleMapReduce(_get_exons_with_isoforms, _all_exons, num_process)
    else:
        a = SimpleMapReduce(_get_exons, _all_exons, num_process)

    result = a(zip(reg_parts, gff_paths))
    return result


def equal_divide(regs, num_process):
    if isinstance(num_process, int):

        if num_process > len(regs):
            return [[x] for x in regs]
        else:
            size_chunk = int(round(len(regs) / num_process))
            if size_chunk * num_process < len(regs):
                size_chunk += 1

            reg_parts = [regs[x: x + size_chunk] for x in
                         range(0, len(regs), size_chunk)]

            return reg_parts
    else:
        raise TypeError("Error@gtf_processing: process number should be a integer")


def do_make_gtf_for_circular_prediction_greedy(gff_db, circular_candidate_regions, output_gtf_path_name="",
                                               is_isoform_structure_shown=False):
    num_core = os.cpu_count() - 1 if os.cpu_count() > 2 else 0
    with open(output_gtf_path_name, "w") as out_gtf:
        out_gtf.write("\n".join(get_gtf_mp(path_bed=circular_candidate_regions,
                                           gff_path=gff_db,
                                           is_structure_show=is_isoform_structure_shown,
                                           num_process=num_core)))
