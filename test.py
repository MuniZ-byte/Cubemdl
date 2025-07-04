#!/usr/bin/env python3
"""
LLM Database Generator with SQL Query Examples

This script generates Cube.dev models from your database and then shows
how to create SQL queries from the generated models.
"""

import os
import yaml
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from llm_database_generator import generate_llm_enhanced_cubes_from_engine

def load_generated_models(model_dir="model"):
    """Load the generated Cube.dev models from YAML files"""
    models = {
        'cubes': {},
        'views': {}
    }
    
    # Load cubes
    cubes_dir = os.path.join(model_dir, "cubes")
    if os.path.exists(cubes_dir):
        for file in os.listdir(cubes_dir):
            if file.endswith('.yml'):
                with open(os.path.join(cubes_dir, file), 'r') as f:
                    cube_data = yaml.safe_load(f)
                    if 'cubes' in cube_data:
                        for cube in cube_data['cubes']:
                            models['cubes'][cube['name']] = cube
    
    # Load views
    views_dir = os.path.join(model_dir, "views")
    if os.path.exists(views_dir):
        for file in os.listdir(views_dir):
            if file.endswith('.yml'):
                with open(os.path.join(views_dir, file), 'r') as f:
                    view_data = yaml.safe_load(f)
                    if 'views' in view_data:
                        for view in view_data['views']:
                            models['views'][view['name']] = view
    
    return models

def generate_sql_examples(models):
    """Generate SQL query examples from the loaded models"""
    examples = []
    
    for cube_name, cube in models['cubes'].items():
        # Basic count
        examples.append({
            'title': f'Count all {cube_name}',
            'sql': f'SELECT MEASURE(count) FROM {cube_name};',
            'description': f'Get total number of records in {cube_name}'
        })
        
        # Group by first dimension
        if 'dimensions' in cube and len(cube['dimensions']) > 0:
            dim = cube['dimensions'][0]['name']
            examples.append({
                'title': f'Group {cube_name} by {dim}',
                'sql': f'SELECT {dim}, MEASURE(count) FROM {cube_name} GROUP BY 1 ORDER BY 2 DESC LIMIT 10;',
                'description': f'Top 10 {dim} values by count'
            })
        
        # Multiple measures
        measures = [m['name'] for m in cube.get('measures', []) if m['name'] != 'count']
        if measures:
            measure = measures[0]
            examples.append({
                'title': f'{cube_name} summary with {measure}',
                'sql': f'SELECT MEASURE(count) as total_records, MEASURE({measure}) as {measure}_value FROM {cube_name};',
                'description': f'Summary statistics for {cube_name}'
            })
        
        # Time-based if time dimension exists
        time_dims = [d for d in cube.get('dimensions', []) if d.get('type') == 'time']
        if time_dims:
            time_dim = time_dims[0]['name']
            examples.append({
                'title': f'{cube_name} monthly trend',
                'sql': f"""SELECT 
  DATE_TRUNC('month', {time_dim}) as month,
  MEASURE(count) as record_count
FROM {cube_name}
WHERE {time_dim} >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 1
ORDER BY 1;""",
                'description': f'Monthly trend for {cube_name} over last 12 months'
            })
    
    return examples

def generate_rest_api_examples(models):
    """Generate REST API query examples"""
    examples = []
    
    for cube_name, cube in models['cubes'].items():
        # Basic count query
        query = {
            "measures": [f"{cube_name}.count"]
        }
        examples.append({
            'title': f'REST API: Count {cube_name}',
            'query': query,
            'description': f'Get total count of {cube_name} via REST API'
        })
        
        # With dimension
        if 'dimensions' in cube and len(cube['dimensions']) > 0:
            dim = cube['dimensions'][0]['name']
            query_with_dim = {
                "measures": [f"{cube_name}.count"],
                "dimensions": [f"{cube_name}.{dim}"],
                "limit": 10
            }
            examples.append({
                'title': f'REST API: {cube_name} by {dim}',
                'query': query_with_dim,
                'description': f'Group {cube_name} by {dim} via REST API'
            })
        
        # Time dimension
        time_dims = [d for d in cube.get('dimensions', []) if d.get('type') == 'time']
        if time_dims:
            time_dim = time_dims[0]['name']
            query_with_time = {
                "measures": [f"{cube_name}.count"],
                "timeDimensions": [{
                    "dimension": f"{cube_name}.{time_dim}",
                    "dateRange": "Last 12 months",
                    "granularity": "month"
                }]
            }
            examples.append({
                'title': f'REST API: {cube_name} time trend',
                'query': query_with_time,
                'description': f'Monthly trend for {cube_name} via REST API'
            })
    
    return examples

