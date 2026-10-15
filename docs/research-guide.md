# Bio Semantic Parser Research Guide

[Project overview](../README.md)

Bio Semantic Parser is a research prototype for extracting candidate biomedical
assertions from study metadata and research text. The main workflow combines
[Gene Expression Omnibus (GEO)](https://www.ncbi.nlm.nih.gov/geo/) data retrieval,
MedCAT concept annotation, and LLM-based relation extraction. It produces
predicate expressions that can be converted to MeTTa for further knowledge
representation experiments.

The research objective is to study how information from biomedical datasets and
publications can be represented for symbolic reasoning. AtomSpace integration,
PLN inference, and evaluation of downstream reasoning remain future work.

## Experimental workflows

### GEO studies and linked abstracts

The main entry point is a GEO Series accession (`GSE`), representing a study.
Its GEO Sample accessions (`GSM`) identify individual samples.

1. Retrieve the study and sample metadata from GEO and cache the study locally.
2. Identify a linked PubMed article and retrieve its abstract.
3. Clean and chunk the abstract, annotate biomedical concepts with MedCAT, and
   use an LLM to extract relationships as predicates.
4. Extract and refine predicates from the study and sample metadata through a
   separate LLM prompting workflow.
5. Convert selected predicates to MeTTa through a separate conversion endpoint.

The interface also supports inspecting a selected GSM table. The preview shows
its first 15 rows; table-to-MeTTa conversion uses 15 randomly sampled rows and
currently requires at least 15 rows. Some GSM records have no table data. These
are displayed as empty results. This path does not implement general extraction
of supplementary tables from arbitrary paper files.

### Full research papers

A separate command-line prototype searches arXiv, downloads PDFs, extracts and
chunks their text, and uses an LLM to produce relationship triples in `.metta`
files. If PDF text extraction fails, it uses the paper summary. This workflow is
independent of the GEO API and does not use MedCAT.

## Representation

The GEO workflow uses FOL-like predicate expressions. For example, the converter
maps the following predicate to a MeTTa expression:

```text
regulates(TP53, apoptosis)
```

```metta
(regulates TP53 apoptosis)
```

The converter supports unary and binary predicates and applies basic syntax
checks. These checks do not establish biomedical correctness or compatibility
with a particular reasoning engine. The arXiv prototype currently writes atoms
in `(subject predicate object)` order; its output needs alignment with the
predicate-first GEO output before combining the two workflows.

## Running an experiment with Docker

Use Docker Engine or Docker Desktop with the Docker Compose plugin. Pipeline
runs require network access to the data sources and the selected LLM provider.

### Configuration

```bash
git clone https://github.com/iCog-Labs-Dev/bio-semantic-parser.git
cd bio-semantic-parser
cp -n Backend/.env.example Backend/.env
```

Edit `Backend/.env` using the [environment example](../Backend/.env.example). Select
`AI_PROVIDER=openai` or `AI_PROVIDER=gemini`, and supply the corresponding API
key. The model names in the example are repository defaults; select a model
available to your account.

| Variable | Purpose | Default |
| --- | --- | --- |
| `AI_PROVIDER` | LLM provider: `openai` or `gemini` | `openai` |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | Credential for the selected provider | Must be supplied |
| `OPENAI_MODEL` / `GEMINI_MODEL` | Model used for extraction | See environment example |
| `NCBI_API_KEY` | Optional credential for NCBI E-utilities | Empty |
| `PUBLIC_HOST` | Server IP address or hostname reachable from the browser | `localhost` |
| `BACKEND_PORT` | Published backend port | `8010` |
| `FRONTEND_PORT` | Published interface port | `3030` |
| `MEDCAT_PORT` | Published MedCAT port | `5000` |

For access from another computer, set `PUBLIC_HOST` to the server's IP address or
hostname, without a scheme or port. Compose derives the browser's HTTP and
WebSocket API URLs from `PUBLIC_HOST` and `BACKEND_PORT`. Container ports and
internal service addresses remain fixed when published ports change.

Docker deployment uses `Backend/.env` for configuration. An existing
`frontend/.env` is used only when running the frontend outside Docker. When
updating an existing deployment, add the host and port settings to your current
`Backend/.env`; the copy command above preserves existing files.

### Start the services

```bash
cd Backend
mkdir -p models data
docker compose up -d --build
docker compose ps
```

The services run in the background and use restart policies. On first startup,
MedCAT downloads its example models into `Backend/models`; the backend waits for
MedCAT to become healthy. MedCAT is pinned to service version `v1.1.1` to match
the downloaded model format, with `en_core_web_md` as its spaCy model. Its image
uses `linux/amd64`, with Docker emulation on ARM64 hosts.

With the default settings, open the interface at `http://localhost:3030` and the
API documentation at `http://localhost:8010/docs`. For remote access, substitute
your configured host and ports. Both the interface and backend ports must be
reachable from the browser. The interface runs the React development server;
the supplied setup serves HTTP and WebSocket traffic directly.

### Inspect and update a run

Run these commands from `Backend`:

```bash
docker compose logs -f medcat-service fastapi-backend frontend
```

Press `Ctrl+C` to leave the log stream without stopping the containers. To stop
the experiment's services:

```bash
docker compose stop
```

After changing the host or port settings, run `docker compose up -d` to recreate
the affected containers. A plain restart does not apply new environment values
or port mappings. After changing frontend code, rebuild that service:

```bash
docker compose up -d --build --no-deps frontend
```

## API usage

The API documentation at `/docs` describes the current request parameters.

| Method | Path | Purpose |
| --- | --- | --- |
| WebSocket | `/ws/{client_id}` | Receive progress messages and intermediate results |
| POST | `/process` | Run the GEO workflow using `gse_id` and `client_id` query parameters |
| POST | `/convert_fol_to_metta` | Convert a plain-text predicate block to MeTTa |
| POST | `/get_gsm` | Preview a sample table using `gse_id` and `gsm_id` |
| POST | `/gsm_to_metta` | Convert sampled table rows using `gse_id` and `gsm_id` |

For programmatic use of `/process`, establish the WebSocket connection first
and use the same `client_id` in the POST request. Intermediate results arrive
over the socket; the POST response is an acknowledgement rather than the
extracted dataset.

## Local development

The backend Docker image uses Python 3.10. To run the backend locally, first
create `Backend/.env` as above, then install the dependencies in a virtual
environment:

```bash
cd Backend
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8010
```

MedCAT must be running separately for abstract extraction. Set `MEDCAT_URL` in
`Backend/.env` to its reachable `/api/process` endpoint, including the published
MedCAT port. Compose overrides this value with its internal service address when
running the backend in Docker. Choose an available Uvicorn port and configure
the local frontend to match it.

For the frontend, use Node.js 24 and follow the
[frontend development instructions](../frontend/README.md). Copy
`frontend/.env.example` to `frontend/.env`, set its backend HTTP and WebSocket
URLs, and run `npm ci` followed by `npm start` from `frontend`.

### Run the full-paper prototype

From `Backend`, with the virtual environment active and provider credentials in
`.env`:

```bash
python -m app.services.full_paper_semantic_parsing \
  --topic "cancer immunotherapy" --max-papers 1
```

Outputs are written to `Backend/output/` by default. Use `--paper-title` instead
of `--topic` to supply a paper title as the search query, and `--output-dir` to
choose an output directory.

## Reproducibility and limitations

- Record the repository commit, study and sample accessions, LLM provider and
  model, prompts, and dependency versions with each experimental result. Retain
  the source inputs and generated assertions for review.
- Table conversion samples rows without a fixed random seed, so its output may
  differ from the displayed preview and between runs. LLM responses may also
  vary between calls or provider model revisions.
- The main GEO workflow requires a linked PubMed article. Missing articles,
  empty sample tables, and unavailable external services limit which studies
  can be processed.
- Python dependencies are not pinned to exact versions. The frontend includes
  an npm lockfile, and the MedCAT service image is version-pinned.
- The repository does not yet contain a benchmark establishing biomedical
  extraction accuracy or downstream reasoning utility. Generated assertions
  require evaluation beyond the available syntax checks.

## Verification

Deployment checks exercise port configuration and model startup behavior with
mock downloads. From the repository root, with Python and the Docker Compose
CLI available:

```bash
python3 -m unittest discover -s Backend/app/tests/unit -p test_deployment.py -v
```

For frontend regression tests and a production build, use the local frontend
environment described above:

```bash
cd frontend
CI=true npm test -- --watchAll=false --runInBand
npm run build
```

These checks cover software behavior. They do not evaluate extraction quality
or replace a live GEO, MedCAT, and LLM experiment.

The interface reports request failures beside the affected extraction, sample,
or MeTTa conversion, with a retry action and collapsed technical details.
Results already received remain available after a failure. If the progress
connection drops, use **Reconnect**; this does not restart a running request or
recover missed updates. A finished request without complete progress updates is
marked as potentially incomplete. On HTTP deployments where clipboard access
is unavailable, select and copy the generated code manually.

For a manual table-preview check, try `GSE12277` and `GSM308237`: the
[GEO sample record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM308237)
contains an expression table. For an empty-table case, `GSE183947` and
[`GSM5574685`](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM5574685)
have no sample-level SOFT table rows. The current preview reads these rows;
it does not load separate SRA or supplementary datasets.

