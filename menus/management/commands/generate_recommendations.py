"""
Two-model recommendation pipeline for Revove (local-only, no network)

Pipeline:
  - Model A1: Embeddings (gte-small by default) to pick representative reviews
  - Model A2: Dish/attribute extractor (Qwen2 1.5B GGUF via llama.cpp)
  - Model B: Reasoning/synthesis (Qwen2.5 7B GGUF via llama.cpp)

Requirements:
  pip install sentence-transformers numpy
  llama.cpp binary available locally (LLAMA_BIN)

This command assumes the GGUF model files are already on disk. It will fail
early with a clear error if dependencies or model paths are missing.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from django.core.management.base import BaseCommand, CommandError

from menus.models import Place, PlaceRecommendation, Review

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore


# ---------------------------------------------------------------------------
# Simple llama.cpp runner
# ---------------------------------------------------------------------------
class LlamaRunner:
    def __init__(self, llama_bin: Path, model_path: Path, max_tokens: int = 512, temperature: float = 0.4, threads: int = 4):
        self.llama_bin = llama_bin
        self.model_path = model_path
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.threads = threads

    def run(self, prompt: str) -> str:
        # llama-run expects: llama-run [options] model [prompt]
        cmd = [
            str(self.llama_bin),
            "--temp",
            str(self.temperature),
            "--context-size",
            "4096",
            "--threads",
            str(self.threads),
            str(self.model_path),
            prompt,
        ]

        try:
            out = subprocess.check_output(cmd, text=True)
        except FileNotFoundError as exc:
            raise CommandError(f"llama.cpp binary not found at {self.llama_bin}") from exc
        except subprocess.CalledProcessError as exc:  # pragma: no cover - runtime
            raise CommandError(f"llama.cpp invocation failed: {exc}") from exc

        return out.strip()


# ---------------------------------------------------------------------------
# Embedding layer (A1)
# ---------------------------------------------------------------------------
class EmbeddingEngine:
    def __init__(self, model_name: str):
        if SentenceTransformer is None:
            raise CommandError("sentence-transformers is not installed. Please install it to run embeddings.")
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.model.encode(list(texts), convert_to_numpy=True)

    def cluster_reviews(self, reviews: Sequence[str], top_k: int = 20) -> List[str]:
        if not reviews:
            return []
        vectors = self.embed(reviews)
        centroid = np.mean(vectors, axis=0)
        norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(centroid)
        scores = np.dot(vectors, centroid) / np.maximum(norms, 1e-8)
        idxs = np.argsort(scores)[::-1][:top_k]
        return [reviews[i] for i in idxs]


# ---------------------------------------------------------------------------
# Dish extraction (A2)
# ---------------------------------------------------------------------------
class DishExtractor:
    def __init__(self, runner: LlamaRunner):
        self.runner = runner

    def extract(self, review_batch: List[str], top_k: int = 10, debug_raw: bool = False) -> Tuple[List[Dict[str, Any]], str]:
        prompt = f"""
You are a food review analyst. Extract dish or menu-item mentions from these reviews.

Return ONLY JSON array. Each entry:
{{
  "menu_item": "name",
  "sentiment": 0-1,
  "keywords": ["k1", "k2"],
  "review_count": int
}}

Limit to the top {top_k} distinct items, aggregate duplicates, and keep keywords concise.

Reviews:
{json.dumps(review_batch, indent=2)}
"""
        raw = self.runner.run(prompt)
        parsed = self._parse_json_list(raw)
        if debug_raw:
            return parsed, raw
        return parsed, raw

    @staticmethod
    def _parse_json_list(text: str) -> List[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            start, end = text.find("["), text.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except Exception:
                    return []
            return []


# ---------------------------------------------------------------------------
# Reasoning / synthesis (B)
# ---------------------------------------------------------------------------
class ReasoningEngine:
    def __init__(self, runner: LlamaRunner):
        self.runner = runner

    def generate_recommendations(
        self, place_name: str, extracted_items: List[Dict[str, Any]], max_recs: int, debug_raw: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        prompt = f"""
You generate a "What to Order" section for a restaurant guide.

Restaurant: "{place_name}"

Signals from reviews (already extracted):
{json.dumps(extracted_items, indent=2)}

