using './deployment.bicep'

param ResourcePrefix = ''
param Location = ''
param VnetResourceGroup = ''
param VnetName = ''
param AppsSubnetName = ''
param EndpointsSubnetName = ''
param PrivateDnsZoneResourceGroup = ''
param DeployNewDnsZones = false
param HostingPlanName = 'plan-${ResourcePrefix}'
param HostingPlanSku = 'B3'
param WebsiteName = '${ResourcePrefix}-website'
param logAnalyticsWorkspaceName = 'law-${ResourcePrefix}'
param ApplicationInsightsName = 'appins-${ResourcePrefix}'
param AzureSearchUseSemanticSearch = 'true'
param AzureSearchSemanticSearchConfig = 'default'
param AzureSearchIndexIsPrechunked = 'false'
param AzureSearchTopK = '5'
param AzureSearchEnableInDomain = 'false'
param AzureSearchContentColumns = 'content'
param AzureSearchFilenameColumn = 'filename'
param AzureSearchTitleColumn = 'title'
param AzureSearchUrlColumn = 'url'
param AzureOpenAIResource = 'aoai-${ResourcePrefix}'
param AzureOpenAIGPTModel = 'gpt-35-turbo'
param AzureOpenAIGPTModelName = 'gpt-35-turbo'
param AzureOpenAIGPTModelVersion = '0613'
param AzureOpenAIEmbeddingModel = 'text-embedding-ada-002'
param AzureOpenAIEmbeddingModelName = 'text-embedding-ada-002'
param AzureOpenAIEmbeddingModelVersion = '2'
param OrchestrationStrategy = 'openai_function'
param AzureOpenAITemperature = '0'
param AzureOpenAITopP = '1'
param AzureOpenAIMaxTokens = '1000'
param AzureOpenAIStopSequence = '\n'
param AzureOpenAISystemMessage = 'You are an AI assistant that helps people find information.'
param AzureOpenAIApiVersion = '2023-07-01-preview'
param AzureOpenAIStream = 'true'
param AzureAISearchName = 'search-${ResourcePrefix}'
param AzureAISearchSku = 'standard'
param AzureSearchIndex = 'index-${ResourcePrefix}'
param AzureSearchConversationLogIndex = 'conversations'
param StorageAccountName = 'stor${ResourcePrefix}'
param FunctionName = 'func-${ResourcePrefix}-backend'
param FormRecognizerName = 'formrecog-${ResourcePrefix}'
param FormRecognizerLocation = Location
param SpeechServiceName = 'speech-${ResourcePrefix}'
param ContentSafetyName = 'contentsafety-${ResourcePrefix}'
param authType = 'keys'
param principalId = ''

