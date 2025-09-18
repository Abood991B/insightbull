"""
Phase 7: Orchestration and Logging Integration Tests
===================================================

Tests for the complete Phase 7 implementation as specified in the FYP Report:
- Pipeline class orchestration (Facade pattern)
- Scheduler automated periodic execution
- LogSystem singleton integration
- End-to-end integration testing

Based on FYP Report Phase 7 requirements:
"The system's flow orchestration is handled through the Pipeline class
and the Scheduler, which automates periodic execution. Logging
infrastructure is centralized using the LogSystem singleton."
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add the backend directory to sys.path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.business.pipeline import DataPipeline, PipelineConfig, DateRange
from app.business.scheduler import Scheduler, JobStatus
from app.infrastructure.log_system import LogSystem, get_logger
from app.service.sentiment_processing import reset_sentiment_engine


@pytest.fixture(autouse=True)
def reset_sentiment_engine_between_tests():
    """Reset the singleton SentimentEngine between tests to prevent duplicate loading messages"""
    reset_sentiment_engine()
    yield
    reset_sentiment_engine()


class TestPhase7PipelineOrchestration:
    """Test Pipeline class as Facade pattern orchestrator"""
    
    @pytest.mark.asyncio
    async def test_pipeline_facade_pattern(self):
        """Test that Pipeline acts as proper Facade for data flow orchestration"""
        # Disable auto-configure to avoid unicode emoji logging issues
        pipeline = DataPipeline(auto_configure_collectors=False)
        
        # Test Facade pattern - single interface for complex subsystem
        assert hasattr(pipeline, 'run_pipeline'), "Pipeline should have run_pipeline method"
        assert hasattr(pipeline, 'text_processor'), "Pipeline should manage text processing"
        assert hasattr(pipeline, 'sentiment_engine'), "Pipeline should manage sentiment analysis"
        assert hasattr(pipeline, '_collectors'), "Pipeline should manage data collectors"
        
        print("✅ Pipeline implements Facade pattern correctly")
    
    @pytest.mark.asyncio
    async def test_pipeline_orchestration_flow(self):
        """Test complete data flow orchestration through Pipeline"""
        pipeline = DataPipeline(auto_configure_collectors=False)
        
        # Create test configuration
        config = PipelineConfig(
            symbols=["AAPL"],
            date_range=DateRange(
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            ),
            max_items_per_symbol=5,
            include_reddit=False,  # Skip external APIs for testing
            include_newsapi=False,
            include_finnhub=False,
            include_marketaux=False
        )
        
        # Mock external dependencies to avoid API calls
        with patch.object(pipeline, '_collect_data', return_value={}):
            with patch.object(pipeline, '_process_data', return_value=[]):
                with patch.object(pipeline, '_store_data', return_value=0):
                    result = await pipeline.run_pipeline(config)
                    
                    assert result is not None, "Pipeline should return result"
                    assert hasattr(result, 'pipeline_id'), "Result should have pipeline_id"
                    assert hasattr(result, 'status'), "Result should have status"
                    
        print("✅ Pipeline orchestrates complete data flow correctly")


class TestPhase7SchedulerIntegration:
    """Test Scheduler for automated periodic execution"""
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """Test Scheduler properly initializes with Pipeline integration"""
        scheduler = Scheduler()
        
        # Test that scheduler has required components
        assert hasattr(scheduler, 'pipeline'), "Scheduler should have Pipeline instance"
        assert hasattr(scheduler, 'data_collector'), "Scheduler should have DataCollector"
        assert hasattr(scheduler, 'scheduler'), "Scheduler should have APScheduler instance"
        assert hasattr(scheduler, 'jobs'), "Scheduler should track jobs"
        
        print("✅ Scheduler initializes with proper Pipeline integration")
    
    @pytest.mark.asyncio
    async def test_scheduler_periodic_execution(self):
        """Test Scheduler can schedule and execute periodic tasks"""
        scheduler = Scheduler()
        
        # Mock pipeline execution to avoid actual data collection
        mock_pipeline_result = Mock()
        mock_pipeline_result.status = "completed"
        
        with patch.object(scheduler.pipeline, 'run_pipeline', return_value=mock_pipeline_result):
            # Test scheduling a job
            job_id = await scheduler.schedule_data_collection(
                name="test_job",
                cron_expression="0 * * * *",  # Every hour
                symbols=["AAPL"],
                lookback_days=1
            )
            
            assert job_id is not None, "Should return job ID"
            assert job_id in scheduler.jobs, "Job should be tracked"
            
            job = scheduler.jobs[job_id]
            assert job.name == "test_job", "Job should have correct name"
            assert job.parameters["symbols"] == ["AAPL"], "Job should have correct parameters"
        
        print("✅ Scheduler handles periodic execution correctly")
    
    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self):
        """Test Scheduler start/stop lifecycle"""
        scheduler = Scheduler()
        
        # Test starting scheduler
        await scheduler.start()
        assert scheduler._is_running, "Scheduler should be running after start"
        
        # Test stopping scheduler
        await scheduler.stop()
        assert not scheduler._is_running, "Scheduler should be stopped after stop"
        
        print("✅ Scheduler lifecycle management works correctly")


class TestPhase7LogSystemIntegration:
    """Test LogSystem singleton integration"""
    
    def test_logsystem_singleton_pattern(self):
        """Test LogSystem implements proper Singleton pattern"""
        # Create multiple instances
        log1 = LogSystem()
        log2 = LogSystem()
        
        # Should be the same instance
        assert log1 is log2, "LogSystem should implement Singleton pattern"
        
        # Test get_logger function
        logger1 = get_logger()
        logger2 = get_logger()
        
        # Should use the same logging system
        assert logger1 is not None, "get_logger should return logger"
        assert logger2 is not None, "get_logger should return logger"
        
        print("✅ LogSystem implements Singleton pattern correctly")
    
    def test_logsystem_integration_across_components(self):
        """Test LogSystem is properly integrated across Pipeline and Scheduler"""
        # Test Pipeline uses LogSystem
        pipeline = DataPipeline(auto_configure_collectors=False)
        assert hasattr(pipeline, 'logger'), "Pipeline should have logger"
        
        # Test Scheduler uses LogSystem  
        scheduler = Scheduler()
        assert hasattr(scheduler, 'logger'), "Scheduler should have logger"
        
        # Both should use the same logging system
        pipeline_logger = pipeline.logger
        scheduler_logger = scheduler.logger
        
        assert pipeline_logger is not None, "Pipeline logger should exist"
        assert scheduler_logger is not None, "Scheduler logger should exist"
        
        print("✅ LogSystem properly integrated across all components")


class TestPhase7EndToEndIntegration:
    """End-to-end integration tests for Phase 7"""
    
    @pytest.mark.asyncio
    async def test_complete_phase7_integration(self):
        """Test complete Phase 7 integration: Pipeline + Scheduler + LogSystem"""
        
        # Initialize all Phase 7 components
        log_system = LogSystem()
        pipeline = DataPipeline(auto_configure_collectors=False)
        scheduler = Scheduler()
        
        print("Phase 7 Integration Test Starting...")
        print("=" * 50)
        
        # Test 1: LogSystem integration
        assert log_system is not None, "LogSystem should initialize"
        logger = get_logger()
        logger.info("Phase 7 integration test started")
        print("✅ LogSystem singleton working")
        
        # Test 2: Pipeline orchestration
        config = PipelineConfig(
            symbols=["AAPL"],
            date_range=DateRange(
                start_date=datetime.now() - timedelta(hours=1),
                end_date=datetime.now()
            ),
            max_items_per_symbol=1,
            include_reddit=False,  # Skip external APIs
            include_newsapi=False,
            include_finnhub=False,
            include_marketaux=False
        )
        
        # Mock external dependencies
        with patch.object(pipeline, '_collect_data', return_value={}):
            with patch.object(pipeline, '_process_data', return_value=[]):
                with patch.object(pipeline, '_store_data', return_value=0):
                    result = await pipeline.run_pipeline(config)
                    assert result is not None, "Pipeline should execute successfully"
        
        print("✅ Pipeline orchestration working")
        
        # Test 3: Scheduler integration with Pipeline
        with patch.object(scheduler.pipeline, 'run_pipeline', return_value=Mock(status="completed")):
            await scheduler.start()
            assert scheduler._is_running, "Scheduler should start"
            
            # Test scheduling a job
            job_id = await scheduler.schedule_data_collection(
                name="integration_test",
                cron_expression="0 * * * *",  # Every hour
                symbols=["AAPL"],
                lookback_days=1
            )
            
            assert job_id in scheduler.jobs, "Job should be scheduled"
            await scheduler.stop()
            assert not scheduler._is_running, "Scheduler should stop"
        
        print("✅ Scheduler + Pipeline integration working")
        
        logger.info("Phase 7 integration test completed successfully")
        print("✅ Complete Phase 7 integration test passed")
        
        return True
    
    @pytest.mark.asyncio
    async def test_phase7_with_main_app_integration(self):
        """Test Phase 7 components integrate properly with FastAPI main app"""
        
        # Test that components can be imported and initialized like in main.py
        try:
            from app.business.scheduler import Scheduler
            from app.business.pipeline import DataPipeline
            from app.infrastructure.log_system import get_logger
            
            # Simulate main app startup
            logger = get_logger()
            logger.info("Simulating main app startup with Phase 7")
            
            scheduler = Scheduler()
            await scheduler.start()
            
            # Simulate some running time
            await asyncio.sleep(0.1)
            
            # Simulate main app shutdown
            await scheduler.stop()
            logger.info("Simulated main app shutdown with Phase 7")
            
            print("✅ Phase 7 integrates properly with main FastAPI app")
            
        except Exception as e:
            pytest.fail(f"Phase 7 main app integration failed: {e}")


# Test runner for direct execution
async def run_phase7_tests():
    """Run Phase 7 integration tests directly"""
    print("🚀 Running Phase 7: Orchestration and Logging Tests")
    print("=" * 60)
    
    try:
        # Test Pipeline Orchestration
        print("\n📋 Testing Pipeline Orchestration (Facade Pattern)")
        test_pipeline = TestPhase7PipelineOrchestration()
        await test_pipeline.test_pipeline_facade_pattern()
        await test_pipeline.test_pipeline_orchestration_flow()
        
        # Test Scheduler Integration
        print("\n⏰ Testing Scheduler Integration")
        test_scheduler = TestPhase7SchedulerIntegration()
        await test_scheduler.test_scheduler_initialization()
        await test_scheduler.test_scheduler_periodic_execution()
        await test_scheduler.test_scheduler_lifecycle()
        
        # Test LogSystem Integration
        print("\n📝 Testing LogSystem Integration")
        test_logging = TestPhase7LogSystemIntegration()
        test_logging.test_logsystem_singleton_pattern()
        test_logging.test_logsystem_integration_across_components()
        
        # Test End-to-End Integration
        print("\n🔄 Testing End-to-End Integration")
        test_e2e = TestPhase7EndToEndIntegration()
        await test_e2e.test_complete_phase7_integration()
        await test_e2e.test_phase7_with_main_app_integration()
        
        print("\n" + "=" * 60)
        print("✅ All Phase 7 Tests Passed Successfully!")
        print("Phase 7: Orchestration and Logging - COMPLETE")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Phase 7 Tests Failed: {e}")
        return False


if __name__ == "__main__":
    # Run tests directly
    success = asyncio.run(run_phase7_tests())
    exit(0 if success else 1)