from django.core.management.base import BaseCommand

from registerapp.models import Category, City, Country


class Command(BaseCommand):
    help = "Seed starter Category, Country, and City data for event filters."

    def handle(self, *args, **options):
        categories = [
            "Music",
            "Tech",
            "Business",
            "Sports",
            "Workshop",
            "Community",
        ]

        country_city_map = {
            "India": ["Mumbai", "Delhi", "Bengaluru", "Pune", "Hyderabad"],
            "United States": ["New York", "San Francisco", "Austin", "Seattle", "Chicago"],
            "United Kingdom": ["London", "Manchester", "Birmingham", "Leeds"],
            "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary"],
        }

        created_categories = 0
        created_countries = 0
        created_cities = 0

        for category_name in categories:
            _, created = Category.objects.get_or_create(name=category_name)
            if created:
                created_categories += 1

        for country_name, city_list in country_city_map.items():
            country, created_country = Country.objects.get_or_create(name=country_name)
            if created_country:
                created_countries += 1

            for city_name in city_list:
                _, created_city = City.objects.get_or_create(name=city_name, country=country)
                if created_city:
                    created_cities += 1

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))
        self.stdout.write(
            f"Categories added: {created_categories}, Countries added: {created_countries}, Cities added: {created_cities}"
        )
