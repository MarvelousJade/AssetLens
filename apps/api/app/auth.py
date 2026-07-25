from typing import Annotated

from fastapi import Header, HTTPException, status

from .config import settings


def require_demo_user(authorization: Annotated[str | None, Header()] = None) -> str:
    expected = f"Bearer {settings.demo_token}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Enter the demo workspace to access portfolio data.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return "demo-user"
