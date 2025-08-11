from rapidfuzz.distance import Levenshtein
import numpy as np
from scipy.optimize import linear_sum_assignment


# Normalize text to alphanumeric lowercase for robust matching
def normalize(text: str) -> str:
    return "".join(ch.lower() for ch in str(text) if ch.isalnum())


# Flatten CORD structured JSON into flat key-value pairs
def cord_to_kv(data: dict) -> dict:
    flat = {}

    def walk(prefix, node):
        if node is None:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                next_prefix = f"{prefix}_{key}" if prefix else str(key)
                walk(next_prefix, value)
        elif isinstance(node, list):
            for index, item in enumerate(node):
                next_prefix = f"{prefix}_{index}" if prefix else str(prefix)
                walk(next_prefix, item)
        else:
            flat[prefix] = str(node)

    walk("", data)
    return flat


# Flatten FUNSD-style JSON (headers/others expanded to empty-valued keys)
def funsd_to_kv(data: dict) -> dict:
    flat = {}
    for key, value in data.items():
        if isinstance(value, list) and ("HEADER" in key or "OTHER" in key):
            for item in value:
                flat[str(item)] = ""
        else:
            flat[str(key)] = "" if value is None else str(value)
    return flat


# Compute KV F1 (exact or fuzzy) and confusion counts
def compute_kv_f1(gt: dict, pred: dict, fuzzy: bool = True, thr: float = 0.20):
    gt_pairs = [(normalize(k), normalize(v)) for k, v in gt.items()]
    pred_pairs = [(normalize(k), normalize(v)) for k, v in pred.items()]
    matched_indices = set()
    true_positives = 0
    false_positives = 0

    for pred_key, pred_val in pred_pairs:
        found_match = False
        for idx, (gt_key, gt_val) in enumerate(gt_pairs):
            if idx in matched_indices:
                continue
            key_match = (
                Levenshtein.normalized_distance(pred_key, gt_key) <= thr
                if fuzzy
                else pred_key == gt_key
            )
            val_match = (
                Levenshtein.normalized_distance(pred_val, gt_val) <= thr
                if fuzzy
                else pred_val == gt_val
            )
            if key_match and val_match:
                matched_indices.add(idx)
                found_match = True
                break
        if found_match:
            true_positives += 1
        else:
            false_positives += 1

    false_negatives = len(gt_pairs) - len(matched_indices)
    f1 = (
        2 * true_positives / (2 * true_positives + false_positives + false_negatives)
        if true_positives
        else 0.0
    )
    return f1, true_positives, false_positives, false_negatives


# Compute Hungarian-aligned F1 over canonical pairs
def compute_canonical_f1(gt: dict, pred: dict, tau: float = 0.80):
    gt_pairs = [(normalize(k), normalize(v)) for k, v in gt.items()]
    pred_pairs = [(normalize(k), normalize(v)) for k, v in pred.items()]
    if not gt_pairs or not pred_pairs:
        return 0.0
    n, m = len(gt_pairs), len(pred_pairs)
    similarity = np.zeros((n, m))
    for i, (gk, gv) in enumerate(gt_pairs):
        for j, (pk, pv) in enumerate(pred_pairs):
            key_similarity = 1 - Levenshtein.normalized_distance(gk, pk)
            val_similarity = 1 - Levenshtein.normalized_distance(gv, pv)
            if key_similarity >= tau and val_similarity >= tau:
                similarity[i, j] = (key_similarity + val_similarity) / 2
    row_indices, col_indices = linear_sum_assignment(-similarity)
    true_positives = sum(similarity[i, j] > 0 for i, j in zip(row_indices, col_indices))
    false_positives = len(pred_pairs) - true_positives
    false_negatives = len(gt_pairs) - true_positives
    return (
        2 * true_positives / (2 * true_positives + false_positives + false_negatives)
        if true_positives
        else 0.0
    )


