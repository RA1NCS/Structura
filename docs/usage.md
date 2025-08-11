# Usage Guide

This guide provides comprehensive examples and API reference for using the Structura ETL pipeline.

## Basic Usage

### Import and Initialize

```python
from src.main import StructuraPipeline

# Initialize with default settings
pipeline = StructuraPipeline()

# Initialize with custom configuration
pipeline = StructuraPipeline(
    llm_model="gpt-4o-mini",
    max_retries=3,
    timeout=30,
    batch_size=10
)
```

### Process Single Document

```python
# Process a PDF document
result = pipeline.process_document("path/to/receipt.pdf")

# Process an image file
result = pipeline.process_document("path/to/form.png")

# Process with custom schema
result = pipeline.process_document(
    "path/to/document.pdf",
    schema="custom_schema"
)
```

### Process Batch of Documents

```python
# Process all documents in a directory
results = pipeline.process_batch("path/to/documents/")

# Process specific file types
results = pipeline.process_batch(
    "path/to/documents/",
    file_types=[".pdf", ".png", ".jpg"]
)

# Process with progress tracking
results = pipeline.process_batch(
    "path/to/documents/",
    show_progress=True
)
```

## Document Types

### Supported Formats

- **Images**: PNG, JPEG, TIFF, BMP
- **Documents**: PDF, DOCX, TXT
- **Scanned Documents**: Any scanned image format

### Document Categories

1. **Receipts** (CORD dataset format)
2. **Forms** (FUNSD dataset format)
3. **General Documents** (Basic schema)

## Schema Customization

### Default Schemas

```python
from src.schemas import CORDSchema, FUNSDSchema, BasicSchema

# Use CORD schema for receipts
result = pipeline.process_document(
    "receipt.pdf",
    schema=CORDSchema
)

# Use FUNSD schema for forms
result = pipeline.process_document(
    "form.pdf",
    schema=FUNSDSchema
)
```

### Custom Schema Definition

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CustomSchema(BaseModel):
    title: str = Field(description="Document title")
    items: List[str] = Field(description="List of items")
    total: Optional[float] = Field(description="Total amount")
    
    class Config:
        extra = "forbid"  # Strict validation

# Use custom schema
result = pipeline.process_document(
    "document.pdf",
    schema=CustomSchema
)
```

## Configuration Options

### Pipeline Configuration

```python
pipeline = StructuraPipeline(
    # LLM settings
    llm_model="gpt-4o-mini",
    llm_temperature=0.1,
    llm_max_tokens=4000,
    
    # OCR settings
    ocr_timeout=60,
    ocr_max_retries=3,
    
    # Processing settings
    batch_size=10,
    max_workers=4,
    show_progress=True
)
```

### Environment Configuration

```bash
# LLM Configuration
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1

# Azure Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your-endpoint
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key

# Pipeline Configuration
STRUCTURA_BATCH_SIZE=10
STRUCTURA_MAX_WORKERS=4
STRUCTURA_LOG_LEVEL=INFO
```

## Advanced Features

### Few-shot Learning

```python
# Provide custom examples for better accuracy
examples = [
    {
        "input": "Sample receipt text...",
        "output": {"merchant": "Store Name", "total": 25.99}
    }
]

result = pipeline.process_document(
    "document.pdf",
    few_shot_examples=examples
)
```

### Custom Prompts

```python
# Use custom prompt template
custom_prompt = """
Extract the following information from this document:
- Company name
- Date
- Total amount
- Items list

Document: {document_text}
"""

result = pipeline.process_document(
    "document.pdf",
    custom_prompt=custom_prompt
)
```

### Batch Processing with Callbacks

```python
def progress_callback(completed, total, current_file):
    print(f"Processed {completed}/{total}: {current_file}")

def error_callback(file_path, error):
    print(f"Error processing {file_path}: {error}")

results = pipeline.process_batch(
    "path/to/documents/",
    progress_callback=progress_callback,
    error_callback=error_callback
)
```

## Error Handling

### Common Errors and Solutions

```python
try:
    result = pipeline.process_document("document.pdf")
except OCRTimeoutError:
    print("OCR processing timed out, retrying...")
    # Implement retry logic
