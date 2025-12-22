from django.core.management.base import BaseCommand
from menus.models import Place


class Command(BaseCommand):
    help = "Remove grocery-store places (e.g., Safeway, Smith's) from the database."

    DEFAULT_KEYWORDS = [
        "safeway",
        "smith",
        "smiths",
        "smith's",
        "grocery",
        "market",
        "walmart",
        "costco",
        "albertsons",
        "whole foods",
        "trader joe",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which places would be removed without deleting.",
        )
        parser.add_argument(
            "--keywords",
            nargs="*",
            help="Extra lowercase keywords to match in place names (in addition to defaults).",
        )

    def handle(self, *args, **options):
        extra_keywords = [k.strip().lower() for k in options.get("keywords") or [] if k.strip()]
        needles = self.DEFAULT_KEYWORDS + extra_keywords

        matches = []
        for place in Place.objects.all():
            name = (place.name or "").lower()
            if any(key in name for key in needles):
                matches.append(place)

        if not matches:
            self.stdout.write(self.style.SUCCESS("No grocery-like places found."))
            return

        self.stdout.write(self.style.NOTICE(f"Found {len(matches)} place(s) to remove:"))
        for p in matches:
            self.stdout.write(f"- {p.id}: {p.name}")

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("Dry run enabled; no rows deleted."))
            return

        ids = [p.id for p in matches]
        deleted, _ = Place.objects.filter(id__in=ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} place(s) (reviews cascade via FK)."))
