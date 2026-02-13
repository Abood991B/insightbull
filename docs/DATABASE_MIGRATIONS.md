# Database Migration Management

This document provides comprehensive information about managing database migrations in the InsightBull backend.

## Overview

The project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations. Alembic provides versioning and migration capabilities for SQLAlchemy database schemas.

This implementation follows the **FYP's 5-layer architecture** with a clean, academic-focused approach:
- **Simple Repository Pattern** for data access abstraction
- **Basic migration management** without enterprise-level complexity
- **Clean separation of concerns** across the layered architecture

> **Note**: This is a simplified, FYP-appropriate implementation that focuses on core functionality without over-engineering.

## Quick Start

### Basic Commands

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Check migration status
python manage_db.py status

# Create a new migration
python manage_db.py migrate "Description of changes"

# Apply migrations
python manage_db.py upgrade

# View migration history
python manage_db.py history
```

## Migration Management CLI

The `manage_db.py` script provides a convenient command-line interface for common migration tasks:

### Available Commands

#### `migrate` - Create New Migration
```bash
# Create migration with autogenerate (detects model changes)
python manage_db.py migrate "Add user preferences table"

# Create empty migration (manual changes)
python manage_db.py migrate "Custom data migration" --no-autogenerate
```

#### `upgrade` - Apply Migrations
```bash
# Upgrade to latest (head)
python manage_db.py upgrade

# Upgrade to specific revision
python manage_db.py upgrade 8653cc238299
```

#### `downgrade` - Rollback Migrations
```bash
# Downgrade to specific revision
python manage_db.py downgrade 8653cc238299

# Downgrade to base (empty database)
python manage_db.py downgrade base
```

#### `status` - Check Migration Status
```bash
python manage_db.py status
```

#### `history` - View Migration History
```bash
python manage_db.py history
```

#### `current` - Show Current Revision
```bash
python manage_db.py current
```

#### `validate` - Validate Migration Files
```bash
python manage_db.py validate
```

#### `reset` - Reset Database (DANGER!)
```bash
# Reset database (destroys all data!)
python manage_db.py reset --confirm
```

## Direct Alembic Commands

You can also use Alembic directly:

```bash
# Initialize Alembic (already done)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1

# Show current revision
alembic current

# Show history
alembic history

# Show heads
alembic heads
```

## File Structure

```
backend/
├── alembic/                    # Alembic migration directory
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment configuration
│   ├── script.py.mako         # Migration template
│   └── README                 # Alembic documentation
├── alembic.ini               # Alembic configuration
├── manage_db.py              # Database management CLI
└── app/
    ├── data_access/
    │   ├── models/           # SQLAlchemy models
    │   └── repositories/     # Repository pattern implementation
    └── infrastructure/
        └── database/
            ├── connection.py        # Database connection management
            └── migration_manager.py # Migration utility classes
```

## Configuration

### Database URL

The database URL is configured in `alembic.ini` and can be overridden with the `DATABASE_URL` environment variable:

```ini
# alembic.ini
sqlalchemy.url = sqlite:///./data/insight_stock.db
```

### Environment Variables

Create a `.env` file to override database settings:

```bash
DATABASE_URL=sqlite:///./data/insight_stock.db
# or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/insight_stock_db
```

## Migration Best Practices

### 1. Review Generated Migrations

Always review auto-generated migrations before applying them:

```bash
# Create migration
python manage_db.py migrate "Add new column"

# Review the generated file in alembic/versions/
# Edit if necessary

# Apply migration
python manage_db.py upgrade
```

### 2. Test Migrations

Test both upgrade and downgrade:

```bash
# Apply migration
python manage_db.py upgrade

# Test rollback
python manage_db.py downgrade -1

# Re-apply
python manage_db.py upgrade
```

### 3. Backup Before Major Changes

Always backup your database before major schema changes:

```bash
# For SQLite
cp data/insight_stock.db data/insight_stock_backup.db

# For PostgreSQL
pg_dump insight_stock_db > backup.sql
```

### 4. Use Descriptive Messages

Use clear, descriptive migration messages:

```bash
# Good
python manage_db.py migrate "Add sentiment_confidence column to sentiment_data table"

