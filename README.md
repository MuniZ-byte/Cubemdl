# PostgreSQL to Cube.dev YAML Generator

A powerful Python tool that connects to PostgreSQL databases, introspects the schema, and generates Cube.dev-compatible YAML files (cubes and views) following universal templates.

## Features

- **Database Introspection**: Automatically analyzes PostgreSQL schema structure
- **Smart YAML Generation**: Creates cubes, views, measures, dimensions, and relationships
- **Domain-Aware Logic**: Supports ecommerce, SaaS, finance, and other business domains
- **LLM-Enhanced Descriptions**: Optional OpenAI integration for meaningful business descriptions
- **Flexible Output**: Organizes files into cubes/ and views/ directories

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database connection
cp .env.example .env
# Edit .env with your PostgreSQL connection details
```

### Basic Usage

```bash
# Generate YAML files using environment variables
python enhanced_postgres_to_cubedev.py --config-file .env --domain ecommerce

# Or specify connection parameters directly  
python enhanced_postgres_to_cubedev.py \
  --host localhost \
  --database mydb \
  --username admin \
  --password secret \
  --schema public \
  --domain ecommerce
```

### LLM-Enhanced Descriptions

```bash
# Set OpenAI API key for richer descriptions
export OPENAI_API_KEY="your-api-key"

# Run with LLM enhancement
python llm_enhanced_generator.py --config-file .env --domain ecommerce
```

## Output Structure

```
model/
├── cubes/
│   ├── orders.yml
│   ├── customers.yml
│   └── products.yml
├── views/
│   ├── business_metrics.yml
│   └── dimension_catalog.yml
└── README.md
```

## Core Files

- `enhanced_postgres_to_cubedev.py` - Main generator with domain logic
- `llm_enhanced_generator.py` - LLM-powered description generator  
- `postgres_to_cubedev.py` - Core database introspection
- `cubedev_config.py` - Configuration and templates
- `cubedev_utils.py` - Utility functions
- `llm_descriptions.py` - LLM description service

## Configuration

### Environment Variables (.env)

```bash
CUBEJS_DB_HOST=your-postgres-host
CUBEJS_DB_NAME=your-database
CUBEJS_DB_USER=your-username
CUBEJS_DB_PASS=your-password
CUBEJS_DB_PORT=5432
CUBEJS_DB_SCHEMA=public

# Optional: OpenAI API key for enhanced descriptions
OPENAI_API_KEY=your-openai-key
```

### Supported Domains

- `ecommerce` - Orders, products, customers, payments
- `saas` - Users, subscriptions, features, usage  
- `finance` - Transactions, accounts, portfolios
- `generic` - Universal templates

## Description Generation

The tool generates descriptions in three ways:

1. **Basic Templates** (default): Simple pattern-based descriptions
2. **Enhanced Templates**: Smart pattern recognition with domain awareness
3. **LLM-Generated**: OpenAI-powered business-friendly descriptions

### Examples

**Basic**: "Data cube for Sellers analysis"
**Enhanced**: "Sellers master data and attributes"
**LLM**: "Marketplace seller directory with geographic and contact information"

## Usage Examples

### Generate for Specific Tables

```bash
python enhanced_postgres_to_cubedev.py \
  --config-file .env \
  --tables orders customers products \
  --domain ecommerce
```

### Custom Output Directory

```bash
python enhanced_postgres_to_cubedev.py \
  --config-file .env \
  --output-dir /path/to/cube-project/model
```

## Integration with Cube.dev

1. Generate YAML files using this tool
2. Copy output to your Cube.dev project's `model/` directory
3. Start Cube.dev development server:

```bash
npm run dev
```

## License

MIT License - see LICENSE file for details.
