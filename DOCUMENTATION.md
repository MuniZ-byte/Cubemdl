# PostgreSQL to Cube.dev YAML Generator - Complete Documentation

## Overview

This project provides a comprehensive solution for automatically generating Cube.dev-compatible YAML files from PostgreSQL database schemas. It includes intelligent schema introspection, domain-aware logic, and optional LLM-enhanced descriptions.

---

## 📁 Project Structure

```
cubemdl/
├── Core Generator Files
├── Configuration & Utilities  
├── LLM Enhancement
├── Cube.dev Integration
├── Generated Output
└── Documentation
```

---

## 🔧 Core Generator Files

### `postgres_to_cubedev.py`
**Purpose**: Core database introspection and basic YAML generation engine

**Key Features**:
- **Database Connection**: Manages PostgreSQL connections using SQLAlchemy
- **Schema Introspection**: Analyzes tables, columns, data types, and relationships
- **Foreign Key Detection**: Identifies table relationships and join paths
- **Basic YAML Generation**: Creates fundamental cube structures

**Classes**:
- `DatabaseConfig`: Configuration for database connections
- `TableInfo`: Data structure for table metadata
- `PostgreSQLIntrospector`: Main introspection engine

**Use Cases**:
- Simple cube generation without domain logic
- Basic schema analysis and documentation
- Foundation for enhanced generators

**Example Usage**:
```python
introspector = PostgreSQLIntrospector(config)
tables = introspector.introspect_schema()
cube_data = introspector.generate_cube_definition(table)
```

---

### `enhanced_postgres_to_cubedev.py`
**Purpose**: Advanced generator with domain-aware logic and business intelligence

**Key Features**:
- **Domain Detection**: Automatically identifies business domains (ecommerce, SaaS, finance)
- **Smart Measure Generation**: Creates relevant measures based on column types and names
- **Relationship Mapping**: Generates intelligent joins between cubes
- **Table Classification**: Identifies fact tables, dimension tables, and junction tables
- **View Generation**: Creates business-focused views for different use cases

**Domain Logic**:
- **Ecommerce**: Orders, products, customers, payments, reviews
- **SaaS**: Users, subscriptions, features, usage metrics
- **Finance**: Transactions, accounts, portfolios, balances

**Classes**:
- `EnhancedCubeGenerator`: Main enhanced generation engine
- Extends `PostgreSQLIntrospector` with advanced logic

**Use Cases**:
- Production-ready cube generation
- Business-specific metric creation
- Complex schema with multiple related tables
- Enterprise data warehouse modeling

**Example Usage**:
```bash
python enhanced_postgres_to_cubedev.py \
  --host localhost \
  --database ecommerce_db \
  --domain ecommerce \
  --output-dir model
```

---

## 🎯 LLM Enhancement Files

### `llm_descriptions.py`
**Purpose**: AI-powered description generation using OpenAI

**Key Features**:
- **LLM Integration**: Uses OpenAI GPT models for intelligent descriptions
- **Fallback Mechanism**: Gracefully falls back to template-based descriptions
- **Context-Aware**: Considers table structure, sample data, and business domain
- **Smart Prompting**: Generates business-friendly, human-readable descriptions

**Classes**:
- `LLMDescriptionGenerator`: Core LLM interaction engine
- `EnhancedDescriptionService`: Service layer with fallback logic
- `TableContext`: Data structure for LLM context

**Description Quality Comparison**:
```yaml
# Basic Template
description: "Data cube for Sellers analysis"

# Enhanced Template  
description: "Sellers master data and attributes"

# LLM-Generated
description: "Marketplace seller directory with geographic and contact information for vendor performance analysis"
```

**Use Cases**:
- Enterprise documentation requirements
- Business user-friendly interfaces
- Automated documentation generation
- Multi-language description support

---

### `llm_enhanced_generator.py`
**Purpose**: Complete generator with LLM-powered descriptions

**Key Features**:
- **Full LLM Integration**: Combines enhanced generation with AI descriptions
- **Configuration Options**: Enable/disable LLM features
- **Performance Optimization**: Batches LLM requests efficiently
- **Error Handling**: Robust fallback mechanisms

**Use Cases**:
- Premium cube generation with AI descriptions
- Documentation-heavy environments
- Customer-facing analytics platforms
- Multi-tenant applications with custom descriptions

**Example Usage**:
```bash
export OPENAI_API_KEY="your-key"
python llm_enhanced_generator.py \
  --config-file .env \
  --domain ecommerce \
  --llm-model gpt-4
```

---

## ⚙️ Configuration & Utility Files

### `cubedev_config.py`
**Purpose**: Central configuration hub for all generation logic

**Key Components**:
- **Type Mappings**: PostgreSQL to Cube.dev type conversions
- **Domain Templates**: Business-specific patterns and rules
- **Measure Rules**: Automatic measure generation logic
- **View Configurations**: Template definitions for view generation

