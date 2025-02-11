#!/usr/bin/env python3
import logging
from logging import Logger, getLogger

from rdflib import Graph
from rdflib.query import Result
from sema.harvest import Harvest
import os


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


log: Logger = getLogger(__name__)


def _main(
    config: str = "/ddcat/data/dereference_task_emobon_config.yml",
    resultsroot: str = "resultsroot",
) -> None:
    log.info("Starting harvesting")
    cwd = os.getcwd()
    log.info(f"Current working directory: {cwd}")
    log.info(f"Contents of the current working directory: {os.listdir(cwd)}")

    # Check if resultsroot and ddcat folders exist and log their contents recursively
    def log_directory_contents(path: str, folder_name: str):
        if os.path.exists(path):
            log.info(f"{folder_name} directory exists: {path}")
            for root, dirs, files in os.walk(path):
                log.info(f"Directory: {root}")
                for name in files:
                    log.info(f"File: {os.path.join(root, name)}")
                for name in dirs:
                    log.info(f"Sub-directory: {os.path.join(root, name)}")
        else:
            log.info(f"{folder_name} directory does not exist: {path}")

    log_directory_contents(resultsroot, "resultsroot")
    log.debug(f"{config=}")
    log.debug(f"{resultsroot=}")
    harvester = Harvest(config, [])
    harvester.process()
    harvester_result: Result = harvester.target_store.all_triples()
    log.debug(f"{harvester_result=}")
    # the harvester_result should be a list of ResultRow objects
    save_graph = Graph()
    for row in harvester_result:
        save_graph.add(row)

    # log the length of the graph
    log.info(f"Graph length: {len(save_graph)}")

    output_file = f"{resultsroot}/results.ttl"

    with open(output_file, "w") as f:
        f.write(
            save_graph.serialize(format="turtle", encoding="utf-8").decode("utf-8")
        )  # noqa: E501
    log.info(f"Results saved to {output_file}")
    log.info("Harvesting complete")


def main():
    _main()  # simple use all defaults


if __name__ == "__main__":
    main()
