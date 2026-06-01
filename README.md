# RAG Backend (NovoxCore)

This repository contains the ingestion pipeline and simple backend for
building a knowledge base for a Retrieval-Augmented Generation (RAG)
chatbot.

Goal
----
Provide a small-company, maintainable backend that:

- Crawls configured websites
- Extracts and cleans content
- Splits content into retrieval-optimized chunks
- Detects changes to avoid unnecessary rebuilds
- Rebuilds a lightweight vector store
- Supports scheduled automatic updates

Quick start
-----------
1. Create and activate the Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Install Playwright browsers (if using crawler/playwright):

```bash
python -m playwright install
```

3. Run the pipeline once (manual):

```bash
python run_pipeline.py
```

4. Start scheduler to run daily updates (background):

```bash
python backend/app.py --start-scheduler
```

Configuration
-------------
Edit `config.json` to add websites, enable/disable automatic updates, and
control chunking/crawler behavior. Example:

```json
{
  "websites": {
    "novoxcore": {
      "name": "NovoxCore",
      "url": "https://novoxcore.com/",
      "enabled": true,
      "auto_update": true
    }
  }
}
```

Logging
-------
Logs are written to the `logs/` directory. Each run creates a timestamped
log file. Console output is INFO-level; files include DEBUG.

Troubleshooting
---------------
- Playwright may require system dependencies on some Linux distros. If
  you see host validation warnings, install dependencies suggested by
  the Playwright installer (e.g., `libicu`, `libxml2`, `libjpeg-turbo`).

- If the scheduler is not running, run `python backend/app.py --start-scheduler`

Handover notes
--------------
- The vector store implementation is intentionally minimal. Replace
  `backend/vector_store.py` with a proper embedding + vector DB (e.g.,
  FAISS, Milvus, Pinecone) when desired.

- The scheduler uses APScheduler and runs jobs based on `config.json`.

- The change detector stores state in `.update_state.json` by default.

Contact
-------
For internal handover questions, see the `docs/` directory or contact
`novoxcoretech@gmail.com`.
