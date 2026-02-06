# Terraform Defect Prediction Metrics

A tool for collecting code metrics from Terraform repositories to support defect prediction models.

## Features

- **Full History Collection**: Analyze entire repository history
- **Just-In-Time (JIT) Mode**: Analyze specific commits with optional historical context
- **Delta Metrics**: Calculate differences between before/after states
- **Comprehensive Metrics**: Process, similarity, complexity, and attribute change metrics
- **Flexible Deployment**: Run as Python package, standalone script, or Docker container

## Installation

### Option 1: Python Package
```bash
pip install -e .
```

### Option 2: Docker
```bash
docker build -t tf-metrics .
```

## Usage

### As Installed Package
```bash
# Full history collection
tf-metrics /path/to/repo

# JIT mode for specific commit
tf-metrics /path/to/repo --commit abc123

# JIT mode with historical context
tf-metrics /path/to/repo --commit abc123 --history metrics.csv
```

### As Standalone Script
```bash
# Full history
python scripts/collect_metrics.py

# JIT mode
python scripts/collect_metrics.py --commit abc123 --history metrics.csv
```

### With Docker
```bash
# Full history (mount repository as volume)
docker run -v /path/to/repo:/repo tf-metrics /repo

# JIT mode
docker run -v /path/to/repo:/repo tf-metrics /repo --commit abc123

# With historical context
docker run -v /path/to/repo:/repo -v /path/to/metrics.csv:/metrics.csv tf-metrics /repo --commit abc123 --history /metrics.csv
```

## Output

The tool generates `metrics.csv` containing:
- Commit metadata (hash, author, date)
- File and block identifiers
- Code complexity metrics
- Delta metrics (changes from before to after)
- Process metrics (author experience, block history)
- Similarity and attribute change metrics

## Requirements

- Python 3.8+
- Java 17+ (for Terraform parser)
- Git repository

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Project Structure
```
├── scripts/
│   ├── collect_metrics.py    # Main entry point
│   ├── process/               # Metric calculation modules
│   ├── codes/                 # Code parsing
│   └── utility/               # Helper functions
├── tests/                     # Unit and integration tests
├── libs/                      # JAR dependencies
└── setup.py                   # Package configuration
```

## License

MIT License
