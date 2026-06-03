from app.config import get_settings, load_config
import os

load_config()
settings = get_settings()

print("Environment:", settings.environment)
print("Host:", settings.host)
print("Port:", settings.port)
print("Allowed IPs:", settings.allowed_ips)
print("Instances:", settings.instances)

print("\nEnvironment Variables:")
print("PRTG2JIRA_ENVIRONMENT:", os.getenv("PRTG2JIRA_ENVIRONMENT"))
print("PRTG2JIRA_DEFAULT_JIRA_BASE_URL:", os.getenv("PRTG2JIRA_DEFAULT_JIRA_BASE_URL"))
print("PRTG2JIRA_DEFAULT_JIRA_TOKEN:", os.getenv("PRTG2JIRA_DEFAULT_JIRA_TOKEN"))
print("PRTG2JIRA_DEFAULT_PRTG_BASE_URL:", os.getenv("PRTG2JIRA_DEFAULT_PRTG_BASE_URL"))
print("PRTG2JIRA_DEFAULT_PRTG_TOKEN:", os.getenv("PRTG2JIRA_DEFAULT_PRTG_TOKEN"))
