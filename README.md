# LLM-Enhanced Database to Cube.dev Generator

Generate Cube.dev models and views from your PostgreSQL database with AI-powered descriptions using OpenAI.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database Connection
Edit `.env` file with your PostgreSQL credentials:
```env
# PostgreSQL Database Configuration
CUBEJS_DB_HOST=your_host
CUBEJS_DB_PORT=5432
CUBEJS_DB_NAME=your_database
CUBEJS_DB_USER=your_username
CUBEJS_DB_PASS=your_password
CUBEJS_DB_SCHEMA=your_schema

# OpenAI API Key for LLM descriptions
OPENAI_API_KEY=your_openai_api_key
```

### 3. Generate Models
```bash
python3 example_usage.py
```

## What Gets Generated

- **Cube files** (`.yml`) for each database table
- **View files** (`.yml`) that combine multiple cubes
- **LLM-enhanced descriptions** for cubes, measures, and dimensions
- Files saved in `model/cubes/` and `model/views/` directories

## Customization

### Generate Specific Tables Only
Edit `example_usage.py` and change:
```python
tables=["users", "orders", "products"]  # Instead of None
```

### Use Different LLM Model
```python
model_name="gpt-4"  # Instead of "gpt-3.5-turbo"
```

### Disable LLM Descriptions
```python
openai_api_key=None  # Will use fallback descriptions
```

## Example Output

Your PostgreSQL tables will be converted to Cube.dev YAML files like:
```yaml
cubes:
- name: orders
  sql_table: ecommerce.orders
  description: "Order transactions containing customer purchase data..."
  measures:
  - name: count
    type: count
    description: "Total number of orders placed"
  - name: total_amount
    sql: amount
    type: sum
    description: "Total revenue from all orders"
  dimensions:
  - name: order_id
    sql: order_id
    type: string
    description: "Unique identifier for each order"
    primary_key: true
```

## Files Structure

- `llm_database_generator.py` - Main generator with LLM integration
- `enhanced_database_to_cubedev.py` - Enhanced cube generation logic
- `database_to_cubedev.py` - Core database introspection
- `llm_descriptions.py` - OpenAI integration for descriptions
- `cubedev_config.py` - Configuration rules
- `cubedev_utils.py` - Utility functions
- `example_usage.py` - Simple usage example
- `docker-compose.yml` - Docker setup (optional)

## Troubleshooting

1. **Database Connection Issues**: Verify credentials in `.env`
2. **Permission Errors**: Ensure write access to `model/` directory
3. **LLM Errors**: Check OpenAI API key and usage limits
4. **Import Errors**: Run `pip install -r requirements.txt`

## API Usage

```python
from sqlalchemy import create_engine
from llm_database_generator import generate_llm_enhanced_cubes_from_engine

# Create your database engine
engine = create_engine("postgresql://user:pass@host:port/database")

# Generate models with LLM descriptions
stats = generate_llm_enhanced_cubes_from_engine(
    engine=engine,
    output_dir="model",
    schema="your_schema",
    generate_views=True,
    openai_api_key="your-api-key"
)

print(f"Generated {stats['cubes_generated']} cubes and {stats['views_generated']} views")
```

## Next Steps

1. Review generated files in `model/` directory
2. Customize YAML files as needed
3. Use with Cube.dev framework
4. Re-run generator when schema changes
