# Architecture Documentation

This document provides an in-depth explanation of the Structura ETL pipeline's architecture, design decisions, and implementation details.

## System Overview

Structura is designed as a modular, cloud-native ETL pipeline that transforms unstructured documents into structured data using a combination of OCR and LLM technologies. The system follows a microservices-inspired architecture with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Structura Pipeline                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Input     │  │  Document   │  │      Output             │ │
│  │  Handler    │  │  Router     │  │      Handler            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Core Processing                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │     OCR     │  │     LLM     │  │    Schema               │ │
│  │  Processor  │  │  Processor  │  │  Validator              │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    External Services                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐ │
│  │ Azure Document      │  │        OpenAI API                │ │
│  │ Intelligence        │  │                                 │ │
│  └─────────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Input Handler

The input handler is responsible for:
- Accepting various document formats (PDF, images, scanned documents)
- Validating file integrity and format
- Converting documents to a standardized internal representation
- Managing file uploads and temporary storage

**Key Features:**
- Multi-format support (PDF, PNG, JPEG, TIFF, BMP)
- Automatic format detection
- File size validation
- Temporary file management

### 2. Document Router

The document router determines the appropriate processing pipeline based on:
- Document type and format
- User-specified schema preferences
- Automatic document classification
- Processing priority and requirements

**Routing Logic:**
```python
def route_document(document, user_schema=None):
    if user_schema:
        return user_schema
    
    # Auto-detect document type
    if is_receipt_like(document):
        return CORDSchema
    elif is_form_like(document):
        return FUNSDSchema
    else:
        return BasicSchema
```

### 3. OCR Processor

The OCR processor handles text extraction from documents using Azure Document Intelligence:

**Processing Pipeline:**
1. **Document Analysis**: Extract text, layout, and structure
2. **Text Normalization**: Clean and standardize extracted text
3. **Layout Analysis**: Identify document sections and relationships
4. **Metadata Extraction**: Extract document properties and formatting

**Key Features:**
- Azure Document Intelligence integration
- Automatic language detection
- Layout preservation
- Table structure recognition
- Handwriting recognition support

### 4. LLM Processor

The LLM processor transforms OCR output into structured data:

**Processing Steps:**
1. **Prompt Construction**: Build context-aware prompts with few-shot examples
2. **LLM Inference**: Generate structured responses using schema constraints
3. **Response Parsing**: Extract and validate structured data
4. **Error Handling**: Implement retry logic and fallback strategies

**Prompt Engineering:**
```python
def construct_prompt(document_text, schema, examples=None):
    prompt = f"""
    Extract information from the following document according to this schema:
    {schema.json_schema()}
    
    {f"Examples: {examples}" if examples else ""}
    
    Document:
    {document_text}
    
    Output the extracted data in valid JSON format.
    """
    return prompt
```

### 5. Schema Validator

The schema validator ensures data quality and consistency:

**Validation Features:**
- Pydantic-based schema validation
- Type checking and coercion
- Required field validation
- Custom validation rules
- Error reporting and suggestions

## Data Flow

### 1. Document Ingestion

```
Document → Input Handler → Document Router → Processing Queue
```

### 2. OCR Processing

```
Processing Queue → OCR Processor → Azure Document Intelligence → Text + Layout
```

### 3. LLM Processing

```
Text + Layout → LLM Processor → OpenAI API → Structured Response
```

### 4. Validation & Output

```
Structured Response → Schema Validator → Final Output → Client
```

## Schema System

### Schema Hierarchy

```
BaseSchema
├── CORDSchema (Receipts)
│   ├── Merchant Information
│   ├── Transaction Details
│   ├── Item List
│   └── Financial Summary
├── FUNSDSchema (Forms)
│   ├── Form Fields
│   ├── Field Types
│   ├── Field Values
│   └── Field Relationships
└── BasicSchema (General Documents)
    ├── Document Metadata
    ├── Content Summary
    └── Key Information
```

### Schema Definition Example

```python
class CORDSchema(BaseModel):
    merchant: MerchantInfo
    transaction: TransactionInfo
    items: List[MenuItem]
    totals: FinancialTotals
    
    class Config:
        extra = "forbid"
        validate_assignment = True

class MerchantInfo(BaseModel):
    name: str = Field(description="Merchant/store name")
    address: Optional[str] = Field(description="Merchant address")
    phone: Optional[str] = Field(description="Contact phone number")
```

## Error Handling & Resilience

### Error Categories

