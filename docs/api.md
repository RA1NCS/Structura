# API Reference

This document provides comprehensive API documentation for the Structura ETL pipeline, including all classes, methods, and configuration options.

## Core Classes

### StructuraPipeline

The main pipeline class that orchestrates the entire document processing workflow.

#### Constructor

```python
StructuraPipeline(
    llm_model: str = "gpt-4o-mini",
    llm_temperature: float = 0.1,
    llm_max_tokens: int = 4000,
    ocr_timeout: int = 60,
    ocr_max_retries: int = 3,
    batch_size: int = 10,
    max_workers: int = 4,
    show_progress: bool = False,
    cache_enabled: bool = True,
    cache_ttl: int = 3600
)
```

**Parameters:**
- `llm_model`: OpenAI model to use for processing (default: "gpt-4o-mini")
- `llm_temperature`: LLM temperature for response generation (default: 0.1)
- `llm_max_tokens`: Maximum tokens for LLM responses (default: 4000)
- `ocr_timeout`: Timeout for OCR processing in seconds (default: 60)
- `ocr_max_retries`: Maximum retry attempts for OCR (default: 3)
- `batch_size`: Number of documents to process in each batch (default: 10)
- `max_workers`: Maximum number of worker threads (default: 4)
- `show_progress`: Whether to show progress bars (default: False)
- `cache_enabled`: Enable result caching (default: True)
- `cache_ttl`: Cache time-to-live in seconds (default: 3600)

#### Methods

##### process_document

Process a single document and return structured data.

```python
def process_document(
    self,
    document_path: str,
    schema: Optional[Type[BaseModel]] = None,
    few_shot_examples: Optional[List[Dict]] = None,
    custom_prompt: Optional[str] = None,
    **kwargs
) -> BaseModel
```

**Parameters:**
- `document_path`: Path to the document file
- `schema`: Custom schema class (optional)
- `few_shot_examples`: List of example input-output pairs (optional)
- `custom_prompt`: Custom prompt template (optional)
- `**kwargs`: Additional processing options

**Returns:**
- Structured data according to the specified schema

**Example:**
```python
pipeline = StructuraPipeline()
result = pipeline.process_document(
    "receipt.pdf",
    schema=CORDSchema,
    few_shot_examples=[{"input": "...", "output": {...}}]
)
```

##### process_batch

Process multiple documents in batch mode.

```python
def process_batch(
    self,
    documents_path: Union[str, List[str]],
    file_types: Optional[List[str]] = None,
    progress_callback: Optional[Callable] = None,
    error_callback: Optional[Callable] = None,
    **kwargs
) -> List[BaseModel]
```

**Parameters:**
- `documents_path`: Directory path or list of file paths
- `file_types`: List of file extensions to process (optional)
- `progress_callback`: Function called with progress updates (optional)
- `error_callback`: Function called when errors occur (optional)
- `**kwargs`: Additional processing options

**Returns:**
- List of structured data results

**Example:**
```python
def progress_callback(completed, total, current_file):
    print(f"Processed {completed}/{total}: {current_file}")

results = pipeline.process_batch(
    "documents/",
    progress_callback=progress_callback,
    file_types=[".pdf", ".png"]
)
```

##### get_statistics

Get processing statistics and performance metrics.

```python
def get_statistics(self) -> Dict[str, Any]
```

**Returns:**
- Dictionary containing processing statistics

**Example:**
```python
stats = pipeline.get_statistics()
print(f"Total processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.2%}")
```

##### clear_cache

Clear the result cache.

```python
def clear_cache(self) -> None
```

**Example:**
```python
pipeline.clear_cache()
```

## Schema Classes

### BaseSchema

Base class for all document schemas.

```python
class BaseSchema(BaseModel):
    document_type: str = Field(description="Type of document")
    confidence: float = Field(description="Overall confidence score")
    processing_time: float = Field(description="Processing time in seconds")
    
    class Config:
        extra = "forbid"
        validate_assignment = True
```

### CORDSchema

Schema for receipt documents (CORD dataset format).

```python
class CORDSchema(BaseSchema):
    merchant: MerchantInfo
    transaction: TransactionInfo
    items: List[MenuItem]
    totals: FinancialTotals
    
    class Config:
        schema_extra = {
            "example": {
                "merchant": {
                    "name": "Walmart",
                    "address": "123 Main St",
                    "phone": "555-0123"
                },
                "transaction": {
                    "date": "2025-01-15",
                    "time": "14:30:00",
                    "receipt_number": "R123456"
                },
                "items": [
                    {
                        "name": "Milk",
                        "quantity": 2,
                        "unit_price": 3.99,
                        "total_price": 7.98
                    }
                ],
                "totals": {
                    "subtotal": 7.98,
                    "tax": 0.64,
                    "total": 8.62
                }
            }
        }
```

### FUNSDSchema

Schema for form documents (FUNSD dataset format).

