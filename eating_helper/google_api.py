import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

GOOGLE_API_CREDS = "google_api_credentials.json"

# If modifying these scopes, delete the file token_json.
SCOPES = ["https://www.googleapis.com/auth/tasks"]


def get_google_tasks_service():
    """
    Return Google Tasks API usage object.
    """
    creds = None
    # The file *_token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_json = "token.json"
    if os.path.exists(token_json):
        creds = Credentials.from_authorized_user_file(token_json, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_API_CREDS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("tasks", "v1", credentials=creds)
        return service
    except HttpError as err:
        print(err)
        raise err


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
