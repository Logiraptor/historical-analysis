
import docker


def main():
    image = "repo"
    user_cmd = "find . | grep -v git | xargs cat | wc -l"

    client = docker.from_env()

    runner = Runner(client, image, [
        LineCountAnalyzer(),
        DiskUsageAnalyzer(),
    ])
    runner.analyze()


class SimpleCollector:
    def init(self):
        return []

    def process(self, prev, output):
        return prev + [output.strip()]


class DiskUsageAnalyzer(SimpleCollector):
    def command(self, rev):
        return "du -hc | tail -1"


class LineCountAnalyzer(SimpleCollector):
    def command(self, rev):
        return "find . | grep -v git | xargs cat | wc -l"


class Runner:
    def __init__(self, client, image, analyzers):
        self.client = client
        self.image = image
        self.analyzers = analyzers

    def analyze(self):
        rev_list = self._run_on_image(
            "git rev-list --reverse HEAD"
        ).split("\n")

        outputs = []

        cons = []
        for an in self.analyzers:
            output = reduce(self.process(an), rev_list, an.init())
            outputs.append(output)

        for output in outputs:
            print output

    def process(self, analyzer):
        def inner(prev, rev):
            cmd = self._format_user_cmd(rev, analyzer.command(rev))
            output = self._run_on_image(cmd)
            return analyzer.process(prev, output)

        return inner

    def _format_user_cmd(self, rev, cmd):
        return "/bin/bash -c 'git reset --hard {} > /dev/null && {}'".format(rev, cmd)

    def _run_on_image(self, cmd, **kwargs):
        return self.client.containers.run(self.image, command=cmd, **kwargs)


if __name__ == '__main__':
    main()
