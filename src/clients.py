from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from dotenv import load_dotenv
import os
import httpx
import instructor
from openai import AzureOpenAI
from azure.core.pipeline.transport import RequestsTransport
from requests import Session
from requests.adapters import HTTPAdapter

load_dotenv()


# Document Intelligence Client
def get_document_intelligence_client(url=None, token=None):
    session = Session()
    adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=0)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    transport = RequestsTransport(session=session)

    return DocumentIntelligenceClient(
        endpoint=url or os.environ["AZUREDOCINTEL_BASE_URI"],
        credential=AzureKeyCredential(token or os.environ["AZUREDOCINTEL_TOKEN"]),
        transport=transport,
    )


# Instructor OpenAI Client
def get_instructor_client(url=None, token=None, api_version=None):
    http_client = httpx.Client(
        limits=httpx.Limits(max_connections=64, max_keepalive_connections=64)
    )
    return instructor.from_openai(
        AzureOpenAI(
            api_version=api_version or os.environ["AZUREOPENAI_API_VERSION"],
            azure_endpoint=url or os.environ["AZUREOPENAI_BASE_URI"],
            api_key=token or os.environ["AZUREOPENAI_API_TOKEN"],
            http_client=http_client,
        ),
        mode=instructor.Mode.TOOLS,
    )
