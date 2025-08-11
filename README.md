# Structura: LLM-Based ETL for Semantic Normalization of Unstructured Data

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![arXiv](https://img.shields.io/badge/arXiv-2025.XXXXX-b31b1b.svg)](https://doi.org/10.5281/zenodo.16786494)

This repository accompanies the research paper **"An LLM-Based ETL Architecture for Semantic Normalization of Unstructured Data"** by Shreyan Gupta, presented at the IEEE MIT Undergraduate Research Technology Conference (URTC) 2025.

**Paper**: [https://doi.org/10.5281/zenodo.16786494](https://doi.org/10.5281/zenodo.16786494)

## 🚀 Overview

Structura is a cloud-native ETL (Extract, Transform, Load) pipeline designed to convert heterogeneous, unstructured documents into a unified, structured JSON schema without the need for model fine-tuning. The pipeline integrates off-the-shelf Optical Character Recognition (OCR) with a schema-constrained Large Language Model (LLM), utilizing type-checked Pydantic outputs and an efficient few-shot prompting technique.

### Key Features

- **No Fine-tuning Required**: Uses off-the-shelf LLMs with schema-constrained prompting
- **Multi-format Support**: Handles receipts, forms, and other document types
- **Type-safe Outputs**: Pydantic-based schema validation for reliable data extraction
- **Cost-effective**: Processes each page in under 8 seconds at <$0.004 per page
- **Scalable**: Supports larger LLMs for improved accuracy (CORD: 0.89 F1 at <$0.02/page)

## 📊 Performance

| Dataset | Model | F1 Score | Processing Time | Cost/Page |
|---------|-------|----------|-----------------|-----------|
| FUNSD   | GPT-4o-mini | 0.60 | <8s | <$0.004 |
| CORD    | GPT-4o-mini | 0.83 | <8s | <$0.004 |
| CORD    | Larger LLM | 0.89 | <8s | <$0.02 |

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Unstructured  │───▶│  Azure Document  │───▶│  LLM Processing │
│   Documents     │    │   Intelligence   │    │  + Schema      │
│                 │    │     (OCR)        │    │  Validation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Structured     │
                                                │  JSON Output    │
                                                └─────────────────┘
```

## 📁 Repository Structure

```
Structura/
├── src/                    # Core source code
│   ├── ocr/               # OCR processing modules
│   ├── llm/               # LLM integration and prompting
│   ├── schemas/           # Pydantic data models
│   ├── utils/             # Utility functions
│   └── main.py            # Main pipeline entry point
├── data/                  # Sample datasets
│   ├── basic/             # Basic document examples
│   ├── cord/              # CORD receipt dataset
│   └── funsd/             # FUNSD form dataset
├── notebooks/             # Jupyter notebooks
├── tests/                 # Unit and integration tests
├── docs/                  # Documentation
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure Document Intelligence account
- OpenAI API key (or compatible LLM provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RA1NCS/Structura.git
   cd Structura
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="your_endpoint"
   export AZURE_DOCUMENT_INTELLIGENCE_KEY="your_key"
   export OPENAI_API_KEY="your_api_key"
   ```

### Basic Usage

```python
from src.main import StructuraPipeline

# Initialize pipeline
pipeline = StructuraPipeline()

# Process a single document
result = pipeline.process_document("path/to/document.pdf")

# Process a batch of documents
results = pipeline.process_batch("path/to/documents/")
```

## 📚 Documentation

- **[Setup Guide](docs/setup.md)** - Detailed installation and configuration instructions
- **[Usage Guide](docs/usage.md)** - Comprehensive usage examples and API reference
- **[Architecture](docs/architecture.md)** - In-depth system design and implementation details
- **[Evaluation](docs/evaluation.md)** - Performance metrics and benchmark results
- **[API Reference](docs/api.md)** - Complete API documentation

## 🔬 Research

This implementation is based on research presented at IEEE MIT URTC 2025. The paper discusses:

- Novel ETL architecture for document processing
- Schema-constrained LLM prompting techniques
- Performance evaluation on benchmark datasets
- Cost-effectiveness analysis for production deployment

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Azure Document Intelligence for OCR processing
- OpenAI for LLM capabilities
- FUNSD and CORD dataset creators
- IEEE MIT URTC 2025 conference organizers

## 📞 Contact

- **Author**: Shreyan Gupta
- **Email**: shreyangupta08@gmail.com
- **Paper**: [https://doi.org/10.5281/zenodo.16786494](https://doi.org/10.5281/zenodo.16786494)

---

**Citation**: If you use this work in your research, please cite:
```
@article{gupta2025structura,
  title={An LLM-Based ETL Architecture for Semantic Normalization of Unstructured Data},
  author={Gupta, Shreyan},
  journal={IEEE MIT Undergraduate Research Technology Conference},
  year={2025},
  doi={10.5281/zenodo.16786494}
}
```