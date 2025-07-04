"""
Utility functions for PostgreSQL to Cube.dev YAML generation
"""

import re
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import yaml
from datetime import datetime

logger = logging.getLogger(__name__)

class CubeDevUtils:
    """Utility functions for Cube.dev YAML generation"""
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize a name to be Cube.dev compliant"""
        # Convert to lowercase and replace invalid characters
        sanitized = re.sub(r'[^a-z0-9_]', '_', name.lower())
        
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = 'col_' + sanitized
        
        # Remove multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove trailing underscores
        sanitized = sanitized.strip('_')
        
        return sanitized
    
    @staticmethod
    def detect_column_purpose(column_name: str, column_type: str) -> str:
        """Detect the purpose/category of a column"""
        col_name = column_name.lower()
        
        # Primary key detection
        if col_name in ['id', 'uuid'] or col_name.endswith('_id'):
            return 'identifier'
        
        # Time column detection
        if any(term in col_name for term in ['date', 'time', 'timestamp', 'created', 'updated']):
            return 'time'
        
        # Financial column detection
        if any(term in col_name for term in ['amount', 'price', 'cost', 'value', 'total', 'revenue']):
            return 'financial'
        
        # Quantity/metric detection
        if any(term in col_name for term in ['quantity', 'count', 'volume', 'weight', 'score']):
            return 'metric'
        
        # Status/category detection
        if any(term in col_name for term in ['status', 'type', 'category', 'state', 'kind']):
            return 'categorical'
        
        # Name/description detection
        if any(term in col_name for term in ['name', 'title', 'description', 'label']):
            return 'descriptive'
        
        # Boolean detection
        if col_name.startswith('is_') or col_name.startswith('has_') or 'boolean' in column_type.lower():
            return 'boolean'
        
        return 'generic'
    
    @staticmethod
    def generate_description(entity_name: str, entity_type: str, context: str = None) -> str:
        """Generate a descriptive text for cubes, measures, dimensions"""
        entity_name_formatted = entity_name.replace('_', ' ').title()
        
        if entity_type == 'cube':
            return f"Data cube for {entity_name_formatted} analysis"
        elif entity_type == 'measure':
            return f"{entity_name_formatted} metric"
        elif entity_type == 'dimension':
            return f"{entity_name_formatted} dimension"
        elif entity_type == 'view':
            return f"Business view for {entity_name_formatted}"
        else:
            return f"{entity_name_formatted} {entity_type}"
    
    @staticmethod
    def infer_measure_format(column_name: str, column_purpose: str) -> Optional[str]:
        """Infer the appropriate format for a measure"""
        col_name = column_name.lower()
        
        if column_purpose == 'financial':
            return 'currency'
        elif 'percent' in col_name or 'rate' in col_name:
            return 'percent'
        elif column_purpose == 'metric':
            return 'number'
        
        return None
    
    @staticmethod
    def determine_join_relationship(
        source_table: str, 
        target_table: str, 
        fk_columns: List[str]
    ) -> str:
        """Determine the relationship type for joins"""
        
        # Check for junction table patterns
        if len(fk_columns) >= 2:
            # Could be many-to-many through junction
            return 'many_to_one'  # From junction to dimension
        
        # Default to many-to-one (fact to dimension)
        return 'many_to_one'
    
    @staticmethod
    def generate_sql_expression(column_name: str, operation: str, table_alias: str = "CUBE") -> str:
        """Generate SQL expressions for measures and dimensions"""
        
        expressions = {
            'count': f"COUNT(*)",
            'count_distinct': f"COUNT(DISTINCT {{{table_alias}}}.{column_name})",
            'sum': f"SUM({{{table_alias}}}.{column_name})",
            'avg': f"AVG({{{table_alias}}}.{column_name})",
            'min': f"MIN({{{table_alias}}}.{column_name})",
            'max': f"MAX({{{table_alias}}}.{column_name})",
            'concat_names': f"CONCAT({{{table_alias}}}.first_name, ' ', {{{table_alias}}}.last_name)",
            'year_from_date': f"EXTRACT(YEAR FROM {{{table_alias}}}.{column_name})",
            'month_from_date': f"EXTRACT(MONTH FROM {{{table_alias}}}.{column_name})",
            'day_from_date': f"EXTRACT(DAY FROM {{{table_alias}}}.{column_name})"
        }
        
        return expressions.get(operation, f"{{{table_alias}}}.{column_name}")

class YAMLFormatter:
    """Handle YAML formatting and output"""
    
    @staticmethod
    def format_cube_yaml(cube_data: Dict[str, Any]) -> str:
        """Format cube data as YAML string"""
        return yaml.dump(
            {'cubes': [cube_data]}, 
            default_flow_style=False, 
            sort_keys=False, 
            indent=2,
            allow_unicode=True
        )
    
    @staticmethod
    def format_view_yaml(view_data: Dict[str, Any]) -> str:
        """Format view data as YAML string"""
        return yaml.dump(
            {'views': [view_data]}, 
            default_flow_style=False, 
            sort_keys=False, 
            indent=2,
            allow_unicode=True
        )
    
    @staticmethod
    def add_yaml_header(content: str, metadata: Dict[str, Any]) -> str:
        """Add header comments to YAML content"""
        header_lines = [
            "# Generated Cube.dev YAML Configuration",
            f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Database: {metadata.get('database', 'N/A')}",
            f"# Schema: {metadata.get('schema', 'N/A')}",
            f"# Generator: PostgreSQL to Cube.dev YAML Generator",
            "#" + "=" * 70,
            ""
        ]
        
        return "\n".join(header_lines) + "\n" + content
    
    @staticmethod
    def validate_yaml_syntax(yaml_content: str) -> Tuple[bool, Optional[str]]:
        """Validate YAML syntax"""
        try:
            yaml.safe_load(yaml_content)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)

class DatabaseAnalyzer:
    """Analyze database patterns and relationships"""
    
    @staticmethod
    def analyze_table_relationships(tables_info: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze relationships between tables"""
        relationships = {}
        
        for table in tables_info:
            table_name = table['name']
            relationships[table_name] = []
            
            # Find tables this table references
            for fk in table.get('foreign_keys', []):
                referenced_table = fk.get('referred_table')
                if referenced_table:
                    relationships[table_name].append(referenced_table)
        
        return relationships
    
    @staticmethod
    def detect_fact_dimension_pattern(tables_info: List[Dict[str, Any]]) -> Dict[str, str]:
        """Detect fact and dimension tables based on patterns"""
        table_classifications = {}
        
        for table in tables_info:
            table_name = table['name']
            
            # Count foreign keys and numeric columns
            fk_count = len(table.get('foreign_keys', []))
            numeric_cols = sum(1 for col in table.get('columns', []) 
                             if 'int' in col.get('type', '').lower() or 
                                'decimal' in col.get('type', '').lower() or
                                'numeric' in col.get('type', '').lower())
            
            total_cols = len(table.get('columns', []))
            
            # Classification logic
            if fk_count >= 2 and total_cols <= 6:
                table_classifications[table_name] = 'junction'
            elif fk_count >= 2 and numeric_cols > 0:
                table_classifications[table_name] = 'fact'
            elif any(term in table_name.lower() for term in ['dim_', '_dim', 'lookup', 'reference']):
                table_classifications[table_name] = 'dimension'
            elif numeric_cols / total_cols > 0.3 and fk_count > 0:
                table_classifications[table_name] = 'fact'
            else:
                table_classifications[table_name] = 'dimension'
        
        return table_classifications
    
    @staticmethod
    def suggest_pre_aggregations(table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest pre-aggregations based on table structure"""
        suggestions = []
        
        # Find time columns
        time_columns = [col['name'] for col in table_info.get('columns', []) 
                       if 'timestamp' in col.get('type', '').lower() or 
                          'date' in col.get('type', '').lower()]
        
        # Find categorical columns with low cardinality
        categorical_columns = [col['name'] for col in table_info.get('columns', [])
                             if any(term in col['name'].lower() 
                                   for term in ['status', 'type', 'category', 'state'])]
        
        if time_columns and categorical_columns:
            suggestion = {
                'name': 'main_rollup',
                'time_dimension': time_columns[0],
                'granularity': 'day',
                'dimensions': categorical_columns[:3],  # Limit to 3 dimensions
                'measures': ['count'],
                'refresh_key': {'every': '1 hour'}
            }
            suggestions.append(suggestion)
        
        return suggestions

class FileManager:
    """Manage file operations for generated YAML files"""
    
    def __init__(self, base_output_dir: str):
        self.base_dir = Path(base_output_dir)
        self.cubes_dir = self.base_dir / "cubes"
        self.views_dir = self.base_dir / "views"
        self.macros_dir = self.base_dir / "macros"
        
        # Create directories
        self.cubes_dir.mkdir(parents=True, exist_ok=True)
        self.views_dir.mkdir(parents=True, exist_ok=True)
        self.macros_dir.mkdir(parents=True, exist_ok=True)
    
    def save_cube_file(self, cube_data: Dict[str, Any], filename: str = None) -> str:
        """Save cube YAML file"""
        if not filename:
            filename = f"{cube_data['name']}.yml"
        
        # Remove _metadata before saving (Cube.dev doesn't support it)
        cube_data_clean = cube_data.copy()
        if '_metadata' in cube_data_clean:
            del cube_data_clean['_metadata']
        
        filepath = self.cubes_dir / filename
        content = YAMLFormatter.format_cube_yaml(cube_data_clean)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved cube file: {filepath}")
        return str(filepath)
    
    def save_view_file(self, view_data: Dict[str, Any], filename: str = None) -> str:
        """Save view YAML file"""
        if not filename:
            filename = f"{view_data['name']}.yml"
        
        filepath = self.views_dir / filename
        content = YAMLFormatter.format_view_yaml(view_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved view file: {filepath}")
        return str(filepath)
    
    def create_index_file(self, generated_files: List[str]) -> str:
        """Create an index file listing all generated files"""
        index_content = [
            "# Generated Cube.dev Files Index",
            f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Generated Files:",
            ""
        ]
        
        # Group files by type
        cube_files = [f for f in generated_files if '/cubes/' in f]
        view_files = [f for f in generated_files if '/views/' in f]
        
        if cube_files:
            index_content.extend([
                "### Cubes:",
                ""
            ])
            for file in sorted(cube_files):
                filename = Path(file).name
                index_content.append(f"- {filename}")
            index_content.append("")
        
        if view_files:
            index_content.extend([
                "### Views:",
                ""
            ])
            for file in sorted(view_files):
                filename = Path(file).name
                index_content.append(f"- {filename}")
            index_content.append("")
        
        index_content.extend([
            f"**Total Files Generated:** {len(generated_files)}",
            "",
            "## Usage:",
            "",
            "1. Copy the generated files to your Cube.dev project",
            "2. Update database connection settings in cube.js",
            "3. Review and customize the generated cubes and views",
            "4. Run `cube validate` to check for any issues",
            ""
        ])
        
        index_filepath = self.base_dir / "README.md"
        with open(index_filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(index_content))
        
        logger.info(f"Created index file: {index_filepath}")
        return str(index_filepath)
    
    def backup_existing_files(self) -> bool:
        """Backup existing files before generating new ones"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.base_dir / f"backup_{timestamp}"
            
            if self.cubes_dir.exists() and any(self.cubes_dir.iterdir()):
                backup_cubes = backup_dir / "cubes"
                backup_cubes.mkdir(parents=True, exist_ok=True)
                
                for file in self.cubes_dir.glob("*.yml"):
                    file.rename(backup_cubes / file.name)
            
            if self.views_dir.exists() and any(self.views_dir.iterdir()):
                backup_views = backup_dir / "views"
                backup_views.mkdir(parents=True, exist_ok=True)
                
                for file in self.views_dir.glob("*.yml"):
                    file.rename(backup_views / file.name)
            
            if backup_dir.exists():
                logger.info(f"Backed up existing files to: {backup_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup existing files: {e}")
            return False

def validate_cube_definition(cube_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a cube definition for common issues"""
    errors = []
    
    # Check required fields
    if 'name' not in cube_data:
        errors.append("Cube must have a name")
    
    if 'sql_table' not in cube_data and 'sql' not in cube_data:
        errors.append("Cube must have either sql_table or sql defined")
    
    # Check name format
    if 'name' in cube_data:
        name = cube_data['name']
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            errors.append(f"Cube name '{name}' should start with lowercase letter and contain only letters, numbers, and underscores")
    
    # Check measures
    if 'measures' in cube_data:
        for measure in cube_data['measures']:
            if 'name' not in measure:
                errors.append("All measures must have a name")
            if 'type' not in measure:
                errors.append(f"Measure '{measure.get('name', 'unnamed')}' must have a type")
    
    # Check dimensions
    if 'dimensions' in cube_data:
        for dimension in cube_data['dimensions']:
            if 'name' not in dimension:
                errors.append("All dimensions must have a name")
            if 'sql' not in dimension:
                errors.append(f"Dimension '{dimension.get('name', 'unnamed')}' must have sql defined")
    
    return len(errors) == 0, errors

def validate_view_definition(view_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a view definition for common issues"""
    errors = []
    
    # Check required fields
    if 'name' not in view_data:
        errors.append("View must have a name")
    
    # Views can have either 'cubes' or 'includes'
    if 'cubes' not in view_data and 'includes' not in view_data:
        errors.append("View must have cubes or includes defined")
    
    # Check name format
    if 'name' in view_data:
        name = view_data['name']
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            errors.append(f"View name '{name}' should start with lowercase letter and contain only letters, numbers, and underscores")
    
    return len(errors) == 0, errors
