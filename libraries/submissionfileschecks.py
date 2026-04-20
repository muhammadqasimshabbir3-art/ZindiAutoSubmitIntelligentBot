import os
import shutil
from pathlib import Path

from libraries.Config import CONFIG
from libraries.logging_file import logger


class SubmissionFilesChecks:
    """Define SubmissionFilesChecks  which will be used to check format"""

    def __init__(self, credential=None):
        self.credential = credential

        pass

    def is_submission_file_present(self) -> bool:
        """Check if submission file is present in directory for processing."""
        submission_folder = Path(CONFIG.ZindiCompetitionFilesPath.submission_file_folder)
        if not submission_folder.exists():
            return False
        for file in os.listdir(submission_folder):
            if file.endswith(".csv"):
                return True
        return False

    def check_submission_filename_format(self) -> bool:
        """
        Check if all CSV filenames in submission_folder start with a competition name from base_directory.
        Return True if submission file name format is okay, which is {competition_name}_......csv.
        Otherwise, print mismatched files and return False.
        """
        competition_names = [
            d.name for d in Path(CONFIG.ZindiCompetitionFilesPath.competition_folder).iterdir() if d.is_dir()
        ]
        # Get all CSV files in submission_folder
        csv_files = list(Path(CONFIG.ZindiCompetitionFilesPath.submission_file_folder).glob("*.csv"))
        if not csv_files:
            print("No CSV Files Found")
            return False
        # Find mismatched files
        mismatched_files = [
            csv_file.name
            for csv_file in csv_files
            if not any(csv_file.stem.startswith(name) for name in competition_names)
        ]
        if mismatched_files:
            logger.info(f"Mismatched files: {mismatched_files}")
            return False
        return True

    def move_submission_files_to_respective_competition_folder(self) -> bool:
        """Move submission files to respective competition folder for uploading/posting."""
        competition_folder = Path(CONFIG.ZindiCompetitionFilesPath.competition_folder)
        submission_folder = Path(CONFIG.ZindiCompetitionFilesPath.submission_file_folder)

        competition_dirs = [
            d for d in os.listdir(competition_folder) if os.path.isdir(os.path.join(competition_folder, d))
        ]
        csv_files = [f for f in os.listdir(submission_folder) if f.endswith(".csv")]
        for competition in competition_dirs:
            competition_dir = competition_folder / competition
            for file in csv_files:
                if file.startswith(competition):
                    source_file = submission_folder / file
                    destination_file = competition_dir / file
                    shutil.move(str(source_file), str(destination_file))
                    logger.info(f"Moved {file} to {destination_file}")
        return True

    def check_if_competition_names_and_format_correct(self):
        """Check if the given competition names are correct."""
        pass
