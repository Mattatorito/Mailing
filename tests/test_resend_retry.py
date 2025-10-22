"""
Comprehensive tests for resend/retry.py

Covers:
- retry_with_backoff function
- retry decorator
- Exponential backoff calculations
- Jitter functionality
- Smart retry logic
- Error type classification
- Custom exception classes
- HTTP error handling
- Network error handling
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from src.resend.retry import (
    retry_with_backoff,
    retry,
    RetryableError,
    NonRetryableError,
    is_retryable_error,
    smart_retry
)


class TestRetryWithBackoff:
    """Test suite for retry_with_backoff function."""
    
    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        """Test successful execution on first attempt."""
        async def successful_func(value):
            return value * 2
        
        result = await retry_with_backoff(successful_func, 5)
        assert result == 10
    
    @pytest.mark.asyncio
    async def test_success_after_retries(self):
        """Test successful execution after some retries."""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary network failure")
            return "success"
        
        result = await retry_with_backoff(
            failing_then_success,
            max_retries=5,
            base_delay=0.01  # Very small delay for testing
        )
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_exhausted_retries(self):
        """Test that exception is raised when retries are exhausted."""
        async def always_failing():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await retry_with_backoff(
                always_failing,
                max_retries=2,
                base_delay=0.01
            )
    
    @pytest.mark.asyncio
    async def test_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        call_times = []
        
        async def track_timing():
            call_times.append(time.time())
            raise Exception("Test error")
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            await retry_with_backoff(
                track_timing,
                max_retries=3,
                base_delay=0.1,
                backoff_factor=2.0,
                jitter=False  # Disable jitter for predictable timing
            )
        
        # Check that delays increase exponentially
        assert len(call_times) == 4  # Initial + 3 retries
        
        # Calculate actual delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Should be approximately 0.1, 0.2, 0.4 (exponential backoff)
        assert 0.08 <= delays[0] <= 0.12  # ~0.1
        assert 0.18 <= delays[1] <= 0.22  # ~0.2
        assert 0.38 <= delays[2] <= 0.42  # ~0.4
    
    @pytest.mark.asyncio
    async def test_max_delay_limit(self):
        """Test that delay is capped at max_delay."""
        call_times = []
        
        async def track_timing():
            call_times.append(time.time())
            raise Exception("Test error")
        
        with pytest.raises(Exception):
            await retry_with_backoff(
                track_timing,
                max_retries=2,
                base_delay=10.0,
                backoff_factor=2.0,
                max_delay=0.2,  # Cap at 0.2 seconds
                jitter=False
            )
        
        # Calculate delays
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # All delays should be capped at max_delay
        for delay in delays:
            assert delay <= 0.25  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_jitter_effect(self):
        """Test that jitter adds randomness to delays."""
        delays = []
        
        async def capture_delays():
            raise Exception("Test error")
        
        # Run multiple times to collect delay samples
        for _ in range(5):
            call_times = []
            
            async def track_timing():
                call_times.append(time.time())
                raise Exception("Test error")
            
            with pytest.raises(Exception):
                await retry_with_backoff(
                    track_timing,
                    max_retries=1,
                    base_delay=0.1,
                    jitter=True
                )
            
            if len(call_times) >= 2:
                delay = call_times[1] - call_times[0]
                delays.append(delay)
        
        # With jitter, delays should vary
        if len(delays) > 1:
            delay_variance = max(delays) - min(delays)
            assert delay_variance > 0.01  # Some variance expected
    
    @pytest.mark.asyncio
    async def test_function_with_args_kwargs(self):
        """Test retry with function arguments."""
        async def func_with_args(a, b, c=None):
            if c == "fail":
                raise Exception("Intentional failure")
            return a + b + (c or 0)
        
        # Test success with args and kwargs
        result = await retry_with_backoff(func_with_args, 1, 2, c=3)
        assert result == 6
        
        # Test with failure then success
        call_count = 0
        
        async def conditional_func(a, b, c=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First call fails")
            return a + b + (c or 0)
        
        result = await retry_with_backoff(
            conditional_func, 1, 2, c=3,
            max_retries=2,
            base_delay=0.01
        )
        assert result == 6


class TestRetryDecorator:
    """Test suite for retry decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_success(self):
        """Test retry decorator with successful function."""
        @retry(max_retries=3, base_delay=0.01)
        async def successful_function(value):
            return value * 3
        
        result = await successful_function(4)
        assert result == 12
    
    @pytest.mark.asyncio
    async def test_decorator_with_retries(self):
        """Test retry decorator with failing then successful function."""
        call_count = 0
        
        @retry(max_retries=3, base_delay=0.01)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "decorated success"
        
        result = await failing_then_success()
        assert result == "decorated success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_decorator_exhausted_retries(self):
        """Test retry decorator when retries are exhausted."""
        @retry(max_retries=2, base_delay=0.01)
        async def always_failing():
            raise RuntimeError("Always fails")
        
        with pytest.raises(RuntimeError, match="Always fails"):
            await always_failing()
    
    @pytest.mark.asyncio
    async def test_decorator_custom_params(self):
        """Test retry decorator with custom parameters."""
        call_times = []
        
        @retry(max_retries=2, base_delay=0.1, backoff_factor=3.0, jitter=False)
        async def timing_function():
            call_times.append(time.time())
            raise Exception("Test error")
        
        with pytest.raises(Exception):
            await timing_function()
        
        # Verify custom backoff factor was applied
        if len(call_times) >= 3:
            delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
            # Should be approximately 0.1, 0.3 (base_delay * backoff_factor^attempt)
            assert 0.08 <= delays[0] <= 0.12
            assert 0.28 <= delays[1] <= 0.32


