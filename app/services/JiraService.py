from typing import Any, Dict, List, Optional
import httpx
import logging
from app.config import get_instance_config, get_settings, Settings
from app.models import (
    CommentParametersDto,
    InsightDto,
    IssueDto,
    JiraProjectSettingsDto,
    PropertyDto,
    ValueDto,
)

logger: logging.Logger = logging.getLogger(__name__)


class JiraService:
    def __init__(self):
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(timeout=30)

    async def get_first_open_ticket_async(
        self, jira_instance: str, sensor_id: int, project: str
    ) -> Optional[str]:
        """
        Searches for an existing open ticket for given sensor id

        """
        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        query_url: str = (
            f'project="{project}" AND status IN (Open, Paused, "In Progress", "Waiting for Customer", "Waiting for Vendor Support") AND description ~ "id={sensor_id}"'
        )
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response: httpx.Response = await self.http_client.get(
                f"https://{base_url}/rest/api/2/search",
                params={"jql": query_url},
                headers=headers,
            )
            if response.status_code == 200:
                data: Dict[str, Any] = response.json()
                issues: List[Dict[str, Any]] = data.get("issues", [])
                if issues:
                    return issues[0].get("key")
            return None
        except Exception as e:
            # None # going to write a logger here eventually
            logger.error(f"Error getting open Tickets. Exception: {e}.")
            return None

    async def add_jira_comment_async(
        self,
        jira_instance: str,
        ticket: str,
        device: str,
        name: str,
        status: str,
        message: str,
        comment_internal: bool = True,
    ) -> bool:
        """
        Writing comment later
        """
        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        # comment_template: str = "*This is an automatically created comment by PRTG:* {0}{0}The device {1} with the name {2} shows the status {3}.{0}The PRTG message is: {4}"
        comment: str = (
            f"This is an automatically created comment by PRTG: The device {device} with the name {name} shows the status  {status}.The PRTG message is: \n\n{message}"
        )
        valuepayload: ValueDto = ValueDto()
        valuepayload.internal = comment_internal
        ticket_parameters: CommentParametersDto = CommentParametersDto(
            body=comment,
            properties=[
                PropertyDto(key="sd.public.comment", value_payload=valuepayload)
            ],
        )
        logger.info("%s", ticket_parameters.body)
        logger.info("%s", ticket_parameters.properties[0].key)
        logger.info("%s", ticket_parameters.properties[0].value_payload.internal)
        json_string: Dict[str, Any] = ticket_parameters.model_dump(by_alias=True)
        logger.info("%s", json_string)

        response: httpx.Response = await self.http_client.post(
            f"https://{base_url}/rest/api/latest/issue/{ticket}/comment",
            json=json_string,
            headers=headers,
        )

        if response.status_code not in [200, 201]:
            logger.error(
                "Error on invoking AddJiraComment to create a comment on the ticket [%s].Response:{%s} Payload:{%s}",
                ticket,
                response.text,
                json_string,
            )
            return False
        logger.info("%s", response)
        return True

    def get_customer_id(self, tags: str, probe: str) -> str:
        found_customer_number: bool = (
            False  # c# is in german, so make sure there aren't other dependencies with kundenummer when using this method
        )
        customer_number: str = ""
        for tag in tags.split(" "):
            if not found_customer_number and "Customer:" in tag and tag.strip():
                customer_number = tag.split(":")[1]
                logger.info(
                    f"The submitted Kontonummer from the tags was: {customer_number}"
                )
                found_customer_number = True
        if not found_customer_number:
            probe_split = probe.split("-")[0]
            if len(probe_split) >= 5 and probe_split.isdigit():
                logger.info(
                    f"WARNING: no customer number via Tags available the customer number from the remote-probename was: {probe_split}"
                )
                customer_number = probe_split
            else:
                customer_number = "0"
                logger.warning(
                    "No customer number via Tags or Probe available will not be able to get CRM-Key"
                )
        return customer_number

    async def get_crm_key(
        self, jira_instance: str, customer_number: str, tenant: str
    ) -> str:
        # we will get the url from the config
        # jira_instance will be used once we get the config
        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        params: Dict[str, Any] = {
            "resultPerPage": 1,
            "includeTypeAttributes": "true",
            "includeAttributes": "true",
            "includeAttributesDeep": 5,
            "iql": f'"WL Account Number" = {customer_number} AND "Mandant" = {tenant}',
        }
        try:
            response: httpx.Response = await self.http_client.get(
                f"https://{base_url}/rest/insight/1.0/iql/objects",
                headers=headers,
                params=params,
            )
            if response.status_code in [200]:
                response_body: Dict[str, Any] = response.json()
                object_response: InsightDto = InsightDto(**response_body)
                object_key: str = object_response.object_entries[0].object_key
                logger.info(f"CRM-Key is : {object_key}")
                return object_key
            else:
                logger.warning(
                    f"Error on invoking of Insight to get the CRM-Key: {response}"
                )
                logger.info(f"Customer number: {customer_number} Tenant: {tenant}")
                return ""
        except Exception as e:
            logger.warning(f"Error on invoking of Insight to get the CRM-Key: {e}")
            logger.info(f"Customer number: {customer_number} Tenant: {tenant}")
            return ""

    async def new_jira_ticket_service_desk(
        self,
        device: str,
        name: str,
        status: str,
        message: str,
        sensor_id: int,
        service_desk_id: int,
        request_type_id: int,
        raise_on_behalf_of: str,
        monitoring_instance: str,
        jira_instance: str,
    ) -> str:

        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        prtg_url: str = get_instance_config(monitoring_instance, "prtg-base-url")
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        ticket_parameters: Dict[str, Any] = {
            "serviceDeskId": service_desk_id,
            "requestTypeId": request_type_id,
            "requestFieldValues": {
                "summary": f"[PRTG] {device} {name} {status}",
                "description": (
                    f"This is an automatically created issue by PRTG.\n"
                    f"The device {device} with the name {name} shows the status {status}.\n"
                    f"The PRTG message is {message} \n"
                    f"The URL from the sensor is: https://{prtg_url}/sensor.htm?id={sensor_id}&tabid=1"
                ),
            },
            "raiseOnBehalfOf": raise_on_behalf_of,
        }
        # ticketjson not required

        try:
            response: httpx.Response = await self.http_client.post(
                f"https://{base_url}/rest/servicedeskapi/request",
                json=ticket_parameters,
                headers=headers,
            )
            if response.status_code in [200, 201]:
                created_issue: Dict[str, Any] = response.json()
                issue_response: IssueDto = IssueDto(**created_issue)
                issue_key: str = issue_response.key
                if issue_key and issue_key.strip():
                    logger.info(f"The Issue-Key is {issue_key}")
                    return issue_key
                else:
                    logger.error(f"Could not Parse Response. SensorID : {sensor_id}")
                    logger.debug(f"{ticket_parameters}")
                    return "-1"
            else:
                logger.error(
                    f"Error on invoking of NewJiraTicket to create the Ticket. {response}"
                )
                logger.debug(f"{ticket_parameters}")
                return "-1"
        except Exception as e:
            logger.error(
                f"Error on invoking of NewJiraTicket to create the Ticket. {e}"
            )
            logger.debug(f"{ticket_parameters}")
            return "-1"

    async def new_jira_ticket(
        self,
        device: str,
        name: str,
        status: str,
        message: str,
        sensor_id: int,
        project: str,
        monitoring_instance: str,
        jira_instance: str,
    ) -> str:

        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        prtg_url: str = get_instance_config(monitoring_instance, "prtg-base-url")
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        ticket_parameters: Dict[str, Any] = {
            "fields": {
                "project": {"key": project},
                "issuetype": {"name": "Incident"},
                "summary": f"[PRTG] {device} {name} {status}",
                "description": (
                    f"This is an automatically created issue by PRTG.\n"
                    f"The device {device} with the name {name} shows the status {status}.\n"
                    f"The PRTG message is {message} \n"
                    f"The URL from the sensor is: https://{prtg_url}/sensor.htm?id={sensor_id}&tabid=1"
                ),
            }
        }
        # ticketjson not required

        try:
            response: httpx.Response = await self.http_client.post(
                f"https://{base_url}/rest/api/latest/issue",
                json=ticket_parameters,
                headers=headers,
            )
            if response.status_code in [200, 201]:
                created_issue: Dict[str, Any] = response.json()
                issue_response: IssueDto = IssueDto(**created_issue)
                issue_key: str = issue_response.key
                if issue_key and issue_key.strip():
                    logger.info(f"The Issue-Key is {issue_key}")
                    return issue_key
                else:
                    logger.error(f"Could not Parse Response. SensorID : {sensor_id}")
                    logger.debug(f"{ticket_parameters}")
                    return "-1"
            else:
                logger.error(
                    f"Error on invoking of new_jira_ticket to create the Ticket. {response}"
                )
                logger.debug(f"{ticket_parameters}")
                return "-1"
        except Exception as e:
            logger.error(
                f"Error on invoking of new_jira_ticket to create the Ticket. {e}"
            )
            logger.debug(f"{ticket_parameters}")
            return "-1"

    async def update_jira_ticket(
        self, jira_instance: str, ticket_id: str, crm_key: str, reporter: str
    ) -> int:

        base_url: Optional[str] = get_instance_config(jira_instance, "jira-base-url")
        token: str = get_instance_config(jira_instance, "jira-token")
        headers: Dict[str, Any] = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        ticket_parameters: Dict[str, Any] = {
            "fields": {
                "customfield_10504": [{"key": crm_key}],
                "labels": ["PRTG", "Monitoring"],
                "reporter": {"name": reporter},
            }
        }

        try:
            response: httpx.Response = await self.http_client.put(
                f"https://{base_url}/rest/api/latest/issue/{ticket_id}",
                json=ticket_parameters,
                headers=headers,
            )
            if response.status_code in [200, 204]:
                return 0
            else:
                logger.error(
                    f"Error on invoking of update_jira_ticket to update the Ticket. {response}"
                )
                logger.debug(f"{ticket_parameters}")
            return -1
        except Exception as e:
            logger.error(
                f"Error on invoking of UpdateJiraTicket to update the Ticket: {e}"
            )
            logger.debug(f"{ticket_parameters}")
            return -2

    def get_from_tags(self, tags: str, instance: str, setting: str) -> str:
        settings_obj: Optional[Settings] = get_settings()
        if not settings_obj or not settings_obj.instances:
            return ""
        instance_config: Optional[Dict[str, Any]] = settings_obj.instances.get(instance)
        if not instance_config:
            return ""

        project_keys: Optional[Dict[str, Any]] = instance_config.get(setting)
        if not project_keys:
            return ""
        tag_list: List[str] = tags.split()

        try:
            matched_value: Optional[str] = None
            for key, value in project_keys.items():
                if key.lower() == "default":
                    continue
                if any(tag.lower() in key.lower() for tag in tag_list):
                    matched_value = str(value) if value else None
                    break
            if matched_value:
                return matched_value
            default_value: Optional[str] = None
            if isinstance(project_keys, dict) and "default" in project_keys:
                default_value = (
                    str(project_keys["default"]) if project_keys["default"] else None
                )
            return default_value if default_value else ""
        except Exception as e:
            default_value: Optional[str] = None
            if isinstance(project_keys, dict) and "default" in project_keys:
                default_value = (
                    str(project_keys["default"]) if project_keys["default"] else None
                )
                return default_value if default_value else ""
            return ""

    def get_project_from_tags(
        self, tags: str, instance: str, setting: str
    ) -> JiraProjectSettingsDto:
        settings_obj: Optional[Settings] = get_settings()
        if not settings_obj or not settings_obj.instances:
            return JiraProjectSettingsDto()
        instance_config: Optional[Dict[str, Any]] = settings_obj.instances.get(instance)
        if not instance_config:
            return JiraProjectSettingsDto()
        section: Optional[Dict[str, Any]] = instance_config.get(setting)
        if not section:
            return JiraProjectSettingsDto()

        tag_list: List[str] = tags.split()
        try:
            matched_section: Optional[Dict[str, Any]] = None
            for key, value in section.items():
                if key.lower() == "default":
                    continue
                if any(
                    tag.lower() in key.lower() for tag in tag_list
                ):  # This essentially only checks the second item in the list
                    # I would be curious to know if that is the business workflow needed of the C# code
                    matched_section = value if isinstance(value, dict) else {}
                    break
            if matched_section is None:
                default_section: Optional[Dict[str, Any]] = section.get("default")
                if default_section and isinstance(default_section, dict):
                    matched_section = default_section
            if matched_section is not None:
                settings: JiraProjectSettingsDto = JiraProjectSettingsDto()
                for key, value in matched_section.items():
                    key_lower: str = key.lower()
                    if key_lower == "projectkey":
                        settings.project_key = value if value else ""
                    elif key_lower == "servicedesk":
                        if isinstance(value, bool):
                            settings.service_desk = value
                        else:
                            settings.service_desk = False
                    elif key_lower == "servicedeskid":
                        settings.service_desk_id = int(value) if value else None
                    elif key_lower == "requesttypeid":
                        settings.request_type_id = int(value) if value else None
                return settings
            return JiraProjectSettingsDto()
        except Exception as e:
            return JiraProjectSettingsDto()
