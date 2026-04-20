"""
Jira integration for issue tracking and project management.
"""

from typing import Dict, List, Optional

from jira import JIRA

from libraries.logging_file import logger


class JiraManager:
    """Manage Jira operations."""

    def __init__(self, server: str, username: str, api_token: str):
        """
        Initialize Jira manager.

        Args:
            server: Jira server URL (e.g., https://your-domain.atlassian.net)
            username: Jira username/email
            api_token: Jira API token
        """
        self.server = server
        self.username = username
        self.api_token = api_token
        self.jira = None
        self._connect()

    def _connect(self) -> bool:
        """
        Connect to Jira.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.jira = JIRA(server=self.server, basic_auth=(self.username, self.api_token))
            logger.info(f"Successfully connected to Jira: {self.server}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Jira: {str(e)}")
            return False

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        custom_fields: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Create a Jira issue.

        Args:
            project_key: Jira project key
            summary: Issue summary/title
            description: Issue description
            issue_type: Type of issue (Task, Bug, Story, etc.)
            assignee: Assignee username (optional)
            priority: Priority level (optional)
            labels: List of labels (optional)
            custom_fields: Custom fields dictionary (optional)

        Returns:
            str: Issue key if created successfully, None otherwise
        """
        if not self.jira:
            if not self._connect():
                return None

        try:
            issue_dict = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
            }

            if assignee:
                issue_dict["assignee"] = {"name": assignee}

            if priority:
                issue_dict["priority"] = {"name": priority}

            if labels:
                issue_dict["labels"] = labels

            if custom_fields:
                issue_dict.update(custom_fields)

            new_issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Successfully created Jira issue: {new_issue.key}")
            return new_issue.key
        except Exception as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            return None

    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """
        Get issue details.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)

        Returns:
            Dict: Issue information
        """
        if not self.jira:
            if not self._connect():
                return None

        try:
            issue = self.jira.issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.name if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.name if issue.fields.reporter else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "labels": issue.fields.labels,
            }
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {str(e)}")
            return None

    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        status: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> bool:
        """
        Update a Jira issue.

        Args:
            issue_key: Jira issue key
            summary: New summary (optional)
            description: New description (optional)
            assignee: New assignee (optional)
            status: New status (optional)
            labels: New labels (optional)

        Returns:
            bool: True if update successful, False otherwise
        """
        if not self.jira:
            if not self._connect():
                return False

        try:
            update_dict = {}
            if summary:
                update_dict["summary"] = summary
            if description:
                update_dict["description"] = description
            if assignee:
                update_dict["assignee"] = {"name": assignee}
            if labels:
                update_dict["labels"] = labels

            issue = self.jira.issue(issue_key)
            issue.update(fields=update_dict)

            if status:
                self.jira.transition_issue(issue, status)

            logger.info(f"Successfully updated issue: {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}")
            return False

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to an issue.

        Args:
            issue_key: Jira issue key
            comment: Comment text

        Returns:
            bool: True if comment added successfully, False otherwise
        """
        if not self.jira:
            if not self._connect():
                return False

        try:
            issue = self.jira.issue(issue_key)
            self.jira.add_comment(issue, comment)
            logger.info(f"Successfully added comment to issue: {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Error adding comment to issue {issue_key}: {str(e)}")
            return False

    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict]:
        """
        Search for issues using JQL.

        Args:
            jql: Jira Query Language query
            max_results: Maximum number of results to return

        Returns:
            List[Dict]: List of issue information
        """
        if not self.jira:
            if not self._connect():
                return []

        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)
            result = []
            for issue in issues:
                result.append(
                    {
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name,
                        "assignee": issue.fields.assignee.name if issue.fields.assignee else None,
                    }
                )
            return result
        except Exception as e:
            logger.error(f"Error searching issues: {str(e)}")
            return []

    def create_subtask(
        self, parent_issue_key: str, summary: str, description: str, assignee: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a subtask.

        Args:
            parent_issue_key: Parent issue key
            summary: Subtask summary
            description: Subtask description
            assignee: Assignee username (optional)

        Returns:
            str: Subtask key if created successfully, None otherwise
        """
        if not self.jira:
            if not self._connect():
                return None

        try:
            parent_issue = self.jira.issue(parent_issue_key)
            project_key = parent_issue.fields.project.key

            issue_dict = {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": "Sub-task"},
                "parent": {"key": parent_issue_key},
            }

            if assignee:
                issue_dict["assignee"] = {"name": assignee}

            new_issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Successfully created subtask: {new_issue.key}")
            return new_issue.key
        except Exception as e:
            logger.error(f"Error creating subtask: {str(e)}")
            return None
