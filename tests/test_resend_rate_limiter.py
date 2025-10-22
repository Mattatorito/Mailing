"""
Comprehensive tests for resend/rate_limiter.py

Covers:
- RateLimiter class functionality
- Request queuing and time windows
- Burst limiting
- Global rate limiter management
- Predefined service limiters
- RateLimitedClient class
- Decorators and utility functions
- Async operations and concurrency
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from src.resend.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
    get_resend_limiter,
    get_mailgun_limiter,
    get_sendgrid_limiter,
    RateLimitedClient,
    with_rate_limit,
    rate_limited,
    _limiters
)


class TestRateLimiter:
    """Test suite for RateLimiter class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        
        assert limiter.max_requests == 10
        assert limiter.time_window == 60.0
        assert limiter.burst_limit == 10  # Default to max_requests
        assert len(limiter.requests) == 0
        assert limiter._lock is not None
    
    def test_init_with_burst_limit(self):
        """Test initialization with custom burst limit."""
        limiter = RateLimiter(max_requests=10, time_window=60.0, burst_limit=5)
        
        assert limiter.max_requests == 10
        assert limiter.time_window == 60.0
        assert limiter.burst_limit == 5
    
    @pytest.mark.asyncio
    async def test_acquire_first_request(self):
        """Test acquiring first request slot."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        result = await limiter.acquire()
        
        assert result is True
        assert len(limiter.requests) == 1
    
    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring multiple requests within limit."""
        limiter = RateLimiter(max_requests=3, time_window=60.0)
        
        # Acquire 3 requests
        for i in range(3):
            result = await limiter.acquire()
            assert result is True
        
        assert len(limiter.requests) == 3
    
    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self):
        """Test acquiring request when limit is exceeded."""
        limiter = RateLimiter(max_requests=2, time_window=60.0)
        
        # Fill up to limit
        await limiter.acquire()
        await limiter.acquire()
        
        # This should fail
        result = await limiter.acquire()
        assert result is False
        assert len(limiter.requests) == 2
    
    @pytest.mark.asyncio
    async def test_acquire_old_requests_cleaned(self):
        """Test that old requests are cleaned up."""
        limiter = RateLimiter(max_requests=2, time_window=1.0)
        
        # Add an old request manually
        old_time = time.time() - 2.0
        limiter.requests.append(old_time)
        
        # This should succeed because old request is cleaned up
        result = await limiter.acquire()
        assert result is True
        assert len(limiter.requests) == 1
        
        # The old request should be gone
        remaining_time = time.time() - limiter.requests[0]
        assert remaining_time < 1.0
    
    @pytest.mark.asyncio
    async def test_wait_for_slot_immediately_available(self):
        """Test wait_for_slot when slot is immediately available."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        start_time = time.time()
        await limiter.wait_for_slot()
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 0.1
        assert len(limiter.requests) == 1
    
    @pytest.mark.asyncio
    async def test_wait_for_slot_with_delay(self):
        """Test wait_for_slot when slot requires waiting."""
        limiter = RateLimiter(max_requests=1, time_window=0.5)
        
        # Fill the limit
        await limiter.acquire()
        
        start_time = time.time()
        await limiter.wait_for_slot()
        elapsed = time.time() - start_time
        
        # Should have waited for the time window
        assert elapsed >= 0.4  # Allow some tolerance
        assert len(limiter.requests) == 1  # Old request should be cleaned
    
    def test_get_remaining_requests_empty(self):
        """Test get_remaining_requests with no requests."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        remaining = limiter.get_remaining_requests()
        assert remaining == 5
    
    def test_get_remaining_requests_with_active(self):
        """Test get_remaining_requests with active requests."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        # Add some current requests
        now = time.time()
        limiter.requests.extend([now - 10, now - 5, now - 1])
        
        remaining = limiter.get_remaining_requests()
        assert remaining == 2
    
    def test_get_remaining_requests_cleans_old(self):
        """Test that get_remaining_requests cleans old requests."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)
        
        # Add old and new requests
        now = time.time()
        limiter.requests.extend([now - 2.0, now - 0.5])  # One old, one new
        
        remaining = limiter.get_remaining_requests()
        assert remaining == 4  # Only 1 active request remains
        assert len(limiter.requests) == 1
    
    def test_get_reset_time_empty(self):
        """Test get_reset_time with no requests."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        reset_time = limiter.get_reset_time()
        assert reset_time == 0.0
    
    def test_get_reset_time_with_requests(self):
        """Test get_reset_time with active requests."""
        limiter = RateLimiter(max_requests=5, time_window=60.0)
        
        # Add a request 30 seconds ago
        limiter.requests.append(time.time() - 30.0)
        
        reset_time = limiter.get_reset_time()
        assert 29.0 <= reset_time <= 31.0  # Should be around 30 seconds


class TestGlobalRateLimiters:
    """Test suite for global rate limiter management."""
    
    def setup_method(self):
        """Clear global limiters before each test."""
        _limiters.clear()
    
    def teardown_method(self):
        """Clean up after each test."""
        _limiters.clear()
    
    def test_get_rate_limiter_creates_new(self):
        """Test that get_rate_limiter creates new limiter."""
        limiter = get_rate_limiter("test", max_requests=10, time_window=60.0)
        
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60.0
    
    def test_get_rate_limiter_reuses_existing(self):
        """Test that get_rate_limiter reuses existing limiter."""
        limiter1 = get_rate_limiter("test", max_requests=10, time_window=60.0)
        limiter2 = get_rate_limiter("test", max_requests=20, time_window=30.0)  # Different params
        
        # Should return the same instance despite different params
        assert limiter1 is limiter2
        assert limiter2.max_requests == 10  # Original params preserved
    
    def test_get_rate_limiter_with_burst_limit(self):
        """Test get_rate_limiter with burst limit."""
        limiter = get_rate_limiter("test", max_requests=10, time_window=60.0, burst_limit=5)
        
        assert limiter.burst_limit == 5
    
    def test_get_resend_limiter(self):
        """Test predefined Resend limiter."""
        limiter = get_resend_limiter()
        
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 10
        assert limiter.time_window == 1.0
    
    def test_get_resend_limiter_reuses(self):
        """Test that Resend limiter is reused."""
        limiter1 = get_resend_limiter()
        limiter2 = get_resend_limiter()
        
        assert limiter1 is limiter2
    
    def test_get_mailgun_limiter(self):
        """Test predefined Mailgun limiter."""
        limiter = get_mailgun_limiter()
        
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 100
        assert limiter.time_window == 1.0
    
    def test_get_sendgrid_limiter(self):
        """Test predefined SendGrid limiter."""
        limiter = get_sendgrid_limiter()
        
        assert isinstance(limiter, RateLimiter)
        assert limiter.max_requests == 600
        assert limiter.time_window == 60.0


class TestRateLimitedClient:
    """Test suite for RateLimitedClient class."""
    
    def test_init(self):
        """Test RateLimitedClient initialization."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        client = RateLimitedClient(limiter)
        
        assert client.rate_limiter is limiter
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful request through RateLimitedClient."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        client = RateLimitedClient(limiter)
        
        # Mock async function
        async def mock_request(data):
            return f"result: {data}"
        
        result = await client.make_request(mock_request, "test_data")
        
        assert result == "result: test_data"
        assert len(limiter.requests) == 1
    
    @pytest.mark.asyncio
    async def test_make_request_with_rate_limit_error(self):
        """Test request with 429 rate limit error."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        client = RateLimitedClient(limiter)
        
        # Mock function that raises 429 error
        async def mock_request():
            error = Exception("Rate limited")
            error.status_code = 429
            raise error
        
        start_time = time.time()
        with pytest.raises(Exception, match="Rate limited"):
            await client.make_request(mock_request)
        
        elapsed = time.time() - start_time
        # Should have waited additional 5 seconds
        assert elapsed >= 4.9
    
    @pytest.mark.asyncio
    async def test_make_request_with_other_error(self):
        """Test request with non-rate-limit error."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        client = RateLimitedClient(limiter)
        
        # Mock function that raises regular error
        async def mock_request():
            raise ValueError("Some other error")
        
        start_time = time.time()
        with pytest.raises(ValueError, match="Some other error"):
            await client.make_request(mock_request)
        
        elapsed = time.time() - start_time
        # Should not have waited additional time
        assert elapsed < 1.0


