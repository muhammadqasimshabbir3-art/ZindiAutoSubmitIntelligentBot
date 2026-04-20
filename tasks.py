"""
Zindi Automation Submission Bot.

This module represents a Digital Worker for automating Zindi competition submissions.
It is designed to work in both local and Robocorp environments.

Important:
    Be sure to run 'pre-commit' before pushing changes to ensure code quality.
"""

import shutil
from datetime import datetime
from pathlib import Path

from robocorp.tasks import task

from libraries.automation_setup import AutomationSetup
from libraries.Config import CONFIG
from libraries.exception import (
    FileSizeTooLargeToSendThroughGmail,
    IncorrectSubmissionFilesNames,
    SelectedCompetitionListEmptyAfterProcessingError,
    SubmissionFilesNotPresentFolder,
)
from libraries.logging_file import log_build_info, logger
from Workflow.workflow import Processes


def setup_sample_submission_file():
    """Copy hardcoded sample CSV file to SubmissionFilesFolder."""
    sample_csv = Path(__file__).parent / "barbados-traffic-analysis-challenge_submission.csv"
    submission_folder = CONFIG.ZindiCompetitionFilesPath.submission_file_folder

    if sample_csv.exists():
        # Ensure submission folder exists
        submission_folder.mkdir(parents=True, exist_ok=True)

        # Copy the CSV file to submission folder
        destination = submission_folder / sample_csv.name
        if not destination.exists():
            shutil.copy2(sample_csv, destination)
            logger.info(f"Copied sample submission file to {destination}")
        else:
            logger.info(f"Sample submission file already exists at {destination}")
    else:
        logger.warning(f"Sample CSV file not found at {sample_csv}")


@task
def task() -> None:
    """
    Point of entry for our Digital Worker's process.

    This function serves as the entry point for the automation process. It initializes
    the necessary components and executes the workflow. Any exceptions are handled
    and logged, with Jira issue updates for tracking.

    Returns:
        None

    Raises:
        Exception: Any exceptions raised during the workflow execution are logged.
    """
    # Setup output directory (Robocorp pattern)
    output_dir = Path(CONFIG.DIRECTORIES.OUTPUT)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize automation setup (Jira, directories, logging)
    setup = AutomationSetup()

    # Setup sample submission file
    setup_sample_submission_file()

    # Create Jira issue for tracking
    setup.create_jira_issue()

    process = Processes()
    try:
        process.start()

        # Update Jira issue on success
        success_comment = f"""
Automation completed successfully!
- End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: Success
        """.strip()
        setup.update_jira_issue_status("Done", success_comment)

        logger.info("=" * 60)
        logger.info("Automation completed successfully")
        logger.info("=" * 60)

    except SelectedCompetitionListEmptyAfterProcessingError as e:
        setup.handle_error(e)
        logger.error("No valid competitions found after processing")
        raise

    except SubmissionFilesNotPresentFolder as e:
        setup.handle_error(e)
        logger.error("Submission files not found in the expected folder")
        raise

    except IncorrectSubmissionFilesNames as e:
        setup.handle_error(e)
        logger.error("Submission file names are incorrect")
        raise

    except FileSizeTooLargeToSendThroughGmail as e:
        setup.handle_error(e)
        logger.warning("File too large for email, will upload to SharePoint")
        # Don't raise, continue with SharePoint upload

    except Exception as e:
        setup.handle_error(e)
        logger.exception(e)
        raise
    finally:
        # Cleanup or finalization if needed
        pass


if __name__ == "__main__":
    """Entry point when running the script directly."""
    try:
        log_build_info()
    except Exception as e:
        logger.error(f"Failed to log build info: {e}")

    logger.info("Starting Zindi Automation Submission Bot")
    task()
    logger.info("Zindi Automation Submission Bot task complete")
