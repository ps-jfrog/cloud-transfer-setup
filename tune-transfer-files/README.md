# JFrog Artifactory Transfer Thread Tuner

This repository contains tools for monitoring and automatically tuning JFrog Artifactory transfer threads based on system metrics.

## Scripts Overview

### 1. [fetch_metrics.py](fetch_metrics.py)

A utility script to fetch metrics from JFrog Artifactory and Observability endpoints.

#### Purpose
- Fetches metrics from both Artifactory and Observability endpoints
- Saves metrics to timestamped files for analysis
- Useful for debugging and monitoring system performance

#### Usage
```bash
python fetch_metrics.py [options]
```

#### Options
- `--base-url`, `-u`: JFrog base URL (e.g., https://your-domain.jfrog.io)
- `--access-token`, `-t`: JFrog Access Token

#### Environment Variables
- `JFROG_BASE_URL`: Base URL for JFrog instance
- `JFROG_ACCESS_TOKEN`: Access token for authentication

#### Output
- Creates two files:
  - `artifactory_metrics_YYYYMMDD_HHMMSS.txt`
  - `observability_metrics_YYYYMMDD_HHMMSS.txt`

### 2. [tune-transfer-files.py](tune-transfer-files.py)

The main script for monitoring system metrics and automatically adjusting transfer threads.

#### Purpose
- Monitors system metrics (CPU, memory, database connections)
- Automatically adjusts transfer threads based on thresholds
- Provides detailed metrics output in verbose mode

#### Usage
```bash
python tune-transfer-files.py [options]
```

#### Options
- `--config`, `-c`: Path to configuration file (default: config.yaml)
- `--base-url`, `-u`: JFrog base URL
- `--access-token`, `-t`: JFrog Access Token
- `--verbose`, `-v`: Enable verbose output with detailed metrics

#### Environment Variables
- `JFROG_BASE_URL`: Base URL for JFrog instance
- `JFROG_ACCESS_TOKEN`: Access token for authentication

#### Output
- In verbose mode:
  - Displays detailed metrics tables
  - Shows system, JVM, database, and thread metrics
  - Saves raw metrics to `artifactory_metrics.txt`
- Regular mode:
  - Shows thread adjustment decisions
  - Reports basic status information

## Configuration (config.yaml)

The configuration file controls the behavior of the thread tuning script.

### Structure
```yaml
# Artifactory Configuration
artifactory:
  url: "https://<your-domain>.jfrog.io/artifactory"
  access_token: "your-access-token"

# Thread Configuration
threads:
  step: 64        # Number of threads to adjust by
  min: 8          # Minimum number of threads
  max: 1024       # Maximum number of threads

# Monitoring Configuration
monitoring:
  check_interval: 300  # Seconds between checks

# Thresholds
thresholds:
  cpu:
    low: 0.40     # CPU usage threshold for increasing threads
    high: 0.85    # CPU usage threshold for decreasing threads
  heap:
    low: 0.60     # Heap usage threshold for increasing threads
    high: 0.85    # Heap usage threshold for decreasing threads
  db_connections:
    high: 0.90    # Database connection threshold for decreasing threads
```

### Configuration Parameters

#### Artifactory Section
- `url`: Base URL for your JFrog Artifactory instance
- `access_token`: Authentication token for API access

#### Threads Section
- `step`: Number of threads to increase/decrease in each adjustment
- `min`: Minimum allowed number of transfer threads
- `max`: Maximum allowed number of transfer threads

#### Monitoring Section
- `check_interval`: Time in seconds between metric checks

#### Thresholds Section
- `cpu.low`: CPU usage threshold below which threads will be increased
- `cpu.high`: CPU usage threshold above which threads will be decreased
- `heap.low`: Heap memory usage threshold below which threads will be increased
- `heap.high`: Heap memory usage threshold above which threads will be decreased
- `db_connections.high`: Database connection threshold above which threads will be decreased

## Example Usage

1. First, fetch metrics to verify access:
```bash
python fetch_metrics.py --base-url "https://your-domain.jfrog.io" --access-token "your-token"
```

2. Run the thread tuner in verbose mode:
```bash
python tune-transfer-files.py --config config.yaml --verbose
```

3. Run with environment variables:
```bash
export JFROG_BASE_URL="https://your-domain.jfrog.io"
export JFROG_ACCESS_TOKEN="your-token"
python tune-transfer-files.py --verbose
```

## Notes

- The script requires Python 3.6 or higher
- Ensure you have the required permissions in JFrog Artifactory
- Monitor the verbose output to understand the system's behavior
- Adjust thresholds in config.yaml based on your system's characteristics