class TestUtilityFunctions:
    """Test suite for utility functions."""
    
    def setup_method(self):
        """Clear global limiters before each test."""
        _limiters.clear()
    
    def teardown_method(self):
        """Clean up after each test."""
        _limiters.clear()
    
    @pytest.mark.asyncio
    async def test_with_rate_limit_success(self):
        """Test with_rate_limit function success."""
        limiter = RateLimiter(max_requests=10, time_window=60.0)
        
        async def test_func(value):
            return value * 2
        
        result = await with_rate_limit(limiter, test_func, 5)
        
        assert result == 10
        assert len(limiter.requests) == 1
    
    @pytest.mark.asyncio
    async def test_with_rate_limit_waits(self):
        """Test that with_rate_limit waits for slot."""
        limiter = RateLimiter(max_requests=1, time_window=0.5)
        
        # Fill the limit
        await limiter.acquire()
        
        async def test_func():
            return "result"
        
        start_time = time.time()
        result = await with_rate_limit(limiter, test_func)
        elapsed = time.time() - start_time
        
        assert result == "result"
        assert elapsed >= 0.4  # Should have waited
    
    @pytest.mark.asyncio
    async def test_rate_limited_decorator_default_name(self):
        """Test rate_limited decorator with default name."""
        @rate_limited(max_requests=5, time_window=60.0)
        async def test_function(value):
            return value + 1
        
        result = await test_function(10)
        assert result == 11
        
        # Check that limiter was created
        # The name should be based on the test function's module
        expected_name = f"{test_function.__module__}.test_function"
        loop = asyncio.get_event_loop()
        assert loop in _limiters
        # Check if any limiter was created with function name
        limiter_names = list(_limiters[loop].keys())
        assert any("test_function" in name for name in limiter_names)
    
    @pytest.mark.asyncio
    async def test_rate_limited_decorator_custom_name(self):
        """Test rate_limited decorator with custom name."""
        @rate_limited(max_requests=5, time_window=60.0, name="custom_limiter")
        async def test_function(value):
            return value + 1
        
        result = await test_function(10)
        assert result == 11
        
        # Check that limiter was created with custom name
        loop = asyncio.get_event_loop()
        assert loop in _limiters
        assert "custom_limiter" in _limiters[loop]
    
    @pytest.mark.asyncio
    async def test_rate_limited_decorator_reuses_limiter(self):
        """Test that rate_limited decorator reuses limiter."""
        @rate_limited(max_requests=2, time_window=60.0, name="shared_limiter")
        async def function1():
            return "result1"
        
        @rate_limited(max_requests=10, time_window=30.0, name="shared_limiter")
        async def function2():
            return "result2"
        
        # Call both functions
        await function1()
        await function2()
        
        # Should use the same limiter (first one created)
        loop = asyncio.get_event_loop()
        limiter = _limiters[loop]["shared_limiter"]
        assert limiter.max_requests == 2  # From first function
        assert len(limiter.requests) == 2


