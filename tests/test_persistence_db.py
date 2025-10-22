"""
Comprehensive tests for persistence/db.py

Covers:
- DatabaseManager initialization and connections
- SQL query execution
- Transaction management
- Database schema creation
- Global database instance management
- Error handling and edge cases
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.persistence.db import (
    DatabaseManager,
    init_database,
    create_tables,
    get_db,
    close_db,
    _db_manager
)


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""
    
    def test_init_with_default_path(self):
        """Test DatabaseManager initialization with default path."""
        with patch('persistence.db.settings') as mock_settings:
            mock_settings.sqlite_db_path = "/tmp/test.db"
            db = DatabaseManager()
            assert db.db_path == "/tmp/test.db"
            assert db._connection is None
    
    def test_init_with_custom_path(self):
        """Test DatabaseManager initialization with custom path."""
        custom_path = "/custom/path/test.db"
        db = DatabaseManager(custom_path)
        assert db.db_path == custom_path
        assert db._connection is None
    
    def test_get_connection_creates_new(self):
        """Test that get_connection creates new connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            conn = db.get_connection()
            
            assert isinstance(conn, sqlite3.Connection)
            assert db._connection is conn
            assert conn.row_factory == sqlite3.Row
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_get_connection_reuses_existing(self):
        """Test that get_connection reuses existing connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            conn1 = db.get_connection()
            conn2 = db.get_connection()
            
            assert conn1 is conn2
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_close_connection(self):
        """Test closing database connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            conn = db.get_connection()
            assert db._connection is not None
            
            db.close()
            assert db._connection is None
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_close_without_connection(self):
        """Test closing when no connection exists."""
        db = DatabaseManager("/tmp/test.db")
        # Should not raise exception
        db.close()
        assert db._connection is None
    
    def test_execute_query(self):
        """Test executing SQL query."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            # Create test table
            cursor = db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            assert isinstance(cursor, sqlite3.Cursor)
            
            # Insert data
            db.execute("INSERT INTO test (id, name) VALUES (?, ?)", (1, "test"))
            db.commit()
            
            # Query data
            cursor = db.execute("SELECT * FROM test WHERE id = ?", (1,))
            rows = cursor.fetchall()
            assert len(rows) == 1
            assert rows[0]['id'] == 1
            assert rows[0]['name'] == "test"
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_execute_many(self):
        """Test executing query with multiple parameter sets."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            # Create test table
            db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
            
            # Insert multiple rows
            params_list = [(1, "first"), (2, "second"), (3, "third")]
            cursor = db.execute_many("INSERT INTO test (id, name) VALUES (?, ?)", params_list)
            assert isinstance(cursor, sqlite3.Cursor)
            
            db.commit()
            
            # Verify data
            cursor = db.execute("SELECT COUNT(*) as count FROM test")
            count = cursor.fetchone()['count']
            assert count == 3
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_commit(self):
        """Test committing transaction."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            # Create table and insert data
            db.execute("CREATE TABLE test (id INTEGER)")
            db.execute("INSERT INTO test (id) VALUES (?)", (1,))
            
            # Data should not be visible without commit
            db2 = DatabaseManager(tmp_path)
            cursor = db2.execute("SELECT COUNT(*) as count FROM test")
            count = cursor.fetchone()['count']
            assert count == 0
            db2.close()
            
            # Commit and verify
            db.commit()
            
            db3 = DatabaseManager(tmp_path)
            cursor = db3.execute("SELECT COUNT(*) as count FROM test")
            count = cursor.fetchone()['count']
            assert count == 1
            db3.close()
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_rollback(self):
        """Test rolling back transaction."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            # Create table and insert data
            db.execute("CREATE TABLE test (id INTEGER)")
            db.commit()
            
            db.execute("INSERT INTO test (id) VALUES (?)", (1,))
            
            # Rollback and verify data is not there
            db.rollback()
            
            cursor = db.execute("SELECT COUNT(*) as count FROM test")
            count = cursor.fetchone()['count']
            assert count == 0
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_rollback_without_connection(self):
        """Test rollback when no connection exists."""
        db = DatabaseManager("/tmp/test.db")
        # Should not raise exception
        db.rollback()
    
    def test_commit_without_connection(self):
        """Test commit when no connection exists."""
        db = DatabaseManager("/tmp/test.db")
        # Should not raise exception
        db.commit()
    
    def test_context_manager_success(self):
        """Test context manager with successful transaction."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                db.execute("CREATE TABLE test (id INTEGER)")
                db.execute("INSERT INTO test (id) VALUES (?)", (1,))
                # Should auto-commit on successful exit
            
            # Verify data was committed
            with DatabaseManager(tmp_path) as db:
                cursor = db.execute("SELECT COUNT(*) as count FROM test")
                count = cursor.fetchone()['count']
                assert count == 1
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_context_manager_exception(self):
        """Test context manager with exception (rollback)."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Create table first
            with DatabaseManager(tmp_path) as db:
                db.execute("CREATE TABLE test (id INTEGER)")
            
            # Try to insert with exception
            with pytest.raises(ValueError):
                with DatabaseManager(tmp_path) as db:
                    db.execute("INSERT INTO test (id) VALUES (?)", (1,))
                    raise ValueError("Test exception")
            
            # Verify data was rolled back
            with DatabaseManager(tmp_path) as db:
                cursor = db.execute("SELECT COUNT(*) as count FROM test")
                count = cursor.fetchone()['count']
                assert count == 0
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestDatabaseInitialization:
    """Test suite for database initialization functions."""
    
    def test_init_database_default_path(self):
        """Test database initialization with default path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "test.db")
            
            with patch('persistence.db.settings') as mock_settings:
                mock_settings.sqlite_db_path = test_db_path
                
                init_database()
                
                assert os.path.exists(test_db_path)
    
    def test_init_database_custom_path(self):
        """Test database initialization with custom path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "custom.db")
            
            init_database(test_db_path)
            
            assert os.path.exists(test_db_path)
    
    def test_init_database_creates_directory(self):
        """Test that init_database creates parent directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "subdir", "nested", "test.db")
            
            init_database(test_db_path)
            
            assert os.path.exists(test_db_path)
            assert os.path.exists(os.path.dirname(test_db_path))
    
    def test_create_tables(self):
        """Test table creation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                create_tables(db)
                
                # Verify tables exist
                cursor = db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row['name'] for row in cursor.fetchall()]
                
                expected_tables = ['deliveries', 'suppressions', 'events', 'daily_quota']
                for table in expected_tables:
                    assert table in tables
                
                # Verify indexes exist
                cursor = db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                indexes = [row['name'] for row in cursor.fetchall()]
                
                expected_indexes = [
                    'idx_deliveries_email', 'idx_deliveries_sent_at',
                    'idx_events_email', 'idx_events_message_id'
                ]
                for index in expected_indexes:
                    assert index in indexes
        finally:
            os.unlink(tmp_path)


