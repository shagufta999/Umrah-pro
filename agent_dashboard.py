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

# ========== AUTHENTICATION ==========

def hash_password(password):
    """Hash password with error handling"""
    try:
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Convert to string in case it's not
        password_str = str(password)
        
        return hashlib.sha256(password_str.encode()).hexdigest()
        
    except (AttributeError, TypeError) as e:
        print(f"Error hashing password: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in hash_password: {e}")
        return None


def verify_agent_login(username, password):
    """Verify agent credentials with comprehensive error handling"""
    conn = None
    try:
        # Validate inputs
        if not username or not password:
            print("Username and password are required")
            return None
        
        # Clean inputs
        username = username.strip()
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            print("Failed to hash password")
            return None
        
        # Connect to database
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure tables exist
        c.execute('''CREATE TABLE IF NOT EXISTS agent_credentials
                     (credential_id TEXT PRIMARY KEY,
                      agent_id TEXT UNIQUE NOT NULL,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_login TIMESTAMP)''')
        
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
                      status TEXT DEFAULT 'Active',
                      joined_date TIMESTAMP,
                      onboarding_status TEXT,
                      notes TEXT)''')
        
        # Authenticate agent
        c.execute('''SELECT ac.agent_id, ap.company_name, ap.email, ap.status
                     FROM agent_credentials ac
                     JOIN agent_partners ap ON ac.agent_id = ap.agent_id
                     WHERE ac.username=? AND ac.password_hash=?''',
                  (username, password_hash))
        
        result = c.fetchone()
        
        if result:
            # Validate result structure
            if len(result) != 4:
                print("Invalid result structure from database")
                return None
            
            # Update last login
            try:
                c.execute('UPDATE agent_credentials SET last_login=? WHERE username=?',
                          (datetime.now(), username))
                conn.commit()
                print(f"✅ Agent '{username}' logged in successfully")
            except Exception as e:
                print(f"Warning: Failed to update last login: {e}")
                # Don't fail login just because last_login update failed
            
            # Return agent info as dict for clarity
            return {
                'agent_id': str(result[0]),
                'company_name': str(result[1]) if result[1] else 'Unknown',
                'email': str(result[2]) if result[2] else '',
                'status': str(result[3]) if result[3] else 'Inactive'
            }
        else:
            # Check if username exists but password is wrong
            c.execute('SELECT username FROM agent_credentials WHERE username=?', (username,))
            if c.fetchone():
                print(f"❌ Invalid password for agent '{username}'")
            else:
                print(f"❌ Agent username '{username}' not found")
            
            return None
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in verify_agent_login: {e}")
        return None
        
    except sqlite3.DatabaseError as e:
        print(f"❌ Database error in verify_agent_login: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error in verify_agent_login: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def create_agent_credentials(agent_id, username, password):
    """Create login credentials for an agent with error handling"""
    conn = None
    try:
        # Validate inputs
        if not agent_id or not username or not password:
            print("Agent ID, username, and password are required")
            return False, "All fields are required"
        
        if len(username.strip()) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Clean inputs
        username = username.strip()
        agent_id = str(agent_id).strip()
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            return False, "Failed to hash password"
        
        # Connect to database
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS agent_credentials
                     (credential_id TEXT PRIMARY KEY,
                      agent_id TEXT UNIQUE NOT NULL,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_login TIMESTAMP)''')
        
        # Check if agent exists in agent_partners
        c.execute('SELECT agent_id FROM agent_partners WHERE agent_id=?', (agent_id,))
        if not c.fetchone():
            return False, f"Agent ID '{agent_id}' not found in agent_partners"
        
        # Check if agent already has credentials
        c.execute('SELECT username FROM agent_credentials WHERE agent_id=?', (agent_id,))
        existing = c.fetchone()
        if existing:
            return False, f"Agent already has credentials (username: {existing[0]})"
        
        # Check if username is taken
        c.execute('SELECT agent_id FROM agent_credentials WHERE username=?', (username,))
        if c.fetchone():
            return False, f"Username '{username}' is already taken"
        
        # Create credentials
        credential_id = str(uuid.uuid4())
        
        c.execute('''INSERT INTO agent_credentials
                     (credential_id, agent_id, username, password_hash, created_at)
                     VALUES (?,?,?,?,?)''',
                  (credential_id, agent_id, username, password_hash, datetime.now()))
        
        conn.commit()
        
        # Verify creation
        c.execute('SELECT credential_id FROM agent_credentials WHERE credential_id=?', 
                 (credential_id,))
        if c.fetchone():
            print(f"✅ Credentials created for agent '{username}'")
            return True, "Credentials created successfully"
        else:
            return False, "Credential creation verification failed"
        
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if 'username' in error_msg:
            return False, f"Username '{username}' already exists"
        elif 'agent_id' in error_msg:
            return False, f"Agent ID already has credentials"
        else:
            return False, f"Database integrity error: {e}"
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in create_agent_credentials: {e}")
        return False, "Database error occurred"
        
    except Exception as e:
        print(f"❌ Unexpected error in create_agent_credentials: {e}")
        return False, f"Unexpected error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def get_agent_info(agent_id):
    """Get detailed agent information with error handling"""
    conn = None
    try:
        if not agent_id:
            return None
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        c.execute('''SELECT agent_id, agent_name, company_name, email, phone, 
                     website, status, joined_date, commission_rate
                     FROM agent_partners 
                     WHERE agent_id=?''', (agent_id,))
        
        result = c.fetchone()
        
        if result:
            return {
                'agent_id': str(result[0]),
                'agent_name': str(result[1]) if result[1] else '',
                'company_name': str(result[2]) if result[2] else 'Unknown',
                'email': str(result[3]) if result[3] else '',
                'phone': str(result[4]) if result[4] else '',
                'website': str(result[5]) if result[5] else '',
                'status': str(result[6]) if result[6] else 'Inactive',
                'joined_date': str(result[7]) if result[7] else '',
                'commission_rate': float(result[8]) if result[8] else 0.0
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting agent info: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def update_agent_password(agent_id, new_password):
    """Update agent password with error handling"""
    conn = None
    try:
        if not agent_id or not new_password:
            return False, "Agent ID and new password are required"
        
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Hash new password
        password_hash = hash_password(new_password)
        if not password_hash:
            return False, "Failed to hash password"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Update password
        c.execute('''UPDATE agent_credentials 
                     SET password_hash=? 
                     WHERE agent_id=?''',
                  (password_hash, agent_id))
        
        conn.commit()
        
        # Verify update
        if c.rowcount > 0:
            print(f"✅ Password updated for agent {agent_id}")
            return True, "Password updated successfully"
        else:
            return False, "Agent credentials not found"
        
    except sqlite3.OperationalError as e:
        print(f"Database error updating password: {e}")
        return False, "Database error occurred"
        
    except Exception as e:
        print(f"Unexpected error updating password: {e}")
        return False, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def agent_login_page():
    """Agent login interface with error handling"""
    
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
            
            username = st.text_input(
                "Username", 
                placeholder="agent@company.com",
                help="Enter your agent username or email"
            )
            
            password = st.text_input(
                "Password", 
                type="password", 
                placeholder="••••••••",
                help="Enter your password"
            )
            
            submit = st.form_submit_button(
                "Login", 
                type="primary", 
                use_container_width=True
            )
            
            if submit:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                    
                elif len(username.strip()) < 3:
                    st.error("❌ Username must be at least 3 characters")
                    
                elif len(password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                    
                else:
                    with st.spinner("🔄 Authenticating..."):
                        try:
                            result = verify_agent_login(username, password)
                            
                            if result:
                                # Check account status
                                if result['status'] == 'Active':
                                    # Set session state
                                    st.session_state.agent_logged_in = True
                                    st.session_state.agent_id = result['agent_id']
                                    st.session_state.agent_company = result['company_name']
                                    st.session_state.agent_email = result['email']
                                    st.session_state.agent_username = username
                                    
                                    st.success(f"✅ Welcome back, {result['company_name']}!")
                                    st.balloons()
                                    
                                    # Small delay for user to see success message
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                    
                                else:
                                    st.error("❌ Your account is not active. Please contact support.")
                                    st.info("📧 Email: support@umrahpro.com")
                                    
                            else:
                                st.error("❌ Invalid username or password")
                                st.caption("Please check your credentials and try again")
                                
                        except Exception as e:
                            st.error(f"❌ Login error: {str(e)}")
                            st.caption("Please try again or contact support")
        
        # Additional info sections
        st.markdown("---")
        
        # New agent info
        st.info("""
        📧 **New Agent?** 
        Contact support@umrahpro.com to get your login credentials
        """)
        
        # Forgot password
        with st.expander("🔑 Forgot Password?"):
            st.write("""
            To reset your password:
            1. Contact support@umrahpro.com
            2. Provide your agent ID or registered email
            3. We'll send you a temporary password
            """)
        
        # Debug panel (only in development)
        if st.secrets.get("DEBUG_MODE", False):
            with st.expander("🔧 Debug Panel"):
                if st.button("Check Database Connection"):
                    try:
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        
                        c.execute("SELECT COUNT(*) FROM agent_credentials")
                        cred_count = c.fetchone()[0]
                        
                        c.execute("SELECT COUNT(*) FROM agent_partners")
                        agent_count = c.fetchone()[0]
                        
                        conn.close()
                        
                        st.success(f"✅ Database connected")
                        st.write(f"Agents: {agent_count}")
                        st.write(f"Credentials: {cred_count}")
                        
                    except Exception as e:
                        st.error(f"❌ Database error: {e}")

# ========== HELPER FUNCTION: Create Test Agent Credentials ==========

def create_test_agent_account():
    """Create a test agent account for development/testing"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Create test agent partner if doesn't exist
        test_agent_id = 'test-agent-001'
        
        c.execute('SELECT agent_id FROM agent_partners WHERE agent_id=?', (test_agent_id,))
        if not c.fetchone():
            c.execute('''INSERT INTO agent_partners 
                         (agent_id, agent_name, company_name, email, phone, status, joined_date)
                         VALUES (?,?,?,?,?,?,?)''',
                      (test_agent_id, 'Test Agent', 'Test Travel Co.', 
                       'test@agent.com', '+1234567890', 'Active', datetime.now()))
            
            print("✅ Test agent partner created")
        
        # Create credentials
        success, message = create_agent_credentials(
            test_agent_id, 
            'testagent', 
            'test123'
        )
        
        if success:
            print("✅ Test agent credentials created: testagent / test123")
            return True
        else:
            print(f"⚠️ {message}")
            return False
        
        conn.commit()
        
    except Exception as e:
        print(f"Error creating test account: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

# ========== DATABASE QUERIES ==========

def get_agent_packages(agent_id):
    """Get all packages for an agent with error handling"""
    conn = None
    try:
        if not agent_id:
            print("Agent ID is required")
            return []
        
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
                      status TEXT DEFAULT 'Active',
                      featured BOOLEAN DEFAULT 0,
                      views INTEGER DEFAULT 0,
                      inquiries INTEGER DEFAULT 0,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        
        c.execute('''SELECT package_id, package_name, duration_days, duration_nights,
                     price, category, departure_city, status, views, inquiries,
                     created_at, updated_at
                     FROM packages
                     WHERE agent_id=?
                     ORDER BY created_at DESC''',
                  (agent_id,))
        
        packages = []
        for row in c.fetchall():
            try:
                packages.append({
                    'id': str(row[0]),
                    'name': str(row[1]) if row[1] else 'Unnamed Package',
                    'duration_days': int(row[2]) if row[2] else 0,
                    'duration_nights': int(row[3]) if row[3] else 0,
                    'price': float(row[4]) if row[4] else 0.0,
                    'category': str(row[5]) if row[5] else 'Standard',
                    'departure_city': str(row[6]) if row[6] else 'Unknown',
                    'status': str(row[7]) if row[7] else 'Inactive',
                    'views': int(row[8]) if row[8] else 0,
                    'inquiries': int(row[9]) if row[9] else 0,
                    'created_at': str(row[10]) if row[10] else '',
                    'updated_at': str(row[11]) if row[11] else ''
                })
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error parsing package row: {e}")
                continue
        
        return packages
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_agent_packages: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error in get_agent_packages: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def get_package_details(package_id):
    """Get full details of a package with error handling"""
    conn = None
    try:
        if not package_id:
            print("Package ID is required")
            return None
        
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
                      status TEXT DEFAULT 'Active',
                      featured BOOLEAN DEFAULT 0,
                      views INTEGER DEFAULT 0,
                      inquiries INTEGER DEFAULT 0,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        
        c.execute('SELECT * FROM packages WHERE package_id=?', (package_id,))
        
        row = c.fetchone()
        
        if not row:
            print(f"Package {package_id} not found")
            return None
        
        # Validate row length
        if len(row) < 22:
            print(f"Invalid package data structure for {package_id}")
            return None
        
        package = {
            'id': str(row[0]),
            'agent_id': str(row[1]) if row[1] else '',
            'name': str(row[2]) if row[2] else 'Unnamed Package',
            'duration_days': int(row[3]) if row[3] else 0,
            'duration_nights': int(row[4]) if row[4] else 0,
            'price': float(row[5]) if row[5] else 0.0,
            'category': str(row[6]) if row[6] else 'Standard',
            'departure_city': str(row[7]) if row[7] else 'Unknown',
            'target_countries': str(row[8]) if row[8] else '',
            'departure_dates': str(row[9]) if row[9] else 'TBA',
            'makkah_hotel': str(row[10]) if row[10] else 'TBA',
            'makkah_hotel_rating': int(row[11]) if row[11] else 0,
            'makkah_distance': str(row[12]) if row[12] else 'N/A',
            'madinah_hotel': str(row[13]) if row[13] else 'TBA',
            'madinah_hotel_rating': int(row[14]) if row[14] else 0,
            'madinah_distance': str(row[15]) if row[15] else 'N/A',
            'inclusions': str(row[16]) if row[16] else '',
            'exclusions': str(row[17]) if row[17] else '',
            'group_size': str(row[18]) if row[18] else 'Flexible',
            'status': str(row[19]) if row[19] else 'Inactive',
            'featured': bool(row[20]) if row[20] is not None else False,
            'views': int(row[21]) if row[21] else 0,
            'inquiries': int(row[22]) if row[22] else 0
        }
        
        return package
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_package_details: {e}")
        return None
        
    except (ValueError, TypeError, IndexError) as e:
        print(f"Error parsing package details: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in get_package_details: {e}")
        return None
        
    finally:
        if conn:
            conn.close()


def add_package(agent_id, package_data):
    """Add new package with error handling"""
    conn = None
    try:
        # Validate inputs
        if not agent_id:
            return None, "Agent ID is required"
        
        if not package_data:
            return None, "Package data is required"
        
        required_fields = ['name', 'duration_days', 'duration_nights', 'price', 
                          'category', 'departure_city']
        
        for field in required_fields:
            if field not in package_data or not package_data[field]:
                return None, f"Missing required field: {field}"
        
        # Validate data types
        try:
            duration_days = int(package_data['duration_days'])
            duration_nights = int(package_data['duration_nights'])
            price = float(package_data['price'])
            
            if duration_days <= 0 or duration_nights <= 0:
                return None, "Duration must be positive"
            
            if price <= 0:
                return None, "Price must be positive"
                
        except (ValueError, TypeError):
            return None, "Invalid duration or price format"
        
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
                      status TEXT DEFAULT 'Active',
                      featured BOOLEAN DEFAULT 0,
                      views INTEGER DEFAULT 0,
                      inquiries INTEGER DEFAULT 0,
                      created_at TIMESTAMP,
                      updated_at TIMESTAMP)''')
        
        package_id = str(uuid.uuid4())
        
        c.execute('''INSERT INTO packages
                     (package_id, agent_id, package_name, duration_days, duration_nights,
                      price, category, departure_city, departure_dates,
                      makkah_hotel, makkah_hotel_rating, makkah_distance,
                      madinah_hotel, madinah_hotel_rating, madinah_distance,
                      inclusions, exclusions, group_size, status, created_at, updated_at)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (package_id, agent_id, 
                   str(package_data['name']),
                   int(package_data['duration_days']),
                   int(package_data['duration_nights']),
                   float(package_data['price']),
                   str(package_data['category']),
                   str(package_data['departure_city']),
                   str(package_data.get('departure_dates', 'TBA')),
                   str(package_data.get('makkah_hotel', 'TBA')),
                   int(package_data.get('makkah_rating', 0)),
                   str(package_data.get('makkah_distance', 'N/A')),
                   str(package_data.get('madinah_hotel', 'TBA')),
                   int(package_data.get('madinah_rating', 0)),
                   str(package_data.get('madinah_distance', 'N/A')),
                   str(package_data.get('inclusions', '')),
                   str(package_data.get('exclusions', '')),
                   str(package_data.get('group_size', 'Flexible')),
                   'Active',
                   datetime.now(),
                   datetime.now()))
        
        conn.commit()
        
        # Verify creation
        c.execute('SELECT package_id FROM packages WHERE package_id=?', (package_id,))
        if c.fetchone():
            print(f"✅ Package created: {package_id}")
            return package_id, "Package created successfully"
        else:
            return None, "Package creation verification failed"
        
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error in add_package: {e}")
        return None, "Package with this ID already exists"
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in add_package: {e}")
        return None, "Database error occurred"
        
    except (ValueError, TypeError) as e:
        print(f"Data validation error in add_package: {e}")
        return None, f"Invalid data format: {str(e)}"
        
    except Exception as e:
        print(f"Unexpected error in add_package: {e}")
        return None, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def update_package(package_id, package_data):
    """Update existing package with error handling"""
    conn = None
    try:
        # Validate inputs
        if not package_id:
            return False, "Package ID is required"
        
        if not package_data:
            return False, "Package data is required"
        
        # Validate numeric fields if provided
        if 'duration_days' in package_data:
            try:
                if int(package_data['duration_days']) <= 0:
                    return False, "Duration days must be positive"
            except (ValueError, TypeError):
                return False, "Invalid duration days format"
        
        if 'price' in package_data:
            try:
                if float(package_data['price']) <= 0:
                    return False, "Price must be positive"
            except (ValueError, TypeError):
                return False, "Invalid price format"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if package exists
        c.execute('SELECT package_id FROM packages WHERE package_id=?', (package_id,))
        if not c.fetchone():
            return False, f"Package {package_id} not found"
        
        c.execute('''UPDATE packages SET
                     package_name=?, duration_days=?, duration_nights=?, price=?,
                     category=?, departure_city=?, departure_dates=?,
                     makkah_hotel=?, makkah_hotel_rating=?, makkah_distance=?,
                     madinah_hotel=?, madinah_hotel_rating=?, madinah_distance=?,
                     inclusions=?, exclusions=?, group_size=?, updated_at=?
                     WHERE package_id=?''',
                  (str(package_data.get('name', '')),
                   int(package_data.get('duration_days', 0)),
                   int(package_data.get('duration_nights', 0)),
                   float(package_data.get('price', 0)),
                   str(package_data.get('category', 'Standard')),
                   str(package_data.get('departure_city', '')),
                   str(package_data.get('departure_dates', 'TBA')),
                   str(package_data.get('makkah_hotel', 'TBA')),
                   int(package_data.get('makkah_rating', 0)),
                   str(package_data.get('makkah_distance', 'N/A')),
                   str(package_data.get('madinah_hotel', 'TBA')),
                   int(package_data.get('madinah_rating', 0)),
                   str(package_data.get('madinah_distance', 'N/A')),
                   str(package_data.get('inclusions', '')),
                   str(package_data.get('exclusions', '')),
                   str(package_data.get('group_size', 'Flexible')),
                   datetime.now(),
                   package_id))
        
        conn.commit()
        
        if c.rowcount > 0:
            print(f"✅ Package {package_id} updated")
            return True, "Package updated successfully"
        else:
            return False, "No changes were made"
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in update_package: {e}")
        return False, "Database error occurred"
        
    except (ValueError, TypeError) as e:
        print(f"Data validation error in update_package: {e}")
        return False, f"Invalid data format: {str(e)}"
        
    except Exception as e:
        print(f"Unexpected error in update_package: {e}")
        return False, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def update_package_status(package_id, status):
    """Update package status with error handling"""
    conn = None
    try:
        if not package_id:
            return False, "Package ID is required"
        
        if not status:
            return False, "Status is required"
        
        # Validate status
        valid_statuses = ['Active', 'Inactive', 'Pending', 'Archived']
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if package exists
        c.execute('SELECT package_id FROM packages WHERE package_id=?', (package_id,))
        if not c.fetchone():
            return False, f"Package {package_id} not found"
        
        c.execute('UPDATE packages SET status=?, updated_at=? WHERE package_id=?',
                  (status, datetime.now(), package_id))
        
        conn.commit()
        
        if c.rowcount > 0:
            print(f"✅ Package {package_id} status updated to {status}")
            return True, f"Status updated to {status}"
        else:
            return False, "No changes were made"
        
    except sqlite3.OperationalError as e:
        print(f"Database error in update_package_status: {e}")
        return False, "Database error occurred"
        
    except Exception as e:
        print(f"Unexpected error in update_package_status: {e}")
        return False, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def delete_package(package_id):
    """Delete package with error handling"""
    conn = None
    try:
        if not package_id:
            return False, "Package ID is required"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if package exists
        c.execute('SELECT package_name FROM packages WHERE package_id=?', (package_id,))
        package = c.fetchone()
        
        if not package:
            return False, f"Package {package_id} not found"
        
        package_name = package[0]
        
        # Delete package
        c.execute('DELETE FROM packages WHERE package_id=?', (package_id,))
        
        conn.commit()
        
        if c.rowcount > 0:
            print(f"✅ Package '{package_name}' deleted")
            return True, f"Package '{package_name}' deleted successfully"
        else:
            return False, "Deletion failed"
        
    except sqlite3.OperationalError as e:
        print(f"Database error in delete_package: {e}")
        return False, "Database error occurred"
        
    except Exception as e:
        print(f"Unexpected error in delete_package: {e}")
        return False, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()


def get_agent_inquiries(agent_id):
    """Get package inquiries for agent with error handling"""
    conn = None
    try:
        if not agent_id:
            print("Agent ID is required")
            return []
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure tables exist
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
                      status TEXT DEFAULT 'Pending',
                      inquiry_date TIMESTAMP)''')
        
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
            try:
                inquiries.append({
                    'id': str(row[0]),
                    'customer_name': str(row[1]) if row[1] else 'Unknown',
                    'customer_email': str(row[2]) if row[2] else '',
                    'customer_phone': str(row[3]) if row[3] else '',
                    'travelers': int(row[4]) if row[4] else 1,
                    'preferred_date': str(row[5]) if row[5] else 'Flexible',
                    'message': str(row[6]) if row[6] else '',
                    'status': str(row[7]) if row[7] else 'Pending',
                    'inquiry_date': str(row[8]) if row[8] else '',
                    'package_name': str(row[9]) if row[9] else 'Unknown Package'
                })
            except (ValueError, TypeError, IndexError) as e:
                print(f"Error parsing inquiry row: {e}")
                continue
        
        return inquiries
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_agent_inquiries: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error in get_agent_inquiries: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def get_agent_stats(agent_id):
    """Get agent statistics with error handling"""
    
    # Default stats structure
    default_stats = {
        'total_packages': 0,
        'active_packages': 0,
        'total_views': 0,
        'total_inquiries': 0,
        'pending_inquiries': 0
    }
    
    conn = None
    try:
        if not agent_id:
            print("Agent ID is required")
            return default_stats
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        stats = {}
        
        # Total packages
        try:
            c.execute('SELECT COUNT(*) FROM packages WHERE agent_id=?', (agent_id,))
            result = c.fetchone()
            stats['total_packages'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting total_packages: {e}")
            stats['total_packages'] = 0
        
        # Active packages
        try:
            c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=? AND status='Active'", 
                     (agent_id,))
            result = c.fetchone()
            stats['active_packages'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting active_packages: {e}")
            stats['active_packages'] = 0
        
        # Total views
        try:
            c.execute('SELECT SUM(views) FROM packages WHERE agent_id=?', (agent_id,))
            result = c.fetchone()
            stats['total_views'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting total_views: {e}")
            stats['total_views'] = 0
        
        # Total inquiries
        try:
            c.execute('SELECT COUNT(*) FROM package_inquiries WHERE agent_id=?', 
                     (agent_id,))
            result = c.fetchone()
            stats['total_inquiries'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting total_inquiries: {e}")
            stats['total_inquiries'] = 0
        
        # Pending inquiries
        try:
            c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=? AND status='Pending'", 
                     (agent_id,))
            result = c.fetchone()
            stats['pending_inquiries'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting pending_inquiries: {e}")
            stats['pending_inquiries'] = 0
        
        return stats
        
    except sqlite3.OperationalError as e:
        print(f"Database operational error in get_agent_stats: {e}")
        return default_stats
        
    except Exception as e:
        print(f"Unexpected error in get_agent_stats: {e}")
        return default_stats
        
    finally:
        if conn:
            conn.close()


def update_inquiry_status(inquiry_id, status):
    """Update inquiry status with error handling"""
    conn = None
    try:
        if not inquiry_id:
            return False, "Inquiry ID is required"
        
        if not status:
            return False, "Status is required"
        
        # Validate status
        valid_statuses = ['Pending', 'Contacted', 'Converted', 'Rejected', 'Closed']
        if status not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if inquiry exists
        c.execute('SELECT inquiry_id FROM package_inquiries WHERE inquiry_id=?', 
                 (inquiry_id,))
        if not c.fetchone():
            return False, f"Inquiry {inquiry_id} not found"
        
        c.execute('UPDATE package_inquiries SET status=? WHERE inquiry_id=?',
                  (status, inquiry_id))
        
        conn.commit()
        
        if c.rowcount > 0:
            print(f"✅ Inquiry {inquiry_id} status updated to {status}")
            return True, f"Inquiry status updated to {status}"
        else:
            return False, "No changes were made"
        
    except sqlite3.OperationalError as e:
        print(f"Database error in update_inquiry_status: {e}")
        return False, "Database error occurred"
        
    except Exception as e:
        print(f"Unexpected error in update_inquiry_status: {e}")
        return False, f"Error: {str(e)}"
        
    finally:
        if conn:
            conn.close()

# ========== DASHBOARD PAGES ==========

def show_dashboard_overview():
    """Dashboard overview page with error handling"""
    
    st.markdown("## 📊 Dashboard Overview")
    
    try:
        # Get stats with error handling
        stats = get_agent_stats(st.session_state.agent_id)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Total Packages", stats.get('total_packages', 0))
        
        with col2:
            st.metric("✅ Active Packages", stats.get('active_packages', 0))
        
        with col3:
            st.metric("👁️ Total Views", stats.get('total_views', 0))
        
        with col4:
            pending = stats.get('pending_inquiries', 0)
            total = stats.get('total_inquiries', 0)
            st.metric("📧 Inquiries", total, f"{pending} pending")
        
        st.markdown("---")
        
        # Recent activity
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            st.markdown("### 📦 Your Packages")
            
            try:
                packages = get_agent_packages(st.session_state.agent_id)[:5]
                
                if packages:
                    for pkg in packages:
                        try:
                            status_color = "🟢" if pkg.get('status') == 'Active' else "🔴"
                            
                            st.markdown(f"""
                            {status_color} **{pkg.get('name', 'Unknown')}** - ${pkg.get('price', 0):,.0f}
                            
                            👁️ {pkg.get('views', 0)} views • 📧 {pkg.get('inquiries', 0)} inquiries
                            """)
                            st.markdown("---")
                        except Exception as e:
                            print(f"Error displaying package: {e}")
                            continue
                else:
                    st.info("No packages yet. Create your first package!")
                    
            except Exception as e:
                st.error(f"Error loading packages: {e}")
                st.info("Try refreshing the page")
        
        with col_act2:
            st.markdown("### 📧 Recent Inquiries")
            
            try:
                inquiries = get_agent_inquiries(st.session_state.agent_id)[:5]
                
                if inquiries:
                    for inq in inquiries:
                        try:
                            status_icon = "⏳" if inq.get('status') == 'Pending' else "✅"
                            inquiry_date = inq.get('inquiry_date', '')[:10] if inq.get('inquiry_date') else 'N/A'
                            
                            st.markdown(f"""
                            {status_icon} **{inq.get('customer_name', 'Unknown')}** - {inq.get('package_name', 'Unknown Package')}
                            
                            📅 {inquiry_date} • {inq.get('travelers', 0)} travelers
                            """)
                            st.markdown("---")
                        except Exception as e:
                            print(f"Error displaying inquiry: {e}")
                            continue
                else:
                    st.info("No inquiries yet")
                    
            except Exception as e:
                st.error(f"Error loading inquiries: {e}")
                st.info("Try refreshing the page")
    
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {e}")
        st.info("Please try refreshing the page or contact support if the problem persists")


def show_packages_page():
    """Packages management page with error handling"""
    
    st.markdown("## 📦 Package Management")
    
    tab1, tab2 = st.tabs(["📋 My Packages", "➕ Add New Package"])
    
    # ========== TAB 1: MY PACKAGES ==========
    with tab1:
        try:
            packages = get_agent_packages(st.session_state.agent_id)
            
            st.markdown(f"### Your Packages ({len(packages)})")
            
            if not packages:
                st.info("No packages yet. Create your first package!")
            else:
                for pkg in packages:
                    try:
                        with st.expander(f"{pkg.get('name', 'Unknown')} - ${pkg.get('price', 0):,.0f} ({pkg.get('status', 'Unknown')})"):
                            # Get full details
                            details = get_package_details(pkg['id'])
                            
                            if not details:
                                st.error("⚠️ Could not load package details")
                                continue
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Duration:** {details.get('duration_days', 0)} Days / {details.get('duration_nights', 0)} Nights")
                                st.write(f"**Category:** {details.get('category', 'N/A')}")
                                st.write(f"**Departure City:** {details.get('departure_city', 'N/A')}")
                                st.write(f"**Group Size:** {details.get('group_size', 'N/A')}")
                            
                            with col2:
                                st.write(f"**Makkah Hotel:** {details.get('makkah_hotel', 'N/A')} ({details.get('makkah_hotel_rating', 0)}⭐)")
                                st.write(f"**Madinah Hotel:** {details.get('madinah_hotel', 'N/A')} ({details.get('madinah_hotel_rating', 0)}⭐)")
                                st.write(f"**Views:** {pkg.get('views', 0)}")
                                st.write(f"**Inquiries:** {pkg.get('inquiries', 0)}")
                            
                            st.markdown("**Inclusions:**")
                            st.text(details.get('inclusions', 'N/A'))
                            
                            st.markdown("---")
                            
                            # Actions
                            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                            
                            with btn_col1:
                                if st.button("✏️ Edit", key=f"edit_{pkg['id']}"):
                                    st.session_state.editing_package = pkg['id']
                                    st.rerun()
                            
                            with btn_col2:
                                if pkg.get('status') == 'Active':
                                    if st.button("⏸️ Pause", key=f"pause_{pkg['id']}"):
                                        try:
                                            success, message = update_package_status(pkg['id'], 'Inactive')
                                            if success:
                                                st.success("Package paused")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed: {message}")
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                else:
                                    if st.button("▶️ Activate", key=f"activate_{pkg['id']}"):
                                        try:
                                            success, message = update_package_status(pkg['id'], 'Active')
                                            if success:
                                                st.success("Package activated")
                                                st.rerun()
                                            else:
                                                st.error(f"Failed: {message}")
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                            
                            with btn_col3:
                                if st.button("📊 Stats", key=f"stats_{pkg['id']}"):
                                    st.info(f"Views: {pkg.get('views', 0)} | Inquiries: {pkg.get('inquiries', 0)}")
                            
                            with btn_col4:
                                if st.button("🗑️ Delete", key=f"delete_{pkg['id']}"):
                                    try:
                                        success, message = delete_package(pkg['id'])
                                        if success:
                                            st.success(message)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {message}")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                    
                    except Exception as e:
                        st.error(f"Error displaying package: {e}")
                        continue
        
        except Exception as e:
            st.error(f"❌ Error loading packages: {e}")
            st.info("Try refreshing the page")
    
    # ========== TAB 2: ADD NEW PACKAGE ==========
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
            
            if submit:
                # Validate required fields
                if not package_name or not departure_city or not makkah_hotel or not madinah_hotel:
                    st.error("❌ Please fill in all required fields (*)")
                elif duration_days <= 0 or duration_nights <= 0:
                    st.error("❌ Duration must be positive")
                elif price <= 0:
                    st.error("❌ Price must be positive")
                else:
                    try:
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
                            'makkah_distance': makkah_distance or 'N/A',
                            'madinah_hotel': madinah_hotel,
                            'madinah_rating': madinah_rating,
                            'madinah_distance': madinah_distance or 'N/A',
                            'inclusions': inclusions,
                            'exclusions': exclusions or 'None',
                            'group_size': group_size or 'Open'
                        }
                        
                        package_id, message = add_package(st.session_state.agent_id, package_data)
                        
                        if package_id:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.info("💡 Your package is now live and visible to customers on the main app!")
                            
                            # Small delay to show success
                            import time
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to create package: {message}")
                    
                    except Exception as e:
                        st.error(f"❌ Error creating package: {e}")
                        st.caption("Please check your inputs and try again")


def show_inquiries_page():
    """Show and manage package inquiries with error handling"""
    
    st.markdown("## 📧 Package Inquiries")
    st.caption("Manage customer inquiries for your packages")
    
    conn = None
    try:
        # Get inquiries
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure tables exist
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
                      status TEXT DEFAULT 'Pending',
                      inquiry_date TIMESTAMP,
                      booking_confirmed BOOLEAN DEFAULT 0,
                      converted_to_booking_id TEXT)''')
        
        c.execute("""SELECT i.inquiry_id, i.package_id, i.customer_name, i.customer_email,
                     i.customer_phone, i.travelers, i.preferred_date, i.status, i.inquiry_date,
                     i.message, p.package_name, p.price
                     FROM package_inquiries i
                     JOIN packages p ON i.package_id = p.package_id
                     WHERE i.agent_id=?
                     ORDER BY i.inquiry_date DESC""",
                  (st.session_state.agent_id,))
        
        inquiries = c.fetchall()
        
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
        for inquiry in inquiries:
            try:
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
                        st.write(f"**Inquiry Date:** {inquiry[8][:10] if inquiry[8] else 'N/A'}")
                        
                        if inquiry[9]:
                            st.markdown("**💬 Message:**")
                            st.info(inquiry[9])
                    
                    with inq_col2:
                        st.markdown("**🔧 Actions:**")
                        
                        # Update status
                        status_options = ["Pending", "Contacted", "Converted", "Rejected"]
                        current_status_index = status_options.index(inquiry[7]) if inquiry[7] in status_options else 0
                        
                        new_status = st.selectbox(
                            "Change Status",
                            status_options,
                            index=current_status_index,
                            key=f"status_{inquiry[0]}"
                        )
                        
                        if st.button("💾 Update Status", key=f"update_{inquiry[0]}", use_container_width=True):
                            try:
                                update_conn = sqlite3.connect('umrah_pro.db')
                                update_c = update_conn.cursor()
                                update_c.execute("UPDATE package_inquiries SET status=? WHERE inquiry_id=?",
                                               (new_status, inquiry[0]))
                                update_conn.commit()
                                update_conn.close()
                                st.success("✅ Status updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error updating status: {e}")
                        
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
                        
                        # Check if already converted
                        try:
                            check_conn = sqlite3.connect('umrah_pro.db')
                            check_c = check_conn.cursor()
                            check_c.execute("SELECT booking_confirmed, converted_to_booking_id FROM package_inquiries WHERE inquiry_id=?", 
                                          (inquiry[0],))
                            booking_check = check_c.fetchone()
                            is_converted = booking_check and booking_check[0] == 1
                            booking_id_link = booking_check[1] if booking_check and len(booking_check) > 1 else None
                            check_conn.close()
                        except:
                            is_converted = False
                            booking_id_link = None
                        
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
                                        try:
                                            booking_id = str(uuid.uuid4())
                                            commission_amount = total_amount * (commission_rate / 100)
                                            
                                            booking_conn = sqlite3.connect('umrah_pro.db')
                                            booking_c = booking_conn.cursor()
                                            
                                            # Ensure bookings table exists
                                            booking_c.execute('''CREATE TABLE IF NOT EXISTS bookings
                                                              (booking_id TEXT PRIMARY KEY,
                                                               inquiry_id TEXT,
                                                               package_id TEXT,
                                                               agent_id TEXT,
                                                               user_id TEXT,
                                                               customer_name TEXT,
                                                               customer_email TEXT,
                                                               customer_phone TEXT,
                                                               travelers INTEGER,
                                                               package_price REAL,
                                                               total_amount REAL,
                                                               commission_amount REAL,
                                                               payment_status TEXT,
                                                               payment_method TEXT,
                                                               payment_reference TEXT,
                                                               booking_status TEXT,
                                                               confirmed_by_agent_date TIMESTAMP,
                                                               payment_date TIMESTAMP,
                                                               booking_date TIMESTAMP,
                                                               departure_date TEXT,
                                                               return_date TEXT,
                                                               special_requests TEXT,
                                                               notes TEXT)''')
                                            
                                            # Create booking
                                            booking_c.execute("""INSERT INTO bookings VALUES 
                                                              (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                                            (booking_id,
                                                             inquiry[0],  # inquiry_id
                                                             inquiry[1],  # package_id
                                                             st.session_state.agent_id,
                                                             None,  # user_id
                                                             inquiry[2],  # customer_name
                                                             inquiry[3],  # customer_email
                                                             inquiry[4],  # customer_phone
                                                             inquiry[5],  # travelers
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
                                            booking_c.execute("""UPDATE package_inquiries 
                                                              SET status='Converted',
                                                                  booking_confirmed=1,
                                                                  converted_to_booking_id=?
                                                              WHERE inquiry_id=?""",
                                                            (booking_id, inquiry[0]))
                                            
                                            booking_conn.commit()
                                            booking_conn.close()
                                            
                                            st.success("🎉 Booking confirmed successfully!")
                                            st.balloons()
                                            st.session_state[f'show_booking_form_{inquiry[0]}'] = False
                                            
                                            import time
                                            time.sleep(2)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Error creating booking: {e}")
                                            print(f"Booking creation error: {e}")
                        
                        else:
                            st.success("✅ Already converted to booking")
                            
                            if booking_id_link:
                                st.info(f"📋 Booking ID: {booking_id_link[:8]}...")
                                if st.button("👁️ View Booking", key=f"view_booking_{inquiry[0]}", use_container_width=True):
                                    st.info("Navigate to 'Bookings' page to view details")
            
            except Exception as e:
                st.error(f"Error displaying inquiry: {e}")
                print(f"Inquiry display error: {e}")
                continue
    
    except sqlite3.OperationalError as e:
        st.error(f"❌ Database error: {e}")
        st.info("Try refreshing the page or contact support")
    
    except Exception as e:
        st.error(f"❌ Error loading inquiries: {e}")
        st.info("Please try refreshing the page")
    
    finally:
        if conn:
            conn.close()
                        
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