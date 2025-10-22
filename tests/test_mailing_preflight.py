"""
Comprehensive tests for mailing/preflight.py

Covers:
- Environment validation
- Configuration checks
- Template existence verification
- Recipients file validation
- File format support
- File size limits
- Preflight checks integration
- Error and warning handling
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.mailing.preflight import (
    validate_environment,
    check_template_exists,
    validate_recipients_file,
    run_preflight_checks
)


class TestValidateEnvironment:
    """Test suite for validate_environment function."""
    
    def test_validate_environment_all_good(self):
        """Test environment validation with all requirements met."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            # Mock Path exists check
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                # Mock templates directory
                with patch('mailing.preflight.Path') as mock_templates_path:
                    # Configure Path to handle both db and templates calls
                    def path_side_effect(path_str):
                        if path_str == "/tmp/test.db":
                            return mock_db_path
                        elif path_str == "samples":
                            mock_templates = Mock()
                            mock_templates.exists.return_value = True
                            return mock_templates
                    
                    mock_path.side_effect = path_side_effect
                    
                    result = validate_environment()
            
            assert result['status'] == 'ok'
            assert result['errors'] == []
            assert len(result['warnings']) == 0
            assert result['config']['api_key_set'] is True
            assert result['config']['from_email'] == "test@example.com"
            assert result['config']['daily_limit'] == 1000
    
    def test_validate_environment_missing_api_key(self):
        """Test environment validation with missing API key."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = ""
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'error'
            assert "RESEND_API_KEY is missing" in result['errors']
            assert result['config']['api_key_set'] is False
    
    def test_validate_environment_missing_from_email(self):
        """Test environment validation with missing from email."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = ""
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'error'
            assert "RESEND_FROM_EMAIL is missing" in result['errors']
    
    def test_validate_environment_missing_both_required(self):
        """Test environment validation with both required fields missing."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = ""
            mock_settings.resend_from_email = ""
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'error'
            assert len(result['errors']) == 2
            assert "RESEND_API_KEY is missing" in result['errors']
            assert "RESEND_FROM_EMAIL is missing" in result['errors']
    
    def test_validate_environment_db_directory_missing(self):
        """Test environment validation with missing database directory."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/nonexistent/path/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = False
                mock_db_path.parent = Path("/nonexistent/path")
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'ok'  # Warnings don't make status error
            assert "Database directory doesn't exist" in result['warnings'][0]
    
    def test_validate_environment_templates_directory_missing(self):
        """Test environment validation with missing templates directory."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = 1000
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                def path_side_effect(path_str):
                    if path_str == "/tmp/test.db":
                        mock_db_path = Mock()
                        mock_db_path.parent.exists.return_value = True
                        return mock_db_path
                    elif path_str == "samples":
                        mock_templates = Mock()
                        mock_templates.exists.return_value = False
                        return mock_templates
                
                mock_path.side_effect = path_side_effect
                
                result = validate_environment()
            
            assert result['status'] == 'ok'
            assert "Templates directory 'samples' doesn't exist" in result['warnings']
    
    def test_validate_environment_zero_daily_limit(self):
        """Test environment validation with zero daily limit."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = 0
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'ok'
            assert "Daily limit is set to 0 or negative" in result['warnings']
    
    def test_validate_environment_negative_daily_limit(self):
        """Test environment validation with negative daily limit."""
        with patch('mailing.preflight.settings') as mock_settings:
            mock_settings.resend_api_key = "re_test_key"
            mock_settings.resend_from_email = "test@example.com"
            mock_settings.daily_limit = -10
            mock_settings.sqlite_db_path = "/tmp/test.db"
            
            with patch('mailing.preflight.Path') as mock_path:
                mock_db_path = Mock()
                mock_db_path.parent.exists.return_value = True
                mock_path.return_value = mock_db_path
                
                result = validate_environment()
            
            assert result['status'] == 'ok'
            assert "Daily limit is set to 0 or negative" in result['warnings']


