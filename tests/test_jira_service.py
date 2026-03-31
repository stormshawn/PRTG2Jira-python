import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from app.services import JiraService


def mock_jira_config(instance: str, key: str) -> str:
    config_values = {
        "default-jira-token": "sample-token",
        "default-jira-base-uri": "jira.sample.com",
    }
    return config_values.get(f"{instance}-{key}")


@pytest.mark.asyncio
class TestsJiraService:
    async def test_add_jira_comment_successfully_post_comment_return_void_async(self):
        service = JiraService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Comment Set"
        with patch("app.services.JiraService.get_instance_config", mock_jira_config):
            service.http_client.post = AsyncMock(return_value=mock_response)
            result = await service.add_jira_comment_async(
                "default",
                "ML-0002",
                "test Device",
                "Sensor Name",
                "Down",
                "Test Error Message",
            )

        assert result is True

    async def test_add_jira_comment_error_posting_comment_return_void_async(self):
        service = JiraService()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "No Comment Set"
        with patch("app.services.JiraService.get_instance_config", mock_jira_config):
            service.http_client.post = AsyncMock(return_value=mock_response)
            result = await service.add_jira_comment_async(
                "default",
                "ML-0002",
                "test Device",
                "Sensor Name",
                "Down",
                "Test Error Message",
            )
        assert result is False

    def get_customer_id_customer_number_tag_not_probe_return_customer_number(self):
        service = JiraService()
        result = service.get_customer_id("Customer:123 sensor tag", "123ProbeName")
        assert result is not None
        assert result == "123"

    def test_get_customer_id_customer_number_probe_not_tag_length_smaller_five_return_zero(
        self,
    ):
        service = JiraService()
        result = service.get_customer_id("12345 sensor tag", "12345-probename")
        assert result is not None
        assert result == "12345"

    # CRM Section Tests
    async def test_get_crm_key_wrong_customer_number_returns_empty_with_error_log_async(
        self,
    ):
        service = JiraService()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        with patch("app.services.JiraService.get_instance_config", mock_jira_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.get_crm_key("default", "1234", "default-tenant")
        assert result is not None
        assert result == ""

    async def test_get_crm_key_customer_number_error_retrieving_request_returns_empty_with_error_log_async(
        self,
    ):
        service = JiraService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "WRONG JSON"
        mock_response.json = MagicMock(side_effect=Exception("Test Json Error"))
        with patch("app.services.JiraService.get_instance_config", mock_jira_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.get_crm_key("default", "12345", "default-tenant")
        assert result is not None
        assert result == ""

    async def test_get_crm_key_customer_number_successfully_retrieving_request_returns_crm_number(
        self,
    ):
        service = JiraService()
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_response.json = MagicMock(
            return_value={
                "objectEntries": [
                    {"id": 5678, "label": "test Client", "objectKey": "GML-5678"}
                ]
            }
        )
        with patch("app.services.JiraService.get_instance_config", mock_jira_config):
            service.http_client.get = AsyncMock(return_value=mock_response)
            result = await service.get_crm_key("default", "12345", "default-tenant")
        assert result is not None
        assert result == "GML-5678"

    async def test_get_project_from_tags_one_tag_in_config_returns_value_async(self):
        service = JiraService()
        mock_settings = MagicMock()
        mock_settings.instances = {
            "1984": {
                "Projects": {
                    "default": {"projectKey": "ML"},
                    "intern": {"projectKey": "INTERN"},
                }
            }
        }
        with patch("app.services.JiraService.get_settings", return_value=mock_settings):
            result = await service.get_project_from_tags(
                "something intern", "1984", "Projects"
            )
        assert result is not None

    #     assert result == "INTERN"

    # async def test_get_project_from_tags_two_tag_in_config_returns_default_value_async(
    #     test,
    # ):
    #     service = JiraService()
    #     mock_settings = MagicMock()
    #     mock_settings.instances = {
    #         "1984": {
    #             "Projects": {"default": "ML", "intern": "INTERN", "example": "EXAMPLE"}
    #         }
    #     }
    #     with patch("app.services.JiraService.get_settings", return_value=mock_settings):
    #         result = await service.get_project_from_tags("something intern example")
    #     assert result is not None
    #     assert result == "ML"

    # async def test_get_project_from_tags_no_tag_in_config_returns_default_value_async(
    #     self,
    # ):
    #     service = JiraService()
    #     mock_settings = MagicMock()
    #     mock_settings.instances = {
    #         "1984": {
    #             "Projects": {
    #                 "default": "ML",
    #             }
    #         }
    #     }
    #     with patch("app.services.JiraService.get_settings", return_value=mock_settings):
    #         result = await service.get_project_from_tags("something intern")
    #     assert result is not None
    #     assert result == "ML"

    # async def test_get_project_from_tags_default_not_in_config_returns_empty_async(
    #     self,
    # ):
    #     service = JiraService()
    #     mock_settings = MagicMock()
    #     mock_settings.instances = {"1984": {"Projects": {"intern": "INTERN"}}}
    #     with patch("app.services.JiraService.get_settings", return_value=mock_settings):
    #         result = await service.get_project_from_tags("something example")
    #     assert result is not None
    #     assert result == ""

    # async def test_get_project_from_tags_two_tags_and_default_not_in_config_returns_empty_async(
    #     self,
    # ):
    #     service = JiraService()
    #     mock_settings = MagicMock()
    #     mock_settings.instances = {
    #         "1984": {"Projects": {"intern": "INTERN", "example": "EXAMPLE"}}
    #     }
    #     with patch("app.services.JiraService.get_settings", return_value=mock_settings):
    #         result = await service.get_project_from_tags("something intern example")
    #     assert result is not None
    #     assert result == ""
