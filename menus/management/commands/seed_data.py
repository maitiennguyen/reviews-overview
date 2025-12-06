from django.core.management.base import BaseCommand
from menus.models import Place, MenuItem

class Command(BaseCommand):
    help = "Seed sample Bozeman places and menu items."

    def handle(self, *args, **options):
        jam, _ = Place.objects.get_or_create(
            name="Jam!",
            defaults={
                "google_place_id": "fake-jam-id",
                "address": "25 W Main St, Bozeman, MT 59715",
            },
        )
        items = [
            "Jam! Benedict",
            "Huevos Rancheros",
            "Cinnamon Roll Pancakes",
            "Avocado Toast",
        ]
        for name in items:
            MenuItem.objects.get_or_create(place=jam, name=name)

        bbbb, _ = Place.objects.get_or_create(
            name="Backcountry Burger Bar",
            defaults={
                "google_place_id": "fake-backcountry-id",
                "address": "125 W Main St, Bozeman, MT 59715",
            },
        )
        items = ["Classic Burger", "Bison Burger", "Fries", "Backcountry Salad"]
        for name in items:
            MenuItem.objects.get_or_create(place=bbbb, name=name)

        treeline, _ = Place.objects.get_or_create(
            name="Treeline Coffee Roasters",
            defaults={
                "google_place_id": "fake-treeline-id",
                "address": "624 N Broadway Ave, Bozeman, MT 59715",
            },
        )
        items = ["Latte", "Cappuccino", "Cold Brew", "Matcha Latte", "Blueberry Muffin"]
        for name in items:
            MenuItem.objects.get_or_create(place=treeline, name=name)

        self.stdout.write(self.style.SUCCESS("Seed data inserted!"))
