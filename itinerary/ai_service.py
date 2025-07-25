import json
import pandas as pd
import os
from django.conf import settings
from typing import Dict, List, Any
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from openai import OpenAI
from destinations.models import Destination, City

logger = logging.getLogger(__name__)

class AIItineraryService:
    def __init__(self):
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.api_available = True
        else:
            logger.warning("OpenAI API key not configured. AI features will not work.")
            self.client = None
            self.api_available = False
        
        # Initialize RAG components
        self.destinations_data = None
        self.tfidf_vectorizer = None
        self.destination_vectors = None
        self._load_destinations_data()

    def _load_destinations_data(self):
        """Load and process tourism dataset from Django database for RAG"""
        try:
            # Load from Django database instead of CSV
            destinations = Destination.objects.filter(is_active=True).select_related('city', 'category')
            
            if destinations.exists():
                # Convert to pandas DataFrame for easier processing
                data = []
                for dest in destinations:
                    data.append({
                        'Place_Id': dest.id,
                        'Place_Name': dest.name,
                        'Description': dest.description,
                        'Category': dest.category.name,
                        'City': dest.city.name,
                        'Price': float(dest.average_cost),
                        'Rating': float(dest.rating),
                        'Time_Minutes': float(dest.estimated_duration_hours * 60),
                        'Lat': float(dest.latitude) if dest.latitude else None,
                        'Long': float(dest.longitude) if dest.longitude else None,
                    })
                
                self.destinations_data = pd.DataFrame(data)
                self._prepare_rag_vectors()
                logger.info(f"Loaded {len(self.destinations_data)} destinations for RAG")
            else:
                logger.warning("No destinations found in database. RAG functionality will be limited.")
        except Exception as e:
            logger.error(f"Failed to load destinations from database: {str(e)}")

    def _prepare_rag_vectors(self):
        """Prepare TF-IDF vectors for destination similarity search"""
        if self.destinations_data is not None:
            try:
                # Combine relevant text fields for vectorization
                text_features = []
                for _, row in self.destinations_data.iterrows():
                    combined_text = f"{row.get('Place_Name', '')} {row.get('Description', '')} {row.get('Category', '')} {row.get('City', '')}"
                    text_features.append(combined_text)
                
                # Create TF-IDF vectors
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                self.destination_vectors = self.tfidf_vectorizer.fit_transform(text_features)
            except Exception as e:
                logger.error(f"Failed to prepare RAG vectors: {str(e)}")

    def retrieve_relevant_destinations(self, city: str, interests: List[str], budget_range: str, max_results: int = 20) -> List[Dict]:
        """Use RAG to retrieve most relevant destinations based on user preferences"""
        if self.destinations_data is None:
            return []

        try:
            # Filter by city first
            city_destinations = self.destinations_data[
                self.destinations_data['City'].str.lower() == city.lower()
            ].copy()

            if city_destinations.empty:
                logger.warning(f"No destinations found for city: {city}")
                return []

            # Create query from user interests
            query = " ".join(interests)
            
            # Get TF-IDF vector for the query
            if self.tfidf_vectorizer:
                query_vector = self.tfidf_vectorizer.transform([query])
                
                # Get indices for city destinations
                city_indices = city_destinations.index.tolist()
                
                # Calculate similarity scores for city destinations only
                city_vectors = self.destination_vectors[city_indices]
                similarity_scores = cosine_similarity(query_vector, city_vectors).flatten()
                
                # Add similarity scores to dataframe
                city_destinations.loc[:, 'similarity_score'] = similarity_scores
            else:
                # Fallback: random scoring
                city_destinations.loc[:, 'similarity_score'] = np.random.random(len(city_destinations))

            # Apply budget filtering
            budget_filters = {
                'budget': city_destinations['Price'] <= 50000,
                'mid-range': (city_destinations['Price'] > 50000) & (city_destinations['Price'] <= 200000),
                'luxury': city_destinations['Price'] > 200000
            }
            
            if budget_range in budget_filters:
                city_destinations = city_destinations[budget_filters[budget_range]]

            # Sort by similarity and rating
            city_destinations['combined_score'] = (
                city_destinations['similarity_score'] * 0.7 + 
                (city_destinations['Rating'] / 5.0) * 0.3
            )
            
            top_destinations = city_destinations.nlargest(max_results, 'combined_score')
            
            # Convert to list of dictionaries
            result = []
            for _, row in top_destinations.iterrows():
                result.append({
                    'id': row.get('Place_Id'),
                    'name': row.get('Place_Name', ''),
                    'description': row.get('Description', ''),
                    'category': row.get('Category', ''),
                    'city': row.get('City', ''),
                    'price': row.get('Price', 0),
                    'rating': row.get('Rating', 0),
                    'time_minutes': row.get('Time_Minutes', 120),
                    'lat': row.get('Lat'),
                    'lng': row.get('Long'),
                    'similarity_score': row['similarity_score']
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving relevant destinations: {str(e)}")
            return []

    def generate_itinerary(self, 
                          city: str, 
                          interests: List[str], 
                          budget_range: str, 
                          duration_days: int,
                          travel_style: str = "relaxed",
                          additional_preferences: str = "",
                          available_destinations: List[Dict] = None) -> Dict[str, Any]:
        """Generate a personalized itinerary using AI with RAG"""
        
        if not self.api_available:
            return self._generate_fallback_itinerary(city, interests, budget_range, duration_days, travel_style)
        
        try:
            # Use RAG to get relevant destinations
            relevant_destinations = self.retrieve_relevant_destinations(
                city, interests, budget_range, max_results=30
            )
            
            if not relevant_destinations:
                logger.warning(f"No relevant destinations found for {city}")
                relevant_destinations = available_destinations or []
            
            # Dynamic token scaling based on duration
            if travel_style in ['packed', 'action-packed']:
                max_tokens = min(4000, 300 + (duration_days * 200))
            else:
                max_tokens = min(3500, 250 + (duration_days * 150))
            
            # Create the enhanced prompt with RAG data
            prompt = self._create_enhanced_itinerary_prompt(
                city, interests, budget_range, duration_days, 
                travel_style, additional_preferences, relevant_destinations
            )
            
            # Call OpenAI API with updated parameters
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            structured_itinerary = self._parse_ai_response(ai_response, duration_days)
            
            return {
                'success': True,
                'itinerary': structured_itinerary,
                'ai_response_raw': ai_response,
                'prompt_used': prompt,  # Add this missing key
                'destinations_used': relevant_destinations,
                'rag_enabled': True,
                'practical_info': structured_itinerary.get('practical_info', {})
            }
            
        except Exception as e:
            logger.error(f"AI itinerary generation failed: {str(e)}")
            return self._generate_fallback_itinerary(city, interests, budget_range, duration_days, travel_style)

    def _get_system_prompt(self) -> str:
        """Enhanced system prompt for better AI responses"""
        return """You are an expert Indonesian travel planner with deep knowledge of local culture, transportation, and hidden gems. 

Your expertise includes:
- Optimal timing and routing between destinations
- Local cultural etiquette and customs
- Budget-conscious recommendations
- Weather considerations
- Local food specialties and dining recommendations
- Transportation options (Grab, ojek, bus, walking)
- Insider tips for better experiences

Create detailed, practical itineraries that feel authentic and are actually feasible to execute. Include specific timing, costs in Indonesian Rupiah, and local insights.

CRITICAL: Always return valid JSON format wrapped in ```json``` code blocks."""

    def _create_enhanced_itinerary_prompt(self, city: str, interests: List[str], 
                                        budget_range: str, duration_days: int,
                                        travel_style: str, additional_preferences: str,
                                        destinations: List[Dict]) -> str:
        """Create an enhanced prompt with RAG data"""
        
        budget_info = {
            'budget': 'under 500,000 IDR per day (local warungs, public transport, budget activities)',
            'mid-range': '500,000 - 1,500,000 IDR per day (nice restaurants, comfortable transport, paid attractions)', 
            'luxury': 'over 1,500,000 IDR per day (premium restaurants, private transport, exclusive experiences)'
        }
        
        style_info = {
            'relaxed': '2-3 main activities per day with plenty of rest time and leisurely meals',
            'balanced': '3-4 activities per day with moderate pacing and some rest periods',
            'packed': '4-6 activities per day to maximize experiences and see as much as possible',
            'action-packed': '5-7 activities per day for maximum adventure and experiences'
        }
        
        # Format destinations for the prompt
        destinations_text = self._format_destinations_for_ai(destinations)
        
        prompt = f"""
Create a detailed {duration_days}-day travel itinerary for {city}, Indonesia.

TRAVELER PROFILE:
- Interests: {', '.join(interests)}
- Budget: {budget_info.get(budget_range, budget_range)}
- Travel Style: {style_info.get(travel_style, travel_style)}
- Duration: {duration_days} days
- Additional Preferences: {additional_preferences or 'None specified'}

AVAILABLE DESTINATIONS (prioritized by relevance):
{destinations_text}

REQUIREMENTS:
1. **Day-by-Day Structure**: Create a detailed schedule for each day
2. **Timing**: Include specific times (e.g., "9:00 AM - 11:00 AM")
3. **Transportation**: Specify how to get between locations with estimated times and costs
4. **Budget Breakdown**: Provide cost estimates for each activity, meal, and transport
5. **Local Insights**: Include cultural tips, best times to visit, local etiquette
6. **Meals**: Recommend specific local dishes and restaurants matching the budget
7. **Practical Tips**: Weather considerations, what to bring, booking requirements

FORMAT YOUR RESPONSE AS VALID JSON:
```json
{{
  "title": "Custom Itinerary Title",
  "total_estimated_cost": "IDR amount range",
  "overview": "Brief overview of the trip",
  "days": [
    {{
      "day": 1,
      "theme": "Day theme",
      "activities": [
        {{
          "time": "9:00 AM - 11:00 AM",
          "activity": "Activity name",
          "location": "Location name",
          "description": "Detailed description",
          "cost": "IDR amount",
          "tips": "Local tips"
        }}
      ],
      "meals": [
        {{
          "time": "12:00 PM",
          "type": "Lunch",
          "restaurant": "Restaurant name",
          "recommended_dishes": ["dish1", "dish2"],
          "cost": "IDR amount"
        }}
      ],
      "transportation": [
        {{
          "from": "Location A",
          "to": "Location B", 
          "method": "Grab/Ojek/Walking",
          "duration": "15 minutes",
          "cost": "IDR amount"
        }}
      ],
      "daily_total": "IDR amount"
    }}
  ]
}}
```

Make this itinerary authentic, practical, and perfectly suited to the traveler's preferences!
"""
        return prompt

    def _format_destinations_for_ai(self, destinations: List[Dict]) -> str:
        """Format destination data for AI prompt"""
        if not destinations:
            return "No specific destinations available."
            
        formatted = []
        for dest in destinations[:20]:  # Limit to top 20 for token efficiency
            similarity_info = f" (Relevance: {dest.get('similarity_score', 0):.2f})" if 'similarity_score' in dest else ""
            formatted.append(f"""
- {dest['name']} ({dest.get('category', 'Unknown')}){similarity_info}
  Price: {dest.get('price', 0)} IDR | Rating: {dest.get('rating', 0)}/5
  Time needed: {dest.get('time_minutes', 120)} minutes
  Description: {dest.get('description', '')[:150]}...
""")
        return '\n'.join(formatted)

    def _parse_ai_response(self, ai_response: str, duration_days: int) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            # Try to extract JSON from response
            json_start = ai_response.find('```json')
            if json_start != -1:
                json_start = ai_response.find('{', json_start)
                json_end = ai_response.rfind('}')
                if json_end != -1:
                    json_str = ai_response[json_start:json_end + 1]
                    parsed = json.loads(json_str)
                    return parsed
            
            # Fallback: look for any JSON-like structure
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                parsed = json.loads(json_str)
                return parsed
                
            # If no JSON found, create fallback structure
            logger.warning("Could not parse AI response as JSON, creating fallback")
            return self._create_fallback_structure(duration_days, ai_response)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return self._create_fallback_structure(duration_days, ai_response)
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return self._create_fallback_structure(duration_days, ai_response)

    def _create_fallback_structure(self, duration_days: int, ai_response: str = "") -> Dict[str, Any]:
        """Create a fallback itinerary structure when AI parsing fails"""
        days = []
        for day in range(1, duration_days + 1):
            days.append({
                "day": day,
                "theme": f"Day {day} Exploration",
                "activities": [
                    {
                        "time": "9:00 AM - 12:00 PM",
                        "activity": "Morning Exploration",
                        "location": "City Center",
                        "description": "Explore local attractions and landmarks",
                        "cost": "IDR 100,000",
                        "tips": "Start early to avoid crowds"
                    },
                    {
                        "time": "2:00 PM - 5:00 PM", 
                        "activity": "Afternoon Activities",
                        "location": "Popular Area",
                        "description": "Visit museums, parks, or cultural sites",
                        "cost": "IDR 150,000",
                        "tips": "Check opening hours in advance"
                    }
                ],
                "meals": [
                    {
                        "time": "12:00 PM",
                        "type": "Lunch",
                        "restaurant": "Local Restaurant",
                        "recommended_dishes": ["Local Specialty", "Traditional Dish"],
                        "cost": "IDR 75,000"
                    }
                ],
                "transportation": [
                    {
                        "from": "Hotel",
                        "to": "City Center",
                        "method": "Grab",
                        "duration": "15 minutes",
                        "cost": "IDR 25,000"
                    }
                ],
                "daily_total": "IDR 350,000"
            })
        
        return {
            "title": f"{duration_days}-Day Adventure",
            "total_estimated_cost": f"IDR {350000 * duration_days:,}",
            "overview": "A curated itinerary for your trip",
            "days": days
        }

    def match_guide_to_itinerary(self, itinerary_data: Dict, available_guides: List[Dict]) -> List[Dict]:
        """
        Use AI to match tour guides to an itinerary based on compatibility
        
        Args:
            itinerary_data: Dict containing itinerary preferences
            available_guides: List of guide data dicts
            
        Returns:
            List of matched guides with compatibility scores
        """
        try:
            if not self.api_available or not available_guides:
                return self._fallback_guide_matching(itinerary_data, available_guides)
            
            # Prepare prompt for guide matching
            prompt = f"""
            Based on the following travel itinerary preferences, rank and match the best tour guides.
            
            ITINERARY DETAILS:
            - Interests: {', '.join(itinerary_data.get('interests', []))}
            - Budget Range: {itinerary_data.get('budget_range', 'Not specified')}
            - Duration: {itinerary_data.get('duration_days', 'Not specified')} days
            
            AVAILABLE GUIDES:
            """
            
            for i, guide in enumerate(available_guides):
                prompt += f"""
            {i+1}. {guide['name']}
               - Experience: {guide['years_of_experience']} years
               - Specialties: {', '.join(guide.get('specialties', []))}
               - Languages: {', '.join(guide.get('languages', []))}
               - Personality: {', '.join(guide.get('personality_traits', []))}
               - Hourly Rate: Rp {guide['hourly_rate']:,.0f}
               - Daily Rate: Rp {guide['daily_rate']:,.0f}
               - Rating: {guide['average_rating']}/5.0 ({guide['total_reviews']} reviews)
               - Bio: {guide.get('bio', 'No bio available')[:200]}...
                """
            
            prompt += """
            
            Please analyze each guide and provide:
            1. Compatibility score (0-100) based on how well they match the itinerary
            2. Specific reasons for the match
            3. Rank them by compatibility
            
            Respond with a JSON array of the top 5 guides, ordered by compatibility score:
            [
                {
                    "id": guide_id,
                    "name": "Guide Name",
                    "compatibility_score": 85,
                    "match_reasons": [
                        "Specializes in cultural tourism which matches your interests",
                        "Highly rated guide with excellent reviews",
                        "Speaks multiple languages for better communication"
                    ],
                    "recommended_for": "Cultural exploration and local insights",
                    "estimated_cost_per_day": 750000
                }
            ]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert travel consultant specializing in matching tourists with the perfect tour guides based on their preferences and travel style."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Find JSON array in response
                start_idx = ai_response.find('[')
                end_idx = ai_response.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = ai_response[start_idx:end_idx]
                    matched_guides = json.loads(json_str)
                    
                    # Validate and enhance the results
                    enhanced_matches = []
                    for match in matched_guides[:5]:  # Top 5 matches
                        guide_id = match.get('id')
                        guide_data = next((g for g in available_guides if g['id'] == guide_id), None)
                        
                        if guide_data:
                            enhanced_match = {
                                'id': guide_id,
                                'name': match.get('name', guide_data['name']),
                                'compatibility_score': min(100, max(0, match.get('compatibility_score', 50))),
                                'match_reasons': match.get('match_reasons', ['General compatibility']),
                                'recommended_for': match.get('recommended_for', 'Tour guidance'),
                                'estimated_cost_per_day': match.get('estimated_cost_per_day', guide_data['daily_rate']),
                                'guide_data': guide_data
                            }
                            enhanced_matches.append(enhanced_match)
                    
                    return enhanced_matches
                    
            except json.JSONDecodeError:
                logger.warning("Could not parse AI response as JSON, using fallback matching")
                
        except Exception as e:
            logger.error(f"Error in AI guide matching: {str(e)}")
        
        # Fallback to rule-based matching
        return self._fallback_guide_matching(itinerary_data, available_guides)
    
    def _fallback_guide_matching(self, itinerary_data: Dict, available_guides: List[Dict]) -> List[Dict]:
        """
        Rule-based fallback for guide matching when AI is not available
        """
        try:
            matched_guides = []
            interests = set(itinerary_data.get('interests', []))
            budget_range = itinerary_data.get('budget_range', 'mid-range')
            
            for guide in available_guides:
                # Calculate compatibility score based on rules
                score = 0
                reasons = []
                
                # Interest matching (40% of score)
                guide_specialties = set(guide.get('specialties', []))
                interest_overlap = len(interests.intersection(guide_specialties))
                if interest_overlap > 0:
                    score += 40 * (interest_overlap / max(len(interests), 1))
                    reasons.append(f"Specializes in {interest_overlap} of your interest areas")
                
                # Rating quality (30% of score)
                rating_score = (guide.get('average_rating', 0) / 5.0) * 30
                score += rating_score
                if guide.get('average_rating', 0) >= 4.0:
                    reasons.append(f"Highly rated ({guide['average_rating']}/5.0)")
                
                # Experience factor (20% of score)
                experience_years = guide.get('years_of_experience', 0)
                experience_score = min(20, experience_years * 2)
                score += experience_score
                if experience_years >= 3:
                    reasons.append(f"Experienced guide with {experience_years} years")
                
                # Budget compatibility (10% of score)
                daily_rate = guide.get('daily_rate', 0)
                budget_score = 10
                if budget_range == 'budget' and daily_rate <= 500000:
                    budget_score = 10
                    reasons.append("Budget-friendly rates")
                elif budget_range == 'mid-range' and 500000 <= daily_rate <= 1500000:
                    budget_score = 10
                    reasons.append("Reasonable rates for mid-range budget")
                elif budget_range == 'luxury' and daily_rate >= 1000000:
                    budget_score = 10
                    reasons.append("Premium service provider")
                else:
                    budget_score = 5
                
                score += budget_score
                
                # Create match result
                match_result = {
                    'id': guide['id'],
                    'name': guide['name'],
                    'compatibility_score': round(score, 1),
                    'match_reasons': reasons if reasons else ['Available in your destination'],
                    'recommended_for': 'Local guidance and tour assistance',
                    'estimated_cost_per_day': daily_rate,
                    'guide_data': guide
                }
                
                matched_guides.append(match_result)
            
            # Sort by compatibility score
            matched_guides.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            return matched_guides[:5]  # Return top 5 matches
            
        except Exception as e:
            logger.error(f"Error in fallback guide matching: {str(e)}")
            return []

    def _generate_fallback_itinerary(self, city: str, interests: List[str], 
                                   budget_range: str, duration_days: int,
                                   travel_style: str = 'balanced',
                                   additional_preferences: str = "") -> Dict[str, Any]:
        """Generate a fallback itinerary using real destinations from database"""
        
        try:
            # Get relevant destinations using RAG
            relevant_destinations = self.retrieve_relevant_destinations(
                city, interests, budget_range, max_results=20
            )
            
            if not relevant_destinations:
                logger.warning(f"No destinations found for {city}, using generic fallback")
                return self._create_generic_fallback(city, duration_days, budget_range)
            
            # Travel style activity mapping
            activity_counts = {
                'relaxed': 3,
                'balanced': 4,
                'packed': 5,
                'action-packed': 6
            }
            
            activities_per_day = activity_counts.get(travel_style, 3)
            
            budget_amounts = {
                'budget': 300000,
                'mid-range': 800000,
                'luxury': 1500000
            }
            
            daily_budget = budget_amounts.get(budget_range, 500000)
            
            # Create days with real destinations
            days = []
            destination_index = 0
            
            for day_num in range(1, duration_days + 1):
                day_activities = []
                day_cost = 0
                
                # Generate activities for this day
                for activity_num in range(activities_per_day):
                    if destination_index < len(relevant_destinations):
                        dest = relevant_destinations[destination_index]
                        
                        # Calculate time slots
                        start_hour = 9 + (activity_num * 2)
                        end_hour = start_hour + 2
                        
                        activity = {
                            "time": f"{start_hour:02d}:00 - {end_hour:02d}:00",
                            "activity": f"Visit {dest['name']}",
                            "location": dest['name'],
                            "description": dest['description'][:100] + "..." if len(dest['description']) > 100 else dest['description'],
                            "cost": f"IDR {int(dest['price']):,}",
                            "tips": f"Rated {dest['rating']}/5 stars. Duration: {int(dest['time_minutes'])} minutes."
                        }
                        
                        day_activities.append(activity)
                        day_cost += dest['price']
                        destination_index += 1
                    else:
                        # Recycle destinations if we run out
                        destination_index = 0
                        if relevant_destinations:  # Check if we have any destinations
                            dest = relevant_destinations[destination_index]
                            start_hour = 9 + (activity_num * 2)
                            end_hour = start_hour + 2
                            
                            activity = {
                                "time": f"{start_hour:02d}:00 - {end_hour:02d}:00",
                                "activity": f"Revisit {dest['name']}",
                                "location": dest['name'],
                                "description": "Explore different aspects or nearby areas",
                                "cost": f"IDR {int(dest['price'] * 0.5):,}",  # Half price for revisit
                                "tips": "Take time to discover hidden details you missed before."
                            }
                            day_activities.append(activity)
                            day_cost += dest['price'] * 0.5
                            destination_index += 1
                
                # Add meals
                meals = [
                    {
                        "time": "12:00 PM",
                        "type": "Lunch",
                        "restaurant": f"Local Restaurant in {city}",
                        "recommended_dishes": ["Local Specialty", "Traditional Dish"],
                        "cost": f"IDR {int(daily_budget * 0.15):,}"
                    }
                ]
                
                # Add transportation
                transportation = [
                    {
                        "from": "Hotel",
                        "to": "Destination Area",
                        "method": "Grab/Taxi",
                        "duration": "15-30 minutes",
                        "cost": f"IDR {int(daily_budget * 0.1):,}"
                    }
                ]
                
                day = {
                    "day": day_num,
                    "theme": f"Day {day_num} - {travel_style.title()} Exploration",
                    "activities": day_activities,
                    "meals": meals,
                    "transportation": transportation,
                    "daily_total": f"IDR {int(day_cost + (daily_budget * 0.25)):,}"  # Activities + meals + transport
                }
                
                days.append(day)
            
            total_cost = daily_budget * duration_days
            
            itinerary = {
                "title": f"{duration_days}-Day {city} Adventure ({travel_style.title()} Style)",
                "total_estimated_cost": f"IDR {int(total_cost):,}",
                "overview": f"A {travel_style} {duration_days}-day itinerary featuring {len(relevant_destinations)} destinations in {city}",
                "days": days
            }
            
            return {
                'success': True,
                'itinerary': itinerary,
                'ai_response_raw': f"Fallback itinerary generated using {len(relevant_destinations)} real destinations",
                'prompt_used': f"Fallback generation for {city} with {', '.join(interests)} interests",
                'rag_enabled': True,
                'destinations_used': relevant_destinations
            }
            
        except Exception as e:
            logger.error(f"Error generating fallback itinerary: {str(e)}")
            return self._create_generic_fallback(city, duration_days, budget_range)

    def _create_generic_fallback(self, city: str, duration_days: int, budget_range: str) -> Dict[str, Any]:
        """Create a generic fallback when no destinations are available"""
        budget_amounts = {
            'budget': 300000,
            'mid-range': 800000,
            'luxury': 1500000
        }
        
        daily_budget = budget_amounts.get(budget_range, 500000)
        
        fallback_itinerary = self._create_fallback_structure(duration_days)
        fallback_itinerary['title'] = f"{duration_days}-Day {city} Itinerary"
        fallback_itinerary['total_estimated_cost'] = f"IDR {daily_budget * duration_days:,}"
        
        # Update daily costs based on budget
        for day in fallback_itinerary['days']:
            day['daily_total'] = f"IDR {daily_budget:,}"
        
        return {
            'success': True,
            'itinerary': fallback_itinerary,
            'ai_response_raw': f"Generic fallback itinerary generated for {city}",
            'prompt_used': f"Generic fallback for {city}",
            'rag_enabled': False,
            'destinations_used': []
        }
