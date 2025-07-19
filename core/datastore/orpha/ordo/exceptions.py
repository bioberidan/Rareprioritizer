"""
Custom exceptions for Orpha Disease Preprocessing System
"""


class OrphaException(Exception):
    """Base exception for all Orpha-related errors"""
    pass


class XMLParsingError(OrphaException):
    """Raised when XML parsing fails"""
    pass


class TaxonomyError(OrphaException):
    """Base exception for taxonomy-related errors"""
    pass


class NodeNotFoundError(TaxonomyError):
    """Raised when a requested node (disease or category) is not found"""
    def __init__(self, node_id: str, node_type: str = "node"):
        self.node_id = node_id
        self.node_type = node_type
        super().__init__(f"{node_type.capitalize()} with ID '{node_id}' not found")


class AmbiguousNameError(TaxonomyError):
    """Raised when a name resolves to multiple IDs"""
    def __init__(self, name: str, ids: list):
        self.name = name
        self.ids = ids
        super().__init__(
            f"Name '{name}' is ambiguous, found {len(ids)} matches: {', '.join(ids)}"
        )


class DataIntegrityError(OrphaException):
    """Raised when data integrity issues are detected"""
    pass


class FileNotFoundError(OrphaException):
    """Raised when required data files are not found"""
    pass


class InvalidDataFormatError(OrphaException):
    """Raised when data format is invalid or corrupted"""
    pass


class MemoryLimitExceededError(OrphaException):
    """Raised when memory usage exceeds configured limits"""
    def __init__(self, current_mb: float, limit_mb: float):
        self.current_mb = current_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"Memory usage ({current_mb:.1f}MB) exceeds limit ({limit_mb:.1f}MB)"
        )


class ValidationError(OrphaException):
    """Raised when data validation fails"""
    def __init__(self, message: str, issues: list = None):
        self.issues = issues or []
        super().__init__(message) 