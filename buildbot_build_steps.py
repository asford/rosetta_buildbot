#Builder imports
from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import FileDownload
from buildbot.process.properties import WithProperties
from buildbot.process.properties import Interpolate, Property, renderer

from test_support import UnitTest, IntegrationTest
from build_support import SconsCompile, DeployBuild

# Updates scons configuration.
update_scons_steps = [
    FileDownload(mastersrc="site.settings", slavedest="source/tools/build/site.settings", workdir="main"),
    ShellCommand(
      command='echo "SetOption(\'implicit_cache\', 1);Decider(\'MD5-timestamp\')" >> SConscript',
      workdir="main/source",
      haltOnFailure=True,
      description="configure", descriptionSuffix="SConscript")]

#Steps to perform a full build
full_build_steps = update_scons_steps + [
    # build for unit tests
    SconsCompile(
      build_targets=None, # Set blank build targets, otherwise default targets pulled from env.
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      haltOnFailure=True,
      description="compiling"),
    SconsCompile(
      build_cat="test",
      build_targets=None, # Set blank build targets, otherwise default targets pulled from env.
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      haltOnFailure=True,
      description="compiling", descriptionSuffix="tests"),
    SconsCompile(
      build_targets = Interpolate("%(prop:build_targets)s"),
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      haltOnFailure=True,
      description="compiling", descriptionSuffix="targets")
]

#Steps for unittesting
unittest_steps = [
    UnitTest(
      verbose=True,
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      flunkOnFailure=True,
      description="testing", descriptionSuffix="unit"),
    ShellCommand(
        command=["python", "setup.py", "nosetests"],
        workdir = "main/pyrosetta",
        flunkOnFailure=True,
        description="testing", descriptionSuffix="bindings"),
]

#Steps for integration testing
integration_steps = [
    ShellCommand(
      command=["rm", "-rf", "ref", "new"],
      workdir="main/tests/integration",
      description="clean", descriptionSuffix="integration"),
    IntegrationTest(
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/tests/integration",
      flunkOnFailure=True,
      description="run", descriptionSuffix="integration"),
    ShellCommand(
      command=["./integration_archive.py", "save", "--force", Interpolate("%(prop:integration_result_dir)s/%(prop:build_mode)s"), "ref", Interpolate("%(src::branch)s"), Interpolate("%(src::revision)s")],
      workdir="main/tests/integration",
      description="save", descriptionSuffix="integration")
]

binding_build_steps = [
    ShellCommand(
      command=[
        'source/src/python/packaged_bindings/BuildPackagedBindings.py',
        '--python_lib=python2.7',
        '--boost_lib=boost_python',
        Interpolate('--boost_path=%(prop:binding_boost_path)s'),
        Interpolate('--python_path=%(prop:binding_python_path)s'),
        '--compiler=gcc',
        Interpolate("--jobs=%(prop:slave_build_cores)s"),
        '--update',
        '--package_path=pyrosetta'],
      workdir="main",
      haltOnFailure=True,
      timeout=60*60,
      description="build", descriptionSuffix="bindings")
    ]

# Binary deployment steps
binary_deploy_steps = [
  FileDownload(mastersrc="deploy_build.py", slavedest="deploy_build.py", workdir="main"),
  DeployBuild(workdir="main")
  ]

binding_deploy_steps = [
    ShellCommand(
        command=[
          "python", "setup.py", "bdist_egg",
          "--dist-dir", Interpolate("%(prop:build_result_dir)s/%(prop:build_mode)s/%(src::branch)s/%(src::got_revision)s")],
        workdir="main/pyrosetta",
        flunkOnFailure=True,
        description="package", descriptionSuffix="bindings"),
]

clean_build_step = ShellCommand(
      command=Interpolate("%(prop:force_build_clean:#?|git clean -f -d| echo Not cleaning.)s"),
      workdir="main",
      haltOnFailure=True,
      description="clean", descriptionSuffix="build dir")

complete_full_factory = BuildFactory(
    # check out the source
    [ Git(repourl=Property("slave_repo_url"), mode='incremental', workdir="main"), clean_build_step ] +
    full_build_steps +
    binding_build_steps +
    unittest_steps +
    integration_steps)

complete_without_bindings_factory = BuildFactory(
    # check out the source
    [ Git(repourl=Property("slave_repo_url"), mode='incremental', workdir="main"), clean_build_step ] +
    full_build_steps +
    unittest_steps +
    integration_steps)

build_and_deploy_full_factory = BuildFactory(
    # check out the source
    [ Git(repourl=Property("slave_repo_url"), mode='incremental', workdir="main"), clean_build_step] + update_scons_steps +
    [ SconsCompile(
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      haltOnFailure=True,
      description="compiling", descriptionSuffix="bin")] +
    binding_build_steps +
    binary_deploy_steps +
    binding_deploy_steps)


build_and_deploy_without_bindings_factory = BuildFactory(
    # check out the source
    [ Git(repourl=Property("slave_repo_url"), mode='incremental', workdir="main"), clean_build_step] +  update_scons_steps +
    [SconsCompile(
      jobs=Interpolate("%(prop:slave_build_cores)s"),
      workdir="main/source",
      haltOnFailure=True,
      description="compiling", descriptionSuffix="bin")] +
    binary_deploy_steps
)
