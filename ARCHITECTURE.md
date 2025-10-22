# Professional Email Marketing Platform

Enterprise-grade email marketing solution with comprehensive security, performance optimization, and multi-interface support.

## Architecture Overview

This platform follows a **layered architecture** with clear separation of concerns:

### Core Layers
1. **Presentation Layer**: Multiple UI interfaces (CLI, GUI, Web)
2. **Business Logic Layer**: Email campaign processing and validation
3. **Data Access Layer**: Repository pattern with SQLite persistence
4. **Integration Layer**: External email service providers (Resend)

### Key Design Patterns
- **Repository Pattern**: Data access abstraction
- **Template Method**: Extensible email processing pipeline
- **Observer Pattern**: Event-driven statistics and monitoring
- **Strategy Pattern**: Pluggable email providers
- **Factory Pattern**: Component creation and dependency injection

## Key Dependencies

### Core Dependencies
- **Python 3.11+**: Runtime environment
- **asyncio**: Asynchronous email processing
- **SQLite**: Local database storage
- **Jinja2**: Template engine for email content
- **bleach**: HTML sanitization for security

### Email & Communication
- **resend**: Primary email service provider
- **email-validator**: Email address validation
- **requests**: HTTP client for API communication

### Security & Validation
- **cryptography**: Encryption and secure operations
- **pydantic**: Data validation and serialization
- **bandit**: Security linting and vulnerability detection

### User Interface
- **PySide6**: Modern Qt-based GUI framework
- **customtkinter**: Enhanced Tkinter interface
- **click**: Command-line interface framework

### Development & Testing
- **pytest**: Testing framework with plugins
- **coverage.py**: Code coverage analysis
- **flake8**: Code style and quality checking
- **mypy**: Static type checking

### Performance & Monitoring
- **psutil**: System resource monitoring
- **threading**: Concurrent processing capabilities
- **dataclasses**: Efficient data structures

## Project Structure

```
├── src/                     # Source code
│   ├── mailing/            # Core email functionality
│   ├── templating/         # Template engine with security
│   ├── validation/         # Email validation systems
│   ├── persistence/        # Database layer
│   ├── resend/            # Email service integration
│   ├── stats/             # Analytics and reporting
│   ├── data_loader/       # Data import systems
│   ├── security/          # Security utilities
│   ├── gui/               # PySide6 GUI
│   └── tk_gui/            # CustomTkinter GUI
├── tests/                  # Comprehensive test suite
├── docs/                   # Documentation
├── config/                 # Configuration files
├── scripts/               # Development utilities
├── data/                  # Database and sample data
└── reports/               # Coverage and audit reports
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository_url>
cd Mailing

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Alternative: Use make (requires Makefile)
make install
```

### Running the Application

#### Main Entry Points

1. **Command Line Interface (CLI)**:
   ```bash
   python main.py
   ```

2. **PySide6 GUI Application**:
   ```bash
   python -m src.gui
   ```

3. **CustomTkinter GUI**:
   ```bash
   python -m src.tk_gui
   ```

4. **Direct Module Usage**:
   ```bash
   python -c "from src.mailing import sender; sender.send_campaign()"
   ```

### Development

```bash
# Run tests
pytest
# OR using make
make test

# Run with coverage
pytest --cov=src
# OR using make
make test-cov

# Code quality checks
flake8 src/
# OR using make
make lint

# Security audit
bandit -r src/
# OR using make
make security
```

## Features

- **Enterprise Security**: XSS protection, injection prevention, data sanitization
- **High Performance**: Multi-threaded processing, concurrent email validation
- **Professional UI**: Multiple interface options (CLI, GUI, Web)
- **Comprehensive Testing**: 100% test coverage with security and performance tests
- **Production Ready**: Docker support, monitoring, logging

## Architecture

This project follows enterprise software development patterns:

- **Separation of Concerns**: Clear module boundaries
- **Dependency Injection**: Configurable components
- **Test-Driven Development**: Comprehensive test coverage
- **Security First**: Multiple layers of protection
- **Performance Optimized**: Concurrent processing capabilities