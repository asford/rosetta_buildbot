from buildbot.steps.shell import ShellCommand
from buildbot.status.results import SUCCESS, FAILURE
from buildbot.process.properties import Interpolate, Property

import re

class UnitTest(ShellCommand):
    """Execute rosetta unit tests and return success or failure."""

    def __init__(self, build_mode = None, build_extras = None, jobs=None, verbose=False, **kwargs):

        command = ["test/run.py", "-d", "../database"]

        if build_mode:
            command.extend(["--mode" , build_mode])
        else:
            command.extend([Interpolate("%(prop:build_mode:#?|--mode|)s"), Interpolate("%(prop:build_mode)s")])

        if build_extras:
            command.extend(["--extras" , build_extras])
        else:
            command.extend([Interpolate("%(prop:build_extras:#?|--extras|)s"), Interpolate("%(prop:build_extras)s")])

        if jobs:
            command.extend(["-j", jobs])

        if not verbose:
            command.extend(["--mute", "all"])

        ShellCommand.__init__(self, command=command, **kwargs) 

        self.test_summary = ""
        self.tests_failed = None
        self.result = None

    def commandComplete(self, cmd):

        #Extract test summary
        test_summary = []
        tests_failed = None
        summary = False

        for l in self.getLog("stdio").readlines():
            if l.find("Unit test summary") >= 0:
                summary=True
                continue

            if l.find("End of Unit test summary") >= 0:
                summary=False
                break

            if summary:
                test_summary.append(l)

                if re.search("number tests failed:\s*(\d+)", l):
                    tests_failed = int(re.search("number tests failed:\s*(\d+)", l).groups()[0])

        self.test_summary = "".join(test_summary)
        self.tests_failed = tests_failed

        if self.tests_failed != 0:
            self.result = FAILURE
        else:
            self.result = SUCCESS

    def evaluateCommand(self, cmd):
        if cmd.didFail():
            return FAILURE
        else:
            return self.result

    def createSummary(self, log):
        self.addCompleteLog("test_summary", self.test_summary)

class IntegrationTest(ShellCommand):

    def __init__(self, build_mode = None, build_extras = None, jobs=None, **kwargs):
        command = ["./integration.py"]

        if build_mode:
            command.extend(["--mode" , build_mode])
        else:
            command.extend([Interpolate("%(prop:build_mode:#?|--mode|)s"), Interpolate("%(prop:build_mode)s")])

        if build_extras:
            command.extend(["--extras" , build_extras])
        else:
            command.extend([Interpolate("%(prop:build_extras:#?|--extras|)s"), Interpolate("%(prop:build_extras)s")])

        if jobs:
            command.extend(["-j", jobs])

        ShellCommand.__init__(self, command=command, **kwargs) 
