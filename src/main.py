# -*- coding: utf-8 -*-
import os
from model_utils import load_model, make_inference
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi_utils import Oauth2ClientCredentials
from pydantic import BaseModel
from keycloak.uma_permissions import AuthStatus
from keycloak_utils import get_keycloak_data


class Instance(BaseModel):
    cylinders: int
    displacement: float
    horsepower: float
    weight: float
    acceleration: float
    model_year: int
    origin: int


app = FastAPI()
keycloak_openid, token_endpoint = get_keycloak_data()
oauth2_scheme = Oauth2ClientCredentials(tokenUrl=token_endpoint)

model_path: str = os.getenv("MODEL_PATH")
if model_path is None:
    raise ValueError("The environment variable $MODEL_PATH is empty!")


async def get_token_status(token: str) -> AuthStatus:
    return keycloak_openid.has_uma_access(
        token, "infer_endpoint#doInfer")


async def check_token(token: str = Depends(oauth2_scheme)) -> None:
    print("---")
    print(token)
    print("---")
    auth_status = await get_token_status(token)
    is_logged = auth_status.is_logged_in
    is_authorized = auth_status.is_authorized

    print("---")
    print(auth_status)
    print(token_endpoint)
    print("---")

    if not is_logged:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/healthcheck")
def healthcheck() -> dict[str, str]:
    print(token_endpoint)
    return {"status": "ok"}


@app.post("/predictions")
async def predictions(instance: Instance,
                      token: str = Depends(check_token)) -> dict[str, float]:
    return make_inference(load_model(model_path), instance.dict())
