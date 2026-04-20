import os
from pathlib import Path


class Configuration:
    logger_file_path = "app.log"

    # Environment detection
    IS_ROBOCORP = (
        os.getenv("RPA_SECRET_MANAGER") == "Robocorp.Vault.FileSecrets"
        or os.getenv("RC_ENVIRONMENT") is not None
        or os.path.exists("/tmp/robocorp-temp")
    )

    # Bitbucket credentials from environment
    BITBUCKET_WORKSPACE = os.getenv("BITBUCKET_WORKSPACE", "")
    BITBUCKET_USERNAME = os.getenv("BITBUCKET_USERNAME", "")
    BITBUCKET_APP_PASSWORD = os.getenv("BITBUCKET_APP_PASSWORD", "")
    BITBUCKET_REPO_SLUG = os.getenv("BITBUCKET_REPO_SLUG", "")

    # Jira configuration from environment (fallback if not in Bitwarden)
    JIRA_SERVER = os.getenv("JIRA_SERVER", "")
    JIRA_USERNAME = os.getenv("JIRA_USERNAME", "")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
    JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "AUTO")

    class DIRECTORIES:
        """
        This class serves as a container for any directories you require for your automation
        these will be created automatically or would already exist
        """

        # Use Robocorp output directory if in Robocorp, otherwise use local
        _is_robocorp = (
            os.getenv("RPA_SECRET_MANAGER") == "Robocorp.Vault.FileSecrets"
            or os.getenv("RC_ENVIRONMENT") is not None
            or os.path.exists("/tmp/robocorp-temp")
        )
        if _is_robocorp:
            BASE = Path(os.getenv("ROBOT_ARTIFACTS", "/tmp/robocorp-temp"))
        else:
            BASE = Path().cwd()

        TEMP = BASE / "temp"
        OUTPUT = BASE / "output"
        REPORT = OUTPUT / "submission_report.csv"
        SUBMSSION_FILES = BASE / f"{OUTPUT}/subimssionfiles"
        OUTPUT_SCREENSHOTS = os.path.join(OUTPUT, "screenshots")
        MAPPING = OUTPUT / "mapping"

    class ReportsFiles:
        """Reports of submissions of competitions."""

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
        """List of Credential groups."""

        items_list = ["Phantom Wallet", "Zindi_Credential", "SharePoint", "Jira"]

    class ZindiCompetitionFilesPath:
        """Zindi competitions files paths."""

        competition_folder = Path().cwd() / "Competitions"
        submission_file_folder = Path().cwd() / "SubmissionFilesFolder"

    class INPUTS:
        selected_competition_names_to_work = [
            "barbados-traffic-analysis-challenge",
            "agribora-commodity-price-forecasting-challenge",
        ]
        download_dataset_for_selected_competition_name = False
        show_leader_board = False
        user_rank_for_selected_competition = True
        upload_submission_file = True
        show_daily_submission = True


CONFIG = Configuration()
