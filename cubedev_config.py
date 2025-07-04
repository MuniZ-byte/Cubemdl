# Configuration for PostgreSQL to Cube.dev YAML Generator

# Database Connection Templates
DATABASE_CONFIGS = {
    "development": {
        "host": "localhost",
        "port": 5432,
        "database": "development_db",
        "username": "dev_user",
        "password": "dev_password",
        "schema": "public"
    },
    "staging": {
        "host": "staging-db.company.com",
        "port": 5432,
        "database": "staging_db",
        "username": "staging_user",
        "password": "${STAGING_DB_PASSWORD}",
        "schema": "public"
    },
    "production": {
        "host": "prod-db.company.com",
        "port": 5432,
        "database": "production_db",
        "username": "readonly_user",
        "password": "${PROD_DB_PASSWORD}",
        "schema": "public"
    }
}

# Table Classification Rules
TABLE_CLASSIFICATION = {
    "fact_table_indicators": {
        "name_patterns": [
            "fact_", "sales_", "orders_", "transactions_", "events_", 
            "payments_", "bookings_", "sessions_", "activities_",
            "_fact", "_sales", "_orders", "_transactions", "_events"
        ],
        "column_patterns": [
            "amount", "quantity", "price", "cost", "value", "total",
            "count", "revenue", "profit", "volume", "weight",
            "duration", "distance", "score", "rating"
        ],
        "foreign_key_threshold": 2,  # Minimum FK count for fact tables
        "numeric_column_threshold": 0.3  # Minimum ratio of numeric columns
    },
    
    "dimension_table_indicators": {
        "name_patterns": [
            "dim_", "customers", "products", "users", "categories",
            "locations", "employees", "vendors", "suppliers",
            "_dim", "_master", "_ref", "_lookup"
        ],
        "column_patterns": [
            "name", "title", "description", "category", "type",
            "status", "code", "label", "classification", "group"
        ],
        "text_column_threshold": 0.4  # Minimum ratio of text columns
    },
    
    "junction_table_indicators": {
        "name_patterns": [
            "_junction", "_bridge", "_mapping", "_relation",
            "user_roles", "product_categories", "order_items"
        ],
        "foreign_key_threshold": 2,  # Exactly 2 or more FKs
        "max_columns": 6  # Maximum columns for junction tables
    }
}

# Column Type Mapping Configuration
COLUMN_TYPE_MAPPINGS = {
    # Numeric types
    "integer": "number",
    "bigint": "number", 
    "smallint": "number",
    "tinyint": "number",
    "decimal": "number",
    "numeric": "number",
    "real": "number",
    "double precision": "number",
    "float": "number",
    "money": "number",
    
    # String types
    "varchar": "string",
    "character varying": "string",
    "text": "string",
    "char": "string",
    "character": "string",
    "nvarchar": "string",
    "nchar": "string",
    "citext": "string",
    
    # Time types
    "timestamp": "time",
    "timestamp without time zone": "time",
    "timestamp with time zone": "time",
    "timestamptz": "time",
    "date": "time",
    "time": "time",
    "timetz": "time",
    "interval": "string",
    
    # Boolean types
    "boolean": "boolean",
    "bool": "boolean",
    
    # UUID and JSON
    "uuid": "string",
    "json": "string",
    "jsonb": "string",
    
    # Array types (mapped to string for simplicity)
    "array": "string",
    "text[]": "string",
    "varchar[]": "string",
    "integer[]": "string"
}

# Measure Generation Rules
MEASURE_GENERATION_RULES = {
    "default_measures": [
        {
            "name": "count",
            "type": "count",
            "description": "Total number of records",
            "applies_to": "all"
        },
        {
            "name": "count_distinct",
            "type": "count_distinct",
            "description": "Count of unique records",
            "applies_to": "primary_key"
        }
    ],
    
    "numeric_measures": {
        "financial_columns": {
            "patterns": ["amount", "price", "cost", "value", "total", "revenue", "profit"],
            "measures": ["sum", "avg", "min", "max"],
            "format": "currency"
        },
        "quantity_columns": {
            "patterns": ["quantity", "count", "volume", "weight"],
            "measures": ["sum", "avg", "min", "max"],
            "format": "number"
        },
        "score_columns": {
            "patterns": ["score", "rating", "percentage"],
            "measures": ["avg", "min", "max"],
            "format": "percent"
        },
        "metric_columns": {
            "patterns": ["duration", "distance", "size", "length", "width", "height"],
            "measures": ["sum", "avg", "min", "max"],
            "format": "number"
        }
    }
}

# Dimension Generation Rules
DIMENSION_GENERATION_RULES = {
    "time_dimensions": {
        "patterns": ["created_at", "updated_at", "timestamp", "date", "time"],
        "granularities": [
            {"name": "hour", "interval": "1 hour"},
            {"name": "day", "interval": "1 day"},
            {"name": "week", "interval": "1 week"},
            {"name": "month", "interval": "1 month"},
            {"name": "quarter", "interval": "1 quarter"},
            {"name": "year", "interval": "1 year"}
        ],
        "custom_granularities": [
            {
                "name": "fiscal_year", 
                "interval": "1 year", 
                "offset": "3 months",
                "description": "Fiscal year starting April"
            },
            {
                "name": "business_week", 
                "interval": "1 week", 
                "offset": "1 day",
                "description": "Week starting on Monday"
            }
        ]
    },
    
    "categorical_dimensions": {
        "patterns": ["status", "type", "category", "state", "kind", "classification"]
    },
    
    "identifier_dimensions": {
        "patterns": ["id", "uuid", "key", "code", "reference"]
    }
}

