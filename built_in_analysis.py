

# Day of week of commit
# Time of day of commit
# 'velocity'
# number of files

import re
import docker


class Analysis(object):
    def execute(self, ctx):
        raise NotImplementedError()


class BashContext(object):
    def __init__(self, ctx):
        self.ctx = ctx

    def run(self, cmd, **kwargs):
        cmd = "bash -c '{}'".format(cmd)
        return self.ctx.run(cmd, **kwargs)

    @classmethod
    def wrap(cls, execute):
        def execute_with_bash(self, ctx):
            return execute(self, BashContext(ctx))

        return execute_with_bash


class BashAnalysis(Analysis):
    @BashContext.wrap
    def execute(self, ctx):
        output = ctx.run(self.bash_script())
        return self.parse_result(output)

    def bash_script(self):
        raise NotImplementedError()

    def parse_result(self, output):
        raise NotImplementedError()


class RelevantFileAnalysis(Analysis):
    def __init__(self, extension):
        self.extension = extension

    @BashContext.wrap
    def list_files(self, ctx):
        output = ctx.run(
            r'find . -not -path "*/\.*" -type f | grep {}$'.format(self.extension))
        return output.split(b"\n")[:-1]

    def execute(self, ctx):
        files = self.list_files(ctx)
        return self.process_files(ctx, files)

    def process_files(self, ctx, files):
        raise NotImplementedError()


class Pylint(RelevantFileAnalysis):
    def __init__(self):
        super(Pylint, self).__init__("py")

    def process_files(self, ctx, files):
        ctx = BashContext(ctx)
        file_output = " ".join(files)

        pylint_output = ctx.run("pylint {} || true".format(file_output))
        match = re.search(
            r"Your code has been rated at (?P<score>\d+(.\d+)?)/10", pylint_output)
        return {'pylint': float(match.group('score'))}


class FileNameAnalysis(RelevantFileAnalysis):
    def process_files(self, ctx, files):
        return {'filenames': files}


class FileCountAnalysis(RelevantFileAnalysis):
    def process_files(self, ctx, files):
        return {'files': len(files)}


class LineCountAnalysis(RelevantFileAnalysis):
    def process_files(self, ctx, files):
        ctx = BashContext(ctx)
        file_output = " ".join(files)
        wc_output = ctx.run("wc -l {} | tail -1".format(file_output))
        count = re.search(r"(?P<count>\d+)", wc_output).group("count")
        return {'lines': int(count)}


class DiskUsageAnalysis(BashAnalysis):
    def bash_script(self):
        return "du -hc | tail -1"

    def parse_result(self, output):
        return {'file_size': output.strip()}


class DiffSizeAnalalysis(BashAnalysis):
    def bash_script(self):
        return "git show | wc -l"

    def parse_result(self, output):
        return {'diff_size': int(output.strip())}
