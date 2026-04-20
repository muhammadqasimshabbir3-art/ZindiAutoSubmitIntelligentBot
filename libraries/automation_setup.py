"""
Automation setup and initialization utilities.
Handles Jira integration, directory setup, and error tracking.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from libraries.bitwarden_credential import BitwardenCredentialManagement
from libraries.Config import CONFIG
from libraries.jira_setup import JiraManager
from libraries.logging_file import log_build_info, logger


class AutomationSetup:
    """Handles automation setup, Jira integration, and error tracking."""

    def __init__(self):
        """Initialize automation setup."""
        self.jira_manager: Optional[JiraManager] = None
        self.jira_issue_key: Optional[str] = None
        bitwarden = BitwardenCredentialManagement()
        self.all_items = bitwarden.get_credential("jira_credentials")
        self._initialize_jira()
        self._setup_directories()
        self._log_startup_info()

    def _get_custom_field(self, item: dict, field_name: str):
        """Extract custom field value from Bitwarden item."""
        fields = item.get("fields", [])
        for f in fields:
            if f.get("name") == field_name:
                return f.get("value")
        return None

    def _initialize_jira(self) -> None:
        """Initialize Jira connection if credentials are available."""
        try:
            jira_credential = self.all_items  # direct item dictionary

            # --- GET SERVER FROM CUSTOM FIELD ---
            jira_server = (
                self._get_custom_field(jira_credential, "server") or CONFIG.JIRA_SERVER or os.getenv("JIRA_SERVER", "")
            )

            # --- GET USERNAME FROM BITWARDEN (LOGIN USERNAME) ---
            jira_username = (
                jira_credential.get("username", "") or CONFIG.JIRA_USERNAME or os.getenv("JIRA_USERNAME", "")
            )

            # --- GET API TOKEN (PASSWORD FIELD) ---
            jira_api_token = (
                jira_credential.get("password", "") or CONFIG.JIRA_API_TOKEN or os.getenv("JIRA_API_TOKEN", "")
            )

            print("📌 SERVER:", jira_server)
            print("📌 USERNAME:", jira_username)
            print("📌 TOKEN:", jira_api_token[:6] + "*****")

            # --- Initialize Jira only if all values exist ---
            if jira_server and jira_username and jira_api_token:
                self.jira_manager = JiraManager(server=jira_server, username=jira_username, api_token=jira_api_token)
                logger.info("Jira manager initialized successfully")
            else:
                logger.warning("Jira credentials missing. Skipping Jira initialization.")

        except Exception as e:
            logger.warning(f"Failed to initialize Jira: {str(e)}. Continuing without Jira integration.")

    def _setup_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        try:
            directories = [
                CONFIG.DIRECTORIES.TEMP,
                CONFIG.DIRECTORIES.OUTPUT,
                CONFIG.DIRECTORIES.MAPPING,
                CONFIG.ZindiCompetitionFilesPath.competition_folder,
                CONFIG.ZindiCompetitionFilesPath.submission_file_folder,
            ]
            for directory in directories:
                if isinstance(directory, Path):
                    directory.mkdir(parents=True, exist_ok=True)
                elif isinstance(directory, str):
                    os.makedirs(directory, exist_ok=True)
            logger.info("Directories setup completed")
        except Exception as e:
            logger.error(f"Error setting up directories: {str(e)}")

    def _log_startup_info(self) -> None:
        """Log startup information."""
        logger.info("=" * 60)
        logger.info("Zindi Automation Submission Bot - Starting")
        logger.info("=" * 60)
        logger.info(f"Environment: {'Robocorp' if CONFIG.IS_ROBOCORP else 'Local'}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if CONFIG.BITBUCKET_WORKSPACE:
            logger.info(f"Bitbucket Workspace: {CONFIG.BITBUCKET_WORKSPACE}")
        log_build_info()

    def create_jira_issue(self) -> Optional[str]:
        """Create a Jira issue for tracking this automation run."""
        if not self.jira_manager:
            return None

        try:
            project_key = CONFIG.JIRA_PROJECT_KEY or os.getenv("JIRA_PROJECT_KEY", "AUTO")
            summary = f"Zindi Automation Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            description = f"""
Automation Run Details:
- Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Environment: {'Robocorp' if CONFIG.IS_ROBOCORP else 'Local'}
- Competitions: {', '.join(CONFIG.INPUTS.selected_competition_names_to_work)}
- Bot: Zindi Automation Submission Bot

This issue tracks the automation execution and any errors encountered.
            """.strip()

            issue_key = self.jira_manager.create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type="Task",
                labels=["automation", "zindi", "bot"],
            )
            if issue_key:
                logger.info(f"Created Jira issue for tracking: {issue_key}")
                self.jira_issue_key = issue_key
                return issue_key
        except Exception as e:
            logger.warning(f"Failed to create Jira issue: {str(e)}")
        return None

    def update_jira_issue_status(self, status: str, comment: str = "") -> None:
        """Update Jira issue with status and comment."""
        if not self.jira_manager or not self.jira_issue_key:
            return

        try:
            if comment:
                self.jira_manager.add_comment(self.jira_issue_key, comment)
            self.jira_manager.update_issue(self.jira_issue_key, status=status)
        except Exception as e:
            logger.warning(f"Failed to update Jira issue: {str(e)}")

    def handle_error(self, error: Exception) -> None:
        """Handle errors and create/update Jira issues."""
        error_type = type(error).__name__
        error_message = str(error)

        logger.error(f"Error occurred: {error_type} - {error_message}")

        if not self.jira_issue_key and self.jira_manager:
            self.jira_issue_key = self.create_jira_issue()

        if self.jira_issue_key and self.jira_manager:
            error_comment = f"""
Error Details:
- Error Type: {error_type}
- Error Message: {error_message}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            self.jira_manager.add_comment(self.jira_issue_key, error_comment)
            self.jira_manager.update_issue(
                self.jira_issue_key, status="In Progress", labels=["automation", "zindi", "bot", "error"]
            )
