# -*- coding: utf-8 -*-
#BEGIN_HEADER
# The header block is where all import statments should live
from __future__ import print_function
import os
from Bio import SeqIO
from pprint import pprint, pformat
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from KBaseReport.KBaseReportClient import KBaseReport
from util import (
    check_hisat2_parameters,
    setup_hisat2,
    fetch_reads_refs_from_sampleset,
    fetch_reads_from_reference
)
from kb_hisat2.hisat2 import Hisat2
#END_HEADER


class kb_hisat2:
    '''
    Module Name:
    kb_hisat2

    Module Description:
    A KBase module: kb_hisat2
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = "https://github.com/briehl/kb_hisat2"
    GIT_COMMIT_HASH = "2d7e32ccd12fa157beba745dee22afbeb9eec74d"

    #BEGIN_CLASS_HEADER
    # Class variables and functions can be defined in this block
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR

        # Any configuration parameters that are important should be parsed and
        # saved in the constructor.
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.workspace_url = config['workspace-url']
        self.shared_folder = config['scratch']
        self.num_threads = 2

        #END_CONSTRUCTOR

    def run_hisat2(self, ctx, params):
        """
        :param params: instance of type "Hisat2Params" -> structure:
           parameter "ws_id" of String, parameter "sampleset_id" of String,
           parameter "genome_id" of String, parameter "num_threads" of Long,
           parameter "quality_score" of String, parameter "skip" of Long,
           parameter "trim3" of Long, parameter "trim5" of Long, parameter
           "np" of Long, parameter "minins" of Long, parameter "maxins" of
           Long, parameter "orientation" of String, parameter
           "min_intron_length" of Long, parameter "max_intron_length" of
           Long, parameter "no_spliced_alignment" of type "bool" (indicates
           true or false values, false <= 0, true >=1), parameter
           "transcriptome_mapping_only" of type "bool" (indicates true or
           false values, false <= 0, true >=1), parameter "tailor_alignments"
           of String
        :returns: instance of type "ResultsToReport" (Object for Report type)
           -> structure: parameter "report_name" of String, parameter
           "report_ref" of String
        """
        # ctx is the context object
        # return variables are: returnVal
        #BEGIN run_hisat2

        returnVal = dict()

        # steps to cover.
        # 0. check the parameters
        param_err = check_hisat2_parameters(params)
        if len(param_err) > 0:
            for err in param_err:
                print(err)
            raise ValueError("Errors found in parameters, see above for details.")

        hs_runner = Hisat2(self.callback_url, self.workspace_url, self.shared_folder)
        # 1. Get hisat2 index from genome.
        #    a. If it exists in cache, use that.
        #    b. Otherwise, build it
        idx_prefix = hs_runner.build_index(params["genome_ref"])

        # 2. Get list of reads object references
        reads_refs = fetch_reads_refs_from_sampleset(
            params["sampleset_ref"], self.workspace_url, self.callback_url
        )

        # 3. Run hisat with index and reads.
        alignments = dict()
        for idx, reads_ref in enumerate(reads_refs):
            reads = fetch_reads_from_reference(reads_ref, self.callback_url)
            output_file = "aligned_reads_{}".format(idx)
            alignments[reads_ref] = hs_runner.run_hisat2(
                idx_prefix, reads, params, output_file=output_file
            )
            # delete reads file
            os.remove(reads["file_fwd"])
            if "file_rev" in reads:
                os.remove(reads["file_rev"])
        #END run_hisat2

        # At some point might do deeper type checking...
        if not isinstance(returnVal, dict):
            raise ValueError('Method run_hisat2 return value ' +
                             'returnVal is not type dict as required.')
        # return the results
        return [returnVal]

    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
