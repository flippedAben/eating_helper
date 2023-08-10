from googleapiclient.discovery import build

from .auth import get_creds


def get_google_tasks_service():
    scopes = ["https://www.googleapis.com/auth/tasks"]
    service = build("tasks", "v1", credentials=get_creds(scopes))
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
