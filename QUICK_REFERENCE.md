# Quick Reference: Generated YAML Files

## Cube Files Structure

### Standard Cube Template
```yaml
cubes:
- name: cube_name
  sql_table: schema.table_name
  description: "Business description"
  
  measures:
    - Basic counts (count, count_distinct)
    - Aggregations (sum, avg, min, max)
    - Domain-specific measures
    
  dimensions:
    - Primary keys
    - Foreign keys  
    - Business attributes
    - Time dimensions with granularities
    
  joins:
    - Relationships to other cubes
    - many_to_one, one_to_many patterns
    
  segments: (optional)
    - Business filters
```

## Cube Types by Business Function

### 📊 **Transaction/Fact Cubes**
- `order_items.yml` - Line item details, revenue analysis
- `order_payments.yml` - Payment transactions, financial metrics

### 👥 **Master Data/Dimension Cubes**  
- `customers.yml` - Customer demographics, segmentation
- `products.yml` - Product catalog, category analysis
- `sellers.yml` - Vendor information, performance tracking

### 🔗 **Reference Data Cubes**
- `geolocation.yml` - Geographic coordinates, regional data
- `product_category_name_translations.yml` - Localization data

### 📝 **Relationship/Activity Cubes**
- `orders.yml` - Order headers, status tracking
- `order_reviews.yml` - Customer feedback, satisfaction metrics

## View Files Structure

### Business Views Template
```yaml
views:
- name: view_name
  description: "Business purpose"
  cubes:
  - join_path: cube1
    includes: '*'
    prefix: true
  - join_path: cube2  
    includes: '*'
    prefix: true
```

## Key Patterns

### Measure Naming Convention
- `count` - Total record count
- `count_distinct` - Unique value count  
- `sum_field` - Total aggregation
- `avg_field` - Average calculation
- `min_field` / `max_field` - Range analysis

### Dimension Types
- `string` - Text fields, IDs, categories
- `number` - Numeric attributes  
- `time` - Dates with granularities (hour, day, week, month, quarter, year)

### Join Relationships
- `many_to_one` - Child to parent (order_items → orders)
- `one_to_many` - Parent to children (orders → order_items)

## Business Intelligence Patterns

### Ecommerce Domain
- **Revenue Analysis**: order_items cube with price measures
- **Customer Segmentation**: customers cube with geographic dimensions
- **Product Performance**: products cube with category analysis
- **Operational Metrics**: orders cube with status and timing

### Time Intelligence
- All time dimensions include standard granularities
- Shipping dates, creation dates, review dates for temporal analysis
- Enables period-over-period comparisons

### Geographic Intelligence  
- City, state, ZIP code hierarchies
- Coordinate data for mapping
- Regional performance analysis capabilities

This structure enables comprehensive business analytics across all major ecommerce KPIs and operational metrics.
