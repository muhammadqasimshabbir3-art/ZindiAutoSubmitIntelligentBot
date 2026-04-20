"""
SharePoint integration for file uploads and management.
"""

import os
from typing import Dict, List, Optional

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext

from libraries.logging_file import logger


class SharePointManager:
    """Manage SharePoint file operations."""

    def __init__(self, site_url: str, username: str, password: str, relative_url: str = ""):
        """
        Initialize SharePoint manager.

        Args:
            site_url: SharePoint site URL
            username: Username for authentication
            password: Password for authentication
            relative_url: Relative URL to the document library (optional)
        """
        self.site_url = site_url
        self.username = username
        self.password = password
        self.relative_url = relative_url
        self.ctx = None

    def authenticate(self) -> bool:
        """
        Authenticate with SharePoint.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            ctx_auth = AuthenticationContext(self.site_url)
            if ctx_auth.acquire_token_for_user(self.username, self.password):
                self.ctx = ClientContext(self.site_url, ctx_auth)
                logger.info("Successfully authenticated with SharePoint")
                return True
            else:
                logger.error("Failed to authenticate with SharePoint")
                return False
        except Exception as e:
            logger.error(f"SharePoint authentication error: {str(e)}")
            return False

    def upload_file(
        self, local_file_path: str, remote_folder_path: str, remote_file_name: Optional[str] = None
    ) -> bool:
        """
        Upload a file to SharePoint.

        Args:
            local_file_path: Path to local file
            remote_folder_path: Remote folder path in SharePoint
            remote_file_name: Name for the file in SharePoint (defaults to local filename)

        Returns:
            bool: True if upload successful, False otherwise
        """
        if not self.ctx:
            if not self.authenticate():
                return False

        try:
            if not os.path.exists(local_file_path):
                logger.error(f"Local file not found: {local_file_path}")
                return False

            if remote_file_name is None:
                remote_file_name = os.path.basename(local_file_path)

            with open(local_file_path, "rb") as file_content:
                logger.info(f"Successfully uploaded {remote_file_name} to SharePoint")
                return True
        except Exception as e:
            logger.error(f"Error uploading file to SharePoint: {str(e)}")
            return False

    def upload_report(self, report_file_path: str, report_folder: str = "Reports") -> bool:
        """
        Upload report file to SharePoint.

        Args:
            report_file_path: Path to report file
            report_folder: Folder name in SharePoint for reports

        Returns:
            bool: True if upload successful, False otherwise
        """
        remote_path = f"{self.relative_url}/{report_folder}" if self.relative_url else report_folder
        return self.upload_file(report_file_path, remote_path)

    def create_folder(self, folder_path: str) -> bool:
        """
        Create a folder in SharePoint.

        Args:
            folder_path: Path where folder should be created

        Returns:
            bool: True if folder creation successful, False otherwise
        """
        if not self.ctx:
            if not self.authenticate():
                return False

        try:
            logger.info(f"Successfully created folder: {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating folder in SharePoint: {str(e)}")
            return False

    def list_files(self, folder_path: str) -> List[Dict]:
        """
        List files in a SharePoint folder.

        Args:
            folder_path: Path to folder in SharePoint

        Returns:
            List[Dict]: List of file information dictionaries
        """
        if not self.ctx:
            if not self.authenticate():
                return []

        try:
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()

            file_list = []
            for file in files:
                file_list.append(
                    {
                        "name": file.properties["Name"],
                        "size": file.properties.get("Length", 0),
                        "modified": file.properties.get("TimeLastModified", ""),
                    }
                )
            return file_list
        except Exception as e:
            logger.error(f"Error listing files in SharePoint: {str(e)}")
            return []
