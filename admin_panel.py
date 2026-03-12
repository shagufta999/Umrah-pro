"""
UMRAH PRO - ADMIN PANEL
Complete admin interface with data cleanup tools
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import hashlib
import uuid
import pandas as pd
import json

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Umrah Pro - Admin Panel",
    page_icon="favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ADMIN DATABASE FUNCTIONS ==========

def init_admin_db():
    """Initialize admin database with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        print("🔧 Initializing admin database...")
        
        # Admin credentials table
        c.execute('''CREATE TABLE IF NOT EXISTS admin_credentials
                     (admin_id TEXT PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      role TEXT DEFAULT 'admin',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        conn.commit()
        print("✅ Admin database initialized successfully")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in init_admin_db: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error in init_admin_db: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def hash_password(pwd):
    """Hash password using SHA256 with error handling"""
    try:
        if not pwd:
            raise ValueError("Password cannot be empty")
        
        return hashlib.sha256(str(pwd).encode()).hexdigest()
        
    except (AttributeError, TypeError) as e:
        print(f"Error hashing password: {e}")
        return None
        
    except Exception as e:
        print(f"Unexpected error in hash_password: {e}")
        return None


def create_admin(username, password, role='admin'):
    """Create admin account with error handling"""
    conn = None
    try:
        # Validate inputs
        if not username or len(username.strip()) < 3:
            print("Username must be at least 3 characters")
            return False
        
        if not password or len(password) < 6:
            print("Password must be at least 6 characters")
            return False
        
        if role not in ['admin', 'super_admin', 'moderator']:
            print(f"Invalid role: {role}. Using 'admin' instead.")
            role = 'admin'
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            print("Failed to hash password")
            return False
        
        # Create admin
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS admin_credentials
                     (admin_id TEXT PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      role TEXT DEFAULT 'admin',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        admin_id = str(uuid.uuid4())
        
        c.execute('''INSERT INTO admin_credentials 
                     (admin_id, username, password_hash, role, created_at) 
                     VALUES (?,?,?,?,?)''',
                  (admin_id, username.strip(), password_hash, role, datetime.now()))
        
        conn.commit()
        
        # Verify creation
        c.execute('SELECT admin_id FROM admin_credentials WHERE admin_id=?', (admin_id,))
        if c.fetchone():
            print(f"✅ Admin '{username}' created successfully")
            return True
        else:
            print("❌ Admin creation verification failed")
            return False
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Admin username '{username}' already exists: {e}")
        return False
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in create_admin: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error in create_admin: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def auth_admin(username, password):
    """Authenticate admin with error handling"""
    conn = None
    try:
        # Validate inputs
        if not username or not password:
            print("Username and password are required")
            return None
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            print("Failed to hash password")
            return None
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS admin_credentials
                     (admin_id TEXT PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      role TEXT DEFAULT 'admin',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Authenticate
        c.execute('''SELECT admin_id, role, username 
                     FROM admin_credentials 
                     WHERE username=? AND password_hash=?''',
                  (username.strip(), password_hash))
        
        result = c.fetchone()
        
        if result:
            print(f"✅ Admin '{username}' authenticated successfully")
            return {
                'admin_id': result[0],
                'role': result[1],
                'username': result[2]
            }
        else:
            # Check if username exists
            c.execute('SELECT username FROM admin_credentials WHERE username=?', 
                     (username.strip(),))
            if c.fetchone():
                print(f"❌ Invalid password for admin '{username}'")
            else:
                print(f"❌ Admin username '{username}' not found")
            return None
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in auth_admin: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error in auth_admin: {e}")
        return None
        
    finally:
        if conn:
            conn.close()

# ========== COMPLETE DATABASE INITIALIZATION ==========

def init_all_tables():
    """Initialize ALL database tables for the entire app"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        print("🔧 Initializing all database tables...")
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id TEXT PRIMARY KEY, 
                      username TEXT UNIQUE NOT NULL, 
                      password_hash TEXT NOT NULL, 
                      email TEXT NOT NULL, 
                      phone TEXT, 
                      country TEXT DEFAULT 'United States', 
                      subscription TEXT DEFAULT 'free',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Agent partners
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
        
        # Packages
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
        
        # Package inquiries
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
        
        # Bookings
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
                      payment_status TEXT DEFAULT 'Pending',
                      booking_status TEXT DEFAULT 'Confirmed',
                      booking_date TIMESTAMP)''')

        # Family members table
        c.execute('''CREATE TABLE IF NOT EXISTS family_members
                     (id TEXT PRIMARY KEY, 
                      user_id TEXT NOT NULL, 
                      name TEXT NOT NULL, 
                      relationship TEXT,
                      phone TEXT, 
                      latitude REAL, 
                      longitude REAL, 
                      location_name TEXT,
                      status TEXT DEFAULT 'Not tracking', 
                      battery INTEGER DEFAULT 100, 
                      last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Agent credentials table (for agent login)
        c.execute('''CREATE TABLE IF NOT EXISTS agent_credentials
                     (credential_id TEXT PRIMARY KEY,
                      agent_id TEXT UNIQUE NOT NULL,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      last_login TIMESTAMP,
                      FOREIGN KEY (agent_id) REFERENCES agent_partners(agent_id))''')
        
        conn.commit()
        print("✅ All database tables initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

# Initialize all tables immediately
init_all_tables()

def get_dashboard_stats():
    """Get dashboard statistics with comprehensive error handling"""
    conn = None
    
    # Default stats structure
    default_stats = {
        'total_users': 0,
        'premium_users': 0,
        'total_agents': 0,
        'active_agents': 0,
        'total_packages': 0,
        'active_packages': 0,
        'total_bookings': 0,
        'paid_bookings': 0,
        'total_revenue': 0.0,
        'total_inquiries': 0,
        'pending_inquiries': 0,
        'new_users_week': 0,
        'new_packages_week': 0,
        'new_inquiries_week': 0
    }
    
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        stats = {}
        
        # ========== USERS STATS ==========
        try:
            c.execute("SELECT COUNT(*) FROM users")
            result = c.fetchone()
            stats['total_users'] = int(result[0]) if result and result[0] else 0
        except sqlite3.OperationalError:
            print("⚠️ Users table not found, setting total_users to 0")
            stats['total_users'] = 0
        except Exception as e:
            print(f"Error getting total_users: {e}")
            stats['total_users'] = 0
        
        try:
            c.execute("SELECT COUNT(*) FROM users WHERE subscription='premium'")
            result = c.fetchone()
            stats['premium_users'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting premium_users: {e}")
            stats['premium_users'] = 0
        
        # ========== AGENTS STATS ==========
        try:
            c.execute("SELECT COUNT(*) FROM agent_partners")
            result = c.fetchone()
            stats['total_agents'] = int(result[0]) if result and result[0] else 0
        except sqlite3.OperationalError:
            print("⚠️ Agent_partners table not found, setting total_agents to 0")
            stats['total_agents'] = 0
        except Exception as e:
            print(f"Error getting total_agents: {e}")
            stats['total_agents'] = 0
        
        try:
            c.execute("SELECT COUNT(*) FROM agent_partners WHERE status='Active'")
            result = c.fetchone()
            stats['active_agents'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting active_agents: {e}")
            stats['active_agents'] = 0
        
        # ========== PACKAGES STATS ==========
        try:
            c.execute("SELECT COUNT(*) FROM packages")
            result = c.fetchone()
            stats['total_packages'] = int(result[0]) if result and result[0] else 0
        except sqlite3.OperationalError:
            print("⚠️ Packages table not found, setting total_packages to 0")
            stats['total_packages'] = 0
        except Exception as e:
            print(f"Error getting total_packages: {e}")
            stats['total_packages'] = 0
        
        try:
            c.execute("SELECT COUNT(*) FROM packages WHERE status='Active'")
            result = c.fetchone()
            stats['active_packages'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting active_packages: {e}")
            stats['active_packages'] = 0
        
        # ========== BOOKINGS STATS ==========
        try:
            c.execute("SELECT COUNT(*) FROM bookings")
            result = c.fetchone()
            stats['total_bookings'] = int(result[0]) if result and result[0] else 0
        except sqlite3.OperationalError:
            print("⚠️ Bookings table not found, setting total_bookings to 0")
            stats['total_bookings'] = 0
        except Exception as e:
            print(f"Error getting total_bookings: {e}")
            stats['total_bookings'] = 0
        
        try:
            c.execute("SELECT COUNT(*) FROM bookings WHERE payment_status='Paid'")
            result = c.fetchone()
            stats['paid_bookings'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting paid_bookings: {e}")
            stats['paid_bookings'] = 0
        
        try:
            c.execute("SELECT SUM(total_amount) FROM bookings WHERE payment_status='Paid'")
            result = c.fetchone()
            stats['total_revenue'] = float(result[0]) if result and result[0] else 0.0
        except (ValueError, TypeError) as e:
            print(f"Error calculating total_revenue: {e}")
            stats['total_revenue'] = 0.0
        except Exception as e:
            print(f"Error getting total_revenue: {e}")
            stats['total_revenue'] = 0.0
        
        # ========== INQUIRIES STATS ==========
        try:
            c.execute("SELECT COUNT(*) FROM package_inquiries")
            result = c.fetchone()
            stats['total_inquiries'] = int(result[0]) if result and result[0] else 0
        except sqlite3.OperationalError:
            print("⚠️ Package_inquiries table not found, setting total_inquiries to 0")
            stats['total_inquiries'] = 0
        except Exception as e:
            print(f"Error getting total_inquiries: {e}")
            stats['total_inquiries'] = 0
        
        try:
            c.execute("SELECT COUNT(*) FROM package_inquiries WHERE status='Pending'")
            result = c.fetchone()
            stats['pending_inquiries'] = int(result[0]) if result and result[0] else 0
        except Exception as e:
            print(f"Error getting pending_inquiries: {e}")
            stats['pending_inquiries'] = 0
        
        # ========== RECENT ACTIVITY (LAST 7 DAYS) ==========
        try:
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # New users
            try:
                c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (seven_days_ago,))
                result = c.fetchone()
                stats['new_users_week'] = int(result[0]) if result and result[0] else 0
            except Exception as e:
                print(f"Error getting new_users_week: {e}")
                stats['new_users_week'] = 0
            
            # New packages
            try:
                c.execute("SELECT COUNT(*) FROM packages WHERE created_at > ?", (seven_days_ago,))
                result = c.fetchone()
                stats['new_packages_week'] = int(result[0]) if result and result[0] else 0
            except Exception as e:
                print(f"Error getting new_packages_week: {e}")
                stats['new_packages_week'] = 0
            
            # New inquiries
            try:
                c.execute("SELECT COUNT(*) FROM package_inquiries WHERE inquiry_date > ?", 
                         (seven_days_ago,))
                result = c.fetchone()
                stats['new_inquiries_week'] = int(result[0]) if result and result[0] else 0
            except Exception as e:
                print(f"Error getting new_inquiries_week: {e}")
                stats['new_inquiries_week'] = 0
                
        except Exception as e:
            print(f"Error calculating weekly stats: {e}")
            stats['new_users_week'] = 0
            stats['new_packages_week'] = 0
            stats['new_inquiries_week'] = 0
        
        return stats
        
    except sqlite3.OperationalError as e:
        print(f"❌ Database operational error in get_dashboard_stats: {e}")
        return default_stats
        
    except Exception as e:
        print(f"❌ Unexpected error in get_dashboard_stats: {e}")
        return default_stats
        
    finally:
        if conn:
            conn.close()


def get_all_admins():
    """Get list of all admin accounts with error handling"""
    conn = None
    try:
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''CREATE TABLE IF NOT EXISTS admin_credentials
                     (admin_id TEXT PRIMARY KEY,
                      username TEXT UNIQUE NOT NULL,
                      password_hash TEXT NOT NULL,
                      role TEXT DEFAULT 'admin',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''SELECT admin_id, username, role, created_at 
                     FROM admin_credentials 
                     ORDER BY created_at DESC''')
        
        admins = []
        for row in c.fetchall():
            admins.append({
                'admin_id': str(row[0]),
                'username': str(row[1]),
                'role': str(row[2]),
                'created_at': str(row[3])
            })
        
        return admins
        
    except sqlite3.OperationalError as e:
        print(f"Database error getting admins: {e}")
        return []
        
    except Exception as e:
        print(f"Unexpected error getting admins: {e}")
        return []
        
    finally:
        if conn:
            conn.close()


