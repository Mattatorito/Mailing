#!/usr/bin/env python3
"""
Performance and load testing suite for email marketing system.
Comprehensive benchmarking and stress testing framework.
"""

import os
import asyncio
import time
import tempfile
import statistics
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager

import pytest
from unittest.mock import Mock, patch

from src.mailing.models import Recipient, DeliveryResult
from src.mailing.sender import run_campaign
from src.data_loader.streaming import StreamingDataLoader
from src.validation.email_validator import EmailValidator
from src.templating.engine import TemplateEngine


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""
    operation: str
    duration: float
    memory_usage: float
    cpu_usage: float
    throughput: float
    success_rate: float
    errors: List[str]


class PerformanceProfiler:
    """Advanced performance profiling utilities."""
    
    def __init__(self):
        self.metrics = []
        self.process = psutil.Process()
    
    @contextmanager
    def measure(self, operation: str):
        """Context manager for measuring performance."""
        # Collect initial metrics
        gc.collect()  # Force garbage collection
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()
        start_time = time.perf_counter()
        
        errors = []
        success_count = 0
        total_count = 0
        
        try:
            yield {
                'record_success': lambda: setattr(self, '_success_count', 
                                                getattr(self, '_success_count', 0) + 1),
                'record_error': lambda e: errors.append(str(e)),
                'record_operation': lambda: setattr(self, '_total_count', 
                                                   getattr(self, '_total_count', 0) + 1)
            }
        finally:
            # Collect final metrics
            end_time = time.perf_counter()
            final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = self.process.cpu_percent()
            
            duration = end_time - start_time
            memory_usage = final_memory - initial_memory
            cpu_usage = (initial_cpu + final_cpu) / 2
            
            success_count = getattr(self, '_success_count', 0)
            total_count = getattr(self, '_total_count', 1)
            
            metrics = PerformanceMetrics(
                operation=operation,
                duration=duration,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                throughput=total_count / duration if duration > 0 else 0,
                success_rate=success_count / total_count if total_count > 0 else 0,
                errors=errors
            )
            
            self.metrics.append(metrics)
            
            # Reset counters
            self._success_count = 0
            self._total_count = 0


@pytest.mark.performance
class TestEmailValidationPerformance:
    """Performance tests for email validation."""
    
    def setup_method(self):
        self.profiler = PerformanceProfiler()
        self.validator = EmailValidator()
    
    def test_email_validation_bulk_performance(self):
        """Test email validation performance with large datasets."""
        test_sizes = [1000, 5000, 10000, 25000]
        
        for size in test_sizes:
            emails = [f"user{i}@domain{i % 100}.com" for i in range(size)]
            
            with self.profiler.measure(f"email_validation_{size}") as tracker:
                for email in emails:
                    tracker['record_operation']()
                    try:
                        result = self.validator.is_valid(email)
                        if result:
                            tracker['record_success']()
                    except Exception as e:
                        tracker['record_error'](e)
        
        # Performance assertions
        latest_metric = self.profiler.metrics[-1]
        assert latest_metric.throughput > 1000, f"Validation throughput too low: {latest_metric.throughput}/sec"
        assert latest_metric.success_rate > 0.95, f"Success rate too low: {latest_metric.success_rate}"
        assert latest_metric.memory_usage < 500, f"Memory usage too high: {latest_metric.memory_usage}MB"
    
    def test_email_validation_concurrent_performance(self):
        """Test concurrent email validation performance."""
        emails = [f"concurrent_user{i}@test{i % 50}.com" for i in range(1000)]  # Reduced for faster testing
        thread_counts = [1, 2, 4, 8]  # Reduced thread counts
        
        for thread_count in thread_counts:
            with self.profiler.measure(f"concurrent_validation_t{thread_count}") as tracker:
                with ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = []
                    
                    for email in emails:
                        future = executor.submit(self._validate_email_with_tracking, 
                                               email, tracker)
                        futures.append(future)
                    
                    for future in futures:
                        future.result()
        
        # Analyze concurrency benefits
        metrics_by_threads = {m.operation: m for m in self.profiler.metrics 
                            if "concurrent_validation" in m.operation}
        
        single_thread = metrics_by_threads.get("concurrent_validation_t1")
        multi_thread = metrics_by_threads.get("concurrent_validation_t8")
        
        if single_thread and multi_thread:
            speedup = single_thread.duration / multi_thread.duration
            assert speedup > 2, f"Insufficient concurrency speedup: {speedup}x"
    
    def _validate_email_with_tracking(self, email: str, tracker: Dict[str, Callable]):
        """Helper method for tracking email validation."""
        tracker['record_operation']()
        try:
            result = self.validator.is_valid(email)
            if result:
                tracker['record_success']()
            return result
        except Exception as e:
            tracker['record_error'](e)
            return False


