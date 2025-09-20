# Real AI Integration for TourismHub Itinerary Generator
# This module provides real AI API integration for generating accurate, location-specific itineraries

import requests
import json
import os
from typing import Dict, List, Optional

class RealAIIntegration:
    """Real AI integration for generating accurate itineraries with exact place names"""
    
    def __init__(self):
        # API Keys - Set these in environment variables for production
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # API Endpoints
        self.openai_endpoint = "https://api.openai.com/v1/chat/completions"
        self.google_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def generate_itinerary_with_openai(self, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Optional[Dict]:
        """Generate itinerary using OpenAI GPT-4 API"""
        
        if not self.openai_api_key:
            return None
            
        prompt = self._create_openai_prompt(city, starting_location, duration, mood, interests)
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional travel planner with extensive knowledge of cities worldwide. Generate accurate, location-specific itineraries with exact place names, addresses, and practical information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.openai_endpoint, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            itinerary_text = result['choices'][0]['message']['content']
            
            # Parse the AI response into structured format
            return self._parse_ai_response(itinerary_text, city, starting_location, duration, mood, interests)
            
        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return None
    
    def generate_itinerary_with_google(self, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Optional[Dict]:
        """Generate itinerary using Google Gemini API"""
        
        if not self.google_api_key:
            return None
            
        prompt = self._create_google_prompt(city, starting_location, duration, mood, interests)
        
        url = f"{self.google_endpoint}?key={self.google_api_key}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000
            }
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            itinerary_text = result['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the AI response into structured format
            return self._parse_ai_response(itinerary_text, city, starting_location, duration, mood, interests)
            
        except Exception as e:
            print(f"Google API Error: {e}")
            return None
    
    def _create_openai_prompt(self, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> str:
        """Create a detailed prompt for OpenAI"""
        
        interests_text = ", ".join(interests)
        
        prompt = f"""
        Generate a detailed {duration}-minute itinerary for {city} starting from {starting_location}.
        
        Requirements:
        - Mood: {mood}
        - Interests: {interests_text}
        - Duration: {duration} minutes
        - Starting Location: {starting_location}
        
        Please provide:
        1. Exact place names with full addresses
        2. Realistic time allocations for each activity
        3. Practical tips and recommendations
        4. Cost estimates in local currency
        5. Transportation options between locations
        6. Best times to visit each location
        
        Format the response as a JSON object with this structure:
        {{
            "title": "Mood Duration-Minute City Experience",
            "description": "Brief description of the itinerary",
            "activities": [
                {{
                    "name": "Activity Name",
                    "duration": "X minutes",
                    "description": "Detailed description",
                    "location": "Exact address and location",
                    "tips": "Practical tips and recommendations",
                    "cost": "Cost in local currency",
                    "best_time": "Best time to visit",
                    "transportation": "How to get there from previous location"
                }}
            ],
            "tips": [
                "General tips for the itinerary"
            ],
            "estimated_cost": "Total estimated cost",
            "difficulty": "Easy/Moderate/Active",
            "best_time": "Best time to start",
            "transportation": "Overall transportation method"
        }}
        
        Make sure all place names are real and accurate for {city}.
        """
        
        return prompt
    
    def _create_google_prompt(self, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> str:
        """Create a detailed prompt for Google Gemini"""
        
        interests_text = ", ".join(interests)
        
        prompt = f"""
        As a professional travel planner, create a {duration}-minute itinerary for {city} starting from {starting_location}.
        
        Traveler Profile:
        - Mood: {mood}
        - Interests: {interests_text}
        - Duration: {duration} minutes
        - Starting Point: {starting_location}
        
        Requirements:
        1. Use only real, existing places in {city}
        2. Provide exact addresses and location details
        3. Include realistic time estimates
        4. Add practical tips and local insights
        5. Estimate costs in local currency
        6. Suggest transportation between locations
        
        Return a JSON response with this exact structure:
        {{
            "title": "Mood Duration-Minute City Experience",
            "description": "Brief description",
            "activities": [
                {{
                    "name": "Real Place Name",
                    "duration": "X minutes",
                    "description": "What to do there",
                    "location": "Full address, City",
                    "tips": "Practical advice",
                    "cost": "Cost in local currency",
                    "best_time": "When to visit",
                    "transportation": "How to get there"
                }}
            ],
            "tips": ["General tips"],
            "estimated_cost": "Total cost",
            "difficulty": "Easy/Moderate/Active",
            "best_time": "Best start time",
            "transportation": "Main transport method"
        }}
        
        Ensure all locations are real and accessible in {city}.
        """
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Dict:
        """Parse AI response into structured itinerary format"""
        
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                itinerary = json.loads(json_str)
                
                # Add metadata
                itinerary['starting_location'] = starting_location
                itinerary['total_duration'] = f"{duration} minutes"
                itinerary['mood'] = mood
                itinerary['interests'] = interests
                itinerary['ai_generated'] = True
                itinerary['real_ai'] = True
                
                return itinerary
                
        except json.JSONDecodeError:
            pass
        
        # Fallback: create structured response from text
        return self._create_fallback_itinerary(response_text, city, starting_location, duration, mood, interests)
    
    def _create_fallback_itinerary(self, response_text: str, city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Dict:
        """Create fallback itinerary from AI text response"""
        
        # This would parse the text response and extract structured information
        # For now, return a basic structure
        
        return {
            'title': f'AI-Generated {duration}-Minute {city} Experience',
            'description': f'AI-powered itinerary for {city} starting from {starting_location}',
            'starting_location': starting_location,
            'total_duration': f"{duration} minutes",
            'activities': [
                {
                    'name': 'AI-Generated Activity',
                    'duration': f'{duration} minutes',
                    'description': 'AI-recommended activity',
                    'location': f'{city}',
                    'tips': 'AI-generated tips',
                    'cost': 'Varies'
                }
            ],
            'tips': ['AI-generated tips'],
            'estimated_cost': 'Varies',
            'difficulty': 'Moderate',
            'best_time': 'Any time',
            'transportation': 'Walking',
            'mood': mood,
            'interests': interests,
            'ai_generated': True,
            'real_ai': True,
            'raw_response': response_text
        }
    
    def get_real_time_data(self, city: str, location: str) -> Dict:
        """Get real-time data for a location (weather, traffic, etc.)"""
        
        # This would integrate with weather APIs, traffic APIs, etc.
        # For now, return mock data
        
        return {
            'weather': 'Sunny, 25°C',
            'traffic': 'Moderate',
            'crowd_level': 'Medium',
            'best_time': 'Morning',
            'accessibility': 'Good'
        }

# Usage example
def generate_real_ai_itinerary(city: str, starting_location: str, duration: str, mood: str, interests: List[str]) -> Optional[Dict]:
    """Main function to generate real AI itinerary"""
    
    ai_integration = RealAIIntegration()
    
    # Try OpenAI first
    itinerary = ai_integration.generate_itinerary_with_openai(city, starting_location, duration, mood, interests)
    if itinerary:
        return itinerary
    
    # Fallback to Google
    itinerary = ai_integration.generate_itinerary_with_google(city, starting_location, duration, mood, interests)
    if itinerary:
        return itinerary
    
    # If both fail, return None to use fallback system
    return None

# Environment setup instructions
ENVIRONMENT_SETUP = """
To use real AI integration, set these environment variables:

1. For OpenAI GPT-4:
   export OPENAI_API_KEY="your-openai-api-key"

2. For Google Gemini:
   export GOOGLE_API_KEY="your-google-api-key"

3. For Anthropic Claude (optional):
   export ANTHROPIC_API_KEY="your-anthropic-api-key"

Then import and use:
from ai_integration import generate_real_ai_itinerary

itinerary = generate_real_ai_itinerary(
    city="Hyderabad",
    starting_location="Central Station",
    duration="30",
    mood="relaxed",
    interests=["culture", "nature"]
)
"""
