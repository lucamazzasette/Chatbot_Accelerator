import json
import os
import sys
from unittest.mock import ANY

from azure.functions import QueueMessage
import pytest
from pytest_httpserver import HTTPServer
from tests.functional.app_config import AppConfig
from tests.request_matching import RequestMatcher, verify_request_made
from tests.constants import (
    AZURE_STORAGE_CONFIG_FILE_NAME,
    AZURE_STORAGE_CONFIG_CONTAINER_NAME,
)

sys.path.append(
    os.path.join(os.path.dirname(sys.path[0]), "..", "..", "..", "backend", "batch")
)

from backend.batch.batch_push_results import batch_push_results  # noqa: E402

pytestmark = pytest.mark.functional

FILE_NAME = "test.pdf"


@pytest.fixture(autouse=True)
def setup_blob_metadata_mocking(httpserver: HTTPServer, app_config: AppConfig):
    httpserver.expect_request(
        f"/{app_config.get('AZURE_BLOB_CONTAINER_NAME')}/{FILE_NAME}",
        method="HEAD",
    ).respond_with_data()

    httpserver.expect_request(
        f"/{app_config.get('AZURE_BLOB_CONTAINER_NAME')}/{FILE_NAME}",
        method="PUT",
    ).respond_with_data()


@pytest.fixture
def message(app_config: AppConfig):
    return QueueMessage(
        body=json.dumps(
            {
                "topic": "topic",
                "subject": f"/blobServices/default/{app_config.get('AZURE_BLOB_CONTAINER_NAME')}/documents/blobs/{FILE_NAME}",
                "eventType": "Microsoft.Storage.BlobCreated",
                "id": "id",
                "data": {
                    "api": "PutBlob",
                    "clientRequestId": "73a48942-0eae-11ef-9576-0242ac110002",
                    "requestId": "9cc44179-401e-005a-4fbb-a2e687000000",
                    "eTag": "0x8DC70D257E6452E",
                    "contentType": "application/pdf",
                    "contentLength": 544811,
                    "blobType": "BlockBlob",
                    "url": f"https://{app_config.get('AZURE_BLOB_ACCOUNT_NAME')}.blob.core.windows.net/documents/{FILE_NAME}",
                    "sequencer": "00000000000000000000000000036029000000000017251c",
                    "storageDiagnostics": {
                        "batchId": "c98008b9-e006-007c-00bb-a2ae9f000000"
                    },
                },
                "dataVersion": "",
                "metadataVersion": "1",
                "eventTime": "2024-05-10T09:22:51.5565464Z",
            }
        )
    )


def test_config_file_is_retrieved_from_storage(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/{AZURE_STORAGE_CONFIG_CONTAINER_NAME}/{AZURE_STORAGE_CONFIG_FILE_NAME}",
            method="GET",
            headers={
                "Authorization": ANY,
            },
            times=1,
        ),
    )


def test_integrated_vectorization_datasouce_created(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/datasources('{app_config.get('AZURE_SEARCH_DATASOURCE_NAME')}')",
            method="PUT",
            json={
                "name": app_config.get("AZURE_SEARCH_DATASOURCE_NAME"),
                "type": "azureblob",
                "credentials": {
                    "connectionString": f"DefaultEndpointsProtocol=https;AccountName={app_config.get('AZURE_BLOB_ACCOUNT_NAME')};AccountKey=c29tZS1ibG9iLWFjY291bnQta2V5;EndpointSuffix=core.windows.net"
                },
                "container": {"name": f"{app_config.get('AZURE_BLOB_CONTAINER_NAME')}"},
                "dataDeletionDetectionPolicy": {
                    "@odata.type": "#Microsoft.Azure.Search.NativeBlobSoftDeleteDeletionDetectionPolicy"
                },
            },
            query_string="api-version=2023-10-01-Preview",
            times=1,
        ),
    )


