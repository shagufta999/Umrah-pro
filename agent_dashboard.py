"""
AGENT DASHBOARD - UMRAH PRO
Self-service portal for travel agents to manage packages
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import hashlib
import uuid
import pandas as pd

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Agent Dashboard - Umrah Pro",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CURRENCY DATA (ADD THIS!) ==========

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
    },
    "🇰🇼 Kuwait": {
        "currency": "KWD",
        "symbol": "KD",
        "rate": 0.31,
        "flag": "🇰🇼"
    },
    "🇶🇦 Qatar": {
        "currency": "QAR",
        "symbol": "QR",
        "rate": 3.64,
        "flag": "🇶🇦"
    },
    "🇴🇲 Oman": {
        "currency": "OMR",
        "symbol": "OMR",
        "rate": 0.38,
        "flag": "🇴🇲"
    },
    "🇧🇭 Bahrain": {
        "currency": "BHD",
        "symbol": "BD",
        "rate": 0.38,
        "flag": "🇧🇭"
    },
    "🇯🇴 Jordan": {
        "currency": "JOD",
        "symbol": "JD",
        "rate": 0.71,
        "flag": "🇯🇴"
    },
    "🇱🇧 Lebanon": {
        "currency": "LBP",
        "symbol": "LL",
        "rate": 15000,
        "flag": "🇱🇧"
    },
    "🇲🇦 Morocco": {
        "currency": "MAD",
        "symbol": "MAD",
        "rate": 10,
        "flag": "🇲🇦"
    },
    "🇩🇿 Algeria": {
        "currency": "DZD",
        "symbol": "DA",
        "rate": 135,
        "flag": "🇩🇿"
    },
    "🇹🇳 Tunisia": {
        "currency": "TND",
        "symbol": "DT",
        "rate": 3.1,
        "flag": "🇹🇳"
    },
    "🇱🇾 Libya": {
        "currency": "LYD",
        "symbol": "LD",
        "rate": 4.8,
        "flag": "🇱🇾"
    },
    "🇸🇩 Sudan": {
        "currency": "SDG",
        "symbol": "SDG",
        "rate": 600,
        "flag": "🇸🇩"
    },
    "🇮🇶 Iraq": {
        "currency": "IQD",
        "symbol": "IQD",
        "rate": 1310,
        "flag": "🇮🇶"
    },
    "🇸🇾 Syria": {
        "currency": "SYP",
        "symbol": "SYP",
        "rate": 2512,
        "flag": "🇸🇾"
    },
    "🇾🇪 Yemen": {
        "currency": "YER",
        "symbol": "YER",
        "rate": 250,
        "flag": "🇾🇪"
    },
    "🇦🇫 Afghanistan": {
        "currency": "AFN",
        "symbol": "AFN",
        "rate": 70,
        "flag": "🇦🇫"
    },
    "🇮🇷 Iran": {
        "currency": "IRR",
        "symbol": "IRR",
        "rate": 42000,
        "flag": "🇮🇷"
    },
    "🇺🇿 Uzbekistan": {
        "currency": "UZS",
        "symbol": "UZS",
        "rate": 11000,
        "flag": "🇺🇿"
    },
    "🇰🇿 Kazakhstan": {
        "currency": "KZT",
        "symbol": "KZT",
        "rate": 450,
        "flag": "🇰🇿"
    },
    "🇦🇿 Azerbaijan": {
        "currency": "AZN",
        "symbol": "AZN",
        "rate": 1.7,
        "flag": "🇦🇿"
    },
    "🇹🇲 Turkmenistan": {
        "currency": "TMT",
        "symbol": "TMT",
        "rate": 3.5,
        "flag": "🇹🇲"
    },
    "🇰🇬 Kyrgyzstan": {
        "currency": "KGS",
        "symbol": "KGS",
        "rate": 85,
        "flag": "🇰🇬"
    },
    "🇹🇯 Tajikistan": {
        "currency": "TJS",
        "symbol": "TJS",
        "rate": 10.5,
        "flag": "🇹🇯"
    },
    "🇧🇳 Brunei": {
        "currency": "BND",
        "symbol": "BND",
        "rate": 1.34,
        "flag": "🇧🇳"
    },
    "🇲🇻 Maldives": {
        "currency": "MVR",
        "symbol": "MVR",
        "rate": 15.4,
        "flag": "🇲🇻"
    },
    "🇰🇪 Kenya": {
        "currency": "KES",
        "symbol": "KSh",
        "rate": 130,
        "flag": "🇰🇪"
    },
    "🇹🇿 Tanzania": {
        "currency": "TZS",
        "symbol": "TSh",
        "rate": 2500,
        "flag": "🇹🇿"
    },
    "🇺🇬 Uganda": {
        "currency": "UGX",
        "symbol": "USh",
        "rate": 3700,
        "flag": "🇺🇬"
    },
    "🇪🇹 Ethiopia": {
        "currency": "ETB",
        "symbol": "ETB",
        "rate": 55,
        "flag": "🇪🇹"
    },
    "🇸🇴 Somalia": {
        "currency": "SOS",
        "symbol": "SOS",
        "rate": 570,
        "flag": "🇸🇴"
    },
    "🇸🇳 Senegal": {
        "currency": "XOF",
        "symbol": "CFA",
        "rate": 605,
        "flag": "🇸🇳"
    },
    "🇬🇭 Ghana": {
        "currency": "GHS",
        "symbol": "GH₵",
        "rate": 12,
        "flag": "🇬🇭"
    },
    "🇨🇮 Ivory Coast": {
        "currency": "XOF",
        "symbol": "CFA",
        "rate": 605,
        "flag": "🇨🇮"
    },
    "🇨🇲 Cameroon": {
        "currency": "XAF",
        "symbol": "FCFA",
        "rate": 605,
        "flag": "🇨🇲"
    },
    "Other": {
        "currency": "USD",
        "symbol": "$",
        "rate": 1.0,
        "flag": "🌍"
    }
}


# ========== DATABASE INITIALIZATION ==========

def init_agent_dashboard_tables():
    """Initialize tables for agent dashboard"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    # Agent credentials table
    c.execute('''CREATE TABLE IF NOT EXISTS agent_credentials
                 (credential_id TEXT PRIMARY KEY,
                  agent_id TEXT,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  created_at TIMESTAMP,
                  last_login TIMESTAMP,
                  FOREIGN KEY (agent_id) REFERENCES agent_partners(agent_id))''')
    
    # Packages table
    c.execute('''CREATE TABLE IF NOT EXISTS packages
                 (package_id TEXT PRIMARY KEY,
                  agent_id TEXT,
                  package_name TEXT,
                  duration_days INTEGER,
                  duration_nights INTEGER,
                  price REAL,
                  category TEXT,
                  departure_city TEXT,
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
                  updated_at TIMESTAMP,
                  FOREIGN KEY (agent_id) REFERENCES agent_partners(agent_id))''')
    
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
                  inquiry_date TIMESTAMP,
                  FOREIGN KEY (package_id) REFERENCES packages(package_id),
                  FOREIGN KEY (agent_id) REFERENCES agent_partners(agent_id))''')
    
    # Analytics table
    c.execute('''CREATE TABLE IF NOT EXISTS agent_analytics
                 (analytics_id TEXT PRIMARY KEY,
                  agent_id TEXT,
                  date DATE,
                  page_views INTEGER,
                  package_views INTEGER,
                  inquiries INTEGER,
                  conversions INTEGER,
                  FOREIGN KEY (agent_id) REFERENCES agent_partners(agent_id))''')
    
    conn.commit()
    conn.close()

init_agent_dashboard_tables()

# ========== AUTHENTICATION ==========

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_agent_login(username, password):
    """Verify agent credentials"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    password_hash = hash_password(password)
    
    c.execute('''SELECT ac.agent_id, ap.company_name, ap.email, ap.status
                 FROM agent_credentials ac
                 JOIN agent_partners ap ON ac.agent_id = ap.agent_id
                 WHERE ac.username=? AND ac.password_hash=?''',
              (username, password_hash))
    
    result = c.fetchone()
    
    if result:
        # Update last login
        c.execute('UPDATE agent_credentials SET last_login=? WHERE username=?',
                  (datetime.now(), username))
        conn.commit()
    
    conn.close()
    
    return result if result else None

def create_agent_credentials(agent_id, username, password):
    """Create login credentials for an agent"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    credential_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    
    try:
        c.execute('''INSERT INTO agent_credentials
                     (credential_id, agent_id, username, password_hash, created_at)
                     VALUES (?,?,?,?,?)''',
                  (credential_id, agent_id, username, password_hash, datetime.now()))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def agent_login_page():
    """Agent login interface"""
    
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>🏢 Umrah Pro Agent Portal</h1>
        <p style="font-size: 1.2rem; color: #666;">
            Manage your packages and connect with customers
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("agent_login"):
            st.markdown("### 🔐 Agent Login")
            
            username = st.text_input("Username", placeholder="agent@company.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    result = verify_agent_login(username, password)
                    
                    if result:
                        if result[3] == 'Active':
                            st.session_state.agent_logged_in = True
                            st.session_state.agent_id = result[0]
                            st.session_state.agent_company = result[1]
                            st.session_state.agent_email = result[2]
                            st.session_state.agent_username = username
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Your account is not active. Please contact support.")
                    else:
                        st.error("❌ Invalid credentials")
        
        st.markdown("---")
        st.info("📧 **New Agent?** Contact support@umrahpro.com to get your login credentials")

# ========== DATABASE QUERIES ==========

def get_agent_packages(agent_id):
    """Get all packages for an agent"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('''SELECT package_id, package_name, duration_days, duration_nights,
                 price, category, departure_city, status, views, inquiries,
                 created_at, updated_at
                 FROM packages
                 WHERE agent_id=?
                 ORDER BY created_at DESC''',
              (agent_id,))
    
    packages = []
    for row in c.fetchall():
        packages.append({
            'id': row[0],
            'name': row[1],
            'duration_days': row[2],
            'duration_nights': row[3],
            'price': row[4],
            'category': row[5],
            'departure_city': row[6],
            'status': row[7],
            'views': row[8],
            'inquiries': row[9],
            'created_at': row[10],
            'updated_at': row[11]
        })
    
    conn.close()
    return packages

def get_package_details(package_id):
    """Get full details of a package"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM packages WHERE package_id=?', (package_id,))
    
    row = c.fetchone()
    
    if not row:
        conn.close()
        return None
    
    package = {
        'id': row[0],
        'agent_id': row[1],
        'name': row[2],
        'duration_days': row[3],
        'duration_nights': row[4],
        'price': row[5],
        'category': row[6],
        'departure_city': row[7],
        'departure_dates': row[8],
        'makkah_hotel': row[9],
        'makkah_hotel_rating': row[10],
        'makkah_distance': row[11],
        'madinah_hotel': row[12],
        'madinah_hotel_rating': row[13],
        'madinah_distance': row[14],
        'inclusions': row[15],
        'exclusions': row[16],
        'group_size': row[17],
        'status': row[18],
        'featured': row[19],
        'views': row[20],
        'inquiries': row[21]
    }
    
    conn.close()
    return package

def add_package(agent_id, package_data):
    """Add new package"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    package_id = str(uuid.uuid4())
    
    c.execute('''INSERT INTO packages
                 (package_id, agent_id, package_name, duration_days, duration_nights,
                  price, category, departure_city, departure_dates,
                  makkah_hotel, makkah_hotel_rating, makkah_distance,
                  madinah_hotel, madinah_hotel_rating, madinah_distance,
                  inclusions, exclusions, group_size, status, created_at, updated_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (package_id, agent_id, 
               package_data['name'], package_data['duration_days'], package_data['duration_nights'],
               package_data['price'], package_data['category'], package_data['departure_city'],
               package_data['departure_dates'], package_data['makkah_hotel'],
               package_data['makkah_rating'], package_data['makkah_distance'],
               package_data['madinah_hotel'], package_data['madinah_rating'],
               package_data['madinah_distance'], package_data['inclusions'],
               package_data['exclusions'], package_data['group_size'],
               'Active', datetime.now(), datetime.now()))
    
    conn.commit()
    conn.close()
    
    return package_id

