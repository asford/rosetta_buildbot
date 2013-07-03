#!/usr/bin/env python
import os
from os import path
import shutil

import re
import logging
logging.basicConfig(level=logging.DEBUG)

import subprocess
import tempfile

def resolve_build_drop_directory( target_directory, branch = None, revision = None, mode = None, extras = None, force_build_name=None):
    """Generate build drop directory, resolving source and build parameters as needed."""
    if branch is None:
        branch = subprocess.check_output('git rev-parse --abbrev-ref HEAD'.split(" ")).strip()
    if revision is None:
        revision = subprocess.check_output('git rev-parse HEAD'.split(" ")).strip()

    if force_build_name:
        build_type_name = force_build_name
    else:
        build_type_name = []
        if mode:
            build_type_name.append(mode)

        if extras:
            build_type_name.append(extras)

        if build_type_name:
            build_type_name = "_".join(build_type_name)
        else:
            build_type_name = "default"

    return path.join(target_directory, build_type_name, branch, revision)

def perform_test_build(rosetta_root, targets = None, mode = None, extras = None):
    """Perform no-op scons build of the given build targets, generating a tree of build dependencies."""
    command = ["scons", "--tree=prune,derived", "-n"]
    
    if mode:
        command.append("mode=%s" % mode)
    if extras:
        command.append("extras=%s" % extras)
    
    command.extend(targets)

    logging.info("Beginning archive test build: %s", " ".join(command))
    build_result = subprocess.check_output(command, cwd=path.join(rosetta_root, "source"), universal_newlines=True)

    logging.debug("Build result:\n%s", build_result)

    for t in targets:
        if not re.search("`%s' is up to date." % t, build_result):
            logging.error("Target not up to date in scons test build: %s", t)

    return build_result

def extract_build_products(scons_tree_lines):
    """Process tree of build dependencies to extract all binary and library targets."""
    build_product_pattern=re.compile("(?<=\+-)build.*")
    object_file_pattern=re.compile("\.(os|o)$")
    library_file_pattern=re.compile("\.so$")
    
    library_files = set()
    binary_files = set()

    for l in scons_tree_lines:
        build_product_match = build_product_pattern.search(l)
        if not build_product_match:
            continue

        if object_file_pattern.search(l, build_product_match.start(), build_product_match.end()):
            continue

        if library_file_pattern.search(l, build_product_match.start(), build_product_match.end()):
            library_files.add(build_product_match.group())
        else:
            binary_files.add(build_product_match.group())
    
    return binary_files, library_files

def get_bin_name(build_binary):
    """Convert binary path to base name, strips off additional build parameters added to binary name."""
    binary_basename = path.basename(build_binary)
    if not binary_basename.find("."):
        return binary_basename
    else:
        return binary_basename[:binary_basename.find(".")]

def get_lib_name(build_library):
    """Convert library path to base name."""
    library_basename = path.basename(build_library)
    return library_basename

def archive_build_products(rosetta_root, target_bins, target_libs, target_directory):
    """Copy binaries, libraries, and database into target directory."""
    database_drop_dir = path.join(target_directory, "database")
    bin_drop_dir = path.join(target_directory, "bin")
    lib_drop_dir = path.join(target_directory, "lib")

    os.makedirs(bin_drop_dir)
    for b in target_bins:
        b_source = path.join(rosetta_root, "source", b)
        b_target = path.join(bin_drop_dir, get_bin_name(b))
        logging.info("Archive bin: %s %s", b_source, b_target)
        #Copy file with stripped filename and then symlink under old name
        shutil.copy(b_source, b_target)

        b_link_target = path.join(bin_drop_dir, path.basename(b))
        logging.info("Linking bin: %s %s", get_bin_name(b), b_link_target)
        os.symlink(get_bin_name(b), b_link_target)

    os.makedirs(lib_drop_dir)
    for l in target_libs:
        l_source = path.join(rosetta_root, "source", l)
        l_target = path.join(lib_drop_dir, get_lib_name(l))
        logging.info("Archive lib: %s %s", l_source, l_target)
        shutil.copy(l_source, l_target)

    source_database = path.join(rosetta_root, "database") 
    logging.info("Archive database: %s %s", source_database, database_drop_dir)
    shutil.copytree(source_database, database_drop_dir)

