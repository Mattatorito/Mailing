# Testing Documentation

## Overview

This document provides comprehensive guidance for testing the Professional Email Marketing Tool. Our testing strategy ensures high code quality, security, and performance across all system components.

## Testing Architecture

### Test Categories

#### 1. Unit Tests (`tests/test_*.py`)
- **Purpose**: Test individual components in isolation
- **Coverage Target**: 95%+ for core business logic
- **Location**: `tests/` directory
- **Execution**: `pytest tests/`

#### 2. Integration Tests (`tests/test_*_integration.py`)
- **Purpose**: Test component interactions and data flow
- **Coverage Target**: 90%+ for critical integration points
- **Location**: Mixed with unit tests
- **Execution**: `pytest -m integration`

#### 3. Performance Tests (`tests/test_performance_comprehensive.py`)
- **Purpose**: Validate system performance under load
- **Metrics**: Throughput, latency, memory usage, CPU utilization
- **Execution**: `pytest -m performance`

#### 4. Security Tests (`tests/test_security_comprehensive.py`)
- **Purpose**: Identify security vulnerabilities and validate protections
- **Focus Areas**: Injection attacks, XSS, authentication, authorization
- **Execution**: `pytest -m security`

#### 5. End-to-End Tests (`tests/test_e2e_*.py`)
- **Purpose**: Test complete user workflows
- **Scope**: CLI operations, API endpoints, data processing pipelines
- **Execution**: `pytest -m e2e`

## Test Organization

### Directory Structure
```
tests/
├── test_cli.py                    # CLI interface tests
├── test_models.py                 # Data model tests
├── test_validation.py             # Input validation tests
├── test_templating.py             # Template engine tests
├── test_persistence_db.py         # Database layer tests
├── test_resend_client.py          # API client tests
├── test_performance_comprehensive.py  # Performance benchmarks
├── test_security_comprehensive.py     # Security validation
├── fixtures/                      # Test data and fixtures
│   ├── templates/                 # Test email templates
│   ├── data/                      # Sample datasets
│   └── configs/                   # Test configurations
└── conftest.py                    # Shared test configuration

```

### Test Naming Conventions

#### Files
- `test_<module_name>.py` - Standard unit tests
- `test_<module_name>_integration.py` - Integration tests
- `test_<module_name>_extended.py` - Comprehensive test suites

#### Functions
- `test_<functionality>()` - Basic functionality tests
- `test_<functionality>_edge_cases()` - Edge case validation
- `test_<functionality>_error_handling()` - Error condition tests
- `test_<functionality>_performance()` - Performance validation

#### Classes
- `Test<ComponentName>` - Main test class for component
- `Test<ComponentName>Integration` - Integration test class
- `Test<ComponentName>Security` - Security test class

## Test Configuration

### pytest.ini Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=mailing
    --cov=data_loader
    --cov=templating
    --cov=validation
    --cov=resend
    --cov=persistence
    --cov=stats
    --cov=gui
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=90
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    security: marks tests as security tests
    e2e: marks tests as end-to-end tests
    gui: marks tests that require GUI components
```

### Environment Setup

#### Test Dependencies
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock
pip install coverage diff-cover bandit safety
pip install psutil  # For performance monitoring
```

#### Test Database
```python
# Separate test database configuration
SQLITE_DB_PATH = "test_mailing.sqlite3"
TEST_MODE = True
```

## Writing Tests

### Unit Test Best Practices

#### 1. Test Structure (Arrange-Act-Assert)
```python
def test_email_validation():
    # Arrange
    validator = EmailValidator()
    test_email = "user@example.com"
    
    # Act
    result = validator.is_valid(test_email)
    
    # Assert
    assert result is True
```

#### 2. Descriptive Test Names
```python
def test_email_validator_rejects_invalid_domain():
    """Test that email validator properly rejects emails with invalid domains."""
    pass

def test_campaign_sender_handles_rate_limiting():
    """Test that campaign sender respects API rate limits."""
    pass
```

