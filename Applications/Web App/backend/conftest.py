import os
import sys
import pytest

backend_dir = os.path.dirname(os.path.abspath(__file__))
test_db_path = os.path.join(backend_dir, "test_database.db")
test_log_path = os.path.join(backend_dir, "test_audit_logs.log")

os.environ["MADN_DB_PATH"] = test_db_path
os.environ["MADN_LOG_PATH"] = test_log_path

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Clean up test DB before tests
    for p in [test_db_path, test_db_path + "-wal", test_db_path + "-shm", test_log_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
    
    import database
    database.DB_PATH = test_db_path
    database.LOG_PATH = test_log_path
    database.init_db()
    
    yield
    
    # Clean up test DB after tests
    for p in [test_db_path, test_db_path + "-wal", test_db_path + "-shm", test_log_path]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except:
                pass