except LLMValidationError as e:
    print(f"LLM validation failed: {e}")
    # Handle schema validation errors
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def process_with_retry(pipeline, document_path):
    return pipeline.process_document(document_path)

result = process_with_retry(pipeline, "document.pdf")
```

## Performance Optimization

### Batch Processing

```python
# Optimal batch size depends on your system
optimal_batch_size = min(20, os.cpu_count() * 2)

results = pipeline.process_batch(
    "path/to/documents/",
    batch_size=optimal_batch_size
)
```

### Parallel Processing

```python
# Use multiple workers for parallel processing
pipeline = StructuraPipeline(max_workers=8)

# Process multiple directories in parallel
from concurrent.futures import ThreadPoolExecutor

def process_directory(dir_path):
    return pipeline.process_batch(dir_path)

directories = ["dir1/", "dir2/", "dir3/"]
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_directory, directories))
```

### Memory Management

```python
# Process large datasets in chunks
def process_large_dataset(dataset_path, chunk_size=100):
    files = os.listdir(dataset_path)
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i + chunk_size]
        chunk_paths = [os.path.join(dataset_path, f) for f in chunk]
        
        # Process chunk
        results = pipeline.process_batch(chunk_paths)
        
        # Save results
        save_results(results, f"chunk_{i//chunk_size}.json")
        
        # Clear memory
        del results
```

## Output Formats

### Standard Output

```python
# Process document and get structured output
result = pipeline.process_document("document.pdf")

# Access extracted data
print(f"Merchant: {result.merchant}")
print(f"Total: {result.total}")
print(f"Items: {result.items}")
```

### Export Options

```python
# Export to JSON
import json
with open("output.json", "w") as f:
    json.dump(result.dict(), f, indent=2)

# Export to CSV
import pandas as pd
df = pd.DataFrame([result.dict()])
df.to_csv("output.csv", index=False)

# Export to Excel
df.to_excel("output.xlsx", index=False)
```

## Monitoring and Logging

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Pipeline will use configured logging
pipeline = StructuraPipeline()
```

### Performance Metrics

```python
# Get processing statistics
stats = pipeline.get_statistics()
print(f"Total documents processed: {stats['total_processed']}")
print(f"Average processing time: {stats['avg_time']:.2f}s")
print(f"Success rate: {stats['success_rate']:.2%}")
```

## Integration Examples

### Web Application

```python
from flask import Flask, request, jsonify
from src.main import StructuraPipeline

app = Flask(__name__)
pipeline = StructuraPipeline()

@app.route('/process', methods=['POST'])
def process_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    result = pipeline.process_document(file)
    
    return jsonify(result.dict())

if __name__ == '__main__':
    app.run(debug=True)
```

### API Service

```python
from fastapi import FastAPI, UploadFile, File
from src.main import StructuraPipeline

app = FastAPI()
pipeline = StructuraPipeline()

@app.post("/extract")
async def extract_data(file: UploadFile = File(...)):
    # Save uploaded file temporarily
    temp_path = f"/tmp/{file.filename}"
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Process document
    result = pipeline.process_document(temp_path)
    
    # Clean up
    os.remove(temp_path)
    
    return result.dict()
```

## Best Practices

1. **Use appropriate batch sizes** for your system resources
2. **Implement proper error handling** and retry logic
3. **Monitor performance metrics** to optimize processing
4. **Use custom schemas** for domain-specific documents
5. **Implement logging** for debugging and monitoring
6. **Handle large datasets** in chunks to manage memory
7. **Use few-shot examples** for better accuracy on specific document types
8. **Implement caching** for frequently processed documents

## Troubleshooting

### Common Issues

1. **Memory errors**: Reduce batch size or process in chunks
2. **Timeout errors**: Increase timeout values or implement retry logic
3. **Validation errors**: Check schema compatibility or use custom schemas
4. **API rate limits**: Implement rate limiting and exponential backoff

### Getting Help

- Check the [Setup Guide](setup.md) for configuration issues
- Review the [Architecture](architecture.md) for system understanding
- Consult the [Evaluation](evaluation.md) for performance insights
- Open an issue on GitHub for bugs or feature requests