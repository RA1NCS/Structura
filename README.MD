# Structura: An LLM-Based ETL Architecture for Semantic Normalization of Unstructured Data

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16786494.svg)](https://doi.org/10.5281/zenodo.16786494)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

<!-- [![arXiv](https://img.shields.io/badge/arXiv-2025.XXXXX-b31b1b.svg)](https://doi.org/10.5281/zenodo.16786494) -->

## Abstract

Automating extract–transform–load (ETL) pipelines for scanned business documents typically demands costly, finetuned, layout-aware models. We present a cloud-native architecture that transforms heterogeneous documents into a unified, structured JSON schema—without any model fine-tuning. Our pipeline combines off-the-shelf OCR (Azure Document Intelligence) with a schema-constrained large language model (LLM), guided by type-checked Pydantic outputs and a one-pass swap heuristic for efficient few-shot prompting. Evaluated on the FUNSD (form) and CORD (receipt) corpora, the system achieves 0.60 and 0.83 fuzzy KV F1 scores, respectively, while processing each page in under eight seconds at under $0.004 on standard cloud quota. Scaling to a larger LLM boosts CORD accuracy to 0.89 F1 at under $0.02 per page. The entire pipeline—code, prompts, and metric scripts—is open-sourced, enabling lightweight, fully-deployable semantic ETL for small-to medium-scale workloads.

## Repository structure

```
Structura/
├── docs/
│   ├── Few-Shot Optimization Pipeline.pdf
│   └── System Architecture Diagram.pdf
├── paper/
├── src/
│   ├── benchmark.py
│   ├── clients.py
│   ├── inference.py
│   ├── main.py
│   ├── metrics.py
│   ├── optimizer.py
│   ├── schemas.py
│   ├── system_prompt.py
│   ├── benchmarks/
│   ├── datasets/
│   │   ├── cord/
│   │   └── funsd/
│   └── prompts/
│       ├── cord/
│       └── funsd/
├── LICENSE
├── README.MD
└── requirements.txt
```

## Setup

1. Python 3.10+ is recommended.

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment variables. Copy the provided template and fill in values from your Azure resources:

```bash
cp .env.template .env
```

Environment keys consumed by the code:

```bash
# Document Intelligence Endpoint
AZUREDOCINTEL_BASE_URI: Azure Document Intelligence endpoint
AZUREDOCINTEL_TOKEN: Azure Document Intelligence API key

# Azure OpenAI Endpoint
AZUREOPENAI_BASE_URI: Azure OpenAI endpoint
AZUREOPENAI_API_TOKEN: Azure OpenAI API key
AZUREOPENAI_API_VERSION: Azure OpenAI API version
AZUREOPENAI_MODEL_NAME: Deployed Azure OpenAI model name
```

The library loads variables via dotenv at import time (see `src/clients.py`).

## Datasets

Sample datasets are included under `src/datasets/`:

-   `cord/`: CORD receipt corpus (images and JSON annotations)
-   `funsd/`: FUNSD form corpus (images and JSON annotations)

Each dataset has `images/` and `annotations/` directories. Filenames (without extension) align between image and JSON.

## Usage

### 1) End-to-end benchmark and few-shot optimization

The default entrypoint runs CORD with `gpt-4o-mini`, generates few-shot exemplars, evaluates, and iteratively improves the exemplar set with a one-pass swap heuristic.

```bash
python src/main.py
```

Artifacts are written to `src/benchmarks/` as JSON plus failure reports for timeouts/errors.

Adjust high-level settings in `src/main.py`:

-   `dataset_name`: one of `cord` or `funsd`
-   `schema`: a Pydantic schema from `src/schemas.py` (e.g., `CORDSchema`)
-   `model`: your Azure OpenAI deployment name (e.g., `gpt-4o-mini`)
-   `fewshot_count`, `fewshot_z_swap`, `max_test_size`: exemplar and evaluation sizes

### 2) Single-document inference

```python
from src.inference import get_response
from src.schemas import CORDSchema
from src.system_prompt import get_system_prompt

system_prompt = get_system_prompt(train_set=["075", "153"], dataset="cord", overwrite=False, use_fewshot=True)
ocr_text, ocr_ms, llm_json, llm_ms = get_response(
    system_prompt=system_prompt,
    pydantic_schema=CORDSchema,
    model_name="gpt-4o-mini",
    file_path="src/datasets/cord/images/000.png",
    temperature=0.3,
)
print(llm_json)
```

### 3) Benchmarks and metrics

`src/benchmark.py` computes metrics and aggregates results. Metrics include fuzzy and exact KV F1, canonical F1 (Hungarian alignment), value quality, and confusion statistics (see `src/metrics.py`).

## System architecture

![System Architecture Diagram](docs/architecture.png)

Core execution path:

1. OCR via Azure Document Intelligence `prebuilt-layout` with KEY_VALUE_PAIRS (`src/inference.get_docintel_result`).
2. Prompt construction from dataset templates plus generated exemplars (`src/system_prompt.py`).
3. LLM call through Azure OpenAI with `instructor` for schema-constrained Pydantic outputs (`src/inference.get_instructor_response`).
4. Structured JSON validation by Pydantic models in `src/schemas.py`.
5. Parallelization with thread pools for OCR and LLM, bounded connection pools, and lightweight rate limiting for OCR posts (`src/inference.py`, `src/benchmark.py`).

## Few-shot optimization pipeline

![Few-Shot Optimization Pipeline](docs/pipeline.png)

This repository implements a one-pass swap heuristic (see `src/optimizer.py`):

1. Select an initial exemplar set and a disjoint test set (`src/system_prompt.get_random_train_set`).
2. Evaluate training exemplars without few-shot examples to estimate individual utility.
3. Generate a test-time system prompt with few-shot examples and evaluate on the test set.
4. Swap out the best-performing training exemplars for the worst-performing test samples (z-swap).
5. Iterate until the train/test sets stabilize or the iteration budget is reached.

The few-shot examples are materialized into `src/prompts/<dataset>/fewshot_examples.txt` and combined with `src/prompts/<dataset>/prompt.txt`.

## Results (paper)

-   FUNSD (forms), fuzzy KV F1: 0.60
-   CORD (receipts), fuzzy KV F1: 0.83
-   Larger LLM on CORD: 0.89
-   Throughput: <8 seconds per page on standard cloud quota
-   Cost: <$0.004 per page with the small model; <$0.02 with a larger model

Empirical outputs for this repository appear under `src/benchmarks/`.

## Configuration reference

Key tunables (edit in code):

-   `src/main.py`: dataset/model selection, exemplar counts, temperature
-   `src/benchmark.py`: parallelism, timeouts/retries, output file naming
-   `src/metrics.py`: thresholds for fuzzy matching and canonical alignment

## Citation

```
@article{gupta2025llm,
  author    = {Gupta, Shreyan},
  title     = {An LLM-Based ETL Architecture for Semantic
               Normalization of Unstructured Data},
  url       = {https://doi.org/10.5281/zenodo.16786494},
  year      = 2025
  doi       = {10.5281/zenodo.16786494},
  version   = {v1},
  journal   = {Preprint submitted to IEEE MIT Undergraduate
               Research Technology Conference (URTC) 2025},
}
```

## License

MIT License. See `LICENSE`.