class TestGlobalDatabaseManager:
    """Test suite for global database manager functions."""
    
    def setup_method(self):
        """Reset global state before each test."""
        close_db()
    
    def teardown_method(self):
        """Clean up after each test."""
        close_db()
    
    def test_get_db_creates_instance(self):
        """Test that get_db creates global instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "test.db")
            
            with patch('persistence.db.settings') as mock_settings:
                mock_settings.sqlite_db_path = test_db_path
                
                db = get_db()
                
                assert isinstance(db, DatabaseManager)
                assert db.db_path == test_db_path
                assert os.path.exists(test_db_path)
    
    def test_get_db_reuses_instance(self):
        """Test that get_db reuses existing instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "test.db")
            
            with patch('persistence.db.settings') as mock_settings:
                mock_settings.sqlite_db_path = test_db_path
                
                db1 = get_db()
                db2 = get_db()
                
                assert db1 is db2
    
    def test_close_db(self):
        """Test closing global database instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "test.db")
            
            with patch('persistence.db.settings') as mock_settings:
                mock_settings.sqlite_db_path = test_db_path
                
                db = get_db()
                assert db is not None
                
                close_db()
                
                # Should create new instance after close
                db2 = get_db()
                assert db2 is not db
    
    def test_close_db_without_instance(self):
        """Test closing when no global instance exists."""
        # Should not raise exception
        close_db()


class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        # Try to connect to invalid path
        db = DatabaseManager("/invalid/path/that/does/not/exist/test.db")
        
        with pytest.raises(sqlite3.OperationalError):
            db.get_connection()
    
    def test_sql_syntax_error(self):
        """Test handling of SQL syntax errors."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            with pytest.raises(sqlite3.OperationalError):
                db.execute("INVALID SQL SYNTAX")
        finally:
            db.close()
            os.unlink(tmp_path)
    
    def test_constraint_violation(self):
        """Test handling of constraint violations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            db = DatabaseManager(tmp_path)
            
            # Create table with unique constraint
            db.execute("CREATE TABLE test (id INTEGER UNIQUE)")
            db.execute("INSERT INTO test (id) VALUES (?)", (1,))
            
            # Try to insert duplicate
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("INSERT INTO test (id) VALUES (?)", (1,))
                db.commit()
        finally:
            db.close()
            os.unlink(tmp_path)


class TestMainModule:
    """Test suite for main module execution."""
    
    def test_main_execution(self):
        """Test that main module initializes database correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_db_path = os.path.join(tmp_dir, "test.db")
            
            with patch('persistence.db.settings') as mock_settings:
                mock_settings.sqlite_db_path = test_db_path
                
                # Call init_database directly since it's what main does
                from src.persistence.db import init_database
                init_database(test_db_path)
                
                # Verify database was created
                assert os.path.exists(test_db_path)


