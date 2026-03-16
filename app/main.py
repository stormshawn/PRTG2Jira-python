"""
Main application will go here
"""
from contextlib import asynccontextmanager
import logging
from typing import List

from fastapi import FastAPI, HTTPException

from app.config import get_instance_config, get_settings, load_config
from app.middleware.ip_whitelist import IPWhitelistMiddleware
from app.models import JiraProjectSettingsDto
from app.models.JiraRequestDto import JiraRequestDto
from app.services import JiraService, PRTGService

logging.basicConfig(
    level=logging.INFO,
    format="%{astctime}s- %{name}s - %{levelname}s - %{message}s"
)
logger: logging.Logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PRTG service")
    load_config()
    settings = get_settings()
    logger.info(f"Environment: (settings.environment)")
    yield
    logger.info("Shutting down PRTG Service")

app: FastAPI = FastAPI(
    title="PRTG2JIRA API",
    description="Receives notifications from PRTG and creates/updates JIRA issues",
    version="1.0.0",
    lifespan=lifespan
)

settings = get_settings()
if settings.environment=="production":
    app.add_middleware(IPWhitelistMiddleware, allowed_ips=settings.allowed_ips, enabled=True)
    logger.info("IP whitelist middleware enabled")
    
jira_service: JiraService = JiraService()
prtg_service: PRTGService = PRTGService()

@app.get("/status",tags=["Health"], summary="Health Check", description="Returns http OK to verify that the application is running")

async def health_check():
    return {"Status:": "OK"}

@app.post("/{instance}/prtg2jira", tags=["PRTG Integration"], summary="Process PRTG notification", description="Receives http notification from PRTG and creates/updates Jira issue")

async def process_prtg_notification(instance: str, 
                                    status: str = Form(...),
                                    name: str = Form(...),
                                    sensor_id: int = Form(...),
                                    priority: Optional[str] = Form(None),
                                    probe: Optional[str] = Form(None),                                    priority: Optional[str] = Form(None),
                                    device: Optional[str] = Form(None),                                    priority: Optional[str] = Form(None),
                                    message: Optional[str] = Form(None),
                                    tags: Optional[str] = Form(None),
                                    ):


    jira_request: JiraRequestDto = JiraRequestDto(status=status,
                                              name=name,
                                              priority= priority,
                                              probe=probe,
                                              device=device,
                                              message=message,
                                              tags=tags)
    jira_request_instance: str = instance if get_instance_config(instance, "jira-base-url") else "default"
    if not get_instance_config(jira_request_instance, "jira-base-url"):
        logger.error(f"Problem 0 Jira: {jira_request}")
        raise HTTPException(status_code=500, details="Problem 0 Jira")
    
    prtg_request_instance: str = instance if get_instance_config(instance, "prtg-base-url") else "default"
    if not get_instance_config(prtg_request_instance, "prtg-base-url"):
        logger.error(f"Problem 0 PRTG: {jira_request}")
        raise HTTPException(status_code=500, details="Problem 0 PRTG")
    
    project: JiraProjectSettingsDto = jira_service.get_project_from_tags(tags, instance, "Projects")
    tenant: str = jira_service.get_from_tags(tags, instance, "Tenant")
    reporter: str = jira_service.get_from_tags(tags, instance, "Reporter")
    comment_internal: bool = jira_service.get_from_tags(tags, instance, "Comment").lower() != "extern"

    if not project.project_key:
        logger.error(f"Problem 22: {jira_request}") 
        raise HTTPException(status_code=500, details="Problem 22")
    
    if project.service_desk and (not project.service_desk_id or not project.request_type_id):
        logger.error(f"Problem 26: {jira_request}") 
        raise HTTPException(status_code=500, details="Problem 26")


    open_ticket_key: str = await jira_service.get_first_open_ticket_async(jira_instance, jira_request.sensor_id, project.project_key)

    down_warning_statuses: List[str] = ["Down",
		 "Down (before: Warning)",
		 "Warning",
		 "Warning (before: Down)",
		 "Warning ended (now: Down)",
		 "Down ended (now: Warning)"]
    up_ended_statuses: List[str] = ["Down ended (now: Up)",
		 "Down ended (now: Paused)",
		 "Warning ended (now: Up)",
		 "Up"]
