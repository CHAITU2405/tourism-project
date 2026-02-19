from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS
# Custom translation system
from werkzeug.utils import secure_filename
# Note: Using plaintext passwords per request (no hashing)
from datetime import datetime, date, timedelta
import json
import os
import random
import string
import time
import asyncio
import base64
import math
from typing import Dict, Optional
from io import BytesIO
from deep_translator import GoogleTranslator
import edge_tts
from gtts import gTTS
from geopy.geocoders import Nominatim
import requests
from openrouteservice import convert
try:
    import google.generativeai as genai
except Exception:
    genai = None  # e.g. Python 3.14 + protobuf incompatibility on Render
from models import db, User, Hotel, Booking, Admin, RoomType, RoomAvailability, Review, Wishlist, VehicleRental, Vehicle, VehicleBooking, VehicleReview, Complaint
from sqlalchemy import or_, and_, text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# Database in instance folder only (Flask convention)
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'tourism.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Custom translation system
app.config['LANGUAGES'] = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'it': 'Italiano',
    'pt': 'Português',
    'ru': 'Русский',
    'ja': '日本語',
    'ko': '한국어',
    'zh': '中文',
    'hi': 'हिन्दी',
    'ar': 'العربية',
    'th': 'ไทย',
    'vi': 'Tiếng Việt',
    'tr': 'Türkçe',
    'pl': 'Polski',
    'nl': 'Nederlands',
    'sv': 'Svenska',
    'da': 'Dansk',
    'no': 'Norsk',
    'fi': 'Suomi',
    'cs': 'Čeština',
    'hu': 'Magyar',
    'ro': 'Română',
    'bg': 'Български',
    'hr': 'Hrvatski',
    'sk': 'Slovenčina',
    'sl': 'Slovenščina',
    'et': 'Eesti',
    'lv': 'Latviešu',
    'lt': 'Lietuvių',
    'el': 'Ελληνικά',
    'he': 'עברית',
    'fa': 'فارسی',
    'ur': 'اردو',
    'bn': 'বাংলা',
    'ta': 'தமிழ்',
    'te': 'తెలుగు',
    'ml': 'മലയാളം',
    'kn': 'ಕನ್ನಡ',
    'gu': 'ગુજરાતી',
    'pa': 'ਪੰਜਾਬੀ',
    'mr': 'मराठी',
    'ne': 'नेपाली',
    'si': 'සිංහල',
    'my': 'မြန်မာ',
    'km': 'ខ្មែរ',
    'lo': 'ລາວ',
    'ka': 'ქართული',
    'hy': 'Հայերեն',
    'az': 'Azərbaycan',
    'kk': 'Қазақ',
    'ky': 'Кыргыз',
    'uz': 'Oʻzbek',
    'tg': 'Тоҷикӣ',
    'mn': 'Монгол',
    'bo': 'བོད་ཡིག',
    'dz': 'རྫོང་ཁ',
    'am': 'አማርኛ',
    'ti': 'ትግርኛ',
    'om': 'Afaan Oromoo',
    'so': 'Soomaali',
    'sw': 'Kiswahili',
    'zu': 'IsiZulu',
    'xh': 'IsiXhosa',
    'af': 'Afrikaans',
    'eu': 'Euskera',
    'ca': 'Català',
    'gl': 'Galego',
    'cy': 'Cymraeg',
    'ga': 'Gaeilge',
    'mt': 'Malti',
    'is': 'Íslenska',
    'fo': 'Føroyskt',
    'kl': 'Kalaallisut',
    'iu': 'ᐃᓄᒃᑎᑐᑦ',
    'cr': 'ᓀᐦᐃᔭᐍᐏᐣ',
    'oj': 'ᐊᓂᔑᓈᐯᒧᐎᓐ',
    'chr': 'ᏣᎳᎩ',
    'haw': 'ʻŌlelo Hawaiʻi',
    'mi': 'Te Reo Māori',
    'sm': 'Gagana Samoa',
    'to': 'Lea fakatonga',
    'fj': 'Na Vosa Vakaviti',
    'ty': 'Reo Tahiti',
    'mg': 'Malagasy',
    'ny': 'Chichewa',
    'sn': 'ChiShona',
    'st': 'Sesotho',
    'tn': 'Setswana',
    'ss': 'SiSwati',
    've': 'Tshivenḓa',
    'ts': 'Xitsonga',
    'nr': 'IsiNdebele',
    'nso': 'Sesotho sa Leboa'
}

# No word mapping: UI strings shown as-is. Translator page uses GoogleTranslator (LANG_CONFIG, /api/translate).
def get_locale():
    return 'en'

def _(text, lang=None):
    """Passthrough: no JSON word mapping; translator feature is separate."""
    return text

app.jinja_env.globals.update(_=_)
app.jinja_env.globals.update(get_locale=get_locale)
app.jinja_env.globals.update(LANGUAGES=app.config['LANGUAGES'])

@app.route('/set_language/<language>')
def set_language(language=None):
    """No-op: word mapping removed; redirect back."""
    return redirect(request.referrer or url_for('index'))

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS for translation API
CORS(app)

# Language configuration for translation
LANG_CONFIG: Dict[str, Dict[str, str]] = {
    # Major World Languages
    "en": {"name": "English (US)", "translate": "en", "voice": "en-US-AriaNeural"},
    "es": {"name": "Spanish", "translate": "es", "voice": "es-ES-ElviraNeural"},
    "fr": {"name": "French", "translate": "fr", "voice": "fr-FR-DeniseNeural"},
    "de": {"name": "German", "translate": "de", "voice": "de-DE-KatjaNeural"},
    "it": {"name": "Italian", "translate": "it", "voice": "it-IT-ElsaNeural"},
    "pt": {"name": "Portuguese", "translate": "pt", "voice": "pt-BR-FranciscaNeural"},
    "ru": {"name": "Russian", "translate": "ru", "voice": "ru-RU-SvetlanaNeural"},
    "ja": {"name": "Japanese", "translate": "ja", "voice": "ja-JP-NanamiNeural"},
    "ko": {"name": "Korean", "translate": "ko", "voice": "ko-KR-SunHiNeural"},
    "zh": {"name": "Chinese (Simplified)", "translate": "zh", "voice": "zh-CN-XiaoxiaoNeural"},
    "ar": {"name": "Arabic", "translate": "ar", "voice": "ar-SA-ZariyahNeural"},
    
    # Indian Languages
    "hi": {"name": "Hindi", "translate": "hi", "voice": "hi-IN-SwaraNeural"},
    "te": {"name": "Telugu", "translate": "te", "voice": "te-IN-ShrutiNeural"},
    "ta": {"name": "Tamil", "translate": "ta", "voice": "ta-IN-PallaviNeural"},
    "bn": {"name": "Bengali", "translate": "bn", "voice": "bn-IN-TanishaaNeural"},
    "mr": {"name": "Marathi", "translate": "mr", "voice": "mr-IN-AarohiNeural"},
    "gu": {"name": "Gujarati", "translate": "gu", "voice": "gu-IN-DhwaniNeural"},
    "kn": {"name": "Kannada", "translate": "kn", "voice": "kn-IN-SapnaNeural"},
    "ml": {"name": "Malayalam", "translate": "ml", "voice": "ml-IN-SobhanaNeural"},
    "pa": {"name": "Punjabi", "translate": "pa", "voice": "pa-IN-PreetiNeural"},
    "or": {"name": "Odia", "translate": "or", "voice": "or-IN-KalpanaNeural"},
    "as": {"name": "Assamese", "translate": "as", "voice": "as-IN-JyotiNeural"},
    "ne": {"name": "Nepali", "translate": "ne", "voice": "ne-NP-HemkalaNeural"},
    
    # Southeast Asian Languages
    "th": {"name": "Thai", "translate": "th", "voice": "th-TH-PremwadeeNeural"},
    "vi": {"name": "Vietnamese", "translate": "vi", "voice": "vi-VN-HoaiMyNeural"},
    "id": {"name": "Indonesian", "translate": "id", "voice": "id-ID-GadisNeural"},
    "ms": {"name": "Malay", "translate": "ms", "voice": "ms-MY-YasminNeural"},
    "tl": {"name": "Filipino", "translate": "tl", "voice": "fil-PH-BlessicaNeural"},
    "my": {"name": "Burmese", "translate": "my", "voice": "my-MM-NilarNeural"},
    "km": {"name": "Khmer", "translate": "km", "voice": "km-KH-SreymomNeural"},
    "lo": {"name": "Lao", "translate": "lo", "voice": "lo-LA-KeomanyNeural"},
    
    # European Languages
    "nl": {"name": "Dutch", "translate": "nl", "voice": "nl-NL-ColetteNeural"},
    "sv": {"name": "Swedish", "translate": "sv", "voice": "sv-SE-HilleviNeural"},
    "no": {"name": "Norwegian", "translate": "no", "voice": "nb-NO-IselinNeural"},
    "da": {"name": "Danish", "translate": "da", "voice": "da-DK-ChristelNeural"},
    "fi": {"name": "Finnish", "translate": "fi", "voice": "fi-FI-NooraNeural"},
    "pl": {"name": "Polish", "translate": "pl", "voice": "pl-PL-AgnieszkaNeural"},
    "cs": {"name": "Czech", "translate": "cs", "voice": "cs-CZ-VlastaNeural"},
    "sk": {"name": "Slovak", "translate": "sk", "voice": "sk-SK-ViktoriaNeural"},
    "hu": {"name": "Hungarian", "translate": "hu", "voice": "hu-HU-NoemiNeural"},
    "ro": {"name": "Romanian", "translate": "ro", "voice": "ro-RO-AlinaNeural"},
    "bg": {"name": "Bulgarian", "translate": "bg", "voice": "bg-BG-KalinaNeural"},
    "hr": {"name": "Croatian", "translate": "hr", "voice": "hr-HR-GabrijelaNeural"},
    "sr": {"name": "Serbian", "translate": "sr", "voice": "sr-RS-SophieNeural"},
    "sl": {"name": "Slovenian", "translate": "sl", "voice": "sl-SI-PetraNeural"},
    "et": {"name": "Estonian", "translate": "et", "voice": "et-EE-AnuNeural"},
    "lv": {"name": "Latvian", "translate": "lv", "voice": "lv-LV-EveritaNeural"},
    "lt": {"name": "Lithuanian", "translate": "lt", "voice": "lt-LT-OnaNeural"},
    "el": {"name": "Greek", "translate": "el", "voice": "el-GR-AthinaNeural"},
    "tr": {"name": "Turkish", "translate": "tr", "voice": "tr-TR-EmelNeural"},
    "uk": {"name": "Ukrainian", "translate": "uk", "voice": "uk-UA-PolinaNeural"},
    
    # Middle Eastern & African Languages
    "fa": {"name": "Persian (Farsi)", "translate": "fa", "voice": "fa-IR-DilaraNeural"},
    "ur": {"name": "Urdu", "translate": "ur", "voice": "ur-PK-UzmaNeural"},
    "he": {"name": "Hebrew", "translate": "he", "voice": "he-IL-HilaNeural"},
    "sw": {"name": "Swahili", "translate": "sw", "voice": "sw-KE-ZuriNeural"},
    "am": {"name": "Amharic", "translate": "am", "voice": "am-ET-MekdesNeural"},
    "yo": {"name": "Yoruba", "translate": "yo", "voice": "yo-NG-AdeolaNeural"},
    "ig": {"name": "Igbo", "translate": "ig", "voice": "ig-NG-NnekaNeural"},
    "ha": {"name": "Hausa", "translate": "ha", "voice": "ha-NG-ZainabNeural"},
    
    # East Asian Languages
    "zh-tw": {"name": "Chinese (Traditional)", "translate": "zh-tw", "voice": "zh-TW-HsiaoyuNeural"},
    "yue": {"name": "Cantonese", "translate": "yue", "voice": "yue-CN-XiaoxiaoNeural"},
    
    # Other Important Languages
    "ca": {"name": "Catalan", "translate": "ca", "voice": "ca-ES-AlbaNeural"},
    "eu": {"name": "Basque", "translate": "eu", "voice": "eu-ES-AinhoaNeural"},
    "gl": {"name": "Galician", "translate": "gl", "voice": "gl-ES-SabelaNeural"},
    "is": {"name": "Icelandic", "translate": "is", "voice": "is-IS-GudrunNeural"},
    "ga": {"name": "Irish", "translate": "ga", "voice": "ga-IE-OrlaNeural"},
    "cy": {"name": "Welsh", "translate": "cy", "voice": "cy-GB-NiaNeural"},
    "mt": {"name": "Maltese", "translate": "mt", "voice": "mt-MT-GraceNeural"},
    "sq": {"name": "Albanian", "translate": "sq", "voice": "sq-AL-AnilaNeural"},
    "mk": {"name": "Macedonian", "translate": "mk", "voice": "mk-MK-MarijaNeural"},
    "bs": {"name": "Bosnian", "translate": "bs", "voice": "bs-BA-VesnaNeural"},
    "me": {"name": "Montenegrin", "translate": "me", "voice": "sr-RS-SophieNeural"},
}

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom Jinja2 filters and functions
@app.template_filter('from_json')
def from_json_filter(json_string):
    """Convert JSON string to Python object"""
    if json_string:
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return []
    return []

