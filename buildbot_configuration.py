slave_list = \
    [("big%s" % big, {"max_builds" : 3, "properties" : {"slave_build_cores" : 20}}) for big in xrange(1,4)] + \
    [ ("dig%s" % dig, {"max_builds" : 1, "properties" : {"slave_build_cores" : 20}}) for dig in xrange(1, 25)] + \
    [("buildbot0",  {"max_builds" : 1, "properties" : {"slave_build_cores" : 6}})]

master_repo_url = 'ssh://git@github.com/RosettaCommons/main.git'
slave_repo_url  = 'ssh://git@github.com/RosettaCommons/main.git'
reference_repo = '/lab/gos/RosettaCommons/main.git'

target_builds = ["release"]

target_branches = {
  "master"                      : {"extras" : ""},
  "asford/indexed_structure_store"     : {"extras" : "hdf5"},
  "matdes/master"     : {"extras" : ""}
}

integration_result_dir = "/work/buildbot/integration_results"
build_result_dir = "/work/buildbot/builds"

binding_python_path = "/work/buildbot/buildbot_env"
binding_boost_path = "/work/buildbot/opt"
