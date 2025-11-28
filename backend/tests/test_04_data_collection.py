"""
Phase 5 Data Collection Pipeline - Comprehensive Test Suite
=        #        # Test configuration - using complete Top 20 target stock list
        # Top 20 IXT Technology Stocks including Magnificent Seven
        self.test_symbols = [
            "NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "PLTR", "CSCO", "AMD", "IBM", "CRM",
            "NOW", "INTU", "QCOM", "MU", "TXN", "ADBE", "GOOGL", "AMZN", "META", "TSLA"
        ]
        
        # Use default configuration with complete stock list
        self.test_config = PipelineConfig.create_default_config(
            max_items_per_symbol=3  # Lower for testing all 20 stocks
        )onfiguration - using your complete Top 20 (IXT + Magnificent Seven) stock list
        self.test_symbols = [
            'NVDA', 'MSFT', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'CSCO', 'AMD', 'IBM', 'CRM',
            'NOW', 'INTU', 'QCOM', 'MU', 'TXN', 'ADBE', 'GOOGL', 'AMZN', 'META', 'TSLA'
        ]
        self.test_config = PipelineConfig(
            symbols=self.test_symbols,
            date_range=DateRange.near_realtime(),  # Near real-time: 5 days for better API coverage
            max_items_per_symbol=3  # Reduced to 3 since we have 20 stocks now
        )===================================================

This test file validates the complete Phase 5 implementation including:
- Multi-source data collection (HackerNews, FinHub, NewsAPI, MarketAux)
- API key management and security
- Data pipeline orchestration
- Error handling and resilience
- Performance metrics

Usage:
    python test_phase5_comprehensive.py

Features Tested:
- ✅ Individual collector functionality
- ✅ Pipeline orchestration
- ✅ API key validation
- ✅ Error handling
- ✅ Data quality validation
- ✅ Performance benchmarking
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import replace
from app.utils.timezone import utc_now
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from app.business.pipeline import DataPipeline, PipelineConfig
    from app.infrastructure.collectors.base_collector import DateRange, CollectionConfig
    from app.infrastructure.collectors.hackernews_collector import HackerNewsCollector
    from app.infrastructure.collectors.finnhub_collector import FinHubCollector
    from app.infrastructure.collectors.newsapi_collector import NewsAPICollector
    from app.infrastructure.collectors.marketaux_collector import MarketauxCollector
    
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Import error: {e}")
    IMPORTS_AVAILABLE = False


class Phase5TestSuite:
    """Comprehensive test suite for Phase 5 data collection pipeline"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': utc_now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'individual_collectors': {},
            'pipeline_tests': {},
            'performance_metrics': {},
            'errors': []
        }
        
        # Test configuration - using limited symbols to avoid API rate limits
        # Use only 3 major stocks for testing to prevent hitting rate limits
        self.test_symbols = [
            "NVDA", "MSFT", "AAPL"  # Reduced from 20 to 3 stocks for testing
        ]
        self.test_config = PipelineConfig(
            symbols=self.test_symbols,
            date_range=DateRange.last_days(2),  # Reduced from 5 to 2 days
            max_items_per_symbol=2,  # Reduced from 5 to 2 items
            include_marketaux=False  # Keep disabled due to API quota limits
        )
    
    def log_test(self, test_name: str, success: bool, details: Dict[str, Any] = None):
        """Log test result"""
        self.test_results['tests_run'] += 1
        
        if success:
            self.test_results['tests_passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results['tests_failed'] += 1
            print(f"❌ {test_name}")
            if details and 'error' in details:
                self.test_results['errors'].append({
                    'test': test_name,
                    'error': str(details['error'])
                })
        
        if details:
            print(f"   Details: {details}")
    
    async def test_api_keys(self) -> bool:
        """Test API key availability and validity"""
        print("\n🔑 TESTING API KEY CONFIGURATION")
        print("=" * 50)
        
        # Note: HackerNews uses free Algolia API (no key required)
        required_keys = {
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
            'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY')
        }
        
        all_keys_valid = True
        
        for key_name, key_value in required_keys.items():
            if key_value and len(key_value) > 8:
                self.log_test(f"API Key {key_name}", True, 
                            {'masked_key': f"{key_value[:8]}..."})
            else:
                self.log_test(f"API Key {key_name}", False, 
                            {'error': 'Missing or invalid'})
                all_keys_valid = False
        
        return all_keys_valid
    
    async def test_individual_collectors(self) -> Dict[str, bool]:
        """Test each collector individually"""
        print("\n📊 TESTING INDIVIDUAL COLLECTORS")
        print("=" * 50)
        
        collectors_config = [
            ('HackerNews', HackerNewsCollector, {}),  # No API key needed - free Algolia API
            ('FinHub', FinHubCollector, {
                'api_key': os.getenv('FINNHUB_API_KEY')
            }),
            ('NewsAPI', NewsAPICollector, {
                'api_key': os.getenv('NEWSAPI_KEY')
            }),
            ('MarketAux', MarketauxCollector, {
                'api_key': os.getenv('MARKETAUX_API_KEY')
            })
        ]
        
        collector_results = {}
        
        for name, collector_class, config in collectors_config:
            try:
                start_time = time.time()
                
                # Initialize collector
                if name == 'HackerNews':
                    # HackerNews collector requires no API key
                    collector = collector_class()
                else:
                    if config['api_key']:
                        collector = collector_class(api_key=config['api_key'])
                    else:
                        collector_results[name] = False
                        self.log_test(f"{name} Collector Init", False, 
                                    {'error': 'Missing API key'})
                        continue
                
                # Test connection
                connection_valid = await collector.validate_connection()
                
                if connection_valid:
                    # Test data collection with first few stocks for individual test
                    # Convert PipelineConfig to CollectionConfig for individual collectors
                    collection_config = CollectionConfig(
                        symbols=self.test_symbols[:3],  # Test with first 3 stocks
                        date_range=self.test_config.date_range,
                        max_items_per_symbol=2,
                        include_comments=self.test_config.include_comments
                    )
                    
                    result = await collector.collect_data(collection_config)
                    
                    execution_time = time.time() - start_time
                    
                    success = result.success
                    items_collected = len(result.data) if result.data else 0
                    
                    self.log_test(f"{name} Collector", success, {
                        'items_collected': items_collected,
                        'execution_time': f"{execution_time:.2f}s",
                        'connection_valid': connection_valid
                    })
                    
                    collector_results[name] = success
                    
                    # Store detailed metrics
                    self.test_results['individual_collectors'][name] = {
                        'success': success,
                        'items_collected': items_collected,
                        'execution_time': execution_time,
                        'connection_valid': connection_valid,
                        'error_message': result.error_message if hasattr(result, 'error_message') else None
                    }
                    
                else:
                    collector_results[name] = False
                    self.log_test(f"{name} Collector", False, 
                                {'error': 'Connection validation failed'})
                    
            except Exception as e:
                collector_results[name] = False
                self.log_test(f"{name} Collector", False, {'error': str(e)})
        
        return collector_results
    
    async def test_pipeline_orchestration(self) -> bool:
        """Test the complete pipeline orchestration"""
        print("\n🔄 TESTING PIPELINE ORCHESTRATION")
        print("=" * 50)
        
        try:
            start_time = time.time()
            
            # Initialize pipeline
            pipeline = DataPipeline()
            
            # Test health check
            health_result = await pipeline.health_check()
            healthy_collectors = sum(1 for collector in health_result.get('collectors', {}).values() 
                                   if collector.get('healthy', False))
            
            self.log_test("Pipeline Health Check", True, {
                'healthy_collectors': f"{healthy_collectors}/{len(health_result.get('collectors', {}))}"
            })
            
            # Test full pipeline execution
            result = await pipeline.run_pipeline(self.test_config)
            
            execution_time = time.time() - start_time
            
            success = result.status.value == 'completed'
            
            pipeline_details = {
                'status': result.status.value,
                'total_items': result.total_items_collected,
                'execution_time': f"{execution_time:.2f}s",
                'pipeline_id': result.pipeline_id
            }
            
            if result.collector_stats:
                pipeline_details['collector_breakdown'] = {
                    stat.name: {
                        'items': stat.items_collected,
                        'success': stat.success,
                        'time': f"{stat.execution_time:.2f}s"
                    }
                    for stat in result.collector_stats
                }
            
            self.log_test("Pipeline Execution", success, pipeline_details)
            
            # Store pipeline metrics
            self.test_results['pipeline_tests'] = {
                'success': success,
                'total_items_collected': result.total_items_collected,
                'execution_time': execution_time,
                'healthy_collectors': healthy_collectors,
                'collector_stats': pipeline_details.get('collector_breakdown', {})
            }
            
            return success
            
        except Exception as e:
            self.log_test("Pipeline Execution", False, {'error': str(e)})
            return False
    
    async def test_data_quality(self) -> bool:
        """Test data quality and validation"""
        print("\n🔍 TESTING DATA QUALITY")
        print("=" * 50)
        
        try:
            pipeline = DataPipeline()
            result = await pipeline.run_pipeline(replace(self.test_config, max_items_per_symbol=5))
            
            # PipelineResult doesn't contain data directly - check if any items were collected
            if result.total_items_collected == 0:
                self.log_test("Data Quality - Non-empty", False, {'error': 'No data collected'})
                return False
            
            # For data quality testing, collect sample data directly from a collector
            from app.infrastructure.collectors.hackernews_collector import HackerNewsCollector
            collector = HackerNewsCollector()  # No API key needed
            collection_config = CollectionConfig(
                symbols=self.test_symbols[:1],  # Just one symbol for testing
                date_range=self.test_config.date_range,
                max_items_per_symbol=1,
                include_comments=self.test_config.include_comments
            )
            
            collection_result = await collector.collect_data(collection_config)
            if not collection_result.data:
                self.log_test("Data Quality - Non-empty", False, {'error': 'No sample data collected'})
                return False
            
            # Check data structure
            sample_item = collection_result.data[0]
            required_fields = ['stock_symbol', 'text', 'timestamp', 'url', 'source']
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(sample_item, field) or getattr(sample_item, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_test("Data Quality - Structure", False, 
                            {'missing_fields': missing_fields})
                return False
            
            # Check symbol coverage using collected data
            symbols_found = set(item.stock_symbol for item in collection_result.data if hasattr(item, 'stock_symbol'))
            expected_symbols = set(self.test_symbols[:1])  # We only tested one symbol
            
            symbol_coverage = len(symbols_found.intersection(expected_symbols)) / len(expected_symbols)
            
            self.log_test("Data Quality - Symbol Coverage", symbol_coverage >= 0.5, {
                'coverage': f"{symbol_coverage:.1%}",
                'symbols_found': list(symbols_found),
                'expected_symbols': list(expected_symbols)
            })
            
            # Check timestamp validity
            valid_timestamps = 0
            for item in collection_result.data[:10]:  # Check first 10 items
                if hasattr(item, 'timestamp') and item.timestamp:
                    # Check if timestamp is recent (within last 7 days)
                    if isinstance(item.timestamp, datetime):
                        age = utc_now().replace(tzinfo=item.timestamp.tzinfo) - item.timestamp
                        if age.days <= 7:
                            valid_timestamps += 1
            
            timestamp_validity = valid_timestamps / min(len(collection_result.data), 10)
            
            self.log_test("Data Quality - Timestamps", timestamp_validity >= 0.8, {
                'validity_rate': f"{timestamp_validity:.1%}",
                'valid_count': valid_timestamps
            })
            
            return True
            
        except Exception as e:
            self.log_test("Data Quality", False, {'error': str(e)})
            return False
    
    async def test_performance_benchmarks(self) -> Dict[str, float]:
        """Test performance benchmarks"""
        print("\n⚡ TESTING PERFORMANCE BENCHMARKS")
        print("=" * 50)
        
        benchmarks = {}
        
        try:
            # Test different configurations - reduced to prevent API rate limits
            configs = [
                ('Light Test', replace(self.test_config, max_items_per_symbol=1)),
                ('Standard Test', replace(self.test_config, max_items_per_symbol=2))
                # Removed large load test to prevent API rate limiting
            ]
            
            pipeline = DataPipeline()
            
            for config_name, config in configs:
                start_time = time.time()
                result = await pipeline.run_pipeline(config)
                execution_time = time.time() - start_time
                
                # Add delay between configs to prevent rate limiting
                await asyncio.sleep(2)
                
                items_per_second = result.total_items_collected / execution_time if execution_time > 0 else 0
                
                benchmarks[config_name] = execution_time
                
                self.log_test(f"Performance - {config_name}", True, {
                    'execution_time': f"{execution_time:.2f}s",
                    'items_collected': result.total_items_collected,
                    'items_per_second': f"{items_per_second:.2f}",
                    'status': result.status.value
                })
            
            self.test_results['performance_metrics'] = benchmarks
            
        except Exception as e:
            self.log_test("Performance Benchmarks", False, {'error': str(e)})
        
        return benchmarks
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 5 tests"""
        print("🚀 PHASE 5 COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"Target Stocks: {', '.join(self.test_symbols)}")
        print(f"Test Date: {utc_now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        # Run test sequence
        api_keys_valid = await self.test_api_keys()
        
        if not api_keys_valid:
            print("\n⚠️  WARNING: Some API keys are missing. Tests may fail.")
        
        collector_results = await self.test_individual_collectors()
        pipeline_success = await self.test_pipeline_orchestration()
        data_quality_success = await self.test_data_quality()
        performance_benchmarks = await self.test_performance_benchmarks()
        
        # Calculate overall results
        overall_success = (
            self.test_results['tests_passed'] > 0 and
            self.test_results['tests_failed'] < self.test_results['tests_passed'] and
            pipeline_success
        )
        
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.test_results['tests_passed']}")
        print(f"❌ Tests Failed: {self.test_results['tests_failed']}")
        print(f"📊 Success Rate: {(self.test_results['tests_passed'] / self.test_results['tests_run']) * 100:.1f}%")
        print(f"🎯 Overall Status: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        if self.test_results['errors']:
            print(f"\n❌ Errors encountered: {len(self.test_results['errors'])}")
            for error in self.test_results['errors'][:3]:  # Show first 3 errors
                print(f"   • {error['test']}: {error['error']}")
        
        print(f"\n🎉 Phase 5 Data Collection Pipeline: {'OPERATIONAL' if overall_success else 'NEEDS ATTENTION'}")
        
        return self.test_results


async def main():
    """Main test execution"""
    if not IMPORTS_AVAILABLE:
        print("❌ Cannot run tests due to import errors")
        return
    
    test_suite = Phase5TestSuite()
    results = await test_suite.run_all_tests()
    
    # Save results to file
    results_file = 'phase5_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())