#### 3. Test Data Management
```python
@pytest.fixture
def sample_recipients():
    """Provide sample recipient data for testing."""
    return [
        Recipient(email="user1@test.com", name="User One"),
        Recipient(email="user2@test.com", name="User Two"),
    ]

def test_campaign_processing(sample_recipients):
    # Use fixture data
    pass
```

#### 4. Mocking External Dependencies
```python
@patch('resend.client.httpx')
def test_api_client_error_handling(mock_httpx):
    # Mock external HTTP calls
    mock_httpx.post.side_effect = httpx.RequestError("Network error")
    
    client = ResendClient()
    with pytest.raises(ResendError):
        client.send_message("test@example.com", "Subject", "Body")
```

### Integration Test Guidelines

#### 1. Database Integration
```python
@pytest.fixture
def test_database():
    """Provide isolated test database."""
    db_path = ":memory:"  # Use in-memory SQLite
    db = DatabaseManager(db_path)
    db.initialize()
    yield db
    db.close()

def test_delivery_repository_integration(test_database):
    repo = DeliveryRepository(test_database)
    # Test actual database operations
```

#### 2. API Integration
```python
@pytest.mark.integration
async def test_resend_api_integration():
    """Test actual API integration (requires API key)."""
    if not os.getenv("RESEND_API_KEY"):
        pytest.skip("API key not available for integration test")
    
    client = ResendClient()
    # Test real API calls with test data
```

### Performance Test Guidelines

#### 1. Benchmark Structure
```python
@pytest.mark.performance
def test_email_validation_performance():
    """Benchmark email validation throughput."""
    validator = EmailValidator()
    emails = [f"user{i}@domain{i}.com" for i in range(10000)]
    
    start_time = time.time()
    for email in emails:
        validator.is_valid(email)
    elapsed = time.time() - start_time
    
    throughput = len(emails) / elapsed
    assert throughput > 1000, f"Validation too slow: {throughput}/sec"
```

#### 2. Memory Usage Testing
```python
def test_memory_efficiency():
    """Test memory usage during large operations."""
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operation
    large_dataset = load_large_dataset()
    process_dataset(large_dataset)
    
    final_memory = process.memory_info().rss
    memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
    
    assert memory_growth < 100, f"Excessive memory usage: {memory_growth}MB"
```

### Security Test Guidelines

#### 1. Input Validation Testing
```python
@pytest.mark.security
def test_email_injection_protection():
    """Test protection against email header injection."""
    malicious_email = "user@domain.com\r\nBcc: attacker@evil.com"
    
    validator = EmailValidator()
    assert not validator.is_valid(malicious_email)
```

#### 2. XSS Protection Testing
```python
@pytest.mark.security
def test_template_xss_protection():
    """Test XSS protection in template rendering."""
    xss_payload = '<script>alert("XSS")</script>'
    
    engine = TemplateEngine()
    html_result, _ = engine.render("test_template.html", {
        'user_input': xss_payload
    })
    
    assert '<script>' not in html_result
    assert '&lt;script&gt;' in html_result  # Should be escaped
```

## Test Execution

### Local Development

#### Run All Tests
```bash
pytest
```

#### Run Specific Test Categories
```bash
pytest -m "not slow"           # Skip slow tests
pytest -m integration         # Integration tests only
pytest -m performance         # Performance tests only
pytest -m security           # Security tests only
```

#### Run Tests with Coverage
```bash
pytest --cov=. --cov-report=html
```

#### Run Tests in Parallel
```bash
pytest -n auto  # Requires pytest-xdist
```

### Continuous Integration

#### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Coverage Requirements

### Coverage Targets by Component

| Component | Target Coverage | Current Coverage |
|-----------|----------------|------------------|
| Core Business Logic | 95% | 95%+ |
| Data Models | 100% | 100% |
| Validation | 95% | 95% |
| Database Layer | 90% | 97% |
| API Clients | 90% | 100% |
| Template Engine | 95% | 93% |
| CLI Interface | 85% | 89% |
| GUI Components | 80% | 92% |
| **Overall Project** | **90%** | **93%** |

### Coverage Analysis

#### Generate Coverage Reports
```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

#### Coverage Exclusions
```python
# Use pragma comments for uncoverable code
def emergency_shutdown():
    sys.exit(1)  # pragma: no cover

