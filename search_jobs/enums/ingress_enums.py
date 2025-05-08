from enum import Enum
from app.config import app_config

app_configs = app_config.AppConfig.get_all_configs()


class JobType(Enum):
    HISTORICAL = "historical"
    INCREMENTAL = "incremental"


class IngestionSourceEnum(Enum):
    DOCCEBO_API_COURSE_DATA_INGESTION = "DOCCEBO_API_COURSE_DATA_INGESTION"
    KAAS_API_DATA_INGESTION = "KAAS_API_DATA_INGESTION"
