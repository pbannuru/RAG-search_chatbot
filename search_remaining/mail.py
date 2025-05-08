import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import app_config

# Load configuration settings
app_configs = app_config.AppConfig.get_all_configs()

def send_failure_email(task_name, error_message, attachments=None):
    # Email configuration
    sender_email = app_configs["sender_email"]
    receiver_email = app_configs["receiver_email"]
    subject = f"Task Failure Alert: {task_name}"
    host = app_configs["smtp"]

    # Create the email content
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    body = f"The task '{task_name}' has failed.\n\nError details:\n{error_message}"
    msg.attach(MIMEText(body, "plain"))

    # Attach any files provided
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, "rb") as file:
                    part = MIMEApplication(file.read(), Name=file_path.split("/")[-1])
                    part['Content-Disposition'] = f'attachment; filename="{file_path.split("/")[-1]}"'
                    msg.attach(part)
            except Exception as file_error:
                print(f"Failed to attach file {file_path}: {file_error}")

    # Send the email
    try:
        with smtplib.SMTP(host) as server:
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"Failure notification sent for task: {task_name}")
    except Exception as email_error:
        print(f"Failed to send email notification: {email_error}")

# Main section to call send_failure_email if this script is run directly
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python mail.py <task_name> <error_message> <attachment1> [<attachment2> ...]")
    else:
        task_name = sys.argv[1]
        error_message = sys.argv[2]
        attachments = sys.argv[3:]  # Collect all remaining arguments as attachment file paths
        send_failure_email(task_name, error_message, attachments)
