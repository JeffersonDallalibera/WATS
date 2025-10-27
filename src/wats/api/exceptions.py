# WATS_Project/wats_app/api/exceptions.py

"""
Custom exceptions for the recording upload API system.
"""

class ApiError(Exception):
    """Base exception for all API-related errors."""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class AuthenticationError(ApiError):
    """Raised when API authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class NetworkError(ApiError):
    """Raised when network connection fails."""
    def __init__(self, message: str = "Network connection failed"):
        super().__init__(message, status_code=0)

class ServerError(ApiError):
    """Raised when the server returns an error."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code=status_code)

class ValidationError(ApiError):
    """Raised when request validation fails."""
    def __init__(self, message: str = "Request validation failed"):
        super().__init__(message, status_code=400)

class UploadError(ApiError):
    """Raised when file upload fails."""
    def __init__(self, message: str = "File upload failed"):
        super().__init__(message, status_code=422)