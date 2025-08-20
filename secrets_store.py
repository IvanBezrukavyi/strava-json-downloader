
import keyring
SERVICE = "strava-json-downloader"
KEY_ID = "client_id"
KEY_SECRET = "client_secret"
def get_client_id():
    return keyring.get_password(SERVICE, KEY_ID)
def get_client_secret():
    return keyring.get_password(SERVICE, KEY_SECRET)
def set_credentials(client_id: str, client_secret: str):
    keyring.set_password(SERVICE, KEY_ID, client_id)
    keyring.set_password(SERVICE, KEY_SECRET, client_secret)
