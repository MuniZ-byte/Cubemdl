#!/usr/bin/env python3
"""
LLM-Enhanced Description Generator for Cube.dev YAML

This module uses OpenAI/LLM to generate meaningful descriptions for cubes,
measures, and dimensions based on database schema and sample data.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TableContext:
    """Context information for LLM description generation"""
    table_name: str
    table_type: str  # fact, dimension, junction
    schema: str
    columns: List[Dict[str, Any]]
    sample_data: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    domain: str = "generic"

class LLMDescriptionGenerator:
    """Generate meaningful descriptions using LLM"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available. Install with: pip install openai")
            self.enabled = False
            return
        
        if not self.api_key:
            logger.warning("No OpenAI API key found. Using basic descriptions.")
            self.enabled = False
            return
            
        # Initialize OpenAI client
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
        self.enabled = True
        logger.info(f"LLM Description Generator initialized with model: {model}")
    
    def generate_cube_description(self, table_context: TableContext) -> str:
        """Generate cube description using LLM"""
        if not self.enabled:
            return self._fallback_cube_description(table_context.table_name)
        
        try:
            prompt = self._build_cube_prompt(table_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert. Generate concise, business-friendly descriptions for data cubes in a data warehouse."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            description = response.choices[0].message.content.strip()
            logger.debug(f"Generated cube description for {table_context.table_name}: {description}")
            return description
            
        except Exception as e:
            logger.warning(f"LLM failed for cube {table_context.table_name}: {e}")
            return self._fallback_cube_description(table_context.table_name)
    
    def generate_dimension_description(self, column_name: str, column_type: str, table_context: TableContext) -> str:
        """Generate dimension description using LLM"""
        if not self.enabled:
            return self._fallback_dimension_description(column_name)
        
        try:
            prompt = self._build_dimension_prompt(column_name, column_type, table_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert. Generate concise descriptions for database columns/dimensions. Keep it under 10 words."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3
            )
            
            description = response.choices[0].message.content.strip()
            logger.debug(f"Generated dimension description for {column_name}: {description}")
            return description
            
        except Exception as e:
            logger.warning(f"LLM failed for dimension {column_name}: {e}")
            return self._fallback_dimension_description(column_name)
    
    def generate_measure_description(self, measure_name: str, measure_type: str, column_name: str, table_context: TableContext) -> str:
        """Generate measure description using LLM"""
        if not self.enabled:
            return self._fallback_measure_description(measure_name, measure_type)
        
        try:
            prompt = self._build_measure_prompt(measure_name, measure_type, column_name, table_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst expert. Generate concise descriptions for business metrics/measures. Keep it under 15 words."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=60,
                temperature=0.3
            )
            
            description = response.choices[0].message.content.strip()
            logger.debug(f"Generated measure description for {measure_name}: {description}")
            return description
            
        except Exception as e:
            logger.warning(f"LLM failed for measure {measure_name}: {e}")
            return self._fallback_measure_description(measure_name, measure_type)
    
    def _build_cube_prompt(self, table_context: TableContext) -> str:
        """Build prompt for cube description"""
        
        # Sample data preview
        sample_preview = ""
        if table_context.sample_data:
            sample_preview = f"\nSample data preview:\n{json.dumps(table_context.sample_data[:2], indent=2, default=str)}"
        
        # Column summary
        column_names = [col['name'] for col in table_context.columns[:10]]
        
        prompt = f"""
Analyze this database table and generate a concise business description for a data cube:

Table: {table_context.table_name}
Schema: {table_context.schema}  
Domain: {table_context.domain}
Table Type: {table_context.table_type}
Columns: {', '.join(column_names)}
{sample_preview}

Generate a 1-sentence description that explains what business entity/process this table represents.
Focus on business value, not technical details.
"""
        return prompt.strip()
    
    def _build_dimension_prompt(self, column_name: str, column_type: str, table_context: TableContext) -> str:
        """Build prompt for dimension description"""
        
        prompt = f"""
Generate a concise description for this database column used as a dimension:

Table: {table_context.table_name}
Column: {column_name}
Type: {column_type}
Domain: {table_context.domain}

Describe what this column represents in business terms. Keep it under 10 words.
Examples:
- customer_id → "Unique customer identifier"
- order_date → "Date when order was placed"
- product_category → "Product classification category"
"""
        return prompt.strip()
    
    def _build_measure_prompt(self, measure_name: str, measure_type: str, column_name: str, table_context: TableContext) -> str:
        """Build prompt for measure description"""
        
        prompt = f"""
Generate a concise description for this business metric/measure:

Measure: {measure_name}
Type: {measure_type}
Source Column: {column_name}
Table: {table_context.table_name}
Domain: {table_context.domain}

Describe what this metric measures in business terms. Keep it under 15 words.
Examples:
- sum_amount → "Total monetary value of all transactions"
- avg_price → "Average price across all products"
- count_orders → "Total number of orders placed"
"""
        return prompt.strip()
    
    def _fallback_cube_description(self, table_name: str) -> str:
        """Fallback cube description when LLM is not available"""
        formatted_name = table_name.replace('_', ' ').title()
        return f"Data cube for {formatted_name} analysis"
    
    def _fallback_dimension_description(self, column_name: str) -> str:
        """Fallback dimension description when LLM is not available"""
        formatted_name = column_name.replace('_', ' ').title()
        return f"{formatted_name} dimension"
    
    def _fallback_measure_description(self, measure_name: str, measure_type: str) -> str:
        """Fallback measure description when LLM is not available"""
        formatted_name = measure_name.replace('_', ' ').title()
        return f"{formatted_name} metric"

class EnhancedDescriptionService:
    """Service to coordinate LLM and fallback description generation"""
    
    def __init__(self, enable_llm: bool = True, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.llm_generator = None
        
        if enable_llm:
            self.llm_generator = LLMDescriptionGenerator(api_key, model)
            if self.llm_generator.enabled:
                logger.info("Enhanced descriptions enabled with LLM")
            else:
                logger.info("Enhanced descriptions disabled - using basic templates")
        else:
            logger.info("LLM descriptions disabled by configuration")
    
    def describe_cube(self, table_context: TableContext) -> str:
        """Generate cube description"""
        if self.llm_generator and self.llm_generator.enabled:
            return self.llm_generator.generate_cube_description(table_context)
        else:
            return self._basic_cube_description(table_context.table_name, table_context.table_type)
    
    def describe_dimension(self, column_name: str, column_type: str, table_context: TableContext) -> str:
        """Generate dimension description"""
        if self.llm_generator and self.llm_generator.enabled:
            return self.llm_generator.generate_dimension_description(column_name, column_type, table_context)
        else:
            return self._basic_dimension_description(column_name, table_context.table_type)
    
    def describe_measure(self, measure_name: str, measure_type: str, column_name: str, table_context: TableContext) -> str:
        """Generate measure description"""
        if self.llm_generator and self.llm_generator.enabled:
            return self.llm_generator.generate_measure_description(measure_name, measure_type, column_name, table_context)
        else:
            return self._basic_measure_description(measure_name, measure_type, table_context.domain)
    
    def _basic_cube_description(self, table_name: str, table_type: str) -> str:
        """Basic cube description with table type awareness"""
        formatted_name = table_name.replace('_', ' ').title()
        
        if table_type == 'fact':
            return f"{formatted_name} transaction and metrics data"
        elif table_type == 'dimension':
            return f"{formatted_name} master data and attributes"
        elif table_type == 'junction':
            return f"{formatted_name} relationship mapping data"
        else:
            return f"Data cube for {formatted_name} analysis"
    
    def _basic_dimension_description(self, column_name: str, table_type: str) -> str:
        """Basic dimension description with context awareness"""
        formatted_name = column_name.replace('_', ' ').title()
        
        # Smart mappings for common column patterns
        if column_name.endswith('_id'):
            entity = column_name[:-3].replace('_', ' ').title()
            return f"Unique {entity} identifier"
        elif 'date' in column_name or 'time' in column_name:
            return f"Date/time when {formatted_name.lower()} occurred"
        elif column_name in ['status', 'state']:
            return f"Current status or state"
        elif column_name in ['name', 'title']:
            return f"Display name or title"
        elif 'zip' in column_name or 'postal' in column_name:
            return f"Postal/ZIP code"
        elif 'city' in column_name:
            return f"City location"
        elif 'state' in column_name and 'status' not in column_name:
            return f"State/province location"
        else:
            return f"{formatted_name} attribute"
    
    def _basic_measure_description(self, measure_name: str, measure_type: str, domain: str) -> str:
        """Basic measure description with domain awareness"""
        formatted_name = measure_name.replace('_', ' ').title()
        
        # Domain-specific descriptions
        if domain == 'ecommerce':
            if 'price' in measure_name or 'amount' in measure_name:
                return f"Total {measure_type} of monetary values"
            elif 'quantity' in measure_name:
                return f"Total {measure_type} of items"
            elif measure_type == 'count':
                return f"Total number of records"
        
        # Generic descriptions
        if measure_type == 'sum':
            return f"Total sum of {formatted_name.lower()}"
        elif measure_type == 'avg':
            return f"Average {formatted_name.lower()}"
        elif measure_type == 'count':
            return f"Count of {formatted_name.lower()}"
        elif measure_type == 'count_distinct':
            return f"Unique count of {formatted_name.lower()}"
        else:
            return f"{measure_type.title()} of {formatted_name.lower()}"