```python
class FUNSDSchema(BaseSchema):
    form_type: str = Field(description="Type of form")
    fields: List[FormField]
    relationships: List[FieldRelationship]
    
    class Config:
        schema_extra = {
            "example": {
                "form_type": "invoice",
                "fields": [
                    {
                        "id": "company_name",
                        "type": "text",
                        "value": "ABC Corp",
                        "bbox": [100, 50, 200, 70],
                        "confidence": 0.95
                    }
                ],
                "relationships": [
                    {
                        "from": "company_name",
                        "to": "invoice_number",
                        "type": "header"
                    }
                ]
            }
        }
```

### BasicSchema

Schema for general documents.

```python
class BasicSchema(BaseSchema):
    title: Optional[str] = Field(description="Document title")
    content_summary: str = Field(description="Content summary")
    key_information: Dict[str, Any] = Field(description="Key extracted information")
    metadata: DocumentMetadata
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Sample Document",
                "content_summary": "This is a sample document for demonstration",
                "key_information": {
                    "author": "John Doe",
                    "date": "2025-01-15"
                },
                "metadata": {
                    "page_count": 1,
                    "language": "en",
                    "format": "pdf"
                }
            }
        }
```

## Supporting Classes

### MerchantInfo

Information about the merchant or business.

```python
class MerchantInfo(BaseModel):
    name: str = Field(description="Merchant/store name")
    address: Optional[str] = Field(description="Merchant address")
    phone: Optional[str] = Field(description="Contact phone number")
    website: Optional[str] = Field(description="Business website")
    tax_id: Optional[str] = Field(description="Tax identification number")
```

### TransactionInfo

Transaction details and metadata.

```python
class TransactionInfo(BaseModel):
    date: str = Field(description="Transaction date")
    time: Optional[str] = Field(description="Transaction time")
    receipt_number: Optional[str] = Field(description="Receipt number")
    cashier: Optional[str] = Field(description="Cashier name")
    payment_method: Optional[str] = Field(description="Payment method used")
```

### MenuItem

Individual item information from receipts.

```python
class MenuItem(BaseModel):
    name: str = Field(description="Item name")
    quantity: Optional[float] = Field(description="Item quantity")
    unit_price: Optional[float] = Field(description="Price per unit")
    total_price: Optional[float] = Field(description="Total price for item")
    category: Optional[str] = Field(description="Item category")
    modifiers: Optional[List[str]] = Field(description="Item modifications")
```

### FinancialTotals

Financial summary and totals.

```python
class FinancialTotals(BaseModel):
    subtotal: Optional[float] = Field(description="Subtotal amount")
    tax: Optional[float] = Field(description="Tax amount")
    discount: Optional[float] = Field(description="Discount amount")
    total: float = Field(description="Total amount")
    currency: str = Field(default="USD", description="Currency code")
```

### FormField

Individual form field information.

```python
class FormField(BaseModel):
    id: str = Field(description="Unique field identifier")
    type: str = Field(description="Field type (text, number, checkbox, etc.)")
    value: str = Field(description="Extracted field value")
    bbox: List[int] = Field(description="Bounding box coordinates [x1, y1, x2, y2]")
    confidence: float = Field(description="Confidence score for extraction")
    label: Optional[str] = Field(description="Field label or description")
```

### FieldRelationship

Relationships between form fields.

```python
class FieldRelationship(BaseModel):
    from_field: str = Field(description="Source field identifier")
    to_field: str = Field(description="Target field identifier")
    type: str = Field(description="Relationship type")
    confidence: float = Field(description="Confidence in relationship")
```

### DocumentMetadata

General document metadata.

```python
class DocumentMetadata(BaseModel):
    page_count: int = Field(description="Number of pages")
    language: str = Field(description="Document language")
    format: str = Field(description="Document format")
    file_size: Optional[int] = Field(description="File size in bytes")
    created_date: Optional[str] = Field(description="Document creation date")
    modified_date: Optional[str] = Field(description="Document modification date")
```

## Configuration Classes

### PipelineConfig

Configuration for the processing pipeline.

```python
class PipelineConfig(BaseModel):
    # LLM Configuration
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    llm_timeout: int = 30
    
    # OCR Configuration
    ocr_timeout: int = 60
    ocr_max_retries: int = 3
    ocr_batch_size: int = 5
    
    # Processing Configuration
    batch_size: int = 10
    max_workers: int = 4
    show_progress: bool = False
    
    # Caching Configuration
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 1000
    
    class Config:
        env_prefix = "STRUCTURA_"
```

### ProcessingOptions

Options for individual document processing.

```python
class ProcessingOptions(BaseModel):
    schema: Optional[Type[BaseModel]] = None
    few_shot_examples: Optional[List[Dict]] = None
    custom_prompt: Optional[str] = None
    confidence_threshold: float = 0.7
    max_retries: int = 3
    timeout: int = 60
    include_raw_text: bool = False
    include_ocr_data: bool = False
```

## Error Classes

### StructuraError

Base exception class for Structura.

```python
class StructuraError(Exception):
    """Base exception for Structura pipeline errors."""
    pass
```

### OCRProcessingError

Errors related to OCR processing.

