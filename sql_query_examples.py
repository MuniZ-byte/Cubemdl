#!/usr/bin/env python3
"""
SQL Query Examples for Generated Cube.dev Models

This script demonstrates different ways to generate SQL queries from your 
Cube.dev YAML models using both SQL API and REST API approaches.
"""

import os
import json
import requests
import psycopg2
import pandas as pd
from typing import Dict, List, Optional
import yaml

class CubeQueryGenerator:
    """Generate SQL queries from Cube.dev models"""
    
    def __init__(self, 
                 api_url: str = "http://localhost:4000",
                 sql_host: str = "localhost",
                 sql_port: int = 15432,
                 sql_user: str = "cube",
                 sql_password: str = "password",
                 sql_database: str = "cube"):
        """
        Initialize the query generator
        
        Args:
            api_url: Cube.dev REST API URL
            sql_host: SQL API host
            sql_port: SQL API port
            sql_user: SQL API username
            sql_password: SQL API password
            sql_database: SQL API database name
        """
        self.api_url = api_url
        self.sql_connection_params = {
            'host': sql_host,
            'port': sql_port,
            'user': sql_user,
            'password': sql_password,
            'database': sql_database
        }
    
    def load_cube_models(self, model_dir: str = "model") -> Dict:
        """Load generated cube models from YAML files"""
        models = {
            'cubes': {},
            'views': {}
        }
        
        # Load cubes
        cubes_dir = os.path.join(model_dir, "cubes")
        if os.path.exists(cubes_dir):
            for file in os.listdir(cubes_dir):
                if file.endswith('.yml') or file.endswith('.yaml'):
                    with open(os.path.join(cubes_dir, file), 'r') as f:
                        cube_data = yaml.safe_load(f)
                        if 'cubes' in cube_data:
                            for cube in cube_data['cubes']:
                                models['cubes'][cube['name']] = cube
        
        # Load views
        views_dir = os.path.join(model_dir, "views")
        if os.path.exists(views_dir):
            for file in os.listdir(views_dir):
                if file.endswith('.yml') or file.endswith('.yaml'):
                    with open(os.path.join(views_dir, file), 'r') as f:
                        view_data = yaml.safe_load(f)
                        if 'views' in view_data:
                            for view in view_data['views']:
                                models['views'][view['name']] = view
        
        return models
    
    def generate_sql_examples(self, models: Dict) -> List[Dict]:
        """Generate example SQL queries for the loaded models"""
        examples = []
        
        for cube_name, cube in models['cubes'].items():
            # Basic count query
            examples.append({
                'title': f'Count records in {cube_name}',
                'sql': f'SELECT MEASURE(count) FROM {cube_name};',
                'description': f'Get total count of records in {cube_name} cube'
            })
            
            # Dimension grouping
            if 'dimensions' in cube:
                for dim in cube['dimensions'][:2]:  # First 2 dimensions
                    examples.append({
                        'title': f'Group {cube_name} by {dim["name"]}',
                        'sql': f'SELECT {dim["name"]}, MEASURE(count) FROM {cube_name} GROUP BY 1;',
                        'description': f'Count records grouped by {dim["name"]}'
                    })
            
            # Time-based analysis if time dimensions exist
            time_dims = [d for d in cube.get('dimensions', []) if d.get('type') == 'time']
            if time_dims:
                time_dim = time_dims[0]['name']
                examples.append({
                    'title': f'Monthly trend for {cube_name}',
                    'sql': f"""SELECT 
  DATE_TRUNC('month', {time_dim}) as month,
  MEASURE(count)
FROM {cube_name}
WHERE {time_dim} >= '2024-01-01'
GROUP BY 1
ORDER BY 1;""",
                    'description': f'Monthly trend analysis for {cube_name}'
                })
            
            # Multiple measures if available
            measures = [m for m in cube.get('measures', []) if m['name'] != 'count']
            if measures and len(measures) > 0:
                measure = measures[0]['name']
                examples.append({
                    'title': f'Multiple measures for {cube_name}',
                    'sql': f"""SELECT 
  MEASURE(count) as record_count,
  MEASURE({measure}) as {measure}_total
FROM {cube_name};""",
                    'description': f'Multiple measures from {cube_name}'
                })
        
        return examples
    
    def generate_rest_api_examples(self, models: Dict) -> List[Dict]:
        """Generate REST API query examples"""
        examples = []
        
        for cube_name, cube in models['cubes'].items():
            # Basic query
            query = {
                "measures": [f"{cube_name}.count"],
                "dimensions": [],
                "filters": []
            }
            
            examples.append({
                'title': f'REST API: Count {cube_name}',
                'query': query,
                'curl': self._generate_curl_command(query),
                'description': f'REST API query to count records in {cube_name}'
            })
            
            # With dimensions
            if 'dimensions' in cube and len(cube['dimensions']) > 0:
                dim = cube['dimensions'][0]['name']
                query_with_dim = {
                    "measures": [f"{cube_name}.count"],
                    "dimensions": [f"{cube_name}.{dim}"],
                    "filters": []
                }
                
                examples.append({
                    'title': f'REST API: {cube_name} grouped by {dim}',
                    'query': query_with_dim,
                    'curl': self._generate_curl_command(query_with_dim),
                    'description': f'Group {cube_name} by {dim} using REST API'
                })
            
            # With time dimension
            time_dims = [d for d in cube.get('dimensions', []) if d.get('type') == 'time']
            if time_dims:
                time_dim = time_dims[0]['name']
                query_with_time = {
                    "measures": [f"{cube_name}.count"],
                    "dimensions": [],
                    "timeDimensions": [{
                        "dimension": f"{cube_name}.{time_dim}",
                        "dateRange": ["2024-01-01", "2024-12-31"],
                        "granularity": "month"
                    }]
                }
                
                examples.append({
                    'title': f'REST API: {cube_name} time analysis',
                    'query': query_with_time,
                    'curl': self._generate_curl_command(query_with_time),
                    'description': f'Time-based analysis of {cube_name}'
                })
        
        return examples
    
    def _generate_curl_command(self, query: Dict) -> str:
        """Generate curl command for REST API query"""
        query_json = json.dumps(query, indent=2)
        return f"""curl -H "Authorization: YOUR_TOKEN" \\
  -G \\
  --data-urlencode 'query={query_json}' \\
  {self.api_url}/cubejs-api/v1/load"""
    
    def test_sql_connection(self) -> bool:
        """Test connection to SQL API"""
        try:
            conn = psycopg2.connect(**self.sql_connection_params)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            print(f"SQL API connection failed: {e}")
            return False
    
    def execute_sql_query(self, sql: str) -> Optional[pd.DataFrame]:
        """Execute SQL query against Cube.dev SQL API"""
        try:
            conn = psycopg2.connect(**self.sql_connection_params)
            df = pd.read_sql(sql, conn)
            conn.close()
            return df
        except Exception as e:
            print(f"SQL query failed: {e}")
            return None
    
    def execute_rest_query(self, query: Dict, token: str = None) -> Optional[Dict]:
        """Execute REST API query"""
        try:
            headers = {}
            if token:
                headers['Authorization'] = token
            
            params = {'query': json.dumps(query)}
            response = requests.get(
                f"{self.api_url}/cubejs-api/v1/load",
                params=params,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"REST API query failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"REST API query failed: {e}")
            return None

def main():
    """Main function to demonstrate query generation"""
    print("🔍 Cube.dev SQL Query Examples Generator")
    print("=" * 50)
    
    # Initialize query generator
    generator = CubeQueryGenerator()
    
    # Load generated models
    print("\n📁 Loading generated Cube.dev models...")
    models = generator.load_cube_models()
    
    if not models['cubes']:
        print("❌ No cube models found. Please run the generator first.")
        return
    
    print(f"✅ Loaded {len(models['cubes'])} cubes and {len(models['views'])} views")
    
    # Generate SQL examples
    print("\n🔧 Generating SQL query examples...")
    sql_examples = generator.generate_sql_examples(models)
    
    # Generate REST API examples
    print("🔧 Generating REST API query examples...")
    rest_examples = generator.generate_rest_api_examples(models)
    
    # Display SQL examples
    print("\n" + "=" * 60)
    print("📋 SQL API QUERY EXAMPLES")
    print("=" * 60)
    
    for i, example in enumerate(sql_examples[:10], 1):  # Show first 10
        print(f"\n{i}. {example['title']}")
        print("-" * 40)
        print(f"Description: {example['description']}")
        print(f"SQL Query:")
        print(example['sql'])
    
    # Display REST API examples
    print("\n" + "=" * 60)
    print("🌐 REST API QUERY EXAMPLES")
    print("=" * 60)
    
    for i, example in enumerate(rest_examples[:5], 1):  # Show first 5
        print(f"\n{i}. {example['title']}")
        print("-" * 40)
        print(f"Description: {example['description']}")
        print(f"Query JSON:")
        print(json.dumps(example['query'], indent=2))
        print(f"\nCurl Command:")
        print(example['curl'])
    
    # Test connection
    print("\n" + "=" * 60)
    print("🔌 CONNECTION TEST")
    print("=" * 60)
    
    print("\nTesting SQL API connection...")
    if generator.test_sql_connection():
        print("✅ SQL API connection successful!")
        
        # Try executing a simple query
        if models['cubes']:
            cube_name = list(models['cubes'].keys())[0]
            test_sql = f"SELECT MEASURE(count) FROM {cube_name} LIMIT 1;"
            print(f"\nExecuting test query: {test_sql}")
            result = generator.execute_sql_query(test_sql)
            if result is not None:
                print("✅ Query executed successfully!")
                print(result)
            else:
                print("❌ Query execution failed")
    else:
        print("❌ SQL API connection failed")
        print("\nTo enable SQL API, run Cube.dev with:")
        print("export CUBEJS_PG_SQL_PORT=15432")
        print("export CUBEJS_SQL_USER=cube")
        print("export CUBEJS_SQL_PASSWORD=password")
        print("npm run dev")
    
    print("\n" + "=" * 60)
    print("📚 NEXT STEPS")
    print("=" * 60)
    print("""
1. Start Cube.dev with SQL API enabled:
   export CUBEJS_PG_SQL_PORT=15432
   npm run dev

2. Connect using PostgreSQL tools:
   psql -h localhost -p 15432 -U cube cube

3. Try the generated SQL queries above

4. Use REST API with your application:
   - Copy the curl commands above
   - Replace YOUR_TOKEN with actual API token
   - Integrate with your frontend/BI tools

5. Connect BI tools:
   - Tableau: PostgreSQL driver → localhost:15432
   - Power BI: PostgreSQL connector
   - Grafana: PostgreSQL datasource
   - Metabase: PostgreSQL database
""")

if __name__ == "__main__":
    main()
