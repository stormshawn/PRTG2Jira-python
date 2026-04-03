import os

from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.main import app
from app.services import JiraService, PRTGService


# TOD here need to think here later
class TestsApi:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_jira_service = MagicMock(spec=JiraService)
        self.mock_prtg_service = MagicMock(spec=PRTGService)

        self.mock_jira_service.get_first_open_ticket_async = AsyncMock()
        self.mock_jira_service.get_customer_id = AsyncMock()
        self.mock_jira_service.get_crm_key = AsyncMock()
        self.mock_jira_service.new_jira_ticket = AsyncMock()
        self.mock_jira_service.new_jira_ticket_service_desk = AsyncMock()

        self.mock_prtg_service.acknowledge_alarm_async = AsyncMock()

        self.mock_config = {}

        yield

    def mock_get_instance_config(self, instance: str, key: str):
        config_key = f"{instance}-{key}"
        return self.mock_config.get(config_key)

    def setup_environment(self, environment: str):
        if environment == "VARIABLE_ENVIRONMENT":
            os.environ["ENVIRONMENT"] = "VARIABLE_ENVIRONMENT"
        elif environment == "Development":
            os.environ["ENVIRONMENT"] = "Development"
        elif environment == "Production":
            os.environ["ENVIRONMENT"] = "Production"
        else:
            raise ValueError(f"Unsupported environment: {environment}")

    @pytest.mark.parametrize("request_endpoint", ["/1984"])
    def test_prtg_2_jira_error_no_project_in_config_returns_status_internal_server_error(
        self, request_endpoint
    ):
        with patch("app.main.jira_service", self.mock_jira_service):
            with patch("app.main.prtg_service", self.mock_prtg_service):
                with patch(
                    "app.main.get_instance_config", self.mock_get_instance_config
                ):
                    # might need to set configs here
                    self.mock_config["default-jira-base-url"] = "jira.example.com"
                    self.mock_config["1984-jira-base-url"] = "jira.example.com"
                    self.mock_config["default-prtg-base-url"] = "prtg.example.com"
                    self.mock_config["1984-prtg-base-url"] = "prtg.example.com"

                    self.mock_jira_service.get_project_from_tags = MagicMock(
                        return_value=MagicMock(project_key=None, service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={"sensor_id": "123", "status": "Down", "name": "Test"},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response is not None
                    assert response.status_code == 500
                    assert "Problem 22" in response.text
