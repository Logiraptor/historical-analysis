"""
This module performs analysis on git repos.
"""

import collections
import re
import docker
import pandas
import time


def main():
    image = "hist"

    client = docker.from_env()

    runner = Runner(client, image, [
        LineCountAnalyzer(),
        DiskUsageAnalyzer(),
    ])

    results = runner.analyze()
    results.to_csv('output.csv')


Revision = collections.namedtuple("Revision", [
    "git_hash", "date", "description", "author"
])


class DiskUsageAnalyzer(object):
    def command(self):
        return "bash -c 'du -hc | tail -1'"

    def parse_result(self, output):
        return {'file_size': output.strip()}


class LineCountAnalyzer(object):
    def command(self):
        return "bash -c 'find . | grep -v git | xargs cat | wc -l'"

    def parse_result(self, output):
        return {'lines': int(output.strip())}


class Runner(object):
    """
    Runner is responsible for running a set of analyzers against a git repo

    """

    def __init__(self, client, image, analyzers):
        self.client = client
        self.image = image
        self.analyzers = analyzers

    def analyze(self):
        """
        analyze creates a docker image for every commit in a repo,
        then runs a set of analyzers against those images

        returns a pandas.DataFrame with the results
        """
        outputs = []
        rev_list = self.get_revision_list()

        for i, revision in enumerate(rev_list):
            image_tag = self.create_revision_container(revision)
            row = revision._asdict()
            for analyzer in self.analyzers:

                print "Running {} on commit {} ({}/{})".format(
                    type(analyzer).__name__,
                    revision.git_hash,
                    i + 1, len(rev_list))

                cmd = analyzer.command()
                output = self.client.containers.run(image_tag, cmd)
                try:
                    result = analyzer.parse_result(output)
                    row.update(result)
                except Exception as e:
                    print "Error: ", e.message

            outputs.append(row)

        return pandas.DataFrame(outputs)

    def get_revision_list(self):
        """
        get_revision_list gets a set of Revision objects from git.
        """
        rev_list = self._run_on_image(
            'git log --pretty=format:"[%H] [%ae] [%at] %s"'
        ).split("\n")

        regex = r"\[(?P<hash>[^\]]+)\] \[(?P<email>[^\]]+)\] \[(?P<timestamp>[^\]]+)\] (?P<subject>.*)"

        revisions = []
        for rev in rev_list:
            if not rev:
                continue
            match = re.match(regex, rev)
            revisions.append(Revision(
                git_hash=match.group("hash"),
                date=match.group("timestamp"),
                description=match.group("subject"),
                author=match.group("email"),
            ))

        # Skip last (blank) line
        return revisions

    def create_revision_container(self, rev):
        container = self._run_on_image(
            "git reset --hard {}".format(rev.git_hash), detach=True)
        container.commit(self.image, rev.git_hash)
        return "{}:{}".format(self.image, rev.git_hash)

    def _run_on_image(self, cmd, **kwargs):
        return self.client.containers.run(self.image, cmd, **kwargs)


if __name__ == '__main__':
    main()
