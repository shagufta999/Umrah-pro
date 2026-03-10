"""
UMRAH PRO - COMPLETE APPLICATION
Main user-facing app with all features integrated
Now with Country Selection & Multi-Currency Support
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time
import hashlib
import uuid
import json
import requests
from bs4 import BeautifulSoup
import random
import math
import pandas as p

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Umrah Pro - Your Complete Umrah Planning Companion",
    page_icon="favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== DATABASE INITIALIZATION ==========

def init_db():  
    """Initialize all database tables"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()

        print("🔧 Initializing database tables...")
        
        # Users table with country field
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (id TEXT PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, 
                    email TEXT, phone TEXT, country TEXT, subscription TEXT DEFAULT 'free',
                    created_at TIMESTAMP)''')
        
        # Family members table
        c.execute('''CREATE TABLE IF NOT EXISTS family_members
                    (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, relationship TEXT,
                    phone TEXT, latitude REAL, longitude REAL, location_name TEXT,
                    status TEXT, battery INTEGER, last_updated TIMESTAMP)''')
        
        # User progress table WITH guide_type
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                    (user_id TEXT, 
                    step_id INTEGER, 
                    guide_type TEXT DEFAULT 'umrah',
                    completed BOOLEAN,
                    PRIMARY KEY(user_id, step_id, guide_type))''')
        
        # Bookmarks table
        c.execute('''CREATE TABLE IF NOT EXISTS bookmarks
                    (id TEXT PRIMARY KEY, user_id TEXT, type TEXT, 
                    name TEXT, details TEXT, created_at TIMESTAMP)''')
        
        # Checklist progress table
        c.execute('''CREATE TABLE IF NOT EXISTS checklist_progress
                    (user_id TEXT, category TEXT, item TEXT, checked BOOLEAN,
                    PRIMARY KEY(user_id, category, item))''')
        
        # Package inquiries table
        c.execute('''CREATE TABLE IF NOT EXISTS package_inquiries
                    (inquiry_id TEXT PRIMARY KEY,
                    package_id TEXT,
                    agent_id TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    travelers INTEGER,
                    preferred_date TEXT,
                    message TEXT,
                    status TEXT,
                    inquiry_date TIMESTAMP)''')
        
        # Packages table with target_countries field
        c.execute('''CREATE TABLE IF NOT EXISTS packages
                    (package_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    package_name TEXT,
                    duration_days INTEGER,
                    duration_nights INTEGER,
                    price REAL,
                    category TEXT,
                    departure_city TEXT,
                    target_countries TEXT,
                    departure_dates TEXT,
                    makkah_hotel TEXT,
                    makkah_hotel_rating INTEGER,
                    makkah_distance TEXT,
                    madinah_hotel TEXT,
                    madinah_hotel_rating INTEGER,
                    madinah_distance TEXT,
                    inclusions TEXT,
                    exclusions TEXT,
                    group_size TEXT,
                    status TEXT,
                    featured BOOLEAN DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    inquiries INTEGER DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP)''')
        
        # Agent partners table
        c.execute('''CREATE TABLE IF NOT EXISTS agent_partners
                    (agent_id TEXT PRIMARY KEY,
                    agent_name TEXT,
                    company_name TEXT,
                    email TEXT,
                    phone TEXT,
                    website TEXT,
                    commission_rate REAL,
                    payment_method TEXT,
                    bank_details TEXT,
                    status TEXT,
                    joined_date TIMESTAMP,
                    onboarding_status TEXT,
                    notes TEXT)''')
        
        # Prayer notifications table
        c.execute('''CREATE TABLE IF NOT EXISTS prayer_notifications
                    (user_id TEXT PRIMARY KEY,
                    enabled BOOLEAN,
                    fajr BOOLEAN,
                    dhuhr BOOLEAN,
                    asr BOOLEAN,
                    maghrib BOOLEAN,
                    isha BOOLEAN,
                    minutes_before INTEGER,
                    latitude REAL,
                    longitude REAL,
                    timezone TEXT,
                    calculation_method INTEGER)''')
        
        # Quran memorization table
        c.execute('''CREATE TABLE IF NOT EXISTS quran_memorization
                    (user_id TEXT,
                    surah_number INTEGER,
                    ayah_number INTEGER,
                    status TEXT,
                    memorized_date TIMESTAMP,
                    last_reviewed TIMESTAMP,
                    review_count INTEGER DEFAULT 0,
                    PRIMARY KEY(user_id, surah_number, ayah_number))''')
        
        # Bookings table
        c.execute('''CREATE TABLE IF NOT EXISTS bookings
                    (booking_id TEXT PRIMARY KEY,
                    package_id TEXT,
                    agent_id TEXT,
                    customer_name TEXT,
                    customer_email TEXT,
                    customer_phone TEXT,
                    travelers INTEGER,
                    departure_date TEXT,
                    return_date TEXT,
                    total_amount REAL,
                    payment_status TEXT,
                    booking_status TEXT,
                    booking_date TIMESTAMP)''')
    
        conn.commit()
        print("✅ Database tables initialized successfully")
        return True
    
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False
    finally:
        if conn:
            conn.close()

    init_db()

# ========== AUTH FUNCTIONS ==========

def hash_password(pwd):
    """Hash password"""
    return hashlib.sha256(pwd.encode()).hexdigest()

def create_user(username, password, email, country, phone=""):
    """Create new user with country"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    user_id = str(uuid.uuid4())
    try:
        c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)',
                  (user_id, username, hash_password(password), email, phone, country, 'free', datetime.now()))
        conn.commit()
        conn.close()
        return True, user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        conn.close()
        return False, None

def auth_user(username, password):
    """Authenticate user"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    try:
        c.execute('SELECT id, subscription, country FROM users WHERE username=? AND password_hash=?',
                  (username, hash_password(password)))
        result = c.fetchone()
        
        if result:
            return result[0], result[1], result[2]
        else:
            return None, None, None
    except Exception as e:
        print(f"Auth error: {e}")
        return None, None, None
    finally:
        conn.close()

def get_user_country(user_id):
    """Get user's country"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    try:
        c.execute('SELECT country FROM users WHERE id=?', (user_id,))
        result = c.fetchone()
        return result[0] if result else "🇺🇸 United States"
    except Exception as e:
        print(f"Exception error: {e}")
        return None, None, None
    finally:
        conn.close()

def upgrade_subscription(user_id, plan):
    """Upgrade user subscription"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    c.execute('UPDATE users SET subscription=? WHERE id=?', (plan, user_id))
    conn.commit()
    conn.close()

# ========== SESSION STATE ==========

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'subscription' not in st.session_state:
    st.session_state.subscription = 'free'
if 'user_country' not in st.session_state:
    st.session_state.user_country = "🇺🇸 United States"
if 'page' not in st.session_state:
    st.session_state.page = "🏠 Home"

# ========== ENHANCED CUSTOM CSS ==========
st.markdown("""
<style>
    /* Import beautiful fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Amiri+Quran&family=Scheherazade+New:wght@400;700&display=swap');
    
    /* Main app styling */
    .main {
        background: linear-gradient(to bottom, #f0fdf4, #ffffff);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #047857, #059669);
        color: white;
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white !important;
    }
    
    /* Main header with animated gradient */
    .main-header {
        background: linear-gradient(135deg, #059669, #10b981, #34d399);
        background-size: 200% 200%;
        animation: gradientShift 3s ease infinite;
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(5, 150, 105, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-header h1 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        font-family: 'Poppins', sans-serif;
        font-size: 1.2rem;
        opacity: 0.95;
        font-weight: 300;
    }
    
    /* Feature cards with hover effect */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #059669;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, transparent, rgba(5, 150, 105, 0.05));
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.15);
        border-left-width: 8px;
    }
    
    .feature-card:hover::before {
        opacity: 1;
    }
    
    /* Package cards with premium styling */
    .package-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .package-card::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(5, 150, 105, 0.1), transparent);
        opacity: 0;
        transition: opacity 0.5s ease;
    }
    
    .package-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 40px rgba(5, 150, 105, 0.2);
        border-color: #059669;
    }
    
    .package-card:hover::after {
        opacity: 1;
    }
    
    /* Price tag with shine effect */
    .price-tag {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 15px;
        font-size: 1.8rem;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
        position: relative;
        overflow: hidden;
        font-family: 'Poppins', sans-serif;
    }
    
    .price-tag::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        transform: rotate(45deg);
        animation: shine 3s infinite;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) rotate(45deg); }
        100% { transform: translateX(100%) rotate(45deg); }
    }
    
    /* Dua box with elegant design */
    .dua-box {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        padding: 2rem;
        border-radius: 20px;
        border: 3px solid #059669;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.15);
        position: relative;
    }
    
    .dua-box::before {
        content: '☪️';
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 3rem;
        opacity: 0.1;
    }
    
    /* Arabic text with beautiful styling */
    .arabic-text {
        font-family: 'Amiri Quran', 'Scheherazade New', 'Traditional Arabic', serif !important;
        font-size: 2.2rem;
        line-height: 3.5rem;
        text-align: right;
        color: #065f46;
        font-weight: bold;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 10px;
        direction: rtl;
    }
    
    /* Premium badge with glow */
    .premium-badge {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
        font-family: 'Poppins', sans-serif;
        display: inline-block;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4); }
        50% { box-shadow: 0 4px 25px rgba(245, 158, 11, 0.6); }
    }
    
    /* Country badge */
    .country-badge {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        padding: 0.5rem 1.2rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        display: inline-block;
        margin-left: 0.5rem;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    /* Stats card */
    .stat-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .stat-card:hover {
        transform: scale(1.05);
        border-color: #059669;
        box-shadow: 0 8px 25px rgba(5, 150, 105, 0.15);
    }
    
    .stat-card h3 {
        color: #059669;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        margin: 0;
    }
    
    .stat-card p {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(5, 150, 105, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #047857, #059669);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.4);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #059669, #10b981, #34d399);
        background-size: 200% 200%;
        animation: progressShine 2s ease infinite;
    }
    
    @keyframes progressShine {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Metric styling */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(5, 150, 105, 0.15);
    }
    
    [data-testid="stMetric"] label {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #059669;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border-radius: 10px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #dcfce7, #bbf7d0);
        transform: translateX(5px);
    }
    
    /* Info box */
    .stAlert {
        border-radius: 15px;
        border-left-width: 5px;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: white;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Input styling */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        font-family: 'Poppins', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #059669;
        box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1);
    }
    
    /* Card containers */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #059669, #10b981);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #047857, #059669);
    }
    
    /* Loading animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
</style>
""", unsafe_allow_html=True)

# ========== CURRENCY EXCHANGE RATES ==========

CURRENCY_DATA = {
    "🇺🇸 United States": {
        "currency": "USD",
        "symbol": "$",
        "rate": 1.0,
        "flag": "🇺🇸"
    },
    "🇬🇧 United Kingdom": {
        "currency": "GBP",
        "symbol": "£",
        "rate": 0.79,
        "flag": "🇬🇧"
    },
    "🇨🇦 Canada": {
        "currency": "CAD",
        "symbol": "C$",
        "rate": 1.35,
        "flag": "🇨🇦"
    },
    "🇦🇪 United Arab Emirates": {
        "currency": "AED",
        "symbol": "AED",
        "rate": 3.67,
        "flag": "🇦🇪"
    },
    "🇸🇦 Saudi Arabia": {
        "currency": "SAR",
        "symbol": "SAR",
        "rate": 3.75,
        "flag": "🇸🇦"
    },
    "🇵🇰 Pakistan": {
        "currency": "PKR",
        "symbol": "Rs",
        "rate": 278,
        "flag": "🇵🇰"
    },
    "🇮🇳 India": {
        "currency": "INR",
        "symbol": "₹",
        "rate": 83,
        "flag": "🇮🇳"
    },
    "🇧🇩 Bangladesh": {
        "currency": "BDT",
        "symbol": "৳",
        "rate": 110,
        "flag": "🇧🇩"
    },
    "🇮🇩 Indonesia": {
        "currency": "IDR",
        "symbol": "Rp",
        "rate": 15600,
        "flag": "🇮🇩"
    },
    "🇲🇾 Malaysia": {
        "currency": "MYR",
        "symbol": "RM",
        "rate": 4.7,
        "flag": "🇲🇾"
    },
    "🇹🇷 Turkey": {
        "currency": "TRY",
        "symbol": "₺",
        "rate": 32,
        "flag": "🇹🇷"
    },
    "🇪🇬 Egypt": {
        "currency": "EGP",
        "symbol": "E£",
        "rate": 31,
        "flag": "🇪🇬"
    },
    "🇳🇬 Nigeria": {
        "currency": "NGN",
        "symbol": "₦",
        "rate": 1250,
        "flag": "🇳🇬"
    },
    "🇿🇦 South Africa": {
        "currency": "ZAR",
        "symbol": "R",
        "rate": 18.5,
        "flag": "🇿🇦"
    },
    "🇦🇺 Australia": {
        "currency": "AUD",
        "symbol": "A$",
        "rate": 1.52,
        "flag": "🇦🇺"
    },
    "🇫🇷 France": {
        "currency": "EUR",
        "symbol": "€",
        "rate": 0.92,
        "flag": "🇫🇷"
    },
    "🇩🇪 Germany": {
        "currency": "EUR",
        "symbol": "€",
        "rate": 0.92,
        "flag": "🇩🇪"
    },
    "🇳🇱 Netherlands": {
        "currency": "EUR",
        "symbol": "€",
        "rate": 0.92,
        "flag": "🇳🇱"
    },
    "🇸🇬 Singapore": {
        "currency": "SGD",
        "symbol": "S$",
        "rate": 1.34,
        "flag": "🇸🇬"
    },
    "🇯🇵 Japan": {
        "currency": "JPY",
        "symbol": "¥",
        "rate": 149,
        "flag": "🇯🇵"
    }
}

def convert_price(usd_price, country):
    """Convert USD price to local currency"""
    currency_info = CURRENCY_DATA.get(country)
    if not currency_info:
        return usd_price, "$"
    
    converted_price = usd_price * currency_info['rate']
    symbol = currency_info['symbol']
    
    # Format based on currency
    if currency_info['currency'] in ['JPY', 'IDR', 'PKR', 'NGN']:
        # No decimals for these currencies
        return int(converted_price), symbol
    else:
        return round(converted_price, 2), symbol

def format_price(price, symbol):
    """Format price with proper thousand separators"""
    if isinstance(price, int):
        return f"{symbol}{price:,}"
    else:
        return f"{symbol}{price:,.2f}"

# ========== FAMILY TRACKING FUNCTIONS ==========

