import logging.config
from datetime import datetime
from time import sleep

import yaml
from pydantic import ValidationError
from pymongo import MongoClient
from pymongo.database import Database

from app.settings import (
    Settings,
    TARGET_CRITERIA,
    TARGET_COLLECTIONS,
    CONFIG_FILE,
    LOGS_CONFIG_FILE
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


def clean_from_database(db: Database):
    now_timestamp = datetime.utcnow().timestamp()

    try:
        logger.info("Cleaning files")

        for collection in TARGET_COLLECTIONS:
            result = db[collection].delete_many(
                {TARGET_CRITERIA: {'$lte': now_timestamp}}
            )
            if result.deleted_count > 0:
                logger.info("Data deleted", extra={
                    "count": result.deleted_count,
                    "collection": collection
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
            clean_from_database(db)
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