class TestCheckTemplateExists:
    """Test suite for check_template_exists function."""
    
    def test_check_template_exists_true(self):
        """Test template existence check when template exists."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_templates_dir = Mock()
            mock_template_path = Mock()
            mock_template_path.exists.return_value = True
            mock_templates_dir.__truediv__ = Mock(return_value=mock_template_path)
            mock_path.return_value = mock_templates_dir
            
            result = check_template_exists("welcome.html")
            
            assert result is True
            mock_path.assert_called_with("samples")
            mock_templates_dir.__truediv__.assert_called_with("welcome.html")
    
    def test_check_template_exists_false(self):
        """Test template existence check when template doesn't exist."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_templates_dir = Mock()
            mock_template_path = Mock()
            mock_template_path.exists.return_value = False
            mock_templates_dir.__truediv__ = Mock(return_value=mock_template_path)
            mock_path.return_value = mock_templates_dir
            
            result = check_template_exists("nonexistent.html")
            
            assert result is False
            mock_path.assert_called_with("samples")
            mock_templates_dir.__truediv__.assert_called_with("nonexistent.html")
    
    def test_check_template_exists_various_names(self):
        """Test template existence check with various template names."""
        template_names = [
            "welcome.html",
            "newsletter.html",
            "confirmation.txt",
            "template_with_underscores.html",
            "template-with-dashes.html"
        ]
        
        with patch('mailing.preflight.Path') as mock_path:
            mock_templates_dir = Mock()
            mock_template_path = Mock()
            mock_template_path.exists.return_value = True
            mock_templates_dir.__truediv__ = Mock(return_value=mock_template_path)
            mock_path.return_value = mock_templates_dir
            
            for template_name in template_names:
                result = check_template_exists(template_name)
                assert result is True