**Configuration Sections**:
```python
TYPE_MAPPINGS = {
    'integer': 'number',
    'varchar': 'string',
    'timestamp': 'time'
}

DOMAIN_SPECIFIC_RULES = {
    'ecommerce': {
        'fact_tables': ['orders', 'order_items'],
        'measures': ['revenue', 'quantity', 'profit']
    }
}
```

**Use Cases**:
- Customizing generation behavior
- Adding new business domains
- Modifying type mappings
- Extending measure generation rules

---

### `cubedev_utils.py`
**Purpose**: Utility functions and helper classes

**Key Components**:
- **CubeDevUtils**: Name sanitization, column analysis, SQL generation
- **YAMLFormatter**: YAML output formatting and validation
- **DatabaseAnalyzer**: Relationship analysis and pattern detection
- **FileManager**: File operations and directory management

**Utility Functions**:
- **Name Sanitization**: Ensures Cube.dev-compliant naming
- **SQL Generation**: Creates appropriate SQL expressions
- **Validation**: Checks cube and view definitions
- **File Operations**: Manages output directories and backups

**Use Cases**:
- Custom validation rules
- File organization strategies
- SQL expression customization
- Backup and recovery operations

---

## 🌐 Cube.dev Integration Files

### `cube.js`
**Purpose**: Main Cube.dev configuration file

**Configuration**:
- **Database Connection**: PostgreSQL connection settings
- **Security**: API secrets and authentication
- **Caching**: Memory-based caching configuration
- **Development**: Development mode settings

**Use Cases**:
- Cube.dev server configuration
- Database connection management
- Security policy definition
- Performance optimization

---

### `docker-compose.yml`
**Purpose**: Containerized deployment configuration

**Services**:
- **Cube**: Main Cube.dev service
- **Redis**: Caching and queue management
- **Environment**: Volume and network configuration

**Use Cases**:
- Development environment setup
- Production deployment
- Scaling and load balancing
- Integration testing

---

### `package.json`
**Purpose**: Node.js dependencies and scripts

**Dependencies**:
- **@cubejs-backend/cli**: Cube.dev command-line tools
- **Development Tools**: Testing and build utilities

**Use Cases**:
- Cube.dev CLI operations
- Development workflow management
- Dependency management
- Build automation

---

## 📊 Generated Output Files

### Cubes Directory (`model/cubes/`)

Each cube file represents a data entity with measures, dimensions, and relationships:

#### `orders.yml`
**Purpose**: Order transaction data cube
**Type**: Dimension/Fact Table
**Key Measures**:
- `count`: Total number of orders
- `count_distinct`: Unique order count
**Key Dimensions**:
- `order_id`: Primary key
- `customer_id`: Customer reference
- `order_status`: Order state
- `order_purchase_timestamp`: Time dimension with granularities
**Joins**: Links to customers, order_items, order_payments
**Use Cases**: Order volume analysis, status tracking, temporal analysis

#### `order_items.yml`
**Purpose**: Individual line items within orders
**Type**: Junction/Fact Table
**Key Measures**:
- `sum_price`, `avg_price`: Price analytics
- `sum_freight_value`: Shipping cost analysis
- Currency formatting for financial measures
**Key Dimensions**:
- `order_id`, `order_item_id`: Composite primary key
- `product_id`, `seller_id`: Relationship keys
- `shipping_limit_date`: Time constraints
**Joins**: Central hub connecting orders, products, sellers
**Use Cases**: Revenue analysis, shipping cost optimization, seller performance

#### `customers.yml`
**Purpose**: Customer master data
**Type**: Dimension Table
**Key Measures**:
- `count`: Customer counts
**Key Dimensions**:
- `customer_id`: Primary key
- `customer_zip_code_prefix`: Geographic segmentation
- `customer_city`, `customer_state`: Location hierarchy
**Use Cases**: Customer segmentation, geographic analysis, demographic studies

#### `products.yml`
**Purpose**: Product catalog information
**Type**: Dimension Table
**Key Measures**:
- `sum_product_weight_g`: Total weight calculations
- `avg_product_weight_g`: Weight analytics
**Key Dimensions**:
- `product_id`: Primary key
- `product_category_name`: Category classification
- `product_weight_g`, dimensions: Physical attributes
**Use Cases**: Product performance, category analysis, inventory management

#### `sellers.yml`
**Purpose**: Seller/vendor information
**Type**: Dimension Table
**Key Dimensions**:
- `seller_id`: Primary key
- Geographic dimensions: city, state, zip code
**Use Cases**: Seller performance analysis, geographic distribution, vendor management

#### `order_payments.yml`
**Purpose**: Payment transaction details
**Type**: Dimension/Fact Table
**Key Measures**:
- `sum_payment_value`: Total payment amounts
- Financial aggregations with currency formatting
**Key Dimensions**:
- `order_id`: Links to orders
- `payment_type`: Payment method classification
- `payment_installments`: Payment terms
**Use Cases**: Payment analysis, financial reporting, payment method optimization

