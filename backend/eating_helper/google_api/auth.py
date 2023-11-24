import logging
import os.path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from ..secrets import GOOGLE_API_CREDENTIALS_FILE_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_creds() -> Credentials:
    scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/tasks",
    ]
    creds = None
    token_json = "token.json"
    if os.path.exists(token_json):
        creds = Credentials.from_authorized_user_file(token_json, scopes)

    refreshed_token: bool = try_refresh_token(creds)
    if not refreshed_token:
        if os.path.exists(token_json):
            logger.info("Removing existing expired token.")
            os.remove(token_json)

        logger.info("Getting new token.")
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_API_CREDENTIALS_FILE_PATH,
            scopes,
        )
        creds = flow.run_local_server(port=8082)

    # Save the credentials for the next run
    with open(token_json, "w") as token:
        token.write(creds.to_json())

    return creds


def try_refresh_token(creds: Credentials) -> bool:
    if creds:
        logger.info(
            f"Got cached token. Status: {creds.expired=} {creds.refresh_token=}"
        )
        if creds.expired:
            try:
                creds.refresh(Request())
                logger.info("Refreshed token.")
                return True
            except RefreshError as e:
                error_data = e.args[1]
                if error_data["error"] == "invalid_grant":
                    return False
                else:
                    logger.error("Failed to refresh token due to unexpected error.")
                    raise e
    return False
