#!/usr/bin/env python3
"""
Simple example showing how to use the LLM database generator
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from llm_database_generator import generate_llm_enhanced_cubes_from_engine

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

if __name__ == "__main__":
    main()
