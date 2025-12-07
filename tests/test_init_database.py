import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from src.api import init_db as init_db_module  

def test_init_database_success():
    """
    Тестує успішне виконання init_database():
    - викликається create_all
    - inspect отримує список таблиць
    - print виконується
    """
    with patch("src.api.init_db.Base.metadata.create_all") as mock_create_all, \
         patch("src.api.init_db.inspect") as mock_inspect, \
         patch("builtins.print") as mock_print:

        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["user", "room", "booking"]
        mock_inspect.return_value = mock_inspector

        init_db_module.init_database()

        mock_create_all.assert_called_once()
        mock_inspect.assert_called_once()
        mock_inspector.get_table_names.assert_called_once()
        assert mock_print.call_count > 0


def test_init_database_exception():
    """
    Тестує блок except:
    - симулюємо Exception при create_all
    - перевіряємо, що Exception піднімається і traceback виконується
    """
    import traceback

    with patch("src.api.init_db.Base.metadata.create_all", side_effect=Exception("DB Error")), \
         patch("builtins.print") as mock_print, \
         patch.object(traceback, "print_exc") as mock_traceback:

        with pytest.raises(Exception, match="DB Error"):
            init_db_module.init_database()

        assert any("Error initializing database" in str(call) for call in [str(a) for a in mock_print.call_args_list])
        mock_traceback.assert_called_once()


def test_init_database_main_subprocess():
    """
    Тестує виконання init_database через __main__ у новому процесі
    """
    result = subprocess.run(
        [sys.executable, "-m", "src.api.init_db"],
        capture_output=True,
        text=True
    )
    assert "Starting database initialization..." in result.stdout
    assert "Database initialized!" in result.stdout
