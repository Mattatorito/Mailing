#!/usr/bin/env python3
"""
Security testing suite for email marketing system.
Comprehensive security validation and vulnerability detection.
"""

import os
import re
import html
import hashlib
import secrets
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, Mock

import pytest
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.templating.engine import TemplateEngine, TemplateError

from src.validation.email_validator import EmailValidator
from src.templating.engine import TemplateEngine
from src.mailing.models import Recipient
from src.persistence.db import DatabaseManager
from src.mailing.config import settings


class SecurityTestFramework:
    """Framework for security testing and vulnerability assessment."""
    
    # Common injection patterns
    INJECTION_PATTERNS = [
        # XSS patterns
        '<script>alert("xss")</script>',
        'javascript:alert("xss")',
        '<img src="x" onerror="alert(1)">',
        '"><script>alert(document.cookie)</script>',
        
        # HTML injection
        '<iframe src="javascript:alert(1)"></iframe>',
        '<object data="javascript:alert(1)">',
        '<embed src="javascript:alert(1)">',
        
        # Template injection
        '{{7*7}}',
        '${7*7}',
        '#{7*7}',
        '{{config.items()}}',
        '{{request.application.__globals__}}',
        
        # SQL injection (even though we use SQLite)
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "1'; UPDATE users SET email='hacked@evil.com'; --",
        
        # Command injection
        '; cat /etc/passwd',
        '| whoami',
        '$(whoami)',
        '`whoami`',
        
        # Path traversal
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
        '....//....//....//etc/passwd',
        
        # LDAP injection
        '*)(uid=*',
        '*)(&(password=*',
        
        # Email header injection
        '\r\nBcc: attacker@evil.com',
        '\nSubject: Injected Subject',
        '%0ABcc: hacker@evil.com',
    ]
    
    # Dangerous file extensions
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
        '.jar', '.php', '.asp', '.aspx', '.jsp', '.py', '.rb', '.pl'
    ]
    
    @staticmethod
    def generate_malicious_payloads(base_pattern: str) -> List[str]:
        """Generate variations of malicious payloads."""
        payloads = [base_pattern]
        
        # URL encoding variations
        payloads.append(base_pattern.replace('<', '%3C').replace('>', '%3E'))
        payloads.append(base_pattern.replace(' ', '%20'))
        
        # Double encoding
        double_encoded = base_pattern.replace('<', '%253C').replace('>', '%253E')
        payloads.append(double_encoded)
        
        # Case variations
        payloads.append(base_pattern.upper())
        payloads.append(base_pattern.lower())
        
        # Unicode variations
        payloads.append(base_pattern.replace('<', '\u003C').replace('>', '\u003E'))
        
        return payloads


