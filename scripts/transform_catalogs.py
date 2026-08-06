#!/usr/bin/env python3
import argparse
import html
import logging
from datetime import datetime, timezone
from pathlib import Path
from rdflib import Graph, URIRef, Literal, RDF, Namespace

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

DCAT = Namespace("http://www.w3.org/ns/dcat#")
DCT = Namespace("http://purl.org/dc/terms/")

def parse_args():
    parser = argparse.ArgumentParser(description="Transform DCAT dump using SPARQL queries into sub-catalogs.")
    parser.add_argument("--dump", type=Path, default=Path("public/emobon-dcat-dump.ttl"), help="Input dump TTL file")
    parser.add_argument("--queries", type=Path, default=Path("queries"), help="Directory containing .rq SPARQL query files")
    parser.add_argument("--output", type=Path, default=Path("public"), help="Output directory for generated TTL files and index.html")
    return parser.parse_args()

def execute_queries(dump_file: Path, queries_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not dump_file.exists():
        log.warning(f"Dump file {dump_file} does not exist. Creating empty catalog output structure.")
        source_graph = Graph()
    else:
        log.info(f"Loading RDF graph from {dump_file}...")
        source_graph = Graph()
        source_graph.parse(dump_file, format="turtle")
        log.info(f"Loaded {len(source_graph)} triples from {dump_file}.")

    generated_catalogs = []
    
    # Track main dump if present
    if dump_file.exists():
        dump_stat = dump_file.stat()
        generated_catalogs.append({
            "filename": dump_file.name,
            "title": "Main EMO BON Dataset Catalogue Dump",
            "type": "Full Dump",
            "triples": len(source_graph),
            "size_kb": round(dump_stat.st_size / 1024, 2),
            "query_file": "N/A"
        })

    # Initialize combined master graph
    combined_graph = Graph()
    for prefix, ns in source_graph.namespaces():
        combined_graph.bind(prefix, ns)

    for triple in source_graph:
        combined_graph.add(triple)

    if queries_dir.exists():
        query_files = sorted(queries_dir.glob("*.rq"))
        log.info(f"Found {len(query_files)} query files in {queries_dir}.")

        for q_path in query_files:
            log.info(f"Executing SPARQL query from {q_path.name}...")
            query_str = q_path.read_text(encoding="utf-8")
            out_filename = f"{q_path.stem}.ttl"
            out_filepath = output_dir / out_filename

            try:
                res = source_graph.query(query_str)
                sub_graph = Graph()

                # Bind prefixes from source graph
                for prefix, ns in source_graph.namespaces():
                    sub_graph.bind(prefix, ns)

                if res.type == "CONSTRUCT":
                    for triple in res:
                        sub_graph.add(triple)
                elif res.type == "SELECT":
                    catalog_uri = URIRef(f"https://data.emobon.embrc.eu/#catalog-{q_path.stem}")
                    sub_graph.add((catalog_uri, RDF.type, DCAT.Catalog))
                    catalog_title = q_path.stem.replace("_", " ").title()
                    sub_graph.add((catalog_uri, DCT.title, Literal(f"EMO BON Catalog - {catalog_title}", lang="en")))

                    matching_datasets = set()
                    vars_in_res = res.vars if hasattr(res, 'vars') and res.vars else []
                    
                    # Check if 'dataset' or 's' is among select variables
                    target_var = None
                    for v in ['dataset', 's']:
                        if v in [str(var) for var in vars_in_res]:
                            target_var = v
                            break

                    for row in res:
                        if target_var and getattr(row, target_var, None):
                            val = getattr(row, target_var)
                            if isinstance(val, URIRef):
                                matching_datasets.add(val)
                        else:
                            for val in row:
                                if isinstance(val, URIRef):
                                    matching_datasets.add(val)

                    for ds_uri in matching_datasets:
                        sub_graph.add((catalog_uri, DCAT.dataset, ds_uri))
                        # Include all triples for matched dataset
                        for s, p, o in source_graph.triples((ds_uri, None, None)):
                            sub_graph.add((s, p, o))

                sub_graph.serialize(destination=str(out_filepath), format="turtle")
                log.info(f"Saved sub-catalog to {out_filepath} with {len(sub_graph)} triples.")

                # Merge triples into combined_graph
                for triple in sub_graph:
                    combined_graph.add(triple)

                # Extract title from constructed sub_graph for the dcat:Catalog subject
                catalog_title = None
                for cat_uri in sub_graph.subjects(RDF.type, DCAT.Catalog):
                    for _, _, title_val in sub_graph.triples((cat_uri, DCT.title, None)):
                        catalog_title = str(title_val)
                        break
                    if catalog_title:
                        break

                if not catalog_title:
                    for _, _, title_val in sub_graph.triples((None, DCT.title, None)):
                        catalog_title = str(title_val)
                        break

                if not catalog_title:
                    catalog_title = q_path.stem.replace("_", " ").title()

                stat = out_filepath.stat()
                generated_catalogs.append({
                    "filename": out_filename,
                    "title": catalog_title,
                    "type": f"Sub-Catalog ({res.type})",
                    "triples": len(sub_graph),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "query_file": q_path.name
                })

            except Exception as e:
                log.error(f"Error processing query {q_path.name}: {e}")
    else:
        log.warning(f"Queries directory {queries_dir} does not exist.")

    # Create master combined file linking sub-catalogs
    if len(combined_graph):
        main_catalog_uri = URIRef("https://data.emobon.embrc.eu")
        for cat_uri in combined_graph.subjects(RDF.type, DCAT.Catalog):
            if cat_uri != main_catalog_uri:
                combined_graph.add((main_catalog_uri, DCAT.catalog, cat_uri))

        combined_filepath = output_dir / "emobon-dcat-combined.ttl"
        log.info(f"Deduplicating and serializing combined master catalog to {combined_filepath}...")
        combined_graph.serialize(destination=str(combined_filepath), format="turtle")
        combined_stat = combined_filepath.stat()
        log.info(f"Combined master catalog saved with {len(combined_graph)} unique triples ({round(combined_stat.st_size / 1024, 2)} KB).")

        generated_catalogs.append({
            "filename": combined_filepath.name,
            "title": "EMO BON Combined Master Catalogue",
            "type": "Combined (Dump + Sub-Catalogs)",
            "triples": len(combined_graph),
            "size_kb": round(combined_stat.st_size / 1024, 2),
            "query_file": "Merged"
        })

    # Generate HTML index
    generate_index_html(output_dir / "index.html", generated_catalogs)


def generate_index_html(html_file: Path, catalogs: list):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    rows_html = ""
    for cat in catalogs:
        fname = html.escape(cat["filename"])
        title = html.escape(cat["title"])
        ctype = html.escape(cat["type"])
        query_file = html.escape(cat["query_file"])
        triples = cat["triples"]
        size_kb = cat["size_kb"]
        
        rows_html += f"""
        <tr>
            <td><strong><a href="{fname}" download>{fname}</a></strong></td>
            <td>{title}</td>
            <td><span class="badge">{ctype}</span></td>
            <td><code>{query_file}</code></td>
            <td>{triples:,}</td>
            <td>{size_kb} KB</td>
            <td><a href="{fname}" class="btn">Download Turtle</a></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMO BON DCAT Dataset Catalogues</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --accent-color: #38bdf8;
            --accent-hover: #0284c7;
            --border-color: #334155;
            --badge-bg: #0369a1;
        }}
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }}
        h1 {{
            color: var(--accent-color);
            margin: 0 0 0.5rem 0;
            font-size: 2.2rem;
        }}
        p.subtitle {{
            color: var(--text-muted);
            margin: 0;
            font-size: 1.1rem;
        }}
        .meta-info {{
            margin-top: 1rem;
            font-size: 0.9rem;
            color: var(--text-muted);
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 1rem 1.25rem;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background-color: rgba(15, 23, 42, 0.6);
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        tr:hover td {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            background: var(--badge-bg);
            color: #fff;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        code {{
            background: rgba(0,0,0,0.3);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.85rem;
        }}
        .btn {{
            display: inline-block;
            background: var(--accent-color);
            color: #0f172a;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85rem;
            transition: background 0.2s ease;
        }}
        .btn:hover {{
            background: var(--accent-hover);
            color: #fff;
            text-decoration: none;
        }}
        footer {{
            margin-top: 3rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>EMO BON DCAT Catalogues</h1>
            <p class="subtitle">Harvested dataset catalogues and SPARQL-derived sub-catalogues published as static Turtle (.ttl) files.</p>
            <div class="meta-info">
                <span>Last updated: <strong>{now_utc}</strong></span>
            </div>
        </header>
        <main>
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Title</th>
                            <th>Type</th>
                            <th>Query File</th>
                            <th>Triples</th>
                            <th>Size</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html if rows_html else '<tr><td colspan="7" style="text-align:center;">No catalog files available.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </main>
        <footer>
            <p>EMO BON Dataset Catalogue Dump Pipeline &bull; Published via GitHub Pages</p>
        </footer>
    </div>
</body>
</html>
"""
    html_file.write_text(html_content, encoding="utf-8")
    log.info(f"Generated index.html at {html_file}")

if __name__ == "__main__":
    args = parse_args()
    execute_queries(args.dump, args.queries, args.output)
