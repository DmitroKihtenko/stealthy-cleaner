import datetime

from pythonjsonlogger import jsonlogger

from app.settings import APP_NAME


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        log_record["timestamp"] = (
            datetime.datetime.fromtimestamp(record.created).isoformat(
                timespec="milliseconds") + "Z"
        )
        log_record["level"] = record.levelname.lower()
        log_record["msg"] = record.message
        log_record["app_name"] = APP_NAME

        log_record.pop("asctime", None)
        log_record.pop("color_message", None)
        log_record.pop("message", None)
