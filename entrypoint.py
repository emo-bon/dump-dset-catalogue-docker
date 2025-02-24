#!/usr/bin/env python3
from logging import Logger, getLogger
from pathlib import Path

from rdflib import Graph
from rdflib.query import Result
from sema.commons.glob import getMatchingGlobPaths
from sema.harvest import Harvest

log: Logger = getLogger(__name__)


def log_directory_contents(path: Path):
    contents = getMatchingGlobPaths(path, ["*"])
    if path.exists():
        log.info(f"Contents of {path !s}")
        for content in contents:
            log.info(
                f"[{'file' if content.is_file() else ' dir'}] {content !s}"
            )
    else:
        log.info(f"{path !s} does not exist")


def _main(
    *,
    config: str = "/ddcat/config/harvest-emobon-dcat.yml",
    resultsroot: str = "/resultsroot",
) -> None:
    """Testable version of `main()` allows to pass named arguments
    rather then just take defaults for them."""

    cwd = Path(".").absolute()
    log.info(f"Current working directory: {cwd !s}")
    log_directory_contents(cwd)

    resultsroot = Path(resultsroot).absolute()
    log_directory_contents(resultsroot)

    output_file: Path = resultsroot / "emobon-dcat-dump.ttl"
    if output_file.exists():
        log.warning("output-file already exists -- will remove it")
        output_file.unlink()

    config = Path(config).absolute()
    log.info(f"Using config file: {config !s}")

    log.info("Starting harvesting")
    harvester = Harvest(config, [])
    harvester.process()
    log.info("Harvesting complete")

    harvester_result: Result = harvester.target_store.all_triples()
    log.debug(f"{harvester_result=}")
    # the harvester_result should be a list of ResultRow objects
    dump_graph = Graph()
    for row in harvester_result:
        dump_graph.add(row)

    # log the length of the graph
    log.info(f"Graph length: {len(dump_graph)}")

    if len(dump_graph):
        dump_graph.serialize(destination=str(output_file), format="turtle")
        log.info(f"Results saved to {output_file}")
    else:
        log.info("No results to write.")


def main():
    _main()  # simple use all defaults


if __name__ == "__main__":
    main()