@app.template_filter('to_json')
def to_json_filter(obj):
    """Convert Python object to JSON string"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return '[]'

@app.template_filter('tojson')
def tojson_filter(obj):
    """Convert Python object to JSON string (alias for to_json)"""
    try:
        return json.dumps(obj)
    except (TypeError, ValueError):
        return '[]'

@app.template_filter('format_currency')
def format_currency_filter(amount):
    """Format number as currency"""
    try:
        return f"${float(amount):.2f}"
    except (ValueError, TypeError):
        return "$0.00"

# Translation helper functions
def get_lang_code(lang_key: str) -> str:
    """Get language code for translation"""
    cfg = LANG_CONFIG.get(lang_key)
    if not cfg:
        raise ValueError(f"Unsupported language: {lang_key}")
    return cfg["translate"]

def get_voice(lang_key: str, override_voice: Optional[str] = None) -> str:
    """Get voice for text-to-speech"""
    if override_voice:
        return override_voice
    cfg = LANG_CONFIG.get(lang_key)
    if not cfg:
        raise ValueError(f"Unsupported language: {lang_key}")
    return cfg["voice"]

def translate_text(text: str, source_lang_key: str, target_lang_key: str) -> str:
    """Translate text from source language to target language"""
    if not text:
        return ""
    source_code = get_lang_code(source_lang_key)
    target_code = get_lang_code(target_lang_key)
    translated = GoogleTranslator(source=source_code, target=target_code).translate(text)
    return translated or ""

async def synthesize_speech_async(text: str, voice: str, rate: str = "+0%", volume: str = "+0%") -> bytes:
    """Synthesize speech asynchronously using Edge TTS"""
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    audio_buffer = BytesIO()
    async for chunk in communicator.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    return audio_buffer.getvalue()

def synthesize_speech(text: str, lang_key: str, voice: Optional[str] = None) -> bytes:
    """Synthesize speech with fallback to gTTS"""
    selected_voice = get_voice(lang_key, voice)
    # Try Edge TTS first
    try:
        return asyncio.run(synthesize_speech_async(text=text, voice=selected_voice))
    except Exception:
        # Fallback to gTTS when Edge TTS is blocked
        gtts_lang = get_lang_code(lang_key)
        tts = gTTS(text=text, lang=gtts_lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()

# Food Recommendation Model
indian_foods = {
    "delhi": {
        "coords": (28.7041, 77.1025),
        "veg": ["Chole Bhature", "Rajma Chawal", "Paneer Butter Masala"],
        "nonveg": ["Butter Chicken", "Kebabs", "Mutton Korma"]
    },
    "mumbai": {
        "coords": (19.0760, 72.8777),
        "veg": ["Vada Pav", "Pav Bhaji", "Misal Pav"],
        "nonveg": ["Bombil Fry", "Chicken Sukka", "Prawn Curry"]
    },
    "bengaluru": {
        "coords": (12.9716, 77.5946),
        "veg": ["Ragi Mudde", "Bisi Bele Bath", "Mysore Masala Dosa"],
        "nonveg": ["Donne Biryani", "Mangalorean Chicken Curry", "Nati Koli Saaru"]
    },
    "hyderabad": {
        "coords": (17.3850, 78.4867),
        "veg": ["Bagara Baingan", "Mirchi ka Salan", "Khatti Dal"],
        "nonveg": ["Hyderabadi Biryani", "Mutton Curry", "Chicken 65"]
    },
    "kolkata": {
        "coords": (22.5726, 88.3639),
        "veg": ["Shukto", "Aloo Posto", "Beguni"],
        "nonveg": ["Macher Jhol", "Kosha Mangsho", "Prawn Malai Curry"]
    },
    "chennai": {
        "coords": (13.0827, 80.2707),
        "veg": ["Sambar", "Curd Rice", "Masala Dosa"],
        "nonveg": ["Chettinad Chicken", "Fish Curry", "Mutton Biryani"]
    },
    "ahmedabad": {
        "coords": (23.0225, 72.5714),
        "veg": ["Dhokla", "Undhiyu", "Sev Khamani"],
        "nonveg": ["Mutton Pulao", "Chicken Handi", "Egg Curry"]
    },
    "pune": {
        "coords": (18.5204, 73.8567),
        "veg": ["Misal Pav", "Pithla Bhakri", "Sabudana Khichdi"],
        "nonveg": ["Kolhapuri Chicken", "Mutton Rassa", "Tambada Pandhra Rassa"]
    },
    "lucknow": {
        "coords": (26.8467, 80.9462),
        "veg": ["Tehri", "Bedmi Poori", "Paneer Pasanda"],
        "nonveg": ["Tunday Kebab", "Galouti Kebab", "Awadhi Biryani"]
    },
    "jaipur": {
        "coords": (26.9124, 75.7873),
        "veg": ["Dal Baati Churma", "Ker Sangri", "Gatte ki Sabzi"],
        "nonveg": ["Laal Maas", "Jungli Maas", "Kheema Baati"]
    },
    "kochi": {
        "coords": (9.9312, 76.2673),
        "veg": ["Avial", "Thoran", "Olan"],
        "nonveg": ["Meen Curry", "Karimeen Pollichathu", "Prawn Roast"]
    },
    "visakhapatnam": {
        "coords": (17.6868, 83.2185),
        "veg": ["Pulihora", "Gutti Vankaya Curry", "Pesara Pappu"],
        "nonveg": ["Royyala Iguru", "Chepala Pulusu", "Chicken Fry"]
    },
    "bhubaneswar": {
        "coords": (20.2961, 85.8245),
        "veg": ["Dalma", "Pakhala Bhata", "Santula"],
        "nonveg": ["Macha Besara", "Chuna Macha Tarkari", "Mutton Curry"]
    },
    "udaipur": {
        "coords": (24.5854, 73.7125),
        "veg": ["Dal Baati", "Mirchi Vada", "Aloo Tikki"],
        "nonveg": ["Laal Maas", "Egg Curry", "Mutton Curry"]
    },
    "madurai": {
        "coords": (9.9252, 78.1198),
        "veg": ["Idiyappam", "Onion Uttapam", "Kootu"],
        "nonveg": ["Madurai Kari Dosai", "Mutton Chukka", "Chicken Chettinad"]
    },
    "mysuru": {
        "coords": (12.2958, 76.6394),
        "veg": ["Mysore Pak", "Set Dosa", "Bisi Bele Bath"],
        "nonveg": ["Mysore Mutton Curry", "Chicken Ghee Roast", "Fish Fry"]
    },
    "rajahmundry": {
        "coords": (17.0005, 81.8040),
        "veg": ["Avakai Pachadi", "Gongura Pappu", "Pulihora"],
        "nonveg": ["Gongura Mutton", "Fish Pulusu", "Royyala Vepudu"]
    },
}

def haversine(coord1, coord2):
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth radius in km
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_nearest_city(city):
    """Find the nearest city in our dataset"""
    # Try direct match first
    if city.lower() in indian_foods:
        return city.lower()

    # If not found, calculate distance to nearest city
    try:
        geolocator = Nominatim(user_agent="tourism_food_finder")
        location = geolocator.geocode(city)
        if not location:
            return None

        input_coords = (location.latitude, location.longitude)
        nearest_city = None
        min_dist = float("inf")

        for c, data in indian_foods.items():
            dist = haversine(input_coords, data["coords"])
            if dist < min_dist:
                min_dist = dist
                nearest_city = c

        return nearest_city
    except Exception:
        return None

def get_food_recommendations(city):
    """Get food recommendations for a city"""
    nearest = get_nearest_city(city)
    if not nearest:
        return None, None, None

    foods = indian_foods[nearest]
    return nearest, foods["veg"][:3], foods["nonveg"][:3]

# Gemini AI Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDpreWSSGLb7SD6nnJR-zKK0RQB1bY5cRY")
if genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        pass

def get_available_models():
    """Get list of available Gemini models"""
    if not genai:
        return ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        return available_models
    except Exception as e:
        print(f"Error getting models: {e}")
        return ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

# Location Blog Chatbot Model
def get_location_blog_info(location):
    """Get comprehensive location information using Gemini AI"""
    if not genai:
        return None
    # Try different model names in order of preference
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.5-flash']
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""
            You are a comprehensive travel guide and tourism expert. Provide detailed information about {location} in a structured, blog-style format. Include the following sections:

            ## Overview & Introduction
            - Brief introduction to the place
            - Geographic location and significance
            - Why it's worth visiting

            ## Historical Background
            - Historical significance and timeline
            - Important historical events
            - Cultural heritage and traditions
            - Famous historical figures associated with the place

            ## Tourist Attractions & Landmarks
            - Major tourist attractions
            - Historical monuments and sites
            - Natural attractions
            - Religious and spiritual sites
            - Museums and cultural centers

            ## Local Culture & Traditions
            - Local customs and traditions
            - Festivals and celebrations
            - Art, music, and dance forms
            - Local handicrafts and specialties

            ## Food & Cuisine
            - Local specialties and traditional dishes
            - Popular restaurants and food streets
            - Street food recommendations
            - Dietary considerations

            ## Rules, Regulations & Important Information
            - Entry fees and timings for major attractions
            - Photography rules and restrictions
            - Dress codes for religious sites
            - Local laws and regulations tourists should know
            - Safety guidelines and precautions
            - Emergency contact information

            ## Transportation & Getting Around
            - How to reach the destination
            - Local transportation options
            - Best time to visit
            - Weather conditions and seasons

            ## Accommodation & Stay
            - Types of accommodation available
            - Popular areas to stay
            - Budget considerations

            ## Shopping & Souvenirs
            - Local markets and shopping areas
            - Traditional handicrafts and souvenirs
            - Bargaining tips

            ## Travel Tips & Recommendations
            - Best time to visit
            - Duration of stay recommendations
            - Budget planning tips
            - Local customs to respect
            - Language considerations

            ## Safety & Health
            - Health precautions
            - Safety tips for tourists
            - Emergency services
            - Important contact numbers

            Please provide accurate, up-to-date, and comprehensive information. Format the response in clear sections with proper headings. Make it engaging and informative for tourists planning to visit {location}.
            """
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"Model {model_name} failed: {str(e)}")
            continue
    
    # If all models fail, return a helpful error message
    return f"""# Error: Unable to generate location information

We're currently experiencing issues with our AI service. Please try again in a few moments.

**Alternative suggestions:**
- Check your internet connection
- Try a different location name
- Contact support if the issue persists

**Available models tried:** {', '.join(model_names)}

**Error details:** All models failed to respond. This might be due to API rate limits or temporary service issues."""

# Add built-in Python functions to Jinja2 environment
app.jinja_env.globals.update(min=min, max=max, len=len, range=range)

def generate_booking_reference():
    """Generate a unique booking reference"""
    while True:
        ref = 'BK' + ''.join(random.choices(string.digits, k=8))
        if not Booking.query.filter_by(booking_reference=ref).first():
            return ref

