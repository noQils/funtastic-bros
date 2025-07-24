import openai
import json
from django.conf import settings
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class AIItineraryService:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured. AI features will not work.")

    def generate_itinerary(self, 
                          city: str, 
                          interests: List[str], 
                          budget_range: str, 
                          duration_days: int,
                          available_destinations: List[Dict]) -> Dict[str, Any]:
        """
        Generate a personalized itinerary using AI
        
        Args:
            city: Name of the city to visit
            interests: List of user interests (e.g., ['nature', 'history', 'food'])
            budget_range: 'budget', 'mid-range', or 'luxury'
            duration_days: Number of days for the trip
            available_destinations: List of destination data from database
            
        Returns:
            Dict containing structured itinerary data
        """
        
        if not settings.OPENAI_API_KEY:
            return self._generate_fallback_itinerary(city, interests, budget_range, duration_days, available_destinations)
        
        try:
            # Prepare destinations data for AI
            destinations_text = self._format_destinations_for_ai(available_destinations)
            
            # Create the prompt
            prompt = self._create_itinerary_prompt(city, interests, budget_range, duration_days, destinations_text)
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional travel planner specializing in Indonesian tourism. Create detailed, practical itineraries with accurate timing and costs."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            structured_itinerary = self._parse_ai_response(ai_response, duration_days)
            
            return {
                'success': True,
                'itinerary': structured_itinerary,
                'ai_response_raw': ai_response,
                'prompt_used': prompt
            }
            
        except Exception as e:
            logger.error(f"AI itinerary generation failed: {str(e)}")
            return self._generate_fallback_itinerary(city, interests, budget_range, duration_days, available_destinations)

    def _create_itinerary_prompt(self, city: str, interests: List[str], budget_range: str, duration_days: int, destinations_text: str) -> str:
        """Create a detailed prompt for AI itinerary generation"""
        
        budget_info = {
            'budget': 'under 500,000 IDR per day',
            'mid-range': '500,000 - 1,500,000 IDR per day', 
            'luxury': 'over 1,500,000 IDR per day'
        }
        
        prompt = f"""
Create a detailed {duration_days}-day travel itinerary for {city}, Indonesia.

TRAVELER PREFERENCES:
- Interests: {', '.join(interests)}
- Budget: {budget_info.get(budget_range, budget_range)}
- Duration: {duration_days} days

AVAILABLE DESTINATIONS:
{destinations_text}

REQUIREMENTS:
1. Create a day-by-day schedule with specific times
2. Include only destinations from the provided list
3. Add meal suggestions and transportation between locations
4. Estimate costs in Indonesian Rupiah (IDR)
5. Consider travel time between locations
6. Match activities to the traveler's interests
7. Stay within the specified budget range

FORMAT YOUR RESPONSE AS JSON:
{{
    "title": "Descriptive itinerary title",
    "total_estimated_cost": 0,
    "daily_cost": 0,
    "days": [
        {{
            "day_number": 1,
            "title": "Day 1: Theme",
            "activities": [
                {{
                    "time": "09:00",
                    "duration_minutes": 120,
                    "title": "Activity name",
                    "description": "Detailed description",
                    "type": "destination|meal|transport|rest",
                    "destination_name": "Name if visiting a destination",
                    "estimated_cost": 0,
                    "notes": "AI tips and suggestions"
                }}
            ]
        }}
    ]
}}

Provide practical, realistic timing and ensure the itinerary flows logically throughout each day.
"""
        return prompt

    def _format_destinations_for_ai(self, destinations: List[Dict]) -> str:
        """Format destination data for AI prompt"""
        formatted = []
        for dest in destinations:
            formatted.append(f"""
- {dest['name']} ({dest['category']})
  Location: {dest['address']}
  Cost: {dest['average_cost']} IDR
  Duration: {dest['estimated_duration_hours']} hours
  Best time: {dest['best_time_to_visit']}
  Hours: {dest['opening_hours']}
  Description: {dest['description'][:200]}...
""")
        return '\n'.join(formatted)

    def _parse_ai_response(self, ai_response: str, duration_days: int) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        try:
            # Extract JSON from AI response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
                
            json_str = ai_response[json_start:json_end]
            parsed = json.loads(json_str)
            
            # Validate structure
            if 'days' not in parsed or len(parsed['days']) != duration_days:
                raise ValueError("Invalid itinerary structure")
                
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return self._create_default_structure(duration_days)

    def _generate_fallback_itinerary(self, city: str, interests: List[str], budget_range: str, duration_days: int, available_destinations: List[Dict]) -> Dict[str, Any]:
        """Generate a basic itinerary without AI when API is unavailable"""
        
        # Simple algorithm to select destinations based on interests and budget
        filtered_destinations = []
        budget_limits = {'budget': 50000, 'mid-range': 150000, 'luxury': 500000}
        max_cost = budget_limits.get(budget_range, 100000)
        
        for dest in available_destinations:
            if dest['average_cost'] <= max_cost:
                # Simple scoring based on interest matching
                score = 0
                dest_text = f"{dest['name']} {dest['description']} {dest['category']}".lower()
                for interest in interests:
                    if interest.lower() in dest_text:
                        score += 1
                dest['interest_score'] = score
                filtered_destinations.append(dest)
        
        # Sort by interest score and rating
        filtered_destinations.sort(key=lambda x: (x['interest_score'], x['rating']), reverse=True)
        
        # Create basic itinerary structure
        itinerary = {
            'title': f"{duration_days}-Day {city} Adventure",
            'total_estimated_cost': 0,
            'daily_cost': 0,
            'days': []
        }
        
        destinations_per_day = max(2, len(filtered_destinations) // duration_days)
        dest_index = 0
        
        for day in range(1, duration_days + 1):
            day_activities = []
            day_cost = 0
            
            # Morning activity
            if dest_index < len(filtered_destinations):
                dest = filtered_destinations[dest_index]
                day_activities.append({
                    'time': '09:00',
                    'duration_minutes': int(dest['estimated_duration_hours'] * 60),
                    'title': f"Visit {dest['name']}",
                    'description': dest['description'],
                    'type': 'destination',
                    'destination_name': dest['name'],
                    'estimated_cost': dest['average_cost'],
                    'notes': f"Best time to visit: {dest['best_time_to_visit']}"
                })
                day_cost += dest['average_cost']
                dest_index += 1
            
            # Lunch
            lunch_cost = {'budget': 25000, 'mid-range': 75000, 'luxury': 150000}[budget_range]
            day_activities.append({
                'time': '12:00',
                'duration_minutes': 60,
                'title': 'Lunch Break',
                'description': 'Local restaurant meal',
                'type': 'meal',
                'destination_name': '',
                'estimated_cost': lunch_cost,
                'notes': 'Try local specialties'
            })
            day_cost += lunch_cost
            
            # Afternoon activity
            if dest_index < len(filtered_destinations):
                dest = filtered_destinations[dest_index]
                day_activities.append({
                    'time': '14:00',
                    'duration_minutes': int(dest['estimated_duration_hours'] * 60),
                    'title': f"Explore {dest['name']}",
                    'description': dest['description'],
                    'type': 'destination',
                    'destination_name': dest['name'],
                    'estimated_cost': dest['average_cost'],
                    'notes': f"Opening hours: {dest['opening_hours']}"
                })
                day_cost += dest['average_cost']
                dest_index += 1
            
            itinerary['days'].append({
                'day_number': day,
                'title': f'Day {day}: Exploring {city}',
                'activities': day_activities,
                'daily_cost': day_cost
            })
            itinerary['total_estimated_cost'] += day_cost
        
        itinerary['daily_cost'] = itinerary['total_estimated_cost'] / duration_days
        
        return {
            'success': True,
            'itinerary': itinerary,
            'ai_response_raw': 'Generated using fallback algorithm (AI unavailable)',
            'prompt_used': 'Fallback generation - no AI prompt used'
        }

    def _create_default_structure(self, duration_days: int) -> Dict[str, Any]:
        """Create default itinerary structure when parsing fails"""
        return {
            'title': f'{duration_days}-Day Travel Itinerary',
            'total_estimated_cost': 0,
            'daily_cost': 0,
            'days': [
                {
                    'day_number': i,
                    'title': f'Day {i}: Exploration',
                    'activities': [
                        {
                            'time': '09:00',
                            'duration_minutes': 180,
                            'title': 'Morning Activity',
                            'description': 'Explore local attractions',
                            'type': 'destination',
                            'destination_name': '',
                            'estimated_cost': 100000,
                            'notes': 'Plan your morning adventure'
                        }
                    ]
                } for i in range(1, duration_days + 1)
            ]
        }

    def match_guide_to_itinerary(self, itinerary_data: Dict, available_guides: List[Dict]) -> List[Dict]:
        """
        Match tour guides to an itinerary based on preferences and compatibility
        
        Args:
            itinerary_data: Itinerary information including interests and budget
            available_guides: List of available guide data
            
        Returns:
            List of matched guides with compatibility scores
        """
        
        matched_guides = []
        
        for guide in available_guides:
            score = self._calculate_guide_compatibility_score(itinerary_data, guide)
            if score > 0:
                guide_match = guide.copy()
                guide_match['compatibility_score'] = score
                guide_match['match_reasons'] = self._get_match_reasons(itinerary_data, guide)
                matched_guides.append(guide_match)
        
        # Sort by compatibility score
        matched_guides.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        return matched_guides[:10]  # Return top 10 matches

    def _calculate_guide_compatibility_score(self, itinerary: Dict, guide: Dict) -> float:
        """Calculate compatibility score between itinerary and guide"""
        score = 0.0
        
        # Base score for availability
        if guide.get('is_available', False):
            score += 20
        
        # Specialties matching (40 points max)
        itinerary_interests = itinerary.get('interests', [])
        guide_specialties = guide.get('specialties', [])
        
        for interest in itinerary_interests:
            for specialty in guide_specialties:
                if interest.lower() in specialty.lower():
                    score += 10
        
        # Budget compatibility (20 points max)
        budget_range = itinerary.get('budget_range', 'mid-range')
        guide_daily_rate = guide.get('daily_rate', 0)
        
        budget_limits = {
            'budget': (0, 200000),
            'mid-range': (200000, 600000),
            'luxury': (600000, float('inf'))
        }
        
        min_budget, max_budget = budget_limits.get(budget_range, (0, float('inf')))
        if min_budget <= guide_daily_rate <= max_budget:
            score += 20
        elif guide_daily_rate < min_budget:
            score += 15  # Cheaper than expected (good)
        else:
            score -= 10  # Too expensive
        
        # Rating bonus (20 points max)
        rating = guide.get('average_rating', 0)
        score += rating * 4
        
        # Experience bonus (10 points max)
        experience = guide.get('years_of_experience', 0)
        score += min(experience, 10)
        
        return max(0, score)

    def _get_match_reasons(self, itinerary: Dict, guide: Dict) -> List[str]:
        """Get list of reasons why guide matches the itinerary"""
        reasons = []
        
        # Specialty matches
        interests = itinerary.get('interests', [])
        specialties = guide.get('specialties', [])
        
        for interest in interests:
            for specialty in specialties:
                if interest.lower() in specialty.lower():
                    reasons.append(f"Specializes in {specialty}")
        
        # Rating
        rating = guide.get('average_rating', 0)
        if rating >= 4.5:
            reasons.append("Excellent ratings from previous tourists")
        elif rating >= 4.0:
            reasons.append("High ratings from previous tourists")
        
        # Experience
        experience = guide.get('years_of_experience', 0)
        if experience >= 5:
            reasons.append(f"{experience} years of guiding experience")
        
        # Languages
        languages = guide.get('languages', [])
        if 'English' in languages:
            reasons.append("Speaks English")
        if 'Indonesian' in languages:
            reasons.append("Local language expert")
        
        return reasons[:5]  # Limit to top 5 reasons
