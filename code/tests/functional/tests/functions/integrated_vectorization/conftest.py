import logging
import pytest
import sys
import os
from tests.functional.app_config import AppConfig
from backend.batch.utilities.helpers.config.config_helper import ConfigHelper
from backend.batch.utilities.helpers.env_helper import EnvHelper

logger = logging.getLogger(__name__)
sys.path.append(
    os.path.join(os.path.dirname(sys.path[0]), "..", "..", "..", "backend", "batch")
)


@pytest.fixture(scope="package")
def app_config(make_httpserver, ca):
    logger.info("Creating APP CONFIG")
    with ca.cert_pem.tempfile() as ca_temp_path:
        app_config = AppConfig(
            {
                "AZURE_OPENAI_ENDPOINT": f"https://localhost:{make_httpserver.port}/",
                "AZURE_SEARCH_SERVICE": f"https://localhost:{make_httpserver.port}/",
                "AZURE_CONTENT_SAFETY_ENDPOINT": f"https://localhost:{make_httpserver.port}/",
                "AZURE_SPEECH_REGION_ENDPOINT": f"https://localhost:{make_httpserver.port}/",
                "AZURE_STORAGE_ACCOUNT_ENDPOINT": f"https://localhost:{make_httpserver.port}/",
                "AZURE_SEARCH_USE_INTEGRATED_VECTORIZATION": "True",
                "SSL_CERT_FILE": ca_temp_path,
                "CURL_CA_BUNDLE": ca_temp_path,
            }
        )
        logger.info(f"Created app config: {app_config.get_all()}")
        yield app_config


@pytest.fixture(scope="package")
def manage_app(app_config: AppConfig):
    app_config.apply_to_environment()
    EnvHelper.clear_instance()
    ConfigHelper.clear_config()
    yield
    app_config.remove_from_environment()
    EnvHelper.clear_instance()
    ConfigHelper.clear_config()
