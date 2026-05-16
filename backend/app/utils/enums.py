import enum


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"
    AGENT = "Agent"
    VIEWER = "Viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PropertyStatus(str, enum.Enum):
    AVAILABLE = "available"
    PENDING = "pending"
    RENTED = "rented"
    OFFLINE = "offline"
    NEED_CONFIRM = "need_confirm"
