# CitationMap Docker Setup

This directory contains Docker configuration files for running CitationMap in a containerized environment.

## Quick Start

### Using Docker Compose (Recommended)

1. **Start the Streamlit Dashboard:**
   ```bash
   docker-compose up citationmap
   ```
   The dashboard will be available at http://localhost:8501

2. **Use the CLI:**
   ```bash
   # Start the CLI container
   docker-compose --profile cli up -d citationmap-cli

   # Run analysis
   docker-compose exec citationmap-cli citationmap analyze <ORCID_ID> --output /app/output

   # Check statistics
   docker-compose exec citationmap-cli citationmap stats <ORCID_ID>
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t citationmap .
   ```

2. **Run the Streamlit dashboard:**
   ```bash
   docker run -p 8501:8501 citationmap
   ```

3. **Run CLI commands:**
   ```bash
   docker run -it citationmap citationmap analyze <ORCID_ID>
   ```

## Configuration

### Environment Variables

- `CITATIONMAP_CACHE_DIR`: Directory for caching API responses (default: `/app/cache`)
- `CITATIONMAP_OUTPUT_DIR`: Directory for output files (default: `/app/output`)
- `PYTHONPATH`: Python path (set to `/app/src`)

### Volumes

The Docker setup creates the following volumes:
- `./cache:/app/cache` - Persistent cache for API responses
- `./output:/app/output` - Output directory for reports and analyses
- `./config.toml:/app/config.toml:ro` - Configuration file (read-only)

## Features

### Included Software

- **Python 3.11** - Latest stable Python
- **Google Chrome** - Headless browser for PDF generation
- **ChromeDriver** - WebDriver for browser automation
- **Xvfb** - Virtual display for headless operation

### Services

1. **citationmap** - Main Streamlit dashboard service
2. **citationmap-cli** - CLI service for command-line operations

### Health Checks

The containers include health checks that verify the Streamlit service is responding correctly.

## Development

For development, you can mount your source code:

```bash
docker run -it \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  -p 8501:8501 \
  citationmap
```

## Troubleshooting

### Common Issues

1. **Chrome crashes**: Ensure adequate memory allocation for the container
2. **PDF generation fails**: Check that Chrome is properly installed and Xvfb is running
3. **Port conflicts**: Change the port mapping if 8501 is already in use

### Logs

View container logs:
```bash
docker-compose logs citationmap
```

### Container Access

Access the running container:
```bash
docker-compose exec citationmap bash
```
