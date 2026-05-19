import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.timer_status import TimerStatus, TimerState
from app.services import timer_service
from app.repositories import timer_repository
from app.main import app

# --- Fixtures ---
@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com", is_active=True)

# --- Service Tests ---
@pytest.mark.asyncio
async def test_service_reset_timer_creates_default_config_and_active_status():
    user_id = uuid4()
    db = AsyncMock()
    
    # Mock Config Object
    mock_config = MagicMock()
    mock_config.period = 86400
    mock_config.is_active = True
    
    # Mock Repository methods using patch
    # Note: We patch where it is IMPORTED in the service, or the module itself
    with patch("app.repositories.timer_repository.get_user_config", new_callable=AsyncMock) as mock_get_config, \
         patch("app.repositories.timer_repository.create_user_config", new_callable=AsyncMock) as mock_create_config, \
         patch("app.repositories.timer_repository.get_timer_status", new_callable=AsyncMock) as mock_get_status, \
         patch("app.repositories.timer_repository.create_timer_status", new_callable=AsyncMock) as mock_create_status:
        
        mock_get_config.return_value = None
        mock_create_config.return_value = mock_config
        mock_get_status.return_value = None
        
        # side_effect to return the argument passed to create_timer_status
        def create_status_side_effect(db, status):
            return status
        mock_create_status.side_effect = create_status_side_effect
        
        # Call Service (calling the module function directly)
        result = await timer_service.reset_timer(db, user_id)
        
        mock_create_config.assert_called_once()
        mock_create_status.assert_called_once()
        assert result.status == TimerState.ACTIVE
        assert result.deadline_timestamp is not None

# --- API Tests ---
@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_api_reset_timer(async_client, override_deps, mock_user):
    # Mock service.reset_timer to return a specific status
    mock_status = TimerStatus(
        user_id=mock_user.id,
        status=TimerState.ACTIVE,
        deadline_timestamp=datetime.utcnow(),
        last_check_in=datetime.utcnow()
    )
    
    with patch("app.services.timer_service.reset_timer", new_callable=AsyncMock) as mock_reset:
        mock_reset.return_value = mock_status
        
        response = await async_client.post("/api/v1/timer/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(mock_user.id)
        assert data["status"] == "active"
        mock_reset.assert_called_once()