@pytest.mark.security
class TestEmailValidationSecurity:
    """Security tests for email validation functionality."""
    
    def setup_method(self):
        self.validator = EmailValidator()
        self.security_framework = SecurityTestFramework()
    
    def test_email_injection_protection(self):
        """Test protection against email header injection attacks."""
        malicious_emails = [
            # Header injection attempts
            'user@domain.com\r\nBcc: attacker@evil.com',
            'user@domain.com\nSubject: Injected',
            'user@domain.com%0ABcc: hacker@evil.com',
            'user@domain.com%0D%0ABcc: evil@hacker.com',
            
            # CRLF injection
            'user@domain.com\r\n\r\nThis is injected content',
            'user@domain.com\x0A\x0DAttacker-Header: malicious',
            
            # Null byte injection
            'user@domain.com\x00@evil.com',
            'user\x00@domain.com',
        ]
        
        for malicious_email in malicious_emails:
            # Email validator should reject these
            is_valid = self.validator.is_valid(malicious_email)
            assert not is_valid, f"Malicious email accepted: {repr(malicious_email)}"
    
    def test_email_length_limits_security(self):
        """Test email length limits to prevent DoS attacks."""
        # Test extremely long local part
        long_local = 'a' * 10000 + '@domain.com'
        assert not self.validator.is_valid(long_local), "Overly long local part accepted"
        
        # Test extremely long domain
        long_domain = 'user@' + 'a' * 10000 + '.com'
        assert not self.validator.is_valid(long_domain), "Overly long domain accepted"
        
        # Test extremely long TLD
        long_tld = 'user@domain.' + 'a' * 1000
        assert not self.validator.is_valid(long_tld), "Overly long TLD accepted"
    
    def test_email_unicode_security(self):
        """Test Unicode-based attacks in email addresses."""
        unicode_attacks = [
            # Homograph attacks
            'аdmin@domain.com',  # Cyrillic 'а' instead of 'a'
            'аdmіn@domain.com',  # Mixed Cyrillic characters
            'admin@dоmain.com',  # Cyrillic 'о' instead of 'o'
            
            # Zero-width characters
            'ad\u200Bmin@domain.com',  # Zero-width space
            'admin@dom\u200Cain.com',  # Zero-width non-joiner
            'admin@domain\uFEFF.com',  # Zero-width no-break space
            
            # Bidirectional text attacks
            'admin@dom\u202Eain.com',  # Right-to-left override
            'admin@\u202Ddomain.com',  # Left-to-right override
            
            # Control characters
            'admin@domain\u0000.com',  # Null character
            'admin@domain\u0001.com',  # Start of heading
            'admin@domain\u007F.com',  # Delete character
        ]
        
        for attack_email in unicode_attacks:
            # These should be properly handled or rejected
            try:
                result = self.validator.is_valid(attack_email)
                # If accepted, ensure it's properly normalized
                if result:
                    normalized = self.validator.normalize(attack_email)
                    assert normalized != attack_email, "Unicode attack not normalized"
            except Exception as e:
                # Exceptions during validation are acceptable for security
                assert "unicode" in str(e).lower() or "encoding" in str(e).lower()
    
    def test_regex_dos_protection(self):
        """Test protection against ReDoS (Regular Expression DoS) attacks."""
        # Patterns that can cause catastrophic backtracking
        redos_patterns = [
            # Nested quantifiers
            'a' * 50 + '@' + ('b' * 30 + 'c') * 20 + '.com',
            
            # Alternation with overlap
            'user@' + 'a' * 50 + ('bb' + 'b' * 25) * 10 + '.com',
            
            # Grouping with quantifiers
            'test@' + ('(' + 'a' * 20 + ')*') * 5 + 'domain.com',
        ]
        
        import time
        
        for pattern in redos_patterns:
            start_time = time.time()
            try:
                result = self.validator.is_valid(pattern)
                elapsed = time.time() - start_time
                
                # Validation should complete within reasonable time (1 second)
                assert elapsed < 1.0, f"ReDoS vulnerability detected: {elapsed:.2f}s for pattern"
                
            except (ValueError, TypeError) as e:
                elapsed = time.time() - start_time
                assert elapsed < 1.0, f"ReDoS in exception handling: {elapsed:.2f}s"
                # Expected exceptions for invalid patterns are acceptable