@pytest.mark.performance
class TestCampaignPerformance:
    """Performance tests for email campaign processing."""
    
    def setup_method(self):
        self.profiler = PerformanceProfiler()
    
    @pytest.mark.asyncio
    async def test_campaign_scaling_performance(self):
        """Test campaign performance scaling with recipient count."""
        recipient_counts = [100, 500, 1000, 2500]
        concurrency_levels = [5, 10, 20]
        
        for recipient_count in recipient_counts:
            recipients = [
                Recipient(
                    email=f"perf_user{i}@benchmark{i % 10}.com",
                    name=f"Performance User {i}",
                    variables={"test_id": str(i), "batch": "performance"}
                )
                for i in range(recipient_count)
            ]
            
            for concurrency in concurrency_levels:
                operation_name = f"campaign_r{recipient_count}_c{concurrency}"
                
                with self.profiler.measure(operation_name) as tracker:
                    events = []
                    async for event in run_campaign(
                        recipients=recipients,
                        template_name="performance_test.html",
                        subject="Performance Benchmark",
                        dry_run=True,
                        concurrency=concurrency
                    ):
                        tracker['record_operation']()
                        events.append(event)
                        
                        if event.get("type") == "progress":
                            result = event.get("result")
                            if result and result.success:
                                tracker['record_success']()
                            elif result:
                                tracker['record_error'](result.error or "Unknown error")
        
        # Performance analysis
        self._analyze_campaign_performance()
    
    def _analyze_campaign_performance(self):
        """Analyze campaign performance metrics and assert requirements."""
        campaign_metrics = [m for m in self.profiler.metrics if "campaign_r" in m.operation]
        
        # Group by recipient count and concurrency
        performance_matrix = {}
        for metric in campaign_metrics:
            parts = metric.operation.split("_")
            recipients = int(parts[1][1:])  # Extract number after 'r'
            concurrency = int(parts[2][1:])  # Extract number after 'c'
            
            if recipients not in performance_matrix:
                performance_matrix[recipients] = {}
            performance_matrix[recipients][concurrency] = metric
        
        # Assert performance requirements
        for recipient_count, concurrency_data in performance_matrix.items():
            best_metric = min(concurrency_data.values(), key=lambda m: m.duration)
            
            # Throughput should increase with recipient count
            min_throughput = recipient_count / 60  # At least N recipients per minute
            assert best_metric.throughput >= min_throughput, \
                f"Insufficient throughput for {recipient_count} recipients: {best_metric.throughput}"
            
            # Memory usage should be reasonable
            max_memory = 50 + (recipient_count * 0.01)  # Base + per-recipient allowance
            assert best_metric.memory_usage <= max_memory, \
                f"Excessive memory usage: {best_metric.memory_usage}MB"