```python
class OCRProcessingError(StructuraError):
    """Raised when OCR processing fails."""
    def __init__(self, message: str, document_path: str, error_code: Optional[str] = None):
        self.message = message
        self.document_path = document_path
        self.error_code = error_code
        super().__init__(self.message)
```

### LLMProcessingError

Errors related to LLM processing.

```python
class LLMProcessingError(StructuraError):
    """Raised when LLM processing fails."""
    def __init__(self, message: str, document_path: str, error_code: Optional[str] = None):
        self.message = message
        self.document_path = document_path
        self.error_code = error_code
        super().__init__(self.message)
```

### SchemaValidationError

Errors related to schema validation.

```python
class SchemaValidationError(StructuraError):
    """Raised when schema validation fails."""
    def __init__(self, message: str, validation_errors: List[Dict], document_path: str):
        self.message = message
        self.validation_errors = validation_errors
        self.document_path = document_path
        super().__init__(self.message)
```

## Utility Functions

### Document Utilities

```python
def validate_document_path(document_path: str) -> bool:
    """Validate if document path exists and is accessible."""
    pass

def get_document_type(document_path: str) -> str:
    """Detect document type based on file extension and content."""
    pass

def calculate_document_hash(document_path: str) -> str:
    """Calculate hash of document for caching purposes."""
    pass
```

### Schema Utilities

```python
def load_schema_from_file(schema_path: str) -> Type[BaseModel]:
    """Load schema definition from JSON file."""
    pass

def validate_schema_compatibility(schema1: Type[BaseModel], schema2: Type[BaseModel]) -> bool:
    """Check if two schemas are compatible for conversion."""
    pass

def generate_schema_examples(schema: Type[BaseModel]) -> Dict[str, Any]:
    """Generate example data for a given schema."""
    pass
```

### Processing Utilities

```python
def construct_prompt(document_text: str, schema: Type[BaseModel], examples: Optional[List[Dict]] = None) -> str:
    """Construct LLM prompt for document processing."""
    pass

def parse_llm_response(response_text: str, schema: Type[BaseModel]) -> BaseModel:
    """Parse LLM response and validate against schema."""
    pass

def calculate_confidence_score(extracted_data: BaseModel, raw_text: str) -> float:
    """Calculate confidence score for extracted data."""
    pass
```

## Environment Variables

### Required Variables

```bash
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key-here

# OpenAI API
OPENAI_API_KEY=your-openai-api-key
```

### Optional Variables

```bash
# Pipeline Configuration
STRUCTURA_LLM_MODEL=gpt-4o-mini
STRUCTURA_LLM_TEMPERATURE=0.1
STRUCTURA_BATCH_SIZE=10
STRUCTURA_MAX_WORKERS=4
STRUCTURA_LOG_LEVEL=INFO

# Caching Configuration
STRUCTURA_CACHE_ENABLED=true
STRUCTURA_CACHE_TTL=3600
STRUCTURA_CACHE_MAX_SIZE=1000

# Error Handling
STRUCTURA_MAX_RETRIES=3
STRUCTURA_TIMEOUT=30
```

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": {
    "merchant": {
      "name": "Walmart",
      "address": "123 Main St"
    },
    "transaction": {
      "date": "2025-01-15",
      "total": 25.99
    }
  },
  "metadata": {
    "processing_time": 7.8,
    "confidence": 0.89,
    "schema_version": "1.0"
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "type": "OCRProcessingError",
    "message": "OCR processing failed due to timeout",
    "error_code": "TIMEOUT",
    "document_path": "receipt.pdf"
  },
  "metadata": {
    "timestamp": "2025-01-15T14:30:00Z",
    "request_id": "req_123456"
  }
}
```

## Rate Limits and Quotas

### Azure Document Intelligence

- **Free Tier**: 500 pages/month
- **Standard Tier**: 10,000 pages/month
- **Premium Tier**: Custom limits

### OpenAI API

- **GPT-4o-mini**: 500 requests/minute
- **GPT-4**: 3 requests/minute
- **Custom limits**: Available for enterprise accounts

### Implementation Notes

- Implement exponential backoff for rate limit handling
- Use connection pooling for external API calls
- Implement circuit breaker pattern for service failures
- Cache results to minimize API calls

## Best Practices

### Performance Optimization

1. **Use appropriate batch sizes** based on system resources
2. **Implement caching** for frequently processed documents
3. **Use parallel processing** for large document sets
4. **Monitor resource usage** and adjust accordingly

### Error Handling

1. **Implement comprehensive retry logic** with exponential backoff
2. **Use circuit breaker pattern** for external service failures
3. **Provide meaningful error messages** for debugging
4. **Log all errors** with appropriate context

### Security

1. **Validate all inputs** before processing
2. **Use environment variables** for sensitive configuration
3. **Implement access control** for pipeline operations
4. **Audit all operations** for compliance

### Monitoring

1. **Track processing metrics** (time, success rate, errors)
2. **Monitor resource utilization** (CPU, memory, network)
3. **Set up alerts** for critical failures
4. **Log all operations** for debugging and compliance