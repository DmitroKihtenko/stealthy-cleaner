import logging.config
from datetime import datetime, timezone
from functools import lru_cache
from time import sleep

import yaml
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.database import Database

from app.settings import (
    Settings,
    EXPIRATION_CRITERIA,
    CONFIG_FILE,
    LOGS_CONFIG_FILE,
    ID_CRITERIA,
    METADATA_COLLECTION,
    TARGET_COLLECTION,
)


logger = logging.getLogger()


def load_logging_config():
    try:
        logging.config.fileConfig(LOGS_CONFIG_FILE)
    except OSError as e:
        logger.error(f"Logging file reading error", extra={
            "file": LOGS_CONFIG_FILE,
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })
        raise e


@lru_cache
def get_settings() -> Settings:
    logger.info("Loading configuration", extra={
        "file": CONFIG_FILE
    })

    try:
        with open(CONFIG_FILE, "r") as stream:
            config = yaml.safe_load(stream)

        logger.info("Configuration loaded")

        return Settings.model_validate(config)
    except ValidationError as e:
        logger.error(f"Config file reading error", extra={
            "file": CONFIG_FILE,
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })
    except OSError as e:
        logger.error(f"Config file reading error", extra={
            "file": CONFIG_FILE,
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })
        raise e


def get_message_from_error(error: Exception) -> str:
    err_type = type(error.args)
    if isinstance(err_type, list):
        return ", ".join(error.args)
    else:
        return str(error.args)


def clean_from_database(db: Database, settings: Settings):
    now_timestamp = datetime.now(timezone.utc).timestamp()

    try:
        logger.info("Cleaning files")

        metadata_to_remove = db[METADATA_COLLECTION].find(
            {EXPIRATION_CRITERIA: {"$lte": now_timestamp}},
            projection={ID_CRITERIA: 1}
        )
        files_identifiers = [[]]
        batch_to_remove = 0
        for metadata in metadata_to_remove:
            if len(files_identifiers[
                       batch_to_remove
                   ]) >= settings.cleanup.remove_batch_size:
                batch_to_remove += 1
                files_identifiers.append([])
            files_identifiers[batch_to_remove].append(metadata[ID_CRITERIA])

        deleted_from_metadata = 0
        deleted_from_target = 0

        for batch in files_identifiers:
            result = db[METADATA_COLLECTION].delete_many({
                ID_CRITERIA: {"$in": batch}
            })
            deleted_from_metadata += result.deleted_count

            result = db[TARGET_COLLECTION].delete_many({
                ID_CRITERIA: {"$in": batch}
            })
            deleted_from_target += result.deleted_count

        if deleted_from_metadata > 0:
            logger.info("Data deleted", extra={
                "count": deleted_from_metadata,
                "collection": METADATA_COLLECTION
            })
        if deleted_from_target > 0:
            logger.info("Data deleted", extra={
                "count": deleted_from_metadata,
                "collection": TARGET_COLLECTION
            })
    except Exception as e:
        logger.error("Database cleanup error", extra={
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })


def do_cleanup(db: Database, settings: Settings):
    logger.info("Starting cleanup loop")

    try:
        while True:
            clean_from_database(db, settings)
            sleep(settings.cleanup.seconds_period)
    finally:
        logger.info("Cleanup loop stopped")


def check_connection(client: MongoClient):
    logger.info("Checking database connection")
    try:
        client.server_info()
    except Exception as e:
        logger.error("Database is not available", extra={
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })
        raise e


def main():
    try:
        load_logging_config()
        settings = get_settings()
        client = MongoClient(
            settings.mongo_db.url,
            connectTimeoutMS=settings.mongo_db.seconds_timeout * 1000,
            serverSelectionTimeoutMS=settings.mongo_db.seconds_timeout * 1000,
        )
        db = client[settings.mongo_db.database]

        check_connection(client)
        do_cleanup(db, settings)
    except KeyboardInterrupt:
        logger.info("Program interrupted")
    except Exception as e:
        logger.critical("Critical error", extra={
            "error_type": type(e).__name__,
            "error_message": get_message_from_error(e)
        })
    finally:
        logger.info("Program stopped")


if __name__ == '__main__':
    main()