class TestCustomExceptions:
    """Test suite for custom exception classes."""
    
    def test_retryable_error(self):
        """Test RetryableError exception."""
        error = RetryableError("This can be retried")
        assert isinstance(error, Exception)
        assert str(error) == "This can be retried"
    
    def test_non_retryable_error(self):
        """Test NonRetryableError exception."""
        error = NonRetryableError("This cannot be retried")
        assert isinstance(error, Exception)
        assert str(error) == "This cannot be retried"
    
    def test_is_retryable_error_retryable(self):
        """Test is_retryable_error with RetryableError."""
        error = RetryableError("Test error")
        assert is_retryable_error(error) is True
    
    def test_is_retryable_error_non_retryable(self):
        """Test is_retryable_error with NonRetryableError."""
        error = NonRetryableError("Test error")
        assert is_retryable_error(error) is False
    
    def test_is_retryable_error_http_server_error(self):
        """Test is_retryable_error with HTTP server errors."""
        # Mock HTTP error with status code 500
        error = Exception("Server error")
        error.status_code = 500
        assert is_retryable_error(error) is True
        
        # Mock HTTP error with status code 503
        error = Exception("Service unavailable")
        error.status = 503
        assert is_retryable_error(error) is True
    
    def test_is_retryable_error_http_rate_limit(self):
        """Test is_retryable_error with HTTP rate limiting."""
        error = Exception("Rate limited")
        error.status_code = 429
        assert is_retryable_error(error) is True
    
    def test_is_retryable_error_http_client_error(self):
        """Test is_retryable_error with HTTP client errors."""
        error = Exception("Bad request")
        error.status_code = 400
        assert is_retryable_error(error) is False
        
        error = Exception("Not found")
        error.status_code = 404
        assert is_retryable_error(error) is False
    
    def test_is_retryable_error_aiohttp_errors(self):
        """Test is_retryable_error with aiohttp errors."""
        # Test with actual aiohttp import
        try:
            import aiohttp
            error = aiohttp.ClientError("Test error")
            assert is_retryable_error(error) is True
        except ImportError:
            # If aiohttp not available, test the code path
            error = Exception("Client error")
            # Mock to look like aiohttp error for isinstance check
            error.__class__.__name__ = "ClientError"
            # Since isinstance will fail for mock, it should return False
            assert is_retryable_error(error) is False
    
    def test_is_retryable_error_timeout(self):
        """Test is_retryable_error with timeout errors."""
        error = asyncio.TimeoutError("Timeout")
        assert is_retryable_error(error) is True
    
    def test_is_retryable_error_generic(self):
        """Test is_retryable_error with generic exceptions."""
        error = ValueError("Generic error")
        assert is_retryable_error(error) is False
        
        error = RuntimeError("Runtime error")
        assert is_retryable_error(error) is False


