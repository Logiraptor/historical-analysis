"""
This module performs analysis on git repos.
"""

import docker
import pandas

from analysis import Runner
from built_in_analysis import LineCountAnalysis, DiskUsageAnalysis, DiffSizeAnalalysis, FileCountAnalysis
from built_in_analysis import FileNameAnalysis
# from built_in_analysis import Pylint


def main():
    image = "hist"

    client = docker.from_env()

    runner = Runner(client, image, [
        LineCountAnalysis("py"),
        DiskUsageAnalysis(),
        DiffSizeAnalalysis(),
        FileCountAnalysis("py"),
        FileNameAnalysis("py"),
        # Pylint(),
    ])

    results = runner.analyze()
    results.to_csv('output.csv')


if __name__ == '__main__':
    main()
