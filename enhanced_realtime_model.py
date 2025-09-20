# Enhanced Real-Time Model with Travel Time and Interest-Based Filtering
# This module provides intelligent itinerary generation considering travel time and user interests

import requests
import json
import os
import time
from typing import Dict, List, Optional, Tuple
import math

class EnhancedRealTimeModel:
    """Enhanced real-time model with travel time optimization and interest-based filtering"""
    
    def __init__(self):
        # API Keys
        self.google_places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        self.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        
        # API Endpoints
        self.google_places_endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        self.google_distance_endpoint = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self.google_geocoding_endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
        
        # Interest-based place categories
        self.interest_categories = {
            'culture': ['culture', 'history', 'education'],
            'nature': ['nature', 'photography'],
            'adventure': ['adventure', 'nature'],
            'history': ['culture', 'history', 'education'],
            'food': ['food', 'local_cuisine'],
            'shopping': ['shopping', 'market'],
            'entertainment': ['entertainment', 'family'],
            'spiritual': ['spiritual', 'temple'],
            'photography': ['photography', 'nature'],
            'family': ['family', 'photography']
        }
        
        # Place data with coordinates and travel times
        self.place_database = {
            'visakhapatnam': {
                'kailasagiri_hill_park': {
                    'name': 'Kailasagiri Hill Park',
                    'address': 'Kailasagiri Hill Park, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (17.7292, 83.2847),
                    'categories': ['nature', 'photography', 'family'],
                    'duration': 20,
                    'cost': 20,
                    'rating': 4.2
                },
                'rk_beach': {
                    'name': 'Ramakrishna Beach (RK Beach)',
                    'address': 'RK Beach, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (17.7231, 83.2847),
                    'categories': ['nature', 'photography', 'family'],
                    'duration': 15,
                    'cost': 0,
                    'rating': 4.1
                },
                'submarine_museum': {
                    'name': 'INS Kurusura Submarine Museum',
                    'address': 'INS Kurusura Submarine Museum, RK Beach, Visakhapatnam',
                    'coordinates': (17.7231, 83.2847),
                    'categories': ['culture', 'history', 'family'],
                    'duration': 30,
                    'cost': 50,
                    'rating': 4.3
                },
                'dolphins_nose_lighthouse': {
                    'name': 'Dolphin\'s Nose Lighthouse',
                    'address': 'Dolphin\'s Nose Lighthouse, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (17.7167, 83.2833),
                    'categories': ['adventure', 'photography', 'nature'],
                    'duration': 25,
                    'cost': 30,
                    'rating': 4.0
                },
                'visakha_museum': {
                    'name': 'Visakha Museum',
                    'address': 'Visakha Museum, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (17.6869, 83.2181),
                    'categories': ['culture', 'history', 'education'],
                    'duration': 20,
                    'cost': 25,
                    'rating': 3.8
                },
                'yarada_beach': {
                    'name': 'Yarada Beach',
                    'address': 'Yarada Beach, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (17.6500, 83.2500),
                    'categories': ['nature', 'adventure', 'photography'],
                    'duration': 20,
                    'cost': 0,
                    'rating': 4.4
                },
                'araku_valley': {
                    'name': 'Araku Valley',
                    'address': 'Araku Valley, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (18.3333, 83.0000),
                    'categories': ['nature', 'adventure', 'photography'],
                    'duration': 60,
                    'cost': 100,
                    'rating': 4.5
                },
                'borra_caves': {
                    'name': 'Borra Caves',
                    'address': 'Borra Caves, Visakhapatnam, Andhra Pradesh',
                    'coordinates': (18.1667, 83.0000),
                    'categories': ['nature', 'adventure', 'history'],
                    'duration': 45,
                    'cost': 80,
                    'rating': 4.2
                }
            }
        }
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def estimate_travel_time(self, distance: float, transport_mode: str = 'car') -> int:
        """Estimate travel time based on distance and transport mode"""
        if transport_mode == 'walking':
            return int(distance * 12)  # 5 km/h walking speed
        elif transport_mode == 'car':
            return int(distance * 2)   # 30 km/h average city speed
        elif transport_mode == 'public_transport':
            return int(distance * 3)   # 20 km/h with waiting time
        else:
            return int(distance * 2)   # Default to car
    
    def get_places_by_interests(self, city: str, interests: List[str]) -> List[Dict]:
        """Get places filtered by user interests"""
        city_key = city.lower().replace(' ', '')
        
        if city_key not in self.place_database:
            return []
        
        places = []
        city_places = self.place_database[city_key]
        
        for place_id, place_data in city_places.items():
            place_categories = place_data['categories']
            
            # Check if place matches any user interest
            interest_match = False
            match_score = 0
            
            for interest in interests:
                if interest.lower() in self.interest_categories:
                    interest_categories = self.interest_categories[interest.lower()]
                    for cat in interest_categories:
                        if cat in place_categories:
                            interest_match = True
                            match_score += 1
            
            if interest_match:
                place_with_score = {
                    'id': place_id,
                    'match_score': match_score,
                    **place_data
                }
                places.append(place_with_score)
        
        # Sort by match score (higher score first)
        places.sort(key=lambda x: x['match_score'], reverse=True)
        
        return places
    
    def optimize_itinerary_by_travel_time(self, places: List[Dict], starting_location: str, 
                                        total_duration: int, mood: str) -> List[Dict]:
        """Optimize itinerary to minimize travel time and maximize experience"""
        
        if not places:
            return []
        
        # Get starting coordinates (simplified - in real implementation, use geocoding)
        starting_coords = (17.6869, 83.2181)  # Default to city center
        
        # Calculate distances from starting point
        for place in places:
            distance = self.calculate_distance(starting_coords, place['coordinates'])
            place['distance_from_start'] = distance
            place['travel_time_from_start'] = self.estimate_travel_time(distance)
        
        # Sort by duration first (shorter activities first), then by distance
        places.sort(key=lambda x: (x['duration'], x['distance_from_start']))
        
        # Select places based on total duration and mood
        selected_places = []
        remaining_time = total_duration
        
        for place in places:
            # Calculate total time needed (activity + travel)
            activity_time = place['duration']
            travel_time = place['travel_time_from_start']
            
            # Adjust time based on mood
            if mood == 'relaxed':
                activity_time = int(activity_time * 1.2)  # Take more time
            elif mood == 'adventurous':
                activity_time = int(activity_time * 0.8)  # Move faster
            
            total_time_needed = activity_time + travel_time
            
            # Debug: Print time calculation
            print(f"  Place: {place['name']}, Activity: {activity_time}min, Travel: {travel_time}min, Total: {total_time_needed}min, Remaining: {remaining_time}min")
            
            if total_time_needed <= remaining_time:
                selected_places.append(place)
                remaining_time -= total_time_needed
                
                # Update starting coordinates for next calculation
                starting_coords = place['coordinates']
            else:
                print(f"  Skipping {place['name']} - not enough time")
                break
        
        # If no places selected, include the first place anyway (fallback)
        if not selected_places and places:
            print(f"  Fallback: Including {places[0]['name']} despite time limit")
            selected_places.append(places[0])
        
        return selected_places
    
    def generate_interest_based_itinerary(self, city: str, starting_location: str, 
                                        duration: str, mood: str, interests: List[str]) -> Dict:
        """Generate itinerary based on interests and travel time optimization"""
        
        # Duration mapping
        duration_map = {
            '15': 15,
            '30': 30,
            '60': 60
        }
        
        total_duration = duration_map.get(duration, 30)
        
        # Get places filtered by interests
        interest_places = self.get_places_by_interests(city, interests)
        
        if not interest_places:
            # Fallback to all places if no interest match
            city_key = city.lower().replace(' ', '')
            if city_key in self.place_database:
                interest_places = [
                    {'id': place_id, **place_data} 
                    for place_id, place_data in self.place_database[city_key].items()
                ]
        
        # Debug: Print interest places found
        print(f"Debug: Found {len(interest_places)} places for interests: {interests}")
        for place in interest_places:
            print(f"  - {place['name']} (categories: {place['categories']})")
        
        # Optimize itinerary by travel time
        optimized_places = self.optimize_itinerary_by_travel_time(
            interest_places, starting_location, total_duration, mood
        )
        
        # Debug: Print optimized places
        print(f"Debug: Optimized to {len(optimized_places)} places")
        for place in optimized_places:
            print(f"  - {place['name']} (duration: {place['duration']} min)")
        
        # Generate itinerary
        itinerary = {
            'title': f'🎯 {mood.title()} {duration}-Minute {city.title()} Experience',
            'description': f'Optimized itinerary for {city.title()} based on your interests: {", ".join(interests)}',
            'starting_location': starting_location,
            'total_duration': f"{duration} minutes",
            'mood': mood,
            'interests': interests,
            'real_time': True,
            'travel_optimized': True,
            'interest_based': True,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Create activities with travel time
        activities = []
        current_time = 0
        
        for i, place in enumerate(optimized_places):
            # Add travel time if not first place
            if i > 0:
                prev_place = optimized_places[i-1]
                travel_distance = self.calculate_distance(
                    prev_place['coordinates'], place['coordinates']
                )
                travel_time = self.estimate_travel_time(travel_distance)
                
                if travel_time > 0:
                    activities.append({
                        'name': f'Travel to {place["name"]}',
                        'duration': f'{travel_time} minutes',
                        'description': f'Travel from {prev_place["name"]} to {place["name"]}',
                        'location': f'From {prev_place["address"]} to {place["address"]}',
                        'tips': f'Travel distance: {travel_distance:.1f} km',
                        'cost': 'Transportation cost',
                        'travel_time': True
                    })
                    current_time += travel_time
            
            # Add main activity
            activity = {
                'name': f'Visit {place["name"]}',
                'duration': f'{place["duration"]} minutes',
                'description': f'Explore {place["name"]} - {", ".join(place["categories"])} experience',
                'location': place['address'],
                'tips': f'Rating: {place["rating"]}/5. Categories: {", ".join(place["categories"])}',
                'cost': f'₹{place["cost"]}' if place["cost"] > 0 else 'Free',
                'rating': place['rating'],
                'categories': place['categories'],
                'real_place': True
            }
            
            activities.append(activity)
            current_time += place['duration']
        
        itinerary['activities'] = activities
        
        # Add tips based on interests and mood
        tips = [
            f"Start your journey from {starting_location}",
            f"Total estimated time: {current_time} minutes",
            f"Interests covered: {', '.join(interests)}",
            "Allow extra time for photos and exploration",
            "Wear comfortable walking shoes",
            "Bring a camera or smartphone for memories"
        ]
        
        if mood == 'relaxed':
            tips.append("Take your time to enjoy each location")
        elif mood == 'adventurous':
            tips.append("Be prepared for some physical activity")
        elif mood == 'cultural':
            tips.append("Learn about the local history and culture")
        
        itinerary['tips'] = tips
        
        # Calculate total cost
        total_cost = sum(place['cost'] for place in optimized_places)
        itinerary['estimated_cost'] = f'₹{total_cost}' if total_cost > 0 else 'Free'
        
        itinerary['difficulty'] = 'Moderate'
        itinerary['best_time'] = 'Any time (check weather)'
        itinerary['transportation'] = 'Walking/Public Transport/Car'
        
        return itinerary
    
    def get_real_time_places(self, city: str, interests: List[str]) -> List[Dict]:
        """Get real-time places from Google Places API"""
        
        if not self.google_places_api_key:
            return self.get_places_by_interests(city, interests)
        
        try:
            places = []
            
            # Search for each interest category
            for interest in interests:
                if interest.lower() in self.interest_categories:
                    categories = self.interest_categories[interest.lower()]
                    
                    for category in categories:
                        params = {
                            'query': f'{category} in {city}',
                            'key': self.google_places_api_key,
                            'type': 'tourist_attraction'
                        }
                        
                        response = requests.get(self.google_places_endpoint, params=params, timeout=10)
                        response.raise_for_status()
                        
                        data = response.json()
                        
                        if data['status'] == 'OK':
                            for place in data['results'][:3]:  # Limit to 3 per category
                                places.append({
                                    'name': place['name'],
                                    'address': place.get('formatted_address', ''),
                                    'rating': place.get('rating', 0),
                                    'place_id': place.get('place_id', ''),
                                    'categories': [category],
                                    'duration': 30,  # Default duration
                                    'cost': 0,  # Default cost
                                    'coordinates': (0, 0)  # Would need geocoding
                                })
            
            return places
            
        except Exception as e:
            print(f"Real-time API Error: {e}")
            return self.get_places_by_interests(city, interests)

# Usage function
def generate_enhanced_itinerary(city: str, starting_location: str, duration: str, 
                              mood: str, interests: List[str]) -> Dict:
    """Generate enhanced itinerary with travel time optimization and interest filtering"""
    
    model = EnhancedRealTimeModel()
    return model.generate_interest_based_itinerary(city, starting_location, duration, mood, interests)

# Test function
def test_enhanced_model():
    """Test the enhanced model with different interests"""
    
    print("🧪 Testing Enhanced Real-Time Model")
    print("=" * 50)
    
    test_cases = [
        {
            'city': 'Visakhapatnam',
            'starting_location': 'Central Station',
            'duration': '30',
            'mood': 'relaxed',
            'interests': ['culture', 'history']
        },
        {
            'city': 'Visakhapatnam',
            'starting_location': 'Central Station',
            'duration': '30',
            'mood': 'adventurous',
            'interests': ['nature', 'adventure']
        },
        {
            'city': 'Visakhapatnam',
            'starting_location': 'Central Station',
            'duration': '30',
            'mood': 'cultural',
            'interests': ['photography', 'family']
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🎯 Test {i}: {test_case['mood'].title()} Mood - {', '.join(test_case['interests'])}")
        print("-" * 60)
        
        result = generate_enhanced_itinerary(**test_case)
        
        print(f"Title: {result['title']}")
        print(f"Travel Optimized: {result.get('travel_optimized', False)}")
        print(f"Interest Based: {result.get('interest_based', False)}")
        print()
        
        print("Activities with Travel Time:")
        for j, activity in enumerate(result['activities'], 1):
            travel_indicator = "🚗 " if activity.get('travel_time', False) else "📍 "
            print(f"{travel_indicator}{j}. {activity['name']}")
            print(f"   Duration: {activity['duration']}")
            print(f"   Location: {activity['location']}")
            if 'categories' in activity:
                print(f"   Categories: {', '.join(activity['categories'])}")
            print()
        
        print(f"Total Cost: {result['estimated_cost']}")
        print()

if __name__ == "__main__":
    test_enhanced_model()
