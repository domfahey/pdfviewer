# Logging Infrastructure

This document describes the comprehensive structured logging system implemented in the PDF Viewer application.

## Overview

The logging infrastructure provides production-ready observability with structured logging, correlation IDs, performance tracking, and rich development experience.

## Architecture

### Core Components

1. **Central Configuration** (`backend/app/core/logging.py`)
   - Environment-based logging setup
   - JSON vs console output modes
   - Structured log processors
   - Rich console integration

2. **Request Middleware** (`backend/app/middleware/logging.py`)
   - Correlation ID generation and propagation
   - Request/response timing
   - HTTP context logging
   - Error tracking

3. **Utility Functions** (`backend/app/utils/logger.py`)
   - Performance tracking decorators
   - File operation loggers
   - Exception context logging
   - Safe data serialization

## Features

### Structured Logging
- **JSON Output**: Production-ready structured logs for aggregation
- **Rich Console**: Beautiful colored output for development
- **Consistent Format**: Standardized fields across all log entries
- **Context Preservation**: Automatic context propagation

### Correlation IDs
- **Request Tracking**: Unique ID for each HTTP request
- **Async Propagation**: Context variables maintain correlation across async calls
- **Header Support**: `X-Correlation-ID` header extraction/injection
- **Service Tracing**: End-to-end request tracing capability

### Performance Monitoring
- **Operation Timing**: Automatic timing for all major operations
- **Threshold Filtering**: Only log operations exceeding minimum duration
- **Context Managers**: Easy-to-use performance tracking
- **Decorators**: Automatic performance logging for functions

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `JSON_LOGS` | `false` | Enable JSON format for production |
| `ENVIRONMENT` | `development` | Environment context for logs |

### Development vs Production

**Development Mode** (`JSON_LOGS=false`):
```python
configure_logging(
    level="DEBUG",
    json_logs=False,
    enable_correlation_id=True
)
```

**Production Mode** (`JSON_LOGS=true`):
```python
configure_logging(
    level="INFO", 
    json_logs=True,
    enable_correlation_id=True
)
```

## Usage Examples

### Basic Logging

```python
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Operation completed", user_id="123", duration_ms=45.2)

# Error logging
logger.error("Database connection failed", 
             error="Connection timeout", 
             retry_count=3)
```

### Performance Tracking

```python
from backend.app.utils.logger import PerformanceTracker

# Context manager
with PerformanceTracker("file_processing", logger, file_id="abc123") as tracker:
    # Your operation here
    process_file()
    # Automatic timing and logging

# Decorator usage
from backend.app.core.logging import log_performance

@log_performance("PDF processing")
async def process_pdf(file_path: Path):
    # Automatic performance logging
    return await heavy_pdf_operation(file_path)
```

### File Operations

```python
from backend.app.utils.logger import FileOperationLogger

file_logger = FileOperationLogger(logger)

# Upload logging
file_logger.upload_started("document.pdf", 1024000)
file_logger.upload_completed("file-123", "document.pdf", 145.23, mime_type="application/pdf")

# Processing logging
file_logger.processing_started("file-123", "metadata_extraction")
file_logger.processing_completed("file-123", "metadata_extraction", 23.45)
```

### Exception Logging

```python
from backend.app.utils.logger import log_exception_context

try:
    risky_operation()
except Exception as e:
    log_exception_context(
        logger,
        "PDF processing",
        e,
        file_id="abc123",
        operation_stage="metadata_extraction"
    )
    raise
```

## Log Format Examples

### Development Console Output

```
[13:32:46] INFO     PDF service initialized                   
           upload_dir=uploads max_file_size_mb=50.0           
           [app.services.pdf_service]                         

[13:32:47] INFO     Request started                          
           method=POST url=http://localhost:8000/api/upload  
           correlation_id=uuid-1234 user_agent=Mozilla/5.0   
           [app.middleware.logging]                           

[13:32:48] INFO     File upload completed                    
           file_id=abc-123 filename=document.pdf             
           duration_ms=145.23 success=true                   
           [app.services.pdf_service]                        
```

