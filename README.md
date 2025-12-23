# revove

Revove ingests Google reviews for Bozeman food and drink spots and surfaces them via a Django REST API and a Next.js frontend. AI-generated “what to order” recommendations exist but are hidden while we iterate on quality. Item-level summaries will follow once more reviews are collected (the Google Places New API only returns ~5 top reviews per place and they rotate rarely). The current focus is search-by-item mentions in reviews.