Write {max_recs} concise recommendations (6-20 words each).
Return ONLY JSON array:
[{{"text": "...", "confidence": 0.0-1.0}}]
"""
        raw = self.runner.run(prompt)
        parsed = self._parse_json_list(raw)
        results: List[Dict[str, Any]] = []
        for entry in parsed:
            if isinstance(entry, str):
                results.append({"text": entry, "confidence": None})
            elif isinstance(entry, dict) and "text" in entry:
                results.append(
                    {
                        "text": str(entry["text"]),
                        "confidence": float(entry.get("confidence"))
                        if entry.get("confidence") is not None
                        else None,
                    }
                )
        results = results[:max_recs]
        if debug_raw:
            return results, raw
        return results, raw

    @staticmethod
    def _parse_json_list(text: str) -> List[Dict[str, Any]]:
        try:
            return json.loads(text)
        except Exception:
            start, end = text.find("["), text.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except Exception:
                    return []
            return []


# ---------------------------------------------------------------------------
# Django management command entrypoint
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = "Generate place-level recommendations using the two-model pipeline (embedding -> extraction -> reasoning)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--llama-bin",
            default="./llama.cpp/main",
            help="Path to llama.cpp binary (compiled main).",
        )
        parser.add_argument(
            "--embed-model",
            default="thenlper/gte-small",
            help="Embedding model name/path (Model A1).",
        )
        parser.add_argument(
            "--extractor-model",
            required=True,
            help="Path to Qwen2 1.5B instruct GGUF (Model A2).",
        )
        parser.add_argument(
            "--reasoning-model",
            required=True,
            help="Path to Qwen2.5 7B or Mistral 7B instruct GGUF (Model B).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=400,
            help="Max number of reviews to aggregate per place before sampling.",
        )
        parser.add_argument(
            "--max-recs",
            type=int,
            default=5,
            help="Maximum recommendations to create per place.",
        )
        parser.add_argument(
            "--places",
            nargs="*",
            type=int,
            help="Optional list of Place IDs to process.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do not persist recommendations; only print them.",
        )
        parser.add_argument(
            "--threads",
            type=int,
            default=4,
            help="Threads to pass to llama-run.",
        )
        parser.add_argument(
            "--debug-raw",
            action="store_true",
            help="Log raw LLM outputs for extraction and reasoning.",
        )

    def handle(self, *args, **options):
        llama_bin = Path(options["llama_bin"])
        extractor_path = Path(options["extractor_model"])
        reasoning_path = Path(options["reasoning_model"])
        embed_model = options["embed_model"]
        limit = options["limit"]
        max_recs = options["max_recs"]
        dry_run = options["dry_run"]
        threads = options["threads"]
        debug_raw = options["debug_raw"]

        self._validate_paths(llama_bin, extractor_path, reasoning_path)

        # Initialize engines
        embedder = EmbeddingEngine(embed_model)
        extractor_runner = LlamaRunner(llama_bin, extractor_path, max_tokens=512, temperature=0.2, threads=threads)
        reasoning_runner = LlamaRunner(llama_bin, reasoning_path, max_tokens=512, temperature=0.6, threads=threads)
        extractor = DishExtractor(extractor_runner)
        reasoner = ReasoningEngine(reasoning_runner)

        qs = Place.objects.all()
        if options.get("places"):
            qs = qs.filter(id__in=options["places"])

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Starting two-model pipeline for {total} places"))

        for place in qs:
            reviews = list(
                place.reviews.order_by("-rating", "-created_at")
                .only("rating", "text", "created_at")
                [:limit]
            )
            review_texts = [r.text for r in reviews if r.text]
            if not review_texts:
                self.stdout.write(self.style.WARNING(f"No review text for {place.name}; skipping"))
                continue

            # Print the reviews being processed (truncated for readability)
            self.stdout.write(self.style.NOTICE(f"Reviews for {place.name}:"))
            for r in reviews:
                snippet = (r.text or "").replace("\n", " ")[:200]
                self.stdout.write(f"  - [{r.rating}] {snippet}")

            representative = embedder.cluster_reviews(review_texts, top_k=20)
            if not representative:
                self.stdout.write(self.style.WARNING(f"No representative reviews for {place.name}; skipping"))
                continue

            extracted_items, extraction_raw = extractor.extract(representative, top_k=max_recs * 2, debug_raw=debug_raw)
            if debug_raw:
                self.stdout.write(self.style.WARNING(f"[debug] extractor raw output for {place.name}:\n{extraction_raw[:2000]}"))
            if not extracted_items:
                self.stdout.write(self.style.WARNING(f"No dishes extracted for {place.name}; skipping"))
                continue

            recs, recs_raw = reasoner.generate_recommendations(
                place.name, extracted_items, max_recs=max_recs, debug_raw=debug_raw
            )
            if debug_raw:
                self.stdout.write(self.style.WARNING(f"[debug] reasoning raw output for {place.name}:\n{recs_raw[:2000]}"))
            if not recs:
                self.stdout.write(self.style.WARNING(f"No recommendations produced for {place.name}"))
                continue

            self.stdout.write(self.style.SUCCESS(f"Generated {len(recs)} recommendations for {place.name}"))
            for idx, rec in enumerate(recs, start=1):
                self.stdout.write(f"  #{idx}: {rec['text']} (confidence={rec.get('confidence')})")

            if dry_run:
                continue

            PlaceRecommendation.objects.filter(place=place).delete()
            for i, rec in enumerate(recs[:max_recs], start=1):
                PlaceRecommendation.objects.create(
                    place=place,
                    text=rec["text"][:255],
                    rank=i,
                    confidence=rec.get("confidence"),
                    source="llm",
                )

        self.stdout.write(self.style.SUCCESS("Recommendation generation complete"))

    def _validate_paths(self, llama_bin: Path, extractor_path: Path, reasoning_path: Path) -> None:
        if not llama_bin.exists():
            raise CommandError(f"llama.cpp binary not found at {llama_bin}")
        if not extractor_path.exists():
            raise CommandError(f"Extractor model not found at {extractor_path}")
        if not reasoning_path.exists():
            raise CommandError(f"Reasoning model not found at {reasoning_path}")
