import filecmp
import difflib
from os import path
import os
import shutil

class IntegrationConfig(object):
    def __init__(self, common_patterns = {}, ignore_files=["command.sh"]):
        """Configuration for integration analysis.

        common_patterns - Equivalent patterns to be ignore in diff generation. Provided as dict of form:
                            { pattern_name : (ref_pattern, new_pattern) }
                 
                          Eg. { "branch_directory" : ("build_dir/branch_a", "build_dir/branch_b") }

        ignore_files - Files to ignore. Defaults to ["command.sh"]

        """
        
        self.common_patterns = common_patterns
        self.ignore_files = ignore_files
        
class IntegrationAnalysis(object):
    def __init__(self, ref_dir, new_dir, config = IntegrationConfig()):
        """Configure integration analysis.

        ref_dir - Reference result directory.
        new_dir - New result directory.
        config - IntegrationConfig config object.

        """

        self.ref_dir = ref_dir
        self.new_dir = new_dir
        self.config = config
        
        self.perform_analysis()
    
    def perform_analysis(self):
        dir_comparer = filecmp.dircmp(self.ref_dir, self.new_dir, ignore=self.config.ignore_files)
        
        self.tests_removed = dir_comparer.left_list
        self.tests_added = dir_comparer.right_list
        
        self.test_results = {}
        
        for test in dir_comparer.common_dirs:
            self.test_results[test] = \
                IntegrationTestAnalysis(
                    path.join(self.ref_dir, test),
                    path.join(self.new_dir, test),
                    self.config)
                
    def write_html_report(self, outdir, htmldiff = difflib.HtmlDiff(), process_pool_size = None):
        os.makedirs(outdir)
        
        tests_to_report = [(t, r) for t, r in self.test_results.iteritems() if not r.passed]
        
        if process_pool_size:
            from multiprocessing import Pool
            process_pool = Pool(process_pool_size)
            
            for testname, result in tests_to_report:
                test_outdir = path.join(outdir, testname)
                process_pool.apply_async(__write_analysis_html_report, result, test_outdir)
                
            process_pool.close()
            process_pool.join()
            
        else:
            for testname, result in tests_to_report:
                result.write_html_report(path.join(outdir, testname))
    
    def write_test_report(self, outdir):
        if not path.exists(outdir):
            os.makedirs(outdir)

        with open(path.join(outdir, "tests_failed.txt"), "w") as failed, open(path.join(outdir, "tests_passed.txt"), "w") as passed:
            for test, result in self.test_results.iteritems():
                if result.passed:
                    passed.write(test + "\n")
                else:
                    failed.write(test + "\n")
                    result.write_test_report(path.join(outdir, test))

def __write_analysis_html_report(result, test_outdir):
    result.write_html_report(test_outdir)

class IntegrationTestAnalysis(object):
    def __init__(self, ref_dir, new_dir, config = IntegrationConfig()):
        """Result analysis for a single integration test result.

        ref_dir - Reference result directory.
        new_dir - New result directory.
        config - IntegrationConfifg config object.
        """
        
        self.ref_dir = ref_dir
        self.new_dir = new_dir
        self.config = config
        
        self.perform_analysis()
    
    def perform_analysis(self):
        dir_comparer = filecmp.dircmp(self.ref_dir, self.new_dir, ignore=self.config.ignore_files)
        
        self.diff_files = []
        
        self.diff_files.extend(dir_comparer.diff_files)
        for subdir, subdir_diff in dir_comparer.subdirs.iteritems():
            self.diff_files.extend(path.join(subdir, f) for f in subdir_diff.diff_files)
        
        #self.file_diffs = {}
        
        #for f in self.diff_files:
            #with open(path.join(self.ref_dir, f)) as ref_file, open(path.join(self.new_dir, f)) as new_file:
                #self.file_diffs[f] = list(difflib.context_diff(ref_file.readlines(), new_file.readlines()))
                
    @property
    def passed(self):
        return not self.diff_files
    
    def write_html_report(self, outdir, htmldiff = difflib.HtmlDiff()):
        for f in self.diff_files:
            with open(path.join(self.ref_dir, f)) as ref_file, open(path.join(self.new_dir, f)) as new_file:
                output_file = path.join(outdir, f + ".html")
                if path.dirname(output_file) and not path.exists(path.dirname(output_file)):
                    os.makedirs(path.dirname(output_file))
                    
                with open(output_file, "w") as outfile:
                    outfile.writelines(htmldiff.make_file(ref_file.readlines(), new_file.readlines(), context=True, numlines=3))

    def write_test_report(self, outdir):
        for f in self.diff_files:
            with open(path.join(self.ref_dir, f)) as ref_file, open(path.join(self.new_dir, f)) as new_file:
                output_file = path.join(outdir, f + ".diff")
                if path.dirname(output_file) and not path.exists(path.dirname(output_file)):
                    os.makedirs(path.dirname(output_file))

                with open(output_file, "w") as outfile:
                    outfile.writelines(
                            difflib.unified_diff(
                                ref_file.readlines(), new_file.readlines(),
                                path.join(self.ref_dir, f), path.join(self.new_dir, f),
                                n=3))

            if not path.exists(path.dirname(path.join(outdir, "ref", f))):
                os.makedirs(path.dirname(path.join(outdir, "ref", f)))
            shutil.copy(path.join(self.ref_dir, f), path.join(outdir, "ref", f))

            if not path.exists(path.dirname(path.join(outdir, "new", f))):
                os.makedirs(path.dirname(path.join(outdir, "new", f)))
            shutil.copy(path.join(self.new_dir, f), path.join(outdir, "new", f))
