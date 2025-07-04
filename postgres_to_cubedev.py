#!/usr/bin/env python3
"""
PostgreSQL Database Schema to Cube.dev YAML Data Model Generator

This script connects to a PostgreSQL database, introspects the schema,
and generates Cube.dev-compatible YAML files organized by data model type.
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml
from sqlalchemy import create_engine, MetaData, Table, Column, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    schema: str = 'public'

@dataclass
class TableInfo:
    """Information about a database table"""
    name: str
    schema: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    is_fact_table: bool = False
    is_dimension_table: bool = False
    table_type: str = 'unknown'

class PostgreSQLIntrospector:
    """Handles PostgreSQL database introspection"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self.metadata: Optional[MetaData] = None
        self.inspector = None
        
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            connection_string = (
                f"postgresql://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            self.engine = create_engine(connection_string)
            self.inspector = inspect(self.engine)
            self.metadata = MetaData()
            
            # Test connection
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
                
            logger.info(f"Successfully connected to database: {self.config.database}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def get_tables(self, schema: str = None) -> List[str]:
        """Get list of tables in the specified schema"""
        schema = schema or self.config.schema
        return self.inspector.get_table_names(schema=schema)
    
    def introspect_table(self, table_name: str, schema: str = None) -> TableInfo:
        """Introspect a single table and return detailed information"""
        schema = schema or self.config.schema
        
        # Get columns
        columns = []
        for col in self.inspector.get_columns(table_name, schema=schema):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default'),
                'autoincrement': col.get('autoincrement', False)
            })
        
        # Get primary keys
        pk_constraint = self.inspector.get_pk_constraint(table_name, schema=schema)
        primary_keys = pk_constraint.get('constrained_columns', [])
        
        # Get foreign keys
        foreign_keys = []
        for fk in self.inspector.get_foreign_keys(table_name, schema=schema):
            foreign_keys.append({
                'constrained_columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns'],
                'referred_schema': fk.get('referred_schema', schema)
            })
        
        # Get indexes
        indexes = []
        for idx in self.inspector.get_indexes(table_name, schema=schema):
            indexes.append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx['unique']
            })
        
        table_info = TableInfo(
            name=table_name,
            schema=schema,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            indexes=indexes
        )
        
        # Determine table type
        self._classify_table(table_info)
        
        return table_info
    
    def _classify_table(self, table_info: TableInfo) -> None:
        """Classify table as fact, dimension, or junction based on characteristics"""
        
        # Check for fact table indicators
        fact_indicators = [
            'amount', 'quantity', 'price', 'cost', 'value', 'total',
            'count', 'revenue', 'profit', 'sales', 'transactions'
        ]
        
        # Check for dimension table indicators
        dimension_indicators = [
            'name', 'title', 'description', 'category', 'type',
            'status', 'code', 'label', 'classification'
        ]
        
        # Check for junction table indicators
        junction_indicators = len(table_info.foreign_keys) >= 2
        
        # Count columns with different characteristics
        fact_score = 0
        dimension_score = 0
        
        for col in table_info.columns:
            col_name = col['name'].lower()
            col_type = col['type'].lower()
            
            # Fact table scoring
            if any(indicator in col_name for indicator in fact_indicators):
                fact_score += 2
            if 'numeric' in col_type or 'decimal' in col_type or 'float' in col_type:
                fact_score += 1
            if col_name.endswith('_id') and col['name'] not in table_info.primary_keys:
                fact_score += 1
                
            # Dimension table scoring
            if any(indicator in col_name for indicator in dimension_indicators):
                dimension_score += 2
            if 'varchar' in col_type or 'text' in col_type or 'char' in col_type:
                dimension_score += 1
        
        # Classify table
        if junction_indicators and len(table_info.columns) <= 6:
            table_info.table_type = 'junction'
        elif fact_score > dimension_score and len(table_info.foreign_keys) > 0:
            table_info.table_type = 'fact'
            table_info.is_fact_table = True
        elif dimension_score >= fact_score or len(table_info.foreign_keys) <= 1:
            table_info.table_type = 'dimension'
            table_info.is_dimension_table = True
        else:
            table_info.table_type = 'generic'
    
    def get_sample_data(self, table_name: str, schema: str = None, limit: int = 5) -> List[Dict]:
        """Get sample data from table for analysis"""
        schema = schema or self.config.schema
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text(f"SELECT * FROM {schema}.{table_name} LIMIT {limit}"))
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.warning(f"Could not fetch sample data from {table_name}: {e}")
            return []

