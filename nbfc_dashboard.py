import streamlit as st
from datetime import datetime, timedelta
import calendar
import requests
import time
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# PASSWORD PROTECTION
PASSWORD = "nbfcsecure123"
TOKEN_FILE = "auth_tokens.json"

# Token management functions
def generate_token():
    """Generate a secure token"""
    timestamp = str(datetime.now().timestamp())
    random_str = os.urandom(16).hex()
    return hashlib.sha256((timestamp + random_str).encode()).hexdigest()

def save_token(token):
    """Save token with expiry date"""
    tokens = load_tokens()
    expiry = (datetime.now() + timedelta(days=10)).isoformat()
    tokens[token] = expiry
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

def load_tokens():
    """Load existing tokens"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def validate_token(token):
    """Check if token is valid and not expired"""
    if not token:
        return False
    tokens = load_tokens()
    if token in tokens:
        try:
            expiry = datetime.fromisoformat(tokens[token])
            if datetime.now() < expiry:
                return True
            else:
                del tokens[token]
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(tokens, f)
        except:
            pass
    return False

def clean_expired_tokens():
    """Remove all expired tokens"""
    tokens = load_tokens()
    now = datetime.now()
    tokens = {k: v for k, v in tokens.items() 
              if datetime.fromisoformat(v) > now}
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

clean_expired_tokens()

# Check for token in query parameters
query_params = st.query_params
auth_token = query_params.get("auth_token", None)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if auth_token and validate_token(auth_token):
    st.session_state.authenticated = True

# Password authentication
if not st.session_state.authenticated:
    password = st.text_input("Enter password to access dashboard:", type="password")
    if password == PASSWORD:
        st.session_state.authenticated = True
        new_token = generate_token()
        save_token(new_token)
        st.query_params["auth_token"] = new_token
        st.success("Access granted. Welcome!")
        st.rerun()
    elif password:
        st.error("Incorrect password")
    st.stop()

# Set page configuration
st.set_page_config(
    page_title="Brand Dashboards",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Metabase Configuration
METABASE_URL = "http://43.205.95.106:3000"
METABASE_USERNAME = "shubham.garg@fintechcloud.in"
METABASE_PASSWORD = "Qwerty@12345"

# Function to get Metabase session token
@st.cache_data(ttl=1800, show_spinner=False)
def get_metabase_token():
    """Get authentication token from Metabase"""
    try:
        response = requests.post(
            f"{METABASE_URL}/api/session",
            json={
                "username": METABASE_USERNAME,
                "password": METABASE_PASSWORD
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json()['id']
        return None
    except:
        return None

# Optimized fetch function with timeout
def fetch_metabase_metric_fast(card_id, token):
    """Fast fetch with reduced timeout"""
    if not token or not card_id:
        return None
    
    try:
        headers = {
            "X-Metabase-Session": token,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{METABASE_URL}/api/card/{card_id}/query/json",
            headers=headers,
            json={"parameters": []},
            timeout=15  # Reduced timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                first_row = data[0]
                if isinstance(first_row, dict):
                    return list(first_row.values())[0] if first_row else None
                return first_row
        return None
    except:
        return None

def format_value(value, is_percentage=False):
    """Format value for display"""
    if value is None:
        return "₹0.00" if not is_percentage else "0%"
    
    if is_percentage:
        if isinstance(value, (int, float)):
            return f"{value:.1f}%"
        return str(value)
    
    if isinstance(value, (int, float)):
        if value >= 10000000:
            return f"₹{value/10000000:.2f} Cr"
        elif value >= 100000:
            return f"₹{value/100000:.2f} L"
        else:
            return f"₹{value:,.0f}"
    return "₹0.00"

def parse_metric_value(value_str):
    """Parse formatted metric value back to number"""
    if value_str is None or value_str == "₹0.00":
        return 0
    if isinstance(value_str, (int, float)):
        return value_str
    return 0

# Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: #ffffff;
    }
    
    .main {
        background: transparent;
        padding: 0;
    }
    
    .block-container {
        padding: 2rem 3rem;
        max-width: 1600px;
        background: transparent;
    }
    
    section[data-testid="stAppViewContainer"] {
        background: #ffffff;
    }
    
    [data-testid="stHeader"] {
        background: transparent;
    }
    
    .header-section {
        margin-bottom: 3rem;
        padding-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
    }
    
    .header-left {
        flex: 1;
        text-align: center;
    }
    
    .header-left-score {
        position: absolute;
        left: 3rem;
        top: 2rem;
    }
    
    .sg-score-card {
        font-size: 1rem;
        font-weight: 700;
        color: #2563eb;
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: 2px solid #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .sg-score-value {
        font-size: 1.1rem;
        font-weight: 800;
        color: #1e40af;
    }
    
    .header-right {
        position: absolute;
        right: 3rem;
        top: 2rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .current-date {
        font-size: 1.1rem;
        font-weight: 600;
        color: #64748b;
        background: #f1f5f9;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
    }
    
    .days-left {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f59e0b;
        background: #fef3c7;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        border: 2px solid #fbbf24;
        text-align: center;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        color: #2563eb;
        margin-bottom: 1rem;
        letter-spacing: -1px;
        line-height: 1.1;
    }
    
    .title-underline {
        width: 240px;
        height: 6px;
        background: linear-gradient(to right, #3b82f6, #8b5cf6);
        border-radius: 3px;
        margin: 0 auto;
    }
    
    .brand-card {
        border-radius: 16px;
        padding: 1.25rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .brand-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .card-blue {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    }
    
    .card-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }
    
    .card-orange {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    
    .card-teal {
        background: linear-gradient(135deg, #14b8a6 0%, #0d9488 100%);
    }
    
    .card-purple {
        background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    }
    
    .card-indigo {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    }
    
    .card-red {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    .card-pink {
        background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.5rem;
    }
    
    .card-label {
        font-size: 1.1rem;
        font-weight: 800;
        color: rgba(255, 255, 255, 0.95);
        text-transform: capitalize;
        letter-spacing: 0.3px;
    }
    
    .card-icon {
        font-size: 1.5rem;
        background: rgba(255, 255, 255, 0.25);
        padding: 0.4rem;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
        min-height: 40px;
    }
    
    .card-description {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.95);
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    
    .card-target {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.85);
        font-weight: 500;
        margin-bottom: 0.2rem;
    }
    
    .card-metric {
        font-size: 0.88rem;
        color: rgba(255, 255, 255, 1);
        font-weight: 800;
        background: rgba(255, 255, 255, 0.25);
        padding: 0.35rem 0.7rem;
        border-radius: 8px;
        display: inline-block;
        margin-top: 0.25rem;
        margin-right: 0.35rem;
        border: 2px solid rgba(255, 255, 255, 0.3);
        line-height: 1.3;
    }
    
    a {
        text-decoration: none !important;
        color: inherit !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    header {visibility: hidden;}
    
    [data-testid="column"] {
        padding: 0 0.4rem;
    }
    
    @media (max-width: 768px) {
        .header-section {
            flex-direction: column;
            gap: 1rem;
        }
        
        .header-left-score {
            position: relative;
            left: auto;
            top: auto;
            margin-bottom: 1rem;
        }
        
        .header-right {
            position: relative;
            right: auto;
            top: auto;
        }
        
        .brand-card {
            padding: 1.5rem;
            min-height: 200px;
        }
        .main-title {
            font-size: 2.5rem;
        }
        .title-underline {
            width: 150px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Get current date
ist_timezone = ZoneInfo("Asia/Kolkata")
now = datetime.now(ist_timezone)
current_date = now.strftime("%d %B %Y")
current_day = now.day
days_in_month = calendar.monthrange(now.year, now.month)[1]
days_left = days_in_month - current_day

# Get Metabase token
metabase_token = get_metabase_token()

# Define brand dashboards
brand_dashboards = [
    {"name": "FundoBaBa", "url": "https://tinyurl.com/5n9abwcx", "icon": "💼", "description": "Mumbai Team", "target": "₹25 Cr", "target_value": 25, "metabase_card_id": 441, "pmtd_card_id": 456, "collection_card_id": 453, "color": "blue"},
    {"name": "FastPaise", "url": "https://tinyurl.com/59dtjd88", "icon": "⚡", "description": "Ashutosh", "target": "₹18 Cr", "target_value": 18, "metabase_card_id": 432, "pmtd_card_id": 460, "collection_card_id": 445, "color": "green"},
    {"name": "SnapPaisa", "url": "https://tinyurl.com/2p9mdevt", "icon": "📸", "description": "Mumbai Team", "target": "₹18 Cr", "target_value": 18, "metabase_card_id": 437, "pmtd_card_id": 464, "collection_card_id": 449, "color": "purple"},
    {"name": "BlinkR", "url": "", "icon": "⚡", "description": "Anurag", "target": "₹15 Cr", "target_value": 15, "metabase_card_id": None, "pmtd_card_id": None, "collection_card_id": None, "color": "indigo", "manual_mtd": 65049130, "manual_pmtd": 49800000, "manual_collection": "83.0%"},
    {"name": "Duniya", "url": "https://tinyurl.com/nhzvpuy6", "icon": "🌍", "description": "Harsh", "target": "₹15 Cr", "target_value": 15, "metabase_card_id": 433, "pmtd_card_id": 459, "collection_card_id": 444, "color": "blue"},
    {"name": "Tejas", "url": "https://tinyurl.com/29sb8js4", "icon": "✨", "description": "Nitin", "target": "₹15 Cr", "target_value": 15, "metabase_card_id": 439, "pmtd_card_id": 466, "collection_card_id": 451, "color": "red"},
    {"name": "Salary 4 Sure", "url": "https://tinyurl.com/bdfdufas", "icon": "💸", "description": "Vivek & Pranit", "target": "₹15 Cr", "target_value": 15, "metabase_card_id": 436, "pmtd_card_id": 463, "collection_card_id": 448, "color": "orange"},
    {"name": "Salary Setu", "url": "https://tinyurl.com/2we6eyvf", "icon": "💵", "description": "Prajwal", "target": "₹11 Cr", "target_value": 11, "metabase_card_id": 443, "pmtd_card_id": 458, "collection_card_id": 455, "color": "green"},
    {"name": "Salary Adda", "url": "https://tinyurl.com/4cd79c5b", "icon": "💳", "description": "Asim", "target": "₹10 Cr", "target_value": 10, "metabase_card_id": 442, "pmtd_card_id": 457, "collection_card_id": 454, "color": "teal"},
    {"name": "Zepto Finance", "url": "https://tinyurl.com/44cj83rw", "icon": "⚡", "description": "Arvind Jaiswal", "target": "₹9 Cr", "target_value": 9, "metabase_card_id": 440, "secondary_mtd_card_id": 476, "pmtd_card_id": 467, "secondary_pmtd_card_id": 477, "collection_card_id": 452, "color": "pink"},
    {"name": "Paisa on Salary", "url": "https://tinyurl.com/fpxzjfsk", "icon": "💰", "description": "Ajay", "target": "₹5 Cr", "target_value": 5, "metabase_card_id": 435, "pmtd_card_id": 462, "collection_card_id": 447, "color": "teal"},
    {"name": "Squid Loan", "url": "https://tinyurl.com/mphk5xpc", "icon": "🦑", "description": "Shashikant", "target": "₹5 Cr", "target_value": 5, "metabase_card_id": 438, "pmtd_card_id": 465, "collection_card_id": 450, "color": "indigo"},
    {"name": "Jhatpat", "url": "https://tinyurl.com/294bc6ns", "icon": "🚀", "description": "Vivek", "target": "₹3 Cr", "target_value": 3, "metabase_card_id": 434, "pmtd_card_id": 461, "collection_card_id": 446, "color": "orange"},
    {"name": "Minutes Loan", "url": "https://tinyurl.com/yj3mss22", "icon": "⏱️", "description": "Pranit", "target": "₹3 Cr", "target_value": 3, "metabase_card_id": 470, "pmtd_card_id": 471, "collection_card_id": None, "color": "indigo"},
    {"name": "Paisa Pop", "url": "https://tinyurl.com/4jd65fut", "icon": "🎈", "description": "Priyanka", "target": "₹3 Cr", "target_value": 3, "metabase_card_id": 473, "pmtd_card_id": 474, "collection_card_id": None, "color": "pink"},
    {"name": "Qua Loans", "url": "https://tinyurl.com/bdhj328e", "icon": "🔷", "description": "Harsha & Nitin", "target": "₹3 Cr", "target_value": 3, "metabase_card_id": None, "pmtd_card_id": None, "collection_card_id": None, "color": "blue", "manual_mtd": 26458000, "manual_pmtd": 14700000, "manual_collection": "74.0%"},
    {"name": "Salary 4 You", "url": "https://tinyurl.com/p43ptyp4", "icon": "💵", "description": "Nadeem", "target": "₹3 Cr", "target_value": 3, "metabase_card_id": 486, "pmtd_card_id": 488, "collection_card_id": 491, "color": "green"},
    {"name": "Udhaar Portal", "url": "https://tinyurl.com/wb6n38dx", "icon": "🏦", "description": "Manas", "target": "₹1 Cr", "target_value": 1, "metabase_card_id": 498, "pmtd_card_id": 500, "collection_card_id": 499, "color": "teal"},
    {"name": "Rupee Hype", "url": "https://tinyurl.com/39ztaew8", "icon": "🚀", "description": "Nadeem", "target": "₹1 Cr", "target_value": 1, "metabase_card_id": 485, "pmtd_card_id": 487, "collection_card_id": 492, "color": "purple"}
]

# Parallel data fetching function
def fetch_brand_data(brand, token):
    """Fetch all data for a single brand in parallel"""
    result = {
        'name': brand['name'],
        'mtd': 0,
        'pmtd': 0,
        'collection': "N/A"
    }
    
    # Handle manual entries
    if brand.get('manual_mtd') is not None:
        result['mtd'] = brand['manual_mtd']
        result['pmtd'] = brand.get('manual_pmtd', 0)
        result['collection'] = brand.get('manual_collection', "N/A")
        return result
    
    # Fetch MTD
    if brand.get('metabase_card_id'):
        mtd_value = fetch_metabase_metric_fast(brand['metabase_card_id'], token)
        if mtd_value:
            result['mtd'] = mtd_value
        
        # Add secondary MTD if exists
        if brand.get('secondary_mtd_card_id'):
            secondary_mtd = fetch_metabase_metric_fast(brand['secondary_mtd_card_id'], token)
            if secondary_mtd:
                result['mtd'] += secondary_mtd
    
    # Fetch PMTD
    if brand.get('pmtd_card_id'):
        pmtd_value = fetch_metabase_metric_fast(brand['pmtd_card_id'], token)
        if pmtd_value:
            result['pmtd'] = pmtd_value
        
        # Add secondary PMTD if exists
        if brand.get('secondary_pmtd_card_id'):
            secondary_pmtd = fetch_metabase_metric_fast(brand['secondary_pmtd_card_id'], token)
            if secondary_pmtd:
                result['pmtd'] += secondary_pmtd
    
    # Fetch Collection
    if brand.get('collection_card_id'):
        collection_value = fetch_metabase_metric_fast(brand['collection_card_id'], token)
        if collection_value is not None:
            result['collection'] = f"{collection_value:.1f}%" if isinstance(collection_value, (int, float)) else str(collection_value)
    
    return result

# Show header immediately
sg_score = "₹137 Cr"

st.markdown(f"""
    <div class="header-section">
        <div class="header-left-score">
            <div class="sg-score-card">
                <span>⭐ Month-End Projection:</span>
                <span class="sg-score-value">{sg_score}</span>
            </div>
        </div>
        <div class="header-left">
            <div class="main-title">Performance Console</div>
            <div class="title-underline"></div>
        </div>
        <div class="header-right">
            <div class="current-date">📅 {current_date}</div>
            <div class="days-left">⏰ {days_left} days left in month</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Fetch data in parallel using ThreadPoolExecutor
