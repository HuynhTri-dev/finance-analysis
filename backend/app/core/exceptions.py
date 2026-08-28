"""
name: exceptions.py
description: Centralised custom HTTP exception helpers for the auth module.
             All exceptions follow the Envelope Pattern defined in BRD section 7.
"""

from fastapi import HTTPException, status


def credentials_exception(
    code: str = "UNAUTHORIZED", message: str = "Could not validate credentials."
) -> HTTPException:
    """
    Return a 401 Unauthorized HTTPException with a structured error body.

    Input:
        code (str): Error sub-code.
        message (str): Detail message.

    Output:
        HTTPException: Injected 401 exception.

    Description & Logic:
        - Construct a 401 HTTPException with details wrapped in a dict.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_exception(
    code: str = "FORBIDDEN", message: str = "Insufficient permissions."
) -> HTTPException:
    """
    Return a 403 Forbidden HTTPException.

    Input:
        code (str): Error sub-code.
        message (str): Detail message.

    Output:
        HTTPException: Injected 403 exception.

    Description & Logic:
        - Construct a 403 HTTPException.
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": code, "message": message},
    )


def not_found_exception(resource: str = "Resource") -> HTTPException:
    """
    Return a 404 Not Found HTTPException.

    Input:
        resource (str): Name of the resource that was not found.

    Output:
        HTTPException: Injected 404 exception.

    Description & Logic:
        - Construct a 404 HTTPException.
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "NOT_FOUND", "message": f"{resource} not found."},
    )


def conflict_exception(message: str = "Resource already exists.") -> HTTPException:
    """
    Return a 409 Conflict HTTPException.

    Input:
        message (str): Detail message.

    Output:
        HTTPException: Injected 409 exception.

    Description & Logic:
        - Construct a 409 HTTPException.
    """
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "CONFLICT", "message": message},
    )
