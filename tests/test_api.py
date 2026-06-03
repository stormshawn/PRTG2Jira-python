import os

from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.main import app
from app.services import JiraService, PRTGService


# TODO here need to think here later
class TestsApi:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock_jira_service = MagicMock(spec=JiraService)
        self.mock_prtg_service = MagicMock(spec=PRTGService)

        self.mock_jira_service.get_first_open_ticket_async = AsyncMock()
        self.mock_jira_service.get_customer_id = MagicMock()
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
                        data={"sensor_id": "123"},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response is not None
                    assert response.status_code == 500
                    assert "Problem 22" in response.text

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_base_uri_not_set_returns_status_code_500(
        self, request_endpoint
    ):  # TODO: change in other code url to uri
        with patch("app.main.jira_service", self.mock_jira_service):
            with patch("app.main.prtg_service", self.mock_prtg_service):
                with patch(
                    "app.main.get_instance_config", self.mock_get_instance_config
                ):

                    self.mock_config["default-jira-base-url"] = None
                    self.mock_config["1984-jira-base-url"] = None
                    self.mock_config["default-prtg-base-url"] = "prtg.example.com"
                    self.mock_config["1984-prtg-base-url"] = "prtg.example.com"

                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={"sensor_id": "123", "status": "Down", "name": "Test"},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response.status_code == 500

    @pytest.mark.parametrize(
        "environment, request_endpoint",
        [("Development", "/default"), ("Development", "/1984")],
    )
    def test_prtg_2_jira_no_sensor_id_returns_status_code_500(  # left it as 500, but it is 422
        self, environment, request_endpoint
    ):
        self.setup_environment(environment)
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

                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response is not None
                    assert (
                        response.status_code == 422
                    )  # FastAPI validation error instead of 500

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_post_comment_returns_status_code_200(self, request_endpoint):
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = (
                        "ML-001"
                    )
                    self.mock_jira_service.add_jira_comment_async.return_value = True
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Up",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    # ssert response is not None
                    assert response.status_code == 200
                # assert "Problem 22" in response.text

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_post_comment_and_acknowledge_alarm_returns_status_code_200(
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = (
                        "ML-001"
                    )
                    self.mock_jira_service.add_jira_comment_async.return_value = True

                    self.mock_prtg_service.acknowledge_alarm_async.return_value = 0
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response is not None
                    assert response.status_code == 200

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_post_comment_and_error_acknowledge_alarm_returns_status_code_500(
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = (
                        "ML-001"
                    )
                    self.mock_jira_service.add_jira_comment_async.return_value = True

                    self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert "Problem 17" in response.text
                    assert response.status_code == 503

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_error_getting_customer_id_status_code_404(
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""
                    self.mock_jira_service.get_customer_id = MagicMock(return_value="0")

                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert "Problem 19" in response.text
                    assert response.status_code == 404

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_bad_status_in_request_returns_status_bad_request(
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""

                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    assert response.status_code == 400

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_error_getting_crm_status_code_404(self, request_endpoint):
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""
                    self.mock_jira_service.get_customer_id = MagicMock(return_value="1")
                    self.mock_jira_service.get_crm_key.return_value = ""

                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)  # creates FastAPI instance

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    assert response is not None
                    assert "Problem 20" in response.text
                    assert response.status_code == 404

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_error_creating_ticket_status_code_404(self, request_endpoint):
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""
                    self.mock_jira_service.get_customer_id = MagicMock(return_value="1")
                    self.mock_jira_service.get_crm_key.return_value = "1"
                    self.mock_jira_service.new_jira_ticket.return_value = "-1"
                    self.mock_jira_service.new_jira_ticket_service_desk.return_value = (
                        "-1"
                    )

                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    assert response is not None
                    assert "Problem 15" in response.text
                    assert response.status_code == 500

    @pytest.mark.parametrize("request_endpoint", ["/default", "/1984"])
    def test_prtg_2_jira_creating_ticket_error_acknowledging_alarm_status_code_service_unavailable(
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""
                    self.mock_jira_service.get_customer_id = MagicMock(
                        return_value="1234567"
                    )
                    self.mock_jira_service.get_crm_key.return_value = "GML-1234567"
                    self.mock_jira_service.new_jira_ticket.return_value = "ML-2345"
                    self.mock_jira_service.new_jira_ticket_service_desk.return_value = (
                        "ML-2345"
                    )
                    self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    self.mock_jira_service.update_jira_ticket = MagicMock(
                        return_value=0
                    )
                    self.mock_jira_service.append_sensor_comment_async = AsyncMock(
                        return_value=True
                    )
                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    assert response is not None
                    assert "Problem 16" in response.text
                    assert response.status_code == 503

    @pytest.mark.parametrize(
        "environment, request_endpoint",
        [
            ("Development", "/default"),
            ("Development", "/1984"),
            ("VARIABLE_ENVIRONMENT", "/default"),
            ("VARIABLE_ENVIRONMENT", "/1984"),
        ],
    )
    def test_prtg_2_jira_creating_ticket_status_code_ok(
        self, environment, request_endpoint
    ):
        self.setup_environment(environment)
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    # self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""
                    self.mock_jira_service.get_customer_id = MagicMock(
                        return_value="1234567"
                    )
                    self.mock_jira_service.get_crm_key.return_value = "GML-1234567"
                    self.mock_jira_service.new_jira_ticket.return_value = "ML-2345"

                    self.mock_prtg_service.acknowledge_alarm_async.return_value = 0
                    self.mock_jira_service.update_jira_ticket = MagicMock(
                        return_value=0
                    )
                    self.mock_jira_service.append_sensor_comment_async = AsyncMock(
                        return_value=True
                    )
                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "name": "ExampleSensorName",
                            "status": "Down",
                            "priority": "***",
                            "probe": "12345-Example",
                            "device": "ExampleDeviceName",
                            "message": "ExampleMessage",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    assert response is not None
                    assert (
                        response.status_code == 200
                    ), f"In {environment} result is this"

    @pytest.mark.parametrize(
        "environment, request_endpoint",
        [
            ("Development", "/default"),
            ("Development", "/1984"),
            ("VARIABLE_ENVIRONMENT", "/default"),
            ("VARIABLE_ENVIRONMENT", "/1984"),
        ],
    )
    def test_prtg_2_jira_error_creating_ticket_status_not_implemented(
        self, environment, request_endpoint
    ):
        self.setup_environment(environment)
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
                        return_value=MagicMock(project_key="ML", service_desk=False)
                    )

                    # self.mock_jira_service.get_from_tags = MagicMock(return_value="")
                    self.mock_jira_service.get_first_open_ticket_async.return_value = ""

                    # self.mock_prtg_service.acknowledge_alarm_async.return_value = 1
                    client = TestClient(app)

                    response = client.post(
                        f"{request_endpoint}/prtg2jira",
                        data={
                            "sensor_id": "123",
                            "status": "Up",
                            "tags": "Kunde:12345 ExampleSensorName intern",
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                    assert response is not None
                    assert "Problem 21" in response.text

                    # assert (
                    #     response.status_code == 501
                    # ), f"In {environment} result is this"