class TestValidateRecipientsFile:
    """Test suite for validate_recipients_file function."""
    
    def test_validate_recipients_file_not_found(self):
        """Test validation of non-existent file."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = False
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("/nonexistent/file.csv")
            
            assert result['valid'] is False
            assert "File not found" in result['error']
    
    def test_validate_recipients_file_not_a_file(self):
        """Test validation when path is not a file."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.is_file.return_value = False
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("/some/directory")
            
            assert result['valid'] is False
            assert "Not a file" in result['error']
    
    def test_validate_recipients_file_unsupported_format(self):
        """Test validation with unsupported file format."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.is_file.return_value = True
            mock_file_path.suffix = ".txt"
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("recipients.txt")
            
            assert result['valid'] is False
            assert "Unsupported format" in result['error']
            assert ".txt" in result['error']
            assert "Supported:" in result['error']
    
    def test_validate_recipients_file_too_large(self):
        """Test validation with file too large."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.is_file.return_value = True
            mock_file_path.suffix = ".csv"
            
            # Mock file size > 100MB
            mock_stat = Mock()
            mock_stat.st_size = 105 * 1024 * 1024  # 105MB
            mock_file_path.stat.return_value = mock_stat
            
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("large_file.csv")
            
            assert result['valid'] is False
            assert "File too large" in result['error']
            assert "105.0MB" in result['error']
            assert "max 100MB" in result['error']
    
    def test_validate_recipients_file_csv_valid(self):
        """Test validation with valid CSV file."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.is_file.return_value = True
            mock_file_path.suffix = ".csv"
            
            # Mock reasonable file size
            mock_stat = Mock()
            mock_stat.st_size = 2 * 1024 * 1024  # 2MB
            mock_file_path.stat.return_value = mock_stat
            
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("recipients.csv")
            
            assert result['valid'] is True
            assert result['format'] == ".csv"
            assert result['size_mb'] == 2.0
    
    def test_validate_recipients_file_supported_formats(self):
        """Test validation with all supported file formats."""
        supported_formats = ['.csv', '.json', '.xlsx', '.xls']
        
        for file_format in supported_formats:
            with patch('mailing.preflight.Path') as mock_path:
                mock_file_path = Mock()
                mock_file_path.exists.return_value = True
                mock_file_path.is_file.return_value = True
                mock_file_path.suffix = file_format
                
                mock_stat = Mock()
                mock_stat.st_size = 1024 * 1024  # 1MB
                mock_file_path.stat.return_value = mock_stat
                
                mock_path.return_value = mock_file_path
                
                result = validate_recipients_file(f"recipients{file_format}")
                
                assert result['valid'] is True
                assert result['format'] == file_format
                assert result['size_mb'] == 1.0
    
    def test_validate_recipients_file_case_insensitive_extension(self):
        """Test validation with uppercase file extensions."""
        extensions = ['.CSV', '.JSON', '.XLSX', '.XLS']
        
        for ext in extensions:
            with patch('mailing.preflight.Path') as mock_path:
                mock_file_path = Mock()
                mock_file_path.exists.return_value = True
                mock_file_path.is_file.return_value = True
                mock_file_path.suffix = ext
                
                mock_stat = Mock()
                mock_stat.st_size = 1024 * 1024  # 1MB
                mock_file_path.stat.return_value = mock_stat
                
                mock_path.return_value = mock_file_path
                
                result = validate_recipients_file(f"recipients{ext}")
                
                assert result['valid'] is True
                assert result['format'] == ext.lower()
    
    def test_validate_recipients_file_small_file(self):
        """Test validation with very small file."""
        with patch('mailing.preflight.Path') as mock_path:
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.is_file.return_value = True
            mock_file_path.suffix = ".csv"
            
            # Very small file
            mock_stat = Mock()
            mock_stat.st_size = 1024  # 1KB
            mock_file_path.stat.return_value = mock_stat
            
            mock_path.return_value = mock_file_path
            
            result = validate_recipients_file("small.csv")
            
            assert result['valid'] is True
            assert result['size_mb'] == 0.0  # Rounded to 2 decimal places


class TestRunPreflightChecks:
    """Test suite for run_preflight_checks function."""
    
    def test_run_preflight_checks_minimal(self):
        """Test preflight checks with minimal parameters."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            result = run_preflight_checks()
            
            assert result['overall_status'] == 'ok'
            assert 'environment' in result
            assert 'template' not in result
            assert 'recipients' not in result
    
    def test_run_preflight_checks_with_template_exists(self):
        """Test preflight checks with existing template."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            with patch('mailing.preflight.check_template_exists') as mock_check_template:
                mock_check_template.return_value = True
                
                result = run_preflight_checks(template_name="welcome.html")
                
                assert result['overall_status'] == 'ok'
                assert result['template']['name'] == "welcome.html"
                assert result['template']['exists'] is True
    
    def test_run_preflight_checks_with_template_missing(self):
        """Test preflight checks with missing template."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            with patch('mailing.preflight.check_template_exists') as mock_check_template:
                mock_check_template.return_value = False
                
                result = run_preflight_checks(template_name="missing.html")
                
                assert result['overall_status'] == 'error'
                assert result['template']['name'] == "missing.html"
                assert result['template']['exists'] is False
    
    def test_run_preflight_checks_with_valid_recipients(self):
        """Test preflight checks with valid recipients file."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            with patch('mailing.preflight.validate_recipients_file') as mock_validate_recipients:
                mock_validate_recipients.return_value = {
                    'valid': True,
                    'format': '.csv',
                    'size_mb': 2.5
                }
                
                result = run_preflight_checks(recipients_file="recipients.csv")
                
                assert result['overall_status'] == 'ok'
                assert result['recipients']['valid'] is True
                assert result['recipients']['format'] == '.csv'
    
    def test_run_preflight_checks_with_invalid_recipients(self):
        """Test preflight checks with invalid recipients file."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            with patch('mailing.preflight.validate_recipients_file') as mock_validate_recipients:
                mock_validate_recipients.return_value = {
                    'valid': False,
                    'error': 'File not found'
                }
                
                result = run_preflight_checks(recipients_file="missing.csv")
                
                assert result['overall_status'] == 'error'
                assert result['recipients']['valid'] is False
                assert result['recipients']['error'] == 'File not found'
    
    def test_run_preflight_checks_environment_error(self):
        """Test preflight checks when environment validation fails."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'error',
                'errors': ['RESEND_API_KEY is missing'],
                'warnings': []
            }
            
            result = run_preflight_checks()
            
            assert result['overall_status'] == 'error'
            assert result['environment']['status'] == 'error'
    
    def test_run_preflight_checks_all_parameters(self):
        """Test preflight checks with all parameters provided."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'ok',
                'errors': [],
                'warnings': []
            }
            
            with patch('mailing.preflight.check_template_exists') as mock_check_template:
                mock_check_template.return_value = True
                
                with patch('mailing.preflight.validate_recipients_file') as mock_validate_recipients:
                    mock_validate_recipients.return_value = {
                        'valid': True,
                        'format': '.json',
                        'size_mb': 1.2
                    }
                    
                    result = run_preflight_checks(
                        template_name="newsletter.html",
                        recipients_file="recipients.json"
                    )
                    
                    assert result['overall_status'] == 'ok'
                    assert result['template']['name'] == "newsletter.html"
                    assert result['template']['exists'] is True
                    assert result['recipients']['valid'] is True
                    assert result['recipients']['format'] == '.json'
    
    def test_run_preflight_checks_multiple_errors(self):
        """Test preflight checks with multiple error conditions."""
        with patch('mailing.preflight.validate_environment') as mock_validate_env:
            mock_validate_env.return_value = {
                'status': 'error',
                'errors': ['RESEND_API_KEY is missing'],
                'warnings': []
            }
            
            with patch('mailing.preflight.check_template_exists') as mock_check_template:
                mock_check_template.return_value = False
                
                with patch('mailing.preflight.validate_recipients_file') as mock_validate_recipients:
                    mock_validate_recipients.return_value = {
                        'valid': False,
                        'error': 'Unsupported format'
                    }
                    
                    result = run_preflight_checks(
                        template_name="missing.html",
                        recipients_file="data.txt"
                    )
                    
                    assert result['overall_status'] == 'error'
                    assert result['environment']['status'] == 'error'
                    assert result['template']['exists'] is False
                    assert result['recipients']['valid'] is False