# Segment Generation Rules  
SEGMENT_GENERATION_RULES = {
    "status_segments": {
        "patterns": ["status", "state", "is_active", "active", "enabled"],
        "segments": [
            {
                "name": "active",
                "condition": "= 'active'",
                "description": "Active records only"
            },
            {
                "name": "inactive", 
                "condition": "= 'inactive'",
                "description": "Inactive records only"
            }
        ]
    },
    
    "time_segments": {
        "patterns": ["created_at", "updated_at", "timestamp"],
        "segments": [
            {
                "name": "recent",
                "condition": ">= CURRENT_DATE - INTERVAL '30 days'",
                "description": "Records from last 30 days"
            },
            {
                "name": "this_year",
                "condition": ">= DATE_TRUNC('year', CURRENT_DATE)",
                "description": "Records from current year"
            },
            {
                "name": "this_month",
                "condition": ">= DATE_TRUNC('month', CURRENT_DATE)",
                "description": "Records from current month"
            }
        ]
    },
    
    "boolean_segments": {
        "patterns": ["is_deleted", "is_published", "is_enabled", "visible"],
        "segments": [
            {
                "name": "published",
                "condition": "= true",
                "description": "Published records only"
            }
        ]
    }
}

# Pre-aggregation Configuration
PRE_AGGREGATION_CONFIG = {
    "fact_tables": {
        "default_granularity": "day",
        "partition_granularity": "month",
        "refresh_interval": "1 hour",
        "max_dimensions": 3,
        "preferred_dimensions": ["status", "type", "category", "state"]
    },
    
    "dimension_tables": {
        "enable": False  # Usually not needed for dimension tables
    },
    
    "time_ranges": {
        "build_range_start": "SELECT MIN({time_column}) FROM {table}",
        "build_range_end": "SELECT MAX({time_column}) FROM {table}"
    }
}

# View Generation Configuration
VIEW_GENERATION_CONFIG = {
    "business_metrics_view": {
        "name": "business_metrics",
        "description": "Key business metrics across all entities",
        "include_measures": ["count", "sum_*", "avg_*"],
        "folders": [
            {
                "name": "revenue_metrics",
                "patterns": ["revenue", "amount", "total", "value"]
            },
            {
                "name": "volume_metrics", 
                "patterns": ["count", "quantity", "volume"]
            },
            {
                "name": "performance_metrics",
                "patterns": ["score", "rating", "percentage"]
            }
        ]
    },
    
    "fact_analysis_view": {
        "name": "fact_analysis",
        "description": "Analysis view for fact tables",
        "table_types": ["fact"],
        "include_joins": True
    },
    
    "dimension_catalog_view": {
        "name": "dimension_catalog",
        "description": "Catalog of all dimensional data",
        "table_types": ["dimension"],
        "include_joins": False
    }
}

# Output Configuration
OUTPUT_CONFIG = {
    "directory_structure": {
        "cubes": "cubes",
        "views": "views", 
        "macros": "macros"
    },
    
    "file_naming": {
        "cube_suffix": ".yml",
        "view_suffix": ".yml",
        "use_table_name": True,
        "lowercase": True
    },
    
    "yaml_formatting": {
        "indent": 2,
        "sort_keys": False,
        "default_flow_style": False,
        "include_comments": True
    }
}

# Validation Rules
VALIDATION_RULES = {
    "cube_validation": {
        "required_fields": ["name", "sql_table"],
        "recommended_fields": ["measures", "dimensions"],
        "max_measures": 50,
        "max_dimensions": 100
    },
    
    "view_validation": {
        "required_fields": ["name", "cubes"],
        "max_cubes": 20
    },
    
    "naming_conventions": {
        "cube_name_pattern": r"^[a-z][a-z0-9_]*$",
        "measure_name_pattern": r"^[a-z][a-z0-9_]*$",
        "dimension_name_pattern": r"^[a-z][a-z0-9_]*$"
    }
}

# Domain-Specific Templates
DOMAIN_TEMPLATES = {
    "ecommerce": {
        "fact_tables": ["orders", "order_items", "payments"],
        "dimension_tables": ["customers", "products", "categories"],
        "key_measures": ["total_amount", "quantity", "profit"],
        "key_dimensions": ["order_date", "customer_id", "product_id"]
    },
    
    "saas": {
        "fact_tables": ["usage_events", "billing_events", "feature_usage"],
        "dimension_tables": ["users", "subscriptions", "features"],
        "key_measures": ["usage_count", "billing_amount", "active_users"],
        "key_dimensions": ["event_date", "user_id", "subscription_id"]
    },
    
    "finance": {
        "fact_tables": ["transactions", "positions", "trades"],
        "dimension_tables": ["accounts", "assets", "portfolios"],
        "key_measures": ["amount", "balance", "pnl"],
        "key_dimensions": ["transaction_date", "account_id", "asset_id"]
    }
}
