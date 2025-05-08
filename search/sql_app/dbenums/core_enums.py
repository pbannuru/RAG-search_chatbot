from enum import Enum as EnumEnum


class PersonaEnum(EnumEnum):
    Operator = "operator"
    Engineer = "engineer"


class DomainEnum(EnumEnum):
    Indigo = "indigo"
    PWP = "pwp"
    Scitex= "scitex"
    ThreeD= "ThreeD"


class SourceEnum(EnumEnum):
    All = "all"
    KZ = "kz"
    Kaas = "kaas"
    Docebo = "docebo"


class LanguageEnum(EnumEnum):
    English = "en"
    Chinese = "zh"
    French = "fr"
    German = "de"
    Japanese = "ja"
    Korean = "ko"
    Portuguese = "pt"
    Russian = "ru"
    Spanish = "es"
    Italian = "it"
    PortugueseBr = "pt-BR"
    Hebrew = "he"
    SpanishLatam = "es-419"
    Hungarian = "hu"
    Dutch = "nl"
    SimplifiedChinese = "zh-CN"
    Others = "xx"  # Handles other unspecified languages
