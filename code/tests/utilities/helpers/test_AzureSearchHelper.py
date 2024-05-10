import pytest
from unittest.mock import ANY, MagicMock, patch
from backend.batch.utilities.helpers.azure_search_helper import AzureSearchHelper
from azure.search.documents.indexes.models import (
    ExhaustiveKnnAlgorithmConfiguration,
    ExhaustiveKnnParameters,
    HnswAlgorithmConfiguration,
    HnswParameters,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
)

AZURE_AUTH_TYPE = "keys"
AZURE_SEARCH_KEY = "mock-key"
AZURE_SEARCH_SERVICE = "mock-service"
AZURE_SEARCH_INDEX = "mock-index"
AZURE_SEARCH_USE_SEMANTIC_SEARCH = False
AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG = "default"
AZURE_SEARCH_CONVERSATIONS_LOG_INDEX = "mock-log-index"


@pytest.fixture(autouse=True)
def azure_search_mock():
    with patch("backend.batch.utilities.helpers.AzureSearchHelper.AzureSearch") as mock:
        yield mock


@pytest.fixture(autouse=True)
def llm_helper_mock():
    with patch("backend.batch.utilities.helpers.AzureSearchHelper.LLMHelper") as mock:
        llm_helper = mock.return_value
        llm_helper.get_embedding_model.return_value.embed_query.return_value = [
            0
        ] * 1536

        yield llm_helper


