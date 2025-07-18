import pytest
from core.logging import get_logger

def test_logger_outputs_info_message(caplog):
    logger = get_logger("test_logger")
    test_message = "This is a test log message."
    with caplog.at_level("INFO"):
        logger.info(test_message)
    assert any(test_message in record.message for record in caplog.records) 