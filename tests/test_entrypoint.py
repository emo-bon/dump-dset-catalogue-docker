import tempfile
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from logging import getLogger

from rdflib import Graph, URIRef
from dotenv import load_dotenv
from sema.commons.glob import getMatchingGlobPaths
from datetime import datetime
import os


log = getLogger(__name__)


def load_source(modname, filename):
    loader = SourceFileLoader(modname, filename)
    spec = spec_from_file_location(modname, filename, loader=loader)
    module = module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


def unique_values_of(g: Graph, p: str) -> set:
    return set(str(o) for o in g.objects(predicate=URIRef(p)))


def verify_build(outdir: Path, config: Path, start_ts: float) -> None:
    # verify results
    resultfiles = getMatchingGlobPaths(
        outdir, includes=["*.ttl"], makeRelative=False
    )
    assert len(resultfiles) == 1

    # check that result file
    rf: Path = resultfiles[0]
    assert rf.exists()
    assert rf.stat().st_size > 0
    # file lastmod should be more recent then the start_ts
    assert rf.stat().st_mtime > start_ts

    # non zero output is there, lets parse ...
    g: Graph = Graph().parse(str(rf), format="ttl")

    # result parses as ttl, lets do some extra tests ...
    # 1. we expect at least csv and ttl files to be declared
    found_enc = unique_values_of(g, "https://schema.org/encodingFormat")
    log.debug(f"{found_enc=}")
    expected_encodings = {"text/turtle", "text/csv"}
    assert found_enc >= expected_encodings
    # 2. we expect at least some conformity-declarations
    found_conf = unique_values_of(g, "http://purl.org/dc/terms/conformsTo")
    log.debug(f"{found_conf=}")
    expected_encodings = {
        "https://w3id.org/ro/crate/1.1",
        "https://data.emobon.embrc.eu/observatory-profile/latest",
    }
    assert found_conf >= expected_encodings

    # todo more assertions to make sure we have decent dcat entries
    # also: we have a tests/data/*results.ttl on board to compare with
    # but are not actively doing so
    # unsure if we should (as exact content may change over time)
    # but at least some extra content-checks could be made
    # - minimum number of datasets?
    # - conformity of datasets to profiles? --> at least have all profiles?
    # - ...


def test_cli():
    entrypoint = load_source("entrypoint", "entrypoint.py")
    mainfn: callable = entrypoint._main
    assert mainfn
    root = Path(entrypoint.__file__).parent.absolute()
    config = root / "config/harvest-emobon-dcat.yml"

    def build_and_verify(outdir: str | Path):
        outdir = Path(outdir)  # ensure Path type
        ts: float = datetime.now().timestamp()
        mainfn(
            resultsroot=outdir,
            config=config,
        )
        verify_build(outdir, config, ts)

    load_dotenv()
    tmpdir = os.getenv("TEST_OUTFOLDER")
    if tmpdir:
        tmpdir = Path(tmpdir)
        log.info(
            f"Configured outfolder {tmpdir=} "
            "allows the output to be manually verified.")
        tmpdir.mkdir(exist_ok=True, parents=True)
        build_and_verify(tmpdir)
    else:
        log.info(
            "Temporary outfolder removed at end of test. "
            "Use environment TEST_OUTFOLDER to specify a permanent one."
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            build_and_verify(tmpdir)