@pytest.fixture(autouse=True)
def env_helper_mock():
    with patch("backend.batch.utilities.helpers.AzureSearchHelper.EnvHelper") as mock:
        env_helper = mock.return_value
        env_helper.AZURE_AUTH_TYPE = AZURE_AUTH_TYPE
        env_helper.AZURE_SEARCH_KEY = AZURE_SEARCH_KEY
        env_helper.AZURE_SEARCH_SERVICE = AZURE_SEARCH_SERVICE
        env_helper.AZURE_SEARCH_INDEX = AZURE_SEARCH_INDEX
        env_helper.AZURE_SEARCH_USE_SEMANTIC_SEARCH = AZURE_SEARCH_USE_SEMANTIC_SEARCH
        env_helper.AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG = (
            AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG
        )
        env_helper.AZURE_SEARCH_CONVERSATIONS_LOG_INDEX = (
            AZURE_SEARCH_CONVERSATIONS_LOG_INDEX
        )

        env_helper.is_auth_type_keys.return_value = True

        yield env_helper


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.AzureKeyCredential")
def test_creates_search_clients_with_keys(
    azure_key_credential_mock: MagicMock,
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
):
    # when
    AzureSearchHelper()

    # then
    azure_key_credential_mock.assert_called_once_with(AZURE_SEARCH_KEY)
    search_client_mock.assert_called_once_with(
        endpoint=AZURE_SEARCH_SERVICE,
        index_name=AZURE_SEARCH_INDEX,
        credential=azure_key_credential_mock.return_value,
    )
    search_index_client_mock.assert_called_once_with(
        endpoint=AZURE_SEARCH_SERVICE, credential=azure_key_credential_mock.return_value
    )


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.DefaultAzureCredential")
def test_creates_search_clients_with_rabc(
    default_azure_credential_mock: MagicMock,
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
    env_helper_mock: MagicMock,
):
    # given
    env_helper_mock.is_auth_type_keys.return_value = False

    # when
    AzureSearchHelper()

    # then
    default_azure_credential_mock.assert_called_once_with()
    search_client_mock.assert_called_once_with(
        endpoint=AZURE_SEARCH_SERVICE,
        index_name=AZURE_SEARCH_INDEX,
        credential=default_azure_credential_mock.return_value,
    )
    search_index_client_mock.assert_called_once_with(
        endpoint=AZURE_SEARCH_SERVICE,
        credential=default_azure_credential_mock.return_value,
    )


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_returns_search_client(
    search_index_client_mock: MagicMock, search_client_mock: MagicMock
):
    # given
    azure_search_helper = AzureSearchHelper()

    # when
    search_client = azure_search_helper.get_search_client()

    # then
    assert search_client is search_client_mock.return_value


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_creates_search_index_if_not_exists(
    search_index_client_mock: MagicMock, search_client_mock: MagicMock
):
    # given
    search_index_client_mock.return_value.list_index_names.return_value = [
        "some-irrelevant-index"
    ]

    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile",
        ),
        SearchableField(
            name="metadata",
            type=SearchFieldDataType.String,
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            facetable=True,
            filterable=True,
        ),
        SearchableField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="chunk",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        SimpleField(
            name="offset",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
    ]

    expected_index = SearchIndex(
        name=AZURE_SEARCH_INDEX,
        fields=fields,
        semantic_search=(
            SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name=AZURE_SEARCH_SEMANTIC_SEARCH_CONFIG,
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=None,
                            content_fields=[SemanticField(field_name="content")],
                        ),
                    )
                ]
            )
        ),
        vector_search=VectorSearch(
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="default",
                    parameters=HnswParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE
                    ),
                    kind=VectorSearchAlgorithmKind.HNSW,
                ),
                ExhaustiveKnnAlgorithmConfiguration(
                    name="default_exhaustive_knn",
                    kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                    parameters=ExhaustiveKnnParameters(
                        metric=VectorSearchAlgorithmMetric.COSINE
                    ),
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm_configuration_name="default",
                ),
                VectorSearchProfile(
                    name="myExhaustiveKnnProfile",
                    algorithm_configuration_name="default_exhaustive_knn",
                ),
            ],
        ),
    )

    # when
    AzureSearchHelper()

    # then
    search_index_client_mock.return_value.create_index.assert_called_once_with(
        expected_index
    )


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_does_not_create_search_index_if_it_exists(
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
):
    # given
    search_index_client_mock.return_value.list_index_names.return_value = [
        AZURE_SEARCH_INDEX
    ]

    # when
    AzureSearchHelper()

    # then
    search_index_client_mock.return_value.create_index.assert_not_called()


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_propogates_exceptions_when_creating_search_index(
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
):
    # given
    expected_exception = Exception()
    search_index_client_mock.return_value.create_index.side_effect = expected_exception

    # when
    with pytest.raises(Exception) as exc_info:
        AzureSearchHelper()

    # then
    assert exc_info.value == expected_exception


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_get_conversation_logger_keys(
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
    azure_search_mock: MagicMock,
    llm_helper_mock: MagicMock,
):
    # given
    azure_search_helper = AzureSearchHelper()

    # when
    conversation_logger = azure_search_helper.get_conversation_logger()

    # then
    assert conversation_logger == azure_search_mock.return_value

    azure_search_mock.assert_called_once_with(
        azure_search_endpoint=AZURE_SEARCH_SERVICE,
        azure_search_key=AZURE_SEARCH_KEY,
        index_name=AZURE_SEARCH_CONVERSATIONS_LOG_INDEX,
        embedding_function=llm_helper_mock.get_embedding_model.return_value.embed_query,
        fields=ANY,
        user_agent="langchain chatwithyourdata-sa",
    )


@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchClient")
@patch("backend.batch.utilities.helpers.AzureSearchHelper.SearchIndexClient")
def test_get_conversation_logger_rbac(
    search_index_client_mock: MagicMock,
    search_client_mock: MagicMock,
    azure_search_mock: MagicMock,
    llm_helper_mock: MagicMock,
    env_helper_mock: MagicMock,
):
    # given
    env_helper_mock.is_auth_type_keys.return_value = False
    azure_search_helper = AzureSearchHelper()

    # when
    conversation_logger = azure_search_helper.get_conversation_logger()

    # then
    assert conversation_logger == azure_search_mock.return_value

    azure_search_mock.assert_called_once_with(
        azure_search_endpoint=AZURE_SEARCH_SERVICE,
        azure_search_key=None,
        index_name=AZURE_SEARCH_CONVERSATIONS_LOG_INDEX,
        embedding_function=llm_helper_mock.get_embedding_model.return_value.embed_query,
        fields=ANY,
        user_agent="langchain chatwithyourdata-sa",
    )