def generate_vehicle_booking_reference():
    """Generate a unique vehicle booking reference"""
    while True:
        ref = 'VB' + ''.join(random.choices(string.digits, k=8))
        if not VehicleBooking.query.filter_by(booking_reference=ref).first():
            return ref

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    approved_hotels = Hotel.query.filter_by(is_approved=True).limit(6).all()
    return render_template('index.html', hotels=approved_hotels)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form.get('phone')
        role = request.form.get('role', 'user')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username'].strip()
        password = request.form['password']
        
        # Accept either username or email (form label says "Username or Email")
        user = User.query.filter(
            or_(User.username == username_or_email, User.email == username_or_email)
        ).first()
        
        if user and user.password_hash == password:
            login_user(user)
            next_page = request.args.get('next')
            
            # Check if vehicle rental owner needs to complete profile
            if user.role == 'vehicle_rental' and not user.profile_completed:
                return redirect(url_for('complete_vehicle_owner_profile'))
            
            # Check if hotel owner needs to complete profile
            if user.role == 'hotel' and not user.profile_completed:
                return redirect(url_for('complete_hotel_profile'))
            
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'superadmin':
        return redirect(url_for('superadmin_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'hotel':
        return redirect(url_for('hotel_dashboard'))
    elif current_user.role == 'vehicle_rental':
        return redirect(url_for('vehicle_rental_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Get both hotel and vehicle bookings
    hotel_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    vehicle_bookings = VehicleBooking.query.filter_by(user_id=current_user.id).order_by(VehicleBooking.created_at.desc()).all()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    
    # Combine all bookings for stats
    all_bookings = list(hotel_bookings) + list(vehicle_bookings)
    
    # Get total complaints count for display
    total_complaints = Complaint.query.filter_by(public_visibility=True).count()
    
    return render_template('user_dashboard.html', 
                         hotel_bookings=hotel_bookings, 
                         vehicle_bookings=vehicle_bookings, 
                         bookings=all_bookings,
                         wishlist_items=wishlist_items,
                         total_complaints=total_complaints)

@app.route('/manage-bookings')
@login_required
def manage_bookings():
    if current_user.role != 'user':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Get both hotel and vehicle bookings
    hotel_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    vehicle_bookings = VehicleBooking.query.filter_by(user_id=current_user.id).order_by(VehicleBooking.created_at.desc()).all()
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    
    return render_template('manage_bookings.html', 
                         hotel_bookings=hotel_bookings, 
                         vehicle_bookings=vehicle_bookings, 
                         wishlist_items=wishlist_items)

@app.route('/complete-hotel-profile', methods=['GET', 'POST'])
@login_required
def complete_hotel_profile():
    """Complete hotel owner profile"""
    # Check if user is a hotel owner
    if current_user.role != 'hotel':
        flash('Access denied. Please login as a hotel owner.', 'error')
        return redirect(url_for('login'))
    
    # If profile is already completed, redirect to dashboard
    if current_user.profile_completed:
        return redirect(url_for('hotel_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        email = request.form['email']
        website = request.form.get('website')
        category = request.form['category']
        # Handle amenities - get all selected amenities as a list
        amenities_list = request.form.getlist('amenities')
        amenities = json.dumps(amenities_list)
        # Set default values for price and rooms (will be managed through room types later)
        price_per_night = 0.0  # Default price, actual prices will be set per room type
        total_rooms = 0  # Default rooms, actual count will be sum of all room types
        
        # Handle hotel image upload
        hotel_image = None
        if 'hotel_image' in request.files:
            file = request.files['hotel_image']
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(app.static_folder, 'uploads', 'hotels')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                filename = f"hotel_{int(time.time())}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                hotel_image = f"uploads/hotels/{filename}"
        
        hotel = Hotel(
            name=name,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            phone=phone,
            email=email,
            website=website,
            category=category,
            amenities=amenities,
            price_per_night=price_per_night,
            total_rooms=total_rooms,
            available_rooms=total_rooms,  # Will be updated when room types are added
            images=hotel_image,  # Store the image path
            owner_id=current_user.id
        )
        
        db.session.add(hotel)
        
        # Mark profile as completed
        current_user.profile_completed = True
        db.session.commit()
        
        flash('Hotel profile completed successfully! Welcome to TourismHub! Your hotel is now pending approval.', 'success')
        return redirect(url_for('hotel_dashboard'))
    
    return render_template('complete_hotel_profile.html')

@app.route('/hotel/dashboard')
@login_required
def hotel_dashboard():
    if current_user.role != 'hotel':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Check if profile is completed
    if not current_user.profile_completed:
        return redirect(url_for('complete_hotel_profile'))
    
    hotels = Hotel.query.filter_by(owner_id=current_user.id).all()
    bookings = Booking.query.join(Hotel).filter(Hotel.owner_id == current_user.id).order_by(Booking.created_at.desc()).all()
    
    # Calculate total rooms count from all room types
    total_rooms = 0
    for hotel in hotels:
        for room_type in hotel.room_types:
            if room_type.is_active:
                total_rooms += room_type.total_rooms
    
    return render_template('hotel_dashboard.html', hotels=hotels, bookings=bookings, total_rooms=total_rooms)

@app.route('/hotel/profile/view')
@login_required
def view_hotel_profile():
    """View hotel profile details"""
    if current_user.role != 'hotel':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Get the hotel owned by current user
    hotel = Hotel.query.filter_by(owner_id=current_user.id).first()
    
    if not hotel:
        flash('No hotel profile found. Please complete your hotel profile first.', 'error')
        return redirect(url_for('complete_hotel_profile'))
    
    return render_template('view_hotel_profile.html', hotel=hotel)

@app.route('/hotel/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_hotel_profile():
    """Edit hotel profile details"""
    if current_user.role != 'hotel':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Get the hotel owned by current user
    hotel = Hotel.query.filter_by(owner_id=current_user.id).first()
    
    if not hotel:
        flash('No hotel profile found. Please complete your hotel profile first.', 'error')
        return redirect(url_for('complete_hotel_profile'))
    
    if request.method == 'POST':
        # Update hotel details
        hotel.name = request.form['name']
        hotel.description = request.form['description']
        hotel.address = request.form['address']
        hotel.city = request.form['city']
        hotel.state = request.form['state']
        hotel.country = request.form['country']
        hotel.phone = request.form['phone']
        hotel.email = request.form['email']
        hotel.website = request.form.get('website')
        hotel.category = request.form['category']
        # Handle amenities - get all selected amenities as a list
        amenities_list = request.form.getlist('amenities')
        hotel.amenities = json.dumps(amenities_list)
        
        # Handle hotel image upload
        if 'hotel_image' in request.files:
            file = request.files['hotel_image']
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join(app.static_folder, 'uploads', 'hotels')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generate unique filename
                filename = f"hotel_{int(time.time())}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                hotel.images = f"uploads/hotels/{filename}"
        
        db.session.commit()
        flash('Hotel profile updated successfully!', 'success')
        return redirect(url_for('view_hotel_profile'))
    
    return render_template('edit_hotel_profile.html', hotel=hotel)

@app.route('/hotel/room-types/<int:hotel_id>')
@login_required
def manage_room_types(hotel_id):
    """Manage room types for a hotel"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
    return render_template('manage_room_types.html', hotel=hotel, room_types=room_types)

@app.route('/hotel/add-room-type/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def add_room_type(hotel_id):
    """Add a new room type to a hotel"""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form['description'].strip()
        max_occupancy = int(request.form['max_occupancy'])
        price_per_night = float(request.form['price_per_night'])
        total_rooms = int(request.form['total_rooms'])
        amenities = request.form.getlist('amenities')
        
        # Create room type
        room_type = RoomType(
            hotel_id=hotel_id,
            name=name,
            description=description,
            max_occupancy=max_occupancy,
            price_per_night=price_per_night,
            total_rooms=total_rooms,
            amenities=json.dumps(amenities),
            is_active=True
        )
        
        db.session.add(room_type)
        db.session.commit()
        
        # Initialize availability for next 365 days
        from datetime import date, timedelta
        start_date = date.today()
        for i in range(365):
            current_date = start_date + timedelta(days=i)
            availability = RoomAvailability(
                room_type_id=room_type.id,
                date=current_date,
                available_rooms=total_rooms,
                booked_rooms=0
            )
            db.session.add(availability)
        
        db.session.commit()
        
        flash('Room type added successfully!', 'success')
        return redirect(url_for('manage_room_types', hotel_id=hotel_id))
    
    return render_template('add_room_type.html', hotel=hotel)

@app.route('/hotel/edit-room-type/<int:room_type_id>', methods=['GET', 'POST'])
@login_required
def edit_room_type(room_type_id):
    """Edit a room type"""
    room_type = RoomType.query.get_or_404(room_type_id)
    hotel = room_type.hotel
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        room_type.name = request.form['name'].strip()
        room_type.description = request.form['description'].strip()
        room_type.max_occupancy = int(request.form['max_occupancy'])
        room_type.price_per_night = float(request.form['price_per_night'])
        room_type.total_rooms = int(request.form['total_rooms'])
        room_type.amenities = json.dumps(request.form.getlist('amenities'))
        
        db.session.commit()
        
        flash('Room type updated successfully!', 'success')
        return redirect(url_for('manage_room_types', hotel_id=hotel.id))
    
    return render_template('edit_room_type.html', room_type=room_type, hotel=hotel)

@app.route('/hotel/delete-room-type/<int:room_type_id>')
@login_required
def delete_room_type(room_type_id):
    """Delete a room type (soft delete)"""
    room_type = RoomType.query.get_or_404(room_type_id)
    hotel = room_type.hotel
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    # Soft delete - mark as inactive
    room_type.is_active = False
    db.session.commit()
    
    flash('Room type deleted successfully!', 'success')
    return redirect(url_for('manage_room_types', hotel_id=hotel.id))

@app.route('/hotel/booking/<int:booking_id>/accept')
@login_required
def accept_booking(booking_id):
    """Accept a booking"""
    booking = Booking.query.get_or_404(booking_id)
    hotel = booking.hotel
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'confirmed'
    booking.payment_status = 'paid'  # Assume payment is completed when accepted
    db.session.commit()
    
    flash('Booking accepted successfully!', 'success')
    return redirect(url_for('hotel_dashboard'))

@app.route('/hotel/booking/<int:booking_id>/reject')
@login_required
def reject_booking(booking_id):
    """Reject a booking"""
    booking = Booking.query.get_or_404(booking_id)
    hotel = booking.hotel
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Booking rejected successfully!', 'success')
    return redirect(url_for('hotel_dashboard'))

@app.route('/hotel/booking/<int:booking_id>/complete')
@login_required
def complete_booking(booking_id):
    """Mark booking as completed"""
    booking = Booking.query.get_or_404(booking_id)
    hotel = booking.hotel
    
    # Check if user owns this hotel
    if current_user.role != 'hotel' or hotel.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'completed'
    db.session.commit()
    
    flash('Booking marked as completed!', 'success')
    return redirect(url_for('hotel_dashboard'))

@app.route('/superadmin/dashboard')
@login_required
def superadmin_dashboard():
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    pending_hotels = Hotel.query.filter_by(is_approved=False).all()
    approved_hotels = Hotel.query.filter_by(is_approved=True).all()
    all_hotels = Hotel.query.all()  # Total hotels count
    pending_vehicle_rentals = VehicleRental.query.filter_by(is_approved=False).all()
    approved_vehicle_rentals = VehicleRental.query.filter_by(is_approved=True).all()
    all_users = User.query.all()
    admins = Admin.query.all()
    
    return render_template('superadmin_dashboard.html', 
                         pending_hotels=pending_hotels,
                         approved_hotels=approved_hotels,
                         all_hotels=all_hotels,
                         pending_vehicle_rentals=pending_vehicle_rentals,
                         approved_vehicle_rentals=approved_vehicle_rentals,
                         users=all_users,
                         admins=admins)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    hotels = Hotel.query.filter_by(is_approved=True).all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    
    return render_template('admin_dashboard.html', hotels=hotels, bookings=bookings)

@app.route('/approve_hotel/<int:hotel_id>')
@login_required
def approve_hotel(hotel_id):
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    hotel.is_approved = True
    db.session.commit()
    
    flash(f'Hotel "{hotel.name}" has been approved!', 'success')
    return redirect(url_for('superadmin_dashboard'))

@app.route('/reject_hotel/<int:hotel_id>')
@login_required
def reject_hotel(hotel_id):
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    db.session.delete(hotel)
    db.session.commit()
    
    flash(f'Hotel "{hotel.name}" has been rejected and removed!', 'success')
    return redirect(url_for('superadmin_dashboard'))

@app.route('/approve_vehicle_rental/<int:rental_id>')
@login_required
def approve_vehicle_rental(rental_id):
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    rental = VehicleRental.query.get_or_404(rental_id)
    rental.is_approved = True
    db.session.commit()
    
    flash(f'Vehicle Rental Company "{rental.name}" has been approved!', 'success')
    return redirect(url_for('superadmin_dashboard'))

@app.route('/reject_vehicle_rental/<int:rental_id>')
@login_required
def reject_vehicle_rental(rental_id):
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    rental = VehicleRental.query.get_or_404(rental_id)
    db.session.delete(rental)
    db.session.commit()
    
    flash(f'Vehicle Rental Company "{rental.name}" has been rejected and removed!', 'success')
    return redirect(url_for('superadmin_dashboard'))

@app.route('/add_admin', methods=['POST'])
@login_required
def add_admin():
    if current_user.role != 'superadmin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    user_id = request.form['user_id']
    permissions = request.form.get('permissions', '[]')
    
    # Check if user exists and is not already an admin
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('superadmin_dashboard'))
    
    if user.role in ['admin', 'superadmin']:
        flash('User is already an admin!', 'error')
        return redirect(url_for('superadmin_dashboard'))
    
    # Update user role
    user.role = 'admin'
    
    # Create admin record
    admin = Admin(
        user_id=user_id,
        permissions=permissions,
        created_by=current_user.id
    )
    
    db.session.add(admin)
    db.session.commit()
    
    flash(f'User "{user.username}" has been promoted to admin!', 'success')
    return redirect(url_for('superadmin_dashboard'))

@app.route('/hotels')
def hotels():
    # Get all search parameters
    search = request.args.get('search', '')
    city = request.args.get('city', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=int)
    amenities = request.args.getlist('amenities')
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Build query
    query = Hotel.query.filter_by(is_approved=True)
    
    # Text search
    if search:
        query = query.filter(
            or_(
                Hotel.name.contains(search),
                Hotel.description.contains(search),
                Hotel.city.contains(search),
                Hotel.address.contains(search)
            )
        )
    
    # City filter
    if city:
        query = query.filter_by(city=city)
    
    # Price range filter
    if min_price is not None:
        query = query.filter(Hotel.price_per_night >= min_price)
    if max_price is not None:
        query = query.filter(Hotel.price_per_night <= max_price)
    
    # Rating filter
    if min_rating:
        query = query.filter(Hotel.rating >= min_rating)
    
    # Amenities filter
    if amenities:
        for amenity in amenities:
            query = query.filter(Hotel.amenities.contains(f'"{amenity}"'))
    
    # Sorting
    if sort_by == 'price':
        if sort_order == 'desc':
            query = query.order_by(Hotel.price_per_night.desc())
        else:
            query = query.order_by(Hotel.price_per_night.asc())
    elif sort_by == 'rating':
        if sort_order == 'desc':
            query = query.order_by(Hotel.rating.desc())
        else:
            query = query.order_by(Hotel.rating.asc())
    elif sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(Hotel.name.desc())
        else:
            query = query.order_by(Hotel.name.asc())
    
    hotels = query.all()
    
    # Get filter options
    cities = db.session.query(Hotel.city).filter_by(is_approved=True).distinct().all()
    cities = [city[0] for city in cities]
    
    # Get all unique amenities
    all_amenities = set()
    for hotel in Hotel.query.filter_by(is_approved=True).all():
        if hotel.amenities:
            try:
                hotel_amenities = json.loads(hotel.amenities)
                all_amenities.update(hotel_amenities)
            except:
                pass
    
    return render_template('hotels.html', 
                         hotels=hotels, 
                         cities=cities, 
                         all_amenities=sorted(all_amenities),
                         search=search, 
                         selected_city=city,
                         min_price=min_price,
                         max_price=max_price,
                         min_rating=min_rating,
                         selected_amenities=amenities,
                         sort_by=sort_by,
                         sort_order=sort_order)

@app.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    if not hotel.is_approved:
        flash('Hotel not found!', 'error')
        return redirect(url_for('hotels'))
    
    # Get check-in and check-out dates from query parameters
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    
    # Calculate available rooms based on date range or use total available
    available_rooms = hotel.available_rooms or 0  # Default to total available
    
    if check_in_str and check_out_str:
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            
            # Calculate rooms booked during this period
            overlapping_bookings = Booking.query.filter(
                Booking.hotel_id == hotel_id,
                Booking.status.in_(['pending', 'confirmed']),
                Booking.check_in < check_out,
                Booking.check_out > check_in
            ).all()
            
            # Calculate total rooms booked during this period
            total_booked = sum(booking.rooms for booking in overlapping_bookings)
            available_rooms = max(0, hotel.total_rooms - total_booked)
            
        except ValueError:
            # Invalid date format, use default
            pass
    
    # Ensure available_rooms is never None
    if available_rooms is None:
        available_rooms = hotel.total_rooms
    
    # Get room types for this hotel
    room_types = RoomType.query.filter_by(hotel_id=hotel_id, is_active=True).all()
    
    # Get reviews for this hotel (ordered by most recent)
    reviews = Review.query.filter_by(hotel_id=hotel_id, is_verified=True).order_by(Review.created_at.desc()).all()
    
    return render_template('hotel_detail.html', hotel=hotel, available_rooms=available_rooms, room_types=room_types, reviews=reviews)

@app.route('/book-room/<int:room_type_id>', methods=['GET', 'POST'])
@login_required
def book_room_type(room_type_id):
    """Book a specific room type"""
    if current_user.role != 'user':
        flash('Only regular users can book rooms!', 'error')
        return redirect(url_for('index'))
    
    room_type = RoomType.query.get_or_404(room_type_id)
    hotel = room_type.hotel
    
    if not hotel.is_approved:
        flash('Hotel not available for booking!', 'error')
        return redirect(url_for('hotels'))
    
    if request.method == 'POST':
        check_in_str = request.form['check_in']
        check_out_str = request.form['check_out']
        rooms = int(request.form['rooms'])
        guests = int(request.form['guests'])
        special_requests = request.form.get('special_requests', '').strip()
        
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format!', 'error')
            return redirect(url_for('book_room_type', room_type_id=room_type_id))
        
        if check_in >= check_out:
            flash('Check-out date must be after check-in date!', 'error')
            return redirect(url_for('book_room_type', room_type_id=room_type_id))
        
        if check_in < date.today():
            flash('Check-in date cannot be in the past!', 'error')
            return redirect(url_for('book_room_type', room_type_id=room_type_id))
        
        # Check availability for the selected dates
        nights = (check_out - check_in).days
        total_amount = nights * rooms * room_type.price_per_night
        
        # Check if enough rooms are available
        overlapping_bookings = Booking.query.filter(
            Booking.room_type_id == room_type_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).all()
        
        total_booked = sum(booking.rooms for booking in overlapping_bookings)
        total_rooms = room_type.total_rooms or 0
        available_rooms = max(0, total_rooms - total_booked)
        
        if rooms > available_rooms:
            flash(f'Only {available_rooms} rooms available for the selected dates!', 'error')
            return redirect(url_for('book_room_type', room_type_id=room_type_id))
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            hotel_id=hotel.id,
            room_type_id=room_type_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
            guests=guests,
            total_amount=total_amount,
            status='pending',
            payment_status='pending',
            special_requests=special_requests,
            booking_reference=generate_booking_reference()
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Booking created successfully! Please complete payment to confirm your reservation.', 'success')
        return redirect(url_for('booking_confirmation', booking_id=booking.id))
    
    # GET request - show booking form
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    rooms = request.args.get('rooms', '1')
    guests = request.args.get('guests', '2')
    
    return render_template('book_room_type.html', 
                         room_type=room_type, 
                         hotel=hotel,
                         check_in=check_in,
                         check_out=check_out,
                         rooms=rooms,
                         guests=guests)

@app.route('/book/<int:hotel_id>', methods=['GET', 'POST'])
@login_required
def book_hotel(hotel_id):
    if current_user.role != 'user':
        flash('Only users can book hotels!', 'error')
        return redirect(url_for('index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    if not hotel.is_approved:
        flash('Hotel not available for booking!', 'error')
        return redirect(url_for('hotels'))
    
    if request.method == 'POST':
        check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()
        rooms = int(request.form['rooms'])
        guests = int(request.form['guests'])
        special_requests = request.form.get('special_requests', '')
        
        # Validate dates
        if check_in >= check_out:
            flash('Check-out date must be after check-in date!', 'error')
            available_rooms = hotel.available_rooms or 0 or 0
            return render_template('book_hotel.html', hotel=hotel, available_rooms=available_rooms)
        
        if check_in < date.today():
            flash('Check-in date cannot be in the past!', 'error')
            available_rooms = hotel.available_rooms or 0 or 0
            return render_template('book_hotel.html', hotel=hotel, available_rooms=available_rooms)
        
        # Check room availability for the specific date range
        overlapping_bookings = Booking.query.filter(
            Booking.hotel_id == hotel_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).all()
        
        total_booked = sum(booking.rooms for booking in overlapping_bookings)
        total_rooms = hotel.total_rooms or 0
        available_rooms = max(0, total_rooms - total_booked)
        
        if rooms > available_rooms:
            flash(f'Only {available_rooms} rooms available for the selected dates!', 'error')
            return render_template('book_hotel.html', hotel=hotel, available_rooms=available_rooms)
        
        # Calculate total amount
        nights = (check_out - check_in).days
        total_amount = nights * rooms * hotel.price_per_night
        
        # Generate booking reference
        booking_ref = generate_booking_reference()
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            hotel_id=hotel.id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
            guests=guests,
            total_amount=total_amount,
            special_requests=special_requests,
            booking_reference=booking_ref,
            status='confirmed',  # Auto-confirm for demo
            payment_status='paid'  # Simulate payment
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash(f'Booking successful! Your booking reference is: {booking_ref}', 'success')
        return redirect(url_for('booking_confirmation', booking_id=booking.id))
    
    # Calculate current available rooms for display
    available_rooms = hotel.available_rooms or 0
    return render_template('book_hotel.html', hotel=hotel, available_rooms=available_rooms)

@app.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    """Show booking confirmation page"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.user_id != current_user.id and current_user.role not in ['admin', 'superadmin']:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    return render_template('booking_confirmation.html', booking=booking)

@app.route('/wishlist/add/<int:hotel_id>')
@login_required
def add_to_wishlist(hotel_id):
    """Add hotel to user's wishlist"""
    if current_user.role != 'user':
        flash('Access denied! Only regular users can use wishlist.', 'error')
        return redirect(url_for('index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=current_user.id, hotel_id=hotel_id).first()
    if existing:
        flash('Hotel already in your wishlist!', 'info')
    else:
        wishlist_item = Wishlist(user_id=current_user.id, hotel_id=hotel_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Hotel added to wishlist!', 'success')
    
    return redirect(request.referrer or url_for('hotels'))

@app.route('/wishlist/remove/<int:hotel_id>')
@login_required
def remove_from_wishlist(hotel_id):
    """Remove hotel from user's wishlist"""
    if current_user.role != 'user':
        flash('Access denied! Only regular users can use wishlist.', 'error')
        return redirect(url_for('index'))
    
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, hotel_id=hotel_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Hotel removed from wishlist!', 'success')
    
    return redirect(request.referrer or url_for('user_dashboard'))


@app.route('/itinerary-generator', methods=['GET', 'POST'])
def itinerary_generator():
    """Itinerary feature removed; redirect to home."""
    return redirect(url_for('index'))


@app.route('/api/room-availability/<int:hotel_id>')
def check_room_availability(hotel_id):
    """API endpoint to check room availability for specific dates"""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    
    if not check_in_str or not check_out_str:
        return jsonify({'error': 'Check-in and check-out dates are required'}), 400
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        hotel = Hotel.query.get_or_404(hotel_id)
        
        # Calculate rooms booked during this period
        overlapping_bookings = Booking.query.filter(
            Booking.hotel_id == hotel_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).all()
        
        # Calculate total rooms booked during this period
        total_booked = sum(booking.rooms for booking in overlapping_bookings)
        available_rooms = max(0, hotel.total_rooms - total_booked)
        
        return jsonify({
            'available_rooms': available_rooms,
            'total_rooms': hotel.total_rooms,
            'booked_rooms': total_booked
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/room-type-availability/<int:room_type_id>')
def check_room_type_availability(room_type_id):
    """API endpoint to check room type availability for specific dates"""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    
    if not check_in_str or not check_out_str:
        return jsonify({'error': 'Check-in and check-out dates are required'}), 400
    
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        room_type = RoomType.query.get_or_404(room_type_id)
        
        # Get all overlapping bookings for this room type
        overlapping_bookings = Booking.query.filter(
            Booking.room_type_id == room_type_id,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).all()
        
        # Calculate availability for each date in the range
        availability_data = []
        current_date = check_in
        min_available = float('inf')
        
        while current_date < check_out:
            # Count rooms booked on this specific date
            rooms_booked_on_date = 0
            for booking in overlapping_bookings:
                # Check if this booking overlaps with the current date
                if booking.check_in <= current_date < booking.check_out:
                    rooms_booked_on_date += booking.rooms
            
            # Calculate available rooms for this date
            total_rooms = room_type.total_rooms or 0
            available_rooms = max(0, total_rooms - rooms_booked_on_date)
            min_available = min(min_available, available_rooms)
            
            availability_data.append({
                'date': current_date.isoformat(),
                'available_rooms': available_rooms,
                'total_rooms': room_type.total_rooms,
                'booked_rooms': rooms_booked_on_date
            })
            
            current_date += timedelta(days=1)
        
        # Ensure min_available is not infinity
        if min_available == float('inf'):
            min_available = 0
        
        return jsonify({
            'room_type_id': room_type_id,
            'room_type_name': room_type.name,
            'max_available_rooms': max(0, min_available),
            'total_rooms': room_type.total_rooms,
            'price_per_night': room_type.price_per_night,
            'max_occupancy': room_type.max_occupancy,
            'availability_by_date': availability_data,
            'check_in': check_in.isoformat(),
            'check_out': check_out.isoformat(),
            'overlapping_bookings_count': len(overlapping_bookings)
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle-availability/<int:vehicle_id>')
def check_vehicle_availability(vehicle_id):
    """API endpoint to check vehicle availability for specific dates"""
    pickup_date_str = request.args.get('pickup_date')
    return_date_str = request.args.get('return_date')
    
    if not pickup_date_str or not return_date_str:
        return jsonify({'error': 'Pickup and return dates are required'}), 400
    
    try:
        pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
        
        vehicle = Vehicle.query.get_or_404(vehicle_id)
        
        # Get all overlapping bookings for this vehicle
        # A booking overlaps if it starts before the requested end date AND ends after the requested start date
        overlapping_bookings = VehicleBooking.query.filter(
            VehicleBooking.vehicle_id == vehicle_id,
            VehicleBooking.status.in_(['pending', 'confirmed']),
            VehicleBooking.pickup_date < return_date,
            VehicleBooking.return_date > pickup_date
        ).all()
        
        # Calculate availability for each date in the range
        availability_data = []
        current_date = pickup_date
        min_available = float('inf')
        
        while current_date < return_date:
            # Count vehicle slots booked on this specific date (sum of quantity)
            vehicles_booked_on_date = 0
            for booking in overlapping_bookings:
                if booking.pickup_date <= current_date < booking.return_date:
                    vehicles_booked_on_date += getattr(booking, 'quantity', 1)
            
            # Calculate available vehicles for this date
            available_vehicles = max(0, vehicle.total_vehicles - vehicles_booked_on_date)
            min_available = min(min_available, available_vehicles)
            
            availability_data.append({
                'date': current_date.isoformat(),
                'available_vehicles': available_vehicles,
                'total_vehicles': vehicle.total_vehicles,
                'booked_vehicles': vehicles_booked_on_date
            })
            
            current_date += timedelta(days=1)
        
        # Ensure min_available is not infinity
        if min_available == float('inf'):
            min_available = 0
        
        return jsonify({
            'vehicle_id': vehicle_id,
            'vehicle_name': f"{vehicle.make} {vehicle.model}",
            'max_available_vehicles': max(0, min_available),
            'total_vehicles': vehicle.total_vehicles,
            'price_per_day': vehicle.price_per_day,
            'price_per_hour': vehicle.price_per_hour,
            'availability_by_date': availability_data,
            'pickup_date': pickup_date.isoformat(),
            'return_date': return_date.isoformat(),
            'overlapping_bookings_count': len(overlapping_bookings)
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cancel_booking/<int:booking_id>')
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
# Hotel Review Routes
@app.route('/hotel/<int:hotel_id>/review', methods=['GET', 'POST'])
@login_required
def submit_hotel_review(hotel_id):
    """Submit a review for a hotel"""
    if current_user.role != 'user':
        flash('Only regular users can submit reviews!', 'error')
        return redirect(url_for('index'))
    
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        title = request.form.get('title', '').strip()
        comment = request.form.get('comment', '').strip()
        booking_id = request.form.get('booking_id')
        
        # Validate rating
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars!', 'error')
            return redirect(url_for('submit_hotel_review', hotel_id=hotel_id))
        
        # Check if user has already reviewed this hotel
        existing_review = Review.query.filter_by(
            user_id=current_user.id,
            hotel_id=hotel_id
        ).first()
        
        if existing_review:
            flash('You have already reviewed this hotel!', 'error')
            return redirect(url_for('hotel_detail', hotel_id=hotel_id))
        
        # Check if user has a completed booking for this hotel
        if booking_id:
            booking = Booking.query.filter_by(
                id=booking_id,
                user_id=current_user.id,
                hotel_id=hotel_id,
                status='completed'
            ).first()
            if not booking:
                flash('Invalid booking reference!', 'error')
                return redirect(url_for('submit_hotel_review', hotel_id=hotel_id))
        else:
            # Check if user has any completed booking for this hotel
            booking = Booking.query.filter_by(
                user_id=current_user.id,
                hotel_id=hotel_id,
                status='completed'
            ).first()
            if not booking:
                flash('You can only review hotels you have stayed at!', 'error')
                return redirect(url_for('submit_hotel_review', hotel_id=hotel_id))
            booking_id = booking.id
        
        # Create review
        review = Review(
            user_id=current_user.id,
            hotel_id=hotel_id,
            booking_id=booking_id,
            rating=rating,
            title=title,
            comment=comment,
            is_verified=True
        )
        
        db.session.add(review)
        
        # Update hotel rating
        update_hotel_rating(hotel_id)
        
        db.session.commit()
        
        flash('Thank you for your review!', 'success')
        return redirect(url_for('hotel_detail', hotel_id=hotel_id))
    
    # Get user's completed bookings for this hotel
    bookings = Booking.query.filter_by(
        user_id=current_user.id,
        hotel_id=hotel_id,
        status='completed'
    ).all()
    
    return render_template('submit_hotel_review.html', hotel=hotel, bookings=bookings)

@app.route('/vehicle-rental/<int:rental_id>/review', methods=['GET', 'POST'])
@login_required
def submit_vehicle_review(rental_id):
    """Submit a review for a vehicle rental company"""
    if current_user.role != 'user':
        flash('Only regular users can submit reviews!', 'error')
        return redirect(url_for('index'))
    
    rental_company = VehicleRental.query.get_or_404(rental_id)
    
    if request.method == 'POST':
        rating = int(request.form['rating'])
        title = request.form.get('title', '').strip()
        comment = request.form.get('comment', '').strip()
        booking_id = request.form.get('booking_id')
        
        # Validate rating
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars!', 'error')
            return redirect(url_for('submit_vehicle_review', rental_id=rental_id))
        
        # Check if user has already reviewed this rental company
        existing_review = VehicleReview.query.filter_by(
            user_id=current_user.id,
            rental_company_id=rental_id
        ).first()
        
        if existing_review:
            flash('You have already reviewed this rental company!', 'error')
            return redirect(url_for('vehicle_rental_detail', rental_id=rental_id))
        
        # Check if user has a completed booking for this rental company
        if booking_id:
            booking = VehicleBooking.query.filter_by(
                id=booking_id,
                user_id=current_user.id,
                rental_company_id=rental_id,
                status='completed'
            ).first()
            if not booking:
                flash('Invalid booking reference!', 'error')
                return redirect(url_for('submit_vehicle_review', rental_id=rental_id))
        else:
            # Check if user has any completed booking for this rental company
            booking = VehicleBooking.query.filter_by(
                user_id=current_user.id,
                rental_company_id=rental_id,
                status='completed'
            ).first()
            if not booking:
                flash('You can only review rental companies you have used!', 'error')
                return redirect(url_for('submit_vehicle_review', rental_id=rental_id))
            booking_id = booking.id
        
        # Create review
        review = VehicleReview(
            user_id=current_user.id,
            rental_company_id=rental_id,
            vehicle_id=booking.vehicle_id,
            booking_id=booking_id,
            rating=rating,
            title=title,
            comment=comment,
            is_verified=True
        )
        
        db.session.add(review)
        
        # Update rental company rating
        update_vehicle_rental_rating(rental_id)
        
        db.session.commit()
        
        flash('Thank you for your review!', 'success')
        return redirect(url_for('vehicle_rental_detail', rental_id=rental_id))
    
    # Get user's completed bookings for this rental company
    bookings = VehicleBooking.query.filter_by(
        user_id=current_user.id,
        rental_company_id=rental_id,
        status='completed'
    ).all()
    
    return render_template('submit_vehicle_review.html', rental_company=rental_company, bookings=bookings)

def update_hotel_rating(hotel_id):
    """Update hotel's average rating and total reviews count"""
    hotel = Hotel.query.get(hotel_id)
    if not hotel:
        return
    
    reviews = Review.query.filter_by(hotel_id=hotel_id, is_verified=True).all()
    
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        average_rating = total_rating / len(reviews)
        hotel.rating = round(average_rating, 1)
        hotel.total_reviews = len(reviews)
    else:
        hotel.rating = 0.0
        hotel.total_reviews = 0
    
    db.session.commit()

def update_vehicle_rental_rating(rental_id):
    """Update vehicle rental company's average rating and total reviews count"""
    rental_company = VehicleRental.query.get(rental_id)
    if not rental_company:
        return
    
    reviews = VehicleReview.query.filter_by(rental_company_id=rental_id, is_verified=True).all()
    
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        average_rating = total_rating / len(reviews)
        rental_company.rating = round(average_rating, 1)
        rental_company.total_reviews = len(reviews)
    else:
        rental_company.rating = 0.0
        rental_company.total_reviews = 0
    
    db.session.commit()
    
    flash('Booking cancelled successfully!', 'success')
    return redirect(url_for('user_dashboard'))

# Initialize database and create superadmin
def init_db():
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            import sys
            print(f"init_db create_all: {e}", file=sys.stderr, flush=True)
        try:
            superadmin = User.query.filter_by(username='superadmin').first()
            if not superadmin:
                superadmin = User(
                    username='superadmin',
                    email='admin@tourism.com',
                    password_hash=os.environ.get('SUPERADMIN_PASSWORD', 'admin123'),
                    first_name='Super',
                    last_name='Admin',
                    role='superadmin'
                )
                db.session.add(superadmin)
                db.session.commit()
                import sys
                print("Superadmin created: username='superadmin', password from env or admin123", file=sys.stderr, flush=True)
        except Exception as e:
            db.session.rollback()
            import sys
            print(f"init_db superadmin: {e}", file=sys.stderr, flush=True)
        try:
            vapi_guest = User.query.filter_by(username='vapi_guest').first()
            if not vapi_guest:
                vapi_guest = User(
                    username='vapi_guest',
                    email='vapi@tourism.local',
                    password_hash='vapi_voice_booking',
                    first_name='Voice',
                    last_name='Guest',
                    role='user',
                    profile_completed=True
                )
                db.session.add(vapi_guest)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            import sys
            print(f"init_db vapi_guest: {e}", file=sys.stderr, flush=True)
        try:
            db.session.execute(text('ALTER TABLE vehicle_booking ADD COLUMN quantity INTEGER NOT NULL DEFAULT 1'))
            db.session.commit()
        except Exception:
            db.session.rollback()


# Vehicle Rental Routes
@app.route('/vehicle-rentals')
def vehicle_rentals():
    """Vehicle rentals listing page"""
    # Get search and filter parameters
    search = request.args.get('search', '').strip()
    city = request.args.get('city', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    vehicle_type = request.args.get('vehicle_type', '').strip()
    transmission = request.args.get('transmission', '').strip()
    fuel_type = request.args.get('fuel_type', '').strip()
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Build query - Show vehicles only from approved rental companies
    query = VehicleRental.query.filter_by(is_approved=True)
    
    # Apply filters
    if search:
        # Search in rental company details and also in their vehicles
        search_conditions = [
            VehicleRental.name.ilike(f'%{search}%'),
            VehicleRental.city.ilike(f'%{search}%'),
            VehicleRental.description.ilike(f'%{search}%')
        ]
        
        # Also search in vehicle make and model
        vehicle_search_rentals = db.session.query(VehicleRental.id).join(Vehicle).filter(
            or_(
                Vehicle.make.ilike(f'%{search}%'),
                Vehicle.model.ilike(f'%{search}%')
            )
        ).subquery()
        
        search_conditions.append(VehicleRental.id.in_(db.session.query(vehicle_search_rentals.c.id)))
        
        query = query.filter(or_(*search_conditions))
    
    if city:
        query = query.filter(VehicleRental.city.ilike(f'%{city}%'))
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(VehicleRental.name.asc() if sort_order == 'asc' else VehicleRental.name.desc())
    elif sort_by == 'rating':
        query = query.order_by(VehicleRental.rating.desc() if sort_order == 'desc' else VehicleRental.rating.asc())
    elif sort_by == 'city':
        query = query.order_by(VehicleRental.city.asc() if sort_order == 'asc' else VehicleRental.city.desc())
    elif sort_by == 'price':
        # For price sorting, we'll need to join with vehicles and sort by min price
        query = query.order_by(VehicleRental.name.asc())  # Default fallback
    
    rentals = query.all()
    
    # Get available vehicles for each rental and apply vehicle-level filters
    filtered_rentals = []
    for rental in rentals:
        vehicle_query = Vehicle.query.filter_by(
            rental_company_id=rental.id,
            is_active=True
        )
        
        # Apply vehicle-level filters
        if vehicle_type:
            vehicle_query = vehicle_query.filter_by(vehicle_type=vehicle_type)
        if transmission:
            vehicle_query = vehicle_query.filter_by(transmission=transmission)
        if fuel_type:
            vehicle_query = vehicle_query.filter_by(fuel_type=fuel_type)
        if min_price:
            vehicle_query = vehicle_query.filter(Vehicle.price_per_day >= min_price)
        if max_price:
            vehicle_query = vehicle_query.filter(Vehicle.price_per_day <= max_price)
        
        available_vehicles = vehicle_query.all()
        
        # Only include rental if it has vehicles matching the filters
        if available_vehicles:
            rental.vehicles = available_vehicles
            filtered_rentals.append(rental)
    
    # Get cities for filter dropdown
    cities = db.session.query(VehicleRental.city).filter_by(is_approved=True).distinct().all()
    cities = [city[0] for city in cities if city[0]]
    
    return render_template('vehicle_rentals.html', 
                         rentals=filtered_rentals,
                         search=search,
                         city=city,
                         min_price=min_price,
                         max_price=max_price,
                         vehicle_type=vehicle_type,
                         transmission=transmission,
                         fuel_type=fuel_type,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         cities=cities)

@app.route('/vehicle-rental/<int:rental_id>')
def vehicle_rental_detail(rental_id):
    """Vehicle rental detail page"""
    rental = VehicleRental.query.get_or_404(rental_id)
    
    # Get available vehicles
    available_vehicles = Vehicle.query.filter_by(
        rental_company_id=rental_id,
        is_active=True
    ).all()
    
    # Get pickup and return dates from query parameters
    pickup_date = request.args.get('pickup_date')
    return_date = request.args.get('return_date')
    
    return render_template('vehicle_rental_detail.html', 
                         rental=rental,
                         vehicles=available_vehicles,
                         pickup_date=pickup_date,
                         return_date=return_date)

@app.route('/book-vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def book_vehicle(vehicle_id):
    """Book a vehicle"""
    if current_user.role != 'user':
        flash('Access denied! Only regular users can book vehicles.', 'error')
        return redirect(url_for('index'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    rental = vehicle.rental_company
    
    if request.method == 'POST':
        pickup_date = datetime.strptime(request.form['pickup_date'], '%Y-%m-%d').date()
        return_date = datetime.strptime(request.form['return_date'], '%Y-%m-%d').date()
        pickup_time = datetime.strptime(request.form['pickup_time'], '%H:%M').time()
        return_time = datetime.strptime(request.form['return_time'], '%H:%M').time()
        pickup_location = request.form['pickup_location'].strip()
        return_location = request.form['return_location'].strip()
        drivers_license = request.form['drivers_license'].strip()
        drivers_license_expiry = datetime.strptime(request.form['drivers_license_expiry'], '%Y-%m-%d').date()
        special_requests = request.form.get('special_requests', '').strip()
        
        # Validate dates
        if pickup_date >= return_date:
            flash('Return date must be after pickup date', 'error')
            return render_template('book_vehicle.html', vehicle=vehicle, rental=rental)
        
        if pickup_date < date.today():
            flash('Pickup date cannot be in the past', 'error')
            return render_template('book_vehicle.html', vehicle=vehicle, rental=rental)
        
        # Calculate total amount
        days = (return_date - pickup_date).days
        if days == 0:
            days = 1  # Minimum 1 day
        
        num_vehicles = int(request.form.get('num_vehicles', 1))
        num_vehicles = max(1, min(num_vehicles, vehicle.total_vehicles))
        
        total_amount = vehicle.price_per_day * days * num_vehicles
        
        # Check vehicle availability: sum of quantities in overlapping bookings + requested <= total
        overlapping = VehicleBooking.query.filter(
            VehicleBooking.vehicle_id == vehicle_id,
            VehicleBooking.status.in_(['pending', 'confirmed']),
            or_(
                and_(
                    VehicleBooking.pickup_date <= pickup_date,
                    VehicleBooking.return_date > pickup_date
                ),
                and_(
                    VehicleBooking.pickup_date < return_date,
                    VehicleBooking.return_date >= return_date
                ),
                and_(
                    VehicleBooking.pickup_date >= pickup_date,
                    VehicleBooking.return_date <= return_date
                )
            )
        ).all()
        slots_booked = sum(getattr(b, 'quantity', 1) for b in overlapping)
        if slots_booked + num_vehicles > vehicle.total_vehicles:
            flash('Not enough vehicles available for selected dates', 'error')
            return render_template('book_vehicle.html', vehicle=vehicle, rental=rental)
        
        # Create booking
        booking = VehicleBooking(
            user_id=current_user.id,
            rental_company_id=rental.id,
            vehicle_id=vehicle.id,
            quantity=num_vehicles,
            pickup_date=pickup_date,
            return_date=return_date,
            pickup_time=pickup_time,
            return_time=return_time,
            pickup_location=pickup_location,
            return_location=return_location,
            drivers_license=drivers_license,
            drivers_license_expiry=drivers_license_expiry,
            total_amount=total_amount,
            special_requests=special_requests,
            booking_reference=generate_vehicle_booking_reference()
        )
        
        db.session.add(booking)
        db.session.commit()
        
        flash('Vehicle booked successfully!', 'success')
        return redirect(url_for('vehicle_booking_confirmation', booking_id=booking.id))
    
    return render_template('book_vehicle.html', vehicle=vehicle, rental=rental)

@app.route('/vehicle-booking-confirmation/<int:booking_id>')
@login_required
def vehicle_booking_confirmation(booking_id):
    """Vehicle booking confirmation page"""
    booking = VehicleBooking.query.get_or_404(booking_id)
    
    # Ensure user can only view their own bookings
    if booking.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    return render_template('vehicle_booking_confirmation.html', booking=booking)

@app.route('/manage-vehicle-bookings')
@login_required
def manage_vehicle_bookings():
    """Manage vehicle bookings page"""
    if current_user.role != 'user':
        flash('Access denied! Only regular users can manage vehicle bookings.', 'error')
        return redirect(url_for('index'))
    
    bookings = VehicleBooking.query.filter_by(user_id=current_user.id).order_by(VehicleBooking.created_at.desc()).all()
    return render_template('manage_vehicle_bookings.html', bookings=bookings)

@app.route('/complete-vehicle-owner-profile', methods=['GET', 'POST'])
@login_required
def complete_vehicle_owner_profile():
    """Complete vehicle rental owner profile"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # If profile is already completed, redirect to dashboard
    if current_user.profile_completed:
        return redirect(url_for('vehicle_rental_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form.get('description', '').strip()
        address = request.form['address'].strip()
        city = request.form['city'].strip()
        state = request.form['state'].strip()
        country = request.form['country'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        website = request.form.get('website', '').strip()
        amenities = request.form.getlist('amenities')
        
        # Handle profile picture upload
        profile_picture = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                # Save the file
                filename = f"company_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join('static', 'uploads', 'companies', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                profile_picture = f"uploads/companies/{filename}"
        
        # Create rental company
        rental = VehicleRental(
            name=name,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            phone=phone,
            email=email,
            website=website,
            profile_picture=profile_picture,
            amenities=json.dumps(amenities),
            owner_id=current_user.id
        )
        
        db.session.add(rental)
        
        # Mark profile as completed
        current_user.profile_completed = True
        db.session.commit()
        
        flash('Profile completed successfully! Welcome to TourismHub Vehicle Rental!', 'success')
        return redirect(url_for('vehicle_rental_dashboard'))
    
    return render_template('complete_vehicle_owner_profile.html')

@app.route('/vehicle-rental-profile')
@login_required
def vehicle_rental_profile():
    """View and edit vehicle rental company profile"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # Get user's rental company
    rental = VehicleRental.query.filter_by(owner_id=current_user.id).first()
    
    if not rental:
        flash('No rental company found. Please complete your profile first.', 'error')
        return redirect(url_for('complete_vehicle_owner_profile'))
    
    return render_template('vehicle_rental_profile.html', rental=rental)

@app.route('/edit-vehicle-rental-profile', methods=['GET', 'POST'])
@login_required
def edit_vehicle_rental_profile():
    """Edit vehicle rental company profile"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # Get user's rental company
    rental = VehicleRental.query.filter_by(owner_id=current_user.id).first()
    
    if not rental:
        flash('No rental company found. Please complete your profile first.', 'error')
        return redirect(url_for('complete_vehicle_owner_profile'))
    
    if request.method == 'POST':
        # Update rental company information
        rental.name = request.form['company_name']
        rental.description = request.form['description']
        rental.address = request.form['address']
        rental.city = request.form['city']
        rental.state = request.form['state']
        rental.country = request.form['country']
        rental.phone = request.form['phone']
        rental.email = request.form['email']
        rental.website = request.form.get('website', '').strip()
        
        # Handle amenities
        amenities = request.form.getlist('amenities')
        rental.amenities = json.dumps(amenities) if amenities else None
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                print(f"Processing profile picture upload for rental {rental.id}")
                print(f"Original filename: {file.filename}")
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'companies')
                os.makedirs(upload_dir, exist_ok=True)
                print(f"Upload directory: {upload_dir}")
                
                # Generate unique filename (matching complete profile format)
                filename = f"company_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(file.filename)}"
                file_path = os.path.join(upload_dir, filename)
                print(f"New file path: {file_path}")
                
                # Save the new file
                file.save(file_path)
                print(f"File saved successfully")
                
                # Delete old profile picture if exists
                if rental.profile_picture:
                    print(f"Deleting old profile picture: {rental.profile_picture}")
                    # Handle both old format (just filename) and new format (full path)
                    if rental.profile_picture.startswith('uploads/'):
                        old_file_path = os.path.join('static', rental.profile_picture)
                    else:
                        old_file_path = os.path.join('static', 'uploads', 'companies', rental.profile_picture)
                    
                    print(f"Old file path: {old_file_path}")
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                        print(f"Old file deleted successfully")
                    else:
                        print(f"Old file not found, skipping deletion")
                
                # Store the full path in database (matching complete profile format)
                new_profile_path = f"uploads/companies/{filename}"
                rental.profile_picture = new_profile_path
                print(f"Updated profile_picture in database: {new_profile_path}")
        
        try:
            db.session.commit()
            flash('Company profile updated successfully!', 'success')
            return redirect(url_for('vehicle_rental_profile'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
            print(f"Error updating vehicle rental profile: {e}")
    
    # Get available amenities for the form
    available_amenities = [
        '24/7 Customer Support', 'Free Pickup/Drop', 'GPS Navigation', 
        'Child Safety Seats', 'Insurance Coverage', 'Roadside Assistance',
        'Fuel Service', 'Driver Service', 'Airport Transfer', 'City Tour Packages',
        'Long Distance Travel', 'Corporate Bookings', 'Event Transportation',
        'Luxury Vehicles', 'Economy Options', 'Group Bookings'
    ]
    
    # Get current amenities
    current_amenities = []
    if rental.amenities:
        try:
            current_amenities = json.loads(rental.amenities)
        except:
            current_amenities = []
    
    return render_template('edit_vehicle_rental_profile.html', 
                         rental=rental, 
                         available_amenities=available_amenities,
                         current_amenities=current_amenities)

@app.route('/vehicle-rental-dashboard')
@login_required
def vehicle_rental_dashboard():
    """Vehicle rental dashboard"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # Check if profile is completed
    if not current_user.profile_completed:
        return redirect(url_for('complete_vehicle_owner_profile'))
    
    # Get user's rental companies
    rentals = VehicleRental.query.filter_by(owner_id=current_user.id).all()
    
    # Get vehicles count for all rentals
    vehicles_count = 0
    for rental in rentals:
        vehicles_count += Vehicle.query.filter_by(rental_company_id=rental.id).count()
    
    # Get bookings for all rentals
    all_bookings = []
    for rental in rentals:
        bookings = VehicleBooking.query.filter_by(rental_company_id=rental.id).order_by(VehicleBooking.created_at.desc()).all()
        all_bookings.extend(bookings)
    
    return render_template('vehicle_rental_dashboard.html', 
                         rentals=rentals, 
                         bookings=all_bookings,
                         vehicles_count=vehicles_count)

@app.route('/add-vehicle/<int:rental_id>', methods=['GET', 'POST'])
@login_required
def add_vehicle(rental_id):
    """Add a vehicle to a rental company"""
    rental = VehicleRental.query.get_or_404(rental_id)
    
    # Check if user is a vehicle rental owner and owns this rental company
    if current_user.role != 'vehicle_rental' or rental.owner_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('login'))
    
    # Note: Vehicles can be added immediately without company approval
    
    if request.method == 'POST':
        make = request.form['make'].strip()
        model = request.form['model'].strip()
        year = int(request.form['year'])
        vehicle_type = request.form['vehicle_type'].strip()
        transmission = request.form['transmission'].strip()
        fuel_type = request.form['fuel_type'].strip()
        seating_capacity = int(request.form['seating_capacity'])
        luggage_capacity = request.form.get('luggage_capacity', '').strip()
        mileage = request.form.get('mileage', '').strip()
        features = request.form.getlist('features')
        price_per_day = float(request.form['price_per_day'])
        price_per_hour = float(request.form.get('price_per_hour', 0)) or None
        total_vehicles = int(request.form['total_vehicles'])
        
        # Handle vehicle image upload
        vehicle_image = None
        if 'vehicle_image' in request.files:
            file = request.files['vehicle_image']
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'vehicles')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Generate unique filename
                filename = f"{rental_id}_{make}_{model}_{year}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                vehicle_image = f"uploads/vehicles/{filename}"
        
        # Create vehicle
        vehicle = Vehicle(
            rental_company_id=rental_id,
            make=make,
            model=model,
            year=year,
            vehicle_type=vehicle_type,
            transmission=transmission,
            fuel_type=fuel_type,
            seating_capacity=seating_capacity,
            luggage_capacity=luggage_capacity,
            mileage=mileage,
            features=json.dumps(features),
            price_per_day=price_per_day,
            price_per_hour=price_per_hour,
            total_vehicles=total_vehicles,
            available_vehicles=total_vehicles,
            images=json.dumps([vehicle_image]) if vehicle_image else None
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('vehicle_rental_dashboard'))
    
    return render_template('add_vehicle.html', rental=rental)

@app.route('/view-vehicles')
@login_required
def view_vehicles():
    """View all vehicles for the rental company"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # Check if profile is completed
    if not current_user.profile_completed:
        return redirect(url_for('complete_vehicle_owner_profile'))
    
    # Get user's rental companies
    rentals = VehicleRental.query.filter_by(owner_id=current_user.id).all()
    
    # Get all vehicles for all rentals
    all_vehicles = []
    for rental in rentals:
        vehicles = Vehicle.query.filter_by(rental_company_id=rental.id).all()
        for vehicle in vehicles:
            vehicle.rental_company = rental  # Add rental company info to vehicle
            all_vehicles.append(vehicle)
    
    return render_template('view_vehicles.html', vehicles=all_vehicles, rentals=rentals)

@app.route('/edit-vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    """Edit vehicle details"""
    # Check if user is a vehicle rental owner
    if current_user.role != 'vehicle_rental':
        flash('Access denied. Please login as a vehicle rental owner.', 'error')
        return redirect(url_for('login'))
    
    # Check if profile is completed
    if not current_user.profile_completed:
        return redirect(url_for('complete_vehicle_owner_profile'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    rental = VehicleRental.query.get_or_404(vehicle.rental_company_id)
    
    # Check if user owns this vehicle
    if rental.owner_id != current_user.id:
        flash('Access denied. You can only edit your own vehicles.', 'error')
        return redirect(url_for('view_vehicles'))
    
    if request.method == 'POST':
        vehicle.make = request.form['make'].strip()
        vehicle.model = request.form['model'].strip()
        vehicle.year = int(request.form['year'])
        vehicle.vehicle_type = request.form['vehicle_type'].strip()
        vehicle.transmission = request.form['transmission'].strip()
        vehicle.fuel_type = request.form['fuel_type'].strip()
        vehicle.seating_capacity = int(request.form['seating_capacity'])
        vehicle.luggage_capacity = request.form.get('luggage_capacity', '').strip()
        vehicle.mileage = request.form.get('mileage', '').strip()
        vehicle.features = json.dumps(request.form.getlist('features'))
        vehicle.price_per_day = float(request.form['price_per_day'])
        vehicle.price_per_hour = float(request.form.get('price_per_hour', 0)) or None
        vehicle.total_vehicles = int(request.form['total_vehicles'])
        
        # Handle vehicle image upload (optional update)
        if 'vehicle_image' in request.files:
            file = request.files['vehicle_image']
            if file and file.filename:
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'vehicles')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Generate unique filename
                filename = f"{vehicle.rental_company_id}_{vehicle.make}_{vehicle.model}_{vehicle.year}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                vehicle.images = json.dumps([f"uploads/vehicles/{filename}"])
        
        db.session.commit()
        flash('Vehicle updated successfully!', 'success')
        return redirect(url_for('view_vehicles'))
    
    # Parse features for display
    features_list = []
    if vehicle.features:
        features_list = json.loads(vehicle.features)
    
    return render_template('edit_vehicle.html', vehicle=vehicle, rental=rental, features_list=features_list)

@app.route('/vehicle-rental/booking/<int:booking_id>/accept')
@login_required
def accept_vehicle_booking(booking_id):
    """Accept a vehicle booking"""
    booking = VehicleBooking.query.get_or_404(booking_id)
    rental = booking.vehicle.rental_company
    
    # Check if user owns this rental company
    if current_user.role != 'vehicle_rental' or rental.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'confirmed'
    booking.payment_status = 'paid'  # Assume payment is completed when accepted
    db.session.commit()
    
    flash('Vehicle booking accepted successfully!', 'success')
    return redirect(url_for('vehicle_rental_dashboard'))

@app.route('/vehicle-rental/booking/<int:booking_id>/reject')
@login_required
def reject_vehicle_booking(booking_id):
    """Reject a vehicle booking"""
    booking = VehicleBooking.query.get_or_404(booking_id)
    rental = booking.vehicle.rental_company
    
    # Check if user owns this rental company
    if current_user.role != 'vehicle_rental' or rental.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Vehicle booking rejected successfully!', 'success')
    return redirect(url_for('vehicle_rental_dashboard'))

@app.route('/vehicle-rental/booking/<int:booking_id>/complete')
@login_required
def complete_vehicle_booking(booking_id):
    """Mark vehicle booking as completed"""
    booking = VehicleBooking.query.get_or_404(booking_id)
    rental = booking.vehicle.rental_company
    
    # Check if user owns this rental company
    if current_user.role != 'vehicle_rental' or rental.owner_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    booking.status = 'completed'
    db.session.commit()
    
    flash('Vehicle booking marked as completed!', 'success')
    return redirect(url_for('vehicle_rental_dashboard'))

# Translation API Routes
@app.route('/api/translate', methods=['POST'])
def api_translate():
    """Translate text from source language to target language"""
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "")
    source = payload.get("source", "auto")
    target = payload.get("target", "en")

    # If source is "auto", let Google auto-detect by passing 'auto' directly
    if source == "auto":
        target_code = get_lang_code(target)
        translated = GoogleTranslator(source="auto", target=target_code).translate(text)
    else:
        translated = translate_text(text, source, target)

    return jsonify({
        "ok": True,
        "translated": translated,
    })

@app.route('/api/tts', methods=['POST'])
def api_tts():
    """Convert text to speech"""
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "")
    lang = payload.get("lang", "en")
    voice = payload.get("voice")

    if not text:
        return jsonify({"ok": False, "error": "Missing text"}), 400

    try:
        audio_bytes = synthesize_speech(text=text, lang_key=lang, voice=voice)
        b64_audio = base64.b64encode(audio_bytes).decode("ascii")
        return jsonify({"ok": True, "audio_base64": b64_audio, "mime": "audio/mpeg"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/translate-tts', methods=['POST'])
def api_translate_tts():
    """Translate text and convert to speech"""
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "")
    source = payload.get("source", "en")
    target = payload.get("target", "hi")
    voice = payload.get("voice")

    if not text:
        return jsonify({"ok": False, "error": "Missing text"}), 400

    try:
        translated = translate_text(text, source, target)
        audio_bytes = synthesize_speech(text=translated, lang_key=target, voice=voice)
        b64_audio = base64.b64encode(audio_bytes).decode("ascii")
        return jsonify({
            "ok": True,
            "translated": translated,
            "audio_base64": b64_audio,
            "mime": "audio/mpeg",
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/translator')
def translator():
    """Language translator page"""
    return render_template('translator.html', languages=LANG_CONFIG)

@app.route('/food-recommendations', methods=['GET', 'POST'])
def food_recommendations():
    """Food recommendations page"""
    if request.method == 'POST':
        city = request.form.get('city', '').strip()
        if city:
            nearest_city, veg_foods, nonveg_foods = get_food_recommendations(city)
            if nearest_city:
                return render_template('food_recommendations.html', 
                                     city=city, 
                                     nearest_city=nearest_city,
                                     veg_foods=veg_foods,
                                     nonveg_foods=nonveg_foods,
                                     found=True)
            else:
                return render_template('food_recommendations.html', 
                                     city=city, 
                                     found=False,
                                     error="City not found and no nearby city available.")
        else:
            return render_template('food_recommendations.html', 
                                 error="Please enter a city name.")
    
    return render_template('food_recommendations.html')

@app.route('/api/food-recommendations', methods=['POST'])
def api_food_recommendations():
    """API endpoint for food recommendations"""
    payload = request.get_json(force=True, silent=True) or {}
    city = payload.get("city", "").strip()
    
    if not city:
        return jsonify({"ok": False, "error": "City name is required"}), 400
    
    nearest_city, veg_foods, nonveg_foods = get_food_recommendations(city)
    
    if not nearest_city:
        return jsonify({"ok": False, "error": "City not found and no nearby city available"}), 404
    
    return jsonify({
        "ok": True,
        "city": city,
        "nearest_city": nearest_city,
        "veg_foods": veg_foods,
        "nonveg_foods": nonveg_foods
    })

@app.route('/location-blog', methods=['GET', 'POST'])
def location_blog():
    """Location blog chatbot page"""
    if request.method == 'POST':
        location = request.form.get('location', '').strip()
        if location:
            try:
                blog_content = get_location_blog_info(location)
                return render_template('location_blog.html', 
                                     location=location,
                                     blog_content=blog_content,
                                     found=True)
            except Exception as e:
                return render_template('location_blog.html', 
                                     location=location,
                                     found=False,
                                     error=f"Error generating blog content: {str(e)}")
        else:
            return render_template('location_blog.html', 
                                 error="Please enter a location name.")
    
    return render_template('location_blog.html')

@app.route('/api/location-blog', methods=['POST'])
def api_location_blog():
    """API endpoint for location blog generation"""
    payload = request.get_json(force=True, silent=True) or {}
    location = payload.get("location", "").strip()
    
    if not location:
        return jsonify({"ok": False, "error": "Location name is required"}), 400
    
    try:
        blog_content = get_location_blog_info(location)
        return jsonify({
            "ok": True,
            "location": location,
            "blog_content": blog_content
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/test-gemini')
def test_gemini():
    """Test route to verify Gemini API is working"""
    try:
        result = get_location_blog_info("Taj Mahal")
        return f"<h1>Gemini API Test</h1><p>Status: Working</p><pre>{result[:500]}...</pre>"
    except Exception as e:
        return f"<h1>Gemini API Test</h1><p>Status: Error</p><p>{str(e)}</p>"

# Complaint Box Routes
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """Submit a new tourism complaint/feedback"""
    try:
        # Get form data
        title = request.form.get('complaint_title')
        description = request.form.get('complaint_description')
        complaint_type = request.form.get('complaint_type')
        location = request.form.get('location')
        severity = request.form.get('severity', 'medium')
        suggestions = request.form.get('suggestions', '')
        public_visibility = request.form.get('public_visibility') == 'on'
        
        # Validate required fields
        if not all([title, description, complaint_type, location]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Create new complaint
        complaint = Complaint(
            title=title,
            description=description,
            complaint_type=complaint_type,
            location=location,
            severity=severity,
            suggestions=suggestions,
            public_visibility=public_visibility
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        flash('Your complaint has been submitted successfully! Thank you for helping improve tourism services.', 'success')
        return redirect(url_for('user_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while submitting your complaint. Please try again.', 'error')
        return redirect(url_for('user_dashboard'))

@app.route('/api/complaints')
def get_complaints():
    """API endpoint to get public complaints"""
    try:
        # Get filter and sort parameters
        filter_type = request.args.get('type', '')
        sort_by = request.args.get('sort', 'recent')
        
        # Base query for public complaints only
        query = Complaint.query.filter_by(public_visibility=True)
        
        # Apply filter
        if filter_type:
            query = query.filter_by(complaint_type=filter_type)
        
        # Apply sorting
        if sort_by == 'recent':
            query = query.order_by(Complaint.created_at.desc())
        elif sort_by == 'oldest':
            query = query.order_by(Complaint.created_at.asc())
        elif sort_by == 'severity':
            severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            query = query.order_by(Complaint.severity.desc())
        elif sort_by == 'location':
            query = query.order_by(Complaint.location.asc())
        
        complaints = query.limit(50).all()  # Limit to 50 most recent
        
        # Convert to JSON-serializable format
        complaints_data = []
        for complaint in complaints:
            complaints_data.append({
                'id': complaint.id,
                'title': complaint.title,
                'description': complaint.description,
                'type': complaint.complaint_type,
                'location': complaint.location,
                'severity': complaint.severity,
                'suggestions': complaint.suggestions,
                'created_at': complaint.created_at.isoformat(),
                'status': complaint.status
            })
        
        return jsonify({
            'success': True,
            'complaints': complaints_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/complaints')
@login_required
def admin_complaints():
    """Admin view of all complaints (superadmin only)"""
    if current_user.role != 'superadmin':
        flash('Access denied. Superadmin privileges required.', 'error')
        return redirect(url_for('user_dashboard'))
    
    try:
        # Get all complaints with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        complaints = Complaint.query.order_by(Complaint.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin_complaints.html', complaints=complaints)
        
    except Exception as e:
        flash('Error loading complaints.', 'error')
        return redirect(url_for('superadmin_dashboard'))

@app.route('/admin/complaint/<int:complaint_id>/update', methods=['POST'])
@login_required
def update_complaint_status():
    """Update complaint status and add admin notes"""
    if current_user.role != 'superadmin':
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        complaint_id = request.form.get('complaint_id')
        status = request.form.get('status')
        admin_notes = request.form.get('admin_notes', '')
        
        complaint = Complaint.query.get_or_404(complaint_id)
        complaint.status = status
        complaint.admin_notes = admin_notes
        complaint.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Chatbot API Routes
@app.route('/api/chatbot/hotels')
def chatbot_get_hotels():
    """Get hotels for chatbot by location"""
    try:
        location = request.args.get('location', '').strip()
        if not location:
            return jsonify({'success': False, 'error': 'Location is required'}), 400
        
        # Search hotels by city or name
        hotels = Hotel.query.filter(
            db.or_(
                Hotel.city.ilike(f'%{location}%'),
                Hotel.name.ilike(f'%{location}%')
            )
        ).limit(10).all()
        
        hotels_data = []
        for hotel in hotels:
            hotels_data.append({
                'id': hotel.id,
                'name': hotel.name,
                'address': hotel.address,
                'city': hotel.city,
                'price_per_night': hotel.price_per_night,
                'rating': hotel.rating,
                'image': hotel.images
            })
        
        return jsonify({
            'success': True,
            'hotels': hotels_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chatbot/room-types')
def chatbot_get_room_types():
    """Get room types for a specific hotel"""
    try:
        hotel_id = request.args.get('hotel_id', type=int)
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Hotel ID is required'}), 400
        
        room_types = RoomType.query.filter_by(hotel_id=hotel_id).all()
        
        room_types_data = []
        for room_type in room_types:
            room_types_data.append({
                'id': room_type.id,
                'name': room_type.name,
                'description': room_type.description,
                'price_per_night': room_type.price_per_night,
                'max_occupancy': room_type.max_occupancy,
                'amenities': room_type.amenities
            })
        
        return jsonify({
            'success': True,
            'room_types': room_types_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chatbot/vehicles')
def chatbot_get_vehicles():
    """Get vehicles for chatbot by location"""
    try:
        location = request.args.get('location', '').strip()
        if not location:
            return jsonify({'success': False, 'error': 'Location is required'}), 400
        
        # Search vehicles by rental company city
        vehicles = Vehicle.query.join(VehicleRental).filter(
            db.or_(
                VehicleRental.city.ilike(f'%{location}%'),
                VehicleRental.name.ilike(f'%{location}%')
            )
        ).limit(10).all()
        
        vehicles_data = []
        for vehicle in vehicles:
            vehicles_data.append({
                'id': vehicle.id,
                'make': vehicle.make,
                'model': vehicle.model,
                'vehicle_type': vehicle.vehicle_type,
                'transmission': vehicle.transmission,
                'fuel_type': vehicle.fuel_type,
                'seating_capacity': vehicle.seating_capacity,
                'price_per_day': vehicle.price_per_day,
                'rental_company_id': vehicle.rental_company_id,
                'image': vehicle.images
            })
        
        return jsonify({
            'success': True,
            'vehicles': vehicles_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chatbot/create-hotel-booking', methods=['POST'])
@login_required
def chatbot_create_hotel_booking():
    """Create hotel booking through chatbot"""
    try:
        if current_user.role != 'user':
            return jsonify({'success': False, 'error': 'Only users can make bookings'}), 403
        
        data = request.get_json()
        hotel_id = data.get('hotel_id')
        room_type_id = data.get('room_type_id')
        guests = data.get('guests')
        rooms = data.get('rooms')
        total_amount = data.get('total_amount')
        
        if not all([hotel_id, room_type_id, guests, rooms, total_amount]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Generate booking reference
        booking_reference = f"HTL{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=datetime.now().date(),
            check_out=datetime.now().date() + timedelta(days=1),
            guests=guests,
            rooms=rooms,
            total_amount=total_amount,
            status='pending',
            booking_reference=booking_reference
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_reference': booking_reference,
            'booking_id': booking.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chatbot/create-vehicle-booking', methods=['POST'])
@login_required
def chatbot_create_vehicle_booking():
    """Create vehicle booking through chatbot"""
    try:
        if current_user.role != 'user':
            return jsonify({'success': False, 'error': 'Only users can make bookings'}), 403
        
        data = request.get_json()
        vehicle_id = data.get('vehicle_id')
        rental_company_id = data.get('rental_company_id')
        pickup_date = data.get('pickup_date')
        return_date = data.get('return_date')
        total_amount = data.get('total_amount')
        
        if not all([vehicle_id, rental_company_id, pickup_date, return_date, total_amount]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Generate booking reference
        booking_reference = f"VHC{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        # Create booking
        booking = VehicleBooking(
            user_id=current_user.id,
            rental_company_id=rental_company_id,
            vehicle_id=vehicle_id,
            pickup_date=datetime.strptime(pickup_date, '%Y-%m-%d').date(),
            return_date=datetime.strptime(return_date, '%Y-%m-%d').date(),
            pickup_time=datetime.strptime('10:00', '%H:%M').time(),
            return_time=datetime.strptime('18:00', '%H:%M').time(),
            pickup_location='Chatbot Booking',
            return_location='Chatbot Booking',
            drivers_license='CHATBOT_BOOKING',
            drivers_license_expiry=datetime.now().date() + timedelta(days=365),
            total_amount=total_amount,
            status='pending',
            booking_reference=booking_reference
        )
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'booking_reference': booking_reference,
            'booking_id': booking.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ----- VAPI webhook (watch/ESP32 -> VAPI -> this app). Bookings can be manual (website) or via voice (VAPI). -----
def _vapi_webhook_auth():
    """Optional: require X-VAPI-Secret or Authorization header if VAPI_WEBHOOK_SECRET is set."""
    secret = os.environ.get('VAPI_WEBHOOK_SECRET')
    if not secret:
        return True
    auth = request.headers.get('X-VAPI-Secret') or request.headers.get('Authorization', '').replace('Bearer ', '')
    return auth == secret

@app.route('/api/vapi/webhook', methods=['POST'])
def vapi_webhook():
    """
    Webhook for VAPI (voice from watch/ESP32). No login required.
    Body: { "action": "list_hotels"|"list_vehicles"|"create_hotel_booking"|"create_vehicle_booking"|"get_booking_status", ... }
    Returns JSON with success, message (for TTS), and optional data.
    """
    if not _vapi_webhook_auth():
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    try:
        data = request.get_json() or {}
        action = (data.get('action') or '').strip().lower()
        if not action:
            return jsonify({'success': False, 'message': 'Missing action'}), 400

        if action == 'list_hotels':
            return _vapi_list_hotels(data)
        if action == 'list_vehicles':
            return _vapi_list_vehicles(data)
        if action == 'create_hotel_booking':
            return _vapi_create_hotel_booking(data)
        if action == 'create_vehicle_booking':
            return _vapi_create_vehicle_booking(data)
        if action == 'get_booking_status':
            return _vapi_get_booking_status(data)
        return jsonify({'success': False, 'message': f'Unknown action: {action}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def _vapi_list_hotels(data):
    city = (data.get('city') or '').strip()
    query = Hotel.query.filter_by(is_approved=True)
    if city:
        query = query.filter(Hotel.city.ilike(f'%{city}%'))
    hotels = query.limit(20).all()
    out = [{'name': h.name, 'area': h.city} for h in hotels]
    return jsonify({
        'success': True,
        'message': f'Found {len(out)} hotels.' if out else 'No hotels found.',
        'data': {'hotels': out}
    })

def _vapi_list_vehicles(data):
    city = (data.get('city') or '').strip()
    vehicle_type = (data.get('vehicle_type') or '').strip()
    query = db.session.query(Vehicle).join(VehicleRental).filter(
        VehicleRental.is_approved == True,
        Vehicle.is_active == True
    )
    if city:
        query = query.filter(VehicleRental.city.ilike(f'%{city}%'))
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type.ilike(f'%{vehicle_type}%'))
    vehicles = query.limit(30).all()
    out = [{'name': f'{v.make} {v.model}', 'area': v.rental_company.city} for v in vehicles]
    return jsonify({
        'success': True,
        'message': f'Found {len(out)} vehicles.' if out else 'No vehicles found.',
        'data': {'vehicles': out}
    })

def _vapi_create_hotel_booking(data):
    username = (data.get('username') or '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or user.role != 'user':
        return jsonify({'success': False, 'message': 'User not found or cannot book hotels'}), 404
    hotel_name = (data.get('hotel_name') or '').strip()
    area = (data.get('area') or data.get('city') or '').strip()
    check_in_s = data.get('check_in') or data.get('checkin') or ''
    check_out_s = data.get('check_out') or data.get('checkout') or ''
    rooms = data.get('rooms', 1)
    guests = data.get('guests', rooms)
    if not hotel_name or not check_in_s or not check_out_s:
        return jsonify({'success': False, 'message': 'Missing hotel_name, check_in/checkin, or check_out/checkout'}), 400
    query = Hotel.query.filter_by(is_approved=True).filter(Hotel.name.ilike(f'%{hotel_name}%'))
    if area:
        query = query.filter(Hotel.city.ilike(f'%{area}%'))
    hotel = query.first()
    if not hotel:
        return jsonify({'success': False, 'message': 'Hotel not found'}), 404
    try:
        check_in = datetime.strptime(check_in_s.strip()[:10], '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_s.strip()[:10], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format; use YYYY-MM-DD'}), 400
    if check_out <= check_in:
        return jsonify({'success': False, 'message': 'Check-out must be after check-in'}), 400
    rooms, guests = max(1, int(rooms)), max(1, int(guests))
    overlapping = Booking.query.filter(
        Booking.hotel_id == hotel.id,
        Booking.status.in_(['pending', 'confirmed']),
        Booking.check_in < check_out,
        Booking.check_out > check_in
    ).all()
    total_booked = sum(b.rooms for b in overlapping)
    available = max(0, (hotel.total_rooms or 0) - total_booked)
    if rooms > available:
        return jsonify({'success': False, 'message': f'Only {available} rooms available for these dates'}), 400
    nights = (check_out - check_in).days
    total_amount = nights * rooms * hotel.price_per_night
    special = json.dumps({'source': 'vapi'})
    ref = generate_booking_reference()
    booking = Booking(
        user_id=user.id,
        hotel_id=hotel.id,
        room_type_id=None,
        check_in=check_in,
        check_out=check_out,
        rooms=rooms,
        guests=guests,
        total_amount=total_amount,
        special_requests=special,
        booking_reference=ref,
        status='confirmed',
        payment_status='pending'
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Hotel booking confirmed. Reference: {ref}. {hotel.name}, {rooms} room(s), {check_in} to {check_out}.',
        'data': {'booking_id': booking.id, 'booking_reference': ref}
    })

def _vapi_create_vehicle_booking(data):
    username = (data.get('username') or '').strip()
    if not username:
        return jsonify({'success': False, 'message': 'Missing username'}), 400
    user = User.query.filter_by(username=username).first()
    if not user or user.role != 'user':
        return jsonify({'success': False, 'message': 'User not found or cannot book vehicles'}), 404
    vehicle_id = data.get('vehicle_id')
    rental_company_id = data.get('rental_company_id')
    pickup_s = data.get('pickup_date')
    return_s = data.get('return_date')
    if not vehicle_id or not rental_company_id or not pickup_s or not return_s:
        return jsonify({'success': False, 'message': 'Missing vehicle_id, rental_company_id, pickup_date, or return_date'}), 400
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle or vehicle.rental_company_id != int(rental_company_id):
        return jsonify({'success': False, 'message': 'Vehicle not found'}), 404
    if not vehicle.rental_company.is_approved:
        return jsonify({'success': False, 'message': 'Rental company not approved'}), 400
    try:
        pickup_date = datetime.strptime(pickup_s, '%Y-%m-%d').date()
        return_date = datetime.strptime(return_s, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format; use YYYY-MM-DD'}), 400
    if return_date < pickup_date:
        return jsonify({'success': False, 'message': 'Return date must be on or after pickup date'}), 400
    days = max(1, (return_date - pickup_date).days)
    num_vehicles = max(1, int(data.get('num_vehicles', 1)))
    total_amount = vehicle.price_per_day * days * num_vehicles
    overlapping_list = VehicleBooking.query.filter(
        VehicleBooking.vehicle_id == vehicle_id,
        VehicleBooking.status.in_(['pending', 'confirmed']),
        or_(
            and_(VehicleBooking.pickup_date <= pickup_date, VehicleBooking.return_date > pickup_date),
            and_(VehicleBooking.pickup_date < return_date, VehicleBooking.return_date >= return_date),
            and_(VehicleBooking.pickup_date >= pickup_date, VehicleBooking.return_date <= return_date)
        )
    ).all()
    slots_booked = sum(getattr(b, 'quantity', 1) for b in overlapping_list)
    if slots_booked + num_vehicles > vehicle.total_vehicles:
        return jsonify({'success': False, 'message': 'Vehicle not available for selected dates'}), 400
    special = json.dumps({'source': 'vapi'})
    ref = generate_vehicle_booking_reference()
    booking = VehicleBooking(
        user_id=user.id,
        rental_company_id=vehicle.rental_company_id,
        vehicle_id=vehicle.id,
        quantity=num_vehicles,
        pickup_date=pickup_date,
        return_date=return_date,
        pickup_time=datetime.strptime('10:00', '%H:%M').time(),
        return_time=datetime.strptime('18:00', '%H:%M').time(),
        pickup_location=user.phone or 'Voice booking',
        return_location=user.phone or 'Voice booking',
        drivers_license=user.phone or 'VAPI_VOICE',
        drivers_license_expiry=date.today() + timedelta(days=365),
        total_amount=total_amount,
        special_requests=special,
        booking_reference=ref,
        status='confirmed'
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Vehicle booking confirmed. Reference: {ref}. {vehicle.make} {vehicle.model}, {pickup_date} to {return_date}.',
        'data': {'booking_id': booking.id, 'booking_reference': ref}
    })

def _vapi_get_booking_status(data):
    ref = (data.get('booking_reference') or '').strip()
    kind = (data.get('type') or 'hotel').strip().lower()
    if not ref:
        return jsonify({'success': False, 'message': 'Missing booking_reference'}), 400
    if kind == 'vehicle':
        booking = VehicleBooking.query.filter_by(booking_reference=ref).first()
        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404
        return jsonify({
            'success': True,
            'message': f'Vehicle booking {ref}: {booking.status}.',
            'data': {'booking_reference': ref, 'status': booking.status, 'type': 'vehicle'}
        })
    booking = Booking.query.filter_by(booking_reference=ref).first()
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404
    return jsonify({
        'success': True,
        'message': f'Hotel booking {ref}: {booking.status}.',
        'data': {'booking_reference': ref, 'status': booking.status, 'type': 'hotel'}
    })


# Run init_db when app is loaded so DB exists under gunicorn (e.g. Render)
with app.app_context():
    init_db()

@app.route('/api/bootstrap-superadmin', methods=['GET', 'POST'])
def bootstrap_superadmin():
    """One-time: ensure superadmin exists (e.g. after deploy). Optional ?key= matching BOOTSTRAP_KEY env."""
    key = os.environ.get('BOOTSTRAP_KEY')
    if key and request.args.get('key') != key:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        with app.app_context():
            u = User.query.filter_by(username='superadmin').first()
            if u:
                return jsonify({'ok': True, 'message': 'Superadmin already exists'})
            u = User(
                username='superadmin',
                email='admin@tourism.com',
                password_hash=os.environ.get('SUPERADMIN_PASSWORD', 'admin123'),
                first_name='Super',
                last_name='Admin',
                role='superadmin'
            )
            db.session.add(u)
            db.session.commit()
            return jsonify({'ok': True, 'message': 'Superadmin created. Use username superadmin and your SUPERADMIN_PASSWORD (or admin123).'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)


