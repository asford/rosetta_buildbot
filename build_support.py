from buildbot.steps.shell import Compile, ShellCommand
from buildbot.status.results import SUCCESS, FAILURE
from buildbot.process.properties import Interpolate, Property, renderer
from buildbot.interfaces import IRenderable

from zope.interface import implements

from twisted.internet import defer
from twisted.python.reflect import accumulateClassList

class DeployBuild(ShellCommand):
    """Execute build deploy command."""
    def __init__(
            self,
            target_directory = Interpolate("%(prop:build_result_dir)s"),
            force=True,
            build_name=None,
            build_targets = Interpolate("%(prop:build_targets)s"),
            build_mode = Interpolate("%(prop:build_mode)s"),
            build_extras = Interpolate("%(prop:build_extras)s"),
            link_current_build = Property("link_current_build", default=False),
            **kwargs):

        ShellCommand.__init__(
            self,
            command=BuildCommandRenderer(
               target_directory,
               force,
               build_name,
               build_targets,
               build_mode,
               build_extras,
               link_current_build
            ),
            **kwargs)

class BuildCommandRenderer:
    implements(IRenderable)
    renderables = ["build_targets", "build_mode", "build_extras", "force", "target_directory", "link_current_build"]

    def __init__(self, target_directory, force, build_name, build_targets, build_mode, build_extras, link_current_build):
        self.target_directory = target_directory
        self.force = force
        self.build_name = build_name
        self.build_targets = build_targets
        self.build_mode = build_mode
        self.build_extras = build_extras
        self.link_current_build = link_current_build

    def make_command(self, _):
        command = ["python", "deploy_build.py"]

        if self.build_mode:
            command.extend(["--mode", self.build_mode])

        if self.build_extras:
            command.extend(["--extras", self.build_extras])

        if self.force:
            command.append("--force")

        if self.link_current_build:
            command.extend(["--link_current"])

        if self.build_name:
            command.extend(["--build_name", self.build_name])
        command.append(self.target_directory)

        def split_targets(t):
            if isinstance(t, basestring):
                return t.split(" ")
            else:
                return t

        if self.build_targets:
            command.extend(split_targets(self.build_targets))

        return command

    def getRenderingFor(self, props):
        renderables = []
        accumulateClassList(self.__class__, 'renderables', renderables)

        def setRenderable(res, attr):
            setattr(self, attr, res)

        dl = []
        for renderable in renderables:
            d = props.render(getattr(self, renderable))
            d.addCallback(setRenderable, renderable)
            dl.append(d)
        dl = defer.gatherResults(dl)

        dl.addCallback(self.make_command)
        return dl

class SconsCompile(Compile):
    def __init__(
            self,
            build_targets = Interpolate("%(prop:build_targets)s"),
            build_mode = Interpolate("%(prop:build_mode)s"),
            build_cat = Interpolate("%(prop:build_cat)s"),
            build_extras = Interpolate("%(prop:build_extras)s"),
            jobs = None,
            **kwargs):

        Compile.__init__(
            self,
            command=SconsCommandRenderer(
               build_targets,
               build_mode,
               build_cat,
               build_extras,
               jobs),
            **kwargs)

class SconsCommandRenderer:
    implements(IRenderable)

    renderables = ["build_targets", "build_mode", "build_cat", "build_extras", "build_jobs"]

    def __init__(self, build_targets, build_mode, build_cat, build_extras, build_jobs):
        self.build_targets = build_targets
        self.build_mode = build_mode
        self.build_cat = build_cat
        self.build_extras = build_extras
        self.build_jobs = build_jobs

    def make_command(self, _):
        command = ["scons"]

        if self.build_mode:
            command.append("mode=%s" % self.build_mode)

        if self.build_cat:
            command.append("cat=%s" % self.build_cat)

        if self.build_extras:
            command.append("extras=%s" % self.build_extras)

        if self.build_jobs:
            command.extend(["-j", self.build_jobs])

        def split_targets(t):
            if isinstance(t, basestring):
                return t.split(" ")
            else:
                return t

        if self.build_targets:
            command.extend(split_targets(self.build_targets))

        return command

    def getRenderingFor(self, props):
        renderables = []
        accumulateClassList(self.__class__, 'renderables', renderables)

        def setRenderable(res, attr):
            setattr(self, attr, res)

        dl = []
        for renderable in renderables:
            d = props.render(getattr(self, renderable))
            d.addCallback(setRenderable, renderable)
            dl.append(d)
        dl = defer.gatherResults(dl)

        dl.addCallback(self.make_command)
        return dl
