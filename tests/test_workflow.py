from unittest.mock import Mock, patch

import pytest
from pre_commit.git import commit

from Workflow.workflow import Processes


class TestProcesses:
    """Test cases for Processes class."""

    @patch("Workflow.workflow.BitwardenCredentialManagement")
    @patch("Workflow.workflow.Zindian")
    @patch("Workflow.workflow.ZindiProcessing")
    @patch("Workflow.workflow.ProcessPreparation")
    @patch("Workflow.workflow.Utils")
    @patch("Workflow.workflow.CONFIG")
    def test_processes_init(
        self,
        mock_config,
        mock_utils,
        mock_prep,
        mock_zindi_proc,
        mock_zindian,
        mock_bitwarden,
    ):
        """Test Processes initialization without real credentials."""

        # --- Mock CONFIG ---
        mock_config.ReportsFiles.reports_columns = ["col1", "col2"]
        mock_config.INPUTS.show_leader_board = False
        mock_config.INPUTS.user_rank_for_selected_competition = True
        mock_config.INPUTS.upload_submission_file = True
        mock_config.INPUTS.download_dataset_for_selected_competition_name = False
        mock_config.INPUTS.show_daily_submission = True
        mock_config.DIRECTORIES.REPORT = ["/tmp/report.csv"]

        # --- Mock Bitwarden return as real dict ---
        mock_bitwarden_instance = Mock()
        # Important: get_credential must return dict, not Mock
        mock_bitwarden_instance.get_credential.return_value = {"username": "testuser", "password": "testpass"}
        mock_bitwarden.return_value = mock_bitwarden_instance

        # --- Mock Zindian instance ---
        mock_zindian_instance = Mock()
        mock_zindian.return_value = mock_zindian_instance

        # --- Mock ProcessPreparation instance ---
        mock_prep_instance = Mock()
        mock_prep.return_value = mock_prep_instance

        # --- Mock ZindiProcessing and Utils ---
        mock_zindi_proc.return_value = Mock()
        mock_utils.return_value = Mock()

        # --- Run Processes init ---
        process = Processes()

        # --- Assertions ---
        assert process.all_items["username"] == "testuser"
        assert process.user is not None
        assert process.preparation_process is not None

    @patch("Workflow.workflow.BitwardenCredentialManagement")
    @patch("Workflow.workflow.Zindian")
    @patch("Workflow.workflow.ZindiProcessing")
    @patch("Workflow.workflow.ProcessPreparation")
    @patch("Workflow.workflow.Utils")
    @patch("Workflow.workflow.CONFIG")
    def test_preparation_files_for_processing(
        self,
        mock_config,
        mock_utils,
        mock_prep,
        mock_zindi_proc,
        mock_zindian,
        mock_bitwarden,
    ):
        """Test prepare_files_for_processing method."""

        # --- Mock CONFIG ---
        mock_config.ReportsFiles.reports_columns = ["col1", "col2"]
        mock_config.INPUTS.show_leader_board = False
        mock_config.INPUTS.user_rank_for_selected_competition = True
        mock_config.INPUTS.upload_submission_file = True
        mock_config.INPUTS.download_dataset_for_selected_competition_name = False
        mock_config.INPUTS.show_daily_submission = True
        mock_config.DIRECTORIES.REPORT = ["/tmp/report.csv"]

        # --- Mock Bitwarden ---
        mock_bitwarden_instance = Mock()
        mock_bitwarden_instance.get_credential.return_value = {"username": "testuser", "password": "testpass"}
        mock_bitwarden.return_value = mock_bitwarden_instance

        # --- Mock ProcessPreparation methods ---
        mock_prep_instance = Mock()
        mock_prep_instance.get_opened_competition_names_and_create_dirs.return_value = None
        mock_prep_instance.check_submission_files.return_value = True
        mock_prep_instance.normalize_selected_competition_names.return_value = ["comp1", "comp2"]
        mock_prep_instance.filter_open_competitions.return_value = ["comp1", "comp2"]
        mock_prep_instance.filter_competitions_with_submission_limit.return_value = ["comp1", "comp2"]
        mock_prep_instance.validate_competition_list_not_empty.return_value = None
        mock_prep.return_value = mock_prep_instance

        # --- Mock Zindian, ZindiProcessing, Utils ---
        mock_zindian.return_value = Mock()
        mock_zindi_proc.return_value = Mock()
        mock_utils.return_value = Mock()

        # --- Run Processes method ---
        process = Processes()
        result = process.prepare_files_for_processing()

        # --- Assertions ---
        assert result == ["comp1", "comp2"]
        mock_prep_instance.get_opened_competition_names_and_create_dirs.assert_called_once()
        mock_prep_instance.check_submission_files.assert_called_once()
        mock_prep_instance.normalize_selected_competition_names.assert_called_once()
        mock_prep_instance.filter_open_competitions.assert_called_once()
        mock_prep_instance.filter_competitions_with_submission_limit.assert_called_once()
        mock_prep_instance.validate_competition_list_not_empty.assert_called_once()