class CubeYAMLGenerator:
    """Generates Cube.dev YAML files from database schema"""
    
    def __init__(self, output_dir: str = "model"):
        self.output_dir = Path(output_dir)
        self.cubes_dir = self.output_dir / "cubes"
        self.views_dir = self.output_dir / "views"
        
        # Create directories
        self.cubes_dir.mkdir(parents=True, exist_ok=True)
        self.views_dir.mkdir(parents=True, exist_ok=True)
        
        # Column type mappings
        self.type_mappings = {
            'integer': 'number',
            'bigint': 'number',
            'smallint': 'number',
            'decimal': 'number',
            'numeric': 'number',
            'real': 'number',
            'double precision': 'number',
            'float': 'number',
            'varchar': 'string',
            'character varying': 'string',
            'text': 'string',
            'char': 'string',
            'character': 'string',
            'timestamp': 'time',
            'timestamp without time zone': 'time',
            'timestamp with time zone': 'time',
            'date': 'time',
            'time': 'time',
            'boolean': 'boolean',
            'uuid': 'string',
            'json': 'string',
            'jsonb': 'string'
        }
        
        self.common_measures = {
            'amount': ['sum', 'avg', 'min', 'max'],
            'price': ['sum', 'avg', 'min', 'max'],
            'cost': ['sum', 'avg', 'min', 'max'],
            'value': ['sum', 'avg', 'min', 'max'],
            'total': ['sum', 'avg', 'min', 'max'],
            'quantity': ['sum', 'avg', 'min', 'max'],
            'count': ['sum', 'avg'],
            'score': ['avg', 'min', 'max'],
            'rating': ['avg', 'min', 'max']
        }
    
    def map_sql_type_to_cube(self, sql_type: str) -> str:
        """Map SQL type to Cube.dev type"""
        sql_type_lower = sql_type.lower()
        
        # Handle parameterized types
        base_type = sql_type_lower.split('(')[0]
        
        return self.type_mappings.get(base_type, 'string')
    
    def generate_cube_from_table(self, table_info: TableInfo) -> Dict[str, Any]:
        """Generate a cube definition from table information"""
        
        cube_name = table_info.name
        
        # Base cube structure
        cube = {
            'name': cube_name,
            'sql_table': f"{table_info.schema}.{table_info.name}",
            'description': f"Generated cube for {table_info.name} table"
        }
        
        # Generate measures
        measures = self._generate_measures(table_info)
        if measures:
            cube['measures'] = measures
        
        # Generate dimensions
        dimensions = self._generate_dimensions(table_info)
        if dimensions:
            cube['dimensions'] = dimensions
        
        # Generate joins
        joins = self._generate_joins(table_info)
        if joins:
            cube['joins'] = joins
        
        # Generate segments for common patterns
        segments = self._generate_segments(table_info)
        if segments:
            cube['segments'] = segments
        
        # Generate pre-aggregations for fact tables
        if table_info.is_fact_table:
            pre_aggs = self._generate_pre_aggregations(table_info)
            if pre_aggs:
                cube['pre_aggregations'] = pre_aggs
        
        return cube
    
    def _generate_measures(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate measures for the cube"""
        measures = []
        
        # Always add count measure
        measures.append({
            'name': 'count',
            'type': 'count',
            'description': f"Total number of {table_info.name} records"
        })
        
        # Add count distinct for primary key
        if table_info.primary_keys:
            pk_col = table_info.primary_keys[0]
            measures.append({
                'name': 'count_distinct',
                'sql': pk_col,
                'type': 'count_distinct',
                'description': f"Count of unique {table_info.name} records"
            })
        
        # Generate measures for numeric columns
        for col in table_info.columns:
            cube_type = self.map_sql_type_to_cube(col['type'])
            col_name = col['name'].lower()
            
            if cube_type == 'number' and col['name'] not in table_info.primary_keys:
                
                # Determine appropriate measure types
                measure_types = ['sum', 'avg', 'min', 'max']
                
                # Check for common measure patterns
                for pattern, types in self.common_measures.items():
                    if pattern in col_name:
                        measure_types = types
                        break
                
                # Generate measures
                for measure_type in measure_types:
                    measure_name = f"{measure_type}_{col['name']}"
                    measure = {
                        'name': measure_name,
                        'sql': col['name'],
                        'type': measure_type,
                        'description': f"{measure_type.title()} of {col['name']}"
                    }
                    
                    # Add format for financial columns
                    if any(term in col_name for term in ['amount', 'price', 'cost', 'value', 'total']):
                        measure['format'] = 'currency'
                    
                    measures.append(measure)
        
        return measures
    
    def _generate_dimensions(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate dimensions for the cube"""
        dimensions = []
        
        for col in table_info.columns:
            cube_type = self.map_sql_type_to_cube(col['type'])
            
            dimension = {
                'name': col['name'],
                'sql': col['name'],
                'type': cube_type,
                'description': f"{col['name']} dimension"
            }
            
            # Mark primary key
            if col['name'] in table_info.primary_keys:
                dimension['primary_key'] = True
            
            # Add granularities for time dimensions
            if cube_type == 'time':
                dimension['granularities'] = [
                    {'name': 'day', 'interval': '1 day'},
                    {'name': 'week', 'interval': '1 week'},
                    {'name': 'month', 'interval': '1 month'},
                    {'name': 'quarter', 'interval': '1 quarter'},
                    {'name': 'year', 'interval': '1 year'}
                ]
            
            dimensions.append(dimension)
        
        return dimensions
    
    def _generate_joins(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate join definitions for foreign keys"""
        joins = []
        
        for fk in table_info.foreign_keys:
            if fk['constrained_columns'] and fk['referred_table']:
                join = {
                    'name': fk['referred_table'],
                    'relationship': 'many_to_one',
                    'sql': f"{{CUBE}}.{fk['constrained_columns'][0]} = {{{fk['referred_table']}.{fk['referred_columns'][0]}}}"
                }
                joins.append(join)
        
        return joins
    
    def _generate_segments(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate common segments"""
        segments = []
        
        # Check for common segment patterns
        for col in table_info.columns:
            col_name = col['name'].lower()
            
            # Active/status segments
            if col_name in ['status', 'state', 'is_active', 'active']:
                segments.append({
                    'name': 'active',
                    'sql': f"{{CUBE}}.{col['name']} = 'active'",
                    'description': "Active records only"
                })
            
            # Date-based segments
            if 'created_at' in col_name or 'timestamp' in col_name:
                segments.append({
                    'name': 'recent',
                    'sql': f"{{CUBE}}.{col['name']} >= CURRENT_DATE - INTERVAL '30 days'",
                    'description': "Records from last 30 days"
                })
        
        return segments
    
    def _generate_pre_aggregations(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate pre-aggregations for fact tables"""
        pre_aggs = []
        
        # Find time dimension
        time_dimension = None
        for col in table_info.columns:
            if self.map_sql_type_to_cube(col['type']) == 'time':
                time_dimension = col['name']
                break
        
        if time_dimension:
            pre_agg = {
                'name': 'main',
                'measures': ['count'],
                'time_dimension': time_dimension,
                'granularity': 'day',
                'partition_granularity': 'month',
                'refresh_key': {
                    'every': '1 hour'
                }
            }
            
            # Add dimensions with low cardinality
            dimensions = []
            for col in table_info.columns:
                col_name = col['name'].lower()
                if any(term in col_name for term in ['status', 'type', 'category', 'state']):
                    dimensions.append(col['name'])
            
            if dimensions:
                pre_agg['dimensions'] = dimensions[:3]  # Limit to 3 dimensions
            
            pre_aggs.append(pre_agg)
        
        return pre_aggs
    
    def generate_view_from_cubes(self, cube_names: List[str], view_name: str = "business_metrics") -> Dict[str, Any]:
        """Generate a view that combines multiple cubes"""
        
        view = {
            'name': view_name,
            'description': f"Business metrics view combining {', '.join(cube_names)}",
            'cubes': []
        }
        
        for cube_name in cube_names:
            cube_def = {
                'join_path': cube_name,
                'includes': [
                    'count',
                    'count_distinct'
                ]
            }
            view['cubes'].append(cube_def)
        
        return view
    
    def save_cube_yaml(self, cube: Dict[str, Any], filename: str = None) -> str:
        """Save cube definition to YAML file"""
        if not filename:
            filename = f"{cube['name']}.yml"
        
        filepath = self.cubes_dir / filename
        
        # Wrap in cubes array for proper YAML structure
        yaml_content = {'cubes': [cube]}
        
        with open(filepath, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False, indent=2)
        
        logger.info(f"Generated cube YAML: {filepath}")
        return str(filepath)
    
    def save_view_yaml(self, view: Dict[str, Any], filename: str = None) -> str:
        """Save view definition to YAML file"""
        if not filename:
            filename = f"{view['name']}.yml"
        
        filepath = self.views_dir / filename
        
        # Wrap in views array for proper YAML structure
        yaml_content = {'views': [view]}
        
        with open(filepath, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False, indent=2)
        
        logger.info(f"Generated view YAML: {filepath}")
        return str(filepath)

def main():
    """Main function to orchestrate the generation process"""
    parser = argparse.ArgumentParser(description="Generate Cube.dev YAML from PostgreSQL schema")
    parser.add_argument("--host", required=True, help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--database", required=True, help="Database name")
    parser.add_argument("--username", required=True, help="Database username")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--schema", default="public", help="Database schema")
    parser.add_argument("--output-dir", default="model", help="Output directory for YAML files")
    parser.add_argument("--tables", nargs="*", help="Specific tables to process (default: all)")
    parser.add_argument("--generate-views", action="store_true", help="Generate view definitions")
    
    args = parser.parse_args()
    
    # Create database config
    db_config = DatabaseConfig(
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        schema=args.schema
    )
    
    # Initialize introspector
    introspector = PostgreSQLIntrospector(db_config)
    
    if not introspector.connect():
        logger.error("Failed to connect to database")
        sys.exit(1)
    
    # Initialize YAML generator
    generator = CubeYAMLGenerator(args.output_dir)
    
    # Get tables to process
    if args.tables:
        tables = args.tables
    else:
        tables = introspector.get_tables(args.schema)
    
    logger.info(f"Processing {len(tables)} tables...")
    
    cube_names = []
    
    # Process each table
    for table_name in tables:
        try:
            logger.info(f"Processing table: {table_name}")
            
            # Introspect table
            table_info = introspector.introspect_table(table_name, args.schema)
            
            # Generate cube
            cube = generator.generate_cube_from_table(table_info)
            
            # Save cube YAML
            generator.save_cube_yaml(cube)
            cube_names.append(cube['name'])
            
            logger.info(f"Generated cube for {table_name} (type: {table_info.table_type})")
            
        except Exception as e:
            logger.error(f"Error processing table {table_name}: {e}")
            continue
    
    # Generate views if requested
    if args.generate_views and cube_names:
        try:
            # Generate main business metrics view
            view = generator.generate_view_from_cubes(cube_names, "business_metrics")
            generator.save_view_yaml(view)
            
            # Generate domain-specific views
            fact_cubes = [name for name in cube_names if 'fact' in name.lower() or 
                         any(term in name.lower() for term in ['sales', 'orders', 'transactions'])]
            
            if fact_cubes:
                fact_view = generator.generate_view_from_cubes(fact_cubes, "fact_analysis")
                generator.save_view_yaml(fact_view)
            
        except Exception as e:
            logger.error(f"Error generating views: {e}")
    
    logger.info(f"Generation complete! Generated {len(cube_names)} cubes in {args.output_dir}")
    logger.info(f"Cubes directory: {generator.cubes_dir}")
    logger.info(f"Views directory: {generator.views_dir}")

if __name__ == "__main__":
    main()