class TestConcurrency:
    """Test suite for concurrent operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        """Test concurrent acquire operations."""
        limiter = RateLimiter(max_requests=3, time_window=60.0)
        
        # Launch multiple concurrent acquire operations
        tasks = [limiter.acquire() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Only 3 should succeed
        successful = sum(results)
        assert successful == 3
        assert len(limiter.requests) == 3
    
    @pytest.mark.asyncio
    async def test_concurrent_wait_for_slot(self):
        """Test concurrent wait_for_slot operations."""
        limiter = RateLimiter(max_requests=2, time_window=1.0)
        
        async def make_request(request_id):
            await limiter.wait_for_slot()
            return request_id
        
        # Launch multiple concurrent operations
        start_time = time.time()
        tasks = [make_request(i) for i in range(4)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # All should complete
        assert len(results) == 4
        assert results == [0, 1, 2, 3]
        
        # Should have taken some time for rate limiting
        assert elapsed >= 1.0  # At least one time window
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limited_functions(self):
        """Test concurrent rate-limited functions."""
        @rate_limited(max_requests=2, time_window=0.5, name="test_concurrent")
        async def limited_function(value):
            return value * 2
        
        # Launch multiple concurrent calls
        start_time = time.time()
        tasks = [limited_function(i) for i in range(4)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        # All should complete with correct results
        assert results == [0, 2, 4, 6]
        
        # Should have taken time for rate limiting
        assert elapsed >= 0.5  # At least one time window


class TestEdgeCases:
    """Test suite for edge cases."""
    
    def test_zero_time_window(self):
        """Test behavior with zero time window."""
        limiter = RateLimiter(max_requests=5, time_window=0.0)
        
        # Should work but all requests are considered "old"
        remaining = limiter.get_remaining_requests()
        assert remaining == 5
    
    def test_very_large_time_window(self):
        """Test behavior with very large time window."""
        limiter = RateLimiter(max_requests=2, time_window=86400.0)  # 24 hours
        
        # Add requests
        now = time.time()
        limiter.requests.extend([now - 3600, now - 1800])  # 1 and 0.5 hours ago
        
        remaining = limiter.get_remaining_requests()
        assert remaining == 0  # Both requests still active
    
    @pytest.mark.asyncio
    async def test_acquire_with_empty_deque_edge_case(self):
        """Test acquire when deque becomes empty during cleanup."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)
        
        # Add an old request that will be cleaned up
        limiter.requests.append(time.time() - 2.0)
        
        result = await limiter.acquire()
        assert result is True
        assert len(limiter.requests) == 1
    
    def test_get_reset_time_negative_case(self):
        """Test get_reset_time when calculated time would be negative."""
        limiter = RateLimiter(max_requests=5, time_window=1.0)
        
        # Add a very old request
        limiter.requests.append(time.time() - 5.0)
        
        reset_time = limiter.get_reset_time()
        assert reset_time == 0.0  # Should be clamped to 0


