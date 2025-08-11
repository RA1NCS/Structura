from metrics import evaluate as eval_metrics
import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from inference import get_docintel_result, get_instructor_response
from clients import get_document_intelligence_client, get_instructor_client


# Wrapper to reuse constant benchmark parameters and clients
class Benchmarker:
    def __init__(
        self,
        dataset_name,
        pydantic_schema,
        model_name,
        doc_client,
        llm_client,
        kvf1_thr=0.20,
        canonf1_tau=0.80,
        temperature=1.0,
    ):
        self.dataset_name = dataset_name
        self.pydantic_schema = pydantic_schema
        self.model_name = model_name
        self.doc_client = doc_client
        self.llm_client = llm_client
        self.kvf1_thr = kvf1_thr
        self.canonf1_tau = canonf1_tau
        self.temperature = temperature

    # Run a benchmark for a given file set and system prompt
    def run(self, file_set, system_prompt, fewshot_enabled=True, iteration=None):
        return benchmark(
            file_set=file_set,
            dataset_name=self.dataset_name,
            system_prompt=system_prompt,
            pydantic_schema=self.pydantic_schema,
            model_name=self.model_name,
            doc_client=self.doc_client,
            llm_client=self.llm_client,
            kvf1_thr=self.kvf1_thr,
            canonf1_tau=self.canonf1_tau,
            temperature=self.temperature,
            fewshot_enabled=fewshot_enabled,
            iteration=iteration,
        )


# Resolve the image file path for an id by checking supported extensions
def resolve_image_path(images_dir, file_id, exts=(".png", ".jpg", ".jpeg")):
    for ext in exts:
        candidate = os.path.join(images_dir, f"{file_id}{ext}")
        if os.path.exists(candidate):
            return candidate
    return None


# Load and parse the JSON annotation for an id
def load_annotation(ann_dir, file_id):
    ann_path = os.path.join(ann_dir, f"{file_id}.json")
    with open(ann_path, "r") as f:
        return json.load(f)


