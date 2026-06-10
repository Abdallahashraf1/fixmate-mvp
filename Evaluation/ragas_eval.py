import json
import os
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from datasets import Dataset
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
TESTSET_PATH = ROOT / "testset.jsonl"
README_PATH = ROOT / "README.md"
LATEST_RESULT_MARKER = "## Latest Result"


def _load_env() -> None:
    load_dotenv(ROOT / ".env")
    os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")


def _load_testset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing test set: {path}")

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            rows.append(row)
    return rows


def _chat(api_url: str, eval_user_id: str, row: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{api_url.rstrip('/')}/chat/",
        json={
            "session_id": None,
            "user_id": eval_user_id,
            "role": row.get("role", "Car Specialist"),
            "make": row["make"],
            "model": row["model"],
            "query": row["question"],
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def _ragas_imports():
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        context_precision,
        context_recall,
        faithfulness,
    )

    return evaluate, [faithfulness, answer_relevancy, context_precision, context_recall]


def _score_to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _summary(records: list[dict[str, Any]], metric_names: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "count": len(records),
        "metrics": {},
        "failed_cases": [],
    }
    for name in metric_names:
        scores = [
            score
            for record in records
            if (score := _score_to_float(record.get(name))) is not None
        ]
        if not scores:
            summary["metrics"][name] = {
                "average": None,
                "p50": None,
                "p90": None,
                "count": 0,
            }
            continue

        sorted_scores = sorted(scores)
        p90_index = min(len(sorted_scores) - 1, int(round((len(sorted_scores) - 1) * 0.9)))
        summary["metrics"][name] = {
            "average": sum(scores) / len(scores),
            "p50": statistics.median(scores),
            "p90": sorted_scores[p90_index],
            "count": len(scores),
        }

    for record in records:
        low_metrics = [
            name
            for name in metric_names
            if (score := _score_to_float(record.get(name))) is not None and score < 0.7
        ]
        if low_metrics:
            summary["failed_cases"].append(
                {
                    "question": record.get("question"),
                    "low_metrics": low_metrics,
                    "scores": {name: record.get(name) for name in low_metrics},
                    "source_chunk_ids": record.get("source_chunk_ids", []),
                }
            )
    return summary


def _format_score(value: Any) -> str:
    score = _score_to_float(value)
    if score is None:
        return "not available"
    return f"{score:.3f}"


def _interpret_metric(name: str, value: Any) -> str:
    score = _score_to_float(value)
    if score is None:
        return "RAGAS did not return a usable score for this metric; inspect the detailed JSON for errors."

    quality = "strong"
    if score < 0.6:
        quality = "weak"
    elif score < 0.8:
        quality = "mixed"

    messages = {
        "faithfulness": {
            "strong": "Most answer claims were grounded in the retrieved manual chunks.",
            "mixed": "Some claims may not be fully grounded; inspect low-scoring examples for missing or unsupported details.",
            "weak": "The answers are often not grounded enough in retrieved context; prioritize retrieval quality and stricter answer prompting.",
        },
        "answer_relevancy": {
            "strong": "Answers usually address the user question directly.",
            "mixed": "Answers sometimes drift from the exact question; review query rewriting and prompt instructions.",
            "weak": "Answers frequently miss the question intent; inspect failed cases before tuning retrieval.",
        },
        "context_precision": {
            "strong": "Top-ranked retrieved chunks are usually useful.",
            "mixed": "Useful chunks are mixed with less relevant ones; tune BM25/vector weights, RRF, and metadata filtering.",
            "weak": "Retrieved context has too much noise; tune candidate retrieval, namespace filtering, and chunking.",
        },
        "context_recall": {
            "strong": "Retrieval usually finds the evidence needed for the expected answer.",
            "mixed": "Retrieval misses some needed evidence; consider increasing candidate depth or improving chunk metadata.",
            "weak": "Retrieval often misses required evidence; revisit ingestion, chunking, and make/model filters.",
        },
    }
    return messages.get(name, {}).get(quality, f"The score is {quality}; inspect detailed examples for this metric.")


def _update_readme_latest_result(summary: dict[str, Any], summary_path: Path) -> None:
    if not README_PATH.exists():
        return

    text = README_PATH.read_text(encoding="utf-8")
    marker_index = text.find(LATEST_RESULT_MARKER)
    if marker_index == -1:
        prefix = text.rstrip() + "\n\n"
    else:
        prefix = text[:marker_index].rstrip() + "\n\n"

    metrics = summary.get("metrics", {})
    lines = [
        LATEST_RESULT_MARKER,
        "",
        f"Latest eval: {summary.get('created_at', 'unknown')}",
        f"Test cases: {summary.get('count', 0)}",
        f"Summary file: `{summary_path.relative_to(ROOT)}`",
        "",
    ]
    for metric_name in (
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ):
        metric = metrics.get(metric_name, {})
        average = metric.get("average")
        lines.extend(
            [
                f"{metric_name}: {_format_score(average)}",
                f"Interpretation: {_interpret_metric(metric_name, average)}",
                "",
            ]
        )

    failed_cases = summary.get("failed_cases", [])
    if failed_cases:
        lines.extend(
            [
                f"Cases below 0.700 threshold: {len(failed_cases)}",
                "Inspect the detailed JSON/CSV result files for the exact questions, retrieved chunks, and per-metric scores.",
            ]
        )
    else:
        lines.append("Cases below 0.700 threshold: 0")

    README_PATH.write_text(prefix + "\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    _load_env()

    api_url = os.getenv("FIXMATE_API_URL", "http://127.0.0.1:8000")
    eval_user_id = os.getenv("EVAL_USER_ID", "ragas-eval")
    results_dir = ROOT / os.getenv("RAGAS_RESULTS_DIR", "results")
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_testset(TESTSET_PATH)
    if not rows:
        raise RuntimeError("The evaluation test set is empty.")

    run_rows: list[dict[str, Any]] = []
    for row in rows:
        chat = _chat(api_url, eval_user_id, row)
        sources = chat.get("sources") or []
        contexts = [source.get("text", "") for source in sources if source.get("text")]
        run_rows.append(
            {
                "question": row["question"],
                "answer": chat.get("assistant_text", ""),
                "contexts": contexts,
                "ground_truth": row["ground_truth"],
                "make": row["make"],
                "model": row["model"],
                "source_chunk_ids": [source.get("chunk_id") for source in sources],
                "source_metadata": [
                    {
                        "chunk_id": source.get("chunk_id"),
                        "pdf": source.get("source"),
                        "page": source.get("page"),
                        "rrf_score": source.get("rrf_score"),
                    }
                    for source in sources
                ],
                "expected_sources": row.get("expected_sources", []),
            }
        )

    evaluate, metrics = _ragas_imports()
    dataset = Dataset.from_list(
        [
            {
                "question": row["question"],
                "answer": row["answer"],
                "contexts": row["contexts"],
                "ground_truth": row["ground_truth"],
            }
            for row in run_rows
        ]
    )

    result = evaluate(dataset, metrics=metrics, raise_exceptions=False)
    result_df = result.to_pandas()

    detailed_records: list[dict[str, Any]] = []
    for idx, eval_record in enumerate(result_df.to_dict(orient="records")):
        detailed_records.append({**run_rows[idx], **eval_record})

    metric_names = [metric.name for metric in metrics]
    summary = _summary(detailed_records, metric_names)
    summary["created_at"] = datetime.now(timezone.utc).isoformat()
    summary["api_url"] = api_url
    summary["testset"] = str(TESTSET_PATH)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    detailed_json = results_dir / f"{stamp}_ragas_detailed.json"
    detailed_csv = results_dir / f"{stamp}_ragas_detailed.csv"
    summary_json = results_dir / f"{stamp}_ragas_summary.json"

    detailed_json.write_text(
        json.dumps(detailed_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame(detailed_records).to_csv(detailed_csv, index=False)
    summary_json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _update_readme_latest_result(summary, summary_json)

    print(f"Wrote detailed JSON: {detailed_json}")
    print(f"Wrote detailed CSV: {detailed_csv}")
    print(f"Wrote summary JSON: {summary_json}")
    print(f"Updated README latest result: {README_PATH}")


if __name__ == "__main__":
    main()
