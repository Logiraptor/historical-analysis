import collections
import sys
import re
import pandas

Revision = collections.namedtuple("Revision", [
    "git_hash", "date", "description", "author"
])


class Context(object):
    def __init__(self, image, client):
        self.image = image
        self.client = client

    def run(self, cmd, **kwargs):
        return self.client.containers.run(self.image, cmd, **kwargs)


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
                sys.stdout.flush()

                result = analyzer.execute(Context(image_tag, self.client))
                row.update(result)

            self.client.images.prune({'dangling': True})
            self.client.containers.prune()
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
