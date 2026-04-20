"""
Pytest configuration and shared fixtures.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# 🔑 ADD PROJECT ROOT TO PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_bitwarden_credentials():
    """Mock Bitwarden credentials."""
    return {
        "Zindi_Credential": {"username": "test_user", "password": "test_password"},
        "Phantom Wallet": {"key": "test_key"},
    }


@pytest.fixture
def mock_zindi_user():
    """Mock Zindi user object."""
    user = Mock()
    user.username = "test_user"
    user.get_opened_challenges = Mock(return_value={"id": [1, 2, 3], "name": ["comp1", "comp2", "comp3"]})
    user.get_available_remaining_submissions_for_competition = Mock(
        return_value={"data": {"today": 5, "submitted_today": 0}}
    )
    return user


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""

    class MockConfig:
        class DIRECTORIES:
            TEMP = Path("/tmp/test_temp")
            OUTPUT = Path("/tmp/test_output")
            REPORT = Path("/tmp/test_output/submission_report.csv")
            SUBMSSION_FILES = Path("/tmp/test_output/submissionfiles")
            OUTPUT_SCREENSHOTS = "/tmp/test_output/screenshots"
            MAPPING = Path("/tmp/test_output/mapping")

        class ReportsFiles:
            reports_columns = [
                "Competition Name",
                "today_remaining_submission",
                "today_total_submitted",
                "Best Score",
                "Best rank",
                "user name",
                "Best submission time",
                "Rank after submission",
            ]
            submission_posted_report = "submission_report.csv"

        class CredentialsGroups:
            items_list = ["Phantom Wallet", "Zindi_Credential"]

        class ZindiCompetitionFilesPath:
            competition_folder = Path("/tmp/test_competitions")
            submission_file_folder = "SubmissionFilesFolder"

        class INPUTS:
            selected_competition_names_to_work = ["test-competition-1", "test-competition-2"]
            download_dataset_for_selected_competition_name = False
            show_leader_board = False
            user_rank_for_selected_competition = True
            upload_submission_file = True
            show_daily_submission = True

    return MockConfig()
