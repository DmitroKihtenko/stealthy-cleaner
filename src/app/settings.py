from pydantic import BaseModel, Field

APP_NAME = "stealthy-cleaner"
LOGS_CONFIG_FILE = "logging.conf"
CONFIG_FILE = "config.yaml"
METADATA_COLLECTION: str = "files_metadata"
TARGET_COLLECTION: str = "files"
EXPIRATION_CRITERIA: str = "expiration"
ID_CRITERIA = "identifier"


class MongoDB(BaseModel):
    url: str = Field(
        title="MongoDB url",
        description="MongoDB connection string",
        example="mongodb://root:secret@mongodb:27017",
    )
    database: str = Field(
        title="MongoDB database",
        description="MongoDB target database for cleanup",
        example="stealthy-backend",
    )
    seconds_timeout: int = Field(
        title="MongoDB connection timeout",
        description="MongoDB all connections timeout in seconds",
        example=2,
        gt=0,
    )


class Cleanup(BaseModel):
    seconds_period: int = Field(
        title="Seconds period",
        description="Time in seconds between iterations of process of "
                    "deleting files that have expired",
        example=20,
        gt=0,
    )
    remove_batch_size: int = Field(
        title="Remove batch size",
        description="Amount of files to remove in one request to "
                    "database",
        example=10,
        gt=0,
    )


class Settings(BaseModel):
    mongo_db: MongoDB
    cleanup: Cleanup
