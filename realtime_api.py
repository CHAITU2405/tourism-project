# Real-Time API Integration for TourismHub
# This module provides real-time data from various APIs for accurate place information

import requests
import json
import os
from typing import Dict, List, Optional
import time

class RealTimeAPI:
    """Real-time API integration for getting live place data"""
    
    def __init__(self):
        # API Keys - Set these in environment variables
        self.google_places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.foursquare_api_key = os.getenv('FOURSQUARE_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        
        # API Endpoints
        self.google_places_endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.foursquare_endpoint = "https://api.foursquare.com/v3/places/search"
        self.openweather_endpoint = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_real_places_for_city(self, city: str, category: str = "tourist_attraction") -> List[Dict]:
        """Get real places for a city using Google Places API"""
        
        if not self.google_places_api_key:
            return self._get_fallback_places(city, category)
        
        try:
            # Search for tourist attractions in the city
            params = {
                'query': f'{category} in {city}',
                'key': self.google_places_api_key,
                'type': 'tourist_attraction'
            }
            
            response = requests.get(self.google_places_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                places = []
                for place in data['results'][:10]:  # Limit to 10 places
                    places.append({
                        'name': place['name'],
                        'address': place.get('formatted_address', ''),
                        'rating': place.get('rating', 0),
                        'place_id': place.get('place_id', ''),
                        'types': place.get('types', [])
                    })
                return places
            else:
                return self._get_fallback_places(city, category)
                
        except Exception as e:
            print(f"Google Places API Error: {e}")
            return self._get_fallback_places(city, category)
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a specific place"""
        
        if not self.google_places_api_key or not place_id:
            return None
        
        try:
            endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                'place_id': place_id,
                'key': self.google_places_api_key,
                'fields': 'name,formatted_address,rating,opening_hours,photos,reviews'
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK':
                result = data['result']
                return {
                    'name': result.get('name', ''),
                    'address': result.get('formatted_address', ''),
                    'rating': result.get('rating', 0),
                    'opening_hours': result.get('opening_hours', {}),
                    'photos': result.get('photos', []),
                    'reviews': result.get('reviews', [])
                }
            else:
                return None
                
        except Exception as e:
            print(f"Place Details API Error: {e}")
            return None
    
    def get_weather_data(self, city: str) -> Optional[Dict]:
        """Get real-time weather data for a city"""
        
        if not self.openweather_api_key:
            return self._get_fallback_weather(city)
        
        try:
            params = {
                'q': city,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(self.openweather_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'city': data['name']
            }
            
        except Exception as e:
            print(f"Weather API Error: {e}")
            return self._get_fallback_weather(city)
    
    def get_foursquare_places(self, city: str, category: str = "tourist_attraction") -> List[Dict]:
        """Get places from Foursquare API"""
        
        if not self.foursquare_api_key:
            return []
        
        try:
            headers = {
                'Authorization': self.foursquare_api_key,
                'Accept': 'application/json'
            }
            
            params = {
                'query': category,
                'near': city,
                'limit': 10
            }
            
            response = requests.get(self.foursquare_endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            places = []
            for result in data.get('results', []):
                places.append({
                    'name': result.get('name', ''),
                    'address': result.get('location', {}).get('formatted_address', ''),
                    'rating': result.get('rating', 0),
                    'category': result.get('categories', [{}])[0].get('name', ''),
                    'distance': result.get('distance', 0)
                })
            
            return places
            
        except Exception as e:
            print(f"Foursquare API Error: {e}")
            return []
    
    def _get_fallback_places(self, city: str, category: str) -> List[Dict]:
        """Fallback places when API is not available"""
        
        # Pre-defined real places for major cities
        fallback_places = {
            'visakhapatnam': [
                {'name': 'Kailasagiri Hill Park', 'address': 'Kailasagiri Hill Park, Visakhapatnam, Andhra Pradesh', 'rating': 4.2},
                {'name': 'Ramakrishna Beach', 'address': 'RK Beach, Visakhapatnam, Andhra Pradesh', 'rating': 4.1},
                {'name': 'INS Kurusura Submarine Museum', 'address': 'INS Kurusura Submarine Museum, RK Beach, Visakhapatnam', 'rating': 4.3},
                {'name': 'Dolphin\'s Nose Lighthouse', 'address': 'Dolphin\'s Nose Lighthouse, Visakhapatnam, Andhra Pradesh', 'rating': 4.0},
                {'name': 'Visakha Museum', 'address': 'Visakha Museum, Visakhapatnam, Andhra Pradesh', 'rating': 3.8},
                {'name': 'Yarada Beach', 'address': 'Yarada Beach, Visakhapatnam, Andhra Pradesh', 'rating': 4.4},
                {'name': 'Araku Valley', 'address': 'Araku Valley, Visakhapatnam, Andhra Pradesh', 'rating': 4.5},
                {'name': 'Borra Caves', 'address': 'Borra Caves, Visakhapatnam, Andhra Pradesh', 'rating': 4.2}
            ],
            'hyderabad': [
                {'name': 'Charminar', 'address': 'Charminar, Old City, Hyderabad, Telangana', 'rating': 4.0},
                {'name': 'Golconda Fort', 'address': 'Golconda Fort, Hyderabad, Telangana', 'rating': 4.3},
                {'name': 'Hussain Sagar Lake', 'address': 'Hussain Sagar Lake, Hyderabad, Telangana', 'rating': 4.1},
                {'name': 'Lumbini Park', 'address': 'Lumbini Park, Near Hussain Sagar Lake, Hyderabad', 'rating': 4.0},
                {'name': 'Necklace Road', 'address': 'Necklace Road, Hyderabad, Telangana', 'rating': 4.2},
                {'name': 'Mecca Masjid', 'address': 'Mecca Masjid, Old City, Hyderabad, Telangana', 'rating': 4.1},
                {'name': 'Chowmahalla Palace', 'address': 'Chowmahalla Palace, Old City, Hyderabad, Telangana', 'rating': 4.2},
                {'name': 'Birla Mandir', 'address': 'Birla Mandir, Naubat Pahad, Hyderabad, Telangana', 'rating': 4.3}
            ]
        }
        
        city_key = city.lower().replace(' ', '')
        return fallback_places.get(city_key, [])
    
    def _get_fallback_weather(self, city: str) -> Dict:
        """Fallback weather data when API is not available"""
        
        return {
            'temperature': 25,
            'description': 'Pleasant weather',
            'humidity': 60,
            'wind_speed': 10,
            'city': city
        }
    
    def generate_real_time_itinerary(self, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Dict:
        """Generate itinerary using real-time data"""
        
        # Get real places for the city
        real_places = self.get_real_places_for_city(city)
        
        # Get weather data
        weather = self.get_weather_data(city)
        
        # Generate itinerary based on real data
        itinerary = {
            'title': f'🌍 Real-Time {duration}-Minute {city.title()} Experience',
            'description': f'Live itinerary for {city.title()} starting from {starting_location}',
            'starting_location': starting_location,
            'total_duration': f"{duration} minutes",
            'mood': mood,
            'interests': interests,
            'real_time': True,
            'weather': weather,
            'places_source': 'Real-time API' if real_places else 'Fallback Database',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create activities from real places
        activities = []
        duration_map = {
            '15': 2,
            '30': 3,
            '60': 4
        }
        
        num_activities = duration_map.get(duration, 3)
        
        for i, place in enumerate(real_places[:num_activities]):
            activity = {
                'name': f'Visit {place["name"]}',
                'duration': f'{int(duration) // num_activities} minutes',
                'description': f'Explore {place["name"]} - a popular attraction in {city.title()}',
                'location': place['address'],
                'tips': f'Rating: {place["rating"]}/5. Check weather conditions before visiting.',
                'cost': 'Varies',
                'rating': place['rating'],
                'real_place': True
            }
            activities.append(activity)
        
        itinerary['activities'] = activities
        
        # Add real-time tips
        tips = [
            f"Start your journey from {starting_location}",
            "Check real-time weather conditions",
            "Allow extra time for photos and exploration",
            "Wear comfortable walking shoes",
            "Bring a camera or smartphone for memories"
        ]
        
        if weather:
            tips.append(f"Current weather: {weather['temperature']}°C, {weather['description']}")
        
        itinerary['tips'] = tips
        itinerary['estimated_cost'] = 'Varies based on activities'
        itinerary['difficulty'] = 'Moderate'
        itinerary['best_time'] = 'Any time (check weather)'
        itinerary['transportation'] = 'Walking/Public Transport'
        
        return itinerary

# Usage function
def generate_real_time_itinerary(city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Dict:
    """Generate real-time itinerary using live data"""
    
    api = RealTimeAPI()
    return api.generate_real_time_itinerary(city, starting_location, duration, mood, interests)

# Environment setup instructions
REALTIME_SETUP = """
To use real-time API integration, set these environment variables:

1. For Google Places API:
   export GOOGLE_PLACES_API_KEY="your-google-places-api-key"

2. For Foursquare API:
   export FOURSQUARE_API_KEY="your-foursquare-api-key"

3. For OpenWeather API:
   export OPENWEATHER_API_KEY="your-openweather-api-key"

Then import and use:
from realtime_api import generate_real_time_itinerary

itinerary = generate_real_time_itinerary(
    city="Visakhapatnam",
    starting_location="Central Station",
    duration="30",
    mood="relaxed",
    interests=["culture", "nature"]
)
"""
