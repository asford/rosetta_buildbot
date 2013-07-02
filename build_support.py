from buildbot.steps.shell import Compile
from buildbot.status.results import SUCCESS, FAILURE
from buildbot.process.properties import Interpolate, Property, renderer
from buildbot.interfaces import IRenderable

from zope.interface import implements

from twisted.internet import defer
from twisted.python.reflect import accumulateClassList

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
