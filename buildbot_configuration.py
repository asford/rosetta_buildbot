slave_list = [ ("big%s" % big, {"max_builds" : 3, "properties" : {"slave_build_cores" : 20}}) for big in xrange(1,4)] + [ ("dig%s" % dig, {"max_builds" : 1, "properties" : {"slave_build_cores" : 20}}) for dig in xrange(1, 25)]

master_repo_url = 'file:///work/fordas/workspace/rosetta_dev'
slave_repo_url = 'file:///work/fordas/workspace/rosetta_dev'

target_builds = ["release"]

target_branches = {
  "master"                      : {"extras" : None},
  "pyrosetta_numeric"           : {"extras" : None},
  "pyrosetta_protocols"         : {"extras" : None},
  "pyrosetta_fragment_matching" : {"extras" : None},
  "indexed_structure_store"     : {"extras" : "hdf5"}
}

integration_result_dir = "/work/fordas/buildbot/integration_results"
