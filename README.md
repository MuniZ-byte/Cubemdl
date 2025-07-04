# LLM-Enhanced Database to Cube.dev Generator

Generate Cube.dev models and views from your PostgreSQL database with AI-powered descriptions using OpenAI.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for Cube.js server)
npm install
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

# Cube.js Configuration
CUBEJS_DEV_MODE=true
CUBEJS_API_SECRET=demo-secret-key-12345
CUBEJS_DB_TYPE=postgres

# SQL API Configuration
CUBEJS_PG_SQL_PORT=15432
CUBEJS_SQL_USER=cube
CUBEJS_SQL_PASSWORD=password

# OpenAI API Key for LLM descriptions
OPENAI_API_KEY=your_openai_api_key
```

### 3. Generate Models and Start Server
```bash
# Generate LLM-enhanced models and display SQL examples
python3 test.py

# Start Cube.js server using Docker (recommended)
docker-compose up -d

# OR start using Node.js (alternative)
npm run dev
```

### 4. Access Your Analytics Platform

Once running, access these endpoints:

- 📊 **Playground**: http://localhost:4000 (Visual query builder)
- 🔗 **REST API**: http://localhost:4000/cubejs-api/v1/load
- 🐘 **SQL API**: postgresql://cube:password@localhost:15432/cube

## ✨ What Gets Generated

- **9 Cube files** (`.yml`) for each database table with LLM descriptions
- **2 View files** (`.yml`) that combine multiple cubes for business metrics
- **AI-enhanced descriptions** for cubes, measures, and dimensions
- **SQL query examples** for immediate use
- **REST API examples** for application integration

Files are saved in:
- `model/cubes/` - Individual cube definitions
- `model/views/` - Business metric views

## 🎯 Live Examples from Generated Models

Based on your current ecommerce database with 99,441 customers:

### REST API Query Examples
```bash
# Count total customers
curl -G 'http://localhost:4000/cubejs-api/v1/load' \
  --data-urlencode 'query={"measures":["customers.count"]}'

# Orders by status with customer demographics  
curl -G 'http://localhost:4000/cubejs-api/v1/load' \
  --data-urlencode 'query={
    "measures":["orders.count","order_items.total_price"],
    "dimensions":["orders.order_status","customers.customer_state"],
    "limit":10
  }'

# Monthly revenue trend
curl -G 'http://localhost:4000/cubejs-api/v1/load' \
  --data-urlencode 'query={
    "measures":["order_items.total_price"],
    "timeDimensions":[{
      "dimension":"orders.order_purchase_timestamp",
      "dateRange":"Last 12 months",
      "granularity":"month"
    }]
  }'
```

### SQL API Query Examples
```sql
-- Connect: psql -h localhost -p 15432 -U cube cube

-- Count customers by state
SELECT customer_state, MEASURE(count) 
FROM customers 
GROUP BY 1 
ORDER BY 2 DESC 
LIMIT 10;

-- Product performance analysis
SELECT 
  products.product_category_name,
  MEASURE(order_items.count) as items_sold,
  MEASURE(order_items.total_price) as revenue
FROM order_items
CROSS JOIN products  
GROUP BY 1
ORDER BY 3 DESC
LIMIT 10;

-- Monthly order trend with delivery analysis
SELECT 
  DATE_TRUNC('month', orders.order_purchase_timestamp) as month,
  MEASURE(orders.count) as total_orders,
  MEASURE(orders.avg_delivery_days) as avg_delivery_time
FROM orders
WHERE orders.order_purchase_timestamp >= '2024-01-01'
GROUP BY 1
ORDER BY 1;
```

## 🔧 Customization

### Generate Specific Tables Only
Edit `test.py` and change:
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

## 📁 Project Structure

```
├── model/                           # Generated Cube.dev models
│   ├── cubes/                       # Individual cube definitions
│   │   ├── customers.yml           # Customer demographics cube
│   │   ├── orders.yml              # Order transactions cube  
│   │   ├── order_items.yml         # Order line items cube
│   │   ├── products.yml            # Product catalog cube
│   │   └── ...                     # Additional cubes
│   └── views/                      # Business metric views
│       ├── business_metrics.yml    # Key business KPIs
│       └── dimension_catalog.yml   # Dimension relationships
├── llm_database_generator.py       # Main generator with LLM integration
├── enhanced_database_to_cubedev.py # Enhanced cube generation logic
├── database_to_cubedev.py          # Core database introspection
├── llm_descriptions.py             # OpenAI integration for descriptions
├── cubedev_config.py               # Configuration rules
├── cubedev_utils.py                # Utility functions
├── test.py                         # Complete model generation + examples
├── example_usage.py                # Simple usage example
├── sql_query_examples.py           # SQL query generation examples
├── docker-compose.yml              # Docker deployment setup
├── package.json                    # Node.js dependencies
├── index.js                        # Cube.js server entry point
├── .env                            # Environment configuration
└── requirements.txt                # Python dependencies
```

## 🐳 Docker Deployment (Recommended)

The easiest way to run Cube.js with your generated models:

```bash
# Start the complete stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The Docker setup includes:
- ✅ Cube.js server with your models auto-loaded
- ✅ SQL API enabled on port 15432
- ✅ Web UI on port 4000
- ✅ Auto-restart on configuration changes