def test_integrated_vectorization_index_created(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/indexes('{app_config.get('AZURE_SEARCH_INDEX')}')",
            method="PUT",
            json={
                "name": f"{app_config.get('AZURE_SEARCH_INDEX')}",
                "fields": [
                    {
                        "name": "id",
                        "type": "Edm.String",
                        "key": False,
                        "retrievable": True,
                        "searchable": False,
                        "filterable": True,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "content",
                        "type": "Edm.String",
                        "key": False,
                        "retrievable": True,
                        "searchable": True,
                        "filterable": False,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "content_vector",
                        "type": "Collection(Edm.Single)",
                        "dimensions": 2,
                        "vectorSearchProfile": "myHnswProfile",
                    },
                    {
                        "name": "metadata",
                        "type": "Edm.String",
                        "key": False,
                        "retrievable": True,
                        "searchable": True,
                        "filterable": False,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "title",
                        "type": "Edm.String",
                        "key": False,
                        "retrievable": True,
                        "searchable": True,
                        "filterable": True,
                        "sortable": False,
                        "facetable": True,
                    },
                    {
                        "name": "source",
                        "type": "Edm.String",
                        "key": False,
                        "retrievable": True,
                        "searchable": True,
                        "filterable": True,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "chunk",
                        "type": "Edm.Int32",
                        "key": False,
                        "retrievable": True,
                        "searchable": False,
                        "filterable": True,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "offset",
                        "type": "Edm.Int32",
                        "key": False,
                        "retrievable": True,
                        "searchable": False,
                        "filterable": True,
                        "sortable": False,
                        "facetable": False,
                    },
                    {
                        "name": "chunk_id",
                        "type": "Edm.String",
                        "key": True,
                        "filterable": True,
                        "sortable": True,
                        "facetable": True,
                        "analyzer": "keyword",
                    },
                ],
                "semantic": {
                    "configurations": [
                        {
                            "name": f"{app_config.get('AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG')}",
                            "prioritizedFields": {
                                "prioritizedContentFields": [{"fieldName": "content"}]
                            },
                        }
                    ]
                },
                "vectorSearch": {
                    "profiles": [
                        {
                            "name": "myHnswProfile",
                            "algorithm": "myHnsw",
                            "vectorizer": "myOpenAI",
                        },
                        {
                            "name": "myExhaustiveKnnProfile",
                            "algorithm": "myExhaustiveKnn",
                            "vectorizer": "myOpenAI",
                        },
                    ],
                    "algorithms": [
                        {
                            "name": "myHnsw",
                            "kind": "hnsw",
                            "hnswParameters": {
                                "m": 4,
                                "efConstruction": 400,
                                "efSearch": 500,
                                "metric": "cosine",
                            },
                        },
                        {
                            "name": "myExhaustiveKnn",
                            "kind": "exhaustiveKnn",
                            "exhaustiveKnnParameters": {"metric": "cosine"},
                        },
                    ],
                    "vectorizers": [
                        {
                            "name": "myOpenAI",
                            "kind": "azureOpenAI",
                            "azureOpenAIParameters": {
                                "resourceUri": f"https://localhost:{httpserver.port}/",
                                "deploymentId": f"{app_config.get('AZURE_OPENAI_EMBEDDING_MODEL')}",
                                "apiKey": f"{app_config.get('AZURE_OPENAI_API_KEY')}",
                            },
                        }
                    ],
                },
            },
            query_string="api-version=2023-10-01-Preview",
            times=1,
        ),
    )


def test_integrated_vectorization_skillset_created(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/skillsets('{app_config.get('AZURE_SEARCH_INDEX')}-skillset')",
            method="PUT",
            query_string="api-version=2023-10-01-Preview",
            times=1,
        ),
    )


def test_integrated_vectorization_indexer_created(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/indexers('{app_config.get('AZURE_SEARCH_INDEXER_NAME')}')",
            method="PUT",
            query_string="api-version=2023-10-01-Preview",
            times=1,
        ),
    )


def test_integrated_vectorization_indexer_run(
    message: QueueMessage, httpserver: HTTPServer, app_config: AppConfig
):
    # when
    batch_push_results.build().get_user_function()(message)

    # then
    verify_request_made(
        mock_httpserver=httpserver,
        request_matcher=RequestMatcher(
            path=f"/indexers('{app_config.get('AZURE_SEARCH_INDEXER_NAME')}')/search.run",
            method="POST",
            query_string="api-version=2023-10-01-Preview",
            times=1,
        ),
    )
