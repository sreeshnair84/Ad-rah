import os
from types import SimpleNamespace


# Minimal settings object using environment variables.
# This avoids a hard dependency on pydantic for test runs.
settings = SimpleNamespace(
    AZURE_STORAGE_CONNECTION_STRING=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
    AZURE_CONTAINER_NAME=os.getenv("AZURE_CONTAINER_NAME", "openkiosk-media"),
    LOCAL_MEDIA_DIR=os.getenv("LOCAL_MEDIA_DIR", "./data/media"),
    MONGO_URI=os.getenv("MONGO_URI", None),
    SERVICE_BUS_CONNECTION_STRING=os.getenv("SERVICE_BUS_CONNECTION_STRING"),
    AZURE_AI_ENDPOINT=os.getenv("AZURE_AI_ENDPOINT"),
    AZURE_AI_KEY=os.getenv("AZURE_AI_KEY"),
    SECRET_KEY=os.getenv("SECRET_KEY", "CHANGE_ME_REPLACE_WITH_SECURE_SECRET"),
    ALGORITHM="HS256",
    ACCESS_TOKEN_EXPIRE_MINUTES=60,
    # Local development settings
    USE_LOCAL_EVENT_PROCESSOR=os.getenv("USE_LOCAL_EVENT_PROCESSOR", "true").lower() == "true",
    EVENT_PROCESSOR_QUEUE_SIZE=int(os.getenv("EVENT_PROCESSOR_QUEUE_SIZE", "100")),
)