# Bad
python manage_db.py migrate "Update"
```

### 5. Handle Data Migrations

For complex data migrations, create custom migration scripts:

```python
# In migration file
def upgrade():
    # Schema changes
    op.add_column('stocks', sa.Column('market_cap', sa.BigInteger()))
    
    # Data migration
    connection = op.get_bind()
    connection.execute(
        "UPDATE stocks SET market_cap = 0 WHERE market_cap IS NULL"
    )
    
    # Make column non-nullable
    op.alter_column('stocks', 'market_cap', nullable=False)
```

## Troubleshooting

### Common Issues

#### 1. Migration Conflicts
```bash
# Multiple heads detected
alembic merge -m "Merge migrations" head1 head2
```

#### 2. Invalid Migration State
```bash
# Check current state
python manage_db.py status

# Validate migration files
python manage_db.py validate

# Reset if necessary (DANGER!)
python manage_db.py reset --confirm
```

#### 3. Database Connection Issues
```bash
# Check database URL
echo $DATABASE_URL

# Verify database file exists (for SQLite)
ls -la data/insight_stock.db

# Test connection
python -c "from app.infrastructure.database.connection import get_database_url; print(get_database_url())"
```

#### 4. Import Errors in Migrations
Ensure all models are imported in `alembic/env.py`:

```python
# Add any new models here
from app.data_access.models import Base, Stock, SentimentData, StockPrice
```

### Recovery Procedures

#### 1. Corrupted Migration State
```bash
# Stamp current database with correct revision
alembic stamp head

# Or stamp with specific revision
alembic stamp 8653cc238299
```

#### 2. Lost Migration Files
```bash
# Recreate missing migration
alembic revision --autogenerate -m "Recreate schema"

# Review and edit the generated migration
# Apply the migration
python manage_db.py upgrade
```

## Development Workflow

### Adding New Models

1. Create or modify models in `app/data_access/models/`
2. Create migration:
   ```bash
   python manage_db.py migrate "Add UserPreferences model"
   ```
3. Review generated migration file
4. Apply migration:
   ```bash
   python manage_db.py upgrade
   ```
5. Test the changes
6. Commit both model changes and migration file

### Modifying Existing Models

1. Modify model in `app/data_access/models/`
2. Create migration:
   ```bash
   python manage_db.py migrate "Add email field to User model"
   ```
3. Review migration for data safety
4. Apply migration:
   ```bash
   python manage_db.py upgrade
   ```
5. Test thoroughly
6. Commit changes

## Production Considerations

### Deployment Process

1. **Backup database** before deployment
2. **Test migrations** on staging environment
3. **Apply migrations** during deployment:
   ```bash
   python manage_db.py upgrade
   ```
4. **Verify application** functionality
5. **Rollback if necessary**:
   ```bash
   python manage_db.py downgrade previous_revision
   ```

### Zero-Downtime Migrations

For production systems requiring zero downtime:

1. **Backward-compatible changes first**
2. **Deploy application code**
3. **Remove deprecated code** in subsequent release

Example:
```python
# Step 1: Add new column (nullable)
op.add_column('stocks', sa.Column('new_field', sa.String(100)))

# Step 2: (Next release) Populate data and make non-nullable
# Step 3: (Later release) Remove old column if needed
```

## Integration with Application

The migration system integrates with the application through the **5-layer architecture**:

1. **Data Access Layer** (`app/data_access/`):
   - Database models in `models/`
   - Repository pattern implementation in `repositories/`

2. **Infrastructure Layer** (`app/infrastructure/database/`):
   - Database connection management
   - Migration utilities

### Repository Pattern Integration

The migration system works seamlessly with the repository pattern:

```python
from app.data_access.repositories import StockRepository, SentimentDataRepository
from app.infrastructure.database.connection import get_async_session

# After running migrations, repositories work with updated schema
async with get_async_session() as session:
    stock_repo = StockRepository(session)
    sentiment_repo = SentimentDataRepository(session)
    
    # Repository methods work with migrated database structure
    stocks = await stock_repo.get_all()
```

### Programmatic Usage

```python
from app.infrastructure.database.migration_manager import MigrationManager

# Create manager
manager = MigrationManager()

# Check status
status = manager.check_migration_status()
if status['needs_upgrade']:
    print("Database needs upgrade!")

# Apply migrations programmatically
result = manager.upgrade_database()
if result['success']:
    print("Database upgraded successfully!")
```

## Getting Help

- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Project Issues**: Create issue in repository

---

For additional help or questions, refer to the project documentation or create an issue in the repository.