1. **OCR Errors**: Timeouts, connection failures, unsupported formats
2. **LLM Errors**: API failures, validation errors, rate limits
3. **Schema Errors**: Validation failures, missing required fields
4. **System Errors**: Memory issues, file system problems

### Resilience Strategies

**Retry Logic:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((OCRTimeoutError, LLMRetryableError))
)
def process_with_retry(document):
    return process_document(document)
```

**Circuit Breaker:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = "CLOSED"
```

**Fallback Strategies:**
- Use cached results for failed requests
- Implement simpler processing pipelines
- Provide partial results with error indicators

## Performance Optimization

### Parallel Processing

**Worker Pool Management:**
```python
class WorkerPool:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
```

**Batch Processing:**
```python
def process_batch(documents, batch_size=10):
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_batch_chunk, batch) for batch in batches]
        results = [future.result() for future in as_completed(futures)]
    
    return results
```

### Caching Strategy

**Multi-level Caching:**
1. **Document Cache**: Store processed document results
2. **OCR Cache**: Cache OCR results for identical documents
3. **LLM Cache**: Cache LLM responses for similar content
4. **Schema Cache**: Cache validated schema instances

**Cache Implementation:**
```python
class DocumentCache:
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = LRUCache(max_size)
        self.ttl = ttl
    
    def get(self, document_hash):
        if document_hash in self.cache:
            result, timestamp = self.cache[document_hash]
            if time.time() - timestamp < self.ttl:
                return result
        return None
```

## Security & Privacy

### Data Protection

- **Encryption**: All data encrypted in transit and at rest
- **Access Control**: Role-based access control for pipeline operations
- **Audit Logging**: Comprehensive logging of all operations
- **Data Retention**: Configurable data retention policies

### Privacy Features

- **PII Detection**: Automatic detection of personally identifiable information
- **Data Masking**: Optional masking of sensitive data
- **Compliance**: GDPR and CCPA compliance features
- **Data Localization**: Support for data residency requirements

## Monitoring & Observability

### Metrics Collection

**Performance Metrics:**
- Processing time per document
- Throughput (documents per second)
- Error rates and types
- Resource utilization

**Business Metrics:**
- Success rates by document type
- Schema validation success rates
- Cost per document processed
- User satisfaction scores

### Logging Strategy

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

def process_document(document_path):
    logger.info("Processing document",
                document_path=document_path,
                document_size=os.path.getsize(document_path),
                timestamp=datetime.utcnow().isoformat())
```

**Log Levels:**
- **DEBUG**: Detailed processing information
- **INFO**: General processing status
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures
- **CRITICAL**: System failures

## Scalability Considerations

### Horizontal Scaling

- **Load Balancing**: Distribute processing across multiple instances
- **Auto-scaling**: Automatically adjust resources based on demand
- **Queue Management**: Use message queues for asynchronous processing
- **Database Sharding**: Distribute data across multiple databases

### Vertical Scaling

- **Resource Optimization**: Optimize memory and CPU usage
- **Batch Size Tuning**: Adjust batch sizes based on available resources
- **Concurrency Control**: Manage concurrent processing limits
- **Memory Management**: Implement efficient memory usage patterns

## Deployment Architecture

### Cloud-Native Design

**Containerization:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
CMD ["python", "src/main.py"]
```

**Orchestration:**
- Kubernetes deployment with auto-scaling
- Docker Compose for local development
- Azure Container Instances for serverless deployment

### Infrastructure as Code

**Terraform Configuration:**
```hcl
resource "azurerm_cognitive_account" "document_intelligence" {
  name                = "structura-doc-intel"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FormRecognizer"
  sku_name            = "S0"
}
```

## Future Enhancements

### Planned Features

1. **Multi-language Support**: Support for additional languages
2. **Custom Model Training**: Fine-tuning capabilities for specific domains
3. **Real-time Processing**: Streaming document processing
4. **Advanced Analytics**: Document insights and trend analysis
5. **Integration APIs**: Connectors for popular business systems

### Research Directions

1. **Few-shot Learning**: Improved prompting strategies
2. **Schema Evolution**: Dynamic schema adaptation
3. **Quality Assurance**: Automated quality validation
4. **Cost Optimization**: Intelligent resource allocation

## Conclusion

The Structura architecture provides a robust, scalable foundation for document processing and data extraction. By combining OCR and LLM technologies with a well-designed schema system, it offers a flexible solution for various document processing needs while maintaining high performance and reliability standards.

The modular design allows for easy extension and customization, making it suitable for both research and production environments. The focus on error handling, monitoring, and scalability ensures that the system can handle real-world challenges effectively.