# test_app.py

import os
import pytest
from main import backup_file, on_save, load_directory_path

# Using a fixture to create a temporary directory
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

# Testing the backup_file function
def test_backup_file(temp_dir):
    original_file = temp_dir / "original_file.txt"
    original_file.write_text("test content")
    backup_folder = temp_dir / "backups"
    backup_folder.mkdir()

    backup_file(str(original_file), str(backup_folder))

    # Assert that the backup file exists and has the correct content
    backups = list(backup_folder.iterdir())
    assert len(backups) == 1
    assert backups[0].read_text() == "test content"

# Mocking configparser for load_directory_path testing
@pytest.fixture
def mock_config_parser(monkeypatch):
    mock_config = {
        'LastDirectory': str('/path/to/directory')
    }
    monkeypatch.setattr('configparser.ConfigParser.get', lambda self, section, option: mock_config[option])

# Testing the load_directory_path function
def test_load_directory_path(mock_config_parser, temp_dir):
    # Assuming the load_directory_path function is modified to take a configparser object as an argument
    directory = load_directory_path(mock_config_parser, str(temp_dir / "settings.ini"))
    assert directory == '/path/to/directory'