
import docker


def main():
    image = "repo"
    user_cmd = "find . | grep -v git | xargs cat | wc -l"

    client = docker.from_env()

    runner = Runner(client, image, user_cmd)
    runner.analyze()


class Runner:
    def __init__(self, client, image, user_cmd):
        self.client = client
        self.image = image
        self.user_cmd = user_cmd

    def analyze(self):
        rev_list = self._run_on_image(
            "git rev-list --reverse HEAD"
        ).split("\n")

        print rev_list

        cons = []
        for rev in rev_list:
            cmd = self._format_user_cmd(rev)
            con = self._run_on_image(cmd, detach=True)
            cons.append(con)

        for c in cons:
            c.reload()
            print c.logs()

    def _format_user_cmd(self, rev):
        return "/bin/bash -c 'git reset --hard {} && {}'".format(rev, self.user_cmd)

    def _run_on_image(self, cmd, **kwargs):
        return self.client.containers.run(self.image, command=cmd, **kwargs)


if __name__ == '__main__':
    main()
