# Funtastic Bros - AI-Powered Indonesian Travel Itinerary & Tour Guide Matching App

A comprehensive MVP for an Indonesia-focused travel platform that uses AI to generate personalized itineraries and connects tourists with local tour guides.

## 🎉 LATEST UPDATE: Enhanced AI-Powered Itinerary Creation

Your app now features a **comprehensive 6-step itinerary creation interface** with:

### ✨ New Features Just Added:
- **🇮🇩 Indonesian Cities**: 7 major destinations (Jakarta, Bali, Yogyakarta, Bandung, Surabaya, Malang, Semarang)
- **🤖 RAG Technology**: AI service ready for ChatGPT integration with Indonesian tourism data
- **🎯 Smart Personalization**: 18 interest categories, budget ranges, travel styles
- **📱 Beautiful UI**: Indonesian flag-inspired design with interactive elements
- **⚡ Navigation Fixed**: "Make Itinerary" button now works perfectly

### 🚀 Ready to Test:
Visit **http://127.0.0.1:8000/itinerary/create/** to experience the enhanced creation flow!

---

## 🚀 Features

### ✅ Core MVP Features Implemented

#### 1. AI-Powered Custom Itinerary Generator
- **User Input**: City, interests, budget range, duration
- **AI Generation**: Personalized day-by-day itineraries using OpenAI GPT
- **Smart Recommendations**: Time-optimized schedules with cost estimates
- **Fallback System**: Works without AI API for development/testing

#### 2. Tour Guide Matching System
- **Guide Profiles**: Bio, specialties, languages, personality traits, pricing
- **AI Matching**: Intelligent guide recommendations based on itinerary
- **Filtering**: By city, specialty, language, ratings
- **Booking System**: Basic booking request functionality

#### 3. User Management
- **Dual Roles**: Tourists and Tour Guides
- **Authentication**: Login, registration, profile management
- **Guide Registration**: Easy transition from tourist to guide

#### 4. Destination Database
- **Curated Content**: Pre-populated Malang city attractions
- **Categories**: Nature, History, Culture, Food, Shopping, etc.
- **Rich Data**: Costs, duration, ratings, coordinates, hours

## 🛠️ Technology Stack

- **Backend**: Django 5.2.4, Python 3.13
- **Database**: SQLite (development), PostgreSQL ready
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **AI**: OpenAI GPT-3.5-turbo for itinerary generation
- **Authentication**: Django built-in auth with custom user model

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Git

### 1. Clone the Repository
```bash
git clone <repository-url>
cd funtastic-bros
```

### 2. Set Up Virtual Environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key-here
DEFAULT_CITY=Malang
```

### 5. Database Setup
```bash
python manage.py migrate
python manage.py populate_sample_data
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## 🎯 Sample Accounts

The `populate_sample_data` command creates these test accounts:

- **Admin**: `admin` / `admin123`
- **Tourist**: `tourist1` / `password123`
- **Guide 1**: `guide1` / `password123`
- **Guide 2**: `guide2` / `password123`

## 🗺️ Application Structure

```
funtastic-bros/
├── authentication/          # User management
├── destinations/           # Tourist destinations
├── guides/                # Tour guide management
├── itinerary/             # AI itinerary generation
├── templates/             # HTML templates
├── static/               # CSS, JS, images
├── manage.py
└── requirements.txt
```

## 🧪 Testing the MVP

### 1. Generate AI Itinerary
1. Visit homepage at `http://localhost:8000`
2. Login as `tourist1`
3. Fill out the itinerary form:
   - City: Malang
   - Interests: Select any (Nature, Culture, Food, etc.)
   - Budget: Any range
   - Duration: 3-5 days
4. Click "Generate My AI Itinerary"

### 2. Browse Tour Guides
1. Navigate to "Find Guides"
2. View guide profiles with ratings and specialties
3. Use filters to find specific guide types

### 3. Guide Features
1. Login as `guide1`
2. Access "Guide Profile" from user menu
3. Edit profile, availability, and specialties
4. View booking requests

### 4. Admin Panel
1. Login as `admin` at `http://localhost:8000/admin/`
2. Manage destinations, guides, and itineraries
3. Add new cities and attractions

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern Interface**: Clean Tailwind CSS styling
- **Interactive Elements**: Hover effects, smooth transitions
- **Accessibility**: Focus styles, screen reader support
- **User Feedback**: Success/error messages, loading states

## 🤖 AI Integration

### OpenAI Configuration
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env` file: `OPENAI_API_KEY=your-key-here`
3. AI generates structured itineraries with:
   - Day-by-day schedules
   - Activity timing and costs
   - Location-specific recommendations
   - Budget-appropriate suggestions

### Fallback System
- Works without OpenAI API
- Uses algorithm-based destination matching
- Maintains full functionality for testing

## 📱 API Endpoints

### Core URLs
- `/` - Homepage with itinerary generator
- `/generate/` - AI itinerary generation
- `/explore/` - Browse public itineraries
- `/guides/` - Tour guide directory
- `/destinations/` - Attraction listings
- `/auth/login/` - User authentication

### API Features
- AJAX itinerary saving
- Guide matching algorithms
- Real-time search and filtering

## 🚧 Future Enhancements

### Phase 2 Features
- [ ] Payment integration (Stripe/PayPal)
- [ ] Real-time chat between tourists and guides
- [ ] Google Maps integration with routes
- [ ] Multi-language support (Bahasa Indonesia)
- [ ] Mobile app (React Native/Flutter)
- [ ] Review and rating system
- [ ] Social features (sharing, following)

### Technical Improvements
- [ ] Redis caching for performance
- [ ] Celery for background tasks
- [ ] Docker containerization
- [ ] AWS/GCP deployment
- [ ] API documentation (Swagger)
- [ ] Unit and integration tests

## 🏙️ Expanding Beyond Malang

Currently focused on Malang for MVP. To add new cities:

1. Use admin panel to add City
2. Add DestinationCategory entries
3. Populate Destination data
4. Update guide profiles for new cities

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the Django logs in the terminal
2. Verify `.env` configuration
3. Ensure database migrations are applied
4. Test with sample data

## 🎉 MVP Success Criteria

✅ **Completed Goals:**
- AI-powered itinerary generation
- Tour guide matching system  
- User authentication and profiles
- Responsive web interface
- Admin management system
- Sample data for testing
- Malang city focus with 8+ destinations
- Basic booking workflow

The MVP successfully demonstrates all core features outlined in the original requirements and provides a solid foundation for scaling to multiple Indonesian cities.