# Compute mean normalized edit distance over matched values
def compute_mean_value_edit_distance(gt: dict, pred: dict, thr: float = 0.20):
    distances = []
    for gt_key, gt_val in gt.items():
        normalized_gt_key = normalize(gt_key)
        best_distance = 1.0
        for pred_key, pred_val in pred.items():
            if (
                Levenshtein.normalized_distance(normalized_gt_key, normalize(pred_key))
                <= thr
            ):
                distance = Levenshtein.normalized_distance(
                    normalize(gt_val), normalize(pred_val)
                )
                if distance < best_distance:
                    best_distance = distance
        if best_distance < 1.0:
            distances.append(best_distance)
    return float(sum(distances) / len(distances)) if distances else 1.0


# Compute precision/recall/accuracy and counts
def compute_confusion_metrics(
    tp: int, fp: int, fn: int, total_gt: int, total_pred: int
):
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    tn = max(0, total_gt + total_pred - tp - fp - fn)
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "accuracy": round(accuracy, 4),
    }


# Compute all metrics for a flat KV ground truth and prediction
def compute_metrics(
    gt: dict, pred: dict, kvf1_thr: float = 0.20, canonf1_tau: float = 0.80
):
    # Compute F1 scores and supporting counts for fuzzy and exact key-value matching
    kv_fuzzy, tp_fuzzy, fp_fuzzy, fn_fuzzy = compute_kv_f1(
        gt, pred, fuzzy=True, thr=kvf1_thr
    )
    kv_exact, tp_exact, fp_exact, fn_exact = compute_kv_f1(
        gt, pred, fuzzy=False, thr=0.0
    )
    # Compute canonical F1 and value quality score
    canonical = compute_canonical_f1(gt, pred, tau=canonf1_tau)
    value_quality = 1 - compute_mean_value_edit_distance(gt, pred, thr=kvf1_thr)

    # Compute confusion metrics for fuzzy and exact matches
    fuzzy_stats = compute_confusion_metrics(
        tp_fuzzy, fp_fuzzy, fn_fuzzy, len(gt), len(pred)
    )
    exact_stats = compute_confusion_metrics(
        tp_exact, fp_exact, fn_exact, len(gt), len(pred)
    )
    return {
        "kv_f1_fuzzy": round(kv_fuzzy, 4),
        "kv_f1_exact": round(kv_exact, 4),
        "canonical_f1": round(canonical, 4),
        "value_quality_score": round(value_quality, 4),
        "fuzzy_tp": fuzzy_stats["tp"],
        "fuzzy_fp": fuzzy_stats["fp"],
        "fuzzy_fn": fuzzy_stats["fn"],
        "fuzzy_tn": fuzzy_stats["tn"],
        "fuzzy_precision": fuzzy_stats["precision"],
        "fuzzy_recall": fuzzy_stats["recall"],
        "fuzzy_accuracy": fuzzy_stats["accuracy"],
        "exact_tp": exact_stats["tp"],
        "exact_fp": exact_stats["fp"],
        "exact_fn": exact_stats["fn"],
        "exact_tn": exact_stats["tn"],
        "exact_precision": exact_stats["precision"],
        "exact_recall": exact_stats["recall"],
        "exact_accuracy": exact_stats["accuracy"],
        "total_gt_pairs": len(gt),
        "total_pred_pairs": len(pred),
    }


# Evaluate a (ground_truth, prediction) pair for a dataset using the appropriate adapter
def evaluate(
    dataset: str,
    ground_truth: dict,
    prediction: dict,
    kvf1_thr: float = 0.20,
    canonf1_tau: float = 0.80,
):
    if dataset.upper() == "CORD":
        gt_kv = cord_to_kv(ground_truth)
        pred_kv = cord_to_kv(prediction)
    elif dataset.upper() == "FUNSD":
        gt_kv = funsd_to_kv(ground_truth)
        pred_kv = funsd_to_kv(prediction)
    else:
        gt_kv, pred_kv = ground_truth, prediction
    return compute_metrics(gt_kv, pred_kv, kvf1_thr=kvf1_thr, canonf1_tau=canonf1_tau)
