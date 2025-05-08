
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
from app.config import app_config
from app.config.env import EnvironmentVars


app_configs = app_config.AppConfig.get_all_configs()
environment = EnvironmentVars()

def send_error_report_email(df, sender_email, receiver_email):
    # Extract data from DataFrame
    data = []
    for row in df.iterrows():
        document_id = row["Record"]["documentID"]
        source = "KAAS_API"
        domain = row["Record"]["Domain"]
        content_update_date = row["Record"]["contentUpdateDate"]
        error_message = row["Error"]
        data.append([document_id, source, domain, content_update_date, error_message])

    # Convert data to DataFrame
    data_df = pd.DataFrame(
        data,
        columns=[
            "Document ID",
            "Source",
            "Domain",
            "Content Update Date",
            "Error Message",
        ],
    )

    # Save DataFrame to an Excel file
    csv_filename = "error_data.xlsx"

    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Error Report"

    # Add body text
    body = """Dear [Recipient],\n\nI hope this message finds you well.\nPlease find the attached file containing the report for the KAAS data ingest errors.\n\nIf you have any questions or need further clarification, feel free to reach out.\n\nBest regards,\n---"""
    message.attach(MIMEText(body, "plain"))

    # Convert DataFrame to Excel in memory
    in_memory_fp = io.BytesIO()
    data_df.to_excel(in_memory_fp, index=False, engine="xlsxwriter")

    # Add the Excel file as an attachment
    part = MIMEApplication(in_memory_fp.getvalue(), Name=csv_filename)
    # After the file is closed
    part["Content-Disposition"] = 'attachment; filename="%s"' % csv_filename
    message.attach(part)
    host = app_configs["smtp"]
    # Connect to the SMTP server and send email
    with smtplib.SMTP(host) as smtp:
        smtp.sendmail(sender_email, receiver_email, message.as_string())

# Example usage
sender_email = app_configs["sender_email"]
receiver_email = app_configs["receiver_email"]