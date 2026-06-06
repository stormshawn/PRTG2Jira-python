import datetime
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
import httpx
from app.config import get_instance_config
from urllib.parse import quote
logger: logging.Logger = logging.getLogger(__name__)


class PRTGService():
    def __init__(self):
        self.http_client: httpx.AsyncClient = httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True)

    async def acknowledge_alarm_async(self, instance:str, sensor_id: int, new_jira_ticket_id: str) -> int:
        try:
            response: httpx.Response = await self.http_client.get(self._create_query(f"acknowledgealarm.htm?id={sensor_id}&ackmsg={new_jira_ticket_id}", instance))
            if response.status_code in [200]: # only need 200 since it is a get call 
                logger.info(f"Acknowledge of the sensor with the Sensor ID {sensor_id} was successful.")
                return 0
            else: 
                logger.warning(f"Acknowledge of the sensor with the Sensor ID {sensor_id} was not successful.\n Response was: {response}")
                return sensor_id
        except Exception as e:
            logger.error(f"Error on invoking of PRTG to acknowledge the Alarm for sensor {sensor_id}. Exception: {e}")
            return sensor_id
        
    
    async def append_sensor_comment_async(self, instance: str, sensor_id: int, new_jira_ticket_id: str)-> bool:
        comment: str  = await self._get_sensor_comment_async(instance, sensor_id)
        logger.debug(f"Received current Sensor comment ({sensor_id}) from Server: {comment}: ")
        comment =  f"{comment}\n{datetime.datetime.now()} {new_jira_ticket_id}"
        logger.debug(f"Appended comment ({sensor_id}): {comment}: ")
        return await self._set_sensor_comment_async(instance, sensor_id, comment)


    def _parse_xml_result(self, xml: str)-> Optional[str]:
        root: ET.Element = ET.fromstring(xml) # first two lines
        result_node: Optional[ET.Element] = root.find("result") # prtg will already be the parent node, so we only need to pass result
        return result_node.text if result_node is not None else None
    
    def _create_query(self, query:str, instance: str) -> str: # instance wll be added when the conifig file is made
        base_url: Optional[str] = get_instance_config(instance, "prtg-base-url")
        token: str = get_instance_config(instance, "prtg-token")
        prtg_hash: Optional[str] = get_instance_config(instance, "prtg-hash")
        prtg_username: str = get_instance_config(instance, "prtg-username")
        if token and token.strip():
            return f"https://{base_url}/api/{query}&apitoken={token}"
        elif prtg_username and prtg_username.strip() and prtg_hash and prtg_hash.strip():
             return f"https://{base_url}/api/{query}&username={prtg_username}&passhash={prtg_hash}"
        return ""
    
    async def _get_sensor_comment_async(self, instance: str, sensor_id:int)-> str:
        response: httpx.Response = await self.http_client.get(self._create_query(f"getobjectproperty.htm?id={sensor_id}&name=comments&show=text", instance))
        if response.is_success:
            xml: str = response.text
            result: Optional[str] = self._parse_xml_result(xml)
            return result if result else ""
        return ""
        
    async def _set_sensor_comment_async(self, instance: str, sensor_id: int, comment: str)-> bool:
        response: httpx.Response = await self.http_client.get(self._create_query(f"setobjectproperty.htm?id={sensor_id}&name=comments&value={quote(comment)}", instance))
        if response.is_success:
            logger.info(f"Comment of the sensor with the Sensor ID {sensor_id} was successfully set.")
            return True
        logger.warning(f"Comment of the sensor with the Sensor ID {sensor_id} was not successfully set.")
        return False