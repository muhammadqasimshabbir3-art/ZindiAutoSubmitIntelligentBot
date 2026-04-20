import logging
import mimetypes
import os
import shutil
import smtplib
from email.message import EmailMessage


class Utils:
    """utils method defined"""

    def __init__(self, credential):
        """Initialize Utils with credentials."""
        self.credential = credential

    def check_attachment_size_for_email(self, file_paths: list) -> dict:
        """Check size of attachments before sending email."""
        file_sizes = {}
        for file_path in file_paths:
            try:
                # Get the file size in bytes
                file_size_bytes = os.path.getsize(file_path)
                # Convert the size to MB
                file_size_mb = file_size_bytes / (1024 * 1024)
                file_sizes[file_path] = round(file_size_mb, 2)  # Round to 2 decimal places
                print(f"File: {file_path}, Size: {file_sizes[file_path]} MB")
            except FileNotFoundError:
                print(f"File {file_path} not found.")
                file_sizes[file_path] = None
        return file_sizes

    def send_report_via_email(self, report_path):
        """Send generated report to given email addresses."""
        # Email Configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        email_sender = self.credential.get("Email", {}).get("sender", "")
        app_password = self.credential.get("Email", {}).get("app_password", "")
        email_receiver = self.credential.get("Email", {}).get("receiver", "")
        subject = "Automated Report"
        body = "Hello,\n\nPlease find the attached report.\n\nBest Regards, Zindi Automation Bot"

        # Create Email
        msg = EmailMessage()
        msg["From"] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = subject
        msg.set_content(body)

        # Attach File
        if os.path.exists(report_path):
            with open(report_path, "rb") as file:
                file_data = file.read()
                file_type, _ = mimetypes.guess_type(report_path)
                file_type = file_type or "application/octet-stream"
                msg.add_attachment(
                    file_data,
                    maintype=file_type.split("/")[0],
                    subtype=file_type.split("/")[1],
                    filename=os.path.basename(report_path),
                )

        # Send Email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_sender, app_password)
                server.send_message(msg)
            print(f"✅ Email sent successfully to {email_receiver}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")

    def send_reports_via_email(self, reports_files_path: list):
        """Send multiple report files via email."""
        for report_path in reports_files_path:
            self.send_report_via_email(report_path)


def remove_subdirectories(parent_dir):
    """Remove all directories inside the given parent directory."""
    if not os.path.exists(parent_dir):
        print(f"Path does not exist: {parent_dir}")
        return

    for item in os.listdir(parent_dir):
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path):
            try:
                shutil.rmtree(item_path)
                print(f"Removed directory: {item_path}")
            except Exception as e:
                print(f"Failed to remove {item_path}: {e}")

    logging.info("remove sub directory from competition folder")
