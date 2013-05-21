from buildbot.steps.shell import Compile
from buildbot.status.results import SUCCESS, FAILURE
from buildbot.process.properties import Interpolate, Property

class SconsCompile(Compile):

    def __init__(self, build_target = None, build_mode = None, build_cat = None, build_extras = None, jobs=None, **kwargs):

        command = ["scons"]

        if build_mode:
            command.extend(["mode=%s" % build_mode])
        else:
            command.extend([Interpolate("%(prop:build_mode:#?|mode=|)s%(prop:build_mode)s")])

        if build_cat:
            command.extend(["cat=%s" % build_cat])
        else:
            command.extend([Interpolate("%(prop:build_cat:#?|cat=|)s%(prop:build_cat)s")])

        if build_extras:
            command.extend(["extras=%s" % build_extras])
        else:
            command.extend([Interpolate("%(prop:build_extras:#?|extras=|)s%(prop:build_extras)s")])

        if jobs:
            command.extend(["-j", str(jobs)])

        if build_target:
            command.extend([build_target])

        Compile.__init__(self, command=command, **kwargs) 