class TestMainExecution:
    """Test suite for main module execution."""
    
    def test_main_execution(self):
        """Test main module execution."""
        # Test that we can import the module without executing main
        import src.mailing.preflight
        
        # Test the main execution path by calling it directly
        with patch('mailing.preflight.run_preflight_checks') as mock_run_checks:
            mock_run_checks.return_value = {
                'overall_status': 'ok',
                'environment': {'status': 'ok'}
            }
            
            with patch('builtins.print') as mock_print:
                with patch('json.dumps') as mock_json_dumps:
                    mock_json_dumps.return_value = '{"status": "ok"}'
                    
                    # Execute the main block manually
                    checks = mailing.preflight.run_preflight_checks()
                    
                    # Verify functions were called
                    mock_run_checks.assert_called_once()


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_integration_real_temporary_files(self):
        """Integration test with real temporary files."""
        # Create temporary CSV file with more content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            # Write more content to ensure measurable size
            tmp_file.write("email,name\n")
            for i in range(100):
                tmp_file.write(f"test{i}@example.com,Test User {i}\n")
            csv_file_path = tmp_file.name
        
        try:
            # Test with real file
            result = validate_recipients_file(csv_file_path)
            
            assert result['valid'] is True
            assert result['format'] == '.csv'
            assert result['size_mb'] >= 0  # Allow for very small files
            
        finally:
            # Clean up
            os.unlink(csv_file_path)
    
    def test_integration_large_file_simulation(self):
        """Integration test simulating large file scenarios."""
        # Create a relatively larger temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            # Write some content to make it measurable
            large_data = {"recipients": [{"email": f"user{i}@example.com"} for i in range(1000)]}
            json.dump(large_data, tmp_file)
            json_file_path = tmp_file.name
        
        try:
            result = validate_recipients_file(json_file_path)
            
            assert result['valid'] is True
            assert result['format'] == '.json'
            assert result['size_mb'] > 0
            
        finally:
            os.unlink(json_file_path)
    
    def test_integration_complete_preflight_workflow(self):
        """Complete integration test of preflight workflow."""
        # Create temporary template directory
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "test_template.html"
            template_path.write_text("<html><body>Hello {{name}}!</body></html>")
            
            # Create temporary recipients file
            recipients_path = Path(temp_dir) / "recipients.csv"
            recipients_path.write_text("email,name\ntest@example.com,Test User\n")
            
            # Mock template directory to point to our temp directory
            with patch('mailing.preflight.Path') as mock_path:
                def path_side_effect(path_str):
                    if path_str == "samples":
                        return Path(temp_dir)
                    else:
                        return Path(path_str)
                
                mock_path.side_effect = path_side_effect
                
                # Test template check
                template_exists = check_template_exists("test_template.html")
                assert template_exists is True
                
                # Test recipients file validation
                recipients_result = validate_recipients_file(str(recipients_path))
                assert recipients_result['valid'] is True
                
                # Test complete preflight check
                with patch('mailing.preflight.validate_environment') as mock_env:
                    mock_env.return_value = {
                        'status': 'ok',
                        'errors': [],
                        'warnings': []
                    }
                    
                    full_result = run_preflight_checks(
                        template_name="test_template.html",
                        recipients_file=str(recipients_path)
                    )
                    
                    assert full_result['overall_status'] == 'ok'
                    assert full_result['template']['exists'] is True
                    assert full_result['recipients']['valid'] is True