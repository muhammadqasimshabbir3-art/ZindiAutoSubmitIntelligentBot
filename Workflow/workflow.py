import pandas as pd
from libraries.bitwarden_credential import BitwardenCredentialManagement
from libraries.Config import CONFIG
from libraries.exception import FileSizeTooLargeToSendThroughGmail
from libraries.logging_file import logger
from libraries.utils import Utils
from libraries.zindi.user import Zindian
from libraries.zindi_site import ZindiProcessing
from Workflow.process import ProcessPreparation


class Processes:
    """whole processes."""

    def __init__(self):
        bitwarden = BitwardenCredentialManagement()
        self.all_items = bitwarden.get_credential("zindi_credentials")
        self.user = Zindian(username=self.all_items["username"], fixed_password=self.all_items["password"])
        logger.info(" Logged into Zindi Successfully using api.")
        self.report_dataframe = pd.DataFrame()
        self.preparation_process = ProcessPreparation(zindi_user=self.user)
        self.report_columns = CONFIG.ReportsFiles.reports_columns
        self.show_leaderboard = CONFIG.INPUTS.show_leader_board
        self.show_rank = CONFIG.INPUTS.user_rank_for_selected_competition
        self.upload_submission_file = CONFIG.INPUTS.upload_submission_file
        self.download_dataset = CONFIG.INPUTS.download_dataset_for_selected_competition_name
        self.show_daily_submission_remaining = CONFIG.INPUTS.show_daily_submission
        self.zindi_processing = ZindiProcessing(
            self.user,
            credentials=self.all_items,
            show_leaderboard=self.show_leaderboard,
            show_rank=self.show_rank,
            upload_submission_file=self.upload_submission_file,
            download_dataset=self.download_dataset,
            daily_submission_remaining=self.show_daily_submission_remaining,
            report_dataframe=pd.DataFrame(columns=self.report_columns),
        )
        self.utils = Utils(credential=self.all_items)

    def prepare_files_for_processing(self):
        """Prepare files for processing."""
        self.preparation_process.get_opened_competition_names_and_create_dirs()
        if self.preparation_process.check_submission_files():
            logger.info("File format checks passed.")
        selected_competition_list = self.preparation_process.normalize_selected_competition_names()
        selected_competition_list = self.preparation_process.filter_open_competitions(selected_competition_list)
        selected_competition_list = self.preparation_process.filter_competitions_with_submission_limit(
            selected_competition_list
        )
        self.preparation_process.validate_competition_list_not_empty(selected_competition_list)
        return selected_competition_list

    def process_zindi_site(self, submission_files_checking: list) -> None:
        """Process Zindi site for selected competitions."""
        self.zindi_processing.selected_competitions_to_work(submission_files_checking)

    # TODO: This method implementation if I have time in future
    # def generate_report(self):
    #     """Generate report of all competition submission process."""
    #     pass

    def send_report_to_gmail(self):
        """Send report to user email."""
        try:
            files_size_dict = self.utils.check_attachment_size_for_email(list(CONFIG.DIRECTORIES.REPORT))
            for file_name, file_size in files_size_dict.items():
                if file_size >= 25.0:
                    logger.info("File has 25MB or more - only uploading to SharePoint")
                    raise FileSizeTooLargeToSendThroughGmail
                self.utils.send_report_via_email(file_name)
                logger.info("============== Files sent to Gmail =================")
        except Exception as e:
            logger.error(e)
        finally:
            # TODO: Try to upload file to SharePoint either way if sent to Gmail or not.
            pass

    def start(self):
        """Start processing."""
        selected_competition_list = self.prepare_files_for_processing()
        self.process_zindi_site(selected_competition_list)
        self.send_report_to_gmail()
