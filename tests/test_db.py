import os
import importlib
import pytest
from sqlalchemy.orm import Session
from src.api import db as db_module

def test_default_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    importlib.reload(db_module)

    assert db_module.DATABASE_URL.startswith("postgresql://postgres")

def test_get_db_closes_session():
    gen = db_module.get_db()
    
    db_session = next(gen)
    
    assert isinstance(db_session, Session)
    assert hasattr(db_session, "close")
    
    with pytest.raises(StopIteration):
        next(gen)

def test_create_tables_executes():
    db_module.create_tables()

    assert True
