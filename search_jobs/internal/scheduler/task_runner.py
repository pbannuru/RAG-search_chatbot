from datetime import datetime, timedelta
from enum import Enum
import sched, time
from traceback import print_exception
from app.config.env import environment
from app.services.core_audit_log_service import CoreAuditLogService
from app.services.job_saves_service import JobSaveService
from app.sql_app.database import DbDepends
from batch_jobs.internal.scheduler.task import Task

import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import app_config
import traceback
# from app.config.env import EnvironmentVars
# JobRunners

app_configs = app_config.AppConfig.get_all_configs()


class TaskRunner:
    _tasks = []

    def add(self, task):
        self._tasks.append(task)
        return self

    def run(self):
        # currentTimeString = current_datetime.strftime("%H:%M:%S")
        # today = current_datetime.strftime("%Y-%m-%d")
        self.__run_jobs_in_sequence()

    def __run_jobs_in_sequence(self):
        current_datetime = datetime.now()

        TASKS: list[Task] = self._tasks
        # currentTime = datetime.strptime(f"{today} {runTime}", "%Y-%m-%d %H:%M:%S")
        for task in TASKS:
            with DbDepends() as db:
                # get job last run details

                job_state = JobSaveService(db).get_job_state(task.task_name)
                task.internal_init(
                    db,
                    current_datetime,
                    last_successful_run=job_state.last_successful_run,
                    last_run=job_state.last_run,
                )
                task.init()

                failed = False
                try:
                    task.run()
                except Exception as e:
                    print_exception(e)
                    traceback_details = traceback.format_exc()
                    task.onerror()

                    failed = True
                    self.send_failure_email(task.task_name, traceback_details, str(e))
                # save job state
                JobSaveService(db).save_job_state(
                    task.task_name, current_datetime, not failed
                )

                task.cleanup()

    def send_failure_email(self, task_name, traceback_details, error_message):
        # Email configuration
        sender_email = app_configs["sender_email"]
        receiver_email = app_configs["receiver_email"]
        current_env = environment.SERVER_ENV.value
        subject = f"Task Failure Alert from env {current_env}: {task_name}"

        # Create the email content
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject
        body = f"The task '{task_name}' has failed.\n\n Error details:\n{traceback_details} \n\n Error message:\n{error_message}"
        msg.attach(MIMEText(body, "plain"))
        host = app_configs["smtp"]
        try:
            # Send the email via SMTP without login
            with smtplib.SMTP(host) as server:
                server.sendmail(sender_email, receiver_email, msg.as_string())
                print(f"Failure notification sent for task: {task_name}")
        except Exception as email_error:
            print(f"Failed to send email notification: {email_error}")
