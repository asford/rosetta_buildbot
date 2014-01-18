# Buildslave list
#   name: slave name, as specified in slave configuration
#   args:
#       max_builds: maximum simultanious builds performed by slave
#       properties: build properties
#           slave_build_cores: number of cores used per build
#   build_filter: filter function used to select which builds are performed by slave
slave_list = \
    [{
        "name" : "hyak",
        "args" : {"max_builds" : 1, "properties" : {"slave_build_cores" : 20}},
    }] +\
    [{
        "name" : "buildbot",
        "args" : {
            "max_builds" : 1,
            "properties" : {
                "slave_build_cores" : 6,
                # Source prefixs by the python library and boost libraries used during build.
                "binding_python_path" : "/usr/local",
                "binding_boost_path" : "/work/buildbot/opt"
            }
        }
    }]

master_repo_url = 'ssh://git@github.com/RosettaCommons/main.git'
slave_repo_url  = 'ssh://git@github.com/RosettaCommons/main.git'

default_build_environment = "work"

build_environments = { 
        "work" : {
            ### Repository urls used by master and slave instances.
            "target_slaves" : ["buildbot"],
            # Target build types, ["release", "debug"]
            "target_builds" : ["release"],

            # Target build branches, optionally specify build extras for the branch
            "target_branches" : {
              "master"                         : {"extras" : ""},
              "asford/indexed_structure_store" : {"extras" : "hdf5"},
              "scheme/master"                  : {"extras" : ""}
            },

            # Integration test results will be delivered to this filesystem location by slaves.
            "integration_result_dir" : "/work/buildbot/integration_results",

            # Build results will be delivered to this filesystem location by slaves.
            "build_result_dir" : "/work/buildbot/builds",
            
            # Build python bindings
            "build_bindings" : True,
    }
}

all_target_branches = ["master", "asford/indexed_structure_store", "scheme/master"]
