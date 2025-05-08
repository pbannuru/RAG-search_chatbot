from enum import Enum as EnumEnum


class LogLevelEnum(EnumEnum):
    INFO = "info"
    ERROR = "error"
    CRITICAL = "critical"


class ContextEnum(EnumEnum):
    API = "api"
    SERVICE = "service"


class ServiceEnum(EnumEnum):
    CORE = "core"
    ISEARCHUI = "isearchui"
    JOB = "job"
    EXTRAS = "extras"