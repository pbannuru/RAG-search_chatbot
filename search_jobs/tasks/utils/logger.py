
import os
import datetime
import logging
import pandas as pd


def get_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")


class LogConfig:
    """
    Configuration class for logging settings.
    """

    def __init__(
        self,
        log_dir="PROJECT_logs",
        log_level=logging.INFO,
        format_string="[%(asctime)s]^;%(levelname)s^;%(lineno)d^;%(filename)s^;%(funcName)s()^;%(message)s",
    ):
        self.log_dir = log_dir
        self.log_level = log_level
        self.format_string = format_string


def get_log_file_name(prefix, date):
    """
    Generates a log file name with a given prefix and date.
    """
    return f"log_{prefix}_{date}.log"


def setup_logging(config=LogConfig()):
    """
    Sets up logging configuration based on provided LogConfig object.

    Args:
        config (LogConfig, optional): Configuration object with desired settings. Defaults to LogConfig().
    """
    os.makedirs(config.log_dir, exist_ok=True)

    # Determine current date
    current_date = get_current_date()

    # Set up all log file path
    all_log_file_path = os.path.join(
        config.log_dir, get_log_file_name(prefix="all", date=current_date)
    )
    error_log_file_path = os.path.join(
        config.log_dir, get_log_file_name(prefix="error", date=current_date)
    )

    # Set up all log handler
    all_handler = logging.FileHandler(all_log_file_path, mode="a")  # Append mode
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(logging.Formatter(config.format_string))

    # Set up error log handler
    error_handler = logging.FileHandler(error_log_file_path, mode="a")  # Append mode
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(config.format_string))

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(all_handler)
    root_logger.addHandler(error_handler)


def get_log_dataframe(file_path):
    data = []
    with open(file_path) as log_file:
        for line in log_file.readlines():
            data.append(line.split("^;"))

    log_df = pd.DataFrame(data)
    columns = [
        "Time stamp",
        "Log Level",
        "Line number",
        "File name",
        "Function name",
        "Message",
    ]
    log_df.columns = columns

    log_df["log_message"] = log_df["Time stamp"].astype(str) + ": $" + log_df["Message"]

    return log_df[["log_message"]]