def setup_build_products(rosetta_root, drop_directory, build_type = None, test_binary = None):
    """Execute single rosetta binary to setup rosetta database.
    
        rosetta_root - Rosetta main root directory.
        drop_directory - Archived drop directory to search for bin & database.
        build_type - 'mpi' if build requires mpirun, else None.
        test_binary - Binary to execute, resolves score_jd2, rosetta_scripts, or relax if None.
    """
    candidate_binaries = ["score_jd2", "rosetta_scripts", "relax"]
    if test_binary:
        candidate_binaries.insert(0, test_binary)

    tmpdir = tempfile.mkdtemp()
    
    try:
        test_binary = None
        for c in candidate_binaries:
            c_full = path.join(drop_directory, "bin", c)
            if path.exists(c_full):
                test_binary = c_full
                break

        if not test_binary:
            logging.warning("Unable to resolve test binary from candidate binaries: %s", candidate_binaries)
            return

        test_command = []

        if build_type=="mpi":
            try:
                mpi_prefix = re.search(
                        "(.*)bin/mpirun",
                        subprocess.check_output("which mpirun", shell=True)).group(1)
            except subprocess.CalledProcessError:
                logging.warning("setup_build_products unable to resolve mpirun executable for mpi build.")
                return

            test_command.extend(["mpirun", "--prefix", mpi_prefix])
        elif build_type:
            logging.warning("Unrecognized setup_build_products build type: %s", build_type)

        test_command.extend([test_binary, "-s", path.join(rosetta_root, "source/test/core/io/test_in.pdb")])

        logging.info("Executing test binary to prepare target database: %s", test_command)
        subprocess.call(test_command, cwd=tmpdir)
	
        if build_type=="mpi":
            logging.info("Updating mpi database permissions: %s", test_command)
            subprocess.call("chmod a+r %s/database/rotamer/ExtendedOpt1-5/*" % drop_directory, shell=True, cwd=tmpdir)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Process scons build tree.")
    parser.add_argument("target_directory")
    parser.add_argument("targets", nargs="+")
    parser.add_argument("--mode", default=None)
    parser.add_argument("--extras", default=None)
    parser.add_argument("--branch", default=None)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--build_name", default=None)
    parser.add_argument("--force", default=False, action='store_true')

    args = parser.parse_args()

    rosetta_root = subprocess.check_output("git rev-parse --show-toplevel".split(" ")).strip()
    logging.info("Resolved root directory: %s", rosetta_root)
    if not rosetta_root:
        raise ValueError("Unable to resolve Rosetta root directory.")

    drop_directory = resolve_build_drop_directory(args.target_directory, args.branch, args.revision, args.mode, args.extras, args.build_name)
    logging.info("Resolved drop directory: %s", drop_directory)

    if path.exists(drop_directory):
        logging.warning("Existing drop directory: %s", drop_directory)
        if args.force:
            logging.warning("Removing existing drop directory: %s", drop_directory)
            shutil.rmtree(drop_directory, ignore_errors=True)
        else:
            raise ValueError("Drop directory already exists: %s" % drop_directory)

    build_result = perform_test_build(rosetta_root, args.targets, args.mode, args.extras)

    bins, libs = extract_build_products(build_result.split("\n"))

    archive_build_products(rosetta_root, bins, libs, drop_directory)

    build_type = None
    if args.extras and re.search("mpi", args.extras):
        build_type = "mpi"

    setup_build_products(rosetta_root, drop_directory, build_type = build_type)