def add_family_member(user_id, name, relationship, phone):
    """Add family member with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS family_members
                     (id TEXT PRIMARY KEY, 
                      user_id TEXT, 
                      name TEXT, 
                      relationship TEXT,
                      phone TEXT, 
                      latitude REAL, 
                      longitude REAL, 
                      location_name TEXT,
                      status TEXT, 
                      battery INTEGER, 
                      last_updated TIMESTAMP)''')
        
        member_id = str(uuid.uuid4())
        c.execute('''INSERT INTO family_members 
                     (id, user_id, name, relationship, phone, status, battery, last_updated)
                     VALUES (?,?,?,?,?,?,?,?)''',
                  (member_id, user_id, name, relationship, phone, 'Not tracking', 100, datetime.now()))
        conn.commit()
        return member_id
        
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"Database operational error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error adding family member: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_family_members(user_id):
    """Get all family members with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS family_members
                     (id TEXT PRIMARY KEY, 
                      user_id TEXT, 
                      name TEXT, 
                      relationship TEXT,
                      phone TEXT, 
                      latitude REAL, 
                      longitude REAL, 
                      location_name TEXT,
                      status TEXT, 
                      battery INTEGER, 
                      last_updated TIMESTAMP)''')
        
        c.execute('''SELECT id, name, relationship, phone, latitude, longitude, 
                     location_name, status, battery, last_updated
                     FROM family_members WHERE user_id=?''', (user_id,))
        members = c.fetchall()
        
        return [{
            'id': m[0], 
            'name': m[1], 
            'relationship': m[2], 
            'phone': m[3],
            'lat': m[4], 
            'lng': m[5], 
            'location': m[6],
            'status': m[7], 
            'battery': m[8], 
            'updated': m[9]
        } for m in members]
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error getting family members: {e}")
        return []
    finally:
        if conn:
            conn.close()


def update_member_location(member_id, lat, lng, location, status, battery):
    """Update member location with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('''UPDATE family_members 
                     SET latitude=?, longitude=?, location_name=?, status=?, battery=?, last_updated=?
                     WHERE id=?''',
                  (lat, lng, location, status, battery, datetime.now(), member_id))
        conn.commit()
        
        # Check if any row was updated
        if c.rowcount == 0:
            print(f"Warning: No family member found with id {member_id}")
            return False
        
        return True
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error updating member location: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_family_member(member_id):
    """Delete family member with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('DELETE FROM family_members WHERE id=?', (member_id,))
        conn.commit()
        
        # Check if any row was deleted
        if c.rowcount == 0:
            print(f"Warning: No family member found with id {member_id}")
            return False
        
        return True
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error deleting family member: {e}")
        return False
    finally:
        if conn:
            conn.close()

# ========== PROGRESS TRACKING FUNCTIONS ==========

def get_user_progress(user_id, guide_type='umrah'):
    """Get completed steps for a specific guide with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists with correct structure
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
        conn.commit()
        
        # Get completed steps
        c.execute('''SELECT step_id FROM user_progress 
                     WHERE user_id=? AND guide_type=? AND completed=1''', 
                  (user_id, guide_type))
        completed = [row[0] for row in c.fetchall()]
        
        return completed
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_user_progress: {e}")
        # Try to recover by creating table
        try:
            if conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                             (user_id TEXT, 
                              step_id INTEGER, 
                              guide_type TEXT DEFAULT 'umrah',
                              completed BOOLEAN,
                              PRIMARY KEY(user_id, step_id, guide_type))''')
                conn.commit()
        except:
            pass
        return []
        
    except Exception as e:
        print(f"Unexpected error in get_user_progress: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def save_step_progress(user_id, step_id, completed, guide_type='umrah'):
    """Save step completion status with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists with correct structure
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
        conn.commit()
        
        if completed:
            # Mark as completed
            c.execute('''INSERT OR REPLACE INTO user_progress 
                         (user_id, step_id, guide_type, completed) 
                         VALUES (?,?,?,1)''',
                      (user_id, step_id, guide_type))
        else:
            # Mark as incomplete (delete record)
            c.execute('''DELETE FROM user_progress 
                         WHERE user_id=? AND step_id=? AND guide_type=?''',
                      (user_id, step_id, guide_type))
        
        conn.commit()
        
        # Verify the operation
        if completed:
            c.execute('''SELECT completed FROM user_progress 
                         WHERE user_id=? AND step_id=? AND guide_type=?''',
                      (user_id, step_id, guide_type))
            result = c.fetchone()
            return result is not None and result[0] == 1
        else:
            c.execute('''SELECT COUNT(*) FROM user_progress 
                         WHERE user_id=? AND step_id=? AND guide_type=?''',
                      (user_id, step_id, guide_type))
            return c.fetchone()[0] == 0
        
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error in save_step_progress: {e}")
        return False
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in save_step_progress: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error in save_step_progress: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def get_progress_statistics(user_id):
    """Get progress statistics for all guides with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
        
        # Get counts by guide type
        c.execute('''SELECT guide_type, COUNT(*) 
                     FROM user_progress 
                     WHERE user_id=? AND completed=1 
                     GROUP BY guide_type''',
                  (user_id,))
        
        stats = {}
        for row in c.fetchall():
            stats[row[0]] = row[1]
        
        return stats
        
    except Exception as e:
        print(f"Error getting progress statistics: {e}")
        return {}
        
    finally:
        if conn:
            conn.close()


def reset_user_progress(user_id, guide_type=None):
    """Reset user progress with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        if guide_type:
            # Reset specific guide
            c.execute('''DELETE FROM user_progress 
                         WHERE user_id=? AND guide_type=?''',
                      (user_id, guide_type))
        else:
            # Reset all progress
            c.execute('DELETE FROM user_progress WHERE user_id=?', (user_id,))
        
        conn.commit()
        deleted_count = c.rowcount
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"Error resetting user progress: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def bulk_save_progress(user_id, steps_data, guide_type='umrah'):
    """Save multiple steps at once with error handling
    
    Args:
        user_id: User ID
        steps_data: List of tuples [(step_id, completed), ...]
        guide_type: Type of guide ('umrah', 'hajj', 'salah', etc.)
    
    Returns:
        Tuple of (success_count, failed_count)
    """
    conn = None
    success_count = 0
    failed_count = 0
    
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
        
        # Process each step
        for step_id, completed in steps_data:
            try:
                if completed:
                    c.execute('''INSERT OR REPLACE INTO user_progress 
                                 (user_id, step_id, guide_type, completed) 
                                 VALUES (?,?,?,1)''',
                              (user_id, step_id, guide_type))
                else:
                    c.execute('''DELETE FROM user_progress 
                                 WHERE user_id=? AND step_id=? AND guide_type=?''',
                              (user_id, step_id, guide_type))
                
                success_count += 1
                
            except Exception as e:
                print(f"Error saving step {step_id}: {e}")
                failed_count += 1
        
        conn.commit()
        return (success_count, failed_count)
        
    except Exception as e:
        print(f"Error in bulk_save_progress: {e}")
        return (success_count, failed_count)
        
    finally:
        if conn:
            conn.close()


def migrate_old_progress_data():
    """Migrate old progress data to new structure (one-time use)"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if old table exists
        c.execute("""SELECT name FROM sqlite_master 
                     WHERE type='table' AND name='user_progress_old'""")
        
        if not c.fetchone():
            print("No old data to migrate")
            return True
        
        # Create new table
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
        
        # Migrate data
        c.execute('''INSERT OR IGNORE INTO user_progress 
                     (user_id, step_id, guide_type, completed)
                     SELECT user_id, step_id, 'umrah', completed 
                     FROM user_progress_old''')
        
        migrated_count = c.rowcount
        conn.commit()
        
        print(f"✅ Migrated {migrated_count} records")
        return True
        
    except Exception as e:
        print(f"Error migrating data: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

# ========== PRAYER TIMES FUNCTIONS ==========

def get_user_location_from_ip():
    """Get user's approximate location from IP address with error handling"""
    default_location = {
        'city': 'Makkah',
        'country': 'SA',
        'lat': 21.4225,
        'lon': 39.8262,
        'timezone': 'Asia/Riyadh'
    }
    
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate data before returning
            if data.get('lat') and data.get('lon'):
                return {
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'lat': float(data.get('lat', 21.4225)),
                    'lon': float(data.get('lon', 39.8262)),
                    'timezone': data.get('timezone', 'Asia/Riyadh')
                }
        
        return default_location
        
    except requests.exceptions.Timeout:
        print("IP location request timed out")
        return default_location
        
    except requests.exceptions.RequestException as e:
        print(f"IP location request error: {e}")
        return default_location
        
    except (KeyError, ValueError, TypeError) as e:
        print(f"Error parsing IP location data: {e}")
        return default_location
        
    except Exception as e:
        print(f"Unexpected error in get_user_location_from_ip: {e}")
        return default_location


def get_prayer_times_by_coordinates(lat, lon, timezone='Asia/Riyadh'):
    """Get prayer times using coordinates with error handling"""
    try:
        # Validate inputs
        lat = float(lat)
        lon = float(lon)
        
        if not (-90 <= lat <= 90):
            print(f"Invalid latitude: {lat}")
            return None
        
        if not (-180 <= lon <= 180):
            print(f"Invalid longitude: {lon}")
            return None
        
        # Get current date
        today = datetime.now()
        date_str = today.strftime('%d-%m-%Y')
        
        # API call with coordinates
        url = f"http://api.aladhan.com/v1/timings/{date_str}"
        params = {
            'latitude': lat,
            'longitude': lon,
            'method': 2,  # ISNA
            'timezone': timezone
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if 'data' not in data or 'timings' not in data['data']:
                print("Invalid API response structure")
                return None
            
            timings = data['data']['timings']
            
            return {
                'Fajr': timings.get('Fajr', '00:00'),
                'Sunrise': timings.get('Sunrise', '00:00'),
                'Dhuhr': timings.get('Dhuhr', '00:00'),
                'Asr': timings.get('Asr', '00:00'),
                'Maghrib': timings.get('Maghrib', '00:00'),
                'Isha': timings.get('Isha', '00:00'),
                'date': data['data']['date'].get('readable', date_str),
                'hijri': data['data']['date']['hijri'].get('date', ''),
                'timezone': timezone
            }
        else:
            print(f"Prayer times API returned status code: {response.status_code}")
            return None
        
    except requests.exceptions.Timeout:
        print("Prayer times request timed out")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Prayer times request error: {e}")
        return None
        
    except (ValueError, TypeError) as e:
        print(f"Invalid coordinate values: {e}")
        return None
        
    except (KeyError, IndexError) as e:
        print(f"Error parsing prayer times data: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in get_prayer_times_by_coordinates: {e}")
        return None


def get_next_prayer(prayer_times):
    """Get the next upcoming prayer with error handling"""
    if not prayer_times:
        return None
    
    try:
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        
        prayers = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
        
        for prayer in prayers:
            prayer_time = prayer_times.get(prayer, '00:00')
            
            if prayer_time > current_time:
                # Calculate time remaining
                try:
                    prayer_dt = datetime.strptime(prayer_time, '%H:%M')
                    now_dt = datetime.strptime(current_time, '%H:%M')
                    
                    diff = prayer_dt - now_dt
                    hours = diff.seconds // 3600
                    minutes = (diff.seconds % 3600) // 60
                    
                    return {
                        'name': prayer,
                        'time': prayer_time,
                        'hours_remaining': hours,
                        'minutes_remaining': minutes
                    }
                except ValueError as e:
                    print(f"Error parsing time for {prayer}: {e}")
                    continue
        
        # If all prayers passed, next is tomorrow's Fajr
        return {
            'name': 'Fajr',
            'time': prayer_times.get('Fajr', '00:00'),
            'hours_remaining': 0,
            'minutes_remaining': 0,
            'tomorrow': True
        }
        
    except Exception as e:
        print(f"Error in get_next_prayer: {e}")
        return None


def get_calculation_methods():
    """Get available prayer calculation methods"""
    return {
        '1': 'University of Islamic Sciences, Karachi',
        '2': 'Islamic Society of North America (ISNA)',
        '3': 'Muslim World League',
        '4': 'Umm Al-Qura University, Makkah',
        '5': 'Egyptian General Authority of Survey',
        '7': 'Institute of Geophysics, University of Tehran',
        '8': 'Gulf Region',
        '9': 'Kuwait',
        '10': 'Qatar',
        '11': 'Majlis Ugama Islam Singapura, Singapore',
        '12': 'Union Organization islamic de France',
        '13': 'Diyanet İşleri Başkanlığı, Turkey',
        '14': 'Spiritual Administration of Muslims of Russia'
    }


def save_prayer_notification_settings(user_id, settings):
    """Save user's notification preferences with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Create table if doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS prayer_notifications
                     (user_id TEXT PRIMARY KEY,
                      enabled BOOLEAN,
                      fajr BOOLEAN,
                      dhuhr BOOLEAN,
                      asr BOOLEAN,
                      maghrib BOOLEAN,
                      isha BOOLEAN,
                      minutes_before INTEGER,
                      latitude REAL,
                      longitude REAL,
                      timezone TEXT,
                      calculation_method INTEGER)''')
        
        c.execute('''INSERT OR REPLACE INTO prayer_notifications VALUES 
                     (?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (user_id, 
                   bool(settings.get('enabled', True)),
                   bool(settings.get('fajr', True)),
                   bool(settings.get('dhuhr', True)),
                   bool(settings.get('asr', True)),
                   bool(settings.get('maghrib', True)),
                   bool(settings.get('isha', True)),
                   int(settings.get('minutes_before', 15)),
                   float(settings.get('latitude', 21.4225)),
                   float(settings.get('longitude', 39.8262)),
                   str(settings.get('timezone', 'Asia/Riyadh')),
                   int(settings.get('calculation_method', 2))))
        
        conn.commit()
        return True
        
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error saving prayer settings: {e}")
        return False
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error saving prayer settings: {e}")
        return False
        
    except (ValueError, TypeError) as e:
        print(f"Invalid data type in prayer settings: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error saving prayer settings: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def get_prayer_notification_settings(user_id):
    """Get user's notification preferences with error handling"""
    default_settings = {
        'enabled': True,
        'fajr': True,
        'dhuhr': True,
        'asr': True,
        'maghrib': True,
        'isha': True,
        'minutes_before': 15,
        'latitude': 21.4225,
        'longitude': 39.8262,
        'timezone': 'Asia/Riyadh',
        'calculation_method': 2
    }
    
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS prayer_notifications
                     (user_id TEXT PRIMARY KEY,
                      enabled BOOLEAN,
                      fajr BOOLEAN,
                      dhuhr BOOLEAN,
                      asr BOOLEAN,
                      maghrib BOOLEAN,
                      isha BOOLEAN,
                      minutes_before INTEGER,
                      latitude REAL,
                      longitude REAL,
                      timezone TEXT,
                      calculation_method INTEGER)''')
        
        c.execute('SELECT * FROM prayer_notifications WHERE user_id=?', (user_id,))
        result = c.fetchone()
        
        if result:
            return {
                'enabled': bool(result[1]),
                'fajr': bool(result[2]),
                'dhuhr': bool(result[3]),
                'asr': bool(result[4]),
                'maghrib': bool(result[5]),
                'isha': bool(result[6]),
                'minutes_before': int(result[7]),
                'latitude': float(result[8]),
                'longitude': float(result[9]),
                'timezone': str(result[10]),
                'calculation_method': int(result[11])
            }
        
        return default_settings
        
    except sqlite3.OperationalError as e:
        print(f"Database error getting prayer settings: {e}")
        return default_settings
        
    except (IndexError, ValueError, TypeError) as e:
        print(f"Error parsing prayer settings: {e}")
        return default_settings
        
    except Exception as e:
        print(f"Unexpected error getting prayer settings: {e}")
        return default_settings
        
    finally:
        if conn:
            conn.close()


def get_qibla_direction(lat=21.4225, lon=39.8262):
    """Get Qibla direction with error handling"""
    try:
        lat = float(lat)
        lon = float(lon)
        
        url = f"http://api.aladhan.com/v1/qibla/{lat}/{lon}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'direction' in data['data']:
                direction = float(data['data']['direction'])
                return round(direction, 2)
        
        return 0.0
        
    except requests.exceptions.RequestException as e:
        print(f"Qibla direction request error: {e}")
        return 0.0
        
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error parsing Qibla direction: {e}")
        return 0.0
        
    except Exception as e:
        print(f"Unexpected error in get_qibla_direction: {e}")
        return 0.0


# ========== QURAN FUNCTIONS ==========

def get_surah_list():
    """Get list of all Surahs with error handling"""
    try:
        url = "http://api.alquran.cloud/v1/surah"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and isinstance(data['data'], list):
                return [
                    (
                        int(s.get('number', 0)),
                        str(s.get('englishName', 'Unknown')),
                        str(s.get('name', '')),
                        int(s.get('numberOfAyahs', 0))
                    )
                    for s in data['data']
                    if s.get('number')
                ]
        
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Surah list: {e}")
        return []
        
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error parsing Surah list: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error in get_surah_list: {e}")
        return []


def get_surah_text(surah_number):
    """Get Surah text with error handling (deprecated - use get_surah_with_translation)"""
    try:
        surah_number = int(surah_number)
        
        if not (1 <= surah_number <= 114):
            print(f"Invalid surah number: {surah_number}")
            return None
        
        url = f"http://api.alquran.cloud/v1/surah/{surah_number}/editions/quran-uthmani,en.asad"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()['data']
            arabic_ayahs = data[0]['ayahs']
            english_ayahs = data[1]['ayahs']
            
            verses = []
            for i in range(len(arabic_ayahs)):
                verses.append({
                    'number': arabic_ayahs[i]['numberInSurah'],
                    'arabic': arabic_ayahs[i]['text'],
                    'english': english_ayahs[i]['text']
                })
            
            return {
                'name': data[0]['englishName'],
                'arabic_name': data[0]['name'],
                'revelation': data[0]['revelationType'],
                'verses': verses
            }
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Surah text: {e}")
        return None
        
    except (ValueError, KeyError, IndexError, TypeError) as e:
        print(f"Error parsing Surah text: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in get_surah_text: {e}")
        return None


def get_available_translations():
    """Get all available Quran translations"""
    return {
        'en.asad': 'English - Muhammad Asad',
        'en.sahih': 'English - Sahih International',
        'en.pickthall': 'English - Pickthall',
        'en.yusufali': 'English - Yusuf Ali',
        'en.hilali': 'English - Hilali & Khan',
        'ar.alafasy': 'Arabic - Mishary Alafasy',
        'ur.jalandhry': 'Urdu - Jalandhri',
        'ur.ahmedali': 'Urdu - Ahmed Ali',
        'ur.muhammadjunagarhi': 'Urdu - Muhammad Junagarhi',
        'id.indonesian': 'Indonesian - Ministry of Religious Affairs',
        'tr.diyanet': 'Turkish - Diyanet',
        'tr.vakfi': 'Turkish - Diyanet Vakfi',
        'fr.hamidullah': 'French - Hamidullah',
        'de.bubenheim': 'German - Bubenheim & Elyas',
        'es.cortes': 'Spanish - Cortes',
        'ru.kuliev': 'Russian - Kuliev',
        'bn.bengali': 'Bengali - Muhiuddin Khan',
        'hi.hindi': 'Hindi - Farooq Khan',
        'fa.fooladvand': 'Persian - Fooladvand',
        'sw.barwani': 'Swahili - Al-Barwani',
        'ml.abdulhameed': 'Malayalam - Abdulhameed',
        'ta.tamil': 'Tamil - Jan Trust',
        'zh.chinese': 'Chinese - Ma Jian',
        'ja.japanese': 'Japanese - Saeed Sato',
        'ko.korean': 'Korean - Unknown',
        'pt.elhayek': 'Portuguese - El-Hayek',
        'it.piccardo': 'Italian - Piccardo',
        'nl.siregar': 'Dutch - Siregar',
        'pl.bielawskiego': 'Polish - Bielawskiego',
        'sq.ahmeti': 'Albanian - Ahmeti',
        'bs.korkut': 'Bosnian - Korkut',
        'az.mammadaliyev': 'Azerbaijani - Mammadaliyev'
    }


def get_surah_with_translation(surah_number, translation='en.asad'):
    """Get Surah with selected translation with error handling"""
    try:
        surah_number = int(surah_number)
        
        if not (1 <= surah_number <= 114):
            print(f"Invalid surah number: {surah_number}")
            return None
        
        url = f"http://api.alquran.cloud/v1/surah/{surah_number}/editions/quran-uthmani,{translation}"
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' not in data or len(data['data']) < 2:
                print("Invalid API response structure")
                return None
            
            arabic_ayahs = data['data'][0]['ayahs']
            trans_ayahs = data['data'][1]['ayahs']
            
            if len(arabic_ayahs) != len(trans_ayahs):
                print("Mismatch in verse counts")
                return None
            
            verses = []
            for i in range(len(arabic_ayahs)):
                verses.append({
                    'number': arabic_ayahs[i].get('numberInSurah', i+1),
                    'arabic': arabic_ayahs[i].get('text', ''),
                    'translation': trans_ayahs[i].get('text', '')
                })
            
            return {
                'name': data['data'][0].get('englishName', 'Unknown'),
                'arabic_name': data['data'][0].get('name', ''),
                'revelation': data['data'][0].get('revelationType', 'Unknown'),
                'verses': verses
            }
        else:
            print(f"API returned status code: {response.status_code}")
            return None
        
    except requests.exceptions.Timeout:
        print("Surah request timed out")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Surah: {e}")
        return None
        
    except (ValueError, KeyError, IndexError, TypeError) as e:
        print(f"Error parsing Surah data: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in get_surah_with_translation: {e}")
        return None


def get_available_reciters():
    """Get list of famous Quran reciters"""
    return {
        'ar.alafasy': {
            'name': 'Mishary Rashid Alafasy',
            'style': 'Clear and beautiful',
            'country': '🇰🇼 Kuwait',
            'identifier': 'Alafasy_128kbps'
        },
        'ar.abdulbasitmurattal': {
            'name': 'Abdul Basit (Murattal)',
            'style': 'Slow and clear',
            'country': '🇪🇬 Egypt',
            'identifier': 'Abdul_Basit_Murattal_192kbps'
        },
        'ar.husary': {
            'name': 'Mahmoud Khalil Al-Husary',
            'style': 'Educational',
            'country': '🇪🇬 Egypt',
            'identifier': 'Husary_128kbps'
        },
        'ar.minshawi': {
            'name': 'Mohamed Siddiq Al-Minshawi',
            'style': 'Emotional',
            'country': '🇪🇬 Egypt',
            'identifier': 'Minshawy_Murattal_128kbps'
        },
        'ar.sudais': {
            'name': 'Abdurrahman As-Sudais',
            'style': 'Imam of Masjid al-Haram',
            'country': '🇸🇦 Saudi Arabia',
            'identifier': 'Abdurrahmaan_As-Sudais_192kbps'
        },
        'ar.shaatree': {
            'name': 'Abu Bakr Al-Shatri',
            'style': 'Fast recitation',
            'country': '🇸🇦 Saudi Arabia',
            'identifier': 'Abu_Bakr_Ash-Shaatree_128kbps'
        },
        'ar.ghamadi': {
            'name': 'Saad Al-Ghamdi',
            'style': 'Powerful voice',
            'country': '🇸🇦 Saudi Arabia',
            'identifier': 'Ghamadi_40kbps'
        }
    }


def get_verse_audio_url(surah_number, ayah_number, reciter='ar.alafasy'):
    """Get audio URL for specific verse with error handling"""
    try:
        surah_number = int(surah_number)
        ayah_number = int(ayah_number)
        
        reciters_map = get_available_reciters()
        
        if reciter not in reciters_map:
            reciter = 'ar.alafasy'
        
        identifier = reciters_map[reciter]['identifier']
        
        surah_formatted = str(surah_number).zfill(3)
        ayah_formatted = str(ayah_number).zfill(3)
        
        return f"https://everyayah.com/data/{identifier}/{surah_formatted}{ayah_formatted}.mp3"
        
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error generating verse audio URL: {e}")
        return ""


def get_surah_audio_url(surah_number, reciter='ar.alafasy'):
    """Get audio URL for Surah with error handling"""
    try:
        surah_number = int(surah_number)
        
        reciters = get_available_reciters()
        
        if reciter not in reciters:
            reciter = 'ar.alafasy'
        
        identifier = reciters[reciter]['identifier']
        surah_formatted = str(surah_number).zfill(3)
        
        return f"https://everyayah.com/data/{identifier}/{surah_formatted}001.mp3"
        
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error generating surah audio URL: {e}")
        return ""


def get_full_surah_audio_url(surah_number, reciter='ar.alafasy'):
    """Get complete Surah audio URL with error handling"""
    try:
        surah_number = int(surah_number)
        
        if not (1 <= surah_number <= 114):
            return ""
        
        surah_formatted = str(surah_number).zfill(3)
        
        reciter_servers = {
            'ar.alafasy': f"https://server8.mp3quran.net/afs/{surah_formatted}.mp3",
            'ar.abdulbasitmurattal': f"https://server7.mp3quran.net/basit/{surah_formatted}.mp3",
            'ar.husary': f"https://server13.mp3quran.net/husr/{surah_formatted}.mp3",
            'ar.minshawi': f"https://server10.mp3quran.net/minsh/{surah_formatted}.mp3",
            'ar.sudais': f"https://server11.mp3quran.net/sds/{surah_formatted}.mp3",
            'ar.shaatree': f"https://server12.mp3quran.net/shur/{surah_formatted}.mp3",
            'ar.ghamadi': f"https://server5.mp3quran.net/gmd/{surah_formatted}.mp3"
        }
        
        return reciter_servers.get(reciter, reciter_servers['ar.alafasy'])
        
    except (ValueError, KeyError, TypeError) as e:
        print(f"Error generating full surah audio URL: {e}")
        return ""


def check_audio_url(url):
    """Check if audio URL is accessible with error handling"""
    try:
        if not url:
            return False
        
        response = requests.head(url, timeout=5)
        return response.status_code == 200
        
    except requests.exceptions.RequestException:
        return False
        
    except Exception as e:
        print(f"Error checking audio URL: {e}")
        return False


def get_random_verse():
    """Get random Quran verse with error handling"""
    default_verse = {
        'arabic': 'رَبَّنَا تَقَبَّلْ مِنَّا إِنَّكَ أَنتَ السَّمِيعُ الْعَلِيمُ',
        'english': 'Our Lord, accept this from us. Indeed, You are the Hearing, the Knowing.',
        'ref': 'Al-Baqarah (2:127)'
    }
    
    try:
        s = random.randint(1, 114)
        a = random.randint(1, 10)
        
        url = f"http://api.alquran.cloud/v1/ayah/{s}:{a}/editions/quran-uthmani,en.asad"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and len(data['data']) >= 2:
                return {
                    'arabic': data['data'][0].get('text', default_verse['arabic']),
                    'english': data['data'][1].get('text', default_verse['english']),
                    'ref': f"{data['data'][0]['surah']['englishName']} ({s}:{a})"
                }
        
        return default_verse
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching random verse: {e}")
        return default_verse
        
    except (ValueError, KeyError, IndexError, TypeError) as e:
        print(f"Error parsing random verse: {e}")
        return default_verse
        
    except Exception as e:
        print(f"Unexpected error in get_random_verse: {e}")
        return default_verse

# ========== PACKAGE FUNCTIONS ==========

def get_all_packages(user_country=None):
    """Get all active packages filtered by user's country with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure tables exist
        c.execute('''CREATE TABLE IF NOT EXISTS packages
                     (package_id TEXT PRIMARY KEY,
                      agent_id TEXT,
                      package_name TEXT,
                      duration_days INTEGER,
                      duration_nights INTEGER,
                      price REAL,
                      category TEXT,
                      departure_city TEXT,
                      target_countries TEXT,
                      departure_dates TEXT,
                      makkah_hotel TEXT,
                      makkah_hotel_rating INTEGER,
                      makkah_distance TEXT,
                      madinah_hotel TEXT,
                      madinah_hotel_rating INTEGER,
                      madinah_distance TEXT,
                      inclusions TEXT,
                      exclusions TEXT,
                      group_size TEXT,
                      status TEXT,
                      featured BOOLEAN DEFAULT 0,
                      views INTEGER DEFAULT 0,
                      inquiries INTEGER DEFAULT 0,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS agent_partners
                     (agent_id TEXT PRIMARY KEY,
                      agent_name TEXT,
                      company_name TEXT,
                      email TEXT,
                      phone TEXT,
                      website TEXT,
                      commission_rate REAL,
                      payment_method TEXT,
                      bank_details TEXT,
                      status TEXT,
                      joined_date TIMESTAMP,
                      onboarding_status TEXT,
                      notes TEXT)''')
        
        # Fetch packages
        c.execute('''SELECT p.package_id, p.package_name, p.duration_days, p.duration_nights,
                     p.price, p.category, p.departure_city, p.target_countries, p.makkah_hotel,
                     p.makkah_hotel_rating, p.makkah_distance, p.madinah_hotel, 
                     p.madinah_hotel_rating, p.madinah_distance, p.inclusions,
                     p.exclusions, p.group_size, p.departure_dates,
                     a.company_name, a.email, a.phone, a.website
                     FROM packages p
                     JOIN agent_partners a ON p.agent_id = a.agent_id
                     WHERE p.status='Active' AND a.status='Active'
                     ORDER BY p.created_at DESC''')
        
        packages = []
        for row in c.fetchall():
            try:
                target_countries = str(row[7]) if row[7] else ""
                
                # Filter by user country if provided
                if user_country and target_countries:
                    # Check if user's country is in target countries
                    if user_country not in target_countries and "All Countries" not in target_countries:
                        continue
                
                # Validate and convert data types
                packages.append({
                    'id': str(row[0]),
                    'name': str(row[1]),
                    'duration_days': int(row[2]) if row[2] else 0,
                    'duration_nights': int(row[3]) if row[3] else 0,
                    'duration': f"{row[2]} Days / {row[3]} Nights",
                    'price': float(row[4]) if row[4] else 0.0,
                    'category': str(row[5]) if row[5] else 'Standard',
                    'departure_city': str(row[6]) if row[6] else 'Unknown',
                    'target_countries': target_countries,
                    'makkah_hotel': str(row[8]) if row[8] else 'TBD',
                    'makkah_rating': int(row[9]) if row[9] else 0,
                    'makkah_distance': str(row[10]) if row[10] else 'N/A',
                    'madinah_hotel': str(row[11]) if row[11] else 'TBD',
                    'madinah_rating': int(row[12]) if row[12] else 0,
                    'madinah_distance': str(row[13]) if row[13] else 'N/A',
                    'inclusions': str(row[14]) if row[14] else '',
                    'exclusions': str(row[15]) if row[15] else '',
                    'group_size': str(row[16]) if row[16] else 'Flexible',
                    'departure_dates': str(row[17]) if row[17] else 'Various',
                    'company': str(row[18]) if row[18] else 'Unknown',
                    'company_email': str(row[19]) if row[19] else '',
                    'company_phone': str(row[20]) if row[20] else '',
                    'company_website': str(row[21]) if row[21] else ''
                })
                
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error parsing package row: {e}")
                continue
        
        return packages
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_all_packages: {e}")
        return []
        
    except sqlite3.DatabaseError as e:
        print(f"Database error in get_all_packages: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error in get_all_packages: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def increment_package_view(package_id):
    """Increment package view count with error handling"""
    conn = None
    try:
        if not package_id:
            return False
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS packages
                     (package_id TEXT PRIMARY KEY,
                      agent_id TEXT,
                      package_name TEXT,
                      duration_days INTEGER,
                      duration_nights INTEGER,
                      price REAL,
                      category TEXT,
                      departure_city TEXT,
                      target_countries TEXT,
                      departure_dates TEXT,
                      makkah_hotel TEXT,
                      makkah_hotel_rating INTEGER,
                      makkah_distance TEXT,
                      madinah_hotel TEXT,
                      madinah_hotel_rating INTEGER,
                      madinah_distance TEXT,
                      inclusions TEXT,
                      exclusions TEXT,
                      group_size TEXT,
                      status TEXT,
                      featured BOOLEAN DEFAULT 0,
                      views INTEGER DEFAULT 0,
                      inquiries INTEGER DEFAULT 0,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        
        c.execute('UPDATE packages SET views = views + 1 WHERE package_id=?', (package_id,))
        conn.commit()
        
        # Check if any row was updated
        return c.rowcount > 0
        
    except sqlite3.OperationalError as e:
        print(f"Database error incrementing view count: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error incrementing view count: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def submit_package_inquiry(package_id, agent_id, customer_data):
    """Submit package inquiry with error handling"""
    conn = None
    try:
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'travelers']
        for field in required_fields:
            if field not in customer_data or not customer_data[field]:
                print(f"Missing required field: {field}")
                return None
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS package_inquiries
                     (inquiry_id TEXT PRIMARY KEY,
                      package_id TEXT,
                      agent_id TEXT,
                      customer_name TEXT,
                      customer_email TEXT,
                      customer_phone TEXT,
                      travelers INTEGER,
                      preferred_date TEXT,
                      message TEXT,
                      status TEXT,
                      inquiry_date TIMESTAMP)''')
        
        inquiry_id = str(uuid.uuid4())
        
        # Insert inquiry
        c.execute('''INSERT INTO package_inquiries
                     (inquiry_id, package_id, agent_id, customer_name, customer_email,
                      customer_phone, travelers, preferred_date, message, status, inquiry_date)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                  (inquiry_id, 
                   str(package_id),
                   str(agent_id),
                   str(customer_data['name']),
                   str(customer_data['email']),
                   str(customer_data['phone']),
                   int(customer_data['travelers']),
                   str(customer_data.get('preferred_date', 'Flexible')),
                   str(customer_data.get('message', '')),
                   'Pending',
                   datetime.now()))
        
        # Increment inquiry count
        c.execute('UPDATE packages SET inquiries = inquiries + 1 WHERE package_id=?', 
                 (package_id,))
        
        conn.commit()
        
        # Verify inquiry was created
        c.execute('SELECT inquiry_id FROM package_inquiries WHERE inquiry_id=?', (inquiry_id,))
        if c.fetchone():
            return inquiry_id
        else:
            print("Inquiry creation verification failed")
            return None
        
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error submitting inquiry: {e}")
        return None
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error submitting inquiry: {e}")
        return None
        
    except (ValueError, TypeError) as e:
        print(f"Invalid data type in inquiry: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error submitting inquiry: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def get_agent_by_package(package_id):
    """Get agent details for a package with error handling"""
    conn = None
    try:
        if not package_id:
            return None
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure tables exist
        c.execute('''CREATE TABLE IF NOT EXISTS agent_partners
                     (agent_id TEXT PRIMARY KEY,
                      agent_name TEXT,
                      company_name TEXT,
                      email TEXT,
                      phone TEXT,
                      website TEXT,
                      commission_rate REAL,
                      payment_method TEXT,
                      bank_details TEXT,
                      status TEXT,
                      joined_date TIMESTAMP,
                      onboarding_status TEXT,
                      notes TEXT)''')
        
        c.execute('''SELECT a.agent_id, a.company_name, a.email, a.phone
                     FROM agent_partners a
                     JOIN packages p ON a.agent_id = p.agent_id
                     WHERE p.package_id=?''',
                  (package_id,))
        
        result = c.fetchone()
        
        if result:
            return {
                'agent_id': str(result[0]),
                'company': str(result[1]) if result[1] else 'Unknown',
                'email': str(result[2]) if result[2] else '',
                'phone': str(result[3]) if result[3] else ''
            }
        
        return None
        
    except sqlite3.OperationalError as e:
        print(f"Database error getting agent: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error getting agent: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def get_package_by_id(package_id):
    """Get single package details with error handling"""
    conn = None
    try:
        if not package_id:
            return None
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('''SELECT p.package_id, p.package_name, p.duration_days, p.duration_nights,
                     p.price, p.category, p.departure_city, p.target_countries, p.makkah_hotel,
                     p.makkah_hotel_rating, p.makkah_distance, p.madinah_hotel, 
                     p.madinah_hotel_rating, p.madinah_distance, p.inclusions,
                     p.exclusions, p.group_size, p.departure_dates, p.views, p.inquiries,
                     a.company_name, a.email, a.phone, a.website
                     FROM packages p
                     JOIN agent_partners a ON p.agent_id = a.agent_id
                     WHERE p.package_id=?''',
                  (package_id,))
        
        row = c.fetchone()
        
        if row:
            return {
                'id': str(row[0]),
                'name': str(row[1]),
                'duration_days': int(row[2]) if row[2] else 0,
                'duration_nights': int(row[3]) if row[3] else 0,
                'duration': f"{row[2]} Days / {row[3]} Nights",
                'price': float(row[4]) if row[4] else 0.0,
                'category': str(row[5]) if row[5] else 'Standard',
                'departure_city': str(row[6]) if row[6] else 'Unknown',
                'target_countries': str(row[7]) if row[7] else '',
                'makkah_hotel': str(row[8]) if row[8] else 'TBD',
                'makkah_rating': int(row[9]) if row[9] else 0,
                'makkah_distance': str(row[10]) if row[10] else 'N/A',
                'madinah_hotel': str(row[11]) if row[11] else 'TBD',
                'madinah_rating': int(row[12]) if row[12] else 0,
                'madinah_distance': str(row[13]) if row[13] else 'N/A',
                'inclusions': str(row[14]) if row[14] else '',
                'exclusions': str(row[15]) if row[15] else '',
                'group_size': str(row[16]) if row[16] else 'Flexible',
                'departure_dates': str(row[17]) if row[17] else 'Various',
                'views': int(row[18]) if row[18] else 0,
                'inquiries': int(row[19]) if row[19] else 0,
                'company': str(row[20]) if row[20] else 'Unknown',
                'company_email': str(row[21]) if row[21] else '',
                'company_phone': str(row[22]) if row[22] else '',
                'company_website': str(row[23]) if row[23] else ''
            }
        
        return None
        
    except sqlite3.OperationalError as e:
        print(f"Database error getting package: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error getting package: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def search_packages(keyword, user_country=None):
    """Search packages by keyword with error handling"""
    conn = None
    try:
        if not keyword:
            return []
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        search_term = f"%{keyword}%"
        
        c.execute('''SELECT p.package_id, p.package_name, p.duration_days, p.duration_nights,
                     p.price, p.category, p.departure_city, p.target_countries,
                     a.company_name
                     FROM packages p
                     JOIN agent_partners a ON p.agent_id = a.agent_id
                     WHERE (p.package_name LIKE ? OR p.category LIKE ? OR p.departure_city LIKE ?)
                     AND p.status='Active' AND a.status='Active'
                     ORDER BY p.created_at DESC''',
                  (search_term, search_term, search_term))
        
        packages = []
        for row in c.fetchall():
            try:
                target_countries = str(row[7]) if row[7] else ""
                
                # Filter by user country if provided
                if user_country and target_countries:
                    if user_country not in target_countries and "All Countries" not in target_countries:
                        continue
                
                packages.append({
                    'id': str(row[0]),
                    'name': str(row[1]),
                    'duration': f"{row[2]} Days / {row[3]} Nights",
                    'price': float(row[4]) if row[4] else 0.0,
                    'category': str(row[5]) if row[5] else 'Standard',
                    'departure_city': str(row[6]) if row[6] else 'Unknown',
                    'company': str(row[8]) if row[8] else 'Unknown'
                })
            except (ValueError, TypeError) as e:
                print(f"Error parsing search result: {e}")
                continue
        
        return packages
        
    except sqlite3.OperationalError as e:
        print(f"Database error searching packages: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error searching packages: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def get_featured_packages(limit=5):
    """Get featured packages with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('''SELECT p.package_id, p.package_name, p.price, p.category,
                     a.company_name
                     FROM packages p
                     JOIN agent_partners a ON p.agent_id = a.agent_id
                     WHERE p.featured=1 AND p.status='Active' AND a.status='Active'
                     ORDER BY p.views DESC
                     LIMIT ?''',
                  (int(limit),))
        
        packages = []
        for row in c.fetchall():
            packages.append({
                'id': str(row[0]),
                'name': str(row[1]),
                'price': float(row[2]) if row[2] else 0.0,
                'category': str(row[3]) if row[3] else 'Standard',
                'company': str(row[4]) if row[4] else 'Unknown'
            })
        
        return packages
        
    except Exception as e:
        print(f"Error getting featured packages: {e}")
        return []
        
    finally:
        if conn:
            conn.close()

# ========== CHECKLIST FUNCTIONS ==========

def get_umrah_checklist():
    """Complete Umrah travel checklist"""
    return {
        "📄 Documents (Critical)": {
            "items": [
                "Valid passport (min. 6 months validity)",
                "Umrah visa (processed by agent)",
                "Flight tickets (print + digital)",
                "Hotel booking confirmation",
                "Travel insurance policy",
                "Vaccination certificates (if required)",
                "Emergency contact details",
                "Photocopy of all documents",
                "Agent contact information"
            ],
            "priority": "critical"
        },
        "👕 Clothing & Ihram": {
            "items": [
                "Ihram (2 white unstitched cloths - men)",
                "Extra Ihram set (backup)",
                "Modest Islamic clothing (women)",
                "Comfortable walking shoes",
                "Sandals for Ihram",
                "Light jacket",
                "Sleepwear",
                "Undergarments (1 week supply)"
            ],
            "priority": "high"
        },
        "🧴 Toiletries & Personal Care": {
            "items": [
                "Unscented soap/body wash",
                "Unscented shampoo",
                "Toothbrush & toothpaste",
                "Sunscreen (unscented, SPF 50+)",
                "Hand sanitizer",
                "Tissues & wet wipes"
            ],
            "priority": "high"
        },
        "💊 Health & Medications": {
            "items": [
                "Prescription medications",
                "Pain relievers",
                "Digestive medicine",
                "First aid kit",
                "Face masks",
                "Vitamins"
            ],
            "priority": "critical"
        },
        "🕌 Religious Items": {
            "items": [
                "Small Quran (pocket-sized)",
                "Dua book",
                "Prayer mat (lightweight)",
                "Tasbih (prayer beads)",
                "Zamzam water container (empty)"
            ],
            "priority": "medium"
        }
    }

def save_checklist_progress(user_id, category, item, checked):
    """Save checklist progress"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    if checked:
        c.execute('INSERT OR REPLACE INTO checklist_progress VALUES (?,?,?,?)',
                  (user_id, category, item, 1))
    else:
        c.execute('DELETE FROM checklist_progress WHERE user_id=? AND category=? AND item=?',
                  (user_id, category, item))
    
    conn.commit()
    conn.close()

def get_checklist_progress(user_id):
    """Get checklist progress"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('SELECT category, item FROM checklist_progress WHERE user_id=? AND checked=1',
              (user_id,))
    
    checked_items = {}
    for row in c.fetchall():
        if row[0] not in checked_items:
            checked_items[row[0]] = []
        checked_items[row[0]].append(row[1])
    
    conn.close()
    return checked_items

# ========== DATA: UMRAH STEPS ==========

UMRAH_STEPS = [
    {
        "id": 1,
        "title": "1. Prepare for Ihram",
        "description": "Perform Ghusl (ritual bath) and wear Ihram garments before reaching Miqat",
        "dua_arabic": "لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ، لَبَّيْكَ لَا شَرِيكَ لَكَ لَبَّيْكَ، إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ، لَا شَرِيكَ لَكَ",
        "dua_transliteration": "Labbayka Allahumma labbayk, labbayka la shareeka laka labbayk, innal-hamda wan-ni'mata laka wal-mulk, la shareeka lak",
        "dua_english": "Here I am, O Allah, here I am. Here I am, You have no partner, here I am. Verily all praise, grace and sovereignty belong to You. You have no partner.",
        "details": [
            "Perform Ghusl (full body wash) or at minimum Wudu",
            "Men: Wear two white unstitched cloths (Izar for lower body, Rida for upper body)",
            "Women: Wear modest Islamic clothing (any color, covering entire body except face and hands)",
            "Apply unscented products only (no perfume after Ihram)",
            "Make intention (Niyyah) for Umrah in your heart",
            "Pray 2 Rakah (if not a forbidden time)",
            "Start reciting Talbiyah loudly (men) or softly (women)",
            "From this point: No perfume, no cutting hair/nails, no intimate relations, no hunting"
        ]
    },
    {
        "id": 2,
        "title": "2. Enter Masjid al-Haram",
        "description": "Enter the sacred mosque with right foot first and make dua",
        "dua_arabic": "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ",
        "dua_transliteration": "Allahumma aftah lee abwaaba rahmatik",
        "dua_english": "O Allah, open for me the doors of Your mercy",
        "details": [
            "Enter with your right foot first",
            "Continue reciting Talbiyah until you see the Kaaba",
            "When you first see the Kaaba, raise your hands and make dua (special moment - duas accepted)",
            "Say 'Allahu Akbar' and send blessings upon Prophet Muhammad ﷺ",
            "Approach the Black Stone (Hajar al-Aswad) if possible",
            "Stop reciting Talbiyah when you start Tawaf"
        ]
    },
    {
        "id": 3,
        "title": "3. Perform Tawaf",
        "description": "Circle the Kaaba 7 times counter-clockwise, starting and ending at the Black Stone",
        "dua_arabic": "بِسْمِ اللهِ وَاللهُ أَكْبَرُ، اللَّهُمَّ إِيمَانًا بِكَ وَتَصْدِيقًا بِكِتَابِكَ وَوَفَاءً بِعَهْدِكَ وَاتِّبَاعًا لِسُنَّةِ نَبِيِّكَ مُحَمَّدٍ صَلَّى اللهُ عَلَيْهِ وَسَلَّمَ",
        "dua_transliteration": "Bismillahi wallahu akbar. Allahumma eemanan bika wa tasdeeqan bikitabika wa wafa'an bi'ahdika wattiba'an lisunnati nabiyyika Muhammad (ﷺ)",
        "dua_english": "In the name of Allah, Allah is the Greatest. O Allah, out of faith in You, belief in Your Book, fulfillment of Your covenant and following the Sunnah of Your Prophet Muhammad (ﷺ)",
        "details": [
            "Start at the Black Stone - kiss it if possible, or touch and kiss your hand, or just point to it",
            "Say 'Bismillahi Wallahu Akbar' when starting",
            "Men only: Uncover right shoulder (Idtiba) during all 7 circuits",
            "Men only: Walk briskly (Ramal) during first 3 circuits, normal pace for last 4",
            "Women: Walk at normal pace for all 7 circuits",
            "Make any dua you want during Tawaf (in any language)",
            "Between Yemeni Corner and Black Stone, say: 'Rabbana atina fid-dunya hasanah wa fil-akhirati hasanah wa qina adhaban-nar'",
            "Complete 7 full circuits (one circuit = from Black Stone back to Black Stone)",
            "After Tawaf: Cover right shoulder, pray 2 Rakah behind Maqam Ibrahim (or anywhere in the Haram if crowded)"
        ]
    },
    {
        "id": 4,
        "title": "4. Drink Zamzam Water",
        "description": "Drink the blessed Zamzam water and make dua",
        "dua_arabic": "اللَّهُمَّ إِنِّي أَسْأَلُكَ عِلْمًا نَافِعًا وَرِزْقًا وَاسِعًا وَشِفَاءً مِنْ كُلِّ دَاءٍ",
        "dua_transliteration": "Allahumma inni as'aluka 'ilman nafi'a, wa rizqan wasi'a, wa shifa'an min kulli da'",
        "dua_english": "O Allah, I ask You for beneficial knowledge, abundant provision, and healing from every disease",
        "details": [
            "Zamzam stations are available throughout the Haram",
            "Face the Qibla (Kaaba) when drinking if possible",
            "Drink while standing (Sunnah)",
            "Drink in 3 breaths (pause between gulps)",
            "Make dua while drinking - Prophet ﷺ said 'Zamzam is for whatever it is drunk for'",
            "You can drink as much as you want",
            "Can take Zamzam bottles home for family and friends"
        ]
    },
    {
        "id": 5,
        "title": "5. Perform Sa'i",
        "description": "Walk between the hills of Safa and Marwa 7 times, starting at Safa",
        "dua_arabic": "إِنَّ الصَّفَا وَالْمَرْوَةَ مِنْ شَعَائِرِ اللَّهِ فَمَنْ حَجَّ الْبَيْتَ أَوِ اعْتَمَرَ فَلَا جُنَاحَ عَلَيْهِ أَنْ يَطَّوَّفَ بِهِمَا وَمَنْ تَطَوَّعَ خَيْرًا فَإِنَّ اللَّهَ شَاكِرٌ عَلِيمٌ",
        "dua_transliteration": "Inna as-Safa wal-Marwata min sha'a'irillah. Faman hajjal-bayta awi'tamara fala junaha 'alayhi an yattawwafa bihima. Wa man tatawwa'a khayran fa'innallaha shakirun 'aleem",
        "dua_english": "Indeed, Safa and Marwa are among the symbols of Allah. So whoever makes Hajj or Umrah, there is no blame upon him for walking between them. And whoever volunteers good - then indeed, Allah is appreciative and Knowing",
        "details": [
            "Start at Safa hill - climb up until you can see the Kaaba",
            "Face the Kaaba, raise hands, say 'Allahu Akbar' 3 times",
            "Recite the opening dua (above verse from Quran 2:158)",
            "Walk down towards Marwa - this is lap 1",
            "Men only: Run/jog between the two green lights (about 50 meters)",
            "Women: Walk at normal pace throughout",
            "Reach Marwa, climb up, face Kaaba, raise hands and make dua",
            "Walk back to Safa - this is lap 2",
            "Continue until you complete 7 laps total (end at Marwa)",
            "Make any dua during Sa'i - special time for acceptance",
            "Lap count: Safa→Marwa=1, Marwa→Safa=2, Safa→Marwa=3... end at Marwa=7"
        ]
    },
    {
        "id": 6,
        "title": "6. Halq or Taqsir (Hair Cutting)",
        "description": "Shave head completely (Halq) or trim hair (Taqsir) to complete Umrah",
        "dua_arabic": "الْحَمْدُ لِلَّهِ الَّذِي قَضَى عَنَّا نُسُكَنَا",
        "dua_transliteration": "Alhamdulillahil-ladhi qada 'anna nusukana",
        "dua_english": "All praise is to Allah who enabled us to complete our rites",
        "details": [
            "Men: Complete head shave (Halq) is better and more rewarded",
            "Men: Or trim at least 1 inch (2.5 cm) of hair from all over the head (Taqsir)",
            "Women: Cut only a fingertip's length (about 1-2 cm) from the ends of hair",
            "Women: Do NOT shave head - this is forbidden",
            "Barbers available near Haram for a small fee",
            "After cutting hair, all Ihram restrictions are lifted",
            "You can now remove Ihram and wear normal clothes",
            "You can use perfume, cut nails, etc.",
            "Your Umrah is now COMPLETE! Alhamdulillah!"
        ]
    },
    {
        "id": 7,
        "title": "7. Umrah Completed! 🎉",
        "description": "Congratulations! May Allah accept your Umrah and grant you forgiveness",
        "dua_arabic": "تَقَبَّلَ اللهُ مِنَّا وَمِنكُمْ، رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
        "dua_transliteration": "Taqabbalallahu minna wa minkum. Rabbana atina fid-dunya hasanatan wa fil-akhirati hasanatan wa qina 'adhaban-nar",
        "dua_english": "May Allah accept from us and from you. Our Lord, give us good in this world and good in the Hereafter and protect us from the punishment of the Fire",
        "details": [
            "Make abundant dua of gratitude to Allah",
            "Thank Allah for enabling you to complete this blessed journey",
            "You can perform additional Tawaf (Tawaf al-Nafl) - highly recommended",
            "Visit the Prophet's Mosque in Madinah if you have time",
            "Visit other sacred sites in Makkah and Madinah (see Ziyarat tab)",
            "Maintain the spiritual state and good deeds you gained",
            "Share your experience and encourage others",
            "Make dua for those who couldn't make the journey",
            "Continue learning and growing in your faith"
        ]
    }
]

# ========== HAJJ STEPS DATA ==========

HAJJ_STEPS = [
    {
        'id': 1,
        'title': 'Step 1: Enter Ihram at Meeqat',
        'dua_arabic': 'لَبَّيْكَ اللَّهُمَّ لَبَّيْكَ، لَبَّيْكَ لَا شَرِيكَ لَكَ لَبَّيْكَ، إِنَّ الْحَمْدَ وَالنِّعْمَةَ لَكَ وَالْمُلْكَ، لَا شَرِيكَ لَكَ',
        'dua_transliteration': 'Labbayk Allāhumma labbayk, labbayka lā sharīka laka labbayk',
        'dua_english': 'Here I am, O Allah, here I am. Here I am, You have no partner, here I am.',
        'instructions': [
            'Make intention (niyyah) for Hajj',
            'Perform Ghusl (ritual bath)',
            'Wear Ihram garments',
            'Pray 2 Rakahs',
            'Recite Talbiyah continuously',
            'Enter state of Ihram before Meeqat'
        ]
    },
    {
        'id': 2,
        'title': 'Step 2: Arrival in Makkah - Tawaf al-Qudum',
        'dua_arabic': 'اللَّهُمَّ زِدْ هَذَا الْبَيْتَ تَشْرِيفًا وَتَعْظِيمًا وَتَكْرِيمًا وَمَهَابَةً',
        'dua_transliteration': 'Allāhumma zid hādhā l-bayta tashrīfan wa taʿẓīman wa takrīman wa mahābah',
        'dua_english': 'O Allah, increase this House in honor, esteem, respect and reverence.',
        'instructions': [
            'Perform Tawaf al-Qudum (arrival Tawaf) - 7 circuits around Kaaba',
            'Kiss or touch the Black Stone if possible',
            'Men perform Raml (brisk walking) in first 3 circuits',
            'Pray 2 Rakahs behind Maqam Ibrahim',
            'Drink Zamzam water',
            'Perform Sa\'i between Safa and Marwa (7 laps)',
            'This Tawaf is Sunnah for those performing Hajj al-Ifrad or Qiran'
        ]
    },
    {
        'id': 3,
        'title': 'Step 3: Day of Tarwiyah (8th Dhul Hijjah)',
        'dua_arabic': 'اللَّهُمَّ إِنِّي أُرِيدُ الْحَجَّ فَيَسِّرْهُ لِي وَتَقَبَّلْهُ مِنِّي',
        'dua_transliteration': 'Allāhumma innī urīdu l-ḥajja fa-yassirhu lī wa taqabbalhu minnī',
        'dua_english': 'O Allah, I intend to perform Hajj, so make it easy for me and accept it from me.',
        'instructions': [
            'Proceed to Mina after sunrise',
            'Pray Dhuhr, Asr, Maghrib, Isha and Fajr in Mina',
            'Shorten 4-rakah prayers to 2 rakahs',
            'Do not combine prayers',
            'Stay overnight in Mina (Sunnah)',
            'Engage in dhikr and dua',
            'Prepare mentally and spiritually for Arafat'
        ]
    },
    {
        'id': 4,
        'title': 'Step 4: Day of Arafat (9th Dhul Hijjah) - Most Important Day',
        'dua_arabic': 'لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ',
        'dua_transliteration': 'Lā ilāha illallāhu waḥdahu lā sharīka lah, lahu l-mulku wa lahu l-ḥamd, wa huwa ʿalā kulli shayʾin qadīr',
        'dua_english': 'There is no deity except Allah, alone, without partner. To Him belongs dominion and to Him belongs praise, and He is over all things competent.',
        'instructions': [
            'Depart for Arafat after sunrise',
            'Arrive at Arafat before Dhuhr',
            'Pray Dhuhr and Asr combined and shortened at Dhuhr time',
            'Stay within boundaries of Arafat until sunset (ESSENTIAL)',
            'Stand at Arafat from Dhuhr to sunset - this is the MAIN pillar of Hajj',
            'Make abundant dua, dhikr, and seek forgiveness',
            'Face Qibla and raise hands in supplication',
            'The Prophet said: "Hajj is Arafat"'
        ]
    },
    {
        'id': 5,
        'title': 'Step 5: Night in Muzdalifah (9th night)',
        'dua_arabic': 'اللَّهُمَّ أَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ',
        'dua_transliteration': 'Allāhumma aʿinnī ʿalā dhikrika wa shukrika wa ḥusni ʿibādatik',
        'dua_english': 'O Allah, help me to remember You, to thank You, and to worship You in the best manner.',
        'instructions': [
            'Leave Arafat immediately after sunset (do not pray Maghrib in Arafat)',
            'Proceed to Muzdalifah with calm and patience',
            'Pray Maghrib and Isha combined at Isha time in Muzdalifah',
            'Collect 49 pebbles for stoning (or collect them in Mina)',
            'Stay overnight in Muzdalifah (obligatory)',
            'Pray Fajr early and make dua until nearly sunrise',
            'Women and elderly may leave after midnight'
        ]
    },
    {
        'id': 6,
        'title': 'Step 6: Day of Eid (10th Dhul Hijjah) - Yawm an-Nahr',
        'dua_arabic': 'بِسْمِ اللَّهِ وَاللَّهُ أَكْبَرُ، اللَّهُمَّ مِنْكَ وَلَكَ',
        'dua_transliteration': 'Bismillāhi wallāhu akbar, Allāhumma minka wa lak',
        'dua_english': 'In the name of Allah, Allah is the Greatest. O Allah, from You and for You.',
        'instructions': [
            'Return to Mina before sunrise',
            'Stone the large Jamrah (Jamrat al-Aqabah) with 7 pebbles after sunrise',
            'Say "Bismillah, Allahu Akbar" with each throw',
            'Offer sacrifice (Hadi) - obligatory for Hajj al-Tamattu and Qiran',
            'Shave head (men) or trim hair (women)',
            'First Tahallul - Most Ihram restrictions lifted',
            'Return to Makkah and perform Tawaf al-Ifadah (obligatory)',
            'Perform Sa\'i if doing Hajj al-Tamattu',
            'Return to Mina for the night'
        ]
    },
    {
        'id': 7,
        'title': 'Step 7: Days of Tashriq (11th, 12th, 13th Dhul Hijjah)',
        'dua_arabic': 'اللَّهُمَّ اغْفِرْ لِي وَارْحَمْنِي وَاهْدِنِي وَعَافِنِي وَارْزُقْنِي',
        'dua_transliteration': 'Allāhumma ghfir lī wa-rḥamnī wa-hdinī wa-ʿāfinī wa-rzuqnī',
        'dua_english': 'O Allah, forgive me, have mercy upon me, guide me, give me health, and grant me sustenance.',
        'instructions': [
            'Stay in Mina for 2-3 days',
            'Stone all three Jamarat daily after Dhuhr (21 pebbles per day)',
            'Order: Small, Medium, then Large Jamrah',
            'Make dua after stoning Small and Medium Jamrahs',
            'Can leave on 12th after sunset (hastening) or stay until 13th',
            'If staying, stone on 13th as well',
            'Make abundant dhikr and takbeer'
        ]
    },
    {
        'id': 8,
        'title': 'Step 8: Farewell Tawaf (Tawaf al-Wada)',
        'dua_arabic': 'اللَّهُمَّ تَقَبَّلْ مِنِّي وَأَعِنِّي عَلَى ذِكْرِكَ وَشُكْرِكَ وَحُسْنِ عِبَادَتِكَ',
        'dua_transliteration': 'Allāhumma taqabbal minnī wa aʿinnī ʿalā dhikrika wa shukrika wa ḥusni ʿibādatik',
        'dua_english': 'O Allah, accept from me and help me to remember You, to thank You, and to worship You well.',
        'instructions': [
            'Perform Farewell Tawaf before leaving Makkah (obligatory)',
            'This should be the last thing you do in Makkah',
            'Make dua for acceptance of your Hajj',
            'Drink Zamzam water',
            'Look at the Kaaba with love and longing',
            'Make dua to return again',
            'Leave Masjid al-Haram with left foot first',
            'Your Hajj is now complete - Hajj Mabrur!'
        ]
    }
]

# ========== HAJJ GUIDE PAGE ==========

def show_hajj_guide():
    """Display Hajj step-by-step guide"""
    st.markdown("## 🕋 Complete Hajj Guide with Duas")
    
    st.info("""
    **Important:** Hajj is performed during specific dates (8th-13th Dhul Hijjah). 
    This guide covers the major steps of Hajj al-Tamattu, the most common type.
    """)
    
    # Get completed steps
    completed_steps = get_user_progress(st.session_state.user_id, guide_type='hajj')
    
    # Progress indicator
    progress_percentage = (len(completed_steps) / len(HAJJ_STEPS)) * 100
    st.progress(progress_percentage / 100)
    st.caption(f"Progress: {len(completed_steps)}/{len(HAJJ_STEPS)} steps completed ({progress_percentage:.0f}%)")
    
    st.markdown("---")
    
    for step in HAJJ_STEPS:
        is_done = step['id'] in completed_steps
        
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            checked = st.checkbox("", value=is_done, key=f"hajj_s{step['id']}", 
                                 label_visibility="collapsed")
            if checked != is_done:
                save_step_progress(st.session_state.user_id, step['id'], checked, guide_type='hajj')
                st.rerun()
        
        with col2:
            icon = "✅" if is_done else "⭕"
            with st.expander(f"{icon} **{step['title']}**", expanded=not is_done):
                st.markdown(f"""
                <div class="dua-box">
                    <h4 style="color: #047857; margin-top: 0;">📿 Dua:</h4>
                    <p class="arabic-text">{step['dua_arabic']}</p>
                    <p style="font-style: italic; color: #047857; margin: 0.5rem 0;">
                        <strong>Transliteration:</strong><br>
                        {step['dua_transliteration']}
                    </p>
                    <p style="color: #065f46; margin: 0.5rem 0;">
                        <strong>Translation:</strong><br>
                        {step['dua_english']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("**📝 Instructions:**")
                
                for idx, instruction in enumerate(step['instructions'], 1):
                    st.markdown(f"{idx}. {instruction}")
                
                if not is_done:
                    st.info("💡 Check the box when complete!")
    
    if len(completed_steps) == len(HAJJ_STEPS):
        st.balloons()
        st.success("🎉 **Hajj Mabrur! May Allah accept your Hajj!**")

# ========== ZIYARATH PLACES DATA ==========

ZIYARATH_PLACES = [
    {
        'id': 1,
        'title': '🕌 Masjid al-Haram (Makkah)',
        'location': 'Makkah, Saudi Arabia',
        'description': 'The holiest mosque in Islam, home to the Kaaba',
        'dua': 'Recite Talbiyah and make dua for acceptance',
        'tips': [
            'Visit during less crowded times (after Fajr, before Maghrib)',
            'Perform multiple Tawafs if time permits',
            'Pray in different areas of the Haram',
            'Drink Zamzam water abundantly',
            'Visit the Mataaf (Tawaf area) during night for cooler weather',
            'Make dua at Multazam (between Black Stone and door of Kaaba)'
        ]
    },
    {
        'id': 2,
        'title': '🕌 Masjid an-Nabawi (Madinah)',
        'location': 'Madinah, Saudi Arabia',
        'description': 'The Prophet\'s Mosque, second holiest site in Islam',
        'dua': 'Send Salawat upon the Prophet (PBUH)',
        'tips': [
            'Visit the Prophet\'s grave and give Salam',
            'Visit graves of Abu Bakr (RA) and Umar (RA)',
            'Pray in Rawdah (the garden between pulpit and grave)',
            'Offer 40 consecutive prayers if possible',
            'Women should visit during designated times',
            'Explore the museum inside the mosque'
        ]
    },
    {
        'id': 3,
        'title': '🕌 Masjid Quba',
        'location': 'Madinah, Saudi Arabia',
        'description': 'First mosque built in Islam',
        'dua': 'Make dua for forgiveness and blessings',
        'tips': [
            'Pray 2 Rakahs Tahiyyat al-Masjid',
            'Visit on Saturday morning if possible (Sunnah)',
            'Reward equals one Umrah for praying here',
            'Located about 5 km from Masjid an-Nabawi',
            'Take time to reflect on Islamic history',
            'Accessible by bus or taxi from Madinah'
        ]
    },
    {
        'id': 4,
        'title': '⛰️ Mount Uhud',
        'location': 'Madinah, Saudi Arabia',
        'description': 'Site of the Battle of Uhud',
        'dua': 'Make dua for the martyrs and for steadfastness',
        'tips': [
            'Visit the Martyrs\' Cemetery at the base',
            'Learn about the Battle of Uhud',
            'Remember the 70 companions who were martyred',
            'Visit the site where Hamza (RA) is buried',
            'Reflect on lessons of patience and perseverance',
            'Best visited early morning or late afternoon'
        ]
    },
    {
        'id': 5,
        'title': '⛰️ Cave of Hira',
        'location': 'Makkah, Saudi Arabia',
        'description': 'Where Prophet Muhammad (PBUH) received first revelation',
        'dua': 'Recite Surah Alaq (first revelation)',
        'tips': [
            'Climb is steep and takes 1-2 hours',
            'Wear comfortable shoes and bring water',
            'Best visited in cooler months',
            'Go early morning to avoid heat',
            'Reflect on the Prophet\'s spiritual retreat',
            'Not obligatory, but spiritually meaningful'
        ]
    },
    {
        'id': 6,
        'title': '⛰️ Cave of Thawr',
        'location': 'Makkah, Saudi Arabia',
        'description': 'Where Prophet (PBUH) hid during migration to Madinah',
        'dua': 'Remember the Hijrah and make dua for protection',
        'tips': [
            'Located south of Makkah',
            'Difficult climb, requires good fitness',
            'Remember the spider web and dove miracle',
            'Reflect on trust in Allah (Tawakkul)',
            'Take guide if unfamiliar with the area',
            'Visit during cooler weather'
        ]
    },
    {
        'id': 7,
        'title': '🏛️ Jannat al-Baqi Cemetery',
        'location': 'Madinah, Saudi Arabia',
        'description': 'Historic cemetery where many companions are buried',
        'dua': 'As-salāmu ʿalaykum ahl al-diyār (Peace be upon you, O inhabitants)',
        'tips': [
            'Visit after Fajr or Asr prayers',
            'Many companions are buried here including:',
            '- Uthman ibn Affan (RA)',
            '- Fatimah (RA), daughter of the Prophet',
            '- Abbas (RA), uncle of the Prophet',
            'Make dua for the deceased',
            'Reflect on the temporary nature of this world'
        ]
    },
    {
        'id': 8,
        'title': '🕌 Masjid al-Qiblatain',
        'location': 'Madinah, Saudi Arabia',
        'description': 'Mosque where the Qibla was changed',
        'dua': 'Thank Allah for the blessing of the Kaaba as Qibla',
        'tips': [
            'Historical mosque with two Qiblas (mihrabs)',
            'Learn about the change of Qibla direction',
            'Pray 2 Rakahs and reflect',
            'Located northwest of Masjid an-Nabawi',
            'Open 24/7 for visitors',
            'Good for family visits and Islamic education'
        ]
    },
    {
        'id': 9,
        'title': '🏛️ Makkah Museum',
        'location': 'Makkah, Saudi Arabia',
        'description': 'Museum with Islamic history and artifacts',
        'dua': 'Increase in knowledge and understanding',
        'tips': [
            'Learn about the history of Makkah',
            'See artifacts from Islamic civilization',
            'Educational for children',
            'Air-conditioned and comfortable',
            'Check opening hours before visiting',
            'Great way to spend time between prayers'
        ]
    },
    {
        'id': 10,
        'title': '🏛️ Clock Tower Museum',
        'location': 'Makkah, Saudi Arabia',
        'description': 'Museum at the top of Abraj Al Bait tower',
        'dua': 'Reflect on modern Muslim achievements',
        'tips': [
            'Panoramic view of Masjid al-Haram',
            'Learn about Islamic timekeeping',
            'Best views at night',
            'Requires booking and entry fee',
            'Take elevator to observation deck',
            'Great for photos (within Islamic guidelines)'
        ]
    }
]

# ========== SALAH STEPS DATA ==========

SALAH_STEPS = [
    {
        'id': 1,
        'title': 'Step 1: Make Intention (Niyyah) & Stand (Qiyam)',
        'dua_arabic': 'نَوَيْتُ أَنْ أُصَلِّيَ لِلَّهِ تَعَالَى',
        'dua_transliteration': 'Nawaitu an usalliya lillahi ta\'ala',
        'dua_english': 'I intend to pray for the sake of Allah',
        'instructions': [
            'Make intention in your heart for the specific prayer (Fajr, Dhuhr, Asr, Maghrib, Isha)',
            'Face the Qibla (direction of Kaaba in Makkah)',
            'Stand upright with feet shoulder-width apart',
            'Look at the place where you will prostrate',
            'Keep your mind focused and heart present',
            'Intention is in the heart, saying it out loud is not required'
        ]
    },
    {
        'id': 2,
        'title': 'Step 2: Raise Hands & Say Takbir (Allahu Akbar)',
        'dua_arabic': 'اللَّهُ أَكْبَرُ',
        'dua_transliteration': 'Allahu Akbar',
        'dua_english': 'Allah is the Greatest',
        'instructions': [
            'Raise both hands up to shoulder or ear level',
            'Palms facing forward (Qibla direction)',
            'Say "Allahu Akbar" clearly',
            'This marks the start of prayer - from now on, complete focus required',
            'Do not look around or move unnecessarily',
            'Women raise hands to shoulder level, men to ears'
        ]
    },
    {
        'id': 3,
        'title': 'Step 3: Place Hands & Recite Opening Dua',
        'dua_arabic': 'سُبْحَانَكَ اللَّهُمَّ وَبِحَمْدِكَ، وَتَبَارَكَ اسْمُكَ، وَتَعَالَى جَدُّكَ، وَلَا إِلَهَ غَيْرُكَ',
        'dua_transliteration': 'Subhanaka Allahumma wa bihamdika, wa tabarakasmuka, wa ta\'ala jadduka, wa la ilaha ghayruk',
        'dua_english': 'Glory be to You, O Allah, and praise be to You. Blessed is Your name, exalted is Your majesty, and there is no god but You.',
        'instructions': [
            'Men: Place right hand over left hand on the chest',
            'Women: Place right hand over left hand on the chest (same as men)',
            'Recite the opening dua (Thana) silently',
            'Then say: "A\'udhu billahi minash-shaytanir-rajeem" (I seek refuge in Allah from Satan)',
            'Then say: "Bismillahir-Rahmanir-Raheem" (In the name of Allah, Most Gracious, Most Merciful)',
            'Keep eyes focused on the place of prostration'
        ]
    },
    {
        'id': 4,
        'title': 'Step 4: Recite Surah Al-Fatihah',
        'dua_arabic': 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ ۝ الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ۝ الرَّحْمَٰنِ الرَّحِيمِ ۝ مَالِكِ يَوْمِ الدِّينِ ۝ إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ ۝ اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ ۝ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ',
        'dua_transliteration': 'Bismillahir-Rahmanir-Raheem. Alhamdu lillahi Rabbil-\'alameen. Ar-Rahmanir-Raheem. Maliki yawmid-deen. Iyyaka na\'budu wa iyyaka nasta\'een. Ihdinas-siratal-mustaqeem. Siratal-ladheena an\'amta \'alayhim ghayril-maghdubi \'alayhim wa lad-dalleen.',
        'dua_english': 'In the name of Allah, Most Gracious, Most Merciful. All praise is due to Allah, Lord of the worlds. The Most Gracious, the Most Merciful. Master of the Day of Judgment. You alone we worship, and You alone we ask for help. Guide us on the Straight Path. The path of those You have blessed, not of those who have earned Your anger or gone astray.',
        'instructions': [
            'Recite Surah Al-Fatihah (MANDATORY - prayer invalid without it)',
            'Recite clearly and at a moderate pace',
            'After finishing, say "Ameen" (softly in silent prayers, audibly when praying alone)',
            'In Fajr, Maghrib, and Isha: Imam recites loudly, you listen',
            'In Dhuhr and Asr: Everyone recites silently',
            'Al-Fatihah must be recited in every Rakah'
        ]
    },
    {
        'id': 5,
        'title': 'Step 5: Recite Additional Quran',
        'dua_arabic': 'قُلْ هُوَ اللَّهُ أَحَدٌ ۝ اللَّهُ الصَّمَدُ ۝ لَمْ يَلِدْ وَلَمْ يُولَدْ ۝ وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ',
        'dua_transliteration': 'Qul huwa Allahu ahad. Allahus-samad. Lam yalid wa lam yoolad. Wa lam yakun lahu kufuwan ahad.',
        'dua_english': 'Say: He is Allah, the One. Allah, the Eternal. He neither begets nor is born. Nor is there to Him any equivalent. (Surah Al-Ikhlas 112)',
        'instructions': [
            'After Al-Fatihah, recite any portion of Quran',
            'Common choices: Surah Al-Ikhlas, Al-Kawthar, Al-Asr, Al-Fil',
            'Only in first 2 Rakahs (not in 3rd and 4th Rakah)',
            'The longer the recitation, the more reward',
            'Must be at least 3 short verses or 1 long verse',
            'Can repeat the same Surah in different Rakahs'
        ]
    },
    {
        'id': 6,
        'title': 'Step 6: Bowing (Ruku)',
        'dua_arabic': 'سُبْحَانَ رَبِّيَ الْعَظِيمِ',
        'dua_transliteration': 'Subhana Rabbiyal-Adheem',
        'dua_english': 'Glory be to my Lord, the Most Great',
        'instructions': [
            'Say "Allahu Akbar" and bow down',
            'Place hands on knees with fingers spread',
            'Keep back straight (parallel to ground)',
            'Head in line with back, not raised or lowered',
            'Say "Subhana Rabbiyal-Adheem" 3 times minimum',
            'Stay in Ruku for at least the time it takes to say the Tasbih 3 times'
        ]
    },
    {
        'id': 7,
        'title': 'Step 7: Standing After Ruku',
        'dua_arabic': 'سَمِعَ اللَّهُ لِمَنْ حَمِدَهُ، رَبَّنَا وَلَكَ الْحَمْدُ',
        'dua_transliteration': 'Sami\'a Allahu liman hamidah, Rabbana wa lakal-hamd',
        'dua_english': 'Allah hears those who praise Him. Our Lord, to You belongs all praise.',
        'instructions': [
            'Rise from Ruku saying "Sami\'a Allahu liman hamidah"',
            'Stand fully upright',
            'After standing, say "Rabbana wa lakal-hamd"',
            'Raise hands to shoulders/ears (optional, but Sunnah)',
            'Stand calmly for a moment',
            'This position is called "Qawmah"'
        ]
    },
    {
        'id': 8,
        'title': 'Step 8: First Prostration (Sujud)',
        'dua_arabic': 'سُبْحَانَ رَبِّيَ الْأَعْلَى',
        'dua_transliteration': 'Subhana Rabbiyal-A\'la',
        'dua_english': 'Glory be to my Lord, the Most High',
        'instructions': [
            'Say "Allahu Akbar" and go down to prostration',
            'Seven parts must touch ground: forehead, nose, both palms, both knees, both feet (toes)',
            'Forehead and nose must both touch the ground',
            'Arms should not touch the ground (keep elbows raised)',
            'Say "Subhana Rabbiyal-A\'la" 3 times minimum',
            'This is the closest position to Allah - make sincere dua!',
            'Keep feet upright with toes pointing toward Qibla'
        ]
    },
    {
        'id': 9,
        'title': 'Step 9: Sitting Between Prostrations',
        'dua_arabic': 'رَبِّ اغْفِرْ لِي، رَبِّ اغْفِرْ لِي',
        'dua_transliteration': 'Rabbigh-fir lee, Rabbigh-fir lee',
        'dua_english': 'My Lord, forgive me. My Lord, forgive me.',
        'instructions': [
            'Say "Allahu Akbar" and sit up from Sujud',
            'Sit on left foot, right foot upright (toes pointing to Qibla)',
            'Place hands on thighs/knees',
            'Say "Rabbigh-fir lee" at least once (2 times is better)',
            'Sit calmly for a moment',
            'This sitting is called "Jalsa"'
        ]
    },
    {
        'id': 10,
        'title': 'Step 10: Second Prostration',
        'dua_arabic': 'سُبْحَانَ رَبِّيَ الْأَعْلَى',
        'dua_transliteration': 'Subhana Rabbiyal-A\'la',
        'dua_english': 'Glory be to my Lord, the Most High',
        'instructions': [
            'Say "Allahu Akbar" and prostrate again',
            'Same position as first prostration',
            'Say "Subhana Rabbiyal-A\'la" 3 times minimum',
            'Make dua (any dua in any language)',
            'This completes ONE Rakah',
            'For 2nd Rakah: Stand up saying "Allahu Akbar" and repeat from Step 4'
        ]
    },
    {
        'id': 11,
        'title': 'Step 11: Tashahhud (Sitting for Testament)',
        'dua_arabic': 'التَّحِيَّاتُ لِلَّهِ وَالصَّلَوَاتُ وَالطَّيِّبَاتُ، السَّلَامُ عَلَيْكَ أَيُّهَا النَّبِيُّ وَرَحْمَةُ اللَّهِ وَبَرَكَاتُهُ، السَّلَامُ عَلَيْنَا وَعَلَى عِبَادِ اللَّهِ الصَّالِحِينَ، أَشْهَدُ أَنْ لَا إِلَٰهَ إِلَّا اللَّهُ وَأَشْهَدُ أَنَّ مُحَمَّدًا عَبْدُهُ وَرَسُولُهُ',
        'dua_transliteration': 'At-tahiyyatu lillahi was-salawatu wat-tayyibat. As-salamu \'alayka ayyuhan-Nabiyyu wa rahmatullahi wa barakatuh. As-salamu \'alayna wa \'ala \'ibadillahis-salihin. Ashhadu an la ilaha illallah wa ashhadu anna Muhammadan \'abduhu wa rasooluh.',
        'dua_english': 'All greetings, prayers and good things are for Allah. Peace be upon you, O Prophet, and the mercy of Allah and His blessings. Peace be upon us and upon the righteous servants of Allah. I bear witness that there is no god but Allah, and I bear witness that Muhammad is His servant and messenger.',
        'instructions': [
            'After 2nd Rakah, sit for Tashahhud',
            'Sit on left foot, right foot upright',
            'Place left hand on left thigh, right hand on right thigh',
            'Raise index finger when saying "la ilaha" (point of testimony)',
            'Recite the Tashahhud (At-Tahiyyat)',
            'If prayer is 2 Rakahs (like Fajr), continue to Step 12',
            'If prayer is 3 or 4 Rakahs, stand up after Tashahhud and continue praying'
        ]
    },
    {
        'id': 12,
        'title': 'Step 12: Durood (Salawat on Prophet)',
        'dua_arabic': 'اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ، كَمَا صَلَّيْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ، إِنَّكَ حَمِيدٌ مَجِيدٌ. اللَّهُمَّ بَارِكْ عَلَى مُحَمَّدٍ وَعَلَى آلِ مُحَمَّدٍ، كَمَا بَارَكْتَ عَلَى إِبْرَاهِيمَ وَعَلَى آلِ إِبْرَاهِيمَ، إِنَّكَ حَمِيدٌ مَجِيدٌ',
        'dua_transliteration': 'Allahumma salli \'ala Muhammadin wa \'ala ali Muhammad, kama sallayta \'ala Ibraheema wa \'ala ali Ibraheem, innaka Hameedum-Majeed. Allahumma barik \'ala Muhammadin wa \'ala ali Muhammad, kama barakta \'ala Ibraheema wa \'ala ali Ibraheem, innaka Hameedum-Majeed.',
        'dua_english': 'O Allah, send prayers upon Muhammad and the family of Muhammad, as You sent prayers upon Ibrahim and the family of Ibrahim; You are Praiseworthy and Glorious. O Allah, send blessings upon Muhammad and the family of Muhammad, as You blessed Ibrahim and the family of Ibrahim; You are Praiseworthy and Glorious.',
        'instructions': [
            'In final sitting (after last Rakah), recite Durood after Tashahhud',
            'This is sending blessings upon Prophet Muhammad ﷺ',
            'Recite the Durood Ibrahim (above)',
            'You can also make any personal dua at this point',
            'Ask for forgiveness, Jannah, health, guidance, etc.',
            'Keep it brief and sincere'
        ]
    },
    {
        'id': 13,
        'title': 'Step 13: Ending Prayer (Tasleem)',
        'dua_arabic': 'السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللَّهِ',
        'dua_transliteration': 'As-salamu \'alaykum wa rahmatullah',
        'dua_english': 'Peace and mercy of Allah be upon you',
        'instructions': [
            'Turn head to the right and say "As-salamu alaykum wa rahmatullah"',
            'Turn head to the left and say "As-salamu alaykum wa rahmatullah"',
            'With the second Salam, your prayer is complete!',
            'You can now move and talk',
            'Recommended: Say Tasbeeh (33x Subhanallah, 33x Alhamdulillah, 33x Allahu Akbar)',
            'Make dua with hands raised (optional but recommended)'
        ]
    },
    {
        'id': 14,
        'title': 'After Prayer: Dhikr & Dua',
        'dua_arabic': 'أَسْتَغْفِرُ اللَّهَ (3x)، اللَّهُمَّ أَنتَ السَّلَامُ وَمِنكَ السَّلَامُ، تَبَارَكْتَ يَا ذَا الْجَلَالِ وَالْإِكْرَامِ',
        'dua_transliteration': 'Astaghfirullah (3x). Allahumma antas-salam wa minkas-salam, tabarakta ya dhal-jalali wal-ikram.',
        'dua_english': 'I seek forgiveness from Allah (3x). O Allah, You are Peace and from You comes peace. Blessed are You, O Possessor of majesty and honor.',
        'instructions': [
            'Say "Astaghfirullah" 3 times',
            'Recite the after-prayer dua',
            'Tasbeeh: Say "Subhanallah" 33 times',
            'Say "Alhamdulillah" 33 times',
            'Say "Allahu Akbar" 33 times',
            'Complete with "La ilaha illallahu wahdahu la sharika lah, lahul-mulku wa lahul-hamd, wa huwa \'ala kulli shay\'in qadeer"',
            'Read Ayat al-Kursi (Quran 2:255)',
            'Make personal dua'
        ]
    }
]

# ========== ESSENTIAL DUAS DATA ==========

ESSENTIAL_DUAS = [
    {
        'id': 1,
        'category': '🌅 Morning & Evening',
        'title': 'Morning Dua (Upon Waking)',
        'arabic': 'الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ',
        'transliteration': 'Alhamdu lillahil-ladhi ahyana ba\'da ma amatana wa ilayhin-nushoor',
        'translation': 'All praise is for Allah who gave us life after having taken it from us and unto Him is the resurrection.',
        'occasion': 'When waking up from sleep'
    },
    {
        'id': 2,
        'category': '🌅 Morning & Evening',
        'title': 'Evening Dua (Before Sleep)',
        'arabic': 'بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا',
        'transliteration': 'Bismika Allahumma amootu wa ahya',
        'translation': 'In Your name O Allah, I die and I live.',
        'occasion': 'When going to sleep'
    },
    {
        'id': 3,
        'category': '🍽️ Food & Drink',
        'title': 'Before Eating',
        'arabic': 'بِسْمِ اللَّهِ',
        'transliteration': 'Bismillah',
        'translation': 'In the name of Allah.',
        'occasion': 'Before starting any meal'
    },
    {
        'id': 4,
        'category': '🍽️ Food & Drink',
        'title': 'After Eating',
        'arabic': 'الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مُسْلِمِينَ',
        'transliteration': 'Alhamdu lillahil-ladhi at\'amana wa saqana wa ja\'alana muslimeen',
        'translation': 'All praise is for Allah who fed us and gave us drink and made us Muslims.',
        'occasion': 'After finishing a meal'
    },
    {
        'id': 5,
        'category': '🚗 Travel',
        'title': 'When Boarding Vehicle',
        'arabic': 'بِسْمِ اللَّهِ، الْحَمْدُ لِلَّهِ، سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَـٰذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَىٰ رَبِّنَا لَمُنقَلِبُونَ',
        'transliteration': 'Bismillah, Alhamdulillah. Subhanal-ladhi sakh-khara lana hadha wa ma kunna lahu muqrineen. Wa inna ila Rabbina lamunqaliboon.',
        'translation': 'In the name of Allah. All praise is for Allah. Glory to Him who has brought this under our control, for we could not have done so ourselves. And to our Lord we shall surely return.',
        'occasion': 'When entering a car, bus, plane, etc.'
    },
    {
        'id': 6,
        'category': '🏠 Home',
        'title': 'Entering the Home',
        'arabic': 'بِسْمِ اللَّهِ وَلَجْنَا، وَبِسْمِ اللَّهِ خَرَجْنَا، وَعَلَى اللَّهِ رَبِّنَا تَوَكَّلْنَا',
        'transliteration': 'Bismillahi walajna, wa bismillahi kharajna, wa \'alallahi Rabbina tawakkalna',
        'translation': 'In the name of Allah we enter, in the name of Allah we leave, and upon Allah our Lord we depend.',
        'occasion': 'When entering your house'
    },
    {
        'id': 7,
        'category': '🏠 Home',
        'title': 'Leaving the Home',
        'arabic': 'بِسْمِ اللَّهِ، تَوَكَّلْتُ عَلَى اللَّهِ، لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ',
        'transliteration': 'Bismillah, tawakkaltu \'alallah, wa la hawla wa la quwwata illa billah',
        'translation': 'In the name of Allah, I place my trust in Allah, there is no might and no power except with Allah.',
        'occasion': 'When leaving your house'
    },
    {
        'id': 8,
        'category': '🚻 Bathroom',
        'title': 'Entering Bathroom',
        'arabic': 'بِسْمِ اللَّهِ، اللَّهُمَّ إِنِّي أَعُوذُ بِكَ مِنَ الْخُبُثِ وَالْخَبَائِثِ',
        'transliteration': 'Bismillah. Allahumma inni a\'oudhu bika minal-khubuthi wal-khaba\'ith',
        'translation': 'In the name of Allah. O Allah, I seek refuge in You from evil and evil beings.',
        'occasion': 'Before entering the toilet'
    },
    {
        'id': 9,
        'category': '🚻 Bathroom',
        'title': 'Leaving Bathroom',
        'arabic': 'غُفْرَانَكَ',
        'transliteration': 'Ghufranaka',
        'translation': 'I seek Your forgiveness.',
        'occasion': 'After leaving the toilet'
    },
    {
        'id': 10,
        'category': '🤲 General Supplications',
        'title': 'Seeking Forgiveness',
        'arabic': 'أَسْتَغْفِرُ اللَّهَ وَأَتُوبُ إِلَيْهِ',
        'transliteration': 'Astaghfirullah wa atubu ilayh',
        'translation': 'I seek forgiveness from Allah and repent to Him.',
        'occasion': 'Anytime you make a mistake or sin'
    },
    {
        'id': 11,
        'category': '🤲 General Supplications',
        'title': 'When Faced with Difficulty',
        'arabic': 'حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ',
        'transliteration': 'Hasbunallahu wa ni\'mal-wakeel',
        'translation': 'Allah is sufficient for us, and He is the best Disposer of affairs.',
        'occasion': 'During times of hardship or worry'
    },
    {
        'id': 12,
        'category': '🤲 General Supplications',
        'title': 'Gratitude & Praise',
        'arabic': 'الْحَمْدُ لِلَّهِ',
        'transliteration': 'Alhamdulillah',
        'translation': 'All praise is for Allah.',
        'occasion': 'When something good happens or when expressing gratitude'
    },
    {
        'id': 13,
        'category': '💚 Protection',
        'title': 'Ayat al-Kursi (Verse of the Throne)',
        'arabic': 'اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ',
        'transliteration': 'Allahu la ilaha illa Huwal-Hayyul-Qayyum. La ta\'khudhuhu sinatun wa la nawm. Lahu ma fis-samawati wa ma fil-ard...',
        'translation': 'Allah! There is no god but He, the Living, the Self-subsisting. Neither slumber nor sleep overtakes Him. To Him belongs all that is in the heavens and the earth... (Quran 2:255)',
        'occasion': 'After every Fard prayer, before sleep, for protection'
    },
    {
        'id': 14,
        'category': '💚 Protection',
        'title': 'Last Two Verses of Surah Al-Baqarah',
        'arabic': 'آمَنَ الرَّسُولُ بِمَا أُنزِلَ إِلَيْهِ مِن رَّبِّهِ وَالْمُؤْمِنُونَ ۚ كُلٌّ آمَنَ بِاللَّهِ وَمَلَائِكَتِهِ وَكُتُبِهِ وَرُسُلِهِ...',
        'transliteration': 'Amanar-Rasoolu bima unzila ilayhi mir-Rabbihi wal-mu\'minoon...',
        'translation': 'The Messenger believes in what has been sent down to him from his Lord, and so do the believers... (Quran 2:285-286)',
        'occasion': 'Before sleeping - provides protection for the night'
    },
    {
        'id': 15,
        'category': '☔ Weather',
        'title': 'When It Rains',
        'arabic': 'اللَّهُمَّ صَيِّبًا نَافِعًا',
        'transliteration': 'Allahumma sayyiban nafi\'a',
        'translation': 'O Allah, (bring) beneficial rain.',
        'occasion': 'When rain begins to fall'
    },
    {
        'id': 16,
        'category': '👥 Meeting People',
        'title': 'When Seeing Someone in Distress',
        'arabic': 'الْحَمْدُ لِلَّهِ الَّذِي عَافَانِي مِمَّا ابْتَلَاكَ بِهِ وَفَضَّلَنِي عَلَى كَثِيرٍ مِمَّنْ خَلَقَ تَفْضِيلًا',
        'transliteration': 'Alhamdu lillahil-ladhi \'afani mimma-btalaka bihi wa faddalani \'ala katheerin mimman khalaqa tafdheela',
        'translation': 'All praise is for Allah who saved me from what He tested you with and favored me greatly over many of His creatures.',
        'occasion': 'When seeing someone afflicted (say silently in your heart)'
    },
    {
        'id': 17,
        'category': '🌙 Special Times',
        'title': 'Dua on Laylat al-Qadr',
        'arabic': 'اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي',
        'transliteration': 'Allahumma innaka \'afuwwun tuhibbul-\'afwa fa\'fu \'anni',
        'translation': 'O Allah, You are Forgiving and You love forgiveness, so forgive me.',
        'occasion': 'During Laylat al-Qadr (Night of Power) in Ramadan'
    },
    {
        'id': 18,
        'category': '❤️ For Others',
        'title': 'Dua for Parents',
        'arabic': 'رَبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا',
        'transliteration': 'Rabbir-hamhuma kama rabbayani sagheera',
        'translation': 'My Lord, have mercy upon them as they brought me up when I was small.',
        'occasion': 'Anytime - for your parents\' wellbeing'
    },
    {
        'id': 19,
        'category': '❤️ For Others',
        'title': 'When Someone Sneezes',
        'arabic': 'يَرْحَمُكَ اللَّهُ',
        'transliteration': 'Yarhamukallah',
        'translation': 'May Allah have mercy on you.',
        'occasion': 'After someone sneezes and says Alhamdulillah'
    },
    {
        'id': 20,
        'category': '🎯 Success & Guidance',
        'title': 'Dua for Ease',
        'arabic': 'رَبِّ اشْرَحْ لِي صَدْرِي، وَيَسِّرْ لِي أَمْرِي',
        'transliteration': 'Rabbish-rah li sadri, wa yassir li amri',
        'translation': 'My Lord, expand my chest and make my task easy for me.',
        'occasion': 'Before starting any important task'
    }
]

# ========== ZIYARATH GUIDE PAGE ==========

def show_ziyarath_guide():
    """Display Ziyarath (places to visit) guide"""
    st.markdown("## 🗺️ Ziyarath Guide - Sacred Places to Visit")
    
    st.info("""
    **Ziyarath** means visitation. These are recommended places to visit in Makkah and Madinah 
    for spiritual benefit and to connect with Islamic history.
    """)
    
    # Tab selection for cities
    city_tabs = st.tabs(["🕋 Makkah", "🕌 Madinah", "📍 All Places"])
    
    with city_tabs[0]:
        st.markdown("### Places to Visit in Makkah")
        makkah_places = [p for p in ZIYARATH_PLACES if 'Makkah' in p['location']]
        display_ziyarath_places(makkah_places, tab_name="makkah")  # ← Pass tab name
    
    with city_tabs[1]:
        st.markdown("### Places to Visit in Madinah")
        madinah_places = [p for p in ZIYARATH_PLACES if 'Madinah' in p['location']]
        display_ziyarath_places(madinah_places, tab_name="madinah")  # ← Pass tab name
    
    with city_tabs[2]:
        st.markdown("### All Ziyarath Places")
        display_ziyarath_places(ZIYARATH_PLACES, tab_name="all")  # ← Pass tab name

def display_ziyarath_places(places, tab_name="all"):
    """Helper function to display ziyarath places"""
    completed = get_user_progress(st.session_state.user_id, guide_type='ziyarath')
    
    for place in places:
        is_visited = place['id'] in completed
        
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            # Add tab_name to make key unique across tabs
            visited = st.checkbox("", value=is_visited, 
                                 key=f"ziyarath_{tab_name}_{place['id']}", 
                                 label_visibility="collapsed")
            if visited != is_visited:
                save_step_progress(st.session_state.user_id, place['id'], visited, guide_type='ziyarath')
                st.rerun()
        
        with col2:
            icon = "✅" if is_visited else "📍"
            with st.expander(f"{icon} **{place['title']}**"):
                st.markdown(f"**📍 Location:** {place['location']}")
                st.markdown(f"**ℹ️ Description:** {place['description']}")
                
                st.markdown("---")
                st.markdown(f"**🤲 Dua/Remember:** {place['dua']}")
                
                st.markdown("---")
                st.markdown("**💡 Tips:**")
                for tip in place['tips']:
                    st.markdown(f"• {tip}")
                
                if not is_visited:
                    st.info("✓ Check the box when you visit this place!")
    
    visited_count = len([p for p in places if p['id'] in completed])
    st.caption(f"Visited: {visited_count}/{len(places)} places")

# ========== SALAH GUIDE PAGE ==========

def show_salah_guide():
    """Display Salah (Prayer) step-by-step guide"""
    st.markdown("## 🕌 Complete Salah Guide - How to Pray")
    
    st.info("""
    **Salah (Prayer)** is the second pillar of Islam and must be performed 5 times daily.
    This guide will teach you step-by-step how to pray correctly.
    """)
    
    # Quick reference card
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3b82f6, #2563eb);
                padding: 2rem; border-radius: 15px; color: white; margin-bottom: 2rem;">
        <h3 style="margin-top: 0;">⏰ Daily Prayer Times</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
            <div><strong>Fajr:</strong> Before sunrise (2 Rakah)</div>
            <div><strong>Dhuhr:</strong> After noon (4 Rakah)</div>
            <div><strong>Asr:</strong> Afternoon (4 Rakah)</div>
            <div><strong>Maghrib:</strong> After sunset (3 Rakah)</div>
            <div><strong>Isha:</strong> Night (4 Rakah)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Get completed steps
    completed_steps = get_user_progress(st.session_state.user_id, guide_type='salah')
    
    # Progress indicator
    progress_percentage = (len(completed_steps) / len(SALAH_STEPS)) * 100
    st.progress(progress_percentage / 100)
    st.caption(f"Progress: {len(completed_steps)}/{len(SALAH_STEPS)} steps learned ({progress_percentage:.0f}%)")
    
    st.markdown("---")
    
    for step in SALAH_STEPS:
        is_done = step['id'] in completed_steps
        
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            checked = st.checkbox("", value=is_done, key=f"salah_s{step['id']}", 
                                 label_visibility="collapsed")
            if checked != is_done:
                save_step_progress(st.session_state.user_id, step['id'], checked, guide_type='salah')
                st.rerun()
        
        with col2:
            icon = "✅" if is_done else "⭕"
            with st.expander(f"{icon} **{step['title']}**", expanded=not is_done):
                st.markdown(f"""
                <div class="dua-box">
                    <h4 style="color: #047857; margin-top: 0;">📿 Dua/Dhikr:</h4>
                    <p class="arabic-text">{step['dua_arabic']}</p>
                    <p style="font-style: italic; color: #047857; margin: 0.5rem 0;">
                        <strong>Transliteration:</strong><br>
                        {step['dua_transliteration']}
                    </p>
                    <p style="color: #065f46; margin: 0.5rem 0;">
                        <strong>Translation:</strong><br>
                        {step['dua_english']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("**📝 How to Perform:**")
                
                for idx, instruction in enumerate(step['instructions'], 1):
                    st.markdown(f"{idx}. {instruction}")
                
                if not is_done:
                    st.info("💡 Check the box when you've learned this step!")
    
    if len(completed_steps) == len(SALAH_STEPS):
        st.balloons()
        st.success("🎉 **Masha'Allah! You've learned all the steps of Salah!**")
        st.markdown("""
        <div style="background: linear-gradient(135deg, #059669, #10b981);
                    color: white; padding: 2rem; border-radius: 15px; text-align: center;">
            <h2>🕌 Keep Praying Regularly!</h2>
            <p style="font-size: 1.2rem;">
                Prayer is the pillar of religion. May Allah accept your Salah and make you among the regular prayer performers.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ========== ESSENTIAL DUAS PAGE ==========

def show_duas_guide():
    """Display Essential Duas guide"""
    st.markdown("## 🤲 Essential Duas for Daily Life")
    
    st.info("""
    **Duas (Supplications)** are a way to communicate with Allah throughout the day.
    Learn these essential duas to remember Allah in every situation.
    """)
    
    # Category filter
    categories = list(set(dua['category'] for dua in ESSENTIAL_DUAS))
    
    category_tabs = st.tabs(["📋 All Duas"] + categories)
    
    with category_tabs[0]:
        st.markdown("### All Essential Duas")
        display_duas(ESSENTIAL_DUAS, "all")
    
    for idx, category in enumerate(categories, 1):
        with category_tabs[idx]:
            st.markdown(f"### {category}")
            category_duas = [d for d in ESSENTIAL_DUAS if d['category'] == category]
            display_duas(category_duas, category.replace(' ', '_'))

def display_duas(duas_list, tab_name):
    """Helper function to display duas"""
    completed = get_user_progress(st.session_state.user_id, guide_type='duas')
    
    for dua in duas_list:
        is_learned = dua['id'] in completed
        
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            learned = st.checkbox("", value=is_learned, 
                                 key=f"dua_{tab_name}_{dua['id']}", 
                                 label_visibility="collapsed")
            if learned != is_learned:
                save_step_progress(st.session_state.user_id, dua['id'], learned, guide_type='duas')
                st.rerun()
        
        with col2:
            icon = "✅" if is_learned else "📿"
            with st.expander(f"{icon} **{dua['title']}**"):
                st.markdown(f"""
                <div class="dua-box">
                    <p class="arabic-text">{dua['arabic']}</p>
                    <p style="font-style: italic; color: #047857; margin: 0.5rem 0;">
                        <strong>Transliteration:</strong><br>
                        {dua['transliteration']}
                    </p>
                    <p style="color: #065f46; margin: 0.5rem 0;">
                        <strong>Translation:</strong><br>
                        {dua['translation']}
                    </p>
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 1rem; 
                                border-radius: 10px; margin-top: 1rem;">
                        <strong>📌 When to say:</strong> {dua['occasion']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if not is_learned:
                    st.info("✓ Check the box when you've memorized this dua!")
    
    learned_count = len([d for d in duas_list if d['id'] in completed])
    st.caption(f"Memorized: {learned_count}/{len(duas_list)} duas")    

def get_user_progress(user_id, guide_type='umrah'):
    """Get user's completed steps for a specific guide"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    # Update table to include guide_type
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                     (user_id TEXT, 
                      step_id INTEGER, 
                      guide_type TEXT DEFAULT 'umrah',
                      completed BOOLEAN,
                      PRIMARY KEY(user_id, step_id, guide_type))''')
    except:
        pass
    
    c.execute('SELECT step_id FROM user_progress WHERE user_id=? AND guide_type=? AND completed=1', 
              (user_id, guide_type))
    completed = [row[0] for row in c.fetchall()]
    conn.close()
    return completed

def save_step_progress(user_id, step_id, completed, guide_type='umrah'):
    """Save step completion status for a specific guide"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    if completed:
        c.execute('''INSERT OR REPLACE INTO user_progress (user_id, step_id, guide_type, completed) 
                     VALUES (?,?,?,1)''', (user_id, step_id, guide_type))
    else:
        c.execute('DELETE FROM user_progress WHERE user_id=? AND step_id=? AND guide_type=?', 
                  (user_id, step_id, guide_type))
    
    conn.commit()
    conn.close()

# ========== LOGIN SCREEN ==========

if not st.session_state.logged_in:

    st.markdown("""
    <div class="main-header">
        <h1>🕋 Umrah Pro - Complete Guide</h1>
        <p>Your All-in-One Umrah Companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.markdown("### Login to Your Account")
        user = st.text_input("Username", key="login_user")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Login", type="primary", use_container_width=True):
            uid, subscription, country = auth_user(user, pwd)
            if uid:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.username = user
                st.session_state.subscription = subscription
                st.session_state.user_country = country
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    with tab2:
        st.markdown("### Create New Account")
        
        new_user = st.text_input("Username", key="new_user")
        new_pwd = st.text_input("Password", type="password", key="new_pwd")
        confirm_pwd = st.text_input("Confirm Password", type="password", key="confirm_pwd")
        new_email = st.text_input("Email", key="new_email")
        
        # Country selection
        st.markdown("#### 🌍 Select Your Country")
        st.caption("This helps us show packages and prices relevant to you")
        
        new_country = st.selectbox(
            "Country",
            list(CURRENCY_DATA.keys()),
            key="new_country"
        )
        
        # Show currency info
        currency_info = CURRENCY_DATA[new_country]
        st.info(f"💱 Your currency: **{currency_info['currency']}** ({currency_info['symbol']})")
        
        new_phone = st.text_input("Phone (optional)", key="new_phone")
        
        if st.button("Create Account", type="primary", use_container_width=True):
            if len(new_pwd) < 6:
                st.error("❌ Password must be 6+ characters")
            elif new_pwd != confirm_pwd:
                st.error("❌ Passwords don't match")
            elif not new_email:
                st.error("❌ Email required")
            else:
                success, uid = create_user(new_user, new_pwd, new_email, new_country, new_phone)
                if success:
                    st.success("✅ Account created! Please login.")
                else:
                    st.error("❌ Username already exists")

else:
    # ========== BEAUTIFUL COMPACT HEADER ==========
    
    is_premium = st.session_state.subscription == 'premium'
    user_country = st.session_state.user_country
    currency_info = CURRENCY_DATA.get(user_country, CURRENCY_DATA["🇺🇸 United States"])
    
    # Extract flag and country name
    country_parts = user_country.split()
    country_flag = country_parts[0] if country_parts else "🌍"
    country_name = ' '.join(country_parts[1:]) if len(country_parts) > 1 else user_country
    
    st.markdown(f"""
    <div class="main-header">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div style="text-align: left;">
                <h1 style="font-size: 2rem; margin: 0;">🕋 Assalamu Alaikum!</h1>
                <p style="font-size: 1.3rem; margin: 0.3rem 0 0 0; opacity: 0.9;">Welcome back, <strong>{st.session_state.username}</strong></p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 3rem; margin-bottom: 0.3rem;">{country_flag}</div>
                <div style="font-size: 0.9rem; opacity: 0.9;">{country_name}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ========== SIDEBAR WITH TABS ==========
    
    with st.sidebar:

        st.markdown(f"### 👤 {st.session_state.username}")
        st.caption(f"📍 {user_country}")
        st.caption(f"💱 Currency: {currency_info['currency']} ({currency_info['symbol']})")
        
        if is_premium:
            st.success("⭐ Premium Member")
        else:
            st.info("🆓 Free Plan")
            if st.button("⬆️ Upgrade to Premium", use_container_width=True):
                upgrade_subscription(st.session_state.user_id, 'premium')
                st.session_state.subscription = 'premium'
                st.success("✅ Upgraded!")
                st.balloons()
                st.rerun()
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown("---")
        
        # NAVIGATION TABS IN SIDEBAR
        st.markdown("### 📑 Navigation")
        
        pages = [
            "🏠 Home",
            "📦 Packages",
            "👨‍👩‍👧‍👦 Family GPS",
            "📗 Quran",
            "🕌 Prayer Times",
            "💼 My Bookings",
            "✅ Checklist",
            "ℹ️ Info"
        ]
        
        for page_option in pages:
            if st.button(page_option, use_container_width=True, 
                        type="primary" if st.session_state.page == page_option else "secondary"):
                st.session_state.page = page_option
                st.rerun()
        
       
        
        # Guide dropdown menu
        st.markdown("---")
        st.markdown("### 📖 Islamic Guides")
        
        guide_option = st.selectbox(
            "Select Guide",
            [
                "📖 Umrah Guide", 
                "🕋 Hajj Guide", 
                "🗺️ Ziyarath Guide",
                "🕌 Salah Guide",
                "🤲 Essential Duas"
            ],
            label_visibility="collapsed"
        )
        
        # Set page based on guide selection
        if st.button("Open Guide", type="primary", use_container_width=True):
            st.session_state.page = guide_option
            st.rerun()

        # Progress widget
        completed = get_user_progress(st.session_state.user_id)
        progress = (len(completed) / 7) * 100
        st.markdown("### 📊 Umrah Progress")
        st.progress(progress / 100)
        st.caption(f"{len(completed)}/7 steps • {progress:.0f}%")
        
        st.markdown("---")
        
        # Mini prayer times widget in sidebar
        st.markdown("---")
        st.markdown("### 🕌 Prayer Times")
        
        settings = get_prayer_notification_settings(st.session_state.user_id)
        prayer_times = get_prayer_times_by_coordinates(
            settings['latitude'],
            settings['longitude'],
            settings['timezone']
        )
        
        if prayer_times:
            next_prayer = get_next_prayer(prayer_times)
            
            if next_prayer:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #059669, #10b981);
                            padding: 1rem; border-radius: 10px; color: white; text-align: center;">
                    <div style="font-size: 0.8rem; opacity: 0.9;">⏰ Next Prayer</div>
                    <div style="font-size: 1.2rem; font-weight: bold; margin: 0.3rem 0;">
                        {next_prayer['name']}
                    </div>
                    <div style="font-size: 1.5rem; font-weight: bold;">
                        {next_prayer['time']}
                    </div>
                    <div style="font-size: 0.8rem; opacity: 0.9; margin-top: 0.3rem;">
                        {next_prayer['hours_remaining']}h {next_prayer['minutes_remaining']}m
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("View All Times"):
                for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                    st.markdown(f"**{prayer}:** {prayer_times.get(prayer, '--:--')}")
    # ========== MAIN CONTENT AREA ==========
    
   # ========== HOME PAGE WITH BEAUTIFUL DESIGN ==========
    
    if st.session_state.page == "🏠 Home":
        
        # Quick stats with beautiful cards
        st.markdown("### 📊 Your Progress Dashboard")
        
        col1, col2, col3 = st.columns(3)
        
        
        with col1:
            packages = get_all_packages(user_country)
            
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">📦</div>
                <h3 style="font-size: 2rem; margin: 0;">{len(packages)}</h3>
                <p>Packages Available</p>
                <div style="margin-top: 1rem; font-size: 0.8rem; color: #059669;">For {user_country.split()[1] if len(user_country.split()) > 1 else user_country}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Get duas learned count
            duas_learned = get_user_progress(st.session_state.user_id, guide_type='duas')
            total_duas = len(ESSENTIAL_DUAS)
            duas_pct = (len(duas_learned) / total_duas * 100) if total_duas > 0 else 0
            
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">🤲</div>
                <h3 style="font-size: 2rem; margin: 0;">{len(duas_learned)}/{total_duas}</h3>
                <p>Duas Learned</p>
                <div style="width: 100%; height: 8px; background: #e5e7eb; border-radius: 10px; margin-top: 1rem;">
                    <div style="width: {duas_pct}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #2563eb); border-radius: 10px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            checklist = get_umrah_checklist()
            user_progress_check = get_checklist_progress(st.session_state.user_id)
            total = sum(len(c['items']) for c in checklist.values())
            checked = sum(len(items) for items in user_progress_check.values())
            checklist_pct = (checked / total * 100) if total > 0 else 0
            
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">✅</div>
                <h3 style="font-size: 2rem; margin: 0;">{checked}/{total}</h3>
                <p>Items Packed</p>
                <div style="width: 100%; height: 8px; background: #e5e7eb; border-radius: 10px; margin-top: 1rem;">
                    <div style="width: {checklist_pct}%; height: 100%; background: linear-gradient(90deg, #3b82f6, #2563eb); border-radius: 10px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quick actions with beautiful buttons
        st.markdown("### ⚡ Quick Actions")
        
        col_action1, col_action2 = st.columns(2)

        with col_action1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #3b82f6, #2563eb);
                        padding: 2rem; border-radius: 20px; text-align: center;
                        color: white; cursor: pointer; transition: all 0.3s ease;
                        box-shadow: 0 5px 20px rgba(59, 130, 246, 0.3);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📗</div>
                <h3 style="margin: 0;">Read Quran</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Connect with Allah</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Open Quran", key="btn_quran", use_container_width=True):
                st.session_state.page = "📗 Quran"
                st.rerun()
        
        with col_action2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f59e0b, #d97706);
                        padding: 2rem; border-radius: 20px; text-align: center;
                        color: white; cursor: pointer; transition: all 0.3s ease;
                        box-shadow: 0 5px 20px rgba(245, 158, 11, 0.3);">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📦</div>
                <h3 style="margin: 0;">Browse Packages</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Find perfect deals</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("View Packages", key="btn_packages", use_container_width=True):
                st.session_state.page = "📦 Packages"
                st.rerun()
        
        st.markdown("---")
        
        # Daily verse with stunning design
        st.markdown("### 🎲 Daily Inspiration")
        
        if st.button("✨ Get Daily Verse", type="primary", use_container_width=True):
            verse = get_random_verse()
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); 
                        padding: 3rem; border-radius: 25px; margin: 2rem 0;
                        border: 4px solid #f59e0b; 
                        box-shadow: 0 10px 40px rgba(245, 158, 11, 0.2);
                        position: relative; overflow: hidden;">
                
                <div style="position: absolute; top: 20px; right: 20px; font-size: 5rem; opacity: 0.1;">☪️</div>
                
                <p class="arabic-text" style="font-size: 2.8rem; line-height: 4rem;">
                    {verse['arabic']}
                </p>
                
                <div style="background: rgba(255,255,255,0.8); padding: 2rem; 
                            border-radius: 15px; margin: 2rem 0;">
                    <p style="font-size: 1.3rem; color: #78350f; line-height: 2.2rem; margin: 0;">
                        {verse['english']}
                    </p>
                </div>
                
                <p style="text-align: right; color: #f59e0b; font-weight: 700; 
                        font-size: 1.3rem; margin: 0;">
                    — {verse['ref']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tips section with cards
        st.markdown("---")
        st.markdown("### 💡 Helpful Tips")
        
        tips_col1, tips_col2 = st.columns(2)
        
        with tips_col1:
            st.markdown("""
            <div class="feature-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🕌</div>
                <h3 style="color: #059669; margin-bottom: 1rem;">Before You Go</h3>
                <ul style="color: #6b7280; line-height: 2rem;">
                    <li>Complete your visa application early</li>
                    <li>Get required vaccinations</li>
                    <li>Book accommodation near Haram</li>
                    <li>Learn basic Arabic phrases</li>
                    <li>Pack light, comfortable clothing</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with tips_col2:
            st.markdown("""
            <div class="feature-card">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🤲</div>
                <h3 style="color: #059669; margin-bottom: 1rem;">Spiritual Preparation</h3>
                <ul style="color: #6b7280; line-height: 2rem;">
                    <li>Make sincere intention (Niyyah)</li>
                    <li>Seek forgiveness from others</li>
                    <li>Learn Umrah duas and steps</li>
                    <li>Increase worship and dhikr</li>
                    <li>Prepare list of duas to make</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

     # ========== PACKAGES PAGE WITH CURRENCY CONVERSION ==========
    
    elif st.session_state.page == "📦 Packages":
        st.markdown("## 📦 Umrah Packages")
        
        # Currency info banner
        st.success(f"💱 Prices shown in your local currency: **{currency_info['currency']}** ({currency_info['symbol']})")
        
        packages = get_all_packages(user_country)
        
        if not packages:
            st.info(f"📦 No packages available for {user_country} yet. Check back soon!")
            st.caption("Packages are shown based on your country selection during registration")
        else:
            st.caption(f"Found {len(packages)} packages for {user_country}")
            
            # Filter options
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                categories = sorted(list(set(p['category'] for p in packages)))
                selected_category = st.selectbox("Category", ["All"] + categories)
            
            with filter_col2:
                # Price filter in local currency
                if packages:
                    max_usd = max(p['price'] for p in packages)
                    max_local, symbol = convert_price(max_usd, user_country)
                    
                    if isinstance(max_local, int):
                        price_range = st.slider(
                            f"Max Price ({currency_info['currency']})", 
                            0, int(max_local), int(max_local)
                        )
                    else:
                        price_range = st.slider(
                            f"Max Price ({currency_info['currency']})", 
                            0.0, float(max_local), float(max_local)
                        )
            
            # Apply filters
            filtered_packages = packages
            
            if selected_category != "All":
                filtered_packages = [p for p in filtered_packages if p['category'] == selected_category]
            
            # Filter by price (convert to check)
            filtered_by_price = []
            for p in filtered_packages:
                local_price, _ = convert_price(p['price'], user_country)
                if local_price <= price_range:
                    filtered_by_price.append(p)
            
            filtered_packages = filtered_by_price
            
            st.markdown(f"### Showing {len(filtered_packages)} packages")
            st.markdown("---")
            
            for pkg in filtered_packages:
                # Convert price to user's currency
                local_price, symbol = convert_price(pkg['price'], user_country)
                formatted_price = format_price(local_price, symbol)
                
                with st.expander(f"✈️ {pkg['name']} - {formatted_price}"):
                    increment_package_view(pkg['id'])
                    
                    # Price comparison banner
                    st.info(f"💱 **Original:** ${pkg['price']:,.2f} USD  |  **Your Price:** {formatted_price}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Duration:** {pkg['duration']}")
                        st.write(f"**Category:** {pkg['category']}")
                        st.write(f"**Departure:** {pkg['departure_city']}")
                    
                    with col2:
                        st.write(f"**Makkah:** {pkg['makkah_hotel']} ({pkg['makkah_rating']}⭐)")
                        st.write(f"**Madinah:** {pkg['madinah_hotel']} ({pkg['madinah_rating']}⭐)")
                        st.write(f"**Group:** {pkg['group_size']}")
                    
                    st.markdown("**Inclusions:**")
                    for inc in pkg['inclusions'].split('\n')[:5]:
                        if inc.strip():
                            st.write(f"• {inc}")
                    
                    st.markdown(f"**📞 Operator:** {pkg['company']}")
                    
                    st.markdown("---")
                    
                    with st.form(f"inquiry_{pkg['id']}"):
                        st.markdown("### 📧 Send Inquiry")
                        
                        col_form1, col_form2 = st.columns(2)
                        
                        with col_form1:
                            name = st.text_input("Name *", key=f"n_{pkg['id']}")
                            email = st.text_input("Email *", key=f"e_{pkg['id']}")
                        
                        with col_form2:
                            phone = st.text_input("Phone *", key=f"p_{pkg['id']}")
                            travelers = st.number_input("Travelers *", 1, 50, 2, key=f"t_{pkg['id']}")
                        
                        submit = st.form_submit_button("📧 Send Inquiry", type="primary", use_container_width=True)
                        
                        if submit:
                            if name and email and phone:
                                agent = get_agent_by_package(pkg['id'])
                                
                                if agent:
                                    customer_data = {
                                        'name': name,
                                        'email': email,
                                        'phone': phone,
                                        'travelers': travelers,
                                        'preferred_date': 'Flexible',
                                        'message': f"Interested in {pkg['name']}. Viewed price: {formatted_price}"
                                    }
                                    
                                    submit_package_inquiry(pkg['id'], agent['agent_id'], customer_data)
                                    
                                    st.success(f"✅ Inquiry sent to {pkg['company']}!")
                                    st.info(f"They will contact you at {email}")
                                    st.balloons()
                            else:
                                st.error("❌ Fill all required fields")
    
    # ========== UMRAH GUIDE PAGE ==========
    
    elif st.session_state.page == "📖 Umrah Guide":
        st.markdown("## 📖 Complete Umrah Guide with Duas")
        
        for step in UMRAH_STEPS:
            completed_steps = get_user_progress(st.session_state.user_id, guide_type='umrah')
            is_done = step['id'] in completed_steps
            
            col1, col2 = st.columns([0.05, 0.95])
            
            with col1:
                checked = st.checkbox("", value=is_done, key=f"s{step['id']}", 
                                     label_visibility="collapsed")
                if checked != is_done:
                    save_step_progress(st.session_state.user_id, step['id'], checked)
                    st.rerun()
            
            with col2:
                icon = "✅" if is_done else "⭕"
                with st.expander(f"{icon} **{step['title']}**", expanded=not is_done):
                    st.markdown(f"""
                    <div class="dua-box">
                        <p class="arabic-text">{step['dua_arabic']}</p>
                        <p style="font-style: italic; color: #047857;">
                            {step['dua_transliteration']}
                        </p>
                        <p style="color: #065f46;">
                            {step['dua_english']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**📝 Instructions:**")
                    for s in step['details']:
                        st.markdown(f"• {s}")
        
        if len(completed_steps) == 7:
            st.balloons()
            st.success("🎉 **Congratulations! Umrah Completed!**")
    
    # ========== HAJJ GUIDE PAGE ==========

    elif st.session_state.page == "🕋 Hajj Guide":
        show_hajj_guide()

    # ========== ZIYARATH GUIDE PAGE ==========

    elif st.session_state.page == "🗺️ Ziyarath Guide":
        show_ziyarath_guide()

    # ========== SALAH GUIDE PAGE ==========

    elif st.session_state.page == "🕌 Salah Guide":
        show_salah_guide()

    # ========== ESSENTIAL DUAS PAGE ==========

    elif st.session_state.page == "🤲 Essential Duas":
        show_duas_guide()
    
    # ========== FAMILY GPS PAGE ==========
    
    elif st.session_state.page == "👨‍👩‍👧‍👦 Family GPS":
        st.markdown("## 👨‍👩‍👧‍👦 Family GPS Tracker")
        
        if not is_premium:
            st.info("🆓 Free: Track up to 3 members. Premium: Unlimited!")
        
        with st.expander("➕ Add Family Member"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name")
                relationship = st.selectbox("Relationship", 
                    ["Father", "Mother", "Brother", "Sister", "Spouse", "Son", "Daughter"])
            with col2:
                phone = st.text_input("Phone")
            
            if st.button("Add Member", type="primary"):
                members = get_family_members(st.session_state.user_id)
                if not is_premium and len(members) >= 3:
                    st.error("❌ Free plan limited to 3 members")
                elif name and phone:
                    add_family_member(st.session_state.user_id, name, relationship, phone)
                    st.success(f"✅ {name} added!")
                    st.rerun()
        
        st.markdown("---")
        
        members = get_family_members(st.session_state.user_id)
        
        if members:
            for m in members:
                with st.container():
                    col1, col2, col3 = st.columns([0.3, 0.5, 0.2])
                    
                    with col1:
                        st.markdown(f"### {m['name']}")
                        st.caption(f"{m['relationship']}")
                    
                    with col2:
                        if m['lat'] and m['lng']:
                            st.write(f"📍 {m['location']}")
                        else:
                            st.info("📍 No location yet")
                    
                    with col3:
                        battery = m['battery'] or 100
                        st.metric("🔋", f"{battery}%")
                    
                    if st.button(f"🗑️ Remove", key=f"del_{m['id']}"):
                        delete_family_member(m['id'])
                        st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("👥 No family members yet. Add your first member!")
    
    # ========== QURAN PAGE ==========
    
    # ========== PAGE 5: QURAN & PRAYER (ENHANCED) ==========
    elif st.session_state.page == "📗 Quran":
        st.markdown("## 📗 Quran Reading, Audio & Daily Verse")
        
        qtab1, qtab2, qtab3 = st.tabs([
            "📖 Read Quran",
            "🎵 Listen Quran",
            "🎲 Daily Verse"
        ])
        
        # ========== TAB 1: READ QURAN WITH TRANSLATIONS ==========
        with qtab1:
            st.markdown("### 📖 Read Quran with Translations")
            
            # Language selector
            col1, col2 = st.columns([0.6, 0.4])
            
            with col1:
                translations = get_available_translations()
                selected_translation = st.selectbox(
                    "🌍 Select Translation Language",
                    list(translations.keys()),
                    format_func=lambda x: translations[x],
                    help="Choose your preferred language for Quran translation"
                )
            
            with col2:
                st.info(f"📚 **Selected:** {translations[selected_translation]}")
            
            # Surah selector
            surahs = get_surah_list()
            
            if surahs:
                surah_options = {f"{num}. {eng} ({ar}) - {ayahs} verses": num 
                                for num, eng, ar, ayahs in surahs}
                
                selected_surah = st.selectbox(
                    "📜 Select Surah",
                    list(surah_options.keys()),
                    help="Choose which Surah to read"
                )
                
                load_button = st.button("📖 Load Surah", type="primary", use_container_width=True)
                
                if load_button and selected_surah:
                    surah_num = surah_options[selected_surah]
                    
                    with st.spinner(f"Loading {selected_surah.split('.')[1].split('(')[0].strip()}..."):
                        surah_data = get_surah_with_translation(surah_num, selected_translation)
                        
                        if surah_data:
                            # Header
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #059669, #10b981); 
                                        padding: 2rem; border-radius: 15px; text-align: center; 
                                        color: white; margin: 2rem 0;">
                                <h1>{surah_data['name']}</h1>
                                <h2 style="font-size: 2.5rem;">{surah_data['arabic_name']}</h2>
                                <p style="font-size: 1.2rem; opacity: 0.9;">
                                    {surah_data['revelation'].title()} • {len(surah_data['verses'])} Verses
                                </p>
                            </div>
                            """, unsafe_allow_html=True)  # ← FIXED: Added this parameter
                            
                            # Bismillah (except Surah 9)
                            if surah_num != 9:
                                st.markdown(f"""
                                <div style="text-align: center; padding: 2rem; 
                                            background: #f0fdf4; border-radius: 10px; margin: 1rem 0;">
                                    <p style="font-size: 2rem; color: #065f46; font-weight: bold; 
                                    font-family: 'Traditional Arabic', 'Arial Unicode MS', Arial;">
                                        بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
                                    </p>
                                    <p style="color: #047857; font-style: italic;">
                                        In the name of Allah, the Most Gracious, the Most Merciful
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)  # ← FIXED: Added this parameter
                            
                            st.markdown("---")
                            
                            # Verses
                            # Free users: First 10 verses
                            # Premium users: All verses
                            verses_to_show = surah_data['verses'] if is_premium else surah_data['verses'][:10]
                            
                            for verse in verses_to_show:
                                # Use expander for cleaner view
                                with st.container():
                                    # Verse number badge
                                    col_badge, col_content = st.columns([0.1, 0.9])
                                    
                                    with col_badge:
                                        st.markdown(f"""
                                        <div style="background: #059669; color: white; 
                                                    width: 50px; height: 50px; border-radius: 50%;
                                                    display: flex; align-items: center; justify-content: center;
                                                    font-weight: bold; font-size: 1.3rem;">
                                            {verse['number']}
                                        </div>
                                        """, unsafe_allow_html=True)  # ← FIXED
                                        

                                    
                                    with col_content:
                                        audio_url = get_verse_audio_url(surah_num, verse['number'])
                                        st.audio(audio_url, format='audio/mp3')
                                        # Arabic text
                                        st.markdown(f"""
                                        <p class="arabic-text" style="text-align: right; 
                                        font-size: 2rem; margin: 1rem 0;">
                                            {verse['arabic']}
                                        </p>
                                        """, unsafe_allow_html=True)  # ← FIXED
                                        
                                        # Translation
                                        st.markdown(f"""
                                        <div style="background: #eff6ff; padding: 1rem; 
                                                    border-radius: 8px; border-left: 4px solid #3b82f6;">
                                            <p style="color: #1e40af; margin: 0; line-height: 1.7rem;">
                                                {verse['translation']}
                                            </p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown("<br>", unsafe_allow_html=True)  # ← FIXED
                            
                            # Premium upsell
                            if not is_premium and len(surah_data['verses']) > 10:
                                remaining = len(surah_data['verses']) - 10
                                st.warning(f"🆓 Free plan shows first 10 verses. **{remaining} more verses available** with Premium!")
                                
                                if st.button("⬆️ Upgrade to Read Full Surah", type="primary"):
                                    upgrade_subscription(st.session_state.user_id, 'premium')
                                    st.session_state.subscription = 'premium'
                                    st.success("✅ Upgraded! Reload the page.")
                                    st.balloons()
                                    st.rerun()
                        else:
                            st.error("Could not load Surah. Please try again.")
            else:
                st.error("Could not load Surah list. Check internet connection.")

        # ========== TAB 2: LISTEN QURAN ==========
        with qtab2:
            st.markdown("### 🎵 Listen to Quran Recitation")
            
            # Reciter selector
            col1, col2 = st.columns([0.6, 0.4])
            
            with col1:
                reciters = get_available_reciters()
                selected_reciter = st.selectbox(
                    "🎙️ Select Reciter (Qari)",
                    list(reciters.keys()),
                    format_func=lambda x: f"{reciters[x]['name']} {reciters[x]['country']}",
                    help="Choose your favorite Quran reciter"
                )
            
            with col2:
                reciter_info = reciters[selected_reciter]
                st.info(f"**Style:** {reciter_info['style']}")
                st.caption(f"From: {reciter_info['country']}")
            
            # Surah selector for audio
            surahs_audio = get_surah_list()
            
            if surahs_audio:
                surah_audio_options = {f"{num}. {eng} ({ar})": num 
                                    for num, eng, ar, ayahs in surahs_audio}
                
                selected_surah_audio = st.selectbox(
                    "📜 Select Surah to Listen",
                    list(surah_audio_options.keys()),
                    key="audio_surah_select"
                )
                
                col_play, col_download = st.columns(2)
                
                with col_play:
                    play_button = st.button("▶️ Play Surah", type="primary", use_container_width=True)
                
                with col_download:
                    show_download = st.button("📥 Get Download Link", use_container_width=True)
                
                if play_button or show_download:
                    surah_num = surah_audio_options[selected_surah_audio]
                    audio_url = get_full_surah_audio_url(surah_num, selected_reciter)
                    
                    # Display player header
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #3b82f6, #2563eb); 
                                padding: 2rem; border-radius: 15px; text-align: center; 
                                color: white; margin: 1rem 0;">
                        <h3>🎵 Now Playing</h3>
                        <h2>{selected_surah_audio.split('.')[1].strip()}</h2>
                        <p>Recited by: {reciters[selected_reciter]['name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Check if URL is accessible
                    with st.spinner("Loading audio..."):
                        url_works = check_audio_url(audio_url)
                    
                    if url_works:
                        # Audio player
                        st.audio(audio_url, format='audio/mp3', start_time=0)
                        
                        st.success("🎧 Tip: Use headphones for best experience!")
                        
                        # Download button
                        st.markdown(f"""
                        <div style="margin-top: 1rem;">
                            <a href="{audio_url}" download style="text-decoration: none;">
                                <button style="background: #059669; color: white; border: none; 
                                            padding: 1rem 2rem; border-radius: 8px; cursor: pointer; 
                                            font-weight: bold; width: 100%; font-size: 1rem;">
                                    📥 Download MP3
                                </button>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show direct link as backup
                        if show_download:
                            st.code(audio_url, language=None)
                            st.caption("Copy this link to download in your browser")
                    else:
                        st.error("⚠️ Audio not available from this source. Trying alternative...")
                        
                        # Try alternative URLs
                        alternative_urls = [
                            f"https://download.quran.islamway.net/quran3/{selected_reciter.replace('ar.', '')}/{str(surah_num).zfill(3)}.mp3",
                            f"https://verses.quran.com/{selected_reciter}/{str(surah_num).zfill(3)}.mp3"
                        ]
                        
                        found_working = False
                        for alt_url in alternative_urls:
                            if check_audio_url(alt_url):
                                st.audio(alt_url, format='audio/mp3')
                                st.success("✅ Alternative source loaded!")
                                found_working = True
                                break
                        
                        if not found_working:
                            st.warning("""
                            🔧 **Audio temporarily unavailable**
                            
                            **Alternative options:**
                            1. Try a different reciter
                            2. Visit: https://quran.com (has all audio)
                            3. Download Quran apps: Muslim Pro, Al-Quran, etc.
                            """)
            
            st.markdown("---")
            
            # Top Reciters Info
            with st.expander("ℹ️ About the Reciters"):
                st.markdown("""
                ### 🎙️ Famous Quran Reciters
                
                **Mishary Rashid Alafasy** 🇰🇼
                - One of the most popular reciters worldwide
                - Known for his beautiful, clear voice
                - Imam of Grand Mosque in Kuwait
                
                **Abdul Basit Abdul Samad** 🇪🇬
                - Legendary Egyptian reciter (1927-1988)
                - Two styles: Murattal (slow) and Mujawwad (melodious)
                - Considered one of the greatest ever
                
                **Mahmoud Khalil Al-Husary** 🇪🇬
                - Known as the "Teacher of Reciters"
                - Perfect for learning Tajweed
                - Crystal clear pronunciation
                
                **Mohamed Siddiq Al-Minshawi** 🇪🇬
                - Master of Mujawwad style (1920-1969)
                - Very emotional and powerful
                - Beloved across the Muslim world
                
                **Abdurrahman As-Sudais** 🇸🇦
                - Imam of Masjid al-Haram (Makkah)
                - Emotional and powerful recitation
                - Heard by millions during Hajj
                
                **Saad Al-Ghamdi** 🇸🇦
                - Popular Saudi reciter
                - Strong, resonant voice
                - Great for motivation
                """)

        # ========== TAB 3: DAILY VERSE ==========
        with qtab3:
            st.markdown("### 🎲 Verse of the Day")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Translation selector for daily verse
                translations_daily = get_available_translations()
                selected_trans_daily = st.selectbox(
                    "Select Language",
                    list(translations_daily.keys()),
                    format_func=lambda x: translations_daily[x],
                    key="daily_verse_lang"
                )
            
            with col2:
                if st.button("🎲 Get Random Verse", type="primary", use_container_width=True):
                    st.session_state['refresh_verse'] = True
            
            # Get and display verse
            if st.session_state.get('refresh_verse', False):
                try:
                    s = random.randint(1, 114)
                    a = random.randint(1, 10)
                    url = f"http://api.alquran.cloud/v1/ayah/{s}:{a}/editions/quran-uthmani,{selected_trans_daily}"
                    r = requests.get(url, timeout=10)
                    
                    if r.status_code == 200:
                        data = r.json()['data']
                        verse = {
                            'arabic': data[0]['text'],
                            'translation': data[1]['text'],
                            'ref': f"{data[0]['surah']['englishName']} ({s}:{a})",
                            'surah': data[0]['surah']['name']
                        }
                    else:
                        verse = get_random_verse()  # Fallback
                except:
                    verse = get_random_verse()
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); 
                            padding: 3rem; border-radius: 20px; margin: 2rem 0;
                            border: 4px solid #f59e0b; box-shadow: 0 8px 16px rgba(0,0,0,0.15);">
                    
                    <!-- Surah Name -->
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <p style="font-size: 1.5rem; color: #92400e; font-weight: bold; margin: 0;
                                font-family: 'Traditional Arabic', 'Arial Unicode MS', Arial;">
                            {verse.get('surah', '')}
                        </p>
                    </div>
                    
                    <!-- Arabic Verse -->
                    <p style="font-size: 2.5rem; text-align: right; font-weight: bold;
                            color: #92400e; line-height: 3.5rem; margin-bottom: 2rem;
                            font-family: 'Traditional Arabic', 'Arial Unicode MS', Arial;">
                        {verse['arabic']}
                    </p>
                    
                    <!-- Translation -->
                    <div style="background: rgba(255,255,255,0.7); padding: 1.5rem; 
                                border-radius: 10px; margin-bottom: 1.5rem;">
                        <p style="font-size: 1.2rem; color: #78350f; line-height: 2rem; 
                                margin: 0;">
                            {verse.get('translation', verse.get('english', ''))}
                        </p>
                    </div>
                    
                    <!-- Reference -->
                    <p style="text-align: right; color: #f59e0b; font-weight: bold; 
                            font-size: 1.2rem; margin: 0;">
                        — {verse['ref']}
                    </p>
                </div>
                """, unsafe_allow_html=True)  # ← FIXED: Added this parameter
                
                # Share buttons
                col_share1, col_share2, col_share3 = st.columns(3)
                
                with col_share1:
                    if st.button("📋 Copy Verse"):
                        st.success("Copied!")
                with col_share2:
                    if st.button("📱 Share"):
                        st.info("Share feature coming soon!")
                with col_share3:
                    if st.button("❤️ Save Favorite"):
                        st.success("Saved to favorites!")
    
    # ==========  PRAYER TIMES PAGE ==========
    
    elif st.session_state.page == "🕌 Prayer Times":
        st.markdown("## 🕌 Prayer Times - Global")
        
        # Tabs for different features
        prayer_tabs = st.tabs([
            "⏰ Prayer Times",
            "📍 Location Settings",
            "🔔 Notifications",
            "🧭 Qibla Direction"
        ])
        
        # ========== TAB 1: PRAYER TIMES ==========
        
        with prayer_tabs[0]:
            st.markdown("### 🕌 Today's Prayer Times")
            
            # Get user's saved location or detect
            settings = get_prayer_notification_settings(st.session_state.user_id)
            
            # Auto-detect location button
            col_detect, col_manual = st.columns(2)
            
            with col_detect:
                if st.button("📍 Auto-Detect My Location", use_container_width=True):
                    with st.spinner("Detecting your location..."):
                        location = get_user_location_from_ip()
                        settings['latitude'] = location['lat']
                        settings['longitude'] = location['lon']
                        settings['timezone'] = location['timezone']
                        save_prayer_notification_settings(st.session_state.user_id, settings)
                        st.success(f"✅ Location set to: {location['city']}, {location['country']}")
                        st.rerun()
            
            with col_manual:
                st.info(f"📍 Current: Lat {settings['latitude']:.4f}, Lon {settings['longitude']:.4f}")
            
            # Get prayer times
            prayer_times = get_prayer_times_by_coordinates(
                settings['latitude'],
                settings['longitude'],
                settings['timezone']
            )
            
            if prayer_times:
                # Date display
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #3b82f6, #2563eb);
                            padding: 1.5rem; border-radius: 15px; text-align: center;
                            color: white; margin-bottom: 2rem;">
                    <h3 style="margin: 0;">📅 {prayer_times['date']}</h3>
                    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                        🌙 {prayer_times['hijri']} (Hijri)
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Next prayer countdown
                next_prayer = get_next_prayer(prayer_times)
                
                if next_prayer:
                    if next_prayer.get('tomorrow'):
                        countdown_text = "Tomorrow's Fajr"
                    else:
                        countdown_text = f"{next_prayer['hours_remaining']}h {next_prayer['minutes_remaining']}m"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #059669, #10b981);
                                padding: 2rem; border-radius: 20px; text-align: center;
                                color: white; margin-bottom: 2rem;
                                box-shadow: 0 8px 20px rgba(5, 150, 105, 0.3);">
                        <h4 style="margin: 0; opacity: 0.9;">⏰ Next Prayer</h4>
                        <h2 style="margin: 0.5rem 0; font-size: 2.5rem;">{next_prayer['name']}</h2>
                        <h3 style="margin: 0; font-size: 2rem;">{next_prayer['time']}</h3>
                        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
                            {countdown_text}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Prayer times grid
                st.markdown("### 📋 All Prayer Times")
                
                prayer_cols = st.columns(3)
                prayer_list = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha', 'Sunrise']
                
                prayer_icons = {
                    'Fajr': '🌅',
                    'Sunrise': '☀️',
                    'Dhuhr': '🌞',
                    'Asr': '🌤️',
                    'Maghrib': '🌇',
                    'Isha': '🌙'
                }
                
                prayer_colors = {
                    'Fajr': 'linear-gradient(135deg, #6366f1, #4f46e5)',
                    'Sunrise': 'linear-gradient(135deg, #f59e0b, #d97706)',
                    'Dhuhr': 'linear-gradient(135deg, #eab308, #ca8a04)',
                    'Asr': 'linear-gradient(135deg, #f97316, #ea580c)',
                    'Maghrib': 'linear-gradient(135deg, #ec4899, #db2777)',
                    'Isha': 'linear-gradient(135deg, #8b5cf6, #7c3aed)'
                }
                
                for idx, prayer in enumerate(prayer_list):
                    with prayer_cols[idx % 3]:
                        is_next = next_prayer and next_prayer['name'] == prayer
                        border_style = "border: 3px solid #fbbf24;" if is_next else ""
                        
                        st.markdown(f"""
                        <div style="background: {prayer_colors.get(prayer, '#059669')};
                                    padding: 1.5rem; border-radius: 15px; text-align: center;
                                    color: white; margin-bottom: 1rem;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                                    {border_style}">
                            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">
                                {prayer_icons.get(prayer, '🕌')}
                            </div>
                            <h3 style="margin: 0; font-size: 1.3rem;">{prayer}</h3>
                            <h2 style="margin: 0.5rem 0 0 0; font-size: 2rem;">
                                {prayer_times.get(prayer, '--:--')}
                            </h2>
                            {('<p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">⏰ NEXT</p>' if is_next else '')}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Monthly calendar view
                st.markdown("---")
                
                with st.expander("📅 View Monthly Prayer Times"):
                    month_year = st.date_input("Select Month", datetime.now())
                    
                    if st.button("📥 Download Monthly Timetable", use_container_width=True):
                        st.info("💡 Feature coming soon! You'll be able to download PDF timetables.")
            
            else:
                st.error("❌ Could not load prayer times. Please check your internet connection.")
        
        # ========== TAB 2: LOCATION SETTINGS ==========
        
        with prayer_tabs[1]:
            st.markdown("### 📍 Prayer Time Location Settings")
            
            st.info("""
            Set your exact location for accurate prayer times.
            You can use auto-detection or enter coordinates manually.
            """)
            
            with st.form("location_settings"):
                st.markdown("#### 🌍 Location Coordinates")
                
                loc_col1, loc_col2 = st.columns(2)
                
                with loc_col1:
                    latitude = st.number_input(
                        "Latitude",
                        value=settings['latitude'],
                        min_value=-90.0,
                        max_value=90.0,
                        format="%.6f",
                        help="Your latitude coordinate"
                    )
                
                with loc_col2:
                    longitude = st.number_input(
                        "Longitude",
                        value=settings['longitude'],
                        min_value=-180.0,
                        max_value=180.0,
                        format="%.6f",
                        help="Your longitude coordinate"
                    )
                
                st.markdown("#### 🕰️ Timezone")
                
                common_timezones = [
                    'Asia/Riyadh', 'Asia/Dubai', 'Asia/Karachi', 'Asia/Kolkata',
                    'Asia/Dhaka', 'Asia/Jakarta', 'Asia/Kuala_Lumpur', 'Europe/Istanbul',
                    'Africa/Cairo', 'Europe/London', 'America/New_York', 'America/Toronto',
                    'Australia/Sydney', 'Asia/Tokyo', 'Asia/Singapore'
                ]
                
                timezone = st.selectbox(
                    "Select Timezone",
                    common_timezones,
                    index=common_timezones.index(settings['timezone']) if settings['timezone'] in common_timezones else 0
                )
                
                st.markdown("#### 📐 Calculation Method")
                
                methods = get_calculation_methods()
                method_names = list(methods.values())
                method_ids = list(methods.keys())
                
                current_method_idx = method_ids.index(str(settings['calculation_method'])) if str(settings['calculation_method']) in method_ids else 1
                
                selected_method_name = st.selectbox(
                    "Prayer Time Calculation Method",
                    method_names,
                    index=current_method_idx,
                    help="Different regions use different calculation methods"
                )
                
                selected_method_id = int(method_ids[method_names.index(selected_method_name)])
                
                st.markdown("---")
                
                if st.form_submit_button("💾 Save Location Settings", type="primary", use_container_width=True):
                    settings['latitude'] = latitude
                    settings['longitude'] = longitude
                    settings['timezone'] = timezone
                    settings['calculation_method'] = selected_method_id
                    
                    save_prayer_notification_settings(st.session_state.user_id, settings)
                    
                    st.success("✅ Location settings saved!")
                    st.balloons()
                    st.rerun()
            
            st.markdown("---")
            st.markdown("#### 🗺️ How to Find Your Coordinates")
            
            st.markdown("""
            **Option 1: Use Google Maps**
            1. Open Google Maps
            2. Right-click on your location
            3. Click on the coordinates to copy them
            
            **Option 2: Use GPS**
            - Enable location on your device
            - Click "Auto-Detect My Location" above
            
            **Popular Cities:**
            - 🕋 Makkah: 21.4225, 39.8262
            - 🕌 Madinah: 24.4672, 39.6111
            - 🏙️ Dubai: 25.2048, 55.2708
            - 🏙️ Karachi: 24.8607, 67.0011
            - 🏙️ London: 51.5074, -0.1278
            - 🏙️ New York: 40.7128, -74.0060
            """)
        
        # ========== TAB 3: NOTIFICATIONS ==========
        
        with prayer_tabs[2]:
            st.markdown("### 🔔 Prayer Time Notifications")
            
            st.warning("""
            ⚠️ **Browser Notifications**
            
            Web browsers have limited notification capabilities. For reliable prayer time notifications, 
            we recommend:
            
            1. **Mobile App**: Install a dedicated prayer times app on your phone
            2. **Desktop Notifications**: Use this feature when browsing on computer
            3. **Email Reminders**: Enable email notifications (coming soon)
            
            This web app can show browser notifications when you have the page open.
            """)
            
            with st.form("notification_settings"):
                st.markdown("#### ⏰ Notification Preferences")
                
                enable_notifications = st.checkbox(
                    "Enable Prayer Time Notifications",
                    value=settings.get('enabled', True)
                )
                
                if enable_notifications:
                    st.markdown("**Select Prayers to be Notified:**")
                    
                    notif_col1, notif_col2 = st.columns(2)
                    
                    with notif_col1:
                        notify_fajr = st.checkbox("🌅 Fajr", value=settings.get('fajr', True))
                        notify_dhuhr = st.checkbox("🌞 Dhuhr", value=settings.get('dhuhr', True))
                        notify_asr = st.checkbox("🌤️ Asr", value=settings.get('asr', True))
                    
                    with notif_col2:
                        notify_maghrib = st.checkbox("🌇 Maghrib", value=settings.get('maghrib', True))
                        notify_isha = st.checkbox("🌙 Isha", value=settings.get('isha', True))
                    
                    st.markdown("**Notification Timing:**")
                    
                    minutes_before = st.slider(
                        "Notify me (minutes before prayer time)",
                        min_value=0,
                        max_value=60,
                        value=settings.get('minutes_before', 15),
                        step=5,
                        help="Get notified before the prayer time"
                    )
                
                st.markdown("---")
                
                if st.form_submit_button("💾 Save Notification Settings", type="primary", use_container_width=True):
                    settings['enabled'] = enable_notifications
                    settings['fajr'] = notify_fajr if enable_notifications else False
                    settings['dhuhr'] = notify_dhuhr if enable_notifications else False
                    settings['asr'] = notify_asr if enable_notifications else False
                    settings['maghrib'] = notify_maghrib if enable_notifications else False
                    settings['isha'] = notify_isha if enable_notifications else False
                    settings['minutes_before'] = minutes_before
                    
                    save_prayer_notification_settings(st.session_state.user_id, settings)
                    
                    st.success("✅ Notification settings saved!")
                    st.rerun()
            
            # JavaScript for browser notifications
            if settings.get('enabled', True):
                st.markdown("""
                <script>
                // Request notification permission
                if ('Notification' in window) {
                    if (Notification.permission === 'default') {
                        Notification.requestPermission();
                    }
                }
                </script>
                """, unsafe_allow_html=True)
                
                st.info("💡 **Tip**: Keep this tab open to receive notifications!")
        
        # ========== TAB 4: QIBLA DIRECTION ==========
        
        with prayer_tabs[3]:
            st.markdown("### 🧭 Qibla Direction Finder")
            
            st.info("""
            Find the direction to the Kaaba (Qibla) from your current location.
            The Qibla direction is measured in degrees from North.
            """)
            
            qibla_lat = st.number_input("Your Latitude", value=settings['latitude'], format="%.6f", key="qibla_lat")
            qibla_lon = st.number_input("Your Longitude", value=settings['longitude'], format="%.6f", key="qibla_lon")
            
            if st.button("🧭 Calculate Qibla Direction", type="primary", use_container_width=True):
                with st.spinner("Calculating..."):
                    qibla_direction = get_qibla_direction(qibla_lat, qibla_lon)
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #059669, #10b981);
                                padding: 3rem; border-radius: 20px; text-align: center;
                                color: white; margin: 2rem 0;">
                        <div style="font-size: 4rem; margin-bottom: 1rem;">🧭</div>
                        <h2 style="margin: 0;">Qibla Direction</h2>
                        <h1 style="margin: 1rem 0; font-size: 4rem;">{qibla_direction:.2f}°</h1>
                        <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">
                            From North (Clockwise)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Compass visualization
                    st.markdown(f"""
                    <div style="width: 300px; height: 300px; margin: 2rem auto;
                                border: 4px solid #059669; border-radius: 50%;
                                position: relative; background: white;">
                        <div style="position: absolute; top: 10px; left: 50%;
                                    transform: translateX(-50%); font-weight: bold;">N</div>
                        <div style="position: absolute; bottom: 10px; left: 50%;
                                    transform: translateX(-50%); font-weight: bold;">S</div>
                        <div style="position: absolute; left: 10px; top: 50%;
                                    transform: translateY(-50%); font-weight: bold;">W</div>
                        <div style="position: absolute; right: 10px; top: 50%;
                                    transform: translateY(-50%); font-weight: bold;">E</div>
                        
                        <!-- Qibla arrow -->
                        <div style="position: absolute; top: 50%; left: 50%;
                                    width: 4px; height: 120px; background: #059669;
                                    transform-origin: bottom center;
                                    transform: translate(-50%, -100%) rotate({qibla_direction}deg);">
                            <div style="width: 0; height: 0; 
                                        border-left: 8px solid transparent;
                                        border-right: 8px solid transparent;
                                        border-bottom: 20px solid #059669;
                                        position: absolute;
                                        top: -20px;
                                        left: 50%;
                                        transform: translateX(-50%);"></div>
                        </div>
                        
                        <!-- Center dot -->
                        <div style="position: absolute; top: 50%; left: 50%;
                                    width: 10px; height: 10px; background: #dc2626;
                                    border-radius: 50%; transform: translate(-50%, -50%);"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.success("✅ Use a compass or compass app to find this direction!")
                    
                    st.markdown("""
                    **📱 How to Use:**
                    1. Get a physical compass or compass app on your phone
                    2. Face the direction shown above (degrees from North)
                    3. That's the direction of the Kaaba in Makkah!
                    
                    **💡 Pro Tip:**
                    - Most smartphones have a built-in compass app
                    - Many Islamic apps include Qibla compass features
                    - You can also use the sun's position as a reference
                    """)

    # ========== My Bookings PAGE ==========
    elif st.session_state.page == "💼 My Bookings":
        st.markdown("## 💼 My Umrah Bookings")
        
        # Get user's bookings
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Match by email since we don't link user_id during inquiry
        c.execute("SELECT email FROM users WHERE id=?", (st.session_state.user_id,))
        user_email = c.fetchone()[0]
        
        c.execute("""SELECT b.booking_id, p.package_name, b.travelers, b.total_amount,
                    b.payment_status, b.booking_status, b.departure_date, b.return_date,
                    b.booking_date, a.company_name, a.phone, a.email
                    FROM bookings b
                    JOIN packages p ON b.package_id = p.package_id
                    JOIN agent_partners a ON b.agent_id = a.agent_id
                    WHERE b.customer_email=?
                    ORDER BY b.booking_date DESC""",
                (user_email,))
        
        bookings = c.fetchall()
        conn.close()
        
        if not bookings:
            st.info("📭 No confirmed bookings yet. Browse packages and submit inquiries!")
            
            if st.button("📦 Browse Packages", use_container_width=True):
                st.session_state.page = "📦 Packages"
                st.rerun()
        else:
            st.success(f"✅ You have {len(bookings)} confirmed booking(s)!")
            
            for booking in bookings:
                payment_status_color = {
                    "Paid": "🟢",
                    "Pending": "🟡",
                    "Partial": "🟠",
                    "Refunded": "🔴"
                }
                
                booking_status_color = {
                    "Confirmed": "🟢",
                    "Completed": "✅",
                    "Cancelled": "🔴"
                }
                
                with st.expander(f"🎫 {booking[1]} - {booking_status_color.get(booking[5], '⚪')} {booking[5]}"):
                    book_col1, book_col2 = st.columns([0.6, 0.4])
                    
                    with book_col1:
                        st.markdown("### 📋 Booking Details")
                        st.write(f"**Booking ID:** {booking[0][:8]}...")
                        st.write(f"**Package:** {booking[1]}")
                        st.write(f"**Travelers:** {booking[2]}")
                        st.write(f"**Total Amount:** ${booking[3]:,.2f}")
                        st.write(f"**Departure:** {booking[6]}")
                        st.write(f"**Return:** {booking[7]}")
                        st.write(f"**Booked On:** {booking[8]}")
                        
                        st.markdown("---")
                        
                        st.markdown("### 🏢 Travel Agent")
                        st.write(f"**Company:** {booking[9]}")
                        st.write(f"**Phone:** {booking[10]}")
                        st.write(f"**Email:** {booking[11]}")
                    
                    with book_col2:
                        # Payment status
                        st.markdown(f"### {payment_status_color.get(booking[4], '⚪')} Payment Status")
                        st.markdown(f"## {booking[4]}")
                        
                        if booking[4] == "Pending":
                            st.warning("⚠️ Payment pending. Contact your travel agent.")
                        elif booking[4] == "Paid":
                            st.success("✅ Payment confirmed!")
                        elif booking[4] == "Partial":
                            st.info("ℹ️ Partial payment received.")
                        
                        st.markdown("---")
                        
                        # Booking status
                        st.markdown(f"### {booking_status_color.get(booking[5], '⚪')} Booking Status")
                        st.markdown(f"## {booking[5]}")
                        
                        if booking[5] == "Confirmed":
                            days_until = (datetime.strptime(booking[6], '%Y-%m-%d').date() - datetime.now().date()).days
                            if days_until > 0:
                                st.info(f"🗓️ {days_until} days until departure")
                            else:
                                st.warning("🛫 Departure date has passed")
    
    # ========== CHECKLIST PAGE ==========
    
    elif st.session_state.page == "✅ Checklist":
        st.markdown("## ✅ Umrah Travel Checklist")
        
        checklist = get_umrah_checklist()
        user_progress = get_checklist_progress(st.session_state.user_id)
        
        total_items = sum(len(cat['items']) for cat in checklist.values())
        checked_items = sum(len(items) for items in user_progress.values())
        progress_percent = (checked_items / total_items * 100) if total_items > 0 else 0
        
        st.markdown(f"### 📊 Progress: {progress_percent:.0f}%")
        st.progress(progress_percent / 100)
        st.caption(f"{checked_items} of {total_items} items packed")
        
        st.markdown("---")
        
        for category, data in checklist.items():
            category_total = len(data['items'])
            category_checked = len(user_progress.get(category, []))
            
            priority_icons = {
                'critical': '🔴',
                'high': '🟡',
                'medium': '🟢',
                'low': '⚪'
            }
            
            icon = priority_icons.get(data['priority'], '⚪')
            
            with st.expander(f"{icon} {category} ({category_checked}/{category_total})"):
                for item in data['items']:
                    is_checked = item in user_progress.get(category, [])
                    
                    col_check, col_item = st.columns([0.05, 0.95])
                    
                    with col_check:
                        checked = st.checkbox(
                            "",
                            value=is_checked,
                            key=f"c_{category}_{item}",
                            label_visibility="collapsed"
                        )
                        
                        if checked != is_checked:
                            save_checklist_progress(st.session_state.user_id, category, item, checked)
                            st.rerun()
                    
                    with col_item:
                        if is_checked:
                            st.markdown(f"~~{item}~~ ✅")
                        else:
                            st.markdown(item)
    
    # ========== INFO PAGE ==========
    
    elif st.session_state.page == "ℹ️ Info":
        st.markdown("## ℹ️ About Umrah Pro")
        
        st.markdown(f"""
        ### 📍 Your Settings
        
        **Country:** {user_country}  
        **Currency:** {currency_info['currency']} ({currency_info['symbol']})  
        **Subscription:** {'Premium ⭐' if is_premium else 'Free 🆓'}
        
        *Prices and packages are customized for your country*
        
        ---
        
        ### 📱 Features
        
        **🆓 Free Plan:**
        - ✅ 7 Umrah steps with duas
        - ✅ Track 3 family members
        - ✅ Prayer times & Qibla
        - ✅ First 10 verses of Quran
        - ✅ Travel checklist
        - ✅ Browse packages in your currency
        
        **⭐ Premium Plan ($4.99/month):**
        - ✅ All Free features
        - ✅ Unlimited family tracking
        - ✅ Full Quran reading
        - ✅ Ad-free experience
        - ✅ Priority support
        - ✅ Offline access
        - ✅ Exclusive package deals
        
        ---
        
        ### 📞 Contact & Support
        - **Email:** support@umrahpro.com
        - **WhatsApp:** +966 XX XXX XXXX
        - **Website:** www.umrahpro.com
        
        ---
        
        ### 🌍 Multi-Currency Support
        
        We support {len(CURRENCY_DATA)} countries and currencies!  
        Prices are automatically converted to your local currency.
        
        **Supported Countries:**
        """)
        
        # Display all supported countries in columns
        country_cols = st.columns(4)
        for idx, (country, data) in enumerate(CURRENCY_DATA.items()):
            with country_cols[idx % 4]:
                st.caption(f"{country}")
                st.caption(f"💱 {data['currency']}")
        
        st.markdown("---")
        
        if not is_premium:
            if st.button("⬆️ Upgrade to Premium Now", type="primary", use_container_width=True):
                upgrade_subscription(st.session_state.user_id, 'premium')
                st.session_state.subscription = 'premium'
                st.success("✅ Upgraded to Premium!")
                st.balloons()
                st.rerun()
    
    # ========== FOOTER ==========
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;padding:2rem;background:linear-gradient(135deg,#059669,#10b981);
                color:white;border-radius:15px;">
        <h2>تَقَبَّلَ اللهُ مِنَّا وَمِنكُمْ</h2>
        <p>May Allah accept your Umrah!</p>
        <p style="font-size:0.9rem;opacity:0.9;">Umrah Pro v3.1 • Made with ❤️</p>
    </div>
    """, unsafe_allow_html=True)