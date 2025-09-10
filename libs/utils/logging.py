import logging
import sys

def setup_logger(name: str = "app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s trace=%(trace_id)s msg=%(message)s"
    )
    handler.setFormatter(fmt)
    logger.handlers = [handler]
    return logger

class ContextAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        if "extra" in kwargs:
            extra.update(kwargs["extra"])
        kwargs["extra"] = {"trace_id": extra.get("trace_id", "-")}
        return msg, kwargs