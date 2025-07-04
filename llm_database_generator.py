#!/usr/bin/env python3
"""
LLM-Enhanced Universal Database to Cube.dev Generator

This enhanced version uses OpenAI/LLM to generate meaningful descriptions
for cubes, measures, and dimensions based on actual database content.

Supports multiple database engines:
- PostgreSQL, SQLite, MySQL, Microsoft SQL Server
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import our modules
from enhanced_database_to_cubedev import EnhancedCubeGenerator, DatabaseConfig
from database_to_cubedev import DatabaseIntrospector, DatabaseConfig, TableInfo
from llm_descriptions import EnhancedDescriptionService, TableContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMEnhancedCubeGenerator(EnhancedCubeGenerator):
    """Enhanced generator with LLM-powered descriptions"""
    
    def __init__(self, output_dir: str = "model", config_profile: str = "default", 
                 enable_llm: bool = True, llm_model: str = "gpt-3.5-turbo"):
        super().__init__(output_dir, config_profile)
        
        # Initialize LLM description service
        api_key = os.getenv("OPENAI_API_KEY")
        self.description_service = EnhancedDescriptionService(
            enable_llm=enable_llm,
            api_key=api_key,
            model=llm_model
        )
        
        logger.info(f"LLM Enhanced Generator initialized (LLM: {'enabled' if enable_llm else 'disabled'})")
    
    def generate_enhanced_cube_with_llm(self, table_info: TableInfo, sample_data: List[Dict] = None) -> Dict[str, Any]:
        """Generate cube with LLM-enhanced descriptions"""
        
        # Classify table
        table_type = self.classify_table_enhanced(table_info, sample_data)
        
        # Create table context for LLM
        table_context = TableContext(
            table_name=table_info.name,
            table_type=table_type,
            schema=table_info.schema,
            columns=table_info.columns,
            sample_data=sample_data or [],
            foreign_keys=table_info.foreign_keys,
            domain=self.config_profile
        )
        
        # Base cube structure with LLM description
        cube = {
            'name': self.utils.sanitize_name(table_info.name),
            'sql_table': f"{table_info.schema}.{table_info.name}",
            'description': self.description_service.describe_cube(table_context)
        }
        
        # Generate components with LLM descriptions
        measures = self.generate_enhanced_measures_with_llm(table_info, table_type, table_context)
        dimensions = self.generate_enhanced_dimensions_with_llm(table_info, table_context)
        segments = self.generate_enhanced_segments(table_info)  # Keep existing logic
        
        if measures:
            cube['measures'] = measures
        if dimensions:
            cube['dimensions'] = dimensions
        if segments:
            cube['segments'] = segments
        
        # Generate joins and pre-aggregations (existing logic)
        joins = self._generate_joins(table_info)
        if joins:
            cube['joins'] = joins
        
        if table_type == 'fact':
            pre_aggs = self.generate_enhanced_pre_aggregations(table_info, table_type)
            if pre_aggs:
                cube['pre_aggregations'] = pre_aggs
        
        # Add metadata
        cube['_metadata'] = {
            'table_type': table_type,
            'source_table': f"{table_info.schema}.{table_info.name}",
            'column_count': len(table_info.columns),
            'foreign_key_count': len(table_info.foreign_keys),
            'llm_enhanced': True
        }
        
        return cube
    
    def generate_enhanced_measures_with_llm(self, table_info: TableInfo, table_type: str, table_context: TableContext) -> List[Dict[str, Any]]:
        """Generate measures with LLM descriptions"""
        measures = []
        
        # Default measures with LLM descriptions
        measures.append({
            'name': 'count',
            'type': 'count',
            'description': self.description_service.describe_measure(
                'count', 'count', 'all_records', table_context
            )
        })
        
        if table_info.primary_keys:
            pk_col = table_info.primary_keys[0]
            measures.append({
                'name': 'count_distinct',
                'sql': pk_col,
                'type': 'count_distinct',
                'description': self.description_service.describe_measure(
                    'count_distinct', 'count_distinct', pk_col, table_context
                )
            })
        
        # Generate numeric measures with LLM descriptions
        for col in table_info.columns:
            col_type = self._map_sql_type_to_cube(col['type'])
            col_name = col['name'].lower()
            
            if col_type == 'number' and col['name'] not in table_info.primary_keys:
                # Determine appropriate measure types
                measure_types = self._get_measure_types_for_column(col_name)
                
                for measure_type in measure_types:
                    measure_name = f"{measure_type}_{col['name']}"
                    measure = {
                        'name': measure_name,
                        'sql': col['name'],
                        'type': measure_type,
                        'description': self.description_service.describe_measure(
                            measure_name, measure_type, col['name'], table_context
                        )
                    }
                    
                    # Add format for financial columns
                    if any(term in col_name for term in ['amount', 'price', 'cost', 'value', 'total']):
                        measure['format'] = 'currency'
                    
                    measures.append(measure)
        
        return measures
    
    def generate_enhanced_dimensions_with_llm(self, table_info: TableInfo, table_context: TableContext) -> List[Dict[str, Any]]:
        """Generate dimensions with LLM descriptions"""
        dimensions = []
        
        for col in table_info.columns:
            cube_type = self._map_sql_type_to_cube(col['type'])
            
            dimension = {
                'name': col['name'],
                'sql': col['name'],
                'type': cube_type,
                'description': self.description_service.describe_dimension(
                    col['name'], col['type'], table_context
                )
            }
            
            # Mark primary key
            if col['name'] in table_info.primary_keys:
                dimension['primary_key'] = True
            
            # Add time dimension granularities
            if cube_type == 'time':
                from cubedev_config import DIMENSION_GENERATION_RULES
                time_config = DIMENSION_GENERATION_RULES['time_dimensions']
                dimension['granularities'] = time_config['granularities'].copy()
                
                # Add custom granularities for specific columns
                col_name = col['name'].lower()
                if any(pattern in col_name for pattern in ['created_at', 'updated_at']):
                    dimension['granularities'].extend(time_config['custom_granularities'])
            
            dimensions.append(dimension)
        
        return dimensions
    
    def _get_measure_types_for_column(self, col_name: str) -> List[str]:
        """Get appropriate measure types for a column"""
        from cubedev_config import MEASURE_GENERATION_RULES
        
        # Check for common measure patterns
        for rule_name, rule_config in MEASURE_GENERATION_RULES['numeric_measures'].items():
            if any(pattern in col_name for pattern in rule_config['patterns']):
                return rule_config['measures']
        
        # Default measures for numeric columns
        return ['sum', 'avg', 'min', 'max']
    
    def process_database_with_llm(self, introspector: DatabaseIntrospector, tables: List[str] = None) -> Dict[str, Any]:
        """Process database with LLM enhancements"""
        
        logger.info("Starting LLM-enhanced database processing...")
        
        # Get tables to process
        if not tables:
            tables = introspector.get_tables()
        
        logger.info(f"Processing {len(tables)} tables with LLM descriptions...")
        
        cubes = []
        errors = []
        
        # Process each table
        for table_name in tables:
            try:
                logger.info(f"Processing table: {table_name}")
                
                # Introspect table
                table_info = introspector.introspect_table(table_name)
                
                # Get sample data for LLM context
                sample_data = introspector.get_sample_data(table_name, limit=3)
                
                # Generate cube with LLM descriptions
                cube = self.generate_enhanced_cube_with_llm(table_info, sample_data)
                
                # Validate cube
                from cubedev_utils import validate_cube_definition
                is_valid, validation_errors = validate_cube_definition(cube)
                if not is_valid:
                    logger.warning(f"Validation errors for {table_name}: {validation_errors}")
                    errors.extend(validation_errors)
                
                # Save cube
                filepath = self.file_manager.save_cube_file(cube)
                self.generated_files.append(filepath)
                cubes.append(cube)
                
                # Update stats
                table_type = cube.get('_metadata', {}).get('table_type', 'unknown')
                self.generation_stats['cubes'] += 1
                self.generation_stats[f'{table_type}_tables'] = self.generation_stats.get(f'{table_type}_tables', 0) + 1
                
                logger.info(f"Generated LLM-enhanced cube for {table_name} (type: {table_type})")
                
            except Exception as e:
                logger.error(f"Error processing table {table_name}: {e}")
                errors.append(f"Table {table_name}: {str(e)}")
                self.generation_stats['errors'] += 1
                continue
        
        # Generate views
        logger.info("Generating views...")
        views = self.generate_domain_specific_views(cubes)
        
        for view in views:
            try:
                # Save view
                filepath = self.file_manager.save_view_file(view)
                self.generated_files.append(filepath)
                self.generation_stats['views'] += 1
                
                logger.info(f"Generated view: {view['name']}")
                
            except Exception as e:
                logger.error(f"Error generating view {view.get('name', 'unknown')}: {e}")
                errors.append(f"View {view.get('name', 'unknown')}: {str(e)}")
                self.generation_stats['errors'] += 1
        
        # Create index file
        index_file = self.file_manager.create_index_file(self.generated_files)
        
        # Generate summary
        summary = {
            'total_files': len(self.generated_files),
            'stats': self.generation_stats,
            'errors': errors,
            'output_directory': self.output_dir,
            'generated_files': self.generated_files,
            'index_file': index_file,
            'llm_enhanced': True
        }
        
        logger.info(f"LLM-enhanced generation complete! Summary: {self.generation_stats}")
        
        return summary

def generate_llm_enhanced_cubes_from_engine(
    engine,  # SQLAlchemy Engine instance
    output_dir: str = "model", 
    schema: str = "public", 
    tables: Optional[List[str]] = None,
    generate_views: bool = False,
    openai_api_key: Optional[str] = None,
    model_name: str = "gpt-3.5-turbo"
):
    """
    Generate LLM-enhanced Cube.dev YAML files from a user-provided SQLAlchemy engine.
    
    This is the recommended approach for database-agnostic usage with LLM enhancements.
    
    Args:
        engine: Pre-configured SQLAlchemy Engine instance
        output_dir: Directory to save generated YAML files
        schema: Database schema name (ignored for SQLite)
        tables: Specific tables to process (None = all tables)
        generate_views: Whether to generate view definitions
        openai_api_key: OpenAI API key (or None to use environment variable)
        model_name: LLM model to use for descriptions
        
    Returns:
        Dictionary with generation statistics
        
    Example:
        from sqlalchemy import create_engine
        
        # User provides their own engine
        engine = create_engine("postgresql://user:pass@localhost/db")
        
        # Generate LLM-enhanced cubes
        stats = generate_llm_enhanced_cubes_from_engine(
            engine=engine,
            output_dir="my_llm_cubes",
            generate_views=True,
            openai_api_key="your-api-key"
        )
    """
    # Create config with user-provided engine
    db_config = DatabaseConfig(
        engine_instance=engine,
        schema=schema
    )
    
    # Initialize introspector
    introspector = DatabaseIntrospector(db_config)
    
    if not introspector.connect():
        raise RuntimeError("Failed to connect to database using provided engine")
    
    # Set OpenAI API key in environment if provided
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Initialize LLM-enhanced generator
    generator = LLMEnhancedCubeGenerator(
        output_dir=output_dir,
        enable_llm=openai_api_key is not None,
        llm_model=model_name
    )
    
    # Get tables to process
    if tables is None:
        tables = introspector.get_tables(schema)
    
    logger.info(f"Processing {len(tables)} tables with LLM enhancements...")
    
    stats = {
        'cubes_generated': 0,
        'views_generated': 0,
        'fact_tables': 0,
        'dimension_tables': 0,
        'llm_descriptions': 0,
        'errors': []
    }
    
    cube_names = []
    generated_cubes = []
    
    # Process each table
    for table_name in tables:
        try:
            logger.info(f"Processing table: {table_name}")
            
            # Introspect table
            table_info = introspector.introspect_table(table_name, schema)
            
            # Update stats based on table type
            if table_info.table_type == 'fact':
                stats['fact_tables'] += 1
            elif table_info.table_type == 'dimension':
                stats['dimension_tables'] += 1
            
            # Get sample data for LLM context
            sample_data = introspector.get_sample_data(table_name, schema, limit=3)
            
            # Generate LLM-enhanced cube
            cube = generator.generate_enhanced_cube_with_llm(table_info, sample_data)
            
            # Save cube YAML
            filepath = generator.file_manager.save_cube_file(cube)
            cube_names.append(cube['name'])
            generated_cubes.append(cube)
            stats['cubes_generated'] += 1
            stats['llm_descriptions'] += 1  # Each cube gets LLM-enhanced descriptions
            
            logger.info(f"Generated LLM-enhanced cube for {table_name} (type: {table_info.table_type})")
            
        except Exception as e:
            error_msg = f"Error processing table {table_name}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            continue
    
    # Generate views if requested
    if generate_views and cube_names:
        try:
            # Generate domain-specific views using the existing method
            views = generator.generate_domain_specific_views(generated_cubes)
            for view in views:
                generator.file_manager.save_view_file(view)
                stats['views_generated'] += 1
            
        except Exception as e:
            error_msg = f"Error generating views: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
    
    logger.info(f"LLM-enhanced generation complete! Generated {stats['cubes_generated']} cubes and {stats['views_generated']} views in {output_dir}")
    logger.info(f"LLM descriptions generated: {stats['llm_descriptions']}")
    return stats

