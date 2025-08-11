import os
import instructor
from pydantic import BaseModel
from clients import (
    get_document_intelligence_client,
    get_instructor_client,
)
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    DocumentAnalysisFeature,
)
import time
import threading


_docintel_lock = threading.Lock()
_last_docintel_post = 0.0


# Enforce a minimum interval between Document Intelligence POST requests
def rate_limit_docintel(min_interval_s: float = 0.1) -> None:
    global _last_docintel_post
    with _docintel_lock:
        now = time.time()
        delay = min_interval_s - (now - _last_docintel_post)
        if delay > 0:
            time.sleep(delay)
            now = time.time()
        _last_docintel_post = now


# Get OCR result from Document Intelligence
def get_docintel_result(
    client: DocumentIntelligenceClient, file_path=None, bytes_source=None
):

    if bytes_source is None:
        if isinstance(file_path, (bytes, bytearray)):
            bytes_source = file_path
        elif isinstance(file_path, str) and file_path:
            with open(file_path, "rb") as f:
                bytes_source = f.read()
        else:
            raise ValueError("Provide either file_path or bytes_source")

    rate_limit_docintel(0.1)

    start_time = time.time()
    docintel_result = (
        client.begin_analyze_document(
            "prebuilt-layout",
            AnalyzeDocumentRequest(bytes_source=bytes_source),
            features=[DocumentAnalysisFeature.KEY_VALUE_PAIRS],
            polling_interval=2,
        )
        .result()
        .get("content")
    )
    docintel_latency = time.time() - start_time

    return docintel_result, docintel_latency


# Get response from Instructor
def get_instructor_response(
    client: instructor.client.Instructor,
    system_prompt: str,
    user_prompt: str,
    pydantic_schema: BaseModel,
    model_name: str,
    temperature: float = 1.0,
):
    start_time = time.time()
    response = client.chat.completions.create(
        response_model=pydantic_schema,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model_name,
        temperature=temperature,
    ).model_dump(exclude_none=True)
    llm_latency = time.time() - start_time

    if isinstance(response, dict) and len(response) == 1:
        response = next(iter(response.values()))
    return response, llm_latency


# Run OCR and LLM once, reusing provided clients when available
def get_response(
    model_name: str,
    system_prompt: str = None,
    pydantic_schema: BaseModel = None,
    bytes_source: bytes = None,
    file_path: str = None,
    doc_client: DocumentIntelligenceClient = None,
    llm_client: instructor.client.Instructor = None,
    temperature: float = 1.0,
):
    # Ensure byte source
    if not bytes_source:
        if file_path:
            with open(file_path, "rb") as f:
                bytes_source = f.read()
        else:
            raise ValueError("Either bytes_source or file_path must be provided")

    # Fetch or reuse clients
    docintel_client = doc_client or get_document_intelligence_client()
    llm_client = llm_client or get_instructor_client()

    # Get OCR result
    ocr_result, ocr_latency = get_docintel_result(
        docintel_client, file_path=file_path, bytes_source=bytes_source
    )

    # Get LLM result
    effective_model = model_name
    llm_result, llm_latency = get_instructor_response(
        llm_client,
        system_prompt,
        ocr_result,
        pydantic_schema,
        effective_model,
        temperature,
    )

    return ocr_result, ocr_latency, llm_result, llm_latency
