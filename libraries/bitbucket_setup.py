"""
Bitbucket API integration for repository management and deployment.
"""

from base64 import b64encode
from typing import Dict, List, Optional

import requests

from libraries.logging_file import logger


class BitbucketManager:
    """Manage Bitbucket repository operations."""

    def __init__(self, workspace: str, username: str, app_password: str):
        """
        Initialize Bitbucket manager.

        Args:
            workspace: Bitbucket workspace name
            username: Bitbucket username
            app_password: Bitbucket app password (not regular password)
        """
        self.workspace = workspace
        self.username = username
        self.app_password = app_password
        self.base_url = f"https://api.bitbucket.org/2.0/workspaces/{workspace}"
        self.auth = (username, app_password)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        credentials = f"{self.username}:{self.app_password}"
        encoded_credentials = b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_repositories(self, repo_slug: Optional[str] = None) -> List[Dict]:
        """
        Get repository information.

        Args:
            repo_slug: Optional repository slug to get specific repo

        Returns:
            List[Dict]: Repository information
        """
        try:
            if repo_slug:
                url = f"{self.base_url}/repositories/{repo_slug}"
                response = requests.get(url, headers=self._get_headers(), auth=self.auth)
                response.raise_for_status()
                return [response.json()]
            else:
                url = f"{self.base_url}/repositories"
                response = requests.get(url, headers=self._get_headers(), auth=self.auth)
                response.raise_for_status()
                return response.json().get("values", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching repositories: {str(e)}")
            return []

    def trigger_pipeline(self, repo_slug: str, branch: str = "main", custom_variables: Optional[Dict] = None) -> bool:
        """
        Trigger a Bitbucket pipeline.

        Args:
            repo_slug: Repository slug
            branch: Branch to trigger pipeline for
            custom_variables: Optional custom variables for the pipeline

        Returns:
            bool: True if pipeline triggered successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/repositories/{repo_slug}/pipelines"
            data = {"target": {"ref_type": "branch", "type": "pipeline_ref_target", "ref_name": branch}}
            if custom_variables:
                data["target"]["selector"] = {"type": "custom", "pattern": branch}
                data["variables"] = [{"key": k, "value": v} for k, v in custom_variables.items()]

            response = requests.post(url, headers=self._get_headers(), auth=self.auth, json=data)
            response.raise_for_status()
            logger.info(f"Successfully triggered pipeline for {repo_slug} on branch {branch}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error triggering pipeline: {str(e)}")
            return False

    def get_pipeline_status(self, repo_slug: str, pipeline_uuid: Optional[str] = None) -> Optional[Dict]:
        """
        Get pipeline status.

        Args:
            repo_slug: Repository slug
            pipeline_uuid: Optional pipeline UUID to get specific pipeline

        Returns:
            Dict: Pipeline status information
        """
        try:
            if pipeline_uuid:
                url = f"{self.base_url}/repositories/{repo_slug}/pipelines/{pipeline_uuid}"
            else:
                url = f"{self.base_url}/repositories/{repo_slug}/pipelines"
                url += "?page=1&pagelen=1"

            response = requests.get(url, headers=self._get_headers(), auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching pipeline status: {str(e)}")
            return None

    def create_deployment(self, repo_slug: str, environment: str, version: str) -> bool:
        """
        Create a deployment in Bitbucket.

        Args:
            repo_slug: Repository slug
            environment: Deployment environment name
            version: Version/tag to deploy

        Returns:
            bool: True if deployment created successfully, False otherwise
        """
        try:
            url = f"{self.base_url}/repositories/{repo_slug}/deployments"
            data = {
                "environment": {"type": "deployment_environment", "uuid": environment},
                "release": {"type": "release", "name": version},
                "state": {"type": "deployment_state", "name": "PENDING"},
            }

            response = requests.post(url, headers=self._get_headers(), auth=self.auth, json=data)
            response.raise_for_status()
            logger.info(f"Successfully created deployment for {repo_slug} to {environment}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating deployment: {str(e)}")
            return False

    def get_workspace_info(self) -> Optional[Dict]:
        """
        Get workspace information.

        Returns:
            Dict: Workspace information
        """
        try:
            url = f"https://api.bitbucket.org/2.0/workspaces/{self.workspace}"
            response = requests.get(url, headers=self._get_headers(), auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching workspace info: {str(e)}")
            return None
