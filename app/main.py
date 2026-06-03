from contextlib import asynccontextmanager
import logging
from typing import List, Optional

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from app.config import get_instance_config, get_settings, load_config
from app.middleware import IPWhitelistMiddleware
from app.models import JiraProjectSettingsDto, ProblemResponseDto, JiraRequestDto
from app.services import JiraService, PRTGService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s- %(name)s - %(levelname)s - %(message)s"  #
)
logger: logging.Logger = logging.getLogger(
    __name__
)  # Making a logger instance for the main class


def _problem_response(detail: str, status_code: int) -> JSONResponse:
    problem: ProblemResponseDto = ProblemResponseDto(
        detail=detail, status_code=status_code
    )
    return JSONResponse(
        status_code=status_code, content=problem.model_dump(by_alias=True)
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os

    logger.info("Starting PRTG service")
    load_config()
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    yield
    logger.info("Shutting down PG Service")


app: FastAPI = FastAPI(
    title="PRTG2JIRA API",
    description="Receives notifications from PRTG and creates/updates JIRA issues",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
if settings.environment == "production":
    app.add_middleware(
        IPWhitelistMiddleware, allowed_ips=settings.allowed_ips, enabled=True
    )
    logger.info("IP whitelist middleware enabled")

jira_service: JiraService = JiraService()
prtg_service: PRTGService = PRTGService()


@app.get(  # get endpoint used to define an endpoint, to see if app is down
    "/status",
    tags=["Health"],
    summary="Health Check",
    description="Returns http OK to verify that the application is running",
)
async def health_check():
    return {"status": "OK"}


@app.post(  # used to create resources and returns responses 200 or 201 (depending on the use case)
    "/{instance}/prtg2jira",
    tags=["PRTG Integration"],
    summary="Process PRTG notification",
    description="Receives http notification from PRTG and creates/updates Jira issue",
)
async def process_prtg_notification(  # when prtg server hits this endpoint, it sends in these arguments
    instance: str,  # TODO: change from instance to jira_instance
    status: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    sensor_id: int = Form(...),
    priority: Optional[str] = Form(None),
    probe: Optional[str] = Form(None),
    device: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):

    jira_request: JiraRequestDto = JiraRequestDto(
        status=status,
        name=name,
        sensor_id=sensor_id,
        priority=priority,
        probe=probe,
        device=device,
        message=message,
        tags=tags,
    )
    jira_request_instance: str = (
        instance if get_instance_config(instance, "jira-base-url") else "default"
    )
    if not get_instance_config(jira_request_instance, "jira-base-url"):
        logger.error(f"Problem 0 Jira: {jira_request}")
        return _problem_response("Problem 0 Jira", 500)

    prtg_request_instance: str = (
        instance if get_instance_config(instance, "prtg-base-url") else "default"
    )
    if not get_instance_config(prtg_request_instance, "prtg-base-url"):
        logger.error(f"Problem 0 PRTG: {jira_request}")
        return _problem_response("Problem 0 PRTG", 500)

    project: JiraProjectSettingsDto = jira_service.get_project_from_tags(
        tags, instance, "Projects"
    )
    tenant: str = jira_service.get_from_tags(tags, instance, "Tenant")
    reporter: str = jira_service.get_from_tags(tags, instance, "Reporter")

    comment_value = jira_service.get_from_tags(tags, instance, "Comment") or ""
    comment_internal: bool = comment_value.lower() != "extern"

    if not project.project_key:
        logger.error(f"Problem 22: {jira_request}")
        return _problem_response("Problem 22", 500)

    if project.service_desk and (
        not project.service_desk_id or not project.request_type_id
    ):
        logger.error(f"Problem 26: {jira_request}")
        return _problem_response("Problem 26", 500)

    open_ticket_key: str = await jira_service.get_first_open_ticket_async(
        jira_request_instance, jira_request.sensor_id, project.project_key
    )

    down_warning_statuses: List[str] = [
        "Down",
        "Down (before: Warning)",
        "Warning",
        "Warning (before: Down)",
        "Warning ended (now: Down)",
        "Down ended (now: Warning)",
    ]
    up_ended_statuses: List[str] = [
        "Down ended (now: Up)",
        "Down ended (now: Paused)",
        "Warning ended (now: Up)",
        "Up",
    ]
    # problem_response: ProblemResponseDto = None
    if jira_request.status in down_warning_statuses:
        if not open_ticket_key:
            customer_id: str = jira_service.get_customer_id(
                jira_request.tags, jira_request.probe
            )
            if customer_id == "0":
                # problem_response.detail = f"Problem 19: Can not find CustomerID for {jira_request.name} Please manually Acknowledge and Create Ticket {jira_request.sensor_id}"
                # problem_response.status_code = 404 # might update this to something else
                return _problem_response(
                    f"Problem 19: Can not find CustomerID for {jira_request.name} Please manually Acknowledge and Create Ticket {jira_request.sensor_id}",
                    404,
                )
            crm_key: str = await jira_service.get_crm_key(
                jira_request_instance, customer_id, tenant
            )
            if not crm_key:
                return _problem_response(
                    f"Problem 20: Can not find Customer CRM for {jira_request.name}.  Please manually Acknowledge and Create Ticket {jira_request.sensor_id}",
                    404,
                )
            if project.service_desk:
                new_ticket_id: str = (
                    await jira_service.new_jira_ticket_service_desk(  # new_ticket_id can be service or jira ticket
                        device=device,
                        name=name,
                        status=status,
                        message=message,
                        sensor_id=sensor_id,
                        service_desk_id=project.service_desk_id or 0,
                        request_type_id=project.request_type_id or 0,
                        raise_on_behalf_of=reporter,
                        monitoring_instance=prtg_request_instance,
                        jira_instance=jira_request_instance  # make it jira_instance later
                    )
                )
            else:
                new_ticket_id: str = await jira_service.new_jira_ticket(
                    device=device,
                    name=name,
                    status=status,
                    message=message,
                    sensor_id=sensor_id,
                    project=project.project_key,
                    monitoring_instance=prtg_request_instance,
                    jira_instance=jira_request_instance,
                )  # can be service or jira ticket
            if new_ticket_id != "-1":  # ensure right newJiraTicketId
                update_jira_ticket: int = await jira_service.update_jira_ticket(
                    jira_request_instance, new_ticket_id, crm_key, reporter
                )
                if update_jira_ticket != 0:
                    return _problem_response(
                        "Problem 25: Error occurred updating Ticket.\n Please review Logs.",
                        503,
                    )
                set_comment: bool = await prtg_service.append_sensor_comment_async(
                    prtg_request_instance.lower(), sensor_id, new_ticket_id
                )
                if not set_comment:
                    return _problem_response(
                        "Problem 23: Error occurred setting Sensor comment.\n Please review Logs.",
                        503,
                    )
                ack_result: int = await prtg_service.acknowledge_alarm_async(
                    prtg_request_instance.lower(), sensor_id, new_ticket_id
                )
                if ack_result > 0:
                    return _problem_response(
                        "Problem 16: Error occurred Acknowledging Sensor.\n Please review Logs.",
                        503,
                    )
                else:
                    return {"status": "ok"}
            else:
                return _problem_response(
                    "Problem 15: Jira creation ticket failed.",
                    500,
                )

            # Not adding the Problem 15 as it never reaches it
        else:
            await jira_service.add_jira_comment_async(
                jira_request_instance,
                open_ticket_key,
                device,
                name,
                status,
                message,
                comment_internal,
            )
            if status in [
                "Down",
                "Down (before: Warning)",
                "Warning ended (now: Down)",
            ]:
                ack_result = await prtg_service.acknowledge_alarm_async(
                    prtg_request_instance.lower(), sensor_id, open_ticket_key
                )
                if ack_result > 0:
                    return _problem_response(
                        "Problem 17: Error occurred Acknowledging Sensor.\n Please review Logs.",
                        503,
                    )
                else:
                    return {"status": "ok"}

            return {"status": "ok"}

    elif jira_request.status in up_ended_statuses:
        if open_ticket_key:
            set_comment: bool = await jira_service.add_jira_comment_async(
                jira_request_instance,
                open_ticket_key,
                device,
                name,
                status,
                message,
                comment_internal,
            )
            if not set_comment:
                logger.error(f"Problem 23: {jira_request}")
                return _problem_response(
                    "Problem 23: Error occurred Setting Jira Comment.\n Please review Logs.",
                    503,
                )
            return {"status": "ok"}
        else:
            logger.warning(
                f"Problem 21: {jira_request}"
            )  # Essentially rechecking if there is no open ticket as done in C#
            return {"status": "Problem 21: No Open Tickets found for this Sensor"}
    else:
        logger.error(f"Problem 18: {jira_request}")
        return _problem_response("Problem 18: Status not Found in Body", 400)


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=(settings.environment == "development"),
    )
