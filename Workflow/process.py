import glob
import os
import re

from libraries.Config import CONFIG
from libraries.exception import (
    IncorrectSubmissionFilesNames,
    SelectedCompetitionListEmptyAfterProcessingError,
    SubmissionFilesNotPresentFolder,
)
from libraries.logging_file import logger
from libraries.submissionfileschecks import SubmissionFilesChecks
from libraries.utils import remove_subdirectories


class ProcessPreparation:
    """processes."""

    def __init__(self, zindi_user):
        self.user = zindi_user
        self.submission_files_checks = SubmissionFilesChecks()

    def get_opened_competition_names_and_create_dirs(self):
        """Get opened competitions name list and create directories."""
        remove_subdirectories(CONFIG.ZindiCompetitionFilesPath.competition_folder)

        open_challenge_data = self.user.get_opened_challenges(
            reward="all", kind="competition", fixed_index=None, open_competition=True
        )
        id_list = open_challenge_data["id"].tolist()
        parent_directory = CONFIG.ZindiCompetitionFilesPath.competition_folder
        for folder_name in id_list:
            folder_path = os.path.join(parent_directory, str(folder_name))
            os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Created directories for {len(id_list)} IDs in {parent_directory}")

    def are_submission_files_present_in_competition_folder(self) -> bool:
        """Check if submission CSV files are already present in competition folder."""
        competition_folder = CONFIG.ZindiCompetitionFilesPath.competition_folder
        already_present = False
        for subdir in os.listdir(competition_folder):
            subdir_path = os.path.join(competition_folder, subdir)
            if os.path.isdir(subdir_path):
                csv_files = glob.glob(os.path.join(subdir_path, "*.csv"))
                if csv_files:
                    already_present = True
        return already_present

    def check_submission_files(self):
        """Check submission files for proper preprocessing."""
        if self.submission_files_checks.is_submission_file_present():
            logger.info("Submission file present OKAY")
        else:
            if self.are_submission_files_present_in_competition_folder():
                logger.info("Submission files already present in competition folder")
            else:
                raise SubmissionFilesNotPresentFolder

        if not self.are_submission_files_present_in_competition_folder():
            if self.submission_files_checks.check_submission_filename_format():
                logger.info("Submission filename format OKAY")
            else:
                logger.info("Correct submission files name which should be {competition name from url}.....csv")
                raise IncorrectSubmissionFilesNames

            if self.submission_files_checks.move_submission_files_to_respective_competition_folder():
                logger.info("Move submission files to respective competition folder for posting DONE")
            else:
                logger.info("Files cannot be moved - unexpected error.")
        return True

    @staticmethod
    def normalize_competition_name(name):
        # Convert to lowercase
        name = name.lower()
        # Replace multiple spaces with a single space
        name = re.sub(r"\s+", " ", name)
        # Replace spaces with hyphens
        name = name.replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        name = re.sub(r"[^a-z0-9-]", "", name)
        return name

    def normalize_selected_competition_names(self) -> list:
        """Check if selected competition names are correct and normalize them."""
        selected_competition_list_corrected = []
        selected_competition_list = CONFIG.INPUTS.selected_competition_names_to_work
        open_challenge_data = self.user.get_opened_challenges(
            reward="all", kind="competition", fixed_index=None, open_competition=True
        )
        id_list = open_challenge_data["id"].tolist()
        for selected_competition in selected_competition_list:
            if selected_competition in id_list:
                normalized_competition_name = self.normalize_competition_name(selected_competition)
                if normalized_competition_name in id_list:
                    selected_competition_list_corrected.append(normalized_competition_name)
                else:
                    logger.info(f"Competition name is incorrect: {selected_competition}")
                    logger.info("Removing it from selected competition list")
        return selected_competition_list_corrected

    def filter_open_competitions(self, selected_competition_list: list) -> list:
        """Filter and keep only open competitions from the selected list."""
        open_competitions = []
        open_challenge_data = self.user.get_opened_challenges(
            reward="all", kind="competition", fixed_index=None, open_competition=True
        )
        id_list = open_challenge_data["id"].tolist()
        for selected_competition in selected_competition_list:
            if selected_competition in id_list:
                open_competitions.append(selected_competition)
            else:
                logger.info(f"Competition is not open: {selected_competition}")
                logger.info(f"Removing competition from selected list: {selected_competition}")
        return open_competitions

    def filter_competitions_with_submission_limit(self, selected_competition_list: list) -> list:
        """Filter competitions that have not reached their submission limit."""
        competitions_with_limit = []
        for selected_challenge in selected_competition_list:
            daily_remaining_submission_data = self.user.get_available_remaining_submissions_for_competition(
                selected_challenge
            )
            today_remaining = daily_remaining_submission_data["data"]["today"]
            if today_remaining > 0:
                competitions_with_limit.append(selected_challenge)
            else:
                logger.info(f"Removing competition {selected_challenge}: submission limit already reached")
        return competitions_with_limit

    def validate_competition_list_not_empty(self, selected_competition_list: list) -> None:
        """Validate that the competition list is not empty."""
        if not selected_competition_list:
            raise SelectedCompetitionListEmptyAfterProcessingError
