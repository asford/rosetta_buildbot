# Buildslave list
#   name: slave name, as specified in slave configuration
#   args:
#       max_builds: maximum simultanious builds performed by slave
#       properties: build properties
#           slave_build_cores: number of cores used per build
#   build_filter: filter function used to select which builds are performed by slave
slave_list = \
    [{
        "name" : "big1",
        "args" : {"max_builds" : 1, "properties" : {"slave_build_cores" : 20}},
        "build_filter" : (lambda b: b.startswith("build"))
    }] +\
    [{
        "name" : "buildbot0",
        "args" : {"max_builds" : 1, "properties" : {"slave_build_cores" : 6}},
        "build_filter" : (lambda b: not b.startswith("build"))
    }]

### Repository urls used by master and slave instances.
master_repo_url = 'ssh://git@github.com/RosettaCommons/main.git'
slave_repo_url  = 'ssh://git@github.com/RosettaCommons/main.git'

# Target build types, ["release", "debug"]
target_builds = ["release"]

# Target build branches, optionally specify build extras for the branch
target_branches = {
  "master"                      : {"extras" : ""},
  "asford/indexed_structure_store"     : {"extras" : "hdf5"},
  "matdes/master"     : {"extras" : ""}
}

# Integration test results will be delivered to this filesystem location by slaves.
integration_result_dir = "/work/buildbot/integration_results"

# Build results will be delivered to this filesystem location by slaves.
build_result_dir = "/work/buildbot/builds"

# Source prefixs by the python library and boost libraries used during build.
binding_python_path = "/usr/local"
binding_boost_path = "/work/buildbot/opt"

# Build bindings in addition to core binaries
build_bindings = True