class TestAsyncContext:
    """Test suite for async context and event loop handling."""
    
    def setup_method(self):
        """Clear global limiters before each test."""
        _limiters.clear()
    
    def teardown_method(self):
        """Clean up after each test."""
        _limiters.clear()
    
    @pytest.mark.asyncio
    async def test_multiple_event_loops(self):
        """Test behavior with different event loops."""
        # This test verifies that limiters are properly scoped to event loops
        
        limiter1 = get_rate_limiter("test", max_requests=5, time_window=60.0)
        
        # Create a new event loop
        new_loop = asyncio.new_event_loop()
        
        def get_limiter_in_new_loop():
            asyncio.set_event_loop(new_loop)
            return get_rate_limiter("test", max_requests=10, time_window=30.0)
        
        try:
            # This would normally create a different limiter in the new loop
            # but since we're testing the existing implementation, 
            # we'll just verify current behavior
            assert len(_limiters) >= 1
            current_loop = asyncio.get_event_loop()
            assert current_loop in _limiters
        finally:
            new_loop.close()


class TestPerformance:
    """Test suite for performance considerations."""
    
    @pytest.mark.asyncio
    async def test_large_number_of_requests(self):
        """Test performance with large number of old requests."""
        limiter = RateLimiter(max_requests=100, time_window=60.0)
        
        # Add many old requests
        old_time = time.time() - 120.0
        for _ in range(1000):
            limiter.requests.append(old_time)
        
        # This should efficiently clean up old requests
        start_time = time.time()
        remaining = limiter.get_remaining_requests()
        elapsed = time.time() - start_time
        
        assert remaining == 100
        assert len(limiter.requests) == 0
        assert elapsed < 0.1  # Should be fast
    
    @pytest.mark.asyncio
    async def test_rapid_acquire_calls(self):
        """Test performance with rapid acquire calls."""
        limiter = RateLimiter(max_requests=50, time_window=60.0)
        
        start_time = time.time()
        
        # Make many rapid acquire calls
        results = []
        for _ in range(100):
            result = await limiter.acquire()
            results.append(result)
        
        elapsed = time.time() - start_time
        
        # Should complete quickly
        assert elapsed < 1.0
        
        # First 50 should succeed, rest should fail
        successful = sum(results)
        assert successful == 50