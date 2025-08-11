# Setup Guide

This guide will walk you through setting up the Structura ETL pipeline on your local machine or cloud environment.

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: At least 2GB free space for dependencies and sample data

### Required Accounts

1. **Azure Account**: For Document Intelligence OCR service
2. **OpenAI Account**: For LLM processing (or compatible provider)
3. **Git**: For cloning the repository

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/RA1NCS/Structura.git
cd Structura
```

### 2. Create Virtual Environment

```bash
# Using venv (recommended)
python -m venv structura-env

# Activate virtual environment
# On Linux/macOS:
source structura-env/bin/activate

# On Windows:
structura-env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Azure Document Intelligence Setup

1. **Create Azure Resource**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Search for "Document Intelligence"
   - Click "Create"
   - Choose your subscription and resource group
   - Select a region close to your location
   - Choose pricing tier (Free tier available for testing)
   - Click "Review + Create"

2. **Get Credentials**:
   - Navigate to your Document Intelligence resource
   - Go to "Keys and Endpoint" in the left sidebar
   - Copy the endpoint URL and one of the keys

3. **Set Environment Variables**:
   ```bash
   export AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
   export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-key-here"
   ```

### 5. OpenAI API Setup

1. **Get API Key**:
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new secret key
   - Copy the key

2. **Set Environment Variable**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

### 6. Alternative LLM Providers

If you prefer to use other LLM providers, you can configure them by setting additional environment variables:

```bash
# For Anthropic Claude
export ANTHROPIC_API_KEY="your-claude-api-key"

# For Google Gemini
export GOOGLE_API_KEY="your-gemini-api-key"

# For local models (Ollama)
export OLLAMA_BASE_URL="http://localhost:11434"
```

## Configuration Files

### Environment File

Create a `.env` file in the root directory:

```bash
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Optional: Custom configurations
STRUCTURA_LOG_LEVEL=INFO
STRUCTURA_MAX_RETRIES=3
STRUCTURA_TIMEOUT=30
```

### Load Environment Variables

```bash
# Load from .env file
source .env

# Or use python-dotenv in your code
from dotenv import load_dotenv
load_dotenv()
```

## Verification

### 1. Test Azure Connection

```python
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

client = DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
print("Azure connection successful!")
```

### 2. Test OpenAI Connection

```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
print("OpenAI connection successful!")
```

### 3. Run Basic Pipeline Test

```python
from src.main import StructuraPipeline

pipeline = StructuraPipeline()
print("Pipeline initialized successfully!")
```

## Troubleshooting

### Common Issues

1. **Azure Authentication Error**:
   - Verify endpoint URL format
   - Check if key is correct and not expired
   - Ensure resource is in the same region as your code

2. **OpenAI API Error**:
   - Verify API key is correct
   - Check account billing status
   - Ensure you have access to the requested model

3. **Python Package Issues**:
   - Update pip: `pip install --upgrade pip`
   - Clear cache: `pip cache purge`
   - Reinstall packages: `pip install -r requirements.txt --force-reinstall`

4. **Memory Issues**:
   - Reduce batch size in configuration
   - Use smaller document sizes for testing
   - Increase system swap space

### Getting Help

- Check the [Issues](https://github.com/RA1NCS/Structura/issues) page
- Review the [Usage Guide](usage.md) for examples
- Consult the [Architecture](architecture.md) documentation

## Next Steps

Once setup is complete, you can:

1. Read the [Usage Guide](usage.md) to learn how to use the pipeline
2. Explore the [Architecture](architecture.md) to understand the system design
3. Try processing sample documents from the `data/` directory
4. Run the evaluation benchmarks to test performance

## Production Deployment

For production environments, consider:

- Using Azure Key Vault for secure credential management
- Implementing proper logging and monitoring
- Setting up CI/CD pipelines
- Using containerization (Docker) for consistent deployments
- Implementing retry logic and circuit breakers
- Setting up proper backup and disaster recovery procedures