# Run OCR and LLM in parallel with per-file retries and timeouts; persist metrics per file
def benchmark(
    file_set,
    dataset_name,
    system_prompt,
    pydantic_schema,
    model_name,
    doc_client=None,
    llm_client=None,
    kvf1_thr=0.20,
    canonf1_tau=0.80,
    temperature=1.0,
    fewshot_enabled=True,
    iteration=None,
    max_workers=30,
):
    # Prepare output locations for this benchmark run
    os.makedirs("benchmarks", exist_ok=True)
    base_dir = os.path.join("datasets", dataset_name)
    images_dir = os.path.join(base_dir, "images")
    ann_dir = os.path.join(base_dir, "annotations")

    fewshot_str = str(bool(fewshot_enabled)).lower()
    temp_str = str(temperature)
    iteration_str = ("_" + str(iteration)) if iteration else ""
    out_file = os.path.join(
        "benchmarks",
        f"{dataset_name}_{model_name}_{fewshot_str}_{temp_str}{iteration_str}.json",
    )

    # Initialize the results map to be written incrementally
    results_map = {}
    with open(out_file, "w") as f:
        json.dump(results_map, f)

    doc_client = doc_client or get_document_intelligence_client()
    llm_client = llm_client or get_instructor_client()

    # Map each file id to its image and annotation paths
    contexts = {}
    for file_id in file_set:
        img_path = resolve_image_path(images_dir, file_id)
        ann_path = os.path.join(ann_dir, f"{file_id}.json")
        contexts[file_id] = (img_path, ann_path)

    # Track active futures, start times, and per-file retry counts; cache OCR text for LLM retries
    ocr_futures = {}
    llm_futures = {}
    ocr_started = {}
    llm_started = {}
    ocr_retry_counts = {}
    llm_retry_counts = {}
    llm_inputs = {}
    total_files = len(file_set)
    success_count = 0

    # Use separate pools for OCR and LLM to avoid head-of-line blocking
    with ThreadPoolExecutor(max_workers=max_workers) as ocr_pool, ThreadPoolExecutor(
        max_workers=max_workers
    ) as llm_pool:
        # Submit initial OCR tasks
        for file_id, (img_path, _) in contexts.items():
            # Submit OCR and record start time
            fut = ocr_pool.submit(get_docintel_result, doc_client, file_path=img_path)
            ocr_futures[fut] = file_id
            ocr_started[fut] = time.time()

        # Drive completion of OCR and LLM tasks with timeout handling and retries
        while ocr_futures or llm_futures:
            made_progress = False

            # Handle completed or timed-out OCR
            for fut in list(ocr_futures.keys()):
                file_id = ocr_futures[fut]
                if fut.done():
                    # On OCR success, cache text and schedule LLM
                    try:
                        ocr_text, ocr_ms = fut.result()
                        llm_inputs[file_id] = ocr_text
                        lf = llm_pool.submit(
                            get_instructor_response,
                            llm_client,
                            system_prompt,
                            ocr_text,
                            pydantic_schema,
                            model_name,
                            temperature,
                        )
                        llm_futures[lf] = (file_id, ocr_ms)
                        llm_started[lf] = time.time()
                    # On OCR exception, retry up to two times, else log failure
                    except Exception as e:
                        if ocr_retry_counts.get(file_id, 0) < 2:
                            ocr_retry_counts[file_id] = (
                                ocr_retry_counts.get(file_id, 0) + 1
                            )
                            img_path = contexts[file_id][0]
                            new_fut = ocr_pool.submit(
                                get_docintel_result, doc_client, file_path=img_path
                            )
                            ocr_futures[new_fut] = file_id
                            ocr_started[new_fut] = time.time()
                        else:
                            failures_file = out_file.replace(".json", "_failures.txt")
                            with open(failures_file, "a") as ef:
                                kind = "OCR"
                                ef.write(f"{file_id}\t{kind}\t{repr(e)}\n")
                    del ocr_futures[fut]
                    del ocr_started[fut]
                    made_progress = True
                else:
                    # On OCR timeout, cancel and retry up to two times, else log timeout
                    if time.time() - ocr_started[fut] > 120:
                        try:
                            fut.cancel()
                        except Exception:
                            pass
                        if ocr_retry_counts.get(file_id, 0) < 2:
                            ocr_retry_counts[file_id] = (
                                ocr_retry_counts.get(file_id, 0) + 1
                            )
                            img_path = contexts[file_id][0]
                            new_fut = ocr_pool.submit(
                                get_docintel_result, doc_client, file_path=img_path
                            )
                            ocr_futures[new_fut] = file_id
                            ocr_started[new_fut] = time.time()
                        else:
                            failures_file = out_file.replace(".json", "_failures.txt")
                            with open(failures_file, "a") as ef:
                                ef.write(f"{file_id}\tOCR_TIMEOUT\t'timed out'\n")
                        del ocr_futures[fut]
                        del ocr_started[fut]
                        made_progress = True

            # Handle completed or timed-out LLM
            for fut in list(llm_futures.keys()):
                file_id, ocr_ms = llm_futures[fut]
                if fut.done():
                    # On LLM success, compute metrics and persist the record
                    try:
                        llm_json, llm_ms = fut.result()
                        with open(contexts[file_id][1], "r") as gf:
                            gt = json.load(gf)
                        metrics = eval_metrics(
                            dataset_name, gt, llm_json, kvf1_thr, canonf1_tau
                        )
                        record = {
                            "ocr_latency": ocr_ms,
                            "llm_latency": llm_ms,
                            **metrics,
                        }
                        results_map[file_id] = record
                        with open(out_file, "w") as wf:
                            json.dump(results_map, wf, indent=2)
                        success_count += 1
                    # On LLM exception, retry up to two times using cached OCR, else log failure
                    except Exception as e:
                        if llm_retry_counts.get(file_id, 0) < 2:
                            llm_retry_counts[file_id] = (
                                llm_retry_counts.get(file_id, 0) + 1
                            )
                            ocr_text = llm_inputs.get(file_id)
                            lf = llm_pool.submit(
                                get_instructor_response,
                                llm_client,
                                system_prompt,
                                ocr_text,
                                pydantic_schema,
                                model_name,
                                temperature,
                            )
                            llm_futures[lf] = (file_id, ocr_ms)
                            llm_started[lf] = time.time()
                        else:
                            failures_file = out_file.replace(".json", "_failures.txt")
                            with open(failures_file, "a") as ef:
                                kind = "LLM"
                                ef.write(f"{file_id}\t{kind}\t{repr(e)}\n")
                    del llm_futures[fut]
                    del llm_started[fut]
                    made_progress = True
                else:
                    # On LLM timeout, cancel and retry up to two times using cached OCR, else log timeout
                    if time.time() - llm_started[fut] > 90:
                        try:
                            fut.cancel()
                        except Exception:
                            pass
                        if llm_retry_counts.get(file_id, 0) < 2:
                            llm_retry_counts[file_id] = (
                                llm_retry_counts.get(file_id, 0) + 1
                            )
                            ocr_text = llm_inputs.get(file_id)
                            lf = llm_pool.submit(
                                get_instructor_response,
                                llm_client,
                                system_prompt,
                                ocr_text,
                                pydantic_schema,
                                model_name,
                                temperature,
                            )
                            llm_futures[lf] = (file_id, ocr_ms)
                            llm_started[lf] = time.time()
                        else:
                            failures_file = out_file.replace(".json", "_failures.txt")
                            with open(failures_file, "a") as ef:
                                ef.write(f"{file_id}\tLLM_TIMEOUT\t'timed out'\n")
                        del llm_futures[fut]
                        del llm_started[fut]
                        made_progress = True

            if not made_progress:
                time.sleep(0.2)

    # Print completion summary and return the output file path
    print(f"Completed {success_count}/{total_files} files → {out_file}")
    return out_file


# Load a benchmark file
def load_benchmark(benchmark_file):
    with open(benchmark_file, "r") as f:
        return json.load(f)


# Score a single file
def score_single_file(data) -> float:
    metrics = ["kv_f1_fuzzy", "kv_f1_exact", "canonical_f1", "value_quality_score"]
    return sum(data[m] for m in metrics) / len(metrics)


# Compute the average of four metrics per file, then average across all files
def score_benchmark(benchmark_file) -> float:
    results_map = load_benchmark(benchmark_file)

    file_scores = []
    for file_id in results_map:
        score = score_single_file(results_map[file_id])
        file_scores.append(score)
    return sum(file_scores) / len(file_scores) if file_scores else 0


# Get the top N files from a benchmark file
def get_top_files(benchmark_file, num_files=5, mode="best") -> list[str]:
    results_map = load_benchmark(benchmark_file)
    scored = []

    for file_id in results_map:
        score = score_single_file(results_map[file_id])
        scored.append((file_id, score))

    scored.sort(key=lambda x: x[1], reverse=mode == "best")

    return [fid for fid, _ in scored[:num_files]]