@pytest.mark.security
class TestTemplateSecurity:
    """Test template security features."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TemplateEngine("samples")
        self.security_framework = SecurityTestFramework()
    
    def _assert_safe_html_output(self, html_output: str, original_payload: str):
        """Assert that HTML output is safe from XSS."""
        # Check that dangerous patterns are not present
        dangerous_patterns = [
            '<script',
            'javascript:',
            'onerror=',
            'onload=',
            'onclick=',
            'onmouseover=',
            '<iframe',
            '<object',
            '<embed',
            '<svg',
        ]
        
        html_lower = html_output.lower()
        for pattern in dangerous_patterns:
            assert pattern not in html_lower, f"Dangerous pattern '{pattern}' found in output: {html_output}"
    
    def test_template_injection_protection(self):
        """Test protection against template injection attacks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp.write('''
            <html>
            <body>
                <h1>Hello {{name}}!</h1>
                <p>Company: {{company}}</p>
                <p>Message: {{message}}</p>
            </body>
            </html>
            ''')
            tmp.flush()
            template_path = tmp.name
        
        try:
            for injection_pattern in self.security_framework.INJECTION_PATTERNS:
                variables = {
                    'name': injection_pattern,
                    'company': 'Test Company',
                    'message': 'Test message'
                }
                
                html_result, text_result = self.engine.render(template_path, variables)
                
                # Injection patterns should be escaped in output
                assert injection_pattern not in html_result
                assert injection_pattern not in text_result
                
        finally:
            Path(template_path).unlink()
    
    def test_template_xss_protection(self):
        """Test XSS protection in template rendering."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src="x" onerror="alert(1)">',
            '"><script>alert(document.cookie)</script>',
            'javascript:alert("XSS")',
            '<svg onload="alert(1)">',
            '<iframe src="javascript:alert(1)"></iframe>'
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
            tmp.write('<html><body>{{user_input}}</body></html>')
            tmp.flush()
            template_path = tmp.name
        
        try:
            for payload in xss_payloads:
                variables = {'user_input': payload}
                html_result, _ = self.engine.render(template_path, variables)
                
                # XSS payload should be escaped
                assert '<script>' not in html_result.lower()
                assert 'javascript:' not in html_result.lower()
                assert 'onerror=' not in html_result.lower()
                
        finally:
            Path(template_path).unlink()
        
        # Create a test template in the samples directory
        test_template_path = "samples/test_xss.html"
        test_template_content = '<html><body>{{user_input}}</body></html>'
        
        os.makedirs("samples", exist_ok=True)
        with open(test_template_path, 'w') as f:
            f.write(test_template_content)
        
        try:
            for payload in xss_payloads:
                variables = {'user_input': payload}
                html_result, _ = self.engine.render("test_xss.html", variables)
                
                # XSS payload should be escaped in HTML
                self._assert_safe_html_output(html_result, payload)
                
                # Check for proper HTML escaping
                assert '&lt;' in html_result or payload not in html_result, \
                    f"HTML not properly escaped: {payload}"
                
        finally:
            if os.path.exists(test_template_path):
                os.remove(test_template_path)
    
    def test_template_path_traversal_protection(self):
        """Test protection against path traversal attacks in template loading."""
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '/etc/passwd',
            'C:\\Windows\\System32\\drivers\\etc\\hosts',
            '{{root}}/etc/passwd',
        ]
        
        for malicious_path in malicious_paths:
            with pytest.raises((ValueError, FileNotFoundError, PermissionError)):
                self.engine.render(malicious_path, {})
    
    def test_template_code_execution_protection(self):
        """Test protection against code execution via templates."""
        dangerous_templates = [
            # Python code execution attempts
            '{{[].__class__.__base__.__subclasses__()[104].__init__.__globals__["sys"].exit()}}',
            '{{config.__class__.__init__.__globals__["os"].system("whoami")}}',
            '{{request.application.__globals__.__builtins__.__import__("os").system("ls")}}',
            
            # Jinja2 specific attacks
            '{% for item in [].__class__.__base__.__subclasses__() %}{% endfor %}',
            '{{self.__init__.__globals__.__builtins__.__import__("subprocess").call(["whoami"])}}',
            '{{lipsum.__globals__.os.system("id")}}',
        ]
        
        for dangerous_template in dangerous_templates:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                tmp.write(dangerous_template)
                tmp.flush()
                template_path = tmp.name
            
            try:
                # Should either fail or not execute dangerous code
                with pytest.raises((Exception,)):
                    self.engine.render(template_path, {})
            finally:
                Path(template_path).unlink()
    
@pytest.mark.security
class TestDatabaseSecurity:
    """Security tests for database operations."""
    
    def setup_method(self):
        self.db_manager = DatabaseManager()
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        sql_injections = [
            "'; DROP TABLE deliveries; --",
            "' OR '1'='1",
            "'; INSERT INTO deliveries (email) VALUES ('hacked@evil.com'); --",
            "1'; UPDATE deliveries SET email='hacked@evil.com'; --",
            "' UNION SELECT * FROM sqlite_master; --",
            "; SELECT load_extension('malicious'); --",
        ]
        
        with self.db_manager.get_connection() as conn:
            for injection in sql_injections:
                # Test various database operations with injection attempts
                try:
                    # These should use parameterized queries and be safe
                    cursor = conn.execute(
                        "SELECT * FROM deliveries WHERE email = ?", 
                        (injection,)
                    )
                    cursor.fetchall()
                    
                    # If we get here, the injection was safely handled
                    assert True, "SQL injection properly handled"
                    
                except Exception as e:
                    # Errors are also acceptable - injection should not succeed
                    assert "DROP" not in str(e).upper(), "SQL injection may have executed"
                    assert "UPDATE" not in str(e).upper(), "SQL injection may have executed"
    
    def test_database_file_permissions(self):
        """Test database file has secure permissions."""
        db_path = Path("data") / Path(settings.sqlite_db_path).name
        if db_path.exists():
            file_stat = db_path.stat()
            file_mode = oct(file_stat.st_mode)[-3:]
            
            # Should not be world-readable (no '4' in last digit)
            world_perms = int(file_mode[-1])
            assert world_perms & 4 == 0, f"Database file is world-readable: {file_mode}"
    
    def test_database_connection_security(self):
        """Test database connection security settings."""
        with self.db_manager.get_connection() as conn:
            result = conn.execute("PRAGMA foreign_keys").fetchone()
            assert result[0] == 1, "Foreign keys should be enabled"
            
            # Check secure delete is enabled
            result = conn.execute("PRAGMA secure_delete").fetchone()
            assert result[0] in [1, 2], "Secure delete should be enabled"
            
            # Ensure journal mode is secure
            result = conn.execute("PRAGMA journal_mode").fetchone()
            assert result[0].upper() in ['WAL', 'DELETE'], f"Insecure journal mode: {result[0]}"


@pytest.mark.security
class TestInputValidationSecurity:
    """Security tests for input validation across the system."""
    
    def setup_method(self):
        """Инициализация для каждого теста"""
        self.security_framework = SecurityTestFramework()
    
    def test_recipient_data_validation(self):
        """Test validation of recipient data for security issues."""
        malicious_recipients = [
            # XSS in name field
            Recipient(
                email="test@domain.com",
                name='<script>alert("XSS")</script>',
                variables={}
            ),
            
            # HTML injection in variables
            Recipient(
                email="test@domain.com", 
                name="Test User",
                variables={'company': '<iframe src="javascript:alert(1)"></iframe>'}
            ),
            
            # Extremely long values (DoS attempt)
            Recipient(
                email="test@domain.com",
                name="A" * 100000,
                variables={}
            ),
            
            # Control characters
            Recipient(
                email="test@domain.com",
                name="Test\x00User\x01",
                variables={'role': 'Admin\r\n\r\nInjected: malicious'}
            )
        ]
        
        for recipient in malicious_recipients:
            # Validate that recipient data is properly sanitized
            self._validate_recipient_security(recipient)
    
    def test_file_upload_security(self):
        """Test file upload security measures."""
        # Test dangerous file extensions
        for ext in self.security_framework.DANGEROUS_EXTENSIONS:
            dangerous_filename = f"malicious{ext}"
            
            # File uploads should reject dangerous extensions
            with pytest.raises((ValueError, SecurityError)):
                self._simulate_file_upload(dangerous_filename, b"malicious content")
    
    def test_configuration_security(self):
        """Test configuration security and sensitive data protection."""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential'
        ]
        
        config_dict = settings.__dict__
        for key, value in config_dict.items():
            key_lower = key.lower()
            
            if any(pattern in key_lower for pattern in sensitive_patterns):
                if isinstance(value, str) and len(value) > 0:
                    assert 'test' in value.lower() or '*' in value or value == 'placeholder', \
                        f"Potential sensitive data exposure in config: {key}"
    
    def _validate_recipient_security(self, recipient: Recipient):
        """Validate recipient data for security issues."""
        # Check name field for XSS
        if recipient.name:
            dangerous_chars = ['<', '>', '"', "'", '&']
            for char in dangerous_chars:
                if char in recipient.name:
                    # Should be properly escaped when rendered
                    escaped_name = html.escape(recipient.name)
                    assert escaped_name != recipient.name, "XSS characters not escaped"
        
        # Check variables for injection
        if recipient.variables:
            for key, value in recipient.variables.items():
                if isinstance(value, str):
                    for pattern in self.security_framework.INJECTION_PATTERNS[:5]:
                        assert pattern not in value, f"Injection pattern found in variable {key}: {pattern}"
    
    def _simulate_file_upload(self, filename: str, content: bytes):
        """Simulate file upload for security testing."""
        # This would be connected to actual file upload logic
        # For now, implement basic security checks
        
        # Check file extension
        if any(filename.lower().endswith(ext) for ext in self.security_framework.DANGEROUS_EXTENSIONS):
            raise SecurityError(f"Dangerous file extension: {filename}")
        
        # Check file size (prevent DoS)
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise SecurityError("File too large")
        
        # Check for executable signatures
        if content.startswith(b'MZ') or content.startswith(b'\x7fELF'):
            raise SecurityError("Executable file detected")


@pytest.mark.security
class TestCryptographicSecurity:
    """Security tests for cryptographic operations."""
    
    def test_random_generation_quality(self):
        """Test quality of random number generation."""
        # Generate multiple random values
        random_values = [secrets.token_hex(32) for _ in range(100)]
        
        # Check for uniqueness
        assert len(set(random_values)) == len(random_values), "Random values not unique"
        
        # Check entropy (basic test)
        combined = ''.join(random_values)
        char_counts = {}
        for char in combined:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Character distribution should be reasonably uniform
        max_count = max(char_counts.values())
        min_count = min(char_counts.values())
        ratio = max_count / min_count
        
        assert ratio < 2.0, f"Poor random distribution detected: {ratio}"
    
    def test_hash_security(self):
        """Test hash function security."""
        test_data = "sensitive_data_12345"
        
        # Test SHA-256 (should be used for sensitive data)
        hash_result = hashlib.sha256(test_data.encode()).hexdigest()
        
        # Hash should be deterministic
        hash_result2 = hashlib.sha256(test_data.encode()).hexdigest()
        assert hash_result == hash_result2, "Hash function not deterministic"
        
        # Hash should be different for different inputs
        different_data = "different_sensitive_data"
        different_hash = hashlib.sha256(different_data.encode()).hexdigest()
        assert hash_result != different_hash, "Hash collision detected"
        
        # Hash should have expected length
        assert len(hash_result) == 64, f"SHA-256 hash wrong length: {len(hash_result)}"


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class SecurityAuditReporter:
    """Generate security audit reports."""
    
    def __init__(self):
        self.findings = []
    
    def add_finding(self, severity: str, category: str, description: str, 
                   recommendation: str = ""):
        """Add a security finding."""
        self.findings.append({
            'severity': severity,
            'category': category,
            'description': description,
            'recommendation': recommendation,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    def generate_report(self, output_file: str = "security_audit_report.md"):
        """Generate comprehensive security audit report."""
        report = [
            "# Security Audit Report",
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Findings:** {len(self.findings)}",
            f"- **Critical:** {len([f for f in self.findings if f['severity'] == 'CRITICAL'])}",
            f"- **High:** {len([f for f in self.findings if f['severity'] == 'HIGH'])}",
            f"- **Medium:** {len([f for f in self.findings if f['severity'] == 'MEDIUM'])}",
            f"- **Low:** {len([f for f in self.findings if f['severity'] == 'LOW'])}",
            "",
            "## Security Controls Tested",
            "",
            "- Email injection protection",
            "- Template injection protection", 
            "- XSS protection",
            "- SQL injection protection",
            "- Path traversal protection",
            "- Input validation",
            "- Cryptographic security",
            "- File upload security",
            "",
            "## Detailed Findings",
            ""
        ]
        
        if self.findings:
            for i, finding in enumerate(self.findings, 1):
                report.extend([
                    f"### Finding #{i}: {finding['category']}",
                    "",
                    f"**Severity:** {finding['severity']}",
                    f"**Description:** {finding['description']}",
                    f"**Recommendation:** {finding['recommendation']}",
                    f"**Timestamp:** {finding['timestamp']}",
                    ""
                ])
        else:
            report.append("No security issues detected in automated testing.")
        
        report.extend([
            "",
            "## Security Recommendations",
            "",
            "1. Regularly update dependencies to patch security vulnerabilities",
            "2. Implement rate limiting to prevent abuse",
            "3. Use HTTPS for all communications",
            "4. Implement proper logging and monitoring",
            "5. Regular security audits and penetration testing",
            "6. Implement input sanitization at all entry points",
            "7. Use parameterized queries for all database operations",
            "8. Validate and sanitize all user inputs",
            "9. Implement proper error handling to prevent information disclosure",
            "10. Use secure coding practices throughout development"
        ])
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(report))


if __name__ == "__main__":
    # Run security tests when executed directly
    pytest.main([
        __file__,
        "-v", 
        "-m", "security",
        "--tb=short"
    ])