def delete_admin(admin_id):
    """Delete admin account with error handling"""
    conn = None
    try:
        if not admin_id:
            print("Admin ID is required")
            return False
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Check if admin exists
        c.execute('SELECT username FROM admin_credentials WHERE admin_id=?', (admin_id,))
        admin = c.fetchone()
        
        if not admin:
            print(f"Admin with ID {admin_id} not found")
            return False
        
        # Delete admin
        c.execute('DELETE FROM admin_credentials WHERE admin_id=?', (admin_id,))
        conn.commit()
        
        # Verify deletion
        if c.rowcount > 0:
            print(f"✅ Admin '{admin[0]}' deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete admin")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"Database error deleting admin: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error deleting admin: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


def update_admin_password(admin_id, new_password):
    """Update admin password with error handling"""
    conn = None
    try:
        if not admin_id or not new_password:
            print("Admin ID and new password are required")
            return False
        
        if len(new_password) < 6:
            print("Password must be at least 6 characters")
            return False
        
        # Hash new password
        password_hash = hash_password(new_password)
        if not password_hash:
            print("Failed to hash password")
            return False
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Update password
        c.execute('''UPDATE admin_credentials 
                     SET password_hash=? 
                     WHERE admin_id=?''',
                  (password_hash, admin_id))
        
        conn.commit()
        
        # Verify update
        if c.rowcount > 0:
            print(f"✅ Admin password updated successfully")
            return True
        else:
            print(f"❌ Admin not found or password unchanged")
            return False
        
    except sqlite3.OperationalError as e:
        print(f"Database error updating password: {e}")
        return False
        
    except Exception as e:
        print(f"Unexpected error updating password: {e}")
        return False
        
    finally:
        if conn:
            conn.close()


