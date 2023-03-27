import os
from keycloak import KeycloakOpenID
from typing import Tuple


def get_keycloak_data() -> Tuple[KeycloakOpenID, str]:
    keycloak_url: str = os.getenv("KEYCLOAK_URL")
    client_id: str = os.getenv("CLIENT_ID")
    client_secret: str = os.getenv("CLIENT_SECRET")

    if keycloak_url is None:
        raise ValueError("The keyclock URL isn't defined!")

    if (client_id is None) or (client_secret is None):
        raise ValueError("The client's credentials aren't defined!")

    openid = KeycloakOpenID(
        server_url=keycloak_url,
        client_id=client_id,
        realm_name="inference",
        client_secret_key=client_secret,
        verify=False
    )
    config_well_known = openid.well_known()
    endpoint = config_well_known["token_endpoint"]
    return openid, endpoint
