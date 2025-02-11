import tempfile
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from rdflib import Graph
from sema.commons.glob import getMatchingGlobPaths


def load_source(modname, filename):
    loader = SourceFileLoader(modname, filename)
    spec = spec_from_file_location(modname, filename, loader=loader)
    module = module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


def test_cli():
    entrypoint = load_source("entrypoint", "entrypoint.py")
    assert entrypoint._main
    root = Path(entrypoint.__file__).parent

    def build_and_verify(outdir: Path) -> None:
        entrypoint._main(
            resultsroot=root / "tests/data",
            config=root / "tests/data/dereference_task_emobon_config.yml",
        )
        # verify results
        resultfiles = getMatchingGlobPaths(
            root / "tests/data", includes=["*.ttl"], makeRelative=False
        )
        assert len(resultfiles) == 1
        # try parsing the ttl files too
        for rf in resultfiles:
            assert rf.exists()
            assert rf.stat().st_size > 0
            Graph().parse(str(rf), format="ttl")

    # tmpdir = Path("/tmp/test_ddat")
    # tmpdir.mkdir(exist_ok=True, parents=True)
    # build_and_verify(tmpdir)
    with tempfile.TemporaryDirectory() as tmpdir:
        build_and_verify(Path(tmpdir))