with st.spinner("Loading brand data..."):
    brand_data = {}
    
    # Use parallel execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_brand = {executor.submit(fetch_brand_data, brand, metabase_token): brand for brand in brand_dashboards}
        
        for future in as_completed(future_to_brand):
            try:
                result = future.result()
                brand_data[result['name']] = result
            except:
                pass

# Calculate totals
total_disbursement = sum(brand_data.get(b['name'], {}).get('mtd', 0) for b in brand_dashboards)
total_pmtd_disbursement = sum(brand_data.get(b['name'], {}).get('pmtd', 0) for b in brand_dashboards)
total_target = sum(b['target_value'] for b in brand_dashboards)

mom_growth = total_disbursement - total_pmtd_disbursement
mom_growth_percentage = (mom_growth / total_pmtd_disbursement * 100) if total_pmtd_disbursement > 0 else 0

# Calculate MTD Target
def calculate_mtd_target(current_day, total_target_cr):
    total_target_amount = total_target_cr * 10000000
    
    if 1 <= current_day <= 5:
        mtd_percentage = 21.23 * (current_day / 5) / 100
    elif 6 <= current_day <= 10:
        days_in_bracket = current_day - 5
        mtd_percentage = (21.23 + 11.61 * (days_in_bracket / 5)) / 100
    elif 11 <= current_day <= 15:
        days_in_bracket = current_day - 10
        mtd_percentage = (21.23 + 11.61 + 8.13 * (days_in_bracket / 5)) / 100
    elif 16 <= current_day <= 20:
        days_in_bracket = current_day - 15
        mtd_percentage = (21.23 + 11.61 + 8.13 + 7.75 * (days_in_bracket / 5)) / 100
    elif 21 <= current_day <= 25:
        days_in_bracket = current_day - 20
        mtd_percentage = (21.23 + 11.61 + 8.13 + 7.75 + 12.96 * (days_in_bracket / 5)) / 100
    else:
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_in_bracket = current_day - 25
        total_days_in_bracket = days_in_month - 25
        mtd_percentage = (21.23 + 11.61 + 8.13 + 7.75 + 12.96 + 38.31 * (days_in_bracket / total_days_in_bracket)) / 100
    
    return total_target_amount * mtd_percentage