### Production JSON Output

```json
{
  "timestamp": "2025-07-20T13:32:46.761046Z",
  "level": "info",
  "logger": "app.services.pdf_service",
  "message": "PDF service initialized",
  "upload_dir": "uploads",
  "max_file_size_mb": 50.0,
  "correlation_id": "uuid-1234"
}

{
  "timestamp": "2025-07-20T13:32:48.234567Z", 
  "level": "info",
  "logger": "app.services.pdf_service",
  "message": "File upload completed",
  "file_id": "abc-123",
  "filename": "document.pdf",
  "duration_ms": 145.23,
  "success": true,
  "correlation_id": "uuid-1234"
}
```

## Integration Patterns

### Service Integration

```python
class PDFService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.file_logger = FileOperationLogger(self.logger)
        
    async def upload_pdf(self, file: UploadFile):
        with PerformanceTracker("PDF upload", self.logger, filename=file.filename):
            # Upload logic with automatic logging
            pass
```

### Middleware Integration

```python
# Automatic correlation ID injection
app.add_middleware(LoggingMiddleware)

# Every request gets:
# - Unique correlation ID
# - Request/response timing
# - HTTP context logging
# - Error tracking
```

### API Endpoint Integration

```python
from backend.app.middleware.logging import RequestContextLogger

@app.post("/api/upload")
async def upload_pdf(request: Request, file: UploadFile):
    with RequestContextLogger(logger, request) as log:
        log.info("Processing PDF upload", filename=file.filename)
        # Upload logic
        return response
```

## Monitoring and Observability

### Key Metrics Logged

- **Request Duration**: Time for each HTTP request
- **Operation Performance**: Timing for PDF operations
- **File Operation Metrics**: Upload/download/processing times
- **Error Rates**: Exception frequency and types
- **Resource Usage**: File sizes, page counts, memory usage

### Log Aggregation

For production deployments, structured JSON logs can be aggregated using:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd** + Elasticsearch
- **Prometheus** + Grafana (for metrics)
- **AWS CloudWatch** (for AWS deployments)
- **Google Cloud Logging** (for GCP deployments)

### Alerting

Set up alerts based on:
- Error rate thresholds
- Performance degradation
- File processing failures
- Service availability

## Best Practices

### Development
1. Use appropriate log levels (DEBUG for development details, INFO for business logic)
2. Include relevant context in all log messages
3. Use structured fields instead of string formatting
4. Test logging in both development and production modes

### Production
1. Enable JSON logging for production environments
2. Set up log aggregation and monitoring
3. Configure log retention policies
4. Monitor log volume and performance impact
5. Use correlation IDs for distributed tracing

### Security
1. Never log sensitive data (passwords, tokens, PII)
2. Sanitize user input before logging
3. Use log_dict_safely() for user-provided data
4. Be mindful of log retention and access controls

## Troubleshooting

### Common Issues

**Issue**: Logs not appearing in console
- Check LOG_LEVEL environment variable
- Verify logger configuration in main.py
- Ensure middleware is added before other middleware

**Issue**: Missing correlation IDs
- Verify LoggingMiddleware is configured
- Check that correlation_id processor is enabled
- Ensure context variables are properly set

**Issue**: Performance impact
- Adjust log levels in production
- Use min_duration_ms to filter performance logs
- Monitor log volume and processing overhead

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export JSON_LOGS=false
```

This will show detailed logging information including:
- Request/response bodies (sanitized)
- Internal operation details
- Performance timing for all operations
- Context propagation details

## Future Enhancements

Planned improvements to the logging system:

1. **Metrics Integration**: Direct integration with Prometheus metrics
2. **Trace Sampling**: Configurable trace sampling for high-volume systems
3. **Log Streaming**: Real-time log streaming for development
4. **Advanced Filtering**: More sophisticated log filtering and routing
5. **Custom Processors**: Domain-specific log processors for PDF operations