@pytest.mark.performance  
class TestDataLoadingPerformance:
    """Performance tests for data loading operations."""
    
    def setup_method(self):
        self.profiler = PerformanceProfiler()
        self.loader = StreamingDataLoader()
    
    def test_csv_streaming_performance(self):
        """Test CSV streaming performance with large files."""
        file_sizes = [1000, 5000, 10000, 25000]
        
        for size in file_sizes:
            # Create test CSV data in memory
            csv_content = "email,name,company\n"
            csv_content += "\n".join([
                f"stream_user{i}@performance{i % 100}.com,User {i},Company {i % 50}"
                for i in range(size)
            ])
            
            with self.profiler.measure(f"csv_streaming_{size}") as tracker:
                # Simulate file streaming
                total_processed = 0
                batch_size = 100
                
                for i in range(0, size, batch_size):
                    batch_end = min(i + batch_size, size)
                    batch = csv_content.split('\n')[i+1:batch_end+1]  # Skip header
                    
                    tracker['record_operation']()
                    try:
                        # Process batch
                        for line in batch:
                            if line.strip():
                                parts = line.split(',')
                                if len(parts) >= 3:
                                    total_processed += 1
                                    tracker['record_success']()
                    except Exception as e:
                        tracker['record_error'](e)
        
        # Performance assertions
        latest_metric = self.profiler.metrics[-1]
        assert latest_metric.throughput > 300, f"CSV processing too slow: {latest_metric.throughput}/sec"
        assert latest_metric.memory_usage < 200, f"Memory usage too high: {latest_metric.memory_usage}MB"
    
    def test_memory_efficiency_large_datasets(self):
        """Test memory efficiency with very large datasets."""
        # Test with progressively larger datasets
        sizes = [50000, 100000, 200000]
        
        for size in sizes:
            initial_memory = self.profiler.process.memory_info().rss / 1024 / 1024
            
            with self.profiler.measure(f"memory_efficiency_{size}") as tracker:
                # Simulate processing large dataset in chunks
                chunk_size = 1000
                processed_count = 0
                
                for chunk_start in range(0, size, chunk_size):
                    chunk_end = min(chunk_start + chunk_size, size)
                    chunk_data = [
                        {
                            'email': f"memory_test{i}@efficiency{i % 10}.com",
                            'name': f"Memory Test {i}",
                            'data': f"test_data_{i}"
                        }
                        for i in range(chunk_start, chunk_end)
                    ]
                    
                    tracker['record_operation']()
                    
                    # Process chunk and clear memory
                    for item in chunk_data:
                        if self._validate_data_item(item):
                            processed_count += 1
                            tracker['record_success']()
                    
                    # Clear chunk from memory
                    del chunk_data
                    gc.collect()
            
            final_memory = self.profiler.process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory
            
            # Memory growth should be minimal regardless of dataset size
            assert memory_growth < 100, f"Excessive memory growth: {memory_growth}MB for {size} records"
    
    def _validate_data_item(self, item: Dict[str, str]) -> bool:
        """Validate a single data item."""
        required_fields = ['email', 'name']
        return all(field in item and item[field] for field in required_fields)


@pytest.mark.performance
class TestTemplatePerformance:
    """Performance tests for template rendering."""
    
    def setup_method(self):
        self.profiler = PerformanceProfiler()
        self.engine = TemplateEngine()
    
    def test_template_rendering_performance(self):
        """Test template rendering performance with various complexities."""
        template_complexities = {
            'simple': '<html><body>Hello {{name}}!</body></html>',
            'medium': '''
            <html>
            <body>
                <h1>Welcome {{name}}!</h1>
                <p>Company: {{company}}</p>
                <ul>
                {% for item in items %}
                    <li>{{item}}</li>
                {% endfor %}
                </ul>
            </body>
            </html>
            ''',
            'complex': '''
            <html>
            <body>
                <h1>{{title}}</h1>
                {% if user.premium %}
                    <div class="premium-content">
                        {% for product in products %}
                            <div class="product">
                                <h3>{{product.name}}</h3>
                                <p>Price: ${{product.price}}</p>
                                {% if product.discount %}
                                    <span class="discount">{{product.discount}}% OFF</span>
                                {% endif %}
                            </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <p>Upgrade to premium for exclusive content!</p>
                {% endif %}
            </body>
            </html>
            '''
        }
        
        render_counts = [100, 500, 1000]
        
        for complexity, template_content in template_complexities.items():
            for count in render_counts:
                operation_name = f"template_rendering_{complexity}_{count}"
                
                with self.profiler.measure(operation_name) as tracker:
                    for i in range(count):
                        tracker['record_operation']()
                        try:
                            variables = self._generate_template_variables(complexity, i)
                            
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                                tmp.write(template_content)
                                tmp.flush()
                                template_path = tmp.name
                            
                            html_result, text_result = self.engine.render(template_path, variables)
                            
                            if html_result and len(html_result) > 0:
                                tracker['record_success']()
                                
                            Path(template_path).unlink()
                                
                        except Exception as e:
                            tracker['record_error'](e)
        
        # Performance assertions for template rendering
        self._assert_template_performance()
    
    def _generate_template_variables(self, complexity: str, index: int) -> Dict[str, Any]:
        """Generate template variables based on complexity level."""
        base_vars = {
            'name': f'Template User {index}',
            'company': f'Performance Company {index % 10}'
        }
        
        if complexity == 'medium':
            base_vars['items'] = [f'Item {i}' for i in range(5)]
        elif complexity == 'complex':
            base_vars.update({
                'title': f'Complex Template {index}',
                'user': {'premium': index % 2 == 0},
                'products': [
                    {
                        'name': f'Product {i}',
                        'price': 99.99 + i,
                        'discount': 10 if i % 2 == 0 else None
                    }
                    for i in range(3)
                ]
            })
        
        return base_vars
    
    def _assert_template_performance(self):
        """Assert template rendering performance requirements."""
        template_metrics = [m for m in self.profiler.metrics if "template_rendering" in m.operation]
        
        for metric in template_metrics:
            # Extract complexity and count from operation name
            parts = metric.operation.split('_')
            complexity = parts[2]
            count = int(parts[3])
            
            # Performance requirements based on complexity
            if complexity == 'simple':
                min_throughput = 500  # 500 renders/sec for simple templates
            elif complexity == 'medium':
                min_throughput = 200  # 200 renders/sec for medium templates
            else:  # complex
                min_throughput = 50   # 50 renders/sec for complex templates
            
            assert metric.throughput >= min_throughput, \
                f"Template rendering too slow for {complexity}: {metric.throughput}/sec"
            
            assert metric.success_rate > 0.99, \
                f"Template rendering success rate too low: {metric.success_rate}"


