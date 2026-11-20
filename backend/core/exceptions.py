"""
NSBM EduSphere — Core Exceptions Hierarchy
Standard domain exceptions and HTTP error mappings
"""
from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class EduSphereException(Exception):
    """Base exception for all EduSphere domain exceptions"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundException(EduSphereException):
    """Raised when a requested resource does not exist"""
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(f"{entity_name} with identifier '{identifier}' was not found.")
        self.entity_name = entity_name
        self.identifier = identifier


NotFoundException = EntityNotFoundException


class UnauthorizedException(EduSphereException):
    """Raised when authentication is missing or invalid"""
    def __init__(self, message: str = "Authentication required or invalid credentials"):
        super().__init__(message)


class ForbiddenException(EduSphereException):
    """Raised when user lacks permission to access a resource"""
    def __init__(self, message: str = "Access forbidden: insufficient permissions"):
        super().__init__(message)


class ConflictException(EduSphereException):
    """Raised on state or uniqueness conflicts (e.g. duplicate username or email)"""
    def __init__(self, message: str):
        super().__init__(message)


class ValidationException(EduSphereException):
    """Raised when input fails domain validation rules"""
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=errors)
