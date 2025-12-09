import os
import json
import re
from collections import Counter
from typing import List, Dict, Any

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from menus.models import Place, Review, PlaceRecommendation


try:
    import openai
except Exception:
    openai = None

try:
    from transformers import pipeline
    import torch
except Exception:
    print("no pipeline")
    pipeline = None
    torch = None


STOPWORDS = {
    'the', 'and', 'a', 'an', 'of', 'to', 'in', 'for', 'on', 'with', 'is',
    'it', 'that', 'this', 'they', 'i', 'we', 'you', 'but', 'are', 'was',
}


def extract_candidate_phrases(text: str, top_n: int = 5) -> List[str]:
    # Simple bigram frequency extractor (mock fallback)
    words = [w.lower() for w in re.findall(r"\w+", text) if w.lower() not in STOPWORDS]
    bigrams = zip(words, words[1:])
    counts = Counter([f"{a} {b}" for a, b in bigrams])
    return [phrase for phrase, _ in counts.most_common(top_n)]


class Command(BaseCommand):
    help = "Generate 1-3 place-level 'what to order' recommendations using an LLM or a mock fallback."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=5, help='Max number of recent reviews to aggregate per place')
        parser.add_argument('--places', nargs='*', type=int, help='Optional list of Place IDs to process')
        parser.add_argument('--provider', choices=['gpt_j', 'mock'], default='gpt_j', help='LLM provider to use')
        parser.add_argument('--max-recs', type=int, default=3, help='Maximum recommendations to create per place')
        parser.add_argument('--dry-run', action='store_true', help='Do not persist recommendations; just print them')

    def handle(self, *args, **options):
        limit = options['limit']
        provider = options['provider']
        max_recs = options['max_recs']
        dry_run = options['dry_run']

        if provider == 'gpt_j':
            # Two integration options:
            # 1) Remote inference endpoint set via GPT_J_API_URL
            # 2) Local transformers pipeline if `transformers` is installed and GPT_J_MODEL is set
            neox_url = os.getenv('GPT_J_API_URL')
            neox_model = os.getenv('GPT_J_MODEL')
            print(neox_model, pipeline)
            if not neox_url and not (pipeline and neox_model):
                self.stdout.write(self.style.WARNING('GPT-J not configured (no GPT_J_API_URL and no local GPT_J_MODEL+transformers) — falling back to mock provider'))
                provider = 'mock'

        qs = Place.objects.all()
        if options.get('places'):
            qs = qs.filter(id__in=options['places'])

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f'Starting recommendation generation for {total} places (provider={provider})'))

        for place in qs:
            reviews = list(place.reviews.order_by('-rating', '-created_at')[:limit])
            if not reviews:
                self.stdout.write(self.style.WARNING(f'No reviews for {place.name}; skipping'))
                continue

            prompt = self.build_prompt(place, reviews, max_recs)

            if provider == 'gpt_j':
                recs = self.call_gpt_j(prompt, max_recs)
            else:
                recs = self.mock_generate(reviews, max_recs)

            if not recs:
                self.stdout.write(self.style.WARNING(f'No recommendations generated for {place.name}'))
                continue

            self.stdout.write(self.style.SUCCESS(f'Generated {len(recs)} recommendations for {place.name}'))

            for i, r in enumerate(recs, start=1):
                text = r.get('text') if isinstance(r, dict) else str(r)
                confidence = r.get('confidence') if isinstance(r, dict) else None
                self.stdout.write(f'  #{i}: {text} (confidence={confidence})')

            if dry_run:
                continue

            # Replace existing recommendations for the place
            PlaceRecommendation.objects.filter(place=place).delete()

            for i, r in enumerate(recs[:max_recs], start=1):
                text = r.get('text') if isinstance(r, dict) else str(r)
                confidence = r.get('confidence') if isinstance(r, dict) else None
                PlaceRecommendation.objects.create(
                    place=place,
                    text=text[:255],
                    rank=i,
                    confidence=confidence,
                    source=(r.get('source') if isinstance(r, dict) and r.get('source') else 'ai')
                )

        self.stdout.write(self.style.SUCCESS('Recommendation generation complete'))

    def build_prompt(self, place: Place, reviews: List[Review], max_recs: int) -> str:
        lines = []
        lines.append(f"Place: {place.name}")
        if place.rating:
            lines.append(f"Rating: {place.rating} ({place.user_ratings_total} ratings)")
        if place.address:
            lines.append(f"Address: {place.address}")

        lines.append('\nRecent Reviews:')
        for r in reviews:
            created = r.created_at.isoformat() if r.created_at else ''
            lines.append(f"- [{r.rating}★] {r.text} (by {r.author_name} on {created})")

        lines.append('\nInstructions:')
        lines.append(f"Generate up to {max_recs} concise (6-18 words) 'what to order' recommendations for this place derived from the reviews and place metadata.")
        lines.append('Return a JSON array of objects: [{"text": "...", "confidence": 0.8}, ...]. Do NOT include any extra explanation.')

        return '\n'.join(lines)

    def call_gpt_j(self, prompt: str, max_recs: int) -> List[Dict[str, Any]]:
        """Call a GPT-J style model either via a remote inference endpoint
        (set `GPT_J_API_URL`) or via a local `transformers` pipeline
        (set `GPT_J_MODEL` and have `transformers` installed).
        The endpoint is expected to return text or JSON similar to OpenAI responses.
        """
        neox_url = os.getenv('GPT_J_API_URL')
        neox_model = os.getenv('GPT_J_MODEL')

        # Remote HTTP endpoint integration
        if neox_url:
            try:
                payload = {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 300, "temperature": 0.2, "top_p": 0.95},
                }
                resp = __import__('requests').post(neox_url, json=payload, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                # Endpoint may return a list of dicts with 'generated_text' or a single dict
                text = None
                if isinstance(data, list) and data:
                    text = data[0].get('generated_text') or data[0].get('text')
                elif isinstance(data, dict):
                    text = data.get('generated_text') or data.get('generated_texts') or data.get('text')

                if not text:
                    # fallback: try raw text
                    text = resp.text

                # attempt to extract JSON array from the output
                try:
                    parsed = json.loads(text)
                except Exception:
                    # try to find a JSON substring
                    m = re.search(r"\[\s*\{.*\}\s*\]", text, re.S)
                    if m:
                        parsed = json.loads(m.group(0))
                    else:
                        # last resort: return the raw text as one recommendation
                        return [{'text': text.strip(), 'confidence': None, 'source': 'gpt_j'}]

                results = []
                for item in parsed:
                    if isinstance(item, str):
                        results.append({'text': item})
                    elif isinstance(item, dict):
                        results.append(item)
                return results
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'GPT-J remote call failed: {exc}'))
                return []

        # Local transformers pipeline
        if pipeline and neox_model:
            try:
                device = 0 if torch and torch.cuda.is_available() else -1
                gen = pipeline('text-generation', model=neox_model, tokenizer=neox_model, device=device)
                out = gen(prompt, max_new_tokens=300, do_sample=False)
                text = out[0].get('generated_text') if out and isinstance(out, list) else None
                if not text:
                    return []

                try:
                    parsed = json.loads(text)
                except Exception:
                    m = re.search(r"\[\s*\{.*\}\s*\]", text, re.S)
                    if m:
                        parsed = json.loads(m.group(0))
                    else:
                        return [{'text': text.strip(), 'confidence': None, 'source': 'gpt_j'}]

                results = []
                for item in parsed:
                    if isinstance(item, str):
                        results.append({'text': item})
                    elif isinstance(item, dict):
                        results.append(item)
                return results
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'GPT-J local generation failed: {exc}'))
                return []

        return []

    def mock_generate(self, reviews: List[Review], max_recs: int) -> List[Dict[str, Any]]:
        # Heuristic: find common bigrams across top-rated reviews and format recommendations
        texts = ' '.join(r.text or '' for r in reviews)
        phrases = extract_candidate_phrases(texts, top_n=max_recs * 3)
        recs = []
        for p in phrases[:max_recs]:
            recs.append({'text': f'Try the {p}', 'confidence': 0.5, 'source': 'mock'})
        return recs