mtd_target_amount = calculate_mtd_target(current_day, total_target)
mtd_shortfall = mtd_target_amount - total_disbursement
shortfall_percentage = (abs(mtd_shortfall) / mtd_target_amount * 100) if mtd_target_amount > 0 else 0

# Display summary cards
cols = st.columns(3, gap="medium")

with cols[0]:
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    border-radius: 20px; 
                    padding: 2rem; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    height: 380px;
                    display: flex;
                    flex-direction: column;">
            <div style="font-size: 1.5rem; color: #ffffff; font-weight: 800; margin-bottom: 1.5rem; text-align: center;">
                🌍 Monthly Goal Status
            </div>
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total Target</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #3b82f6;">₹{total_target} Cr</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total MTD Disbursement</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #10b981;">{format_value(total_disbursement)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Achievement</div>
                    <div style="font-size: 2rem; font-weight: 900; color: {'#10b981' if total_disbursement >= total_target * 10000000 else '#f59e0b'};">
                        {(total_disbursement / (total_target * 10000000) * 100):.1f}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    border-radius: 20px; 
                    padding: 2rem; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    height: 380px;
                    display: flex;
                    flex-direction: column;">
            <div style="font-size: 1.5rem; color: #ffffff; font-weight: 800; margin-bottom: 1.5rem; text-align: center;">
                📈 Monthly Shortfall
            </div>
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total MTD Target</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #3b82f6;">{format_value(mtd_target_amount)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total MTD Disbursement</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #10b981;">{format_value(total_disbursement)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Shortfall (Amount and %)</div>
                    <div style="font-size: 2rem; font-weight: 900; color: {'#ef4444' if mtd_shortfall > 0 else '#10b981'};">
                        {format_value(abs(mtd_shortfall))}
                    </div>
                    <div style="font-size: 1.1rem; color: rgba(255, 255, 255, 0.8); font-weight: 700; margin-top: 0.3rem;">
                        {'↓' if mtd_shortfall > 0 else '↑'} {shortfall_percentage:.1f}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    border-radius: 20px; 
                    padding: 2rem; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.1);
                    height: 380px;
                    display: flex;
                    flex-direction: column;">
            <div style="font-size: 1.5rem; color: #ffffff; font-weight: 800; margin-bottom: 1.5rem; text-align: center;">
                🏆 MoM Growth
            </div>
            <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center; gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total PMTD Disbursement</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #8b5cf6;">{format_value(total_pmtd_disbursement)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">Total MTD Disbursement</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #10b981;">{format_value(total_disbursement)}</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.6); font-weight: 600;">MOM Growth (Amount and %)</div>
                    <div style="font-size: 2rem; font-weight: 900; color: {'#10b981' if mom_growth >= 0 else '#ef4444'};">
                        {format_value(abs(mom_growth))}
                    </div>
                    <div style="font-size: 1.1rem; color: rgba(255, 255, 255, 0.8); font-weight: 700; margin-top: 0.3rem;">
                        {'↑' if mom_growth >= 0 else '↓'} {abs(mom_growth_percentage):.1f}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Display brand cards