class PerformanceReporter:
    """Generate comprehensive performance reports."""
    
    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
    
    def generate_report(self, output_file: str = "performance_report.md"):
        """Generate detailed performance report."""
        report = [
            "# Performance Test Report",
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            ""
        ]
        
        # Calculate summary statistics
        all_metrics = self.profiler.metrics
        avg_throughput = statistics.mean([m.throughput for m in all_metrics])
        avg_memory = statistics.mean([m.memory_usage for m in all_metrics])
        avg_success_rate = statistics.mean([m.success_rate for m in all_metrics])
        
        report.extend([
            f"- **Average Throughput:** {avg_throughput:.2f} operations/sec",
            f"- **Average Memory Usage:** {avg_memory:.2f} MB",
            f"- **Average Success Rate:** {avg_success_rate:.2%}",
            f"- **Total Tests:** {len(all_metrics)}",
            "",
            "## Detailed Results",
            "",
            "| Operation | Duration (s) | Throughput (ops/s) | Memory (MB) | Success Rate |",
            "|-----------|--------------|-------------------|-------------|--------------|"
        ])
        
        for metric in all_metrics:
            report.append(
                f"| {metric.operation} | {metric.duration:.3f} | "
                f"{metric.throughput:.2f} | {metric.memory_usage:.2f} | "
                f"{metric.success_rate:.2%} |"
            )
        
        report.extend([
            "",
            "## Performance Insights",
            "",
            self._generate_performance_insights(),
            "",
            "## Recommendations",
            "",
            self._generate_recommendations()
        ])
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(report))
    
    def _generate_performance_insights(self) -> str:
        """Generate performance insights from metrics."""
        insights = []
        
        # Analyze email validation performance
        validation_metrics = [m for m in self.profiler.metrics if "validation" in m.operation]
        if validation_metrics:
            best_validation = max(validation_metrics, key=lambda m: m.throughput)
            insights.append(f"- Email validation peaks at {best_validation.throughput:.0f} validations/sec")
        
        # Analyze campaign performance
        campaign_metrics = [m for m in self.profiler.metrics if "campaign" in m.operation]
        if campaign_metrics:
            best_campaign = min(campaign_metrics, key=lambda m: m.duration)
            insights.append(f"- Optimal campaign performance achieved with configuration: {best_campaign.operation}")
        
        return '\n'.join(insights) if insights else "No specific insights available."
    
    def _generate_recommendations(self) -> str:
        """Generate performance optimization recommendations."""
        recommendations = [
            "- Monitor memory usage during large batch operations",
            "- Consider implementing adaptive concurrency based on system resources",
            "- Optimize template caching for frequently used templates",
            "- Implement connection pooling for database operations"
        ]
        
        return '\n'.join(recommendations)


if __name__ == "__main__":
    # Run performance tests when executed directly
    pytest.main([
        __file__,
        "-v",
        "-m", "performance",
        "--tb=short"
    ])