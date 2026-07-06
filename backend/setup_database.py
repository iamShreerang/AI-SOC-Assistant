#!/usr/bin/env python3
"""
Quick Setup Script for AI SOC Assistant Database Integration

This script helps you set up the Supabase PostgreSQL database and initialize
the backend with minimal manual configuration.

Usage:
    python setup_database.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"[OK] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def print_info(text):
    print(f"[INFO] {text}")

def check_python_version():
    """Ensure Python 3.11+ is being used."""
    if sys.version_info < (3, 11):
        print_error(f"Python 3.11+ required. You have {sys.version}")
        sys.exit(1)
    print_success(f"Python {sys.version.split()[0]} detected")

def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if not env_path.exists():
        print_info(".env file not found. Creating from .env.example...")
        example_path = Path(".env.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print_success(".env file created")
            print_info("Please edit .env and add your DATABASE_URL")
            return False
        else:
            print_error(".env.example not found")
            return False
    print_success(".env file exists")
    return True

def check_database_url():
    """Check if DATABASE_URL is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url or db_url == "postgresql://user:password@localhost:5432/soc_db":
        print_error("DATABASE_URL not configured correctly")
        print_info("Please update DATABASE_URL in .env with your connection string")
        print_info("  Local:    postgresql://user:password@localhost:5432/soc_db")
        print_info("  Supabase: postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres")
        return False
    
    print_success("DATABASE_URL configured")
    return True

def install_dependencies():
    """Install required Python packages."""
    print_info("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
                      check=True, capture_output=True)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    print_info("Testing database connection...")
    try:
        from app.database import check_connection
        if check_connection():
            print_success("Database connection successful")
            return True
        else:
            print_error("Database connection failed")
            return False
    except Exception as e:
        print_error(f"Database connection error: {e}")
        return False

def create_tables():
    """Create database tables."""
    print_info("Creating database tables...")
    try:
        from app.database import create_tables as create_db_tables
        create_db_tables()
        print_success("Database tables created")
        return True
    except Exception as e:
        print_error(f"Failed to create tables: {e}")
        print_info("You may need to run: alembic upgrade head")
        return False

def create_default_users():
    """Create default users."""
    print_info("Creating default users...")
    try:
        from app.database import SessionLocal
        from app.services.db_auth_service import create_default_users as create_users
        db = SessionLocal()
        create_users(db)
        db.close()
        print_success("Default users created")
        print_info("  - Username: analyst | Password: analyst123")
        print_info("  - Username: admin   | Password: admin123")
        print_info("  ⚠️  CHANGE THESE PASSWORDS IN PRODUCTION!")
        return True
    except Exception as e:
        print_error(f"Failed to create users: {e}")
        return False

def run_alembic_upgrade():
    """Run Alembic migrations."""
    print_info("Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True, capture_output=True)
        print_success("Database migrations completed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Migration failed: {e}")
        return False
    except FileNotFoundError:
        print_info("Alembic not found - tables will be created automatically on startup")
        return True

def main():
    """Main setup function."""
    print_header("AI SOC Assistant - Database Setup")
    
    # Change to backend directory if needed
    if Path("backend").exists() and not Path("app").exists():
        os.chdir("backend")
        print_info("Changed to backend directory")
    
    # Step 1: Check Python version
    print_header("Step 1: Checking Python Version")
    check_python_version()
    
    # Step 2: Check .env file
    print_header("Step 2: Checking Configuration")
    if not check_env_file():
        print_info("\nPlease complete the following steps:")
        print("  1. Edit .env file")
        print("  2. Add your Supabase DATABASE_URL")
        print("  3. Run this script again")
        sys.exit(0)
    
    if not check_database_url():
        sys.exit(0)
    
    # Step 3: Install dependencies
    print_header("Step 3: Installing Dependencies")
    if not install_dependencies():
        sys.exit(1)
    
    # Step 4: Test database connection
    print_header("Step 4: Testing Database Connection")
    if not test_database_connection():
        print_info("\nPlease check:")
        print("  1. Your Supabase project is running")
        print("  2. DATABASE_URL is correct in .env")
        print("  3. Your internet connection")
        sys.exit(1)
    
    # Step 5: Run migrations or create tables
    print_header("Step 5: Setting Up Database Schema")
    migration_success = run_alembic_upgrade()
    if not migration_success:
        # Fallback to direct table creation
        if not create_tables():
            sys.exit(1)
    
    # Step 6: Create default users
    print_header("Step 6: Creating Default Users")
    if not create_default_users():
        print_info("Default users may already exist")
    
    # Success!
    print_header("Setup Complete!")
    print_success("Database integration ready")
    print("\nNext steps:")
    print("  1. Start the backend:")
    print("     uvicorn app.main:app --reload")
    print("\n  2. Test the API:")
    print("     http://localhost:8000/docs")
    print("\n  3. Login with default credentials:")
    print("     Username: analyst | Password: analyst123")
    print("\n  4. ⚠️  Change default passwords before production!")
    print("\nFor more information, see:")
    print("  - DATABASE_SETUP.md")
    print("  - IMPLEMENTATION_SUMMARY.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
