import logging
import os.path
from secrets import GOOGLE_API_CREDENTIALS_FILE_PATH

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# If modifying these scopes, delete the file token_json.
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_google_tasks_service():
    """
    Authenticate, and return Google Tasks API usage object.
    """
    creds = None
    token_json = "token.json"
    if os.path.exists(token_json):
        creds = Credentials.from_authorized_user_file(token_json, SCOPES)

    if creds:
        logger.info(
            f"Got cached token. Status: {creds.expired=} {creds.refresh_token=}"
        )
        if creds.expired:
            try:
                creds.refresh(Request())
                logger.info("Refreshed token.")
            except RefreshError as e:
                logger.error("Failed to refresh token.")
                raise e
    else:
        logger.info("Getting new token.")
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_API_CREDENTIALS_FILE_PATH, SCOPES
        )
        creds = flow.run_local_server()

    # Save the credentials for the next run
    with open(token_json, "w") as token:
        token.write(creds.to_json())

    service = build("tasks", "v1", credentials=creds)
    return service


def clear_google_tasks(tasklist_id):
    """
    For some reason, service.tasks().clear(...) does not work as I expected.
    This is the replacement for it.
    """
    service = get_google_tasks_service()
    tasks = service.tasks().list(tasklist=tasklist_id).execute()
    while tasks["items"]:
        for task in tasks["items"]:
            service.tasks().delete(tasklist=tasklist_id, task=task["id"]).execute()
