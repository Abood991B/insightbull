"""
Database Migration Management Utility

Provides convenient functions for managing database migrations with Alembic.
This module simplifies common migration operations and provides proper error handling.
"""

import os
import subprocess
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manager class for handling Alembic database migrations
    """
    
    def __init__(self, backend_root: str = None):
        """
        Initialize the migration manager
        
        Args:
            backend_root: Path to the backend root directory
        """
        if backend_root is None:
            # Assume we're in the backend directory or find it
            current_dir = Path(__file__).parent
            while current_dir.name != 'backend' and current_dir.parent != current_dir:
                current_dir = current_dir.parent
            backend_root = str(current_dir)
        
        self.backend_root = Path(backend_root)
        self.alembic_cfg = self.backend_root / 'alembic.ini'
        self.venv_python = self.backend_root / 'venv' / 'Scripts' / 'python.exe'
        
        if not self.alembic_cfg.exists():
            raise FileNotFoundError(f"Alembic config not found at {self.alembic_cfg}")
    
    def _run_alembic_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Run an Alembic command and return the result
        
        Args:
            command: List of command parts (e.g., ['revision', '--autogenerate'])
            
        Returns:
            Dictionary with success status, output, and error information
        """
        try:
            # Build the full command
            full_command = [
                str(self.venv_python), '-m', 'alembic'
            ] + command
            
            logger.info(f"Running command: {' '.join(full_command)}")
            
            # Run the command in the backend directory
            result = subprocess.run(
                full_command,
                cwd=str(self.backend_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(full_command)
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Migration command timed out")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out after 5 minutes',
                'command': ' '.join(full_command)
            }
        except Exception as e:
            logger.error(f"Error running migration command: {str(e)}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e),
                'command': ' '.join(full_command)
            }
    
    def create_migration(self, message: str, autogenerate: bool = True) -> Dict[str, Any]:
        """
        Create a new migration
        
        Args:
            message: Migration message/description
            autogenerate: Whether to use autogenerate to detect model changes
            
        Returns:
            Result dictionary with success status and details
        """
        command = ['revision']
        if autogenerate:
            command.append('--autogenerate')
        command.extend(['-m', message])
        
        result = self._run_alembic_command(command)
        
        if result['success']:
            logger.info(f"Successfully created migration: {message}")
        else:
            logger.error(f"Failed to create migration: {result['stderr']}")
        
        return result
    
    def upgrade_database(self, revision: str = 'head') -> Dict[str, Any]:
        """
        Upgrade database to a specific revision
        
        Args:
            revision: Target revision (default: 'head' for latest)
            
        Returns:
            Result dictionary with success status and details
        """
        result = self._run_alembic_command(['upgrade', revision])
        
        if result['success']:
            logger.info(f"Successfully upgraded database to {revision}")
        else:
            logger.error(f"Failed to upgrade database: {result['stderr']}")
        
        return result
    
    def downgrade_database(self, revision: str) -> Dict[str, Any]:
        """
        Downgrade database to a specific revision
        
        Args:
            revision: Target revision to downgrade to
            
        Returns:
            Result dictionary with success status and details
        """
        result = self._run_alembic_command(['downgrade', revision])
        
        if result['success']:
            logger.info(f"Successfully downgraded database to {revision}")
        else:
            logger.error(f"Failed to downgrade database: {result['stderr']}")
        
        return result
    
    def get_current_revision(self) -> Dict[str, Any]:
        """
        Get the current database revision
        
        Returns:
            Result dictionary with current revision information
        """
        result = self._run_alembic_command(['current'])
        
        if result['success']:
            # Parse the output to extract revision
            output_lines = result['stdout'].strip().split('\n')
            for line in output_lines:
                if 'Current revision' in line or line.strip().startswith('Rev:'):
                    result['current_revision'] = line.strip()
                    break
            else:
                result['current_revision'] = 'No current revision found'
        
        return result
    
    def get_migration_history(self) -> Dict[str, Any]:
        """
        Get the migration history
        
        Returns:
            Result dictionary with migration history
        """
        result = self._run_alembic_command(['history'])
        
        if result['success']:
            # Parse history into a more structured format
            history_lines = result['stdout'].strip().split('\n')
            migrations = []
            
            for line in history_lines:
                line = line.strip()
                if line and not line.startswith('Rev:') and '->' in line:
                    migrations.append(line)
            
            result['migrations'] = migrations
        
        return result
    
    def check_migration_status(self) -> Dict[str, Any]:
        """
        Check if there are pending migrations
        
        Returns:
            Dictionary with migration status information
        """
        current_result = self.get_current_revision()
        if not current_result['success']:
            return current_result
        
        # Check if we're at head
        heads_result = self._run_alembic_command(['heads'])
        if not heads_result['success']:
            return heads_result
        
        status = {
            'success': True,
            'current_revision': current_result.get('current_revision', 'Unknown'),
            'head_revisions': heads_result['stdout'].strip().split('\n'),
            'needs_upgrade': False
        }
        
        # Simple check if current revision matches head
        # In a real implementation, you'd want more sophisticated checking
        current_output = current_result['stdout']
        heads_output = heads_result['stdout']
        
        if 'head' not in current_output.lower() and heads_output.strip():
            status['needs_upgrade'] = True
        
        return status
    
    def reset_database(self) -> Dict[str, Any]:
        """
        Reset database by downgrading to base and upgrading to head
        WARNING: This will destroy all data!
        
        Returns:
            Result dictionary with reset operation status
        """
        logger.warning("Resetting database - this will destroy all data!")
        
        # Downgrade to base
        downgrade_result = self.downgrade_database('base')
        if not downgrade_result['success']:
            return downgrade_result
        
        # Upgrade to head
        upgrade_result = self.upgrade_database('head')
        if not upgrade_result['success']:
            return upgrade_result
        
        return {
            'success': True,
            'message': 'Database reset successfully',
            'downgrade_output': downgrade_result['stdout'],
            'upgrade_output': upgrade_result['stdout']
        }
    
    def validate_migration_files(self) -> Dict[str, Any]:
        """
        Validate that migration files are properly structured
        
        Returns:
            Validation result dictionary
        """
        versions_dir = self.backend_root / 'alembic' / 'versions'
        
        if not versions_dir.exists():
            return {
                'success': False,
                'error': 'Versions directory not found'
            }
        
        migration_files = list(versions_dir.glob('*.py'))
        validation_results = []
        
        for migration_file in migration_files:
            try:
                with open(migration_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic validation
                has_upgrade = 'def upgrade()' in content
                has_downgrade = 'def downgrade()' in content
                has_revision = 'revision:' in content
                
                validation_results.append({
                    'file': migration_file.name,
                    'has_upgrade': has_upgrade,
                    'has_downgrade': has_downgrade,
                    'has_revision': has_revision,
                    'valid': has_upgrade and has_downgrade and has_revision
                })
                
            except Exception as e:
                validation_results.append({
                    'file': migration_file.name,
                    'error': str(e),
                    'valid': False
                })
        
        all_valid = all(result.get('valid', False) for result in validation_results)
        
        return {
            'success': True,
            'all_valid': all_valid,
            'files_checked': len(validation_results),
            'validation_results': validation_results
        }


# Convenience functions for common operations
def create_migration(message: str, autogenerate: bool = True) -> bool:
    """
    Convenience function to create a new migration
    
    Args:
        message: Migration message
        autogenerate: Whether to use autogenerate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = MigrationManager()
        result = manager.create_migration(message, autogenerate)
        return result['success']
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        return False


def upgrade_database(revision: str = 'head') -> bool:
    """
    Convenience function to upgrade database
    
    Args:
        revision: Target revision
        
    Returns:
        True if successful, False otherwise
    """
    try:
        manager = MigrationManager()
        result = manager.upgrade_database(revision)
        return result['success']
    except Exception as e:
        logger.error(f"Error upgrading database: {str(e)}")
        return False


def get_migration_status() -> Optional[Dict[str, Any]]:
    """
    Convenience function to get migration status
    
    Returns:
        Migration status dictionary or None if error
    """
    try:
        manager = MigrationManager()
        return manager.check_migration_status()
    except Exception as e:
        logger.error(f"Error checking migration status: {str(e)}")
        return None