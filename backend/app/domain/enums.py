from enum import Enum


class EntityType(str, Enum):
    UI_AREA = "UI_AREA"
    FEATURE = "FEATURE"
    INFRA_UNIT = "INFRA_UNIT"
    API = "API"
    CODE_SYMBOL = "CODE_SYMBOL"
    ISSUE = "ISSUE"


class EntityStatus(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ContextType(str, Enum):
    SUMMARY = "summary"
    DETAILS = "details"
    BUSINESS_RULE = "business_rule"
    VALIDATION_RULE = "validation_rule"
    IMPLEMENTATION_HINT = "implementation_hint"
    SECURITY_NOTE = "security_note"
    INFRA_NOTE = "infra_note"
    COMPATIBILITY_NOTE = "compatibility_note"
    EXCEPTION_CASE = "exception_case"


class RelationType(str, Enum):
    CONTAINS = "CONTAINS"
    RELATED_TO = "RELATED_TO"
    USES = "USES"
    IMPLEMENTED_BY = "IMPLEMENTED_BY"
    READS_FROM = "READS_FROM"
    WRITES_TO = "WRITES_TO"
    DEPENDS_ON = "DEPENDS_ON"
    CALLS = "CALLS"


class Locale(str, Enum):
    KO = "ko"
    EN = "en"
