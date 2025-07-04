#!/usr/bin/env python3
"""
Enhanced Universal Database Schema to Cube.dev YAML Data Model Generator

This enhanced version uses configuration-driven generation with better
table classification, relationship detection, and domain-specific templates.

Supports multiple database engines through SQLAlchemy:
- PostgreSQL, SQLite, MySQL, Microsoft SQL Server
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

# Import our custom modules
from cubedev_config import (
    DATABASE_CONFIGS, TABLE_CLASSIFICATION, COLUMN_TYPE_MAPPINGS,
    MEASURE_GENERATION_RULES, DIMENSION_GENERATION_RULES, 
    SEGMENT_GENERATION_RULES, PRE_AGGREGATION_CONFIG,
    VIEW_GENERATION_CONFIG, DOMAIN_TEMPLATES
)
from cubedev_utils import (
    CubeDevUtils, YAMLFormatter, DatabaseAnalyzer, 
    FileManager, validate_cube_definition, validate_view_definition
)
from database_to_cubedev import DatabaseIntrospector, DatabaseConfig, TableInfo

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedCubeGenerator:
    """Enhanced Cube.dev YAML generator with configuration-driven features"""
    
    def __init__(self, output_dir: str = "model", config_profile: str = "default"):
        self.output_dir = output_dir
        self.config_profile = config_profile
        self.file_manager = FileManager(output_dir)
        self.utils = CubeDevUtils()
        self.analyzer = DatabaseAnalyzer()
        
        # Generated files tracking
        self.generated_files = []
        self.generation_stats = {
            'cubes': 0,
            'views': 0,
            'fact_tables': 0,
            'dimension_tables': 0,
            'junction_tables': 0,
            'errors': 0
        }
    
    def classify_table_enhanced(self, table_info: TableInfo, sample_data: List[Dict] = None) -> str:
        """Enhanced table classification using configuration rules"""
        
        table_name = table_info.name.lower()
        
        # Check name patterns first
        fact_patterns = TABLE_CLASSIFICATION['fact_table_indicators']['name_patterns']
        dim_patterns = TABLE_CLASSIFICATION['dimension_table_indicators']['name_patterns']
        junction_patterns = TABLE_CLASSIFICATION['junction_table_indicators']['name_patterns']
        
        # Name-based classification
        if any(pattern in table_name for pattern in fact_patterns):
            return 'fact'
        
        if any(pattern in table_name for pattern in dim_patterns):
            return 'dimension'
            
        if any(pattern in table_name for pattern in junction_patterns):
            return 'junction'
        
        # Column-based classification
        fact_score = 0
        dim_score = 0
        
        fact_col_patterns = TABLE_CLASSIFICATION['fact_table_indicators']['column_patterns']
        dim_col_patterns = TABLE_CLASSIFICATION['dimension_table_indicators']['column_patterns']
        
        numeric_count = 0
        text_count = 0
        total_cols = len(table_info.columns)
        
        for col in table_info.columns:
            col_name = col['name'].lower()
            col_type = col['type'].lower()
            
            # Count column types
            if any(t in col_type for t in ['int', 'decimal', 'numeric', 'float']):
                numeric_count += 1
            if any(t in col_type for t in ['varchar', 'text', 'char']):
                text_count += 1
            
            # Score based on column patterns
            if any(pattern in col_name for pattern in fact_col_patterns):
                fact_score += 2
            if any(pattern in col_name for pattern in dim_col_patterns):
                dim_score += 2
        
        # Calculate ratios
        numeric_ratio = numeric_count / total_cols if total_cols > 0 else 0
        text_ratio = text_count / total_cols if total_cols > 0 else 0
        fk_count = len(table_info.foreign_keys)
        
        # Apply classification rules
        junction_threshold = TABLE_CLASSIFICATION['junction_table_indicators']
        if (fk_count >= junction_threshold['foreign_key_threshold'] and 
            total_cols <= junction_threshold['max_columns']):
            return 'junction'
        
        fact_threshold = TABLE_CLASSIFICATION['fact_table_indicators']
        if (fk_count >= fact_threshold['foreign_key_threshold'] and 
            numeric_ratio >= fact_threshold['numeric_column_threshold']):
            return 'fact'
        
        dim_threshold = TABLE_CLASSIFICATION['dimension_table_indicators']
        if text_ratio >= dim_threshold['text_column_threshold']:
            return 'dimension'
        
        # Default classification based on scores
        if fact_score > dim_score:
            return 'fact'
        else:
            return 'dimension'
    
    def generate_enhanced_measures(self, table_info: TableInfo, table_type: str) -> List[Dict[str, Any]]:
        """Generate measures using configuration rules"""
        measures = []
        
        # Add default measures
        for default_measure in MEASURE_GENERATION_RULES['default_measures']:
            if default_measure['applies_to'] == 'all':
                measures.append({
                    'name': default_measure['name'],
                    'type': default_measure['type'],
                    'description': default_measure['description']
                })
            elif default_measure['applies_to'] == 'primary_key' and table_info.primary_keys:
                measure = {
                    'name': default_measure['name'],
                    'sql': table_info.primary_keys[0],
                    'type': default_measure['type'],
                    'description': default_measure['description']
                }
                measures.append(measure)
        
        # Generate numeric measures
        numeric_rules = MEASURE_GENERATION_RULES['numeric_measures']
        
        for col in table_info.columns:
            col_name = col['name'].lower()
            col_type = self._map_sql_type_to_cube(col['type'])
            
            if col_type == 'number' and col['name'] not in table_info.primary_keys:
                # Find matching rule
                matching_rule = None
                for rule_name, rule_config in numeric_rules.items():
                    if any(pattern in col_name for pattern in rule_config['patterns']):
                        matching_rule = rule_config
                        break
                
                if matching_rule:
                    for measure_type in matching_rule['measures']:
                        measure = {
                            'name': f"{measure_type}_{col['name']}",
                            'sql': col['name'],
                            'type': measure_type,
                            'description': f"{measure_type.title()} of {col['name']}"
                        }
                        
                        if 'format' in matching_rule:
                            measure['format'] = matching_rule['format']
                        
                        measures.append(measure)
        
        return measures
    
    def generate_enhanced_dimensions(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate dimensions using configuration rules"""
        dimensions = []
        
        for col in table_info.columns:
            col_name = col['name'].lower()
            cube_type = self._map_sql_type_to_cube(col['type'])
            
            dimension = {
                'name': col['name'],
                'sql': col['name'],
                'type': cube_type,
                'description': self.utils.generate_description(col['name'], 'dimension')
            }
            
            # Mark primary key
            if col['name'] in table_info.primary_keys:
                dimension['primary_key'] = True
            
            # Add time dimension granularities
            if cube_type == 'time':
                time_config = DIMENSION_GENERATION_RULES['time_dimensions']
                
                # Add standard granularities
                dimension['granularities'] = time_config['granularities'].copy()
                
                # Add custom granularities for specific columns
                if any(pattern in col_name for pattern in ['created_at', 'updated_at']):
                    dimension['granularities'].extend(time_config['custom_granularities'])
            
            dimensions.append(dimension)
        
        return dimensions
    
    def generate_enhanced_segments(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate segments using configuration rules"""
        segments = []
        
        for segment_type, config in SEGMENT_GENERATION_RULES.items():
            for col in table_info.columns:
                col_name = col['name'].lower()
                
                if any(pattern in col_name for pattern in config['patterns']):
                    for segment_template in config['segments']:
                        segment = {
                            'name': segment_template['name'],
                            'sql': f"{{CUBE}}.{col['name']} {segment_template['condition']}",
                            'description': segment_template['description']
                        }
                        
                        # Avoid duplicates
                        if not any(s['name'] == segment['name'] for s in segments):
                            segments.append(segment)
        
        return segments
    
    def generate_enhanced_pre_aggregations(self, table_info: TableInfo, table_type: str) -> List[Dict[str, Any]]:
        """Generate pre-aggregations using configuration rules"""
        pre_aggs = []
        
        if table_type != 'fact':
            return pre_aggs
        
        config = PRE_AGGREGATION_CONFIG['fact_tables']
        
        # Find time dimension
        time_dimension = None
        for col in table_info.columns:
            if self._map_sql_type_to_cube(col['type']) == 'time':
                time_dimension = col['name']
                break
        
        if not time_dimension:
            return pre_aggs
        
        # Find suitable dimensions
        suitable_dimensions = []
        preferred_patterns = config['preferred_dimensions']
        
        for col in table_info.columns:
            col_name = col['name'].lower()
            if any(pattern in col_name for pattern in preferred_patterns):
                suitable_dimensions.append(col['name'])
        
        # Limit dimensions
        suitable_dimensions = suitable_dimensions[:config['max_dimensions']]
        
        # Create pre-aggregation
        pre_agg = {
            'name': 'main_rollup',
            'measures': ['count'],
            'time_dimension': time_dimension,
            'granularity': config['default_granularity'],
            'partition_granularity': config['partition_granularity'],
            'refresh_key': {
                'every': config['refresh_interval']
            }
        }
        
        if suitable_dimensions:
            pre_agg['dimensions'] = suitable_dimensions
        
        # Add build range
        time_range_config = PRE_AGGREGATION_CONFIG['time_ranges']
        pre_agg['build_range_start'] = {
            'sql': time_range_config['build_range_start'].format(
                time_column=time_dimension,
                table=f"{table_info.schema}.{table_info.name}"
            )
        }
        pre_agg['build_range_end'] = {
            'sql': time_range_config['build_range_end'].format(
                time_column=time_dimension,
                table=f"{table_info.schema}.{table_info.name}"
            )
        }
        
        pre_aggs.append(pre_agg)
        return pre_aggs
    
    def generate_enhanced_cube(self, table_info: TableInfo, sample_data: List[Dict] = None) -> Dict[str, Any]:
        """Generate enhanced cube with all features"""
        
        # Classify table
        table_type = self.classify_table_enhanced(table_info, sample_data)
        
        # Base cube structure
        cube = {
            'name': self.utils.sanitize_name(table_info.name),
            'sql_table': f"{table_info.schema}.{table_info.name}",
            'description': self.utils.generate_description(table_info.name, 'cube')
        }
        
        # Generate components
        measures = self.generate_enhanced_measures(table_info, table_type)
        dimensions = self.generate_enhanced_dimensions(table_info)
        segments = self.generate_enhanced_segments(table_info)
        
        if measures:
            cube['measures'] = measures
        if dimensions:
            cube['dimensions'] = dimensions
        if segments:
            cube['segments'] = segments
        
        # Generate joins
        joins = self._generate_joins(table_info)
        if joins:
            cube['joins'] = joins
        
        # Generate pre-aggregations for fact tables
        if table_type == 'fact':
            pre_aggs = self.generate_enhanced_pre_aggregations(table_info, table_type)
            if pre_aggs:
                cube['pre_aggregations'] = pre_aggs
        
        # Add metadata
        cube['_metadata'] = {
            'table_type': table_type,
            'source_table': f"{table_info.schema}.{table_info.name}",
            'column_count': len(table_info.columns),
            'foreign_key_count': len(table_info.foreign_keys)
        }
        
        return cube
    
    def generate_domain_specific_views(self, cubes: List[Dict[str, Any]], domain: str = None) -> List[Dict[str, Any]]:
        """Generate domain-specific views"""
        views = []
        
        # Auto-detect domain if not specified
        if not domain:
            domain = self._detect_domain(cubes)
        
        # Generate business metrics view
        business_view = self._generate_business_metrics_view(cubes)
        if business_view:
            views.append(business_view)
        
        # Generate fact analysis view
        fact_cubes = [cube for cube in cubes if cube.get('_metadata', {}).get('table_type') == 'fact']
        if fact_cubes:
            fact_view = self._generate_fact_analysis_view(fact_cubes)
            views.append(fact_view)
        
        # Generate dimension catalog view
        dim_cubes = [cube for cube in cubes if cube.get('_metadata', {}).get('table_type') == 'dimension']
        if dim_cubes:
            dim_view = self._generate_dimension_catalog_view(dim_cubes)
            views.append(dim_view)
        
        return views
    
    def _map_sql_type_to_cube(self, sql_type: str) -> str:
        """Map SQL type to Cube.dev type using configuration"""
        sql_type_lower = sql_type.lower()
        base_type = sql_type_lower.split('(')[0]
        return COLUMN_TYPE_MAPPINGS.get(base_type, 'string')
    
    def _generate_joins(self, table_info: TableInfo) -> List[Dict[str, Any]]:
        """Generate join definitions"""
        joins = []
        
        for fk in table_info.foreign_keys:
            if fk['constrained_columns'] and fk['referred_table']:
                join = {
                    'name': self.utils.sanitize_name(fk['referred_table']),
                    'relationship': self.utils.determine_join_relationship(
                        table_info.name, 
                        fk['referred_table'], 
                        fk['constrained_columns']
                    ),
                    'sql': f"{{CUBE}}.{fk['constrained_columns'][0]} = {{{self.utils.sanitize_name(fk['referred_table'])}.{fk['referred_columns'][0]}}}"
                }
                joins.append(join)
        
        return joins
    
    def _detect_domain(self, cubes: List[Dict[str, Any]]) -> str:
        """Detect domain based on cube names and patterns"""
        cube_names = [cube['name'].lower() for cube in cubes]
        
        for domain, config in DOMAIN_TEMPLATES.items():
            if domain == 'generic':
                continue
                
            # Check for domain-specific table patterns
            fact_matches = sum(1 for table in config['fact_tables'] 
                             if any(table in name for name in cube_names))
            dim_matches = sum(1 for table in config['dimension_tables'] 
                            if any(table in name for name in cube_names))
            
            total_matches = fact_matches + dim_matches
            if total_matches >= 2:  # At least 2 matches to consider domain
                logger.info(f"Detected domain: {domain}")
                return domain
        
        return 'generic'
    
    def _generate_business_metrics_view(self, cubes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate business metrics view with proper Cube.dev syntax"""
        config = VIEW_GENERATION_CONFIG['business_metrics_view']
        
        # Select key cubes for business metrics
        key_cubes = []
        for cube in cubes:
            cube_name = cube['name']
            # Include cubes that have meaningful measures (not just dimension tables)
            has_financial_measures = any(
                any(term in measure['name'] for term in ['price', 'value', 'amount', 'cost'])
                for measure in cube.get('measures', [])
            )
            has_multiple_measures = len(cube.get('measures', [])) > 2  # More than just count/count_distinct
            
            if has_financial_measures or has_multiple_measures or cube_name in ['orders', 'order_items', 'order_payments']:
                key_cubes.append(cube_name)

        if not key_cubes:
            return None
            
        # Use proper Cube.dev view syntax with cubes array
        view = {
            'name': config['name'],
            'description': config['description'],
            'cubes': []
        }
        
        # Add cubes with proper join_path, includes, and prefix to avoid conflicts
        for cube_name in key_cubes[:3]:  # Limit to 3 cubes to avoid conflicts
            view['cubes'].append({
                'join_path': cube_name,
                'includes': '*',
                'prefix': True
            })
        
        return view
    
    def _generate_fact_analysis_view(self, fact_cubes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate fact analysis view"""
        config = VIEW_GENERATION_CONFIG['fact_analysis_view']
        
        view = {
            'name': config['name'],
            'description': config['description'],
            'cubes': []
        }
        
        for cube in fact_cubes:
            cube_config = {
                'join_path': cube['name'],
                'includes': ['count', 'count_distinct']
            }
            
            # Add all measures from fact tables
            for measure in cube.get('measures', []):
                if measure['name'] not in cube_config['includes']:
                    cube_config['includes'].append(measure['name'])
            
            # Add time dimensions
            for dimension in cube.get('dimensions', []):
                if dimension.get('type') == 'time':
                    cube_config['includes'].append(dimension['name'])
            
            view['cubes'].append(cube_config)
            
            # Add related dimension tables if joins exist
            if config.get('include_joins'):
                for join in cube.get('joins', []):
                    join_config = {
                        'join_path': f"{cube['name']}.{join['name']}",
                        'prefix': join['name'],
                        'includes': ['name', 'description', 'category', 'type']
                    }
                    view['cubes'].append(join_config)
        
        return view
    
    def _generate_dimension_catalog_view(self, dim_cubes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dimension catalog view with proper Cube.dev syntax"""
        config = VIEW_GENERATION_CONFIG['dimension_catalog_view']
        
        # Select dimension cubes
        key_dimension_cubes = []
        for cube in dim_cubes:
            cube_name = cube['name']
            # Include dimension tables that aren't junction tables
            if not any(term in cube_name for term in ['_items', '_payments', '_reviews']):
                key_dimension_cubes.append(cube_name)

        # Use proper Cube.dev view syntax with cubes array
        view = {
            'name': config['name'],
            'description': config['description'],
            'cubes': []
        }
        
        # Add cubes with proper join_path, includes, and prefix to avoid conflicts
        for cube_name in key_dimension_cubes[:3]:  # Limit to 3 cubes to avoid conflicts
            view['cubes'].append({
                'join_path': cube_name,
                'includes': '*',
                'prefix': True
            })
        
        return view
    
    def process_database(self, introspector: DatabaseIntrospector, tables: List[str] = None) -> Dict[str, Any]:
        """Process entire database and generate all YAML files"""
        
        logger.info("Starting enhanced database processing...")
        
        # Get tables to process
        if not tables:
            tables = introspector.get_tables()
        
        logger.info(f"Processing {len(tables)} tables...")
        
        cubes = []
        errors = []
        
        # Process each table
        for table_name in tables:
            try:
                logger.info(f"Processing table: {table_name}")
                
                # Introspect table
                table_info = introspector.introspect_table(table_name)
                
                # Get sample data for analysis
                sample_data = introspector.get_sample_data(table_name)
                
                # Generate cube
                cube = self.generate_enhanced_cube(table_info, sample_data)
                
                # Validate cube
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
                
                logger.info(f"Generated cube for {table_name} (type: {table_type})")
                
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
                # Validate view
                is_valid, validation_errors = validate_view_definition(view)
                if not is_valid:
                    logger.warning(f"View validation errors: {validation_errors}")
                    errors.extend(validation_errors)
                
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
            'index_file': index_file
        }
        
        logger.info(f"Generation complete! Summary: {json.dumps(self.generation_stats, indent=2)}")
        
        return summary

def generate_enhanced_cubes_from_engine(
    engine,  # SQLAlchemy Engine instance
    output_dir: str = "model", 
    schema: str = "public", 
    tables: Optional[List[str]] = None,
    generate_views: bool = False
):
    """
    Generate enhanced Cube.dev YAML files from a user-provided SQLAlchemy engine.
    
    This is the recommended approach for database-agnostic usage with enhanced features.
    
    Args:
        engine: Pre-configured SQLAlchemy Engine instance
        output_dir: Directory to save generated YAML files
        schema: Database schema name (ignored for SQLite)
        tables: Specific tables to process (None = all tables)
        generate_views: Whether to generate view definitions
        
    Returns:
        Dictionary with generation statistics
        
    Example:
        from sqlalchemy import create_engine
        
        # User provides their own engine
        engine = create_engine("postgresql://user:pass@localhost/db")
        
        # Generate enhanced cubes
        stats = generate_enhanced_cubes_from_engine(
            engine=engine,
            output_dir="my_enhanced_cubes",
            generate_views=True
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
    
    # Initialize enhanced generator
    generator = EnhancedCubeGenerator(output_dir)
    
    # Get tables to process
    if tables is None:
        tables = introspector.get_tables(schema)
    
    logger.info(f"Processing {len(tables)} tables with enhanced features...")
    
    stats = {
        'cubes_generated': 0,
        'views_generated': 0,
        'fact_tables': 0,
        'dimension_tables': 0,
        'lookup_tables': 0,
        'errors': []
    }
    
    cube_names = []
    table_analysis = {}
    
    # Process each table
    for table_name in tables:
        try:
            logger.info(f"Processing table: {table_name}")
            
            # Introspect table
            table_info = introspector.introspect_table(table_name, schema)
            table_analysis[table_name] = table_info
            
            # Update stats based on table type
            if table_info.table_type == 'fact':
                stats['fact_tables'] += 1
            elif table_info.table_type == 'dimension':
                stats['dimension_tables'] += 1
            else:
                stats['lookup_tables'] += 1
            
            # Generate enhanced cube
            cube = generator.generate_enhanced_cube_from_table(table_info)
            
            # Save cube YAML
            generator.save_cube_yaml(cube)
            cube_names.append(cube['name'])
            stats['cubes_generated'] += 1
            
            logger.info(f"Generated enhanced cube for {table_name} (type: {table_info.table_type})")
            
        except Exception as e:
            error_msg = f"Error processing table {table_name}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
            continue
    
    # Generate enhanced views if requested
    if generate_views and cube_names:
        try:
            # Generate relationship-aware views
            views = generator.generate_enhanced_views(table_analysis, cube_names)
            for view in views:
                generator.save_view_yaml(view)
                stats['views_generated'] += 1
            
        except Exception as e:
            error_msg = f"Error generating enhanced views: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)
    
    logger.info(f"Enhanced generation complete! Generated {stats['cubes_generated']} cubes and {stats['views_generated']} views in {output_dir}")
    return stats

