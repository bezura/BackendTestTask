import logging
from logging.config import dictConfig as loggerDictConfig

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import logging_conf, settings

loggerDictConfig(logging_conf)

openapi_url = f"{settings.API_V1_PATH}/openapi.json"
app = FastAPI(
    title=settings.TITLE,
    openapi_url=openapi_url,
    debug=settings.DEBUG,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    version=settings.VERSION,
    default_response_class=ORJSONResponse,
)

app.include_router(api_router, prefix=settings.API_V1_PATH)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.DEBUG:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.TITLE,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]
