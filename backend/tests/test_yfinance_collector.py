"""
YFinance Collector Test Suite
=============================

Comprehensive tests for the YFinance collector integration.
Tests include:
- Connection validation
- News data collection
- Data parsing and formatting
- Error handling
- Logging system integration
- Multi-symbol batch collection

Usage:
    pytest tests/test_yfinance_collector.py -v
    # Or run directly:
    python tests/test_yfinance_collector.py

Requirements:
    - yfinance >= 0.2.66
"""

import asyncio
import sys
import os
import time
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.timezone import utc_now
from app.infrastructure.log_system import get_logger


class TestYFinanceCollector:
    """Test suite for YFinance collector functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures with logging"""
        self.logger = get_logger()
        self.logger.info(
            "Starting YFinance collector test suite",
            extra={"operation": "test_setup", "component": "yfinance_collector"}
        )
        
        # Test symbols - major tech stocks
        self.test_symbols = ["AAPL", "MSFT", "NVDA"]
        
        yield
        
        self.logger.info(
            "YFinance collector test suite completed",
            extra={"operation": "test_teardown", "component": "yfinance_collector"}
        )
    
    def test_yfinance_package_installed(self):
        """Test that yfinance package is installed and importable"""
        self.logger.info(
            "Testing yfinance package installation",
            extra={"operation": "test_import", "component": "yfinance_collector"}
        )
        
        try:
            import yfinance as yf
            version = yf.__version__
            
            self.logger.info(
                f"yfinance package found: version {version}",
                extra={"operation": "test_import", "version": version, "status": "success"}
            )
            
            # Verify minimum version (0.2.66 required for news API)
            version_parts = [int(x) for x in version.split('.')[:3]]
            min_version = [0, 2, 66]
            
            is_valid_version = (
                version_parts[0] > min_version[0] or
                (version_parts[0] == min_version[0] and version_parts[1] > min_version[1]) or
                (version_parts[0] == min_version[0] and version_parts[1] == min_version[1] and version_parts[2] >= min_version[2])
            )
            
            assert is_valid_version, f"yfinance version {version} is below minimum required 0.2.66"
            
        except ImportError as e:
            self.logger.error(
                f"yfinance package not installed: {e}",
                extra={"operation": "test_import", "status": "failed", "error": str(e)}
            )
            pytest.fail(f"yfinance package not installed: {e}")
    
    def test_collector_import(self):
        """Test that YFinanceCollector can be imported"""
        self.logger.info(
            "Testing YFinanceCollector import",
            extra={"operation": "test_collector_import", "component": "yfinance_collector"}
        )
        
        try:
            from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
            from app.infrastructure.collectors.base_collector import DataSource
            
            # Verify YFINANCE is in DataSource enum
            assert hasattr(DataSource, 'YFINANCE'), "DataSource enum missing YFINANCE"
            
            self.logger.info(
                "YFinanceCollector imported successfully",
                extra={"operation": "test_collector_import", "status": "success"}
            )
            
        except ImportError as e:
            self.logger.error(
                f"Failed to import YFinanceCollector: {e}",
                extra={"operation": "test_collector_import", "status": "failed", "error": str(e)}
            )
            pytest.fail(f"Failed to import YFinanceCollector: {e}")
    
    def test_collector_initialization(self):
        """Test YFinanceCollector instantiation"""
        self.logger.info(
            "Testing YFinanceCollector initialization",
            extra={"operation": "test_init", "component": "yfinance_collector"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        
        collector = YFinanceCollector()
        
        assert collector is not None, "Collector initialization returned None"
        assert collector.source.value == "yfinance", f"Unexpected source: {collector.source.value}"
        
        self.logger.info(
            "YFinanceCollector initialized successfully",
            extra={
                "operation": "test_init",
                "status": "success",
                "source": collector.source.value
            }
        )
    
    @pytest.mark.asyncio
    async def test_connection_validation(self):
        """Test YFinance connection validation"""
        self.logger.info(
            "Testing YFinance connection validation",
            extra={"operation": "test_connection", "component": "yfinance_collector"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        
        collector = YFinanceCollector()
        
        start_time = time.time()
        is_valid = await collector.validate_connection()
        elapsed = time.time() - start_time
        
        self.logger.info(
            f"Connection validation result: {is_valid}",
            extra={
                "operation": "test_connection",
                "status": "success" if is_valid else "failed",
                "elapsed_seconds": round(elapsed, 2)
            }
        )
        
        assert is_valid, "YFinance connection validation failed"
    
    @pytest.mark.asyncio
    async def test_single_symbol_collection(self):
        """Test collecting news for a single symbol"""
        self.logger.info(
            "Testing single symbol news collection",
            extra={"operation": "test_single_symbol", "component": "yfinance_collector", "symbol": "AAPL"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        collector = YFinanceCollector()
        config = CollectionConfig(
            symbols=["AAPL"],
            date_range=DateRange.last_days(7),
            max_items_per_symbol=10
        )
        
        start_time = time.time()
        result = await collector.collect_data(config)
        elapsed = time.time() - start_time
        
        self.logger.info(
            f"Collected {result.items_collected} items for AAPL",
            extra={
                "operation": "test_single_symbol",
                "symbol": "AAPL",
                "items_collected": result.items_collected,
                "elapsed_seconds": round(elapsed, 2),
                "status": "success" if result.items_collected > 0 else "no_data"
            }
        )
        
        assert result is not None, "Collection returned None"
        # Note: Some symbols may have no news, so we just verify the result structure
        assert hasattr(result, 'data'), "Result missing 'data' attribute"
        assert hasattr(result, 'source'), "Result missing 'source' attribute"
    
    @pytest.mark.asyncio
    async def test_multi_symbol_collection(self):
        """Test collecting news for multiple symbols"""
        symbols = self.test_symbols
        
        self.logger.info(
            f"Testing multi-symbol news collection",
            extra={
                "operation": "test_multi_symbol",
                "component": "yfinance_collector",
                "symbols": symbols,
                "symbol_count": len(symbols)
            }
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        collector = YFinanceCollector()
        config = CollectionConfig(
            symbols=symbols,
            date_range=DateRange.last_days(7),
            max_items_per_symbol=5
        )
        
        start_time = time.time()
        result = await collector.collect_data(config)
        elapsed = time.time() - start_time
        
        self.logger.info(
            f"Collected {result.items_collected} total items for {len(symbols)} symbols",
            extra={
                "operation": "test_multi_symbol",
                "symbols": symbols,
                "total_items": result.items_collected,
                "elapsed_seconds": round(elapsed, 2),
                "items_per_second": round(result.items_collected / elapsed, 2) if elapsed > 0 else 0
            }
        )
        
        assert result is not None, "Collection returned None"
        # Log results
        self.logger.info(
            f"Collection completed successfully",
            extra={"operation": "test_multi_symbol", "success": result.success}
        )
    
    @pytest.mark.asyncio
    async def test_data_item_structure(self):
        """Test that collected items have proper structure"""
        self.logger.info(
            "Testing data item structure",
            extra={"operation": "test_item_structure", "component": "yfinance_collector"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        collector = YFinanceCollector()
        config = CollectionConfig(
            symbols=["MSFT"],
            date_range=DateRange.last_days(7),
            max_items_per_symbol=5
        )
        
        result = await collector.collect_data(config)
        
        if result.items_collected == 0:
            self.logger.warning(
                "No items collected - cannot verify structure",
                extra={"operation": "test_item_structure", "status": "skipped"}
            )
            pytest.skip("No news items available for MSFT to verify structure")
        
        # Verify structure of first item
        item = result.data[0]
        
        required_fields = ['text', 'url', 'source', 'stock_symbol']
        
        for field in required_fields:
            assert hasattr(item, field), f"Item missing required field: {field}"
        
        self.logger.info(
            f"Data item structure validated",
            extra={
                "operation": "test_item_structure",
                "status": "success",
                "sample_source": item.source,
                "has_text": bool(item.text)
            }
        )
    
    @pytest.mark.asyncio
    async def test_no_api_key_required(self):
        """Verify YFinance works without any API key"""
        self.logger.info(
            "Testing that YFinance works without API key",
            extra={"operation": "test_no_api_key", "component": "yfinance_collector"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        
        # Create collector - should not require any API key
        collector = YFinanceCollector()
        
        # Verify it can collect without errors
        is_valid = await collector.validate_connection()
        
        self.logger.info(
            f"YFinance works without API key: {is_valid}",
            extra={
                "operation": "test_no_api_key",
                "status": "success" if is_valid else "failed",
                "requires_api_key": False
            }
        )
        
        assert is_valid, "YFinance should work without any API key"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_symbol(self):
        """Test error handling for invalid symbols"""
        self.logger.info(
            "Testing error handling for invalid symbol",
            extra={"operation": "test_error_handling", "component": "yfinance_collector"}
        )
        
        from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        collector = YFinanceCollector()
        config = CollectionConfig(
            symbols=["INVALID_SYMBOL_XYZ123"],
            date_range=DateRange.last_days(7),
            max_items_per_symbol=5
        )
        
        # Should not raise exception, just return empty/error result
        result = await collector.collect_data(config)
        
        self.logger.info(
            f"Invalid symbol handled gracefully",
            extra={
                "operation": "test_error_handling",
                "status": "success",
                "items_collected": result.items_collected if result else 0
            }
        )
        
        assert result is not None, "Collector should return a result even for invalid symbols"


class TestYFinanceIntegration:
    """Integration tests for YFinance with the pipeline"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup integration test fixtures"""
        self.logger = get_logger()
        self.logger.info(
            "Starting YFinance integration tests",
            extra={"operation": "integration_test_setup", "component": "yfinance_collector"}
        )
        yield
    
    def test_collector_in_exports(self):
        """Test YFinanceCollector is properly exported from collectors module"""
        from app.infrastructure.collectors import YFinanceCollector
        
        assert YFinanceCollector is not None
        
        self.logger.info(
            "YFinanceCollector properly exported from collectors module",
            extra={"operation": "test_exports", "status": "success"}
        )
    
    def test_data_source_enum(self):
        """Test YFINANCE exists in DataSource enum"""
        from app.infrastructure.collectors.base_collector import DataSource
        
        assert hasattr(DataSource, 'YFINANCE'), "YFINANCE not in DataSource enum"
        assert DataSource.YFINANCE.value == 'yfinance', f"Unexpected value: {DataSource.YFINANCE.value}"
        
        self.logger.info(
            "YFINANCE properly defined in DataSource enum",
            extra={"operation": "test_enum", "status": "success", "value": DataSource.YFINANCE.value}
        )
    
    def test_collector_settings(self):
        """Test YFinance has proper collector settings"""
        from app.infrastructure.collectors.collector_settings import get_collector_settings
        
        settings = get_collector_settings('yfinance')
        
        assert settings is not None, "No settings found for yfinance"
        # daily_quota=None means unlimited (no quota limit)
        assert settings.daily_quota is None or settings.daily_quota == 0, "YFinance should have unlimited quota"
        assert settings.requires_api_key == False, "YFinance should not require API key"
        
        self.logger.info(
            f"YFinance collector settings verified",
            extra={
                "operation": "test_settings",
                "status": "success",
                "daily_quota": settings.daily_quota,
                "requires_api_key": settings.requires_api_key
            }
        )
    
    def test_pipeline_includes_yfinance(self):
        """Test pipeline can import YFinanceCollector"""
        self.logger.info(
            "Testing pipeline YFinance integration",
            extra={"operation": "test_pipeline_import", "component": "yfinance_collector"}
        )
        
        try:
            from app.business.pipeline import DataPipeline
            from app.infrastructure.collectors.yfinance_collector import YFinanceCollector
            
            # Verify YFinanceCollector can be used with pipeline
            self.logger.info(
                "Pipeline can work with YFinanceCollector",
                extra={"operation": "test_pipeline_import", "status": "success"}
            )
            
        except ImportError as e:
            self.logger.error(
                f"Pipeline import failed: {e}",
                extra={"operation": "test_pipeline_import", "status": "failed", "error": str(e)}
            )
            pytest.fail(f"Pipeline import failed: {e}")


# Direct execution support
def run_tests():
    """Run tests directly without pytest"""
    logger = get_logger()
    logger.info("=" * 60)
    logger.info("YFinance Collector Test Suite - Direct Execution")
    logger.info("=" * 60)
    
    async def run_async_tests():
        suite = TestYFinanceCollector()
        suite.setup()
        
        tests = [
            ("Package Installation", suite.test_yfinance_package_installed),
            ("Collector Import", suite.test_collector_import),
            ("Collector Initialization", suite.test_collector_initialization),
            ("Connection Validation", suite.test_connection_validation),
            ("Single Symbol Collection", suite.test_single_symbol_collection),
            ("Multi Symbol Collection", suite.test_multi_symbol_collection),
            ("No API Key Required", suite.test_no_api_key_required),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                logger.info(f"\n{'='*40}")
                logger.info(f"Running: {name}")
                logger.info(f"{'='*40}")
                
                if asyncio.iscoroutinefunction(test_func):
                    await test_func()
                else:
                    test_func()
                    
                logger.info(f"PASSED: {name}")
                passed += 1
                
            except Exception as e:
                logger.error(f"FAILED: {name} - {e}")
                failed += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Test Results: {passed} passed, {failed} failed")
        logger.info(f"{'='*60}")
        
        return passed, failed
    
    return asyncio.run(run_async_tests())


if __name__ == "__main__":
    run_tests()
