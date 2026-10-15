# Bio Semantic Parser

A research prototype for extracting biomedical information from
[Gene Expression Omnibus (GEO)](https://www.ncbi.nlm.nih.gov/geo/) study metadata
and PubMed abstracts, using MedCAT and LLMs to produce predicates and MeTTa
representations. A separate prototype processes full papers from arXiv.

The current work focuses on knowledge extraction and representation. AtomSpace
integration and PLN reasoning remain planned research stages.

## Quick start

Requires Docker with the Docker Compose plugin.

```bash
git clone https://github.com/iCog-Labs-Dev/bio-semantic-parser.git
cd bio-semantic-parser
cp -n Backend/.env.example Backend/.env
```

Edit `Backend/.env` to select an LLM provider and supply its API key. For remote
access, set `PUBLIC_HOST` to your server's IP address or hostname. All published
ports are configurable in the same file.

```bash
cd Backend
mkdir -p models data
docker compose up -d --build
```

With the defaults, the interface is at [localhost:3030](http://localhost:3030)
and API documentation at [localhost:8010/docs](http://localhost:8010/docs).
For remote access, use your server's address and configured ports. First startup
downloads the MedCAT models before the backend becomes available.

## Documentation

See the [research guide](docs/research-guide.md) for experimental workflows,
representations, configuration, API usage, local development, tests, and
limitations.
