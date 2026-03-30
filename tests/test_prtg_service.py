import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services import PRTGService


@pytest.fixture
def prtg_service():
    return PRTGService()


@pytest.mark.asyncio
class TestsPRTGServiceAsync:
    async def test_acknowledge_alarm_with_token_and_successful_call_returns_zero(self):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-token": "sample-token",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 0
        service.http_client.get.assert_called_once()  # check later why not populating
        call_args = service.http_client.get.call_args[0][0]
        assert "id=123" in call_args
        assert "ackmsg=JIRA-123" in call_args
        assert "apitoken=sample-token" in call_args

    async def test_acknowledge_alarm_async_with_token_and_failed_call_returns_sensor_id(
        self,
    ):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-token": "sample-token",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 123
        service.http_client.get.assert_called_once()  # check later why not populating
        call_args = service.http_client.get.call_args[0][0]
        assert "id=123" in call_args
        assert "ackmsg=JIRA-123" in call_args
        assert "apitoken=sample-token" in call_args

    async def test_acknowledge_alarm_async_with_pass_hash_and_successful_call_returns_zero(
        self,
    ):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-username": "sample.username",
                "default-prtg-hash": "abc123",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 0

    async def test_acknowledge_alarm_async_with_pass_hash_and_missing_username_returns_sensor_id(
        self,
    ):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-hash": "abc123",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        # mock_response.status_code = 200
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            # service.http_client.get() = AsyncMock(return_value = mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 123

    async def test_acknowledge_alarm_async_missing_hash_returns_sensor_id(self):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-username": "sample.username",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        # mock_response.status_code = 200
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            # service.http_client.get() = AsyncMock(return_value = mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 123

    async def test_acknowledge_alarm_async_without_uri_variable_returns_sensor_id(self):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-token": "sample-token",
                "default-prtg-base-uri": "",
            }
            return config_values.get(f"{instance}-{key}")

        mock_response = MagicMock()
        # mock_response.status_code = 200
        mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            # service.http_client.get() = AsyncMock(return_value = mock_response)
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 123

    async def test_acknowledge_alarm_async_exception_thrown_returns_sensor_id(self):
        service = PRTGService()  # check on why it's not working with prtg_service()

        def mock_get_config(instance: str, key: str):
            config_values = {
                "default-prtg-token": "sample-token",
                "default-prtg-base-uri": "prtg.sample.com",
            }
            return config_values.get(f"{instance}-{key}")

        # mock_response = MagicMock()
        # mock_response.status_code = 404
        # mock_response.text = "TEST VALUE"
        with patch("app.services.PRTGService.get_instance_config", mock_get_config):
            service.http_client.get = AsyncMock(
                side_effect=httpx.RequestError("Some error Test")
            )
            result = await service.acknowledge_alarm_async("default", 123, "JIRA-123")
        assert result == 123
