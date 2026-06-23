from unittest.mock import MagicMock, patch
import pytest
from starlette.requests import Request
from starlette.responses import Response
from api.v1.users import get_user_profile
from models.user import User

@patch("api.v1.users.get_user_version")
def test_get_user_profile_minimal(mock_get_user_version):
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/users/me",
        "headers": [],
        "client": ("127.0.0.1", 5000),
    }
    request = Request(scope)
    response = Response()
    current_user = User(id=1, email="test@test.com", role="user", is_email_verified=True)
    
    result = get_user_profile(
        request=request,
        response=response,
        current_user=current_user,
        minimal=True
    )
    
    assert result == {"status": "logged_in"}
    mock_get_user_version.assert_not_called()


@patch("api.v1.users.get_user_version")
def test_get_user_profile_full(mock_get_user_version):
    mock_get_user_version.return_value = 42
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/users/me",
        "headers": [],
        "client": ("127.0.0.1", 5000),
    }
    request = Request(scope)
    response = Response()
    
    current_user = User(
        id=123,
        email="test@test.com",
        first_name="John",
        last_name="Doe",
        company_name="Company",
        phone="123456",
        avatar_url="http://avatar.com",
        auth_provider="local",
        role="user",
        created_at="2026-01-01",
        updated_at="2026-01-02",
        is_email_verified=True
    )
    
    result = get_user_profile(
        request=request,
        response=response,
        current_user=current_user,
        minimal=False
    )
    
    assert result["status"] == "success"
    assert result["user_info"]["id"] == 123
    assert result["user_info"]["email"] == "test@test.com"
    mock_get_user_version.assert_called_once_with(123)