def print_sql_examples(examples):
    """Print SQL examples in a nice format"""
    print("\n" + "=" * 70)
    print("🔍 SQL QUERY EXAMPLES")
    print("=" * 70)
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print("-" * 50)
        print(f"📝 {example['description']}")
        print("💾 SQL Query:")
        print(example['sql'])

def print_rest_api_examples(examples):
    """Print REST API examples in a nice format"""
    print("\n" + "=" * 70)
    print("🌐 REST API QUERY EXAMPLES")
    print("=" * 70)
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print("-" * 50)
        print(f"📝 {example['description']}")
        print("🔗 Query JSON:")
        print(json.dumps(example['query'], indent=2))
        print("\n💡 Curl command:")
        query_json = json.dumps(example['query'])
        print(f"""curl -H "Authorization: YOUR_TOKEN" \\
  -G \\
  --data-urlencode 'query={query_json}' \\
  http://localhost:4000/cubejs-api/v1/load""")

def print_cube_dev_setup():
    """Print instructions for setting up Cube.dev"""
    print("\n" + "=" * 70)
    print("⚙️  CUBE.DEV SETUP INSTRUCTIONS")
    print("=" * 70)
    print("""
1. 🚀 Start Cube.dev development server:
   npm run dev or docker image
   
2. 🔌 Enable SQL API (optional):
   export CUBEJS_PG_SQL_PORT=15432
   export CUBEJS_SQL_USER=cube
   export CUBEJS_SQL_PASSWORD=password
   npm run dev

3. 🌐 Access Cube.dev:
   - Web UI: http://localhost:4000
   - GraphQL: http://localhost:4000/graphql
   - REST API: http://localhost:4000/cubejs-api/v1/load

4. 🔗 Connect with SQL tools (if SQL API enabled):
   psql -h localhost -p 15432 -U cube cube

5. 📊 Connect BI tools:
   - Host: localhost
   - Port: 15432 (SQL API) or use REST API
   - Database: cube
   - User: cube
   - Password: password

6. 🎯 Use the generated queries:
   - Copy SQL queries above for SQL API
   - Copy REST API queries for web applications
   - Modify filters and dimensions as needed
""")

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    # Create PostgreSQL engine from your .env variables
    db_host = os.getenv('CUBEJS_DB_HOST')
    db_port = os.getenv('CUBEJS_DB_PORT', '5432')
    db_name = os.getenv('CUBEJS_DB_NAME')
    db_user = os.getenv('CUBEJS_DB_USER')
    db_pass = os.getenv('CUBEJS_DB_PASS')
    schema = os.getenv('CUBEJS_DB_SCHEMA', 'public')
    
    # Create connection string
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    
    print("🚀 Generating LLM-enhanced Cube.dev models...")
    
    # Generate models and views with LLM descriptions
    stats = generate_llm_enhanced_cubes_from_engine(
        engine=engine,
        output_dir="model",              # Where to save the generated files
        schema=schema,                   # Your database schema
        tables=None,                     # None = process all tables, or specify: ["users", "orders"]
        generate_views=True,             # Generate view definitions
        openai_api_key=os.getenv('OPENAI_API_KEY'),  # Explicitly pass the API key
        model_name="gpt-3.5-turbo"      # LLM model to use
    )
    
    # Print results
    print("\n🎉 Generation Complete!")
    print(f"✅ Cubes Generated: {stats['cubes_generated']}")
    print(f"✅ Views Generated: {stats['views_generated']}")
    print(f"✅ LLM Descriptions: {stats['llm_descriptions']}")
    
    if stats['errors']:
        print(f"⚠️  Errors: {len(stats['errors'])}")
        for error in stats['errors']:
            print(f"   - {error}")
    
    # Now generate SQL examples from the created models
    print("\n🔍 Loading generated models for SQL examples...")
    models = load_generated_models()
    
    if not models['cubes']:
        print("❌ No cube models found to generate SQL examples")
        return
    
    print(f"✅ Loaded {len(models['cubes'])} cubes and {len(models['views'])} views")
    
    # Generate and display SQL examples
    sql_examples = generate_sql_examples(models)
    print_sql_examples(sql_examples[:10])  # Show first 10 examples
    
    # Generate and display REST API examples  
    rest_examples = generate_rest_api_examples(models)
    print_rest_api_examples(rest_examples[:6])  # Show first 6 examples
    
    # Print setup instructions
    print_cube_dev_setup()
    
    print("\n🎉 Complete! Your Cube.dev models and SQL examples are ready!")
    print("📁 Generated files are in the 'model/' directory")
    print("🚀 Start Cube.dev with 'npm run dev' to use these models")

if __name__ == "__main__":
    main()
