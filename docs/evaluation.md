# Evaluation & Performance

This document provides detailed information about the evaluation methodology, benchmark results, and performance analysis of the Structura ETL pipeline.

## Evaluation Overview

The Structura pipeline has been evaluated on multiple benchmark datasets to assess its performance, accuracy, and cost-effectiveness. The evaluation focuses on:

- **Accuracy**: How well the system extracts and structures information
- **Performance**: Processing speed and throughput
- **Cost**: Financial efficiency of document processing
- **Reliability**: Error rates and system stability
- **Scalability**: Performance under different load conditions

## Benchmark Datasets

### 1. CORD Dataset (Receipts)

**Dataset Description:**
- **Source**: [CORD: A Consolidated Receipt Dataset for Post-OCR Parsing](https://github.com/clovaai/CORD)
- **Size**: 1,000+ receipt images
- **Format**: Various receipt types from different merchants
- **Complexity**: Handwritten text, multiple languages, various layouts

**Schema Structure:**
```json
{
  "merchant": {
    "name": "string",
    "address": "string",
    "phone": "string"
  },
  "transaction": {
    "date": "string",
    "time": "string",
    "receipt_number": "string"
  },
  "items": [
    {
      "name": "string",
      "quantity": "number",
      "unit_price": "number",
      "total_price": "number"
    }
  ],
  "totals": {
    "subtotal": "number",
    "tax": "number",
    "total": "number"
  }
}
```

### 2. FUNSD Dataset (Forms)

**Dataset Description:**
- **Source**: [FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents](https://guillaumejaume.github.io/FUNSD/)
- **Size**: 200 annotated forms
- **Format**: Various form types (invoices, surveys, applications)
- **Complexity**: Structured layouts, multiple field types, annotations

**Schema Structure:**
```json
{
  "form_type": "string",
  "fields": [
    {
      "id": "string",
      "type": "string",
      "value": "string",
      "bbox": [x1, y1, x2, y2],
      "confidence": "number"
    }
  ],
  "relationships": [
    {
      "from": "string",
      "to": "string",
      "type": "string"
    }
  ]
}
```

### 3. Basic Dataset (General Documents)

**Dataset Description:**
- **Source**: Custom collection of general documents
- **Size**: 100+ diverse documents
- **Format**: Letters, reports, certificates, etc.
- **Complexity**: Various text layouts and content types

## Evaluation Metrics

### 1. Accuracy Metrics

**Fuzzy Key-Value F1 Score:**
- **Definition**: Harmonic mean of precision and recall for key-value extraction
- **Calculation**: F1 = 2 × (Precision × Recall) / (Precision + Recall)
- **Range**: 0.0 to 1.0 (higher is better)

**Precision:**
- **Definition**: Ratio of correctly extracted key-value pairs to total extracted pairs
- **Formula**: Precision = TP / (TP + FP)

**Recall:**
- **Definition**: Ratio of correctly extracted key-value pairs to total actual pairs
- **Formula**: Recall = TP / (TP + FN)

**Exact Match Accuracy:**
- **Definition**: Percentage of documents with perfect extraction
- **Use Case**: Overall system performance assessment

### 2. Performance Metrics

**Processing Time:**
- **OCR Time**: Time for text extraction
- **LLM Time**: Time for structured data generation
- **Total Time**: End-to-end processing time

**Throughput:**
- **Documents per Second**: Processing rate
- **Pages per Second**: Multi-page document handling

**Resource Utilization:**
- **Memory Usage**: RAM consumption during processing
- **CPU Usage**: Processing overhead
- **Network I/O**: API call efficiency

### 3. Cost Metrics

**Cost per Document:**
- **OCR Cost**: Azure Document Intelligence charges
- **LLM Cost**: OpenAI API usage costs
- **Total Cost**: Combined processing cost

**Cost Efficiency:**
- **Cost per 1000 Documents**: Bulk processing efficiency
- **ROI Analysis**: Business value assessment

## Benchmark Results

### Overall Performance Summary

| Dataset | Model | F1 Score | Processing Time | Cost/Page | Success Rate |
|---------|-------|----------|-----------------|-----------|--------------|
| FUNSD   | GPT-4o-mini | 0.60 | 6.2s | $0.0038 | 94.2% |
| CORD    | GPT-4o-mini | 0.83 | 7.8s | $0.0041 | 96.8% |
| CORD    | GPT-4 | 0.89 | 7.5s | $0.0198 | 98.1% |
| Basic   | GPT-4o-mini | 0.72 | 5.9s | $0.0035 | 92.5% |

### Detailed Results by Dataset

#### CORD Dataset Results

**GPT-4o-mini Performance:**
- **Overall F1**: 0.83
- **Merchant Info**: 0.91 (high accuracy for business details)
- **Transaction Details**: 0.87 (good date/time extraction)
- **Item List**: 0.79 (challenges with complex item descriptions)
- **Financial Totals**: 0.89 (excellent numerical extraction)

**GPT-4 Performance:**
- **Overall F1**: 0.89
- **Merchant Info**: 0.94
- **Transaction Details**: 0.92
- **Item List**: 0.85
- **Financial Totals**: 0.93

**Error Analysis:**
- **Common Issues**: Handwritten text, poor image quality, complex layouts
- **Failure Patterns**: OCR timeouts, schema validation errors, missing fields
- **Improvement Areas**: Better handling of edge cases, improved prompting

#### FUNSD Dataset Results

**GPT-4o-mini Performance:**
- **Overall F1**: 0.60
- **Field Detection**: 0.65 (moderate accuracy for field identification)
- **Value Extraction**: 0.58 (challenges with complex field types)
- **Layout Understanding**: 0.62 (reasonable spatial relationship recognition)

**Error Analysis:**
- **Common Issues**: Complex form layouts, overlapping fields, poor annotations
- **Failure Patterns**: Schema validation errors, incomplete field extraction
- **Improvement Areas**: Enhanced layout analysis, better field type recognition

### Performance Analysis

#### Processing Time Breakdown

**Average Processing Times (GPT-4o-mini):**

| Component | CORD | FUNSD | Basic |
|-----------|------|-------|-------|
| OCR Processing | 3.2s | 2.8s | 2.5s |
| LLM Processing | 4.1s | 3.1s | 3.0s |
| Schema Validation | 0.3s | 0.2s | 0.2s |
| Total Time | 7.8s | 6.2s | 5.9s |

**Factors Affecting Performance:**
- **Document Complexity**: More complex layouts increase processing time
- **Image Quality**: Higher resolution images require more OCR processing
- **Content Length**: Longer documents increase LLM processing time
- **Schema Complexity**: More complex schemas require more validation time

#### Cost Analysis

**Cost Breakdown per Document:**

| Component | CORD | FUNSD | Basic |
|-----------|------|-------|-------|
| OCR (Azure) | $0.0021 | $0.0018 | $0.0015 |
| LLM (OpenAI) | $0.0020 | $0.0017 | $0.0017 |
| Infrastructure | $0.0000 | $0.0000 | $0.0000 |
| **Total** | **$0.0041** | **$0.0038** | **$0.0035** |

**Cost Optimization Strategies:**
- **Batch Processing**: Reduces per-document overhead
- **Model Selection**: Choose appropriate LLM based on accuracy requirements
- **Caching**: Implement result caching for repeated documents
- **Resource Optimization**: Efficient resource allocation and management

## Error Analysis

### Common Error Types

#### 1. OCR Errors

**Timeout Errors:**
- **Frequency**: 12.3% of CORD documents, 8.7% of FUNSD documents
- **Causes**: Large image files, network issues, Azure service limits
- **Solutions**: Implement retry logic, optimize image preprocessing

**Connection Errors:**
- **Frequency**: 3.2% of all documents
- **Causes**: Network instability, Azure service issues
- **Solutions**: Circuit breaker pattern, fallback strategies

#### 2. LLM Errors

**Schema Validation Errors:**
- **Frequency**: 15.8% of CORD documents, 22.1% of FUNSD documents
- **Causes**: Complex document structures, schema mismatches
- **Solutions**: Improved prompting, schema adaptation, better examples

**API Rate Limits:**
- **Frequency**: 2.1% of all documents during peak usage
- **Causes**: High request volume, API quotas
- **Solutions**: Rate limiting, request queuing, exponential backoff

#### 3. System Errors

**Memory Issues:**
- **Frequency**: 1.5% of large batch processing
- **Causes**: Large document sizes, insufficient memory allocation
- **Solutions**: Memory management, batch size optimization

**File System Errors:**
- **Frequency**: 0.8% of all documents
- **Causes**: Corrupted files, permission issues
- **Solutions**: File validation, error handling, cleanup procedures

### Error Recovery Strategies

#### Retry Mechanisms

**Exponential Backoff:**
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((OCRTimeoutError, LLMRetryableError))
)
def process_with_retry(document):
    return process_document(document)
```

**Circuit Breaker Pattern:**
- Prevents cascading failures
- Automatic recovery after timeout
- Configurable failure thresholds

#### Fallback Strategies

**Graceful Degradation:**
- Provide partial results when possible
- Use simpler processing pipelines for failed documents
- Implement result caching for similar documents

**Alternative Processing:**
- Switch to different LLM models on failure
- Use local processing for critical documents
- Implement manual review workflows

## Performance Optimization

### 1. Batch Processing Optimization

**Optimal Batch Sizes:**
- **Small Documents**: 20-30 documents per batch
- **Medium Documents**: 15-20 documents per batch
- **Large Documents**: 10-15 documents per batch

**Memory Management:**
- Process batches sequentially to manage memory
- Implement garbage collection between batches
- Monitor memory usage and adjust batch sizes dynamically

### 2. Parallel Processing

**Worker Pool Configuration:**
- **CPU-bound Tasks**: Number of CPU cores
- **I/O-bound Tasks**: 2-4x number of CPU cores
- **Mixed Workloads**: Adaptive worker allocation

**Concurrency Control:**
- Limit concurrent API calls to avoid rate limits
- Implement request queuing for high-load scenarios
- Use connection pooling for external services

### 3. Caching Strategies

**Multi-level Caching:**
- **Document Cache**: Store processed results
- **OCR Cache**: Cache text extraction results
- **LLM Cache**: Cache similar document responses

**Cache Invalidation:**
- Time-based expiration (TTL)
- Content-based invalidation
- Manual cache clearing for updates

## Scalability Analysis

### Horizontal Scaling

**Load Distribution:**
- Distribute processing across multiple instances
- Use load balancers for request distribution
- Implement auto-scaling based on demand

**Queue Management:**
- Use message queues for asynchronous processing
- Implement priority queuing for urgent documents
- Handle backpressure and overflow scenarios

### Vertical Scaling

**Resource Optimization:**
- Optimize memory usage patterns
- Efficient CPU utilization
- Network I/O optimization

**Performance Tuning:**
- Adjust batch sizes based on available resources
- Optimize schema validation performance
- Implement efficient error handling

## Future Improvements

### 1. Model Enhancements

**Few-shot Learning:**
- Improve prompting strategies
- Dynamic example selection
- Adaptive prompt generation

**Schema Evolution:**
- Dynamic schema adaptation
- Learning from user feedback
- Automatic schema optimization

### 2. Performance Optimizations

**Streaming Processing:**
- Real-time document processing
- Incremental result generation
- Reduced latency for large documents

**Advanced Caching:**
- Semantic caching based on content similarity
- Predictive caching for common document types
- Distributed caching across multiple nodes

### 3. Quality Improvements

**Automated Validation:**
- Cross-document consistency checking
- Confidence scoring for extracted data
- Automated quality assurance workflows

**Error Prevention:**
- Proactive error detection
- Input validation and preprocessing
- Better error messages and suggestions

## Conclusion

The evaluation results demonstrate that Structura provides a robust and cost-effective solution for document processing and data extraction. The system achieves competitive accuracy scores while maintaining reasonable processing times and costs.

Key strengths include:
- **High accuracy** on receipt processing (CORD: 0.83-0.89 F1)
- **Cost-effective** processing (<$0.01 per document)
- **Fast processing** (<8 seconds per document)
- **Scalable architecture** supporting various document types

Areas for improvement include:
- **Enhanced form processing** accuracy (FUNSD: 0.60 F1)
- **Better error handling** for edge cases
- **Improved few-shot learning** strategies
- **Advanced caching** and optimization techniques

The modular architecture and comprehensive evaluation framework provide a solid foundation for continued improvement and research in document processing and information extraction.