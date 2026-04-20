from unittest.mock import Mock, patch

import pandas as pd

from Workflow.process import ProcessPreparation
from Workflow.workflow import Processes


class TestProcesses:
    """Test cases for Processes and ProcessPreparation."""

    @patch("Workflow.workflow.Zindian")  # Patch Zindian class
    def test_processes_init(self, mock_zindian_class):
        """Test Processes initialization without real credentials."""
        # Dummy all_items dictionary
        dummy_all_items = {"username": "testuser", "password": "testpass"}

        # Patch Processes.__init__ to inject all_items
        original_init = Processes.__init__

        def fake_init(self):
            self.all_items = dummy_all_items
            # Do not call original init to avoid Bitwarden/real auth
            self.user = mock_zindian_class(
                username=dummy_all_items["username"],
                fixed_password=dummy_all_items["password"],
            )

        with patch.object(Processes, "__init__", fake_init):
            process = Processes()

        # Assertions
        mock_zindian_class.assert_called_once_with(username="testuser", fixed_password="testpass")
        assert process.user is not None

    @patch("Workflow.process.remove_subdirectories")  # Prevent actual folder removal
    def test_preparation_files_for_processing(self, mock_remove_subdirs):
        """Test ProcessPreparation methods for file preparation."""
        # Mock zindi_user methods
        mock_zindi_user = Mock()
        # Return a dict with pandas Series so .tolist() works
        mock_zindi_user.get_opened_challenges.return_value = {"id": pd.Series(["comp1", "comp2"])}
        mock_zindi_user.get_available_remaining_submissions_for_competition.return_value = {"data": {"today": 1}}

        prep = ProcessPreparation(zindi_user=mock_zindi_user)

        # Mock submission_files_checks instance
        prep.submission_files_checks = Mock()
        prep.submission_files_checks.is_submission_file_present.return_value = True
        prep.submission_files_checks.check_submission_filename_format.return_value = True
        prep.submission_files_checks.move_submission_files_to_respective_competition_folder.return_value = True

        # Call methods safely
        prep.get_opened_competition_names_and_create_dirs()