for i in range(0, len(brand_dashboards), 4):
    cols = st.columns(4, gap="large")
    
    for j in range(4):
        if i + j < len(brand_dashboards):
            brand = brand_dashboards[i + j]
            data = brand_data.get(brand['name'], {'mtd': 0, 'pmtd': 0, 'collection': 'N/A'})
            
            mtd_value = data['mtd']
            target_value = brand['target_value'] * 10000000
            yet_to_achieve = target_value - mtd_value
            yet_to_achieve_pct = (yet_to_achieve / target_value * 100) if target_value > 0 else 0
            
            if yet_to_achieve > 0:
                yet_to_achieve_str = f"{format_value(yet_to_achieve)} ({yet_to_achieve_pct:.0f}%)"
            else:
                yet_to_achieve_str = "Target Achieved! 🎉"
            
            with cols[j]:
                st.markdown(f"""
                    <a href="{brand['url']}" target="_blank">
                        <div class="brand-card card-{brand['color']}">
                            <div class="card-header">
                                <div class="card-label">{brand['name']}</div>
                                <div class="card-icon">{brand['icon']}</div>
                            </div>
                            <div>
                                <div class="card-description">👤 {brand['description']}</div>
                                <div class="card-target">🎯 Target: {brand['target']}</div>
                                <div style="display: flex; flex-wrap: wrap; gap: 0.25rem; margin-top: 0.3rem;">
                                    <div class="card-metric">📊 MTD Disb: {format_value(mtd_value)}</div>
                                    <div class="card-metric">💰 Collection MTD: {data['collection']}</div>
                                </div>
                                <div style="margin-top: 0.25rem;">
                                    <div class="card-metric">🎯 Yet to Achieve: {yet_to_achieve_str}</div>
                                </div>
                            </div>
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
    
    if i + 4 < len(brand_dashboards):
        st.markdown("<br>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🔧 System Status")
    
    if metabase_token:
        st.success("✅ Metabase Connected")
    else:
        st.error("❌ Connection Failed")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.markdown("---")
    st.caption(f"Last Updated: {datetime.now(ist_timezone).strftime('%H:%M:%S')}")