# ========== INITIALIZE ADMIN DB ON IMPORT ==========
init_admin_db()

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #dc2626, #ef4444);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #dc2626;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .success-card {
        background: linear-gradient(135deg, #059669, #10b981);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .warning-card {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .danger-card {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'admin_id' not in st.session_state:
    st.session_state.admin_id = None
if 'admin_username' not in st.session_state:
    st.session_state.admin_username = None

# ========== LOGIN SCREEN ==========

if not st.session_state.admin_logged_in:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #dc2626, #ef4444);
                padding: 3rem; border-radius: 20px; text-align: center;
                color: white; margin-bottom: 2rem;">
        <h1>🛡️ Admin Panel</h1>
        <p style="font-size: 1.2rem;">Umrah Pro Management System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### 🔐 Admin Login")
            
            admin_username = st.text_input(
                "Username",
                placeholder="Enter admin username",
                key="admin_login_username"
            )
            
            admin_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter admin password",
                key="admin_login_password"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🔓 Login as Admin", type="primary", use_container_width=True):
                if not admin_username or not admin_password:
                    st.error("❌ Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        # Call auth_admin() - returns dict or None
                        admin_info = auth_admin(admin_username, admin_password)
                        
                        if admin_info:  # If authentication successful
                            # admin_info is a dict: {'admin_id': ..., 'role': ..., 'username': ...}
                            st.session_state.admin_logged_in = True
                            st.session_state.admin_id = admin_info['admin_id']
                            st.session_state.admin_role = admin_info['role']
                            st.session_state.admin_username = admin_info['username']
                            
                            st.success(f"✅ Welcome, {admin_info['username']}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Invalid admin credentials")
            
            st.markdown("---")
            
            # First-time setup info
            with st.expander("ℹ️ First Time Setup"):
                st.info("""
                **Create your first admin account:**
                
                Add this code to your Python environment or Streamlit app temporarily:
```python
                from admin_panel import create_admin
                
                # Create admin
                if create_admin("admin", "admin123", "super_admin"):
                    print("✅ Admin created successfully")
```
                
                **Default credentials for testing:**
                - Username: `admin`
                - Password: `admin123`
                
                ⚠️ **Security Warning:** Change default password immediately after first login!
                """)
            
            # Debug panel
            with st.expander("🔧 Debug Panel"):
                if st.button("Create Test Admin", use_container_width=True):
                    if create_admin("admin", "admin123", "super_admin"):
                        st.success("✅ Test admin created: admin / admin123")
                    else:
                        st.warning("⚠️ Admin 'admin' already exists")
                
                st.markdown("---")
                
                # Show all admins
                if st.button("Show All Admins", use_container_width=True):
                    admins = get_all_admins()
                    if admins:
                        st.write(f"**Total Admins:** {len(admins)}")
                        for admin in admins:
                            st.markdown(f"""
                            <div style="background: #f0f0f0; padding: 1rem; 
                                        border-radius: 8px; margin: 0.5rem 0;">
                                <strong>Username:</strong> {admin['username']}<br>
                                <strong>Role:</strong> {admin['role']}<br>
                                <strong>ID:</strong> {admin['admin_id'][:8]}...<br>
                                <strong>Created:</strong> {admin['created_at']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("No admins found. Create one using the button above.")

else:
    # ========== LOGGED IN VIEW ==========
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #dc2626, #ef4444);
                padding: 2rem; border-radius: 15px; text-align: center;
                color: white; margin-bottom: 2rem;">
        <h1>Welcome, {st.session_state.admin_username}! 🛡️</h1>
        <p style="font-size: 1.1rem; margin-top: 0.5rem; opacity: 0.9;">
            Admin Panel - Manage Your Umrah Pro Platform
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ========== ADMIN DASHBOARD (LOGGED IN) ==========
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc2626, #ef4444);
                    padding: 1.5rem; border-radius: 15px; text-align: center;
                    color: white; margin-bottom: 1rem;">
            <h3 style="margin: 0;">🛡️ Admin Panel</h3>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">
                {st.session_state.admin_username}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**Role:** {st.session_state.admin_role}")
        st.markdown(f"**ID:** {st.session_state.admin_id[:8]}...")
        
        st.markdown("---")
        
        admin_menu = st.radio("Admin Menu", [
            "📊 Dashboard",
            "👥 Manage Users",
            "🏢 Manage Agents",
            "📦 Manage Packages",
            "📧 Inquiries",
            "💰 Revenue & Analytics",
            "✉️ Send Invitations",
            "🗑️ Data Cleanup",
            "⚙️ Settings"
        ])
    
    # ========== DASHBOARD ==========
    
    if admin_menu == "📊 Dashboard":
        st.markdown("## 📊 Dashboard Overview")
        
        stats = get_dashboard_stats()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Users", stats['total_users'])
            st.caption(f"⭐ {stats['premium_users']} Premium")
        
        with col2:
            st.metric("🏢 Total Agents", stats['total_agents'])
            st.caption(f"✅ {stats['active_agents']} Active")
        
        with col3:
            st.metric("📦 Total Packages", stats['total_packages'])
            st.caption(f"✅ {stats['active_packages']} Active")
        
        with col4:
            st.metric("📧 Total Inquiries", stats['total_inquiries'])
            st.caption(f"⏳ {stats['pending_inquiries']} Pending")
        
        st.markdown("---")
        
        # Recent activity
        st.markdown("### 📈 Activity (Last 7 Days)")
        
        activity_col1, activity_col2, activity_col3 = st.columns(3)
        
        with activity_col1:
            st.info(f"**New Users:** {stats['new_users_week']}")
        
        with activity_col2:
            st.info(f"**New Packages:** {stats['new_packages_week']}")
        
        with activity_col3:
            st.info(f"**New Inquiries:** {stats['new_inquiries_week']}")
        
        st.markdown("---")
        
        # Recent users
        st.markdown("### 👥 Recent Users")
        
        try:
            conn = sqlite3.connect('umrah_pro.db')
            recent_users = pd.read_sql_query("""
                SELECT username, email, country, subscription, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 10
            """, conn)
            conn.close()
            
            if not recent_users.empty:
                st.dataframe(recent_users, use_container_width=True)
            else:
                st.info("No users registered yet")
                
        except Exception as e:
            st.warning(f"⚠️ Unable to load users data. Database may be empty.")
            st.caption(f"Error: {e}")
        
        if not recent_users.empty:
            st.dataframe(recent_users, use_container_width=True)
        else:
            st.info("No users yet")
        
        # Recent packages
        st.markdown("### 📦 Recent Packages")
        
        conn = sqlite3.connect('umrah_pro.db')
        recent_packages = pd.read_sql_query("""
            SELECT p.package_name, a.company_name, p.price, p.status, p.views, p.inquiries, p.created_at
            FROM packages p
            JOIN agent_partners a ON p.agent_id = a.agent_id
            ORDER BY p.created_at DESC
            LIMIT 10
        """, conn)
        conn.close()
        
        if not recent_packages.empty:
            st.dataframe(recent_packages, use_container_width=True)
        else:
            st.info("No packages yet")
    
    # ========== MANAGE USERS ==========
    
    elif admin_menu == "👥 Manage Users":
        st.markdown("## 👥 Manage Users")
        
        # Search and filters
        search_col1, search_col2, search_col3 = st.columns(3)
        
        with search_col1:
            search_user = st.text_input("🔍 Search by username/email")
        
        with search_col2:
            filter_subscription = st.selectbox("Subscription", ["All", "Free", "Premium"])
        
        with search_col3:
            filter_country = st.selectbox("Country", ["All", "🇺🇸 United States", "🇬🇧 United Kingdom", 
                                                      "🇵🇰 Pakistan", "🇮🇳 India", "🇸🇦 Saudi Arabia"])
        
        # Build query
        query = "SELECT id, username, email, phone, country, subscription, created_at FROM users WHERE 1=1"
        params = []
        
        if search_user:
            query += " AND (username LIKE ? OR email LIKE ?)"
            params.extend([f"%{search_user}%", f"%{search_user}%"])
        
        if filter_subscription != "All":
            query += " AND subscription=?"
            params.append(filter_subscription.lower())
        
        if filter_country != "All":
            query += " AND country=?"
            params.append(filter_country)
        
        query += " ORDER BY created_at DESC"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        c.execute(query, params)
        users = c.fetchall()
        conn.close()
        
        st.markdown(f"### Found {len(users)} users")
        
        if users:
            for user in users:
                with st.expander(f"👤 {user[1]} - {user[5].upper()}"):
                    user_col1, user_col2 = st.columns([0.7, 0.3])
                    
                    with user_col1:
                        st.write(f"**Email:** {user[2]}")
                        st.write(f"**Phone:** {user[3]}")
                        st.write(f"**Country:** {user[4]}")
                        st.write(f"**Subscription:** {user[5]}")
                        st.write(f"**Joined:** {user[6]}")
                    
                    with user_col2:
                        # Actions
                        if user[5] == 'free':
                            if st.button(f"⬆️ Upgrade to Premium", key=f"upgrade_{user[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE users SET subscription='premium' WHERE id=?", (user[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Upgraded to Premium!")
                                st.rerun()
                        else:
                            if st.button(f"⬇️ Downgrade to Free", key=f"downgrade_{user[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE users SET subscription='free' WHERE id=?", (user[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Downgraded to Free")
                                st.rerun()
                        
                        if st.button(f"🗑️ Delete User", key=f"delete_user_{user[0]}"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM users WHERE id=?", (user[0],))
                            c.execute("DELETE FROM family_members WHERE user_id=?", (user[0],))
                            c.execute("DELETE FROM user_progress WHERE user_id=?", (user[0],))
                            c.execute("DELETE FROM checklist_progress WHERE user_id=?", (user[0],))
                            conn.commit()
                            conn.close()
                            st.success("✅ User deleted!")
                            st.rerun()
        else:
            st.info("No users found")
    
    # ========== MANAGE AGENTS ==========
    
    elif admin_menu == "🏢 Manage Agents":
        st.markdown("## 🏢 Manage Travel Agents")
        
        # Tabs
        agent_tabs = st.tabs(["📋 All Agents", "➕ Add New Agent"])
        
        with agent_tabs[0]:
            st.markdown("### All Registered Agents")
            
            # Filters
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                search_agent = st.text_input("🔍 Search by company/email")
            
            with filter_col2:
                filter_status = st.selectbox("Status", ["All", "Active", "Pending", "Suspended"])
            
            # Query
            query = """SELECT agent_id, company_name, email, phone, status, 
                       onboarding_status, commission_rate, joined_date 
                       FROM agent_partners WHERE 1=1"""
            params = []
            
            if search_agent:
                query += " AND (company_name LIKE ? OR email LIKE ?)"
                params.extend([f"%{search_agent}%", f"%{search_agent}%"])
            
            if filter_status != "All":
                query += " AND status=?"
                params.append(filter_status)
            
            query += " ORDER BY joined_date DESC"
            
            conn = sqlite3.connect('umrah_pro.db')
            c = conn.cursor()
            c.execute(query, params)
            agents = c.fetchall()
            conn.close()
            
            st.markdown(f"### Found {len(agents)} agents")
            
            if agents:
                for agent in agents:
                    # Get package count
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=?", (agent[0],))
                    package_count = c.fetchone()[0]
                    c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=?", (agent[0],))
                    inquiry_count = c.fetchone()[0]
                    conn.close()
                    
                    status_color = {"Active": "🟢", "Pending": "🟡", "Suspended": "🔴"}
                    
                    with st.expander(f"{status_color.get(agent[4], '⚪')} {agent[1]} - {agent[4]}"):
                        agent_col1, agent_col2 = st.columns([0.6, 0.4])
                        
                        with agent_col1:
                            st.write(f"**Email:** {agent[2]}")
                            st.write(f"**Phone:** {agent[3]}")
                            st.write(f"**Status:** {agent[4]}")
                            st.write(f"**Onboarding:** {agent[5]}")
                            st.write(f"**Commission:** {agent[6]}%")
                            st.write(f"**Joined:** {agent[7]}")
                            st.write(f"**Packages:** {package_count}")
                            st.write(f"**Inquiries:** {inquiry_count}")
                        
                        with agent_col2:
                            st.markdown("**Actions:**")
                            
                            # Status actions
                            if agent[4] != "Active":
                                if st.button("✅ Activate", key=f"activate_{agent[0]}"):
                                    conn = sqlite3.connect('umrah_pro.db')
                                    c = conn.cursor()
                                    c.execute("UPDATE agent_partners SET status='Active' WHERE agent_id=?", (agent[0],))
                                    conn.commit()
                                    conn.close()
                                    st.success("✅ Agent activated!")
                                    st.rerun()
                            
                            if agent[4] != "Suspended":
                                if st.button("⏸️ Suspend", key=f"suspend_{agent[0]}"):
                                    conn = sqlite3.connect('umrah_pro.db')
                                    c = conn.cursor()
                                    c.execute("UPDATE agent_partners SET status='Suspended' WHERE agent_id=?", (agent[0],))
                                    conn.commit()
                                    conn.close()
                                    st.warning("⏸️ Agent suspended!")
                                    st.rerun()
                            
                            # Commission update
                            new_commission = st.number_input("Commission %", 
                                                            value=float(agent[6]), 
                                                            min_value=0.0, 
                                                            max_value=50.0,
                                                            key=f"comm_{agent[0]}")
                            
                            if st.button("💰 Update Commission", key=f"update_comm_{agent[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE agent_partners SET commission_rate=? WHERE agent_id=?", 
                                         (new_commission, agent[0]))
                                conn.commit()
                                conn.close()
                                st.success("✅ Commission updated!")
                                st.rerun()
                            
                            # Delete
                            if st.button("🗑️ Delete Agent", key=f"delete_agent_{agent[0]}"):
                                st.warning(f"⚠️ This will delete {package_count} packages and {inquiry_count} inquiries!")
                                
                                if st.button("⚠️ CONFIRM DELETE", key=f"confirm_delete_{agent[0]}"):
                                    conn = sqlite3.connect('umrah_pro.db')
                                    c = conn.cursor()
                                    c.execute("DELETE FROM packages WHERE agent_id=?", (agent[0],))
                                    c.execute("DELETE FROM package_inquiries WHERE agent_id=?", (agent[0],))
                                    c.execute("DELETE FROM agent_credentials WHERE agent_id=?", (agent[0],))
                                    c.execute("DELETE FROM agent_partners WHERE agent_id=?", (agent[0],))
                                    conn.commit()
                                    conn.close()
                                    st.success("✅ Agent deleted!")
                                    st.rerun()
            else:
                st.info("No agents found")
        
        with agent_tabs[1]:
            st.markdown("### ➕ Add New Travel Agent")
            
            with st.form("add_agent_form"):
                add_col1, add_col2 = st.columns(2)
                
                with add_col1:
                    company_name = st.text_input("Company Name *")
                    agent_name = st.text_input("Contact Person Name *")
                    email = st.text_input("Email *")
                    phone = st.text_input("Phone *")
                
                with add_col2:
                    website = st.text_input("Website")
                    commission = st.number_input("Commission Rate (%)", 0.0, 50.0, 25.0)
                    payment_method = st.selectbox("Payment Method", 
                                                  ["Bank Transfer", "PayPal", "Stripe", "Cash"])
                    bank_details = st.text_area("Bank Details")
                
                notes = st.text_area("Notes")
                
                submit_agent = st.form_submit_button("➕ Add Agent", type="primary", use_container_width=True)
                
                if submit_agent:
                    if not company_name or not agent_name or not email or not phone:
                        st.error("❌ Please fill all required fields")
                    else:
                        agent_id = str(uuid.uuid4())
                        
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        
                        try:
                            c.execute("""INSERT INTO agent_partners 
                                       (agent_id, agent_name, company_name, email, phone, website,
                                        commission_rate, payment_method, bank_details, status,
                                        joined_date, onboarding_status, notes)
                                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                     (agent_id, agent_name, company_name, email, phone, website,
                                      commission, payment_method, bank_details, 'Pending',
                                      datetime.now(), 'Pending', notes))
                            
                            conn.commit()
                            st.success(f"✅ Agent {company_name} added successfully!")
                            st.info("💡 Next: Create login credentials in Settings > Agent Logins")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            conn.close()
    
    # ========== MANAGE PACKAGES ==========
    
    elif admin_menu == "📦 Manage Packages":
        st.markdown("## 📦 Manage Umrah Packages")
        
        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            search_package = st.text_input("🔍 Search package")
        
        with filter_col2:
            filter_pkg_status = st.selectbox("Status", ["All", "Active", "Inactive", "Featured"])
        
        with filter_col3:
            filter_category = st.selectbox("Category", ["All", "Economy", "Standard", "Premium", "Luxury"])
        
        # Build query
        query = """SELECT p.package_id, p.package_name, p.price, p.status, p.category, 
                   p.views, p.inquiries, p.featured, a.company_name, p.created_at
                   FROM packages p
                   JOIN agent_partners a ON p.agent_id = a.agent_id
                   WHERE 1=1"""
        params = []
        
        if search_package:
            query += " AND p.package_name LIKE ?"
            params.append(f"%{search_package}%")
        
        if filter_pkg_status == "Featured":
            query += " AND p.featured=1"
        elif filter_pkg_status != "All":
            query += " AND p.status=?"
            params.append(filter_pkg_status)
        
        if filter_category != "All":
            query += " AND p.category=?"
            params.append(filter_category)
        
        query += " ORDER BY p.created_at DESC"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        c.execute(query, params)
        packages = c.fetchall()
        conn.close()
        
        st.markdown(f"### Found {len(packages)} packages")
        
        if packages:
            for pkg in packages:
                featured_badge = "⭐ FEATURED" if pkg[7] else ""
                
                with st.expander(f"📦 {pkg[1]} - ${pkg[2]:,.0f} {featured_badge}"):
                    pkg_col1, pkg_col2 = st.columns([0.6, 0.4])
                    
                    with pkg_col1:
                        st.write(f"**Agent:** {pkg[8]}")
                        st.write(f"**Price:** ${pkg[2]:,.2f}")
                        st.write(f"**Category:** {pkg[4]}")
                        st.write(f"**Status:** {pkg[3]}")
                        st.write(f"**Views:** {pkg[5]}")
                        st.write(f"**Inquiries:** {pkg[6]}")
                        st.write(f"**Created:** {pkg[9]}")
                    
                    with pkg_col2:
                        st.markdown("**Actions:**")
                        
                        # Status toggle
                        if pkg[3] == "Active":
                            if st.button("⏸️ Deactivate", key=f"deact_{pkg[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE packages SET status='Inactive' WHERE package_id=?", (pkg[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Package deactivated!")
                                st.rerun()
                        else:
                            if st.button("✅ Activate", key=f"act_{pkg[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE packages SET status='Active' WHERE package_id=?", (pkg[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Package activated!")
                                st.rerun()
                        
                        # Featured toggle
                        if pkg[7]:
                            if st.button("⭐ Remove Featured", key=f"unfeat_{pkg[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE packages SET featured=0 WHERE package_id=?", (pkg[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Removed from featured!")
                                st.rerun()
                        else:
                            if st.button("⭐ Make Featured", key=f"feat_{pkg[0]}"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("UPDATE packages SET featured=1 WHERE package_id=?", (pkg[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Added to featured!")
                                st.rerun()
                        
                        # Delete
                        if st.button("🗑️ Delete", key=f"del_pkg_{pkg[0]}"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM packages WHERE package_id=?", (pkg[0],))
                            c.execute("DELETE FROM package_inquiries WHERE package_id=?", (pkg[0],))
                            conn.commit()
                            conn.close()
                            st.success("✅ Package deleted!")
                            st.rerun()
        else:
            st.info("No packages found")
    
    # ========== INQUIRIES ==========
    
    elif admin_menu == "📧 Inquiries":
        st.markdown("## 📧 Package Inquiries")
        
        # Filters
        filter_inq_col1, filter_inq_col2 = st.columns(2)
        
        with filter_inq_col1:
            search_inquiry = st.text_input("🔍 Search by customer name/email")
        
        with filter_inq_col2:
            filter_inq_status = st.selectbox("Status", ["All", "Pending", "Contacted", "Converted", "Rejected"])
        
        # Query
        query = """SELECT i.inquiry_id, i.customer_name, i.customer_email, i.customer_phone,
                   p.package_name, a.company_name, i.travelers, i.status, i.inquiry_date
                   FROM package_inquiries i
                   JOIN packages p ON i.package_id = p.package_id
                   JOIN agent_partners a ON i.agent_id = a.agent_id
                   WHERE 1=1"""
        params = []
        
        if search_inquiry:
            query += " AND (i.customer_name LIKE ? OR i.customer_email LIKE ?)"
            params.extend([f"%{search_inquiry}%", f"%{search_inquiry}%"])
        
        if filter_inq_status != "All":
            query += " AND i.status=?"
            params.append(filter_inq_status)
        
        query += " ORDER BY i.inquiry_date DESC"
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        c.execute(query, params)
        inquiries = c.fetchall()
        conn.close()
        
        st.markdown(f"### Found {len(inquiries)} inquiries")
        
        if inquiries:
            for inq in inquiries:
                status_colors = {
                    "Pending": "🟡",
                    "Contacted": "🔵",
                    "Converted": "🟢",
                    "Rejected": "🔴"
                }
                
                with st.expander(f"{status_colors.get(inq[7], '⚪')} {inq[1]} - {inq[7]}"):
                    inq_col1, inq_col2 = st.columns([0.7, 0.3])
                    
                    with inq_col1:
                        st.write(f"**Customer:** {inq[1]}")
                        st.write(f"**Email:** {inq[2]}")
                        st.write(f"**Phone:** {inq[3]}")
                        st.write(f"**Package:** {inq[4]}")
                        st.write(f"**Agent:** {inq[5]}")
                        st.write(f"**Travelers:** {inq[6]}")
                        st.write(f"**Date:** {inq[8]}")
                    
                    with inq_col2:
                        st.markdown("**Update Status:**")
                        
                        new_status = st.selectbox("Status", 
                                                 ["Pending", "Contacted", "Converted", "Rejected"],
                                                 key=f"status_{inq[0]}")
                        
                        if st.button("💾 Update", key=f"update_inq_{inq[0]}"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute("UPDATE package_inquiries SET status=? WHERE inquiry_id=?", 
                                     (new_status, inq[0]))
                            conn.commit()
                            conn.close()
                            st.success("✅ Status updated!")
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_inq_{inq[0]}"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute("DELETE FROM package_inquiries WHERE inquiry_id=?", (inq[0],))
                            conn.commit()
                            conn.close()
                            st.success("✅ Inquiry deleted!")
                            st.rerun()
        else:
            st.info("No inquiries found")
    
    # ========== REVENUE & ANALYTICS ==========
    
    elif admin_menu == "💰 Revenue & Analytics":
        st.markdown("## 💰 Revenue & Analytics")
        
        # Revenue summary
        st.markdown("### 💵 Revenue Summary")
        
        conn = sqlite3.connect('umrah_pro.db')
        c = conn.cursor()
        
        # Premium subscriptions
        c.execute("SELECT COUNT(*) FROM users WHERE subscription='premium'")
        premium_count = c.fetchone()[0]
        premium_revenue = premium_count * 4.99
        
        # Package inquiries converted (assuming 10% conversion with $100 commission)
        c.execute("SELECT COUNT(*) FROM package_inquiries WHERE status='Converted'")
        converted_count = c.fetchone()[0]
        package_revenue = converted_count * 100  # Estimated
        
        conn.close()
        
        rev_col1, rev_col2, rev_col3 = st.columns(3)
        
        with rev_col1:
            st.metric("💳 Premium Subscriptions", f"${premium_revenue:.2f}/month")
            st.caption(f"{premium_count} premium users × $4.99")
        
        with rev_col2:
            st.metric("📦 Package Commissions", f"${package_revenue:,.2f}")
            st.caption(f"{converted_count} conversions (estimated)")
        
        with rev_col3:
            total_revenue = premium_revenue + package_revenue
            st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
            st.caption("Monthly estimate")
        
        st.markdown("---")
        
        # Top performing packages
        st.markdown("### 🏆 Top Performing Packages")
        
        conn = sqlite3.connect('umrah_pro.db')
        top_packages = pd.read_sql_query("""
            SELECT p.package_name, a.company_name, p.views, p.inquiries, p.price
            FROM packages p
            JOIN agent_partners a ON p.agent_id = a.agent_id
            WHERE p.status='Active'
            ORDER BY p.inquiries DESC, p.views DESC
            LIMIT 10
        """, conn)
        conn.close()
        
        if not top_packages.empty:
            st.dataframe(top_packages, use_container_width=True)
        else:
            st.info("No package data yet")
        
        st.markdown("---")
        
        # Top agents
        st.markdown("### 🌟 Top Performing Agents")
        
        conn = sqlite3.connect('umrah_pro.db')
        top_agents = pd.read_sql_query("""
            SELECT a.company_name, 
                   COUNT(DISTINCT p.package_id) as packages,
                   SUM(p.views) as total_views,
                   SUM(p.inquiries) as total_inquiries
            FROM agent_partners a
            LEFT JOIN packages p ON a.agent_id = p.agent_id
            WHERE a.status='Active'
            GROUP BY a.agent_id, a.company_name
            ORDER BY total_inquiries DESC
            LIMIT 10
        """, conn)
        conn.close()
        
        if not top_agents.empty:
            st.dataframe(top_agents, use_container_width=True)
        else:
            st.info("No agent data yet")

    # ========== SEND INVITATIONS ==========

    elif admin_menu == "✉️ Send Invitations":
        st.markdown("## ✉️ Send Agent Invitations")
        st.caption("Invite travel agents to join Umrah Pro platform")
        
        invitation_tabs = st.tabs([
            "📤 Send Invitations",
            "📋 Bulk Upload",
            "📊 Invitation Status",
            "📝 Email Templates"
        ])
        
        # ========== TAB 1: SEND INVITATIONS ==========
        
        # ========== TAB 1: SEND INVITATIONS (COMPLETELY FIXED) ==========
        
        with invitation_tabs[0]:
            st.markdown("### 📤 Send Individual Invitation")
            
            # Agent Details (Outside form so they update in real-time)
            st.markdown("#### 👤 Agent Details")
            
            inv_col1, inv_col2 = st.columns(2)
            
            with inv_col1:
                agent_company = st.text_input("Company Name *", placeholder="ABC Travel Agency")
                agent_contact_name = st.text_input("Contact Person *", placeholder="Ahmed Khan")
                agent_email = st.text_input("Email Address *", placeholder="info@abctravel.com")
                agent_phone = st.text_input("Phone Number", placeholder="+966 50 123 4567")
            
            with inv_col2:
                agent_country = st.selectbox("Country *", [
                    "🇸🇦 Saudi Arabia",
                    "🇦🇪 United Arab Emirates",
                    "🇵🇰 Pakistan",
                    "🇮🇳 India",
                    "🇧🇩 Bangladesh",
                    "🇮🇩 Indonesia",
                    "🇲🇾 Malaysia",
                    "🇹🇷 Turkey",
                    "🇪🇬 Egypt",
                    "🇬🇧 United Kingdom",
                    "🇺🇸 United States",
                    "🇨🇦 Canada",
                    "Other"
                ])
                agent_city = st.text_input("City", placeholder="Jeddah")
                agent_website = st.text_input("Website (optional)", placeholder="www.abctravel.com")
                commission_offered = st.number_input("Commission Rate (%)", 0.0, 50.0, 25.0, 0.5)
            
            st.markdown("---")
            
            # Template Selection (Outside form)
            st.markdown("#### 📧 Email Template Selection")
            
            email_template = st.selectbox("Choose Template", [
                "Professional Invitation",
                "Premium Partner Offer",
                "Early Bird Special"
            ])
            
            st.markdown("---")
            
            # Generate email content based on selection (This recalculates every time)
            subject_line = ""
            email_body = ""
            
            if email_template == "Professional Invitation":
                subject_line = "Invitation to Join Umrah Pro - Premium Travel Partner Program"
                email_body = f"""Dear {agent_contact_name if agent_contact_name else '[Contact Name]'},

Assalamu Alaikum!

I hope this message finds you in the best of health and Iman.

I'm reaching out to invite {agent_company if agent_company else '[Your Company]'} to join Umrah Pro, the fastest-growing digital platform connecting Umrah travelers with trusted travel agencies worldwide.

WHY PARTNER WITH UMRAH PRO?

✅ Reach Thousands of Customers - Our platform attracts pilgrims from 50+ countries
✅ Zero Listing Fees - List unlimited packages at no cost
✅ Direct Customer Inquiries - Get qualified leads delivered to your inbox
✅ Competitive Commission - We offer {commission_offered}% commission on bookings
✅ Easy Package Management - Update packages in real-time through your dashboard
✅ Multi-Currency Support - Prices displayed in customer's local currency
✅ 24/7 Platform Access - Manage your business anytime, anywhere

WHAT WE OFFER:
- Dedicated agent dashboard for package management
- Real-time inquiry notifications
- Customer analytics and insights
- Marketing support for your packages
- Featured listing opportunities
- Priority customer support

GETTING STARTED IS EASY:
1. Create your free agent account
2. List your Umrah packages
3. Start receiving customer inquiries
4. Grow your business!

SPECIAL OFFER FOR EARLY PARTNERS:
As one of our founding partners, you'll receive:
- Featured listing for your first 3 packages (FREE)
- Priority placement in search results for 6 months
- Dedicated account manager
- Co-marketing opportunities

We would be honored to have {agent_company if agent_company else '[Your Company]'} as part of the Umrah Pro family.

If you have any questions, please don't hesitate to reach out. I'm here to help!

JazakAllahu Khair,

Umrah Pro Partnership Team
📧 Email: partnerships@umrahpro.com
📞 WhatsApp: +966 XX XXX XXXX
🌐 Website: www.umrahpro.com

---
This is a business invitation. You're receiving this because {agent_company if agent_company else 'your company'} is a recognized Umrah travel service provider."""
            
            elif email_template == "Premium Partner Offer":
                subject_line = "🌟 Exclusive Premium Partnership Opportunity - Umrah Pro"
                email_body = f"""Dear {agent_contact_name if agent_contact_name else '[Contact Name]'},

Assalamu Alaikum wa Rahmatullahi wa Barakatuh!

I'm excited to extend an EXCLUSIVE PREMIUM PARTNERSHIP INVITATION to {agent_company if agent_company else '[Your Company]'}.

🌟 PREMIUM PARTNER BENEFITS:

EXCLUSIVE ADVANTAGES:
✨ Featured Partner Badge - Stand out with premium branding
✨ Priority Search Rankings - Appear at the top of search results
✨ Higher Commission Rate - {commission_offered}% (vs standard 20%)
✨ Dedicated Account Manager - Personal support for your success
✨ Early Access - New features before general release
✨ Co-Marketing - Featured in our newsletters and social media
✨ Analytics Dashboard - Advanced insights and reporting
✨ Custom Package URLs - Shareable links for your marketing

MARKET OPPORTUNITY:
📈 2M+ Muslims search for Umrah packages monthly
🌍 We're targeting 100K active users in Year 1
💰 Average package value: $2,500-5,000
🎯 Your potential monthly bookings: 20-50 packages

YOUR ESTIMATED EARNINGS:
- Conservative: 20 bookings/month × $2,500 × {commission_offered}% = ${int(20 * 2500 * commission_offered / 100):,}/month
- Moderate: 35 bookings/month × $3,000 × {commission_offered}% = ${int(35 * 3000 * commission_offered / 100):,}/month
- Optimistic: 50 bookings/month × $4,000 × {commission_offered}% = ${int(50 * 4000 * commission_offered / 100):,}/month

LIMITED TIME OFFER:
This premium partnership is available to the FIRST 50 AGENCIES ONLY. We're currently at 23 partners.

ZERO RISK:
✅ No setup fees
✅ No monthly fees
✅ No minimum commitment
✅ Cancel anytime
✅ You only pay commission on actual bookings

READY TO JOIN?
Click here to claim your Premium Partner spot!

This opportunity won't last long. Let's grow together!

Best regards,

Partnership Director
Umrah Pro

📧 partnerships@umrahpro.com
📱 WhatsApp: +966 XX XXX XXXX
🌐 www.umrahpro.com/partners"""
            
            elif email_template == "Early Bird Special":
                deadline_date = (datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')
                days_left = 7 - (datetime.now().day % 7)
                
                subject_line = f"🎁 Early Bird Offer: Join Umrah Pro Before {deadline_date}"
                email_body = f"""As-salamu alaykum {agent_contact_name if agent_contact_name else '[Partner]'}!

⏰ LIMITED TIME OFFER - 7 DAYS ONLY

We're launching Umrah Pro officially next month, and we're inviting {agent_company if agent_company else '[Your Company]'} to join as an EARLY BIRD PARTNER.

🎁 EARLY BIRD BONUSES (Worth $2,500+):

1. FREE Featured Listings ($500 value)
   - First 5 packages featured for 12 months
   - Premium badge on all your listings

2. Higher Commission Forever ($1,000+ value)
   - {commission_offered}% commission (vs 20% standard)
   - Rate locked in for lifetime

3. Priority Support ($500 value)
   - Dedicated account manager
   - 24/7 priority email & WhatsApp support

4. Marketing Package ($500 value)
   - Featured in launch campaign
   - Social media spotlight
   - Newsletter feature

5. Advanced Features Early Access
   - Beta test new tools first
   - Influence product roadmap

DEADLINE: {deadline_date}

After this date, standard terms apply:
❌ No featured listings
❌ Standard 20% commission
❌ No launch bonuses

WHY UMRAH PRO?
✅ Modern, mobile-first platform
✅ Multi-currency support (20+ currencies)
✅ Country-specific package filtering
✅ Real-time inquiry notifications
✅ Easy package management
✅ Built by Muslims, for Muslims

WHAT AGENTS ARE SAYING:

"Best decision for our business. We've received 45 inquiries in 2 weeks!"
— Al-Hijaz Tours, Jeddah

"The platform is so easy to use. Our packages are visible to the right customers."
— Makkah Travels, Malaysia

CLAIM YOUR EARLY BIRD SPOT:
Click here to register now!

Questions?
Reply to this email or WhatsApp me: +966 XX XXX XXXX

Don't miss this opportunity! Only {days_left} days left.

JazakAllahu Khair,

Umrah Pro Team

P.S. We're only accepting 100 Early Bird partners. Currently at 68/100."""
            
            # Display Preview (This updates automatically)
            st.markdown("### 📧 Email Preview")
            
            # Template indicator
            template_colors = {
                "Professional Invitation": "#059669",
                "Premium Partner Offer": "#f59e0b",
                "Early Bird Special": "#dc2626"
            }
            
            template_color = template_colors.get(email_template, "#059669")
            
            st.markdown(f"""
            <div style="background: {template_color}; color: white; padding: 1rem; 
                        border-radius: 8px; margin-bottom: 1rem; text-align: center;">
                <strong>📧 Template: {email_template}</strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Subject preview
            st.markdown("**Subject Line:**")
            st.info(subject_line)
            
            # Message preview
            st.markdown("**Message Body:**")
            
            # Use a container with fixed height for the preview
            preview_container = st.container()
            with preview_container:
                st.text_area(
                    label="Content",
                    value=email_body,
                    height=500,
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            st.markdown("---")
            
            # Send Options Form
            st.markdown("### 📤 Send Options")
            
            with st.form("send_invitation_form"):
                send_col1, send_col2 = st.columns(2)
                
                with send_col1:
                    send_method = st.radio("Send Method", [
                        "📧 Send Email Now",
                        "📋 Copy to Clipboard",
                        "💾 Save as Draft"
                    ])
                
                with send_col2:
                    schedule_send = st.checkbox("Schedule for later")
                    if schedule_send:
                        send_date = st.date_input("Send Date")
                        send_time = st.time_input("Send Time")
                
                # Submit button
                submit_invitation = st.form_submit_button("📤 Send Invitation", 
                    type="primary", use_container_width=True)
                
                if submit_invitation:
                    if not agent_company or not agent_contact_name or not agent_email:
                        st.error("❌ Please fill in all required fields (Company, Contact Name, Email)")
                    else:
                        # Save to database
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        
                        # Create table for invitations if doesn't exist
                        c.execute('''CREATE TABLE IF NOT EXISTS agent_invitations
                                    (invitation_id TEXT PRIMARY KEY,
                                     company_name TEXT,
                                     contact_name TEXT,
                                     email TEXT,
                                     phone TEXT,
                                     country TEXT,
                                     city TEXT,
                                     website TEXT,
                                     commission_rate REAL,
                                     template_used TEXT,
                                     status TEXT,
                                     sent_date TIMESTAMP,
                                     opened BOOLEAN DEFAULT 0,
                                     clicked BOOLEAN DEFAULT 0)''')
                        
                        invitation_id = str(uuid.uuid4())
                        
                        c.execute("""INSERT INTO agent_invitations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                 (invitation_id, agent_company, agent_contact_name, agent_email,
                                  agent_phone, agent_country, agent_city, agent_website,
                                  commission_offered, email_template, 'Pending', datetime.now(), 0, 0))
                        
                        conn.commit()
                        conn.close()
                        
                        if send_method == "📧 Send Email Now":
                            try:
                                from email_service import EmailService
                                
                                email_service = EmailService(api_key=st.secrets.get("SENDGRID_API_KEY"))
                                
                                agent_data = {
                                    'company_name': agent_company,
                                    'contact_name': agent_contact_name,
                                    'email': agent_email,
                                    'phone': agent_phone,
                                    'country': agent_country,
                                    'commission_rate': commission_offered
                                }
                                
                                template_map = {
                                    "Professional Invitation": "professional",
                                    "Premium Partner Offer": "premium",
                                    "Early Bird Special": "early_bird"
                                }
                                
                                template_key = template_map.get(email_template, "professional")
                                
                                with st.spinner("Sending email..."):
                                    result = email_service.send_agent_invitation(
                                        agent_email,
                                        agent_data,
                                        template_key
                                    )
                                
                                if result['success']:
                                    conn = sqlite3.connect('umrah_pro.db')
                                    c = conn.cursor()
                                    c.execute("UPDATE agent_invitations SET status='Sent' WHERE invitation_id=?", 
                                             (invitation_id,))
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success(f"✅ Email sent successfully to {agent_email}!")
                                    st.balloons()
                                else:
                                    st.error(f"❌ Failed to send: {result.get('error')}")
                            
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                                st.info("💡 Make sure SendGrid is configured in .streamlit/secrets.toml")
                        
                        elif send_method == "📋 Copy to Clipboard":
                            st.success("✅ Invitation saved to database!")
                            st.info(f"""
                            📋 **Email Content Ready to Copy**
                            
                            **To:** {agent_email}  
                            **Subject:** {subject_line}
                            
                            Copy the message from the preview above and paste into your email client.
                            """)
                        
                        else:  # Save as Draft
                            st.success(f"""
                            💾 **Invitation Saved as Draft**
                            
                            You can view and send it later from the "Invitation Status" tab.
                            """)
            
            # Help section
            with st.expander("💡 Tips for Better Results"):
                st.markdown("""
                ### Email Template Guide:
                
                **📧 Professional Invitation**
                - Best for: First-time outreach
                - Tone: Professional, informative
                - Expected response: 15-20%
                
                **⭐ Premium Partner Offer**
                - Best for: Established agencies
                - Tone: Exclusive, high-value
                - Expected response: 25-30%
                
                **🎁 Early Bird Special**
                - Best for: Time-sensitive campaigns
                - Tone: Urgent, bonus-focused
                - Expected response: 30-35%
                
                ### Best Practices:
                - Personalize the company name and contact person
                - Adjust commission rate based on agency size
                - Follow up within 3-5 days if no response
                - A/B test different templates for better results
                """)
        
        # ========== TAB 2: BULK UPLOAD ==========
        
        with invitation_tabs[1]:
            st.markdown("### 📋 Bulk Upload Agent Contacts")
            st.caption("Upload multiple agents at once from Excel/CSV file")
            
            # Download template
            st.markdown("#### 1️⃣ Download Template")
            
            template_data = {
                'company_name': ['ABC Travel Agency', 'XYZ Tours', 'Best Umrah Services'],
                'contact_name': ['Ahmed Khan', 'Fatima Ali', 'Mohammed Hassan'],
                'email': ['info@abctravel.com', 'contact@xyztours.com', 'hello@bestumrah.com'],
                'phone': ['+966501234567', '+971501234567', '+923001234567'],
                'country': ['Saudi Arabia', 'UAE', 'Pakistan'],
                'city': ['Jeddah', 'Dubai', 'Lahore'],
                'website': ['www.abctravel.com', 'www.xyztours.com', 'www.bestumrah.com'],
                'commission_rate': [25.0, 25.0, 25.0]
            }
            
            template_df = pd.DataFrame(template_data)
            
            csv = template_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV Template",
                data=csv,
                file_name="agent_contacts_template.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            st.markdown("---")
            
            # Upload file
            st.markdown("#### 2️⃣ Upload Your File")
            
            uploaded_file = st.file_uploader("Choose CSV or Excel file", type=['csv', 'xlsx'])
            
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.success(f"✅ File uploaded! Found {len(df)} agents")
                    
                    # Preview
                    st.markdown("#### 3️⃣ Preview Data")
                    st.dataframe(df, use_container_width=True)
                    
                    # Validation
                    required_columns = ['company_name', 'contact_name', 'email']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                    else:
                        st.success("✅ All required columns present")
                        
                        # Email template selection
                        st.markdown("#### 4️⃣ Select Email Template")
                        
                        bulk_template = st.selectbox("Template for all agents", [
                            "Professional Invitation",
                            "Premium Partner Offer",
                            "Early Bird Special"
                        ], key="bulk_template")
                        
                        # Send button
                        if st.button("📤 Send to All Agents", type="primary", use_container_width=True):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            
                            # Create table if doesn't exist
                            c.execute('''CREATE TABLE IF NOT EXISTS agent_invitations
                                        (invitation_id TEXT PRIMARY KEY,
                                        company_name TEXT,
                                        contact_name TEXT,
                                        email TEXT,
                                        phone TEXT,
                                        country TEXT,
                                        city TEXT,
                                        website TEXT,
                                        commission_rate REAL,
                                        template_used TEXT,
                                        status TEXT,
                                        sent_date TIMESTAMP,
                                        opened BOOLEAN DEFAULT 0,
                                        clicked BOOLEAN DEFAULT 0)''')
                            
                            success_count = 0
                            error_count = 0
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for idx, row in df.iterrows():
                                try:
                                    invitation_id = str(uuid.uuid4())
                                    
                                    c.execute("""INSERT INTO agent_invitations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                            (invitation_id,
                                            row.get('company_name', ''),
                                            row.get('contact_name', ''),
                                            row.get('email', ''),
                                            row.get('phone', ''),
                                            row.get('country', ''),
                                            row.get('city', ''),
                                            row.get('website', ''),
                                            row.get('commission_rate', 25.0),
                                            bulk_template,
                                            'Sent',
                                            datetime.now(),
                                            0, 0))
                                    
                                    success_count += 1
                                except Exception as e:
                                    error_count += 1
                                    st.warning(f"⚠️ Error with {row.get('email', 'unknown')}: {e}")
                                
                                # Update progress
                                progress = (idx + 1) / len(df)
                                progress_bar.progress(progress)
                                status_text.text(f"Processing {idx + 1}/{len(df)}...")
                            
                            conn.commit()
                            conn.close()
                            
                            status_text.empty()
                            progress_bar.empty()
                            
                            st.success(f"""
                            ✅ **Bulk Upload Complete!**
                            
                            - ✅ Successfully saved: {success_count}
                            - ❌ Errors: {error_count}
                            
                            💡 Configure SendGrid to enable actual email sending!
                            """)
                            st.balloons()
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {e}")
        
        # ========== TAB 3: INVITATION STATUS ==========
    
        with invitation_tabs[2]:
            st.markdown("### 📊 Invitation Status Tracking")
            
            # Get invitations from database
            conn = sqlite3.connect('umrah_pro.db')
            c = conn.cursor()
            
            try:
                c.execute("""SELECT invitation_id, company_name, contact_name, email, 
                            phone, country, template_used, status, sent_date, opened, clicked
                            FROM agent_invitations
                            ORDER BY sent_date DESC""")
                invitations = c.fetchall()
            except:
                invitations = []
            
            conn.close()
            
            if invitations:
                st.markdown(f"### Total Invitations Sent: {len(invitations)}")
                
                # Summary stats
                summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                
                with summary_col1:
                    st.metric("📤 Sent", len(invitations))
                
                with summary_col2:
                    opened_count = sum(1 for inv in invitations if inv[9])
                    open_rate = (opened_count / len(invitations) * 100) if invitations else 0
                    st.metric("👁️ Opened", f"{opened_count} ({open_rate:.1f}%)")
                
                with summary_col3:
                    clicked_count = sum(1 for inv in invitations if inv[10])
                    click_rate = (clicked_count / len(invitations) * 100) if invitations else 0
                    st.metric("🖱️ Clicked", f"{clicked_count} ({click_rate:.1f}%)")
                
                with summary_col4:
                    # Count actual signups (agents who joined)
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("""SELECT COUNT(*) FROM agent_partners 
                                WHERE email IN (SELECT email FROM agent_invitations)""")
                    signup_count = c.fetchone()[0]
                    conn.close()
                    
                    conversion_rate = (signup_count / len(invitations) * 100) if invitations else 0
                    st.metric("✅ Joined", f"{signup_count} ({conversion_rate:.1f}%)")
                
                st.markdown("---")
                
                # Filter options
                filter_col1, filter_col2 = st.columns(2)
                
                with filter_col1:
                    filter_status = st.selectbox("Filter by Status", 
                        ["All", "Sent", "Contacted", "Joined", "Not Joined"])
                
                with filter_col2:
                    search_inv = st.text_input("🔍 Search by company/email")
                
                st.markdown("---")
                
                # Detailed list
                st.markdown("### 📋 Detailed Invitation List")
                
                for inv in invitations:
                    # Check if company name or email matches search
                    if search_inv:
                        if search_inv.lower() not in inv[1].lower() and search_inv.lower() not in inv[3].lower():
                            continue
                    
                    status_icon = {
                        'Sent': '📤',
                        'Contacted': '📞',
                        'Opened': '👁️',
                        'Clicked': '🖱️',
                        'Joined': '✅'
                    }
                    
                    # Check if joined
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("SELECT agent_id FROM agent_partners WHERE email=?", (inv[3],))
                    has_joined = c.fetchone() is not None
                    conn.close()
                    
                    # Determine current status
                    if has_joined:
                        current_status = 'Joined'
                    elif inv[7] == 'Contacted':
                        current_status = 'Contacted'
                    elif inv[10]:  # clicked
                        current_status = 'Clicked'
                    elif inv[9]:  # opened
                        current_status = 'Opened'
                    else:
                        current_status = 'Sent'
                    
                    # Apply filter
                    if filter_status != "All":
                        if filter_status == "Not Joined" and has_joined:
                            continue
                        elif filter_status == "Joined" and not has_joined:
                            continue
                        elif filter_status not in [current_status, "Not Joined"]:
                            continue
                    
                    with st.expander(f"{status_icon.get(current_status, '📤')} {inv[1]} - {current_status}"):
                        inv_detail_col1, inv_detail_col2 = st.columns([0.65, 0.35])
                        
                        with inv_detail_col1:
                            st.write(f"**Contact:** {inv[2]}")
                            st.write(f"**Email:** {inv[3]}")
                            st.write(f"**Phone:** {inv[4] if inv[4] else 'Not provided'}")
                            st.write(f"**Country:** {inv[5]}")
                            st.write(f"**Template Used:** {inv[6]}")
                            st.write(f"**Sent:** {inv[8]}")
                            
                            status_col1, status_col2, status_col3 = st.columns(3)
                            with status_col1:
                                if inv[9]:
                                    st.success("✅ Opened")
                                else:
                                    st.error("❌ Not Opened")
                            
                            with status_col2:
                                if inv[10]:
                                    st.success("✅ Clicked")
                                else:
                                    st.error("❌ Not Clicked")
                            
                            with status_col3:
                                if has_joined:
                                    st.success("✅ Joined")
                                else:
                                    st.error("❌ Not Joined")
                        
                        with inv_detail_col2:
                            st.markdown("**Actions:**")
                            
                            if not has_joined:
                                # Resend Invitation
                                if st.button("📧 Resend Invitation", key=f"resend_{inv[0]}", use_container_width=True):
                                    # Try to send email if configured
                                    try:
                                        from email_service import EmailService
                                        
                                        # Check if SendGrid is configured
                                        if 'SENDGRID_API_KEY' in st.secrets:
                                            email_service = EmailService(api_key=st.secrets["SENDGRID_API_KEY"])
                                            
                                            agent_data = {
                                                'company_name': inv[1],
                                                'contact_name': inv[2],
                                                'email': inv[3],
                                                'phone': inv[4],
                                                'country': inv[5],
                                                'commission_rate': 25.0
                                            }
                                            
                                            # Map template name
                                            template_map = {
                                                "Professional Invitation": "professional",
                                                "Premium Partner Offer": "premium",
                                                "Early Bird Special": "early_bird"
                                            }
                                            template_key = template_map.get(inv[6], "professional")
                                            
                                            with st.spinner("Resending email..."):
                                                result = email_service.send_agent_invitation(
                                                    inv[3],
                                                    agent_data,
                                                    template_key
                                                )
                                            
                                            if result['success']:
                                                # Update database
                                                conn = sqlite3.connect('umrah_pro.db')
                                                c = conn.cursor()
                                                c.execute("UPDATE agent_invitations SET sent_date=? WHERE invitation_id=?", 
                                                        (datetime.now(), inv[0]))
                                                conn.commit()
                                                conn.close()
                                                
                                                st.success(f"✅ Invitation resent to {inv[3]}!")
                                                st.balloons()
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to resend: {result.get('error')}")
                                        else:
                                            st.warning("⚠️ SendGrid not configured. Please add SENDGRID_API_KEY to secrets.")
                                            st.info(f"💡 You can manually email {inv[3]}")
                                    
                                    except ImportError:
                                        st.warning("⚠️ Email service not installed. Run: pip install sendgrid")
                                        st.info(f"📧 Manually email: {inv[3]}")
                                    except Exception as e:
                                        st.error(f"❌ Error: {e}")
                                
                                # Mark as Contacted
                                if st.button("📞 Mark as Contacted", key=f"contact_{inv[0]}", use_container_width=True):
                                    conn = sqlite3.connect('umrah_pro.db')
                                    c = conn.cursor()
                                    c.execute("UPDATE agent_invitations SET status='Contacted' WHERE invitation_id=?", 
                                            (inv[0],))
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success("✅ Marked as contacted!")
                                    st.rerun()
                                
                                # Add Note
                                with st.form(f"note_form_{inv[0]}"):
                                    note = st.text_area("Add Note", placeholder="Follow-up scheduled for next week...")
                                    
                                    if st.form_submit_button("💾 Save Note", use_container_width=True):
                                        # Add notes column if doesn't exist
                                        conn = sqlite3.connect('umrah_pro.db')
                                        c = conn.cursor()
                                        
                                        try:
                                            c.execute("ALTER TABLE agent_invitations ADD COLUMN notes TEXT")
                                        except:
                                            pass  # Column already exists
                                        
                                        c.execute("UPDATE agent_invitations SET notes=? WHERE invitation_id=?", 
                                                (note, inv[0]))
                                        conn.commit()
                                        conn.close()
                                        
                                        st.success("✅ Note saved!")
                                        st.rerun()
                            else:
                                st.success("🎉 Agent has joined the platform!")
                                
                                # View agent profile button
                                if st.button("👁️ View Agent Profile", key=f"view_{inv[0]}", use_container_width=True):
                                    st.info("Navigate to 'Manage Agents' to view full profile")
                            
                            # Delete invitation
                            st.markdown("---")
                            
                            if st.button("🗑️ Delete Invitation", key=f"del_inv_{inv[0]}", use_container_width=True):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                c.execute("DELETE FROM agent_invitations WHERE invitation_id=?", (inv[0],))
                                conn.commit()
                                conn.close()
                                st.success("✅ Invitation deleted!")
                                st.rerun()
                        
                        # Display notes if exist
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        try:
                            c.execute("SELECT notes FROM agent_invitations WHERE invitation_id=?", (inv[0],))
                            result = c.fetchone()
                            if result and result[0]:
                                st.markdown("---")
                                st.markdown("**📝 Notes:**")
                                st.info(result[0])
                        except:
                            pass
                        conn.close()
            else:
                st.info("📭 No invitations sent yet. Use the 'Send Invitations' tab to get started!")
                
                if st.button("➕ Send Your First Invitation", type="primary", use_container_width=True):
                    st.info("👈 Click on the 'Send Invitations' tab to get started!")
        
        # ========== TAB 4: EMAIL TEMPLATES ==========
        
        with invitation_tabs[3]:
            st.markdown("### 📝 Email Template Library")
            st.caption("Pre-designed templates for different scenarios")
            
            template_display = st.selectbox("View Template", [
                "Professional Invitation",
                "Premium Partner Offer",
                "Early Bird Special",
                "Follow-up Email",
                "Welcome Email (After Signup)"
            ])
            
            if template_display == "Professional Invitation":
                st.markdown("""
                **Subject:** Invitation to Join Umrah Pro - Premium Travel Partner Program
                
                **Best for:** Initial cold outreach to professional agencies
                
                **Key Features:**
                - Professional tone
                - Clear value proposition
                - Platform benefits highlighted
                - Call-to-action included
                
                **Conversion Rate:** ~15-20%
                """)
            
            elif template_display == "Premium Partner Offer":
                st.markdown("""
                **Subject:** Exclusive Premium Partnership Opportunity - Umrah Pro
                
                **Best for:** High-value agencies with established reputation
                
                **Key Features:**
                - Exclusive positioning
                - Revenue projections included
                - Premium benefits emphasized
                - Urgency created (limited spots)
                
                **Conversion Rate:** ~25-30%
                """)
            
            elif template_display == "Early Bird Special":
                st.markdown("""
                **Subject:** 🎁 Early Bird Offer: Join Before [Date]
                
                **Best for:** Launch campaigns and time-sensitive offers
                
                **Key Features:**
                - Strong urgency element
                - Clear deadline
                - Valuable bonuses
                - Social proof included
                
                **Conversion Rate:** ~30-35%
                """)
            
            elif template_display == "Follow-up Email":
                st.code("""Subject: Following up - Partnership with Umrah Pro

    Dear [Name],

    As-salamu alaykum!

    I wanted to follow up on my previous email about partnering with Umrah Pro.

    I understand you're busy, so I'll keep this brief.

    Quick reminder of what we offer:
    ✅ Zero setup fees
    ✅ 25% commission on all bookings
    ✅ Direct customer inquiries
    ✅ Free package listings

    We've had great success with agencies like yours:
    - 45+ inquiries in first 2 weeks (Al-Hijaz Tours)
    - $50,000+ in bookings in first month (Makkah Express)

    Would you be open to a quick 10-minute call this week?

    You can book a time here: [Calendar Link]

    Best regards,
    [Your Name]

    P.S. We're only accepting 50 more partners this month.""", language=None)
            
            else:  # Welcome Email
                st.code("""Subject: Welcome to Umrah Pro! 🎉 Your Account is Active

    Dear [Name],

    As-salamu alaykum and welcome to the Umrah Pro family!

    Your agent account is now active: [Login Link]

    **YOUR NEXT STEPS:**

    1️⃣ **Complete Your Profile** (5 min)
    - Add company logo
    - Fill in business details
    - Verify bank information

    2️⃣ **Create Your First Package** (10 min)
    - Use our easy package builder
    - Add photos and details
    - Set your pricing

    3️⃣ **Start Getting Inquiries!**
    - Your packages go live immediately
    - We'll send you email notifications
    - Track everything in your dashboard

    **NEED HELP?**

    📚 Getting Started Guide: [Link]
    📹 Video Tutorial: [Link]
    💬 WhatsApp Support: +966 XX XXX XXXX
    📧 Email: support@umrahpro.com

    **EXCLUSIVE LAUNCH BONUS:**

    As promised, your first 3 packages will be featured for FREE!

    We're excited to have you on board. Let's make this a successful partnership!

    JazakAllahu Khair,

    The Umrah Pro Team""", language=None)
            
            st.markdown("---")
            
            # Custom template creator
            with st.expander("➕ Create Custom Template"):
                st.markdown("### Create Your Own Template")
                
                with st.form("custom_template"):
                    custom_name = st.text_input("Template Name")
                    custom_subject = st.text_input("Subject Line")
                    custom_body = st.text_area("Email Body", height=300)
                    
                    save_template = st.form_submit_button("💾 Save Template")
                    
                    if save_template:
                        if custom_name and custom_subject and custom_body:
                            # Save to database
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            
                            c.execute('''CREATE TABLE IF NOT EXISTS email_templates
                                        (template_id TEXT PRIMARY KEY,
                                        template_name TEXT,
                                        subject_line TEXT,
                                        body TEXT,
                                        created_at TIMESTAMP)''')
                            
                            template_id = str(uuid.uuid4())
                            c.execute("INSERT INTO email_templates VALUES (?,?,?,?,?)",
                                    (template_id, custom_name, custom_subject, custom_body, datetime.now()))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Template '{custom_name}' saved!")
                        else:
                            st.error("❌ Please fill in all fields")
    
    # ========== DATA CLEANUP ==========
    
    elif admin_menu == "🗑️ Data Cleanup":
        st.markdown("## 🗑️ Database Cleanup Tools")
        st.warning("⚠️ Use these tools carefully! Deleted data cannot be recovered.")
        
        cleanup_tabs = st.tabs([
            "🧹 Quick Clean",
            "🎯 Selective Delete",
            "📊 Statistics",
            "🔄 Full Reset"
        ])
        
        # ========== TAB 1: QUICK CLEAN ==========
        
        with cleanup_tabs[0]:
            st.markdown("### 🧹 Quick Cleanup Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("""
                **Safe Cleanup Options:**
                - Remove test/demo accounts
                - Delete old rejected inquiries
                - Remove orphaned data
                - Clean inactive agents
                """)
                
                if st.button("🧹 Run Safe Cleanup", type="primary", use_container_width=True):
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    
                    with st.spinner("Cleaning..."):
                        # Remove test users
                        c.execute("DELETE FROM users WHERE username LIKE 'test%' OR email LIKE 'test%'")
                        test_users = c.rowcount
                        
                        # Remove old inquiries
                        sixty_days_ago = datetime.now() - timedelta(days=60)
                        c.execute("DELETE FROM package_inquiries WHERE inquiry_date < ? AND status='Rejected'", 
                                 (sixty_days_ago,))
                        old_inquiries = c.rowcount
                        
                        # Remove orphaned data
                        c.execute("DELETE FROM family_members WHERE user_id NOT IN (SELECT id FROM users)")
                        orphaned_family = c.rowcount
                        
                        c.execute("DELETE FROM user_progress WHERE user_id NOT IN (SELECT id FROM users)")
                        orphaned_progress = c.rowcount
                        
                        c.execute("DELETE FROM checklist_progress WHERE user_id NOT IN (SELECT id FROM users)")
                        orphaned_checklist = c.rowcount
                        
                        # Remove orphaned inquiries
                        c.execute("DELETE FROM package_inquiries WHERE package_id NOT IN (SELECT package_id FROM packages)")
                        orphaned_inquiries = c.rowcount
                        
                        conn.commit()
                        conn.close()
                    
                    st.success(f"""
                    ✅ **Cleanup Complete!**
                    
                    - Removed {test_users} test users
                    - Removed {old_inquiries} old inquiries
                    - Removed {orphaned_family} orphaned family records
                    - Removed {orphaned_progress} orphaned progress records
                    - Removed {orphaned_checklist} orphaned checklist items
                    - Removed {orphaned_inquiries} orphaned inquiries
                    """)
                    st.balloons()
            
            with col2:
                st.warning("""
                **Aggressive Cleanup:**
                - Removes ALL data
                - Keeps only structure
                - Cannot be undone
                - Creates backup first
                """)
                
                if st.button("🗑️ Delete ALL Data", type="secondary", use_container_width=True):
                    st.error("⚠️ This action requires confirmation")
                    
                    confirm_text = st.text_input("Type 'DELETE ALL DATA' to confirm:")
                    
                    if st.button("⚠️ CONFIRM DELETE", type="primary"):
                        if confirm_text == "DELETE ALL DATA":
                            import shutil
                            import os
                            
                            # Backup
                            backup_file = f'umrah_pro_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                            shutil.copy('umrah_pro.db', backup_file)
                            
                            # Delete all data
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            
                            c.execute("DELETE FROM users")
                            c.execute("DELETE FROM agent_partners")
                            c.execute("DELETE FROM packages")
                            c.execute("DELETE FROM package_inquiries")
                            c.execute("DELETE FROM family_members")
                            c.execute("DELETE FROM user_progress")
                            c.execute("DELETE FROM checklist_progress")
                            c.execute("DELETE FROM agent_credentials")
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"""
                            ✅ All data deleted!
                            
                            📦 Backup saved: {backup_file}
                            
                            Database is now empty and ready for production use.
                            """)
                            st.balloons()
                        else:
                            st.error("❌ Confirmation text doesn't match!")
        
        # ========== TAB 2: SELECTIVE DELETE ==========
        
        with cleanup_tabs[1]:
            st.markdown("### 🎯 Selective Data Deletion")
            
            delete_option = st.selectbox("What to delete?", [
                "Select option...",
                "Test Users Only",
                "Inactive Packages",
                "Old Inquiries",
                "Specific Agent & Their Data",
                "Specific User & Their Data"
            ])
            
            if delete_option == "Test Users Only":
                st.markdown("#### 🧪 Remove Test Users")
                
                conn = sqlite3.connect('umrah_pro.db')
                c = conn.cursor()
                c.execute("SELECT username, email, created_at FROM users WHERE username LIKE 'test%' OR email LIKE 'test%'")
                test_users = c.fetchall()
                conn.close()
                
                if test_users:
                    st.write(f"Found {len(test_users)} test users:")
                    for user in test_users:
                        st.write(f"• {user[0]} ({user[1]}) - Created: {user[2]}")
                    
                    if st.button("🗑️ Delete All Test Users", type="primary"):
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username LIKE 'test%' OR email LIKE 'test%'")
                        conn.commit()
                        conn.close()
                        st.success("✅ Test users deleted!")
                        st.rerun()
                else:
                    st.info("No test users found")
            
            elif delete_option == "Inactive Packages":
                st.markdown("#### 📦 Remove Inactive Packages")
                
                days_inactive = st.slider("Delete packages inactive for (days):", 7, 90, 30)
                
                cutoff_date = datetime.now() - timedelta(days=days_inactive)
                
                conn = sqlite3.connect('umrah_pro.db')
                c = conn.cursor()
                c.execute("""SELECT package_name, views, inquiries, created_at 
                            FROM packages 
                            WHERE updated_at < ? OR (views = 0 AND inquiries = 0)""", 
                         (cutoff_date,))
                inactive_packages = c.fetchall()
                conn.close()
                
                if inactive_packages:
                    st.write(f"Found {len(inactive_packages)} inactive packages:")
                    for pkg in inactive_packages[:10]:
                        st.write(f"• {pkg[0]} - {pkg[1]} views, {pkg[2]} inquiries")
                    
                    if len(inactive_packages) > 10:
                        st.caption(f"... and {len(inactive_packages) - 10} more")
                    
                    if st.button("🗑️ Delete Inactive Packages", type="primary"):
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM packages WHERE updated_at < ? OR (views = 0 AND inquiries = 0)", 
                                 (cutoff_date,))
                        conn.commit()
                        conn.close()
                        st.success("✅ Inactive packages deleted!")
                        st.rerun()
                else:
                    st.info("No inactive packages found")
            
            elif delete_option == "Old Inquiries":
                st.markdown("#### 📧 Remove Old Inquiries")
                
                days_old = st.slider("Delete inquiries older than (days):", 30, 180, 60)
                status_filter = st.multiselect("Status", ["Pending", "Contacted", "Rejected", "Cancelled"], 
                                              default=["Rejected", "Cancelled"])
                
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                if status_filter:
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    
                    placeholders = ','.join('?' * len(status_filter))
                    query = f"""SELECT customer_name, status, inquiry_date 
                               FROM package_inquiries 
                               WHERE inquiry_date < ? AND status IN ({placeholders})"""
                    
                    c.execute(query, [cutoff_date] + status_filter)
                    old_inquiries = c.fetchall()
                    conn.close()
                    
                    if old_inquiries:
                        st.write(f"Found {len(old_inquiries)} old inquiries:")
                        for inq in old_inquiries[:10]:
                            st.write(f"• {inq[0]} - {inq[1]} - {inq[2]}")
                        
                        if st.button("🗑️ Delete Old Inquiries", type="primary"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute(f"DELETE FROM package_inquiries WHERE inquiry_date < ? AND status IN ({placeholders})", 
                                     [cutoff_date] + status_filter)
                            conn.commit()
                            conn.close()
                            st.success("✅ Old inquiries deleted!")
                            st.rerun()
                    else:
                        st.info("No old inquiries found")
            
            elif delete_option == "Specific Agent & Their Data":
                st.markdown("#### 🏢 Delete Specific Agent")
                
                conn = sqlite3.connect('umrah_pro.db')
                c = conn.cursor()
                c.execute("SELECT agent_id, company_name, email FROM agent_partners")
                agents = c.fetchall()
                conn.close()
                
                if agents:
                    agent_options = {f"{a[1]} ({a[2]})": a[0] for a in agents}
                    selected_agent = st.selectbox("Select Agent to Delete", list(agent_options.keys()))
                    
                    if selected_agent:
                        agent_id = agent_options[selected_agent]
                        
                        # Show what will be deleted
                        conn = sqlite3.connect('umrah_pro.db')
                        c = conn.cursor()
                        c.execute("SELECT COUNT(*) FROM packages WHERE agent_id=?", (agent_id,))
                        package_count = c.fetchone()[0]
                        c.execute("SELECT COUNT(*) FROM package_inquiries WHERE agent_id=?", (agent_id,))
                        inquiry_count = c.fetchone()[0]
                        conn.close()
                        
                        st.warning(f"""
                        ⚠️ **This will delete:**
                        - Agent profile
                        - {package_count} packages
                        - {inquiry_count} inquiries
                        - Agent login credentials
                        
                        This action cannot be undone!
                        """)
                        
                        if st.button("🗑️ DELETE AGENT & ALL DATA", type="primary"):
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            
                            c.execute("DELETE FROM packages WHERE agent_id=?", (agent_id,))
                            c.execute("DELETE FROM package_inquiries WHERE agent_id=?", (agent_id,))
                            c.execute("DELETE FROM agent_credentials WHERE agent_id=?", (agent_id,))
                            c.execute("DELETE FROM agent_partners WHERE agent_id=?", (agent_id,))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success("✅ Agent and all related data deleted!")
                            st.rerun()
                else:
                    st.info("No agents found")
            
            elif delete_option == "Specific User & Their Data":
                st.markdown("#### 👤 Delete Specific User")
                
                search_user_delete = st.text_input("Search user by username or email:")
                
                if search_user_delete:
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    c.execute("""SELECT id, username, email FROM users 
                                WHERE username LIKE ? OR email LIKE ?""",
                             (f"%{search_user_delete}%", f"%{search_user_delete}%"))
                    users = c.fetchall()
                    conn.close()
                    
                    if users:
                        user_options = {f"{u[1]} ({u[2]})": u[0] for u in users}
                        selected_user = st.selectbox("Select User to Delete", list(user_options.keys()))
                        
                        if selected_user:
                            user_id = user_options[selected_user]
                            
                            # Show what will be deleted
                            conn = sqlite3.connect('umrah_pro.db')
                            c = conn.cursor()
                            c.execute("SELECT COUNT(*) FROM family_members WHERE user_id=?", (user_id,))
                            family_count = c.fetchone()[0]
                            c.execute("SELECT COUNT(*) FROM user_progress WHERE user_id=?", (user_id,))
                            progress_count = c.fetchone()[0]
                            conn.close()
                            
                            st.warning(f"""
                            ⚠️ **This will delete:**
                            - User account
                            - {family_count} family members
                            - {progress_count} progress records
                            - All checklist data
                            
                            This action cannot be undone!
                            """)
                            
                            if st.button("🗑️ DELETE USER & ALL DATA", type="primary"):
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                
                                c.execute("DELETE FROM family_members WHERE user_id=?", (user_id,))
                                c.execute("DELETE FROM user_progress WHERE user_id=?", (user_id,))
                                c.execute("DELETE FROM checklist_progress WHERE user_id=?", (user_id,))
                                c.execute("DELETE FROM bookmarks WHERE user_id=?", (user_id,))
                                c.execute("DELETE FROM users WHERE id=?", (user_id,))
                                
                                conn.commit()
                                conn.close()
                                
                                st.success("✅ User and all related data deleted!")
                                st.rerun()
                    else:
                        st.info("No users found")
        
        # ========== TAB 3: STATISTICS ==========
        
        with cleanup_tabs[2]:
            st.markdown("### 📊 Database Statistics")
            
            conn = sqlite3.connect('umrah_pro.db')
            c = conn.cursor()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                c.execute("SELECT COUNT(*) FROM users")
                user_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'test%'")
                test_user_count = c.fetchone()[0]
                
                st.metric("👤 Total Users", user_count)
                if test_user_count > 0:
                    st.caption(f"⚠️ {test_user_count} test users")
            
            with col2:
                c.execute("SELECT COUNT(*) FROM agent_partners")
                agent_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM agent_partners WHERE agent_id NOT IN (SELECT DISTINCT agent_id FROM packages)")
                inactive_agents = c.fetchone()[0]
                
                st.metric("🏢 Total Agents", agent_count)
                if inactive_agents > 0:
                    st.caption(f"⚠️ {inactive_agents} inactive")
            
            with col3:
                c.execute("SELECT COUNT(*) FROM packages")
                package_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM packages WHERE views = 0")
                zero_view_packages = c.fetchone()[0]
                
                st.metric("📦 Total Packages", package_count)
                if zero_view_packages > 0:
                    st.caption(f"⚠️ {zero_view_packages} with 0 views")
            
            st.markdown("---")
            
            col4, col5, col6 = st.columns(3)
            
            with col4:
                c.execute("SELECT COUNT(*) FROM package_inquiries")
                inquiry_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM package_inquiries WHERE status='Rejected'")
                rejected_count = c.fetchone()[0]
                
                st.metric("📧 Total Inquiries", inquiry_count)
                if rejected_count > 0:
                    st.caption(f"{rejected_count} rejected")
            
            with col5:
                c.execute("SELECT COUNT(*) FROM family_members")
                family_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM family_members WHERE user_id NOT IN (SELECT id FROM users)")
                orphaned_family = c.fetchone()[0]
                
                st.metric("👨‍👩‍👧‍👦 Family Members", family_count)
                if orphaned_family > 0:
                    st.caption(f"⚠️ {orphaned_family} orphaned")
            
            with col6:
                # Database size
                import os
                if os.path.exists('umrah_pro.db'):
                    db_size = os.path.getsize('umrah_pro.db') / (1024 * 1024)  # MB
                    st.metric("💾 Database Size", f"{db_size:.2f} MB")
            
            conn.close()
            
            st.markdown("---")
            
            # Recent activity
            st.markdown("### 📈 Recent Activity (Last 7 Days)")
            
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            conn = sqlite3.connect('umrah_pro.db')
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM users WHERE created_at > ?", (seven_days_ago,))
            new_users = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM packages WHERE created_at > ?", (seven_days_ago,))
            new_packages = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM package_inquiries WHERE inquiry_date > ?", (seven_days_ago,))
            new_inquiries = c.fetchone()[0]
            
            conn.close()
            
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            
            with stat_col1:
                st.info(f"**New Users:** {new_users}")
            
            with stat_col2:
                st.info(f"**New Packages:** {new_packages}")
            
            with stat_col3:
                st.info(f"**New Inquiries:** {new_inquiries}")
        
        # ========== TAB 4: FULL RESET ==========
        
        with cleanup_tabs[3]:
            st.markdown("### 🔄 Full Database Reset")
            
            st.error("""
            ⚠️ **DANGER ZONE**
            
            This will completely reset the database to a clean state:
            - All users deleted
            - All agents deleted
            - All packages deleted
            - All inquiries deleted
            - All progress data deleted
            
            **Admin accounts will NOT be deleted**
            
            A backup will be created automatically.
            """)
            
            st.markdown("---")
            
            confirm_reset = st.text_input("Type 'RESET DATABASE' to confirm:")
            
            if st.button("🔄 RESET ENTIRE DATABASE", type="primary", use_container_width=True):
                if confirm_reset == "RESET DATABASE":
                    import shutil
                    
                    # Create backup
                    backup_file = f'umrah_pro_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                    shutil.copy('umrah_pro.db', backup_file)
                    
                    # Reset database
                    conn = sqlite3.connect('umrah_pro.db')
                    c = conn.cursor()
                    
                    # Delete all data except admin credentials
                    c.execute("DELETE FROM users")
                    c.execute("DELETE FROM agent_partners")
                    c.execute("DELETE FROM agent_credentials")
                    c.execute("DELETE FROM packages")
                    c.execute("DELETE FROM package_inquiries")
                    c.execute("DELETE FROM family_members")
                    c.execute("DELETE FROM user_progress")
                    c.execute("DELETE FROM checklist_progress")
                    c.execute("DELETE FROM bookmarks")
                    
                    conn.commit()
                    conn.close()
                    
                    st.success(f"""
                    ✅ **Database Reset Complete!**
                    
                    📦 **Backup saved:** {backup_file}
                    
                    **Database is now clean:**
                    - All user data deleted
                    - All agent data deleted
                    - All packages deleted
                    - All inquiries deleted
                    - Admin accounts preserved
                    
                    Ready for production use! 🚀
                    """)
                    st.balloons()
                else:
                    st.error("❌ Confirmation text doesn't match!")
    
    # ========== SETTINGS ==========
    
    elif admin_menu == "⚙️ Settings":
        st.markdown("## ⚙️ System Settings")
        
        settings_tabs = st.tabs(["👨‍💼 Admin Accounts", "🔑 Agent Logins", "💾 Backup & Restore"])
        
        with settings_tabs[0]:
            st.markdown("### 👨‍💼 Admin Accounts")
            
            # List admins
            admins = get_all_admins()
            
            st.write(f"**Total Admins:** {len(admins)}")
            
            if admins:
                for admin in admins:
                    with st.expander(f"👤 {admin['username']} ({admin['role']})"):
                        st.write(f"**Admin ID:** {admin['admin_id']}")
                        st.write(f"**Created:** {admin['created_at']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            new_password = st.text_input(
                                "New Password",
                                type="password",
                                key=f"pwd_{admin['admin_id']}"
                            )
                            
                            if st.button("🔑 Update Password", key=f"upd_{admin['admin_id']}"):
                                if update_admin_password(admin['admin_id'], new_password):
                                    st.success("✅ Password updated!")
                                else:
                                    st.error("❌ Failed to update password")
                        
                        with col2:
                            if admin['admin_id'] != st.session_state.admin_id:
                                if st.button("🗑️ Delete Admin", key=f"del_{admin['admin_id']}"):
                                    if delete_admin(admin['admin_id']):
                                        st.success("✅ Admin deleted!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete admin")
                            else:
                                st.info("Cannot delete yourself")
            
            st.markdown("---")
            
            # Create new admin
            with st.expander("➕ Create New Admin"):
                new_admin_username = st.text_input("Username", key="new_admin_user")
                new_admin_password = st.text_input("Password", type="password", key="new_admin_pwd")
                new_admin_role = st.selectbox("Role", ["admin", "super_admin", "moderator"])
                
                if st.button("Create Admin", type="primary"):
                    if create_admin(new_admin_username, new_admin_password, new_admin_role):
                        st.success("✅ New admin created!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create admin")
        
        with settings_tabs[1]:
            st.markdown("### 🔑 Create Agent Login Credentials")
            
            # Get agents without credentials
            conn = sqlite3.connect('umrah_pro.db')
            c = conn.cursor()
            c.execute("""SELECT a.agent_id, a.company_name, a.agent_name, a.email
                        FROM agent_partners a
                        WHERE a.agent_id NOT IN (SELECT agent_id FROM agent_credentials)""")
            agents_no_creds = c.fetchall()
            conn.close()
            
            if agents_no_creds:
                st.info(f"**{len(agents_no_creds)} agents** need login credentials")
                
                agent_options = {f"{a[1]} - {a[3]}": a for a in agents_no_creds}
                selected_agent_display = st.selectbox("Select Agent", list(agent_options.keys()))
                
                if selected_agent_display:
                    agent = agent_options[selected_agent_display]
                    agent_id = agent[0]
                    agent_company = agent[1]
                    agent_name = agent[2]
                    agent_email = agent[3]
                    
                    with st.form(f"create_agent_login"):
                        agent_username = st.text_input("Username for Agent", 
                            value=agent_company.lower().replace(" ", ""))
                        agent_password = st.text_input("Password", type="password")
                        confirm_agent_password = st.text_input("Confirm Password", type="password")
                        
                        send_welcome = st.checkbox("Send welcome email to agent", value=True)
                        
                        submit_agent_login = st.form_submit_button("🔑 Create Login", type="primary")
                        
                        if submit_agent_login:
                            if len(agent_password) < 8:
                                st.error("❌ Password must be at least 8 characters")
                            elif agent_password != confirm_agent_password:
                                st.error("❌ Passwords don't match")
                            else:
                                conn = sqlite3.connect('umrah_pro.db')
                                c = conn.cursor()
                                
                                try:
                                    # Create login
                                    c.execute("""INSERT INTO agent_credentials VALUES (?,?,?,?)""",
                                             (agent_id, agent_username, hash_password(agent_password), datetime.now()))
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success(f"✅ Login created for {agent_company}!")
                                    
                                    # Display credentials
                                    st.info(f"""
                                    **Login Credentials Created:**
                                    
                                    **Username:** {agent_username}  
                                    **Password:** {agent_password}
                                    
                                    📧 Agent Email: {agent_email}
                                    """)
                                    
                                    # Send welcome email if checkbox is checked
                                    if send_welcome:
                                        try:
                                            from email_service import EmailService
                                            
                                            if 'SENDGRID_API_KEY' in st.secrets:
                                                email_service = EmailService(api_key=st.secrets["SENDGRID_API_KEY"])
                                                
                                                agent_data = {
                                                    'company_name': agent_company,
                                                    'contact_name': agent_name,
                                                    'email': agent_email,
                                                    'username': agent_username
                                                }
                                                
                                                with st.spinner("Sending welcome email..."):
                                                    result = email_service.send_welcome_email(
                                                        agent_email,
                                                        agent_data
                                                    )
                                                
                                                if result['success']:
                                                    st.success(f"✅ Welcome email sent to {agent_email}!")
                                                    st.balloons()
                                                else:
                                                    st.warning(f"⚠️ Login created but email failed: {result.get('error')}")
                                            else:
                                                st.warning("⚠️ SendGrid not configured. Login created but no email sent.")
                                        
                                        except ImportError:
                                            st.warning("⚠️ Email service not installed. Login created but no email sent.")
                                        except Exception as e:
                                            st.warning(f"⚠️ Login created but email error: {e}")
                                    
                                    st.rerun()
                                
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                                finally:
                                    if 'conn' in locals():
                                        conn.close()
            else:
                st.success("✅ All agents have login credentials!")
        
        with settings_tabs[2]:
            st.markdown("### 💾 Backup & Restore")
            
            import os
            
            # List backups
            backups = [f for f in os.listdir('.') if f.startswith('umrah_pro_backup_') and f.endswith('.db')]
            
            if backups:
                st.write(f"**Found {len(backups)} backup files:**")
                for backup in sorted(backups, reverse=True)[:10]:
                    backup_size = os.path.getsize(backup) / (1024 * 1024)
                    st.write(f"📦 {backup} ({backup_size:.2f} MB)")
            else:
                st.info("No backup files found")
            
            st.markdown("---")
            
            # Create new backup
            if st.button("💾 Create Backup Now", type="primary", use_container_width=True):
                import shutil
                
                backup_file = f'umrah_pro_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                shutil.copy('umrah_pro.db', backup_file)
                

                st.success(f"✅ Backup created: {backup_file}")