class TestSmartRetry:
    """Test suite for smart_retry function."""
    
    @pytest.mark.asyncio
    async def test_smart_retry_success(self):
        """Test smart_retry with successful function."""
        async def successful_func():
            return "success"
        
        result = await smart_retry(successful_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_smart_retry_retryable_error(self):
        """Test smart_retry with retryable errors."""
        call_count = 0
        
        async def retryable_failure():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = Exception("Server error")
                error.status_code = 500
                raise error
            return "recovered"
        
        result = await smart_retry(retryable_failure, max_retries=3)
        assert result == "recovered"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_smart_retry_non_retryable_error(self):
        """Test smart_retry with non-retryable errors."""
        call_count = 0
        
        async def non_retryable_failure():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("Cannot retry this")
        
        with pytest.raises(NonRetryableError, match="Cannot retry this"):
            await smart_retry(non_retryable_failure, max_retries=3)
        
        # Should fail immediately without retries
        assert call_count == 1
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Optimize test delay to avoid 29+ second wait time")
    async def test_smart_retry_rate_limiting_optimized(self):
        """Test smart_retry with rate limiting (429) errors - optimized version."""
        import aiohttp
        pytest.importorskip("aiohttp")  # Skip if aiohttp unavailable
        
        call_times = []
        
        async def rate_limited_func():
            call_times.append(time.time())
            # Mock rate limit with shorter delay for testing
            error = Exception("Rate limited")
            error.status_code = 429
            raise error
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            # Use shorter max_delay for testing
            await smart_retry(rate_limited_func, max_retries=1, max_delay=0.1)
        
        # Should complete quickly in test environment
        total_time = time.time() - start_time
        assert total_time < 1.0  # Much faster for testing
    
    @pytest.mark.asyncio
    async def test_smart_retry_normal_backoff(self):
        """Test smart_retry with normal exponential backoff."""
        call_times = []
        
        async def normal_failure():
            call_times.append(time.time())
            error = Exception("Server error")
            error.status_code = 500
            raise error
        
        with pytest.raises(Exception):
            await smart_retry(normal_failure, max_retries=2)
        
        # Calculate delays between calls
        delays = [call_times[i+1] - call_times[i] for i in range(len(call_times)-1)]
        
        # Should use exponential backoff: 1s, 2s
        assert 0.8 <= delays[0] <= 1.2  # ~1 second
        assert 1.8 <= delays[1] <= 2.2  # ~2 seconds
    
    @pytest.mark.asyncio
    async def test_smart_retry_with_args_kwargs(self):
        """Test smart_retry with function arguments."""
        call_count = 0
        
        async def func_with_params(a, b, c=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = Exception("Temporary error")
                error.status_code = 500
                raise error
            return a + b + (c or 0)
        
        result = await smart_retry(func_with_params, 1, 2, c=3, max_retries=2)
        assert result == 6


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_zero_retries(self):
        """Test retry behavior with zero retries."""
        async def failing_func():
            raise ValueError("Immediate failure")
        
        with pytest.raises(ValueError, match="Immediate failure"):
            await retry_with_backoff(failing_func, max_retries=0)
    
    @pytest.mark.asyncio
    async def test_negative_retries(self):
        """Test retry behavior with negative retries."""
        # With negative retries, range(max_retries + 1) = range(0) = empty
        # So function should not be called at all
        call_count = 0
        
        async def count_calls():
            nonlocal call_count
            call_count += 1
            return "success"
        
        # With -1 retries, range(-1 + 1) = range(0) = no iterations
        result = await retry_with_backoff(count_calls, max_retries=-1)
        
        # Should not call the function and return None
        assert call_count == 0
        assert result is None
    
    @pytest.mark.asyncio
    async def test_zero_delay(self):
        """Test retry behavior with zero delay."""
        call_times = []
        
        async def track_timing():
            call_times.append(time.time())
            raise Exception("Zero delay test")
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            await retry_with_backoff(
                track_timing,
                max_retries=2,
                base_delay=0.0,
                jitter=False
            )
        
        total_time = time.time() - start_time
        # Should complete very quickly with zero delay
        assert total_time < 0.1
    
    @pytest.mark.asyncio
    async def test_very_large_delay(self):
        """Test retry behavior with very large delay."""
        async def failing_func():
            raise Exception("Large delay test")
        
        start_time = time.time()
        
        with pytest.raises(Exception):
            await retry_with_backoff(
                failing_func,
                max_retries=1,
                base_delay=1000.0,  # Very large delay
                max_delay=0.1,  # But capped low
                jitter=False
            )
        
        total_time = time.time() - start_time
        # Should be capped by max_delay
        assert total_time < 1.0
    
    def test_is_retryable_error_edge_cases(self):
        """Test is_retryable_error with edge cases."""
        # Error with both status and status_code
        error = Exception("Both status fields")
        error.status = 500
        error.status_code = 400
        # The function uses 'or' logic: getattr(error, 'status', None) or getattr(error, 'status_code', None)
        # Since status=500 is truthy, it will be used, making it retryable
        assert is_retryable_error(error) is True  # Uses status=500
        
        # Error with None status but has status_code
        error = Exception("None status")
        error.status = None
        error.status_code = 404
        assert is_retryable_error(error) is False  # Uses status_code=404
        
        # Error with None status_code
        error = Exception("None status_code")
        error.status_code = None
        assert is_retryable_error(error) is False


class TestConcurrency:
    """Test suite for concurrent retry operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_retries(self):
        """Test multiple concurrent retry operations."""
        call_counts = {"func1": 0, "func2": 0, "func3": 0}
        
        async def make_func(name, fail_count):
            async def func():
                call_counts[name] += 1
                if call_counts[name] <= fail_count:
                    raise Exception(f"{name} failure")
                return f"{name} success"
            return func
        
        func1 = await make_func("func1", 1)  # Fail once
        func2 = await make_func("func2", 2)  # Fail twice
        func3 = await make_func("func3", 0)  # Never fail
        
        # Run all concurrently
        tasks = [
            retry_with_backoff(func1, max_retries=3, base_delay=0.01),
            retry_with_backoff(func2, max_retries=3, base_delay=0.01),
            retry_with_backoff(func3, max_retries=3, base_delay=0.01)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert results == ["func1 success", "func2 success", "func3 success"]
        assert call_counts["func1"] == 2  # Failed once, succeeded on second
        assert call_counts["func2"] == 3  # Failed twice, succeeded on third
        assert call_counts["func3"] == 1  # Succeeded immediately


class TestPerformance:
    """Test suite for performance considerations."""
    
    @pytest.mark.asyncio
    async def test_many_fast_retries(self):
        """Test performance with many fast retries."""
        call_count = 0
        
        async def fast_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 10:  # Reduce number for faster testing
                raise Exception("Fast failure")
            return "finally succeeded"
        
        start_time = time.time()
        
        result = await retry_with_backoff(
            fast_failing,
            max_retries=20,
            base_delay=0.001,  # Very small delay
            jitter=False
        )
        
        elapsed = time.time() - start_time
        
        assert result == "finally succeeded"
        assert call_count == 10
        # Should complete reasonably quickly
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_decorator_overhead(self):
        """Test that decorator doesn't add significant overhead."""
        @retry(max_retries=0, base_delay=0.0)
        async def simple_func():
            return "immediate"
        
        # Time many calls
        start_time = time.time()
        
        for _ in range(100):
            result = await simple_func()
            assert result == "immediate"
        
        elapsed = time.time() - start_time
        
        # Should be very fast with no retries
        assert elapsed < 0.5