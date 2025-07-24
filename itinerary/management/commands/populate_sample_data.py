from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from destinations.models import City, DestinationCategory, Destination
from guides.models import Language, PersonalityTrait, TourGuide
from itinerary.models import TravelInterest

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate database with sample data for MVP testing'

    def handle(self, *args, **options):
        self.stdout.write('Populating database with sample data...')

        # Create travel interests
        interests_data = [
            ('Nature', 'Mountains, forests, beaches, wildlife'),
            ('History', 'Museums, temples, historical sites'),
            ('Food', 'Local cuisine, street food, restaurants'),
            ('Culture', 'Traditional arts, crafts, festivals'),
            ('Adventure', 'Hiking, water sports, extreme activities'),
            ('Shopping', 'Markets, malls, local products'),
            ('Architecture', 'Buildings, monuments, urban design'),
            ('Photography', 'Scenic views, cultural sites'),
            ('Relaxation', 'Spas, beaches, quiet places'),
            ('Nightlife', 'Bars, clubs, entertainment'),
        ]

        for name, keywords in interests_data:
            TravelInterest.objects.get_or_create(
                name=name,
                defaults={'keywords': keywords}
            )

        # Create languages
        languages_data = [
            ('Indonesian', 'id'),
            ('English', 'en'),
            ('Javanese', 'jv'),
            ('Sundanese', 'su'),
            ('Mandarin', 'zh'),
            ('Arabic', 'ar'),
        ]

        for name, code in languages_data:
            Language.objects.get_or_create(
                name=name,
                defaults={'code': code}
            )

        # Create personality traits
        traits_data = [
            ('Funny', 'Humorous and entertaining guide'),
            ('Informative', 'Provides detailed historical and cultural information'),
            ('Energetic', 'High energy and enthusiastic'),
            ('Patient', 'Takes time to explain and answer questions'),
            ('Adventurous', 'Loves outdoor activities and exploration'),
            ('Professional', 'Formal and business-like approach'),
            ('Friendly', 'Warm and approachable personality'),
            ('Local Expert', 'Deep knowledge of local customs and hidden gems'),
        ]

        for name, description in traits_data:
            PersonalityTrait.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )

        # Create destination categories
        categories_data = [
            ('Nature', 'Natural attractions like parks, mountains, beaches', 'fa-leaf'),
            ('History', 'Historical sites, museums, monuments', 'fa-landmark'),
            ('Culture', 'Cultural sites, temples, traditional villages', 'fa-mosque'),
            ('Food', 'Restaurants, food courts, local eateries', 'fa-utensils'),
            ('Shopping', 'Markets, malls, souvenir shops', 'fa-shopping-bag'),
            ('Adventure', 'Adventure sports, hiking trails', 'fa-mountain'),
            ('Entertainment', 'Theme parks, entertainment venues', 'fa-theater-masks'),
            ('Accommodation', 'Hotels, guesthouses, resorts', 'fa-bed'),
        ]

        for name, description, icon in categories_data:
            DestinationCategory.objects.get_or_create(
                name=name,
                defaults={'description': description, 'icon': icon}
            )

        # Create Malang city (MVP focus)
        malang, created = City.objects.get_or_create(
            name='Malang',
            defaults={
                'description': 'A beautiful city in East Java known for its cool climate, historical sites, and natural attractions.',
                'province': 'East Java',
                'country': 'Indonesia'
            }
        )

        if created:
            self.stdout.write(f'Created city: {malang.name}')

        # Create sample destinations in Malang
        destinations_data = [
            {
                'name': 'Coban Rondo Waterfall',
                'category': 'Nature',
                'description': 'A beautiful waterfall surrounded by pine forests, perfect for nature lovers and photography enthusiasts.',
                'address': 'Pandesari Village, Pujon District, Malang Regency',
                'average_cost': 15000,
                'estimated_duration_hours': 3.0,
                'rating': 4.5,
                'popularity_score': 85,
                'opening_hours': '08:00-17:00',
                'best_time_to_visit': 'Morning',
                'latitude': -7.8667,
                'longitude': 112.4833,
            },
            {
                'name': 'Malang Old Town',
                'category': 'History',
                'description': 'Historic downtown area with Dutch colonial architecture, perfect for cultural exploration and photography.',
                'address': 'Central Malang, Klojen District',
                'average_cost': 0,
                'estimated_duration_hours': 4.0,
                'rating': 4.3,
                'popularity_score': 90,
                'opening_hours': '24 hours',
                'best_time_to_visit': 'Afternoon',
                'latitude': -7.9833,
                'longitude': 112.6167,
            },
            {
                'name': 'Jatim Park 2',
                'category': 'Entertainment',
                'description': 'Family theme park featuring zoo exhibits, educational shows, and fun activities for all ages.',
                'address': 'Oro-oro Ombo, Batu City',
                'average_cost': 90000,
                'estimated_duration_hours': 6.0,
                'rating': 4.2,
                'popularity_score': 95,
                'opening_hours': '08:30-16:30',
                'best_time_to_visit': 'Morning',
                'latitude': -7.8833,
                'longitude': 112.5167,
            },
            {
                'name': 'Alun-Alun Malang',
                'category': 'Culture',
                'description': 'The main town square of Malang, a great place to experience local culture and evening activities.',
                'address': 'Jl. Tugu, Klojen, Malang',
                'average_cost': 0,
                'estimated_duration_hours': 2.0,
                'rating': 4.1,
                'popularity_score': 75,
                'opening_hours': '24 hours',
                'best_time_to_visit': 'Evening',
                'latitude': -7.9833,
                'longitude': 112.6167,
            },
            {
                'name': 'Sarinah Malang Plaza',
                'category': 'Shopping',
                'description': 'Popular shopping center with local and international brands, food court, and entertainment.',
                'address': 'Jl. Basuki Rahmat, Malang',
                'average_cost': 100000,
                'estimated_duration_hours': 3.0,
                'rating': 4.0,
                'popularity_score': 70,
                'opening_hours': '10:00-22:00',
                'best_time_to_visit': 'Afternoon',
                'latitude': -7.9667,
                'longitude': 112.6333,
            },
            {
                'name': 'Warung Rawon Setan',
                'category': 'Food',
                'description': 'Famous local restaurant serving traditional Rawon (black beef soup), a must-try Malang specialty.',
                'address': 'Jl. Arjuno, Malang',
                'average_cost': 35000,
                'estimated_duration_hours': 1.0,
                'rating': 4.6,
                'popularity_score': 80,
                'opening_hours': '19:00-02:00',
                'best_time_to_visit': 'Evening',
                'latitude': -7.9667,
                'longitude': 112.6167,
            },
            {
                'name': 'Mount Bromo Sunrise Tour',
                'category': 'Adventure',
                'description': 'Early morning tour to witness the spectacular sunrise over Mount Bromo volcano.',
                'address': 'Bromo Tengger Semeru National Park',
                'average_cost': 350000,
                'estimated_duration_hours': 12.0,
                'rating': 4.8,
                'popularity_score': 100,
                'opening_hours': '03:00-12:00',
                'best_time_to_visit': 'Early Morning',
                'latitude': -7.9425,
                'longitude': 112.9531,
            },
            {
                'name': 'Museum Malang Tempo Doeloe',
                'category': 'History',
                'description': 'Historical museum showcasing Malang\'s past with vintage collections and cultural artifacts.',
                'address': 'Jl. Gajayana, Malang',
                'average_cost': 20000,
                'estimated_duration_hours': 2.0,
                'rating': 4.2,
                'popularity_score': 65,
                'opening_hours': '08:00-15:00',
                'best_time_to_visit': 'Morning',
                'latitude': -7.9667,
                'longitude': 112.6167,
            },
        ]

        for dest_data in destinations_data:
            category = DestinationCategory.objects.get(name=dest_data['category'])
            dest, created = Destination.objects.get_or_create(
                name=dest_data['name'],
                city=malang,
                defaults={
                    'category': category,
                    'description': dest_data['description'],
                    'address': dest_data['address'],
                    'average_cost': dest_data['average_cost'],
                    'estimated_duration_hours': dest_data['estimated_duration_hours'],
                    'rating': dest_data['rating'],
                    'popularity_score': dest_data['popularity_score'],
                    'opening_hours': dest_data['opening_hours'],
                    'best_time_to_visit': dest_data['best_time_to_visit'],
                    'latitude': dest_data.get('latitude'),
                    'longitude': dest_data.get('longitude'),
                }
            )
            if created:
                self.stdout.write(f'Created destination: {dest.name}')

        # Create a sample admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@funtasticbros.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(f'Created admin user: {admin_user.username}')

        # Create sample regular users
        sample_users = [
            ('tourist1', 'tourist1@example.com', 'Tourist', 'One', 'user'),
            ('guide1', 'guide1@example.com', 'Local', 'Guide', 'guider'),
            ('guide2', 'guide2@example.com', 'Expert', 'Guide', 'guider'),
        ]

        for username, email, first_name, last_name, role in sample_users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    role=role
                )
                self.stdout.write(f'Created user: {user.username} ({role})')

                # Create guide profiles for guide users
                if role == 'guider':
                    nature_category = DestinationCategory.objects.get(name='Nature')
                    culture_category = DestinationCategory.objects.get(name='Culture')
                    indonesian = Language.objects.get(name='Indonesian')
                    english = Language.objects.get(name='English')
                    friendly_trait = PersonalityTrait.objects.get(name='Friendly')
                    expert_trait = PersonalityTrait.objects.get(name='Local Expert')

                    guide_profile = TourGuide.objects.create(
                        user=user,
                        bio=f'Experienced local guide with {5 if username == "guide1" else 8} years of experience in Malang tourism.',
                        phone='+62812345678',
                        years_of_experience=5 if username == "guide1" else 8,
                        hourly_rate=100000 if username == "guide1" else 150000,
                        daily_rate=800000 if username == "guide1" else 1200000,
                        average_rating=4.5 if username == "guide1" else 4.8,
                        total_reviews=23 if username == "guide1" else 47,
                        total_tours=89 if username == "guide1" else 156,
                        is_verified=True,
                        is_available=True,
                    )
                    
                    guide_profile.specialties.add(nature_category, culture_category)
                    guide_profile.languages.add(indonesian, english)
                    guide_profile.personality_traits.add(friendly_trait, expert_trait)
                    guide_profile.cities.add(malang)
                    
                    self.stdout.write(f'Created guide profile for: {user.username}')

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully populated database with sample data!\n'
                'You can now:\n'
                '- Login as admin/admin123 to access admin panel\n'
                '- Login as tourist1/password123 to test tourist features\n'
                '- Login as guide1/password123 to test guide features\n'
                '- Generate AI itineraries for Malang city\n'
                '- Browse and book local guides'
            )
        )
