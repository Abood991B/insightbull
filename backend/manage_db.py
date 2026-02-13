#!/usr/bin/env python3
"""
Database Management CLI

Command-line interface for managing database migrations and operations.
This script provides easy-to-use commands for common database tasks.

Usage:
    python manage_db.py --help
    python manage_db.py migrate "Add new table"
    python manage_db.py upgrade
    python manage_db.py status
    python manage_db.py history
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.data_access.database.migration_manager import MigrationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Database Management CLI for InsightBull',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_db.py migrate "Add user preferences table"
  python manage_db.py migrate "Update stock model" --no-autogenerate  
  python manage_db.py upgrade
  python manage_db.py upgrade 8653cc238299
  python manage_db.py downgrade base
  python manage_db.py status
  python manage_db.py history
  python manage_db.py validate
  python manage_db.py reset --confirm
        """
    )
    
    parser.add_argument(
        '--backend-root',
        type=str,
        help='Path to backend root directory (auto-detected if not provided)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migrate command
    migrate_parser = subparsers.add_parser(
        'migrate', help='Create a new migration'
    )
    migrate_parser.add_argument(
        'message', type=str, help='Migration message/description'
    )
    migrate_parser.add_argument(
        '--no-autogenerate', action='store_true',
        help='Create empty migration without autogenerate'
    )
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser(
        'upgrade', help='Upgrade database to a specific revision'
    )
    upgrade_parser.add_argument(
        'revision', nargs='?', default='head',
        help='Target revision (default: head)'
    )
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser(
        'downgrade', help='Downgrade database to a specific revision'
    )
    downgrade_parser.add_argument(
        'revision', type=str, help='Target revision'
    )
    
    # Status command
    subparsers.add_parser(
        'status', help='Show current migration status'
    )
    
    # History command
    subparsers.add_parser(
        'history', help='Show migration history'
    )
    
    # Current command
    subparsers.add_parser(
        'current', help='Show current revision'
    )
    
    # Validate command
    subparsers.add_parser(
        'validate', help='Validate migration files'
    )
    
    # Reset command
    reset_parser = subparsers.add_parser(
        'reset', help='Reset database (WARNING: destroys all data!)'
    )
    reset_parser.add_argument(
        '--confirm', action='store_true',
        help='Confirm that you want to reset the database'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize migration manager
        manager = MigrationManager(args.backend_root)
        
        # Execute the requested command
        if args.command == 'migrate':
            handle_migrate(manager, args)
        elif args.command == 'upgrade':
            handle_upgrade(manager, args)
        elif args.command == 'downgrade':
            handle_downgrade(manager, args)
        elif args.command == 'status':
            handle_status(manager)
        elif args.command == 'history':
            handle_history(manager)
        elif args.command == 'current':
            handle_current(manager)
        elif args.command == 'validate':
            handle_validate(manager)
        elif args.command == 'reset':
            handle_reset(manager, args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


def handle_migrate(manager: MigrationManager, args):
    """Handle migrate command"""
    print(f"Creating migration: {args.message}")
    
    autogenerate = not args.no_autogenerate
    result = manager.create_migration(args.message, autogenerate)
    
    if result['success']:
        print("✅ Migration created successfully!")
        if result['stdout']:
            print(f"Output: {result['stdout']}")
    else:
        print("❌ Failed to create migration")
        print(f"Error: {result['stderr']}")
        sys.exit(1)


def handle_upgrade(manager: MigrationManager, args):
    """Handle upgrade command"""
    print(f"Upgrading database to: {args.revision}")
    
    result = manager.upgrade_database(args.revision)
    
    if result['success']:
        print("✅ Database upgraded successfully!")
        if result['stdout']:
            print(f"Output: {result['stdout']}")
    else:
        print("❌ Failed to upgrade database")
        print(f"Error: {result['stderr']}")
        sys.exit(1)


def handle_downgrade(manager: MigrationManager, args):
    """Handle downgrade command"""
    print(f"⚠️  WARNING: Downgrading database to: {args.revision}")
    print("This may result in data loss!")
    
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Downgrade cancelled.")
        return
    
    result = manager.downgrade_database(args.revision)
    
    if result['success']:
        print("✅ Database downgraded successfully!")
        if result['stdout']:
            print(f"Output: {result['stdout']}")
    else:
        print("❌ Failed to downgrade database")
        print(f"Error: {result['stderr']}")
        sys.exit(1)


def handle_status(manager: MigrationManager):
    """Handle status command"""
    print("Checking migration status...")
    
    result = manager.check_migration_status()
    
    if result['success']:
        print(f"📋 Current revision: {result['current_revision']}")
        print(f"🎯 Head revisions: {', '.join(result['head_revisions'])}")
        
        if result['needs_upgrade']:
            print("⚡ Database needs upgrade!")
        else:
            print("✅ Database is up to date")
    else:
        print("❌ Failed to check migration status")
        print(f"Error: {result.get('stderr', 'Unknown error')}")
        sys.exit(1)


def handle_history(manager: MigrationManager):
    """Handle history command"""
    print("Migration history:")
    
    result = manager.get_migration_history()
    
    if result['success']:
        if 'migrations' in result and result['migrations']:
            for migration in result['migrations']:
                print(f"  📝 {migration}")
        else:
            print("  No migrations found")
            
        if result['stdout']:
            print("\nFull history:")
            print(result['stdout'])
    else:
        print("❌ Failed to get migration history")
        print(f"Error: {result['stderr']}")
        sys.exit(1)


def handle_current(manager: MigrationManager):
    """Handle current command"""
    print("Current database revision:")
    
    result = manager.get_current_revision()
    
    if result['success']:
        print(f"📍 {result.get('current_revision', 'Unknown')}")
        if result['stdout']:
            print(result['stdout'])
    else:
        print("❌ Failed to get current revision")
        print(f"Error: {result['stderr']}")
        sys.exit(1)


def handle_validate(manager: MigrationManager):
    """Handle validate command"""
    print("Validating migration files...")
    
    result = manager.validate_migration_files()
    
    if result['success']:
        print(f"📊 Checked {result['files_checked']} migration files")
        
        if result['all_valid']:
            print("✅ All migration files are valid!")
        else:
            print("❌ Some migration files have issues:")
            
        for file_result in result['validation_results']:
            status = '✅' if file_result.get('valid', False) else '❌'
            print(f"  {status} {file_result['file']}")
            
            if 'error' in file_result:
                print(f"    Error: {file_result['error']}")
            elif not file_result.get('valid', False):
                issues = []
                if not file_result.get('has_upgrade', False):
                    issues.append('missing upgrade function')
                if not file_result.get('has_downgrade', False):
                    issues.append('missing downgrade function')
                if not file_result.get('has_revision', False):
                    issues.append('missing revision identifier')
                
                if issues:
                    print(f"    Issues: {', '.join(issues)}")
    else:
        print("❌ Failed to validate migration files")
        print(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


def handle_reset(manager: MigrationManager, args):
    """Handle reset command"""
    if not args.confirm:
        print("❌ Database reset requires --confirm flag")
        print("⚠️  WARNING: This will destroy ALL data in the database!")
        print("Usage: python manage_db.py reset --confirm")
        return
    
    print("⚠️  WARNING: Resetting database - this will destroy ALL data!")
    print("This operation will:")
    print("  1. Downgrade database to base (empty)")
    print("  2. Upgrade database to latest schema")
    print("  3. All existing data will be LOST")
    
    confirm = input("Type 'RESET' to continue: ")
    if confirm != 'RESET':
        print("Reset cancelled.")
        return
    
    print("Resetting database...")
    result = manager.reset_database()
    
    if result['success']:
        print("✅ Database reset successfully!")
        print(result['message'])
    else:
        print("❌ Failed to reset database")
        print(f"Error: {result.get('stderr', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()