class TestTableOperations:
    """Test suite for table operations on actual schema."""
    
    def test_deliveries_table_operations(self):
        """Test operations on deliveries table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                create_tables(db)
                
                # Insert delivery record
                db.execute("""
                    INSERT INTO deliveries 
                    (email, template_name, subject, message_id, status, provider)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("test@example.com", "welcome", "Welcome!", "msg_123", "sent", "resend"))
                
                # Query record
                cursor = db.execute("SELECT * FROM deliveries WHERE email = ?", ("test@example.com",))
                row = cursor.fetchone()
                
                assert row['email'] == "test@example.com"
                assert row['template_name'] == "welcome"
                assert row['status'] == "sent"
        finally:
            os.unlink(tmp_path)
    
    def test_suppressions_table_operations(self):
        """Test operations on suppressions table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                create_tables(db)
                
                # Insert suppression record
                db.execute("""
                    INSERT INTO suppressions (email, reason)
                    VALUES (?, ?)
                """, ("suppressed@example.com", "unsubscribed"))
                
                # Query record
                cursor = db.execute("SELECT * FROM suppressions WHERE email = ?", ("suppressed@example.com",))
                row = cursor.fetchone()
                
                assert row['email'] == "suppressed@example.com"
                assert row['reason'] == "unsubscribed"
        finally:
            os.unlink(tmp_path)
    
    def test_events_table_operations(self):
        """Test operations on events table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                create_tables(db)
                
                # Insert event record
                db.execute("""
                    INSERT INTO events (event_type, email, message_id, data)
                    VALUES (?, ?, ?, ?)
                """, ("delivered", "test@example.com", "msg_123", '{"status": "delivered"}'))
                
                # Query record
                cursor = db.execute("SELECT * FROM events WHERE message_id = ?", ("msg_123",))
                row = cursor.fetchone()
                
                assert row['event_type'] == "delivered"
                assert row['email'] == "test@example.com"
        finally:
            os.unlink(tmp_path)
    
    def test_daily_quota_table_operations(self):
        """Test operations on daily_quota table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            with DatabaseManager(tmp_path) as db:
                create_tables(db)
                
                # Insert quota record
                db.execute("""
                    INSERT INTO daily_quota (date, sent_count)
                    VALUES (?, ?)
                """, ("2024-01-01", 150))
                
                # Query record
                cursor = db.execute("SELECT * FROM daily_quota WHERE date = ?", ("2024-01-01",))
                row = cursor.fetchone()
                
                assert row['date'] == "2024-01-01"
                assert row['sent_count'] == 150
        finally:
            os.unlink(tmp_path)