## 🔄 Development Workflow

### 1. Generate/Regenerate Models
```bash
# Generate fresh models with latest database schema
python3 test.py
```

### 2. Deploy to Cube.js
```bash
# Restart to pick up new models
docker-compose restart

# Or for Node.js deployment
npm run dev
```

### 3. Test and Iterate
```bash
# Test API endpoints
curl -s "http://localhost:4000/cubejs-api/v1/meta" | python3 -m json.tool

# Test specific queries
python3 sql_query_examples.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Container won't start**: Check Docker logs
   ```bash
   docker-compose logs cube
   ```

2. **Models not loading**: Verify file permissions and restart
   ```bash
   ls -la model/cubes/
   docker-compose restart
   ```

3. **Database connection errors**: Check `.env` credentials
   ```bash
   # Test connection directly
   psql -h $CUBEJS_DB_HOST -p $CUBEJS_DB_PORT -U $CUBEJS_DB_USER -d $CUBEJS_DB_NAME
   ```

4. **LLM API errors**: Verify OpenAI API key and quota
   ```bash
   curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
   ```

### Reset and Clean Start
```bash
# Stop everything
docker-compose down

# Remove generated models
rm -rf model/cubes/* model/views/*

# Regenerate everything
python3 test.py

# Start fresh
docker-compose up -d
```

## 🚀 API Usage

### Python Integration
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
    openai_api_key="your-api-key",
    model_name="gpt-3.5-turbo"
)

print(f"Generated {stats['cubes_generated']} cubes and {stats['views_generated']} views")
print(f"LLM descriptions: {stats['llm_descriptions']}")
```

### Query Your Running Instance

#### Using requests (Python)
```python
import requests
import json

# Query the REST API
response = requests.get('http://localhost:4000/cubejs-api/v1/load', 
    params={'query': json.dumps({
        "measures": ["customers.count"],
        "dimensions": ["customers.customer_state"]
    })})

data = response.json()
print(f"Results: {data['data']}")
```

#### Using psycopg2 (Python)
```python
import psycopg2
import pandas as pd

# Connect to SQL API
conn = psycopg2.connect(
    host="localhost", port=15432, database="cube",
    user="cube", password="password"
)

# Query using familiar SQL
df = pd.read_sql("""
    SELECT 
        customer_state,
        MEASURE(count) as customer_count
    FROM customers 
    GROUP BY 1 
    ORDER BY 2 DESC 
    LIMIT 10
""", conn)

print(df)
```

## 🔗 Connecting BI Tools

### Grafana
1. Add PostgreSQL datasource
2. Host: `localhost`, Port: `15432` 
3. Database: `cube`, User: `cube`, Password: `password`
4. Query your cubes as regular tables

### Tableau  
1. Connect via PostgreSQL driver
2. Server: `localhost`, Port: `15432`
3. Database: `cube`
4. Use generated cube names as table names

### Power BI
1. Get Data → PostgreSQL database
2. Server: `localhost:15432`, Database: `cube`
3. Import or DirectQuery your cube models

### Metabase
1. Add Database → PostgreSQL
2. Host: `localhost`, Port: `15432`
3. Database name: `cube`
4. Explore your generated cubes

## Generating SQL from Cube.dev Models

Once you have generated your Cube.dev YAML models, you can query them to generate SQL in several ways:

### 1. Using Cube.dev SQL API

The SQL API allows you to query your cubes using PostgreSQL-compatible SQL syntax:

#### Setup SQL API
```bash
# Start Cube.dev with SQL API enabled
export CUBEJS_PG_SQL_PORT=15432
export CUBEJS_SQL_USER=cube
export CUBEJS_SQL_PASSWORD=password
npm run dev
```

#### Connect and Query
```bash
# Connect using psql
PGPASSWORD=password psql -h localhost -p 15432 -U cube cube

# Query your cubes as tables
SELECT status, MEASURE(count) 
FROM orders 
WHERE status = 'completed' 
GROUP BY 1;
```

#### HTTP SQL API
```bash
curl -X POST \
  -H "Authorization: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT status, MEASURE(count) FROM orders GROUP BY 1"}' \
  http://localhost:4000/cubejs-api/v1/cubesql
```

### 2. Using Cube.dev REST API

Query using JSON format to generate analytics queries:

```bash
curl -H "Authorization: YOUR_TOKEN" \
  -G \
  --data-urlencode 'query={
    "dimensions": ["orders.status"],
    "measures": ["orders.count"],
    "filters": [{
      "member": "orders.status",
      "operator": "equals",
      "values": ["completed"]
    }],
    "timeDimensions": [{
      "dimension": "orders.created_at",
      "dateRange": ["2024-01-01", "2024-12-31"],
      "granularity": "month"
    }]
  }' \
  http://localhost:4000/cubejs-api/v1/load
```

### 3. Data Model Mapping

In your generated models, each element maps to SQL as follows:

| Model Element | SQL Equivalent | Example |
|---------------|----------------|---------|
| Cube | Table | `FROM orders` |
| Dimension | Column (GROUP BY) | `SELECT status FROM orders GROUP BY 1` |
| Measure | Aggregated Column | `SELECT MEASURE(count) FROM orders` |
| Segment | Boolean Filter | `WHERE is_completed IS TRUE` |

### 4. Query Examples

#### Basic Aggregation
```sql
-- Count orders by status
SELECT status, MEASURE(count) 
FROM orders 
GROUP BY 1;
```

#### Time-based Analysis
```sql
-- Monthly revenue trend
SELECT 
  DATE_TRUNC('month', created_at) as month,
  MEASURE(total_amount)
FROM orders
WHERE created_at >= '2024-01-01'
GROUP BY 1
ORDER BY 1;
```

#### Cross-cube Joins
```sql
-- Orders with customer information
SELECT 
  customers.country,
  orders.status,
  MEASURE(orders.count)
FROM orders
CROSS JOIN customers
GROUP BY 1, 2;
```

#### Complex Filtering
```sql
-- High-value completed orders
SELECT 
  status,
  MEASURE(count),
  MEASURE(total_amount)
FROM orders
WHERE status = 'completed' 
  AND amount > 100
GROUP BY 1;
```

### 5. Using BI Tools

Connect popular BI tools to query your cubes:

- **Tableau**: Connect via PostgreSQL driver to `localhost:15432`
- **Power BI**: Use PostgreSQL connector with SQL API credentials
- **Grafana**: Add PostgreSQL datasource pointing to Cube SQL API
- **Metabase**: Connect as PostgreSQL database
- **Jupyter/Python**: Use `psycopg2` or `sqlalchemy` with PostgreSQL connection

### 6. Programmatic Access

#### Python Example
```python
import psycopg2
import pandas as pd

# Connect to Cube SQL API
conn = psycopg2.connect(
    host="localhost",
    port=15432,
    database="cube",
    user="cube",
    password="password"
)

# Query your cubes
df = pd.read_sql("""
    SELECT 
        customers.country,
        DATE_TRUNC('month', orders.created_at) as month,
        MEASURE(orders.count) as order_count,
        MEASURE(orders.total_amount) as revenue
    FROM orders 
    CROSS JOIN customers
    WHERE orders.created_at >= '2024-01-01'
    GROUP BY 1, 2
    ORDER BY 1, 2
""", conn)

print(df.head())
```

#### JavaScript/Node.js Example
```javascript
const { Client } = require('pg');

const client = new Client({
  host: 'localhost',
  port: 15432,
  database: 'cube',
  user: 'cube',
  password: 'password'
});

await client.connect();

const result = await client.query(`
  SELECT status, MEASURE(count) 
  FROM orders 
  GROUP BY 1
`);

console.log(result.rows);
```

### 7. Advanced Features

#### Pre-aggregations
Pre-aggregations speed up queries by pre-computing results:

```yaml
# In your cube YAML
pre_aggregations:
- name: orders_by_status
  measures: [count, total_amount]
  dimensions: [status]
  time_dimension: created_at
  granularity: day
```

#### Real-time Updates
Use WebSocket for real-time data:

```javascript
import cube from '@cubejs-client/core';
import WebSocketTransport from '@cubejs-client/ws-transport';

const cubeApi = cube({
  transport: new WebSocketTransport({
    authorization: 'YOUR_TOKEN',
    apiUrl: 'ws://localhost:4000/'
  })
});

// Subscribe to real-time updates
cubeApi.subscribe({
  measures: ['orders.count'],
  dimensions: ['orders.status']
}, (result) => {
  console.log('Real-time update:', result);
});
```

## 🎯 Next Steps

1. **Review Generated Models**: Check files in `model/cubes/` and `model/views/`
2. **Customize as Needed**: Edit YAML files to add custom measures, dimensions, or joins
3. **Connect Your Tools**: Use the SQL API or REST API with your BI tools
4. **Build Dashboards**: Create visualizations using the playground at http://localhost:4000
5. **Automate Updates**: Re-run `python3 test.py` when your database schema changes
6. **Scale Up**: Deploy to production using Docker or Kubernetes

## 🤝 Contributing

This project combines database introspection, AI-powered descriptions, and modern analytics infrastructure. 

To contribute:
1. Fork the repository
2. Make your changes
3. Test with different database schemas
4. Submit a pull request

## 📄 License

Open source project for educational and commercial use.

---

**Need Help?** 
- Check the troubleshooting section above
- Review the generated files in `model/` 
- Test queries using the playground at http://localhost:4000
- Verify your `.env` configuration

**Working Example**: This README reflects a working deployment with 9 cubes and 2 views generated from an ecommerce PostgreSQL database, serving 99,441+ customer records through both SQL and REST APIs.
