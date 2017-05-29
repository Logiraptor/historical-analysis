

# Day of week of commit
# Time of day of commit
# 'velocity'
# number of files

import re


class Analysis(object):
    def execute(self, ctx):
        raise NotImplementedError()


class BashAnalysis(Analysis):
    def execute(self, ctx):
        output = ctx.run(self.command())
        return self.parse_result(output)

    def command(self):
        return "bash -c '{}'".format(self.bash_script())

    def bash_script(self):
        raise NotImplementedError()

    def parse_result(self, output):
        raise NotImplementedError()


class RelevantFileAnalysis(BashAnalysis):
    def __init__(self, extension):
        self.extension = extension

    def bash_script(self):
        return r"find . -not -path '*/\.*' -type f | grep {}$ | {}".format(self.extension, self.pipeline())

    def pipeline(self):
        raise NotImplementedError()


# class Pylint(RelevantFileAnalysis):
#     def __init__(self):
#         super(Pylint, self).__init__("py")

#     def pipeline(self):
#         return r"xargs pylint"

#     def parse_result(self, output):
#         match = re.match(
#             r"Your code has been rated at (?P<score>\d+(.\d+)?)/10", output)
#         return float(match.group("score"))


class FileCountAnalysis(RelevantFileAnalysis):
    def pipeline(self):
        return r"wc -l"

    def parse_result(self, output):
        return {'files': int(output.strip())}


class DiskUsageAnalysis(BashAnalysis):
    def bash_script(self):
        return "du -hc | tail -1"

    def parse_result(self, output):
        return {'file_size': output.strip()}


class LineCountAnalysis(RelevantFileAnalysis):
    def pipeline(self):
        return "xargs cat | wc -l"

    def parse_result(self, output):
        return {'lines': int(output.strip())}


class DiffSizeAnalalysis(BashAnalysis):
    def bash_script(self):
        return "git show | wc -l"

    def parse_result(self, output):
        return {'diff_size': int(output.strip())}
