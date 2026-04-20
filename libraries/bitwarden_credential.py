"""
Bitwarden credential management for retrieving secrets.
Supports both local and Robocorp environments.
"""

import json
import os
import subprocess
from typing import Dict, List, Optional

from libraries.logging_file import logger

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class BitwardenCredentialManagement:
    """Manage credentials from Bitwarden."""

    def __init__(self):
        """Initialize Bitwarden credential management."""
        self.is_robocorp = self._detect_robocorp_environment()
        self.bw_session = None
        self.bw_access_token = None
        if not self.is_robocorp:
            # Try OAuth 2.0 first, then fallback to password unlock
            if not self._authenticate_oauth():
                self._unlock_bitwarden()

    def _detect_robocorp_environment(self) -> bool:
        """
        Detect if running in Robocorp environment.

        Returns:
            bool: True if in Robocorp, False otherwise
        """
        return (
            os.getenv("RPA_SECRET_MANAGER") == "Robocorp.Vault.FileSecrets"
            or os.getenv("RC_ENVIRONMENT") is not None
            or os.path.exists("/tmp/robocorp-temp")
        )

    def _authenticate_oauth(self) -> bool:
        """
        Authenticate with Bitwarden using OAuth 2.0 Client Credentials.

        Returns:
            bool: True if authenticated successfully, False otherwise
        """
        try:
            # Get OAuth credentials from environment or .env file, with hardcoded fallback
            client_id = (
                os.getenv("BITWARDEN_CLIENT_ID")
                or os.getenv("BW_CLIENT_ID")
                or "user.648d61a7-a938-4d4f-9f64-b2e3009c72cd"
            )
            client_secret = (
                os.getenv("BITWARDEN_CLIENT_SECRET")
                or os.getenv("BW_CLIENT_SECRET")
                or "4HHpu6bmTHmjzCR8rkULQBxYGmbCsB"
            )

            if not client_id or not client_secret:
                logger.debug("OAuth credentials not found, skipping OAuth authentication")
                return False

            # Check current status and logout if needed
            import time

            status_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)

            if status_result.returncode == 0:
                try:
                    status = json.loads(status_result.stdout)
                    # If already logged in, logout first to allow OAuth login
                    if status.get("status") in ["authenticated", "unlocked", "locked"]:
                        logger.info("Already logged in, logging out to use OAuth credentials")
                        # Force logout - try multiple times to ensure it works
                        for attempt in range(3):
                            logout_result = subprocess.run(
                                ["bw", "logout"], capture_output=True, text=True, check=False
                            )
                            if logout_result.returncode == 0:
                                break
                            time.sleep(0.3)

                        # Verify logout by checking status again
                        time.sleep(0.5)
                        verify_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
                        if verify_result.returncode == 0:
                            try:
                                verify_status = json.loads(verify_result.stdout)
                                if verify_status.get("status") not in ["authenticated", "unlocked"]:
                                    logger.info("Successfully logged out")
                                else:
                                    logger.warning("Logout may not have completed, but continuing with login attempt")
                            except json.JSONDecodeError:
                                pass
                except json.JSONDecodeError:
                    pass

            # Set environment variables for bw CLI
            env = os.environ.copy()
            env["BW_CLIENTID"] = client_id
            env["BW_CLIENTSECRET"] = client_secret

            # Authenticate using OAuth 2.0 client credentials via API key
            # Try using environment variables first (some versions support this)
            result = subprocess.run(
                ["bw", "login", "--apikey", "--raw"],
                input=f"{client_id}\n{client_secret}\n",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            # Check if we got a session token
            if result.returncode == 0 and result.stdout.strip():
                session_token = result.stdout.strip()
                # Verify the session works
                verify_result = subprocess.run(
                    ["bw", "status", "--session", session_token], capture_output=True, text=True, check=False
                )
                if verify_result.returncode == 0:
                    self.bw_session = session_token
                    logger.info("Bitwarden authenticated successfully using OAuth 2.0 (API key)")
                    return True

            # Alternative: Try without --raw flag and then get session
            result = subprocess.run(
                ["bw", "login", "--apikey"],
                input=f"{client_id}\n{client_secret}\n",
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )

            if result.returncode == 0:
                # Wait a moment for login to complete
                time.sleep(1)
                # Get session after successful login
                status_result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
                if status_result.returncode == 0:
                    try:
                        status = json.loads(status_result.stdout)
                        # For API key login, vault might be locked, try to unlock
                        if status.get("status") == "unlocked":
                            self.bw_session = status.get("session")
                            logger.info("Bitwarden authenticated successfully using OAuth 2.0")
                            return True
                        elif status.get("status") == "locked":
                            # Try to unlock with master password from environment, with hardcoded fallback
                            bw_password = (
                                os.getenv("BITWARDEN_PASSWORD")
                                or os.getenv("BW_PASSWORD")
                                or "F$abf7#2z8?EHMU"
                            )
                            if bw_password:
                                # Try unlock with password
                                unlock_result = subprocess.run(
                                    ["bw", "unlock", "--raw"],
                                    input=f"{bw_password}\n",
                                    capture_output=True,
                                    text=True,
                                    check=False,
                                )
                                if unlock_result.returncode == 0 and unlock_result.stdout.strip():
                                    self.bw_session = unlock_result.stdout.strip()
                                    logger.info(
                                        "Bitwarden authenticated and unlocked using OAuth 2.0 with master password"
                                    )
                                    return True

                                # Alternative: Try using passwordenv
                                unlock_result = subprocess.run(
                                    ["bw", "unlock", "--passwordenv", "BITWARDEN_PASSWORD", "--raw"],
                                    capture_output=True,
                                    text=True,
                                    check=False,
                                )
                                if unlock_result.returncode == 0 and unlock_result.stdout.strip():
                                    self.bw_session = unlock_result.stdout.strip()
                                    logger.info(
                                        "Bitwarden authenticated and unlocked using "
                                        "OAuth 2.0 with master password (env)"
                                    )
                                    return True

                            # Try getting session from status after unlock attempt
                            time.sleep(0.5)
                            status_result = subprocess.run(
                                ["bw", "status"], capture_output=True, text=True, check=False
                            )
                            if status_result.returncode == 0:
                                try:
                                    status = json.loads(status_result.stdout)
                                    if status.get("status") == "unlocked":
                                        self.bw_session = status.get("session")
                                        logger.info("Bitwarden authenticated using OAuth 2.0")
                                        return True
                                except json.JSONDecodeError:
                                    pass
                    except json.JSONDecodeError:
                        pass
            logger.warning(
                f"OAuth authentication failed: {result.stderr if result.stderr else 'Unknown error'},"
                f" will try password unlock"
            )
            return False
        except FileNotFoundError:
            logger.warning("Bitwarden CLI not found. OAuth authentication skipped.")
            return False
        except Exception as e:
            logger.warning(f"OAuth authentication failed: {str(e)}")
            return False

    def _unlock_bitwarden(self) -> bool:
        """
        Unlock Bitwarden vault (local only).

        Returns:
            bool: True if unlocked successfully, False otherwise
        """
        try:
            # Check if already unlocked
            result = subprocess.run(["bw", "status"], capture_output=True, text=True, check=False)
            status = json.loads(result.stdout)
            if status.get("status") == "unlocked":
                self.bw_session = status.get("session")
                logger.info("Bitwarden already unlocked")
                return True

            # Try to unlock with environment variable, with hardcoded fallback
            bw_password = os.getenv("BITWARDEN_PASSWORD") or "F$abf7#2z8?EHMU"
            if not bw_password:
                logger.warning("BITWARDEN_PASSWORD not set, trying to unlock interactively")
                return False

            result = subprocess.run(
                ["bw", "unlock", "--passwordenv", "BITWARDEN_PASSWORD", "--raw"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.bw_session = result.stdout.strip()
            logger.info("Bitwarden unlocked successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unlock Bitwarden: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.warning("Bitwarden CLI not found. Using Robocorp Vault or environment variables.")
            return False

    def _get_from_robocorp_vault(self, item_name: str) -> Optional[Dict]:
        """
        Get credential from Robocorp Vault.

        Args:
            item_name: Name of the credential item

        Returns:
            Dict: Credential dictionary or None
        """
        try:
            from RPA.Robocorp.Vault import Vault

            vault = Vault()
            secret = vault.get_secret(item_name)
            logger.info(f"Retrieved {item_name} from Robocorp Vault")
            return secret
        except ImportError:
            logger.warning("RPA.Robocorp.Vault not available")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Robocorp Vault: {str(e)}")
            return None

    def _get_from_bitwarden(self, item_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get credential from Bitwarden (local).

        Args:
            item_name: Name of the credential item. If None, returns all items.

        Returns:
            Dict: Credential dictionary or None. If item_name is None, returns dict of all items.
        """
        if not self.bw_session:
            logger.error("Bitwarden not unlocked")
            return None

        try:
            # If no item_name provided, get all items
            if item_name is None:
                result = subprocess.run(
                    ["bw", "list", "items", "--session", self.bw_session], capture_output=True, text=True, check=True
                )
                items = json.loads(result.stdout)
                all_credentials = {}

                for item in items:
                    item_name_key = item.get("name", f"item_{item.get('id', 'unknown')}")
                    credential = {}

                    # Extract login credentials
                    if "login" in item:
                        login = item["login"]
                        credential["username"] = login.get("username", "")
                        credential["password"] = login.get("password", "")

                    # Extract custom fields
                    if "fields" in item:
                        for field in item["fields"]:
                            credential[field.get("name", "")] = field.get("value", "")

                    all_credentials[item_name_key] = credential

                logger.info(f"Retrieved {len(all_credentials)} items from Bitwarden")
                return all_credentials

            # Search for specific item
            result = subprocess.run(
                ["bw", "list", "items", "--search", item_name, "--session", self.bw_session],
                capture_output=True,
                text=True,
                check=True,
            )
            items = json.loads(result.stdout)
            if not items:
                logger.warning(f"Item '{item_name}' not found in Bitwarden")
                return None

            # Get the first matching item
            item = items[0]
            credential = {}

            # Extract login credentials
            if "login" in item:
                login = item["login"]
                credential["username"] = login.get("username", "")
                credential["password"] = login.get("password", "")

            # Extract custom fields
            if "fields" in item:
                for field in item["fields"]:
                    credential[field.get("name", "")] = field.get("value", "")

            logger.info(f"Retrieved {item_name} from Bitwarden")
            return credential
        except subprocess.CalledProcessError as e:
            logger.error(f"Error retrieving from Bitwarden: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Bitwarden response: {str(e)}")
            return None

    def _get_from_environment(self, item_name: str) -> Optional[Dict]:
        """
        Get credential from environment variables (fallback).

        Args:
            item_name: Name of the credential item

        Returns:
            Dict: Credential dictionary or None
        """
        # Try common environment variable patterns

        username = os.getenv(f"{item_name.upper()}_USERNAME") or os.getenv(f"{item_name.upper()}_USER")
        password = os.getenv(f"{item_name.upper()}_PASSWORD") or os.getenv(f"{item_name.upper()}_PASS")

        if username and password:
            logger.info(f"Retrieved {item_name} from environment variables")
            return {"username": username, "password": password}

        return None

    def _get_hardcoded_credentials(self, item_name: str) -> Optional[Dict]:
        """
        Get hardcoded credentials as last resort fallback.

        Args:
            item_name: Name of the credential item

        Returns:
            Dict: Credential dictionary or None
        """
        # Hardcoded credentials fallback
        hardcoded_credentials = {
            "zindi_credentials": {
                "username": "asadkhanbloch4949@gmail.com",
                "password": "Qasim7878,,"
            },
            "jira_credentials": {
                "username": "nighatshabbir@gmail.com",
                "password": "F$abf7#2z8?EHMU",
            },
        }

        if item_name in hardcoded_credentials:
            logger.warning(f"Using hardcoded credentials for {item_name} (all other methods failed)")
            return hardcoded_credentials[item_name]

        return None

    def get_credential(self, item_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get a single credential by name, or all credentials if item_name is None.

        Args:
            item_name: Name of the credential item. If None, returns all items.

        Returns:
            Dict: Credential dictionary or None. If item_name is None, returns dict of all items.
        """
        # If no item_name provided, get all items from Bitwarden
        if item_name is None:
            if not self.is_robocorp:
                all_items = self._get_from_bitwarden(None)
                if all_items:
                    return all_items
            logger.warning("Getting all items is only supported for Bitwarden (not Robocorp Vault)")
            return None

        # Try Robocorp Vault first
        if self.is_robocorp:
            credential = self._get_from_robocorp_vault(item_name)
            if credential:
                return credential

        # Try Bitwarden (local)
        credential = self._get_from_bitwarden(item_name)
        if credential:
            return credential

        # Fallback to environment variables
        credential = self._get_from_environment(item_name)
        if credential:
            return credential

        # Last resort: hardcoded credentials
        credential = self._get_hardcoded_credentials(item_name)
        if credential:
            return credential

        logger.error(f"Could not retrieve credential: {item_name}")
        return None

    def get_bitwarden_credentials(self, items_list: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Get multiple credentials from Bitwarden/Robocorp Vault.

        Args:
            items_list: List of credential item names. If None, returns all items.

        Returns:
            Dict: Dictionary of credentials keyed by item name
        """
        # If no items_list provided, get all items
        if items_list is None:
            all_items = self.get_credential(None)
            if all_items:
                return all_items
            return {}

        credentials = {}
        for item_name in items_list:
            credential = self.get_credential(item_name)
            if credential:
                credentials[item_name] = credential
            else:
                logger.warning(f"Failed to retrieve credential: {item_name}")
        return credentials