def update_package(package_id, package_data):
    """Update existing package"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('''UPDATE packages SET
                 package_name=?, duration_days=?, duration_nights=?, price=?,
                 category=?, departure_city=?, departure_dates=?,
                 makkah_hotel=?, makkah_hotel_rating=?, makkah_distance=?,
                 madinah_hotel=?, madinah_hotel_rating=?, madinah_distance=?,
                 inclusions=?, exclusions=?, group_size=?, updated_at=?
                 WHERE package_id=?''',
              (package_data['name'], package_data['duration_days'], package_data['duration_nights'],
               package_data['price'], package_data['category'], package_data['departure_city'],
               package_data['departure_dates'], package_data['makkah_hotel'],
               package_data['makkah_rating'], package_data['makkah_distance'],
               package_data['madinah_hotel'], package_data['madinah_rating'],
               package_data['madinah_distance'], package_data['inclusions'],
               package_data['exclusions'], package_data['group_size'],
               datetime.now(), package_id))
    
    conn.commit()
    conn.close()

def update_package_status(package_id, status):
    """Update package status"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('UPDATE packages SET status=?, updated_at=? WHERE package_id=?',
              (status, datetime.now(), package_id))
    
    conn.commit()
    conn.close()

def delete_package(package_id):
    """Delete package"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('DELETE FROM packages WHERE package_id=?', (package_id,))
    
    conn.commit()
    conn.close()

def get_agent_inquiries(agent_id):
    """Get package inquiries for agent"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute('''SELECT pi.inquiry_id, pi.customer_name, pi.customer_email,
                 pi.customer_phone, pi.travelers, pi.preferred_date,
                 pi.message, pi.status, pi.inquiry_date, p.package_name
                 FROM package_inquiries pi
                 JOIN packages p ON pi.package_id = p.package_id
                 WHERE pi.agent_id=?
                 ORDER BY pi.inquiry_date DESC''',
              (agent_id,))
    
    inquiries = []
    for row in c.fetchall():
        inquiries.append({
            'id': row[0],
            'customer_name': row[1],
            'customer_email': row[2],
            'customer_phone': row[3],
            'travelers': row[4],
            'preferred_date': row[5],
            'message': row[6],
            'status': row[7],
            'inquiry_date': row[8],
            'package_name': row[9]
        })
    
    conn.close()
    return inquiries

def get_agent_stats(agent_id):
    """Get agent statistics"""
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    # Total packages
    c.execute('SELECT COUNT(*) FROM packages WHERE agent_id=?', (agent_id,))
    total_packages = c.fetchone()[0]
    
    # Active packages
    c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=? AND status='Active'", (agent_id,))
    active_packages = c.fetchone()[0]
    
    # Total views
    c.execute('SELECT SUM(views) FROM packages WHERE agent_id=?', (agent_id,))
    total_views = c.fetchone()[0] or 0
    
    # Total inquiries
    c.execute('SELECT COUNT(*) FROM package_inquiries WHERE agent_id=?', (agent_id,))
    total_inquiries = c.fetchone()[0]
    
    # Pending inquiries
    c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=? AND status='Pending'", (agent_id,))
    pending_inquiries = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total_packages': total_packages,
        'active_packages': active_packages,
        'total_views': total_views,
        'total_inquiries': total_inquiries,
        'pending_inquiries': pending_inquiries
    }

# ========== DASHBOARD PAGES ==========

def show_dashboard_overview():
    """Dashboard overview page"""
    
    st.markdown("## 📊 Dashboard Overview")
    
    stats = get_agent_stats(st.session_state.agent_id)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Packages", stats['total_packages'])
    
    with col2:
        st.metric("✅ Active Packages", stats['active_packages'])
    
    with col3:
        st.metric("👁️ Total Views", stats['total_views'])
    
    with col4:
        st.metric("📧 Inquiries", stats['total_inquiries'], 
                 f"{stats['pending_inquiries']} pending")
    
    st.markdown("---")
    
    # Recent activity
    col_act1, col_act2 = st.columns(2)
    
    with col_act1:
        st.markdown("### 📦 Your Packages")
        
        packages = get_agent_packages(st.session_state.agent_id)[:5]
        
        if packages:
            for pkg in packages:
                status_color = "🟢" if pkg['status'] == 'Active' else "🔴"
                
                st.markdown(f"""
                {status_color} **{pkg['name']}** - ${pkg['price']:,.0f}
                
                👁️ {pkg['views']} views • 📧 {pkg['inquiries']} inquiries
                """)
                st.markdown("---")
        else:
            st.info("No packages yet. Create your first package!")
    
    with col_act2:
        st.markdown("### 📧 Recent Inquiries")
        
        inquiries = get_agent_inquiries(st.session_state.agent_id)[:5]
        
        if inquiries:
            for inq in inquiries:
                status_icon = "⏳" if inq['status'] == 'Pending' else "✅"
                
                st.markdown(f"""
                {status_icon} **{inq['customer_name']}** - {inq['package_name']}
                
                📅 {inq['inquiry_date'][:10]} • {inq['travelers']} travelers
                """)
                st.markdown("---")
        else:
            st.info("No inquiries yet")

def show_packages_page():
    """Packages management page"""
    
    st.markdown("## 📦 Package Management")
    
    tab1, tab2 = st.tabs(["📋 My Packages", "➕ Add New Package"])
    
    with tab1:
        packages = get_agent_packages(st.session_state.agent_id)
        
        st.markdown(f"### Your Packages ({len(packages)})")
        
        if not packages:
            st.info("No packages yet. Create your first package!")
        else:
            for pkg in packages:
                with st.expander(f"{pkg['name']} - ${pkg['price']:,.0f} ({pkg['status']})"):
                    # Get full details
                    details = get_package_details(pkg['id'])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Duration:** {details['duration_days']} Days / {details['duration_nights']} Nights")
                        st.write(f"**Category:** {details['category']}")
                        st.write(f"**Departure City:** {details['departure_city']}")
                        st.write(f"**Group Size:** {details['group_size']}")
                    
                    with col2:
                        st.write(f"**Makkah Hotel:** {details['makkah_hotel']} ({details['makkah_hotel_rating']}⭐)")
                        st.write(f"**Madinah Hotel:** {details['madinah_hotel']} ({details['madinah_hotel_rating']}⭐)")
                        st.write(f"**Views:** {pkg['views']}")
                        st.write(f"**Inquiries:** {pkg['inquiries']}")
                    
                    st.markdown("**Inclusions:**")
                    st.text(details['inclusions'])
                    
                    st.markdown("---")
                    
                    # Actions
                    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                    
                    with btn_col1:
                        if st.button("✏️ Edit", key=f"edit_{pkg['id']}"):
                            st.session_state.editing_package = pkg['id']
                            st.rerun()
                    
                    with btn_col2:
                        if pkg['status'] == 'Active':
                            if st.button("⏸️ Pause", key=f"pause_{pkg['id']}"):
                                update_package_status(pkg['id'], 'Paused')
                                st.success("Package paused")
                                st.rerun()
                        else:
                            if st.button("▶️ Activate", key=f"activate_{pkg['id']}"):
                                update_package_status(pkg['id'], 'Active')
                                st.success("Package activated")
                                st.rerun()
                    
                    with btn_col3:
                        if st.button("📊 Stats", key=f"stats_{pkg['id']}"):
                            st.info(f"Views: {pkg['views']} | Inquiries: {pkg['inquiries']}")
                    
                    with btn_col4:
                        if st.button("🗑️ Delete", key=f"delete_{pkg['id']}"):
                            delete_package(pkg['id'])
                            st.success("Package deleted")
                            st.rerun()
    
    with tab2:
        st.markdown("### ➕ Create New Package")
        
        with st.form("add_package_form"):
            # Basic Info
            st.markdown("#### 📋 Basic Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                package_name = st.text_input("Package Name *", placeholder="Premium Umrah 14 Days")
                category = st.selectbox("Category *", 
                    ["Economy", "Standard", "Premium", "VIP Luxury", "Family"])
                price = st.number_input("Price (USD) *", min_value=0.0, value=2500.0, step=100.0)
            
            with col2:
                duration_days = st.number_input("Duration (Days) *", min_value=1, value=14)
                duration_nights = st.number_input("Duration (Nights) *", min_value=1, value=13)
                group_size = st.text_input("Group Size", placeholder="20-25 people")
            
            departure_city = st.text_input("Departure City *", placeholder="New York, Los Angeles, Chicago")
            departure_dates = st.text_area("Departure Dates *", 
                placeholder="March 15, 2024\nApril 12, 2024\nMay 10, 2024")
            
            # Hotels
            st.markdown("#### 🏨 Hotel Details")
            
            col_hotel1, col_hotel2 = st.columns(2)
            
            with col_hotel1:
                st.markdown("**Makkah Hotel**")
                makkah_hotel = st.text_input("Hotel Name (Makkah) *", placeholder="Elaf Kinda Hotel")
                makkah_rating = st.selectbox("Hotel Rating (Makkah) *", [3, 4, 5], index=1)
                makkah_distance = st.text_input("Distance from Haram (Makkah)", placeholder="500 meters")
            
            with col_hotel2:
                st.markdown("**Madinah Hotel**")
                madinah_hotel = st.text_input("Hotel Name (Madinah) *", placeholder="Taiba Hotel")
                madinah_rating = st.selectbox("Hotel Rating (Madinah) *", [3, 4, 5], index=1)
                madinah_distance = st.text_input("Distance from Haram (Madinah)", placeholder="300 meters")
            
            # Inclusions & Exclusions
            st.markdown("#### 📝 Package Details")
            
            col_details1, col_details2 = st.columns(2)
            
            with col_details1:
                inclusions = st.text_area("Inclusions *", 
                    placeholder="✈️ Round-trip airfare\n🏨 Hotel accommodation\n🚌 Ground transportation\n📋 Visa processing\n🍽️ Daily breakfast and dinner",
                    height=200)
            
            with col_details2:
                exclusions = st.text_area("Exclusions", 
                    placeholder="❌ Lunch\n❌ Personal expenses\n❌ Travel insurance\n❌ Tips and gratuities",
                    height=200)
            
            # Submit
            st.markdown("---")
            
            submit = st.form_submit_button("✅ Create Package", type="primary", use_container_width=True)

            # In agent_dashboard.py - Add this field
            target_countries = st.multiselect(
                "Target Countries",
                list(CURRENCY_DATA.keys()),
                help="Select countries where this package is available"
            )
            
            if submit:
                if not package_name or not departure_city or not makkah_hotel or not madinah_hotel:
                    st.error("❌ Please fill in all required fields (*)")
                else:
                    package_data = {
                        'name': package_name,
                        'duration_days': duration_days,
                        'duration_nights': duration_nights,
                        'price': price,
                        'category': category,
                        'departure_city': departure_city,
                        'departure_dates': departure_dates,
                        'makkah_hotel': makkah_hotel,
                        'makkah_rating': makkah_rating,
                        'makkah_distance': makkah_distance,
                        'madinah_hotel': madinah_hotel,
                        'madinah_rating': madinah_rating,
                        'madinah_distance': madinah_distance,
                        'inclusions': inclusions,
                        'exclusions': exclusions or 'None',
                        'group_size': group_size or 'Open'
                    }
                    
                    package_id = add_package(st.session_state.agent_id, package_data)
                    
                    st.success(f"✅ Package '{package_name}' created successfully!")
                    st.balloons()
                    
                    st.info("💡 Your package is now live and visible to customers on the main app!")

def show_inquiries_page():
    """Show and manage package inquiries"""
    st.markdown("## 📧 Package Inquiries")
    st.caption("Manage customer inquiries for your packages")
    
    # Get inquiries
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute("""SELECT i.inquiry_id, i.package_id, i.customer_name, i.customer_email,
                 i.customer_phone, i.travelers, i.preferred_date, i.status, i.inquiry_date,
                 i.message, p.package_name, p.price
                 FROM package_inquiries i
                 JOIN packages p ON i.package_id = p.package_id
                 WHERE i.agent_id=?
                 ORDER BY i.inquiry_date DESC""",
              (st.session_state.agent_id,))
    
    inquiries = c.fetchall()
    conn.close()
    
    if not inquiries:
        st.info("📭 No inquiries yet. Customers will see your packages and send inquiries!")
        return
    
    # Statistics
    total_inquiries = len(inquiries)
    pending = sum(1 for inq in inquiries if inq[7] == 'Pending')
    contacted = sum(1 for inq in inquiries if inq[7] == 'Contacted')
    converted = sum(1 for inq in inquiries if inq[7] == 'Converted')
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("📧 Total", total_inquiries)
    with stat_col2:
        st.metric("⏳ Pending", pending)
    with stat_col3:
        st.metric("📞 Contacted", contacted)
    with stat_col4:
        st.metric("✅ Converted", converted)
    
    st.markdown("---")
    
    # Filter
    filter_status = st.selectbox("Filter by Status", 
        ["All", "Pending", "Contacted", "Converted", "Rejected"])
    
    st.markdown("---")
    
    # Display inquiries
    for inquiry in inquiries:  # THIS IS WHERE 'inquiry' IS DEFINED!
        # Apply filter
        if filter_status != "All" and inquiry[7] != filter_status:
            continue
        
        status_colors = {
            'Pending': '🟡',
            'Contacted': '🔵',
            'Converted': '🟢',
            'Rejected': '🔴'
        }
        
        status_icon = status_colors.get(inquiry[7], '⚪')
        
        with st.expander(f"{status_icon} {inquiry[2]} - {inquiry[10]} ({inquiry[7]})"):
            inq_col1, inq_col2 = st.columns([0.6, 0.4])
            
            with inq_col1:
                st.markdown("**📋 Inquiry Details:**")
                st.write(f"**Customer:** {inquiry[2]}")
                st.write(f"**Email:** {inquiry[3]}")
                st.write(f"**Phone:** {inquiry[4]}")
                st.write(f"**Package:** {inquiry[10]}")
                st.write(f"**Price:** ${inquiry[11]:,.2f}")
                st.write(f"**Travelers:** {inquiry[5]}")
                st.write(f"**Preferred Date:** {inquiry[6]}")
                st.write(f"**Status:** {inquiry[7]}")
                st.write(f"**Inquiry Date:** {inquiry[8]}")
                
                if inquiry[9]:
                    st.markdown("**💬 Message:**")
                    st.info(inquiry[9])
            
            with inq_col2:
                st.markdown("**🔧 Actions:**")
                
                # Update status
                new_status = st.selectbox(
                    "Change Status",
                    ["Pending", "Contacted", "Converted", "Rejected"],
                    index=["Pending", "Contacted", "Converted", "Rejected"].index(inquiry[7]) if inquiry[7] in ["Pending", "Contacted", "Converted", "Rejected"] else 0,
                    key=f"status_{inquiry[0]}"
                )
                
                if st.button("💾 Update Status", key=f"update_{inquiry[0]}", use_container_width=True):
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("UPDATE package_inquiries SET status=? WHERE inquiry_id=?",
                             (new_status, inquiry[0]))
                    conn.commit()
                    conn.close()
                    st.success("✅ Status updated!")
                    st.rerun()
                
                st.markdown("---")
                
                # Quick actions
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    if st.button("📧 Email", key=f"email_{inquiry[0]}", use_container_width=True):
                        st.info(f"📧 Email: {inquiry[3]}")
                
                with action_col2:
                    if st.button("📞 Call", key=f"call_{inquiry[0]}", use_container_width=True):
                        st.info(f"📞 Phone: {inquiry[4]}")
                
                st.markdown("---")
                
                # ========== CONVERT TO BOOKING BUTTON (ADD HERE!) ==========
                
                # Check if already converted
                conn = sqlite3.connect('umrah_pro.db')
                c = conn.cursor()
                
                # Check if booking_confirmed column exists
                try:
                    c.execute("SELECT booking_confirmed, converted_to_booking_id FROM package_inquiries WHERE inquiry_id=?", 
                             (inquiry[0],))
                    booking_check = c.fetchone()
                    is_converted = booking_check and booking_check[0] == 1
                    booking_id_link = booking_check[1] if booking_check and len(booking_check) > 1 else None
                except:
                    is_converted = False
                    booking_id_link = None
                
                conn.close()
                
                if not is_converted and inquiry[7] != 'Converted':
                    if st.button("✅ Convert to Booking", key=f"convert_{inquiry[0]}", 
                                type="primary", use_container_width=True):
                        st.session_state[f'show_booking_form_{inquiry[0]}'] = True
                        st.rerun()
                    
                    # Show booking form if button clicked
                    if st.session_state.get(f'show_booking_form_{inquiry[0]}', False):
                        with st.form(f"booking_form_{inquiry[0]}"):
                            st.markdown("### 📝 Confirm Booking Details")
                            
                            book_col1, book_col2 = st.columns(2)
                            
                            with book_col1:
                                total_amount = st.number_input("Total Amount ($)", 
                                    min_value=0.0, 
                                    value=float(inquiry[11]) * float(inquiry[5]),
                                    step=100.0)
                                departure_date = st.date_input("Departure Date")
                                payment_method = st.selectbox("Payment Method",
                                    ["Bank Transfer", "Credit Card", "Cash", "PayPal"])
                            
                            with book_col2:
                                commission_rate = st.number_input("Commission Rate (%)", 
                                    min_value=0.0, max_value=100.0, value=25.0, step=0.5)
                                return_date = st.date_input("Return Date")
                                payment_status = st.selectbox("Initial Payment Status",
                                    ["Pending", "Partial", "Paid"])
                            
                            special_requests = st.text_area("Special Requests/Notes")
                            
                            form_col1, form_col2 = st.columns(2)
                            
                            with form_col1:
                                confirm_booking = st.form_submit_button("🎉 Confirm Booking", 
                                    type="primary", use_container_width=True)
                            
                            with form_col2:
                                cancel_form = st.form_submit_button("❌ Cancel", 
                                    use_container_width=True)
                            
                            if cancel_form:
                                st.session_state[f'show_booking_form_{inquiry[0]}'] = False
                                st.rerun()
                            
                            if confirm_booking:
                                booking_id = str(uuid.uuid4())
                                commission_amount = total_amount * (commission_rate / 100)
                                
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                
                                try:
                                    # Create booking
                                    c.execute("""INSERT INTO bookings VALUES 
                                               (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                             (booking_id,
                                              inquiry[0],  # inquiry_id
                                              inquiry[1],  # package_id
                                              st.session_state.agent_id,
                                              None,  # user_id
                                              inquiry[2],  # customer_name
                                              inquiry[3],  # customer_email
                                              inquiry[4],  # customer_phone
                                              inquiry[5],  # travelers
                                              str(departure_date),
                                              total_amount / inquiry[5],  # package_price per person
                                              total_amount,
                                              commission_amount,
                                              payment_status,
                                              payment_method,
                                              None,  # payment_reference
                                              'Confirmed',  # booking_status
                                              datetime.now(),  # confirmed_by_agent_date
                                              datetime.now() if payment_status == 'Paid' else None,
                                              datetime.now(),  # booking_date
                                              str(departure_date),
                                              str(return_date),
                                              special_requests,
                                              None))  # notes
                                    
                                    # Update inquiry status
                                    c.execute("""UPDATE package_inquiries 
                                               SET status='Converted'
                                               WHERE inquiry_id=?""",
                                             (inquiry[0],))
                                    
                                    # Add booking_confirmed column if doesn't exist
                                    try:
                                        c.execute("UPDATE package_inquiries SET booking_confirmed=1, converted_to_booking_id=? WHERE inquiry_id=?",
                                                 (booking_id, inquiry[0]))
                                    except:
                                        pass
                                    
                                    conn.commit()
                                    st.success("🎉 Booking confirmed successfully!")
                                    st.balloons()
                                    st.session_state[f'show_booking_form_{inquiry[0]}'] = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error creating booking: {e}")
                                finally:
                                    conn.close()
                
                else:
                    st.success("✅ Already converted to booking")
                    
                    if booking_id_link:
                        st.info(f"📋 Booking ID: {booking_id_link[:8]}...")
                        if st.button("👁️ View Booking", key=f"view_booking_{inquiry[0]}", use_container_width=True):
                            st.info("Navigate to 'Bookings' page to view details")
                        
            

# ========== BOOKINGS PAGE (NEW!) ==========

def show_bookings_page():
    """Show and manage confirmed bookings"""
    st.markdown("## 💳 Confirmed Bookings")
    st.caption("Track confirmed bookings and payments")
    
    # Get agent bookings
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    c.execute("""SELECT b.booking_id, b.customer_name, b.customer_email, b.customer_phone,
                 p.package_name, b.travelers, b.total_amount, b.payment_status,
                 b.booking_status, b.booking_date, b.departure_date, b.payment_method
                 FROM bookings b
                 JOIN packages p ON b.package_id = p.package_id
                 WHERE b.agent_id=?
                 ORDER BY b.booking_date DESC""",
              (st.session_state.agent_id,))
    
    bookings = c.fetchall()
    conn.close()
    
    if not bookings:
        st.info("📭 No confirmed bookings yet. Confirm inquiries to create bookings!")
        return
    
    # Statistics
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("📦 Total Bookings", len(bookings))
    
    with stat_col2:
        paid_bookings = sum(1 for b in bookings if b[7] == 'Paid')
        st.metric("💰 Paid", paid_bookings)
    
    with stat_col3:
        total_revenue = sum(b[6] for b in bookings if b[7] == 'Paid')
        st.metric("💵 Total Revenue", f"${total_revenue:,.2f}")
    
    with stat_col4:
        pending_payments = sum(1 for b in bookings if b[7] == 'Pending')
        st.metric("⏳ Pending Payment", pending_payments)
    
    st.markdown("---")
    
    # Filter options
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        filter_payment = st.selectbox("Payment Status", 
            ["All", "Pending", "Paid", "Partial", "Refunded"])
    
    with filter_col2:
        filter_booking = st.selectbox("Booking Status",
            ["All", "Confirmed", "Completed", "Cancelled"])
    
    # Display bookings
    st.markdown("### 📋 All Bookings")
    
    for booking in bookings:
        # Apply filters
        if filter_payment != "All" and booking[7] != filter_payment:
            continue
        if filter_booking != "All" and booking[8] != filter_booking:
            continue
        
        # Status badges
        payment_status_colors = {
            "Paid": "🟢",
            "Pending": "🟡",
            "Partial": "🟠",
            "Refunded": "🔴"
        }
        
        booking_status_colors = {
            "Confirmed": "🟢",
            "Completed": "✅",
            "Cancelled": "🔴"
        }
        
        payment_icon = payment_status_colors.get(booking[7], "⚪")
        booking_icon = booking_status_colors.get(booking[8], "⚪")
        
        with st.expander(f"{booking_icon} {booking[1]} - {booking[4]} - ${booking[6]:,.2f}"):
            booking_col1, booking_col2 = st.columns([0.6, 0.4])
            
            with booking_col1:
                st.markdown("**📋 Booking Details:**")
                st.write(f"**Booking ID:** {booking[0][:8]}...")
                st.write(f"**Customer:** {booking[1]}")
                st.write(f"**Email:** {booking[2]}")
                st.write(f"**Phone:** {booking[3]}")
                st.write(f"**Package:** {booking[4]}")
                st.write(f"**Travelers:** {booking[5]}")
                st.write(f"**Total Amount:** ${booking[6]:,.2f}")
                st.write(f"**Departure Date:** {booking[10]}")
                st.write(f"**Booked On:** {booking[9]}")
                
                st.markdown("---")
                
                payment_col1, payment_col2 = st.columns(2)
                
                with payment_col1:
                    st.markdown(f"**Payment Status:** {payment_icon} {booking[7]}")
                
                with payment_col2:
                    st.markdown(f"**Booking Status:** {booking_icon} {booking[8]}")
                
                if booking[11]:
                    st.write(f"**Payment Method:** {booking[11]}")
            
            with booking_col2:
                st.markdown("**🔧 Actions:**")
                
                # Update payment status
                new_payment_status = st.selectbox(
                    "Update Payment",
                    ["Pending", "Partial", "Paid", "Refunded"],
                    key=f"payment_{booking[0]}"
                )
                
                if st.button("💰 Update Payment", key=f"update_pay_{booking[0]}", use_container_width=True):
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    
                    update_data = [new_payment_status]
                    query = "UPDATE bookings SET payment_status=?"
                    
                    if new_payment_status == "Paid":
                        query += ", payment_received_date=?"
                        update_data.append(datetime.now())
                    
                    query += " WHERE booking_id=?"
                    update_data.append(booking[0])
                    
                    c.execute(query, tuple(update_data))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Payment status updated!")
                    st.rerun()
                
                st.markdown("---")
                
                # Update booking status
                new_booking_status = st.selectbox(
                    "Update Booking",
                    ["Confirmed", "Completed", "Cancelled"],
                    key=f"booking_{booking[0]}"
                )
                
                if st.button("📦 Update Booking", key=f"update_book_{booking[0]}", use_container_width=True):
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("UPDATE bookings SET booking_status=? WHERE booking_id=?",
                             (new_booking_status, booking[0]))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ Booking status updated!")
                    st.rerun()
                
                st.markdown("---")
                
                # Add payment reference
                with st.form(f"payment_ref_{booking[0]}"):
                    payment_ref = st.text_input("Payment Reference/Transaction ID")
                    payment_method = st.selectbox("Payment Method",
                        ["Bank Transfer", "Credit Card", "PayPal", "Cash", "Other"])
                    
                    if st.form_submit_button("💳 Add Payment Details", use_container_width=True):
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        c.execute("""UPDATE bookings 
                                   SET payment_reference=?, payment_method=?
                                   WHERE booking_id=?""",
                                 (payment_ref, payment_method, booking[0]))
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ Payment details saved!")
                        st.rerun()

# ========== ANALYTICS PAGE ==========

def show_analytics_page():
    """Show analytics and performance metrics"""
    st.markdown("## 📈 Analytics & Performance")
    st.caption("Track your performance and earnings")
    
    conn = sqlite3.connect('umrah_pro.db')
    c = conn.cursor()
    
    # Date range filter
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        date_range = st.selectbox("Time Period", [
            "Last 7 Days",
            "Last 30 Days",
            "Last 3 Months",
            "Last 6 Months",
            "This Year",
            "All Time"
        ])
    
    # Calculate date filter
    from datetime import datetime, timedelta
    
    if date_range == "Last 7 Days":
        start_date = datetime.now() - timedelta(days=7)
    elif date_range == "Last 30 Days":
        start_date = datetime.now() - timedelta(days=30)
    elif date_range == "Last 3 Months":
        start_date = datetime.now() - timedelta(days=90)
    elif date_range == "Last 6 Months":
        start_date = datetime.now() - timedelta(days=180)
    elif date_range == "This Year":
        start_date = datetime(datetime.now().year, 1, 1)
    else:  # All Time
        start_date = datetime(2020, 1, 1)
    
    st.markdown("---")
    
    # ========== KEY METRICS ==========
    
    st.markdown("### 📊 Key Metrics")
    
    # Get statistics
    agent_id = st.session_state.agent_id
    
    # Total packages
    c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=?", (agent_id,))
    total_packages = c.fetchone()[0]
    
    # Active packages
    c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=? AND status='Active'", (agent_id,))
    active_packages = c.fetchone()[0]
    
    # Total views
    c.execute("SELECT SUM(views) FROM packages WHERE agent_id=?", (agent_id,))
    result = c.fetchone()[0]
    total_views = result if result else 0
    
    # Total inquiries
    c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=? AND inquiry_date >= ?",
              (agent_id, start_date))
    total_inquiries = c.fetchone()[0]
    
    # Pending inquiries
    c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=? AND status='Pending'",
              (agent_id,))
    pending_inquiries = c.fetchone()[0]
    
    # Total bookings
    try:
        c.execute("SELECT COUNT(*) FROM bookings WHERE agent_id=? AND booking_date >= ?",
                  (agent_id, start_date))
        total_bookings = c.fetchone()[0]
        
        # Paid bookings
        c.execute("SELECT COUNT(*) FROM bookings WHERE agent_id=? AND payment_status='Paid' AND booking_date >= ?",
                  (agent_id, start_date))
        paid_bookings = c.fetchone()[0]
        
        # Total revenue
        c.execute("SELECT SUM(total_amount) FROM bookings WHERE agent_id=? AND payment_status='Paid' AND booking_date >= ?",
                  (agent_id, start_date))
        result = c.fetchone()[0]
        total_revenue = result if result else 0
        
        # Total commission
        c.execute("SELECT SUM(commission_amount) FROM bookings WHERE agent_id=? AND payment_status='Paid' AND booking_date >= ?",
                  (agent_id, start_date))
        result = c.fetchone()[0]
        total_commission = result if result else 0
        
        bookings_exist = True
    except:
        total_bookings = 0
        paid_bookings = 0
        total_revenue = 0
        total_commission = 0
        bookings_exist = False
    
    # Display metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("📦 Active Packages", active_packages, delta=f"{total_packages} total")
    
    with metric_col2:
        st.metric("👁️ Total Views", f"{total_views:,}")
    
    with metric_col3:
        st.metric("📧 Inquiries", total_inquiries, delta=f"{pending_inquiries} pending")
    
    with metric_col4:
        if bookings_exist:
            conversion_rate = (total_bookings / total_inquiries * 100) if total_inquiries > 0 else 0
            st.metric("✅ Bookings", total_bookings, delta=f"{conversion_rate:.1f}% conversion")
        else:
            st.metric("✅ Bookings", "N/A", delta="Setup needed")
    
    st.markdown("---")
    
    # ========== REVENUE METRICS ==========
    
    if bookings_exist and total_bookings > 0:
        st.markdown("### 💰 Revenue & Earnings")
        
        revenue_col1, revenue_col2, revenue_col3, revenue_col4 = st.columns(4)
        
        with revenue_col1:
            st.metric("💵 Total Revenue", f"${total_revenue:,.2f}")
        
        with revenue_col2:
            st.metric("💰 Your Commission", f"${total_commission:,.2f}")
        
        with revenue_col3:
            st.metric("💳 Paid Bookings", paid_bookings, delta=f"{total_bookings} total")
        
        with revenue_col4:
            avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
            st.metric("📊 Avg Booking", f"${avg_booking_value:,.2f}")
        
        st.markdown("---")
    
    # ========== PACKAGE PERFORMANCE ==========
    
    st.markdown("### 🏆 Top Performing Packages")
    
    c.execute("""SELECT package_name, views, inquiries, 
                 CASE WHEN views > 0 THEN ROUND(inquiries * 100.0 / views, 2) ELSE 0 END as conversion_rate
                 FROM packages 
                 WHERE agent_id=?
                 ORDER BY inquiries DESC, views DESC
                 LIMIT 5""",
              (agent_id,))
    
    top_packages = c.fetchall()
    
    if top_packages:
        package_data = []
        for pkg in top_packages:
            package_data.append({
                "Package": pkg[0],
                "Views": pkg[1],
                "Inquiries": pkg[2],
                "Conversion Rate": f"{pkg[3]}%"
            })
        
        df_packages = pd.DataFrame(package_data)
        st.dataframe(df_packages, use_container_width=True, hide_index=True)
    else:
        st.info("No packages yet. Create your first package to see analytics!")
    
    st.markdown("---")
    
    # ========== INQUIRY TRENDS ==========
    
    st.markdown("### 📈 Inquiry Trends")
    
    # Get inquiries by status
    c.execute("""SELECT status, COUNT(*) 
                 FROM package_inquiries 
                 WHERE agent_id=? AND inquiry_date >= ?
                 GROUP BY status""",
              (agent_id, start_date))
    
    inquiry_stats = c.fetchall()
    
    if inquiry_stats:
        inquiry_col1, inquiry_col2 = st.columns(2)
        
        with inquiry_col1:
            st.markdown("#### Inquiries by Status")
            for status, count in inquiry_stats:
                status_colors = {
                    'Pending': '🟡',
                    'Contacted': '🔵',
                    'Converted': '🟢',
                    'Rejected': '🔴'
                }
                icon = status_colors.get(status, '⚪')
                st.write(f"{icon} **{status}:** {count}")
        
        with inquiry_col2:
            if bookings_exist:
                st.markdown("#### Conversion Funnel")
                
                funnel_data = {
                    "Stage": ["Views", "Inquiries", "Bookings", "Paid"],
                    "Count": [total_views, total_inquiries, total_bookings, paid_bookings]
                }
                
                for i, (stage, count) in enumerate(zip(funnel_data["Stage"], funnel_data["Count"])):
                    if i > 0:
                        prev_count = funnel_data["Count"][i-1]
                        percentage = (count / prev_count * 100) if prev_count > 0 else 0
                        st.write(f"**{stage}:** {count:,} ({percentage:.1f}%)")
                    else:
                        st.write(f"**{stage}:** {count:,}")
    else:
        st.info("No inquiry data yet for this period.")
    
    st.markdown("---")
    
    # ========== MONTHLY PERFORMANCE ==========
    
    st.markdown("### 📅 Monthly Performance")
    
    # Get inquiries per month
    c.execute("""SELECT strftime('%Y-%m', inquiry_date) as month, COUNT(*) as count
                 FROM package_inquiries
                 WHERE agent_id=? AND inquiry_date >= ?
                 GROUP BY month
                 ORDER BY month DESC
                 LIMIT 6""",
              (agent_id, start_date))
    
    monthly_inquiries = c.fetchall()
    
    if monthly_inquiries:
        # Reverse to show oldest to newest
        monthly_inquiries = list(reversed(monthly_inquiries))
        
        months = [row[0] for row in monthly_inquiries]
        inquiry_counts = [row[1] for row in monthly_inquiries]
        
        # Create a simple bar chart
        chart_data = pd.DataFrame({
            'Month': months,
            'Inquiries': inquiry_counts
        })
        
        st.bar_chart(chart_data.set_index('Month'))
        
        st.caption("📊 Inquiry volume by month")
    else:
        st.info("Not enough data yet for monthly trends.")
    
    st.markdown("---")
    
    # ========== PACKAGE CATEGORIES ==========
    
    st.markdown("### 🏷️ Package Distribution")
    
    c.execute("""SELECT category, COUNT(*) as count
                 FROM packages
                 WHERE agent_id=?
                 GROUP BY category""",
              (agent_id,))
    
    categories = c.fetchall()
    
    if categories:
        category_col1, category_col2 = st.columns(2)
        
        with category_col1:
            st.markdown("#### By Category")
            for category, count in categories:
                st.write(f"**{category}:** {count} package{'s' if count != 1 else ''}")
        
        with category_col2:
            # Get average price by category
            c.execute("""SELECT category, AVG(price) as avg_price
                        FROM packages
                        WHERE agent_id=?
                        GROUP BY category""",
                      (agent_id,))
            
            avg_prices = c.fetchall()
            
            if avg_prices:
                st.markdown("#### Avg Price by Category")
                for category, avg_price in avg_prices:
                    st.write(f"**{category}:** ${avg_price:,.2f}")
    else:
        st.info("Create packages to see distribution analytics.")
    
    st.markdown("---")
    
    # ========== RESPONSE TIME ==========
    
    st.markdown("### ⏱️ Performance Insights")
    
    insight_col1, insight_col2, insight_col3 = st.columns(3)
    
    with insight_col1:
        # Average travelers per inquiry
        c.execute("""SELECT AVG(travelers) 
                    FROM package_inquiries 
                    WHERE agent_id=? AND inquiry_date >= ?""",
                  (agent_id, start_date))
        result = c.fetchone()[0]
        avg_travelers = result if result else 0
        
        st.metric("👥 Avg Group Size", f"{avg_travelers:.1f} travelers")
    
    with insight_col2:
        # Most popular package
        c.execute("""SELECT p.package_name, COUNT(*) as count
                    FROM package_inquiries pi
                    JOIN packages p ON pi.package_id = p.package_id
                    WHERE pi.agent_id=? AND pi.inquiry_date >= ?
                    GROUP BY pi.package_id
                    ORDER BY count DESC
                    LIMIT 1""",
                  (agent_id, start_date))
        
        popular = c.fetchone()
        if popular:
            st.metric("🔥 Most Popular", popular[0][:20] + "...", delta=f"{popular[1]} inquiries")
        else:
            st.metric("🔥 Most Popular", "N/A")
    
    with insight_col3:
        # Inquiry to booking ratio
        if bookings_exist and total_inquiries > 0:
            inquiry_to_booking = (total_bookings / total_inquiries * 100)
            st.metric("🎯 Conversion Rate", f"{inquiry_to_booking:.1f}%")
        else:
            st.metric("🎯 Conversion Rate", "N/A")
    
    st.markdown("---")
    
    # ========== RECOMMENDATIONS ==========
    
    st.markdown("### 💡 Recommendations")
    
    recommendations = []
    
    # Check if packages need attention
    if active_packages == 0:
        recommendations.append("⚠️ **No active packages** - Create and activate packages to start receiving inquiries")
    
    if pending_inquiries > 5:
        recommendations.append(f"📧 **{pending_inquiries} pending inquiries** - Respond quickly to increase conversion rate")
    
    if total_views > 0 and total_inquiries == 0:
        recommendations.append("📈 **High views, no inquiries** - Consider updating package descriptions or pricing")
    
    if total_inquiries > 0 and total_views > 0:
        inquiry_rate = (total_inquiries / total_views * 100)
        if inquiry_rate < 5:
            recommendations.append(f"🎯 **Low inquiry rate ({inquiry_rate:.1f}%)** - Improve package details or add more photos")
    
    if bookings_exist and total_inquiries > 0 and total_bookings == 0:
        recommendations.append("💼 **No bookings yet** - Follow up with inquiries more actively")
    
    if not recommendations:
        recommendations.append("✅ **Great job!** Your performance metrics look good. Keep up the excellent work!")
    
    for rec in recommendations:
        if "⚠️" in rec or "📈" in rec or "🎯" in rec or "💼" in rec:
            st.warning(rec)
        else:
            st.success(rec)
    
    conn.close()

def show_settings_page():
    """Settings page"""
    
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2 = st.tabs(["👤 Profile", "🔐 Password"])
    
    with tab1:
        st.markdown("### 👤 Company Profile")
        
        # Get agent details
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('SELECT company_name, email, phone, website FROM agent_partners WHERE agent_id=?',
                  (st.session_state.agent_id,))
        
        agent_data = c.fetchone()
        conn.close()
        
        if agent_data:
            st.info(f"""
            **Company:** {agent_data[0]}
            
            **Email:** {agent_data[1]}
            
            **Phone:** {agent_data[2]}
            
            **Website:** {agent_data[3]}
            """)
        
        st.caption("To update your company details, please contact support@umrahpro.com")
    
    with tab2:
        st.markdown("### 🔐 Change Password")
        
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password"):
                if new_password != confirm_password:
                    st.error("Passwords don't match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    # Verify current password
                    result = verify_agent_login(st.session_state.agent_username, current_password)
                    
                    if result:
                        # Update password
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        
                        new_hash = hash_password(new_password)
                        c.execute('UPDATE agent_credentials SET password_hash=? WHERE username=?',
                                  (new_hash, st.session_state.agent_username))
                        
                        conn.commit()
                        conn.close()
                        
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error("❌ Current password is incorrect")

# ========== MAIN APP ==========

def main():
    """Main application"""
    
    # Check login
    if 'agent_logged_in' not in st.session_state or not st.session_state.agent_logged_in:
        agent_login_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 🏢 {st.session_state.agent_company}")
        st.caption(f"👤 {st.session_state.agent_username}")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        menu = st.sidebar.radio("Menu", [
        "📊 Dashboard",
        "📦 My Packages",
        "📧 Inquiries",
        "💳 Bookings",  # ADD THIS
        "📈 Analytics",
        "⚙️ Settings"
    ])
    
    if menu == "📊 Dashboard":
        show_dashboard_overview()
    elif menu == "📦 My Packages":
        show_packages_page()
    elif menu == "📧 Inquiries":
        show_inquiries_page()
    elif menu == "💳 Bookings":  # ADD THIS
        show_bookings_page()
    elif menu == "📈 Analytics":
        show_analytics_page()
    elif menu == "⚙️ Settings":
        show_settings_page()

if __name__ == "__main__":
    main()