#### `order_reviews.yml`
**Purpose**: Customer review and rating data
**Type**: Dimension Table
**Key Measures**:
- `avg_review_score`: Average ratings
- `min_review_score`, `max_review_score`: Rating ranges
**Key Dimensions**:
- `review_id`: Primary key
- `order_id`: Links to orders
- `review_creation_date`: Temporal analysis
**Use Cases**: Customer satisfaction analysis, quality metrics, feedback trends

#### `geolocation.yml`
**Purpose**: Geographic reference data
**Type**: Dimension Table
**Key Measures**:
- Geographic coordinate aggregations
**Key Dimensions**:
- `geolocation_zip_code_prefix`: Primary key
- `geolocation_lat`, `geolocation_lng`: Coordinates
- `geolocation_city`, `geolocation_state`: Location hierarchy
**Use Cases**: Geographic analysis, delivery optimization, regional performance

---

### Views Directory (`model/views/`)

Views provide business-focused perspectives across multiple cubes:

#### `business_metrics.yml`
**Purpose**: Key business KPIs and metrics
**Structure**:
```yaml
cubes:
- join_path: orders
  includes: '*'
  prefix: true
- join_path: order_items  
  includes: '*'
  prefix: true
- join_path: products
  includes: '*'
  prefix: true
```
**Use Cases**:
- Executive dashboards
- Business performance monitoring
- Cross-functional analytics
- Unified metric reporting

#### `dimension_catalog.yml`
**Purpose**: Consolidated dimensional data
**Structure**: Combines dimensional cubes with prefixed naming
**Use Cases**:
- Master data management
- Dimensional hierarchy analysis
- Reference data exploration
- Data governance

---

## 🛠️ Configuration Files

### `.env`
**Purpose**: Environment-specific configuration
**Contents**:
- Database connection parameters
- Cube.dev settings
- Optional API keys
**Security**: Contains sensitive information, not committed to git

### `.env.example`
**Purpose**: Template for environment configuration
**Use Cases**: Setup guide for new environments, documentation

### `requirements.txt`
**Purpose**: Python dependencies
**Key Dependencies**:
- `sqlalchemy`: Database connectivity
- `psycopg2-binary`: PostgreSQL driver
- `PyYAML`: YAML processing
- `openai`: LLM integration

---

## 📖 Documentation Files

### `README.md`
**Purpose**: Main project documentation
**Contents**:
- Quick start guide
- Installation instructions
- Usage examples
- Integration guidelines

### `model/README.md`
**Purpose**: Generated files index
**Contents**:
- List of generated cubes and views
- Generation metadata
- File organization guide

---

## 🔄 Use Case Scenarios

### 1. **Development Environment Setup**
```bash
# Clone and setup
git clone <repository>
cd cubemdl
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database details

# Generate cubes
python enhanced_postgres_to_cubedev.py --config-file .env --domain ecommerce
```

### 2. **Production Deployment**
```bash
# Generate optimized cubes
python enhanced_postgres_to_cubedev.py \
  --host prod-db.company.com \
  --database analytics_warehouse \
  --domain saas \
  --output-dir /opt/cube/model

# Deploy with Docker
docker-compose up -d
```

### 3. **Custom Domain Implementation**
1. Edit `cubedev_config.py` to add new domain rules
2. Define domain-specific measure patterns
3. Add table classification logic
4. Test with domain parameter: `--domain custom_domain`

### 4. **LLM-Enhanced Documentation**
```bash
# Set up OpenAI integration
export OPENAI_API_KEY="your-api-key"

# Generate with AI descriptions
python llm_enhanced_generator.py \
  --config-file .env \
  --domain ecommerce \
  --llm-model gpt-4
```

### 5. **Multi-Environment Management**
```bash
# Development
python enhanced_postgres_to_cubedev.py --config-file .env.dev --output-dir model/dev

# Staging  
python enhanced_postgres_to_cubedev.py --config-file .env.staging --output-dir model/staging

# Production
python enhanced_postgres_to_cubedev.py --config-file .env.prod --output-dir model/prod
```

---

## 🎯 Business Value

### **For Data Engineers**
- **Automation**: Eliminates manual cube creation
- **Consistency**: Standardized cube patterns
- **Maintenance**: Easy schema evolution support

### **For Business Analysts**
- **Self-Service**: Automatic metric generation
- **Documentation**: Human-readable descriptions
- **Relationships**: Pre-built joins and associations

### **For Organizations**
- **Time-to-Value**: Rapid analytics deployment
- **Scalability**: Handle large, complex schemas
- **Governance**: Consistent naming and patterns

---

This documentation provides a comprehensive guide to understanding, implementing, and extending the PostgreSQL to Cube.dev YAML Generator. Each file serves a specific purpose in creating a robust, scalable analytics platform.