# Exclude test files from coverage
# File: .coveragerc
[run]
omit = 
    tests/*
    */tests/*
    test_*.py
```

## Quality Assurance

### Code Quality Tools

#### Static Analysis
```bash
# Type checking
mypy mailing/ data_loader/ validation/

# Code style
black --check .
isort --check-only .

# Linting
flake8 .

# Security scanning
bandit -r .
safety check
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort

- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
  - id: flake8

- repo: local
  hooks:
  - id: tests
    name: tests
    entry: pytest
    language: system
    pass_filenames: false
    always_run: true
```

### Test Data Management

#### Test Fixtures
```python
# conftest.py
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        'database_url': ':memory:',
        'api_timeout': 5,
        'batch_size': 100
    }

@pytest.fixture
def sample_template():
    """Provide sample email template."""
    return """
    <html>
    <body>
        <h1>Hello {{name}}!</h1>
        <p>Welcome to {{company}}.</p>
    </body>
    </html>
    """
```

#### Test Data Files
```
tests/fixtures/
├── templates/
│   ├── welcome.html
│   ├── newsletter.html
│   └── notification.html
├── data/
│   ├── sample_recipients.csv
│   ├── test_campaigns.json
│   └── performance_data.xlsx
└── configs/
    ├── test_settings.py
    └── ci_config.yaml
```

## Debugging Tests

### Common Debugging Techniques

#### 1. Verbose Output
```bash
pytest -v -s  # Show print statements
```

#### 2. Debug Specific Test
```bash
pytest tests/test_models.py::test_recipient_validation -v -s
```

#### 3. Drop into Debugger
```python
def test_complex_logic():
    # ... test setup
    import pdb; pdb.set_trace()  # Debugger breakpoint
    # ... test execution
```

#### 4. Temporary Skip
```python
@pytest.mark.skip(reason="Debugging in progress")
def test_problematic_function():
    pass
```

### Performance Debugging

#### 1. Profile Tests
```bash
pytest --profile-svg  # Requires pytest-profiling
```

#### 2. Memory Profiling
```python
from memory_profiler import profile

@profile
def test_memory_intensive_operation():
    # Test implementation
    pass
```

## Best Practices Summary

### Development Workflow
1. **Write tests first** (TDD approach when possible)
2. **Run tests frequently** during development
3. **Maintain high coverage** (90%+ target)
4. **Use descriptive names** for tests and assertions
5. **Keep tests independent** and idempotent
6. **Mock external dependencies** appropriately
7. **Test edge cases** and error conditions
8. **Document complex test logic**

### Maintenance
1. **Update tests** when requirements change
2. **Remove obsolete tests** during refactoring
3. **Monitor test performance** and optimize slow tests
4. **Review test failures** promptly
5. **Keep test data current** and relevant

### Team Collaboration
1. **Include tests** in code reviews
2. **Share testing patterns** across the team
3. **Document testing decisions** and rationale
4. **Communicate coverage goals** clearly
5. **Celebrate testing achievements** and milestones

## Troubleshooting

### Common Issues

#### 1. Test Database Issues
```python
# Ensure clean database state
@pytest.fixture(autouse=True)
def clean_database():
    db.clear_all_tables()
    yield
    db.clear_all_tables()
```

#### 2. Async Test Issues
```python
# Proper async test setup
@pytest.mark.asyncio
async def test_async_function():
    result = await async_operation()
    assert result is not None
```

#### 3. Fixture Scope Issues
```python
# Use appropriate fixture scope
@pytest.fixture(scope="function")  # Reset for each test
def user_data():
    return {"name": "Test User"}
```

#### 4. Mock Issues
```python
# Ensure mocks are properly reset
@pytest.fixture(autouse=True)
def reset_mocks():
    yield
    Mock.reset_mock()
```

### Getting Help

- **Documentation**: Check this document and inline comments
- **Test Examples**: Review existing test files for patterns
- **Team Resources**: Consult with team leads on testing strategy
- **External Resources**: pytest documentation, testing best practices

---

**Last Updated**: 2025-10-21  
**Version**: 1.0  
**Maintainer**: Development Team