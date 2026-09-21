import enum


class UserRole(str, enum.Enum):
    OFFICER = "OFFICER"
    SUPERVISOR = "SUPERVISOR"
    OPERATOR = "OPERATOR"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RECEIVED = "RECEIVED"
    COLLECTED = "COLLECTED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"

class SessionEndReason(str, enum.Enum):
    LOGOUT = "LOGOUT"
    EXPIRED = "EXPIRED"
