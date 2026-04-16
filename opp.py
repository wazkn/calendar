import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
from streamlit_option_menu import option_menu

# ==========================================
# CONFIG & CSS
# ==========================================
st.set_page_config(page_title="Nexus Hub", page_icon="🌌", layout="wide")

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        
        /* Modern Dark Theme - Linear Inspired */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #0A0A0A !important; /* Deep OLED Black */
            color: #EDEDED !important;
        }

        /* Expander & Form Backgrounds */
        [data-testid="stForm"], [data-testid="stExpander"] {
            background-color: #121212 !important;
            border: 1px solid #262626 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4) !important;
        }

        /* Inputs & Selectboxes */
        .stTextInput > div > div > input, 
        .stDateInput > div > div > input, 
        .stTimeInput > div > div > input,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input {
            background-color: #171717 !important;
            color: #EDEDED !important;
            border-radius: 8px !important;
            border: 1px solid #333 !important;
            transition: border-color 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus {
            border-color: #3B82F6 !important;
            box-shadow: 0 0 0 1px #3B82F6 !important;
        }

        /* Metric Cards */
        div[data-testid="metric-container"] {
            background-color: #121212;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #262626;
            border-left: 4px solid #3B82F6; 
        }

        /* Buttons */
        .stButton > button {
            background-color: #171717 !important;
            color: #EDEDED !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #262626 !important;
            border-color: #444 !important;
        }
        
        /* Primary Submit Button */
        [data-testid="stFormSubmitButton"] > button {
            background-color: #3B82F6 !important;
            color: white !important;
            border: none !important;
        }
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: #2563EB !important;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #0F0F0F !important;
            border-right: 1px solid #262626 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# DATABASE SETUP
# ==========================================
def init_db():
    conn = sqlite3.connect('nexus_data.db', check_same_thread=False)
    c = conn.cursor()
    
    # Events Table
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, start_time TEXT, end_time TEXT, 
                  category TEXT, color TEXT)''')
                  
    # Goals Table
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT, current INTEGER, target INTEGER, category TEXT)''')
                  
    # Categories Table (Dynamic Settings)
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  name TEXT UNIQUE, color TEXT)''')
                  
    # Seed default categories if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_cats = [("Deep Work", "#3B82F6"), ("Health", "#10B981"), ("Personal", "#F59E0B"), ("Meetings", "#8B5CF6")]
        c.executemany("INSERT INTO categories (name, color) VALUES (?, ?)", default_cats)
        
    conn.commit()
    return conn

conn = init_db()

# ==========================================
# DB HELPER FUNCTIONS
# ==========================================
def get_categories():
    return pd.read_sql_query("SELECT * FROM categories", conn)

def add_category(name, color):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_events():
    return pd.read_sql_query("SELECT * FROM events", conn)

def add_event(title, start, end, category, color):
    c = conn.cursor()
    c.execute("""SELECT id FROM events WHERE 
                 (start_time < ? AND end_time > ?) OR
                 (start_time < ? AND end_time > ?) OR
                 (start_time >= ? AND end_time <= ?)""", 
              (end, start, end, start, start, end))
    if c.fetchone():
        return False 
    
    c.execute("INSERT INTO events (title, start_time, end_time, category, color) VALUES (?, ?, ?, ?, ?)",
              (title, start, end, category, color))
    conn.commit()
    return True

def get_goals():
    return pd.read_sql_query("SELECT * FROM goals", conn)

def update_goal_progress(goal_id, new_value):
    c = conn.cursor()
    c.execute("UPDATE goals SET current = ? WHERE id = ?", (new_value, goal_id))
    conn.commit()

def add_goal(name, target, category):
    c = conn.cursor()
    c.execute("INSERT INTO goals (name, current, target, category) VALUES (?, 0, ?, ?)",
              (name, target, category))
    conn.commit()

# ==========================================
# MAIN APP ROUTING
# ==========================================
def main():
    inject_custom_css()

    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #EDEDED; font-weight: 600; letter-spacing: 1px;'>NEXUS</h2>", unsafe_allow_html=True)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        menu_selection = option_menu(
            menu_title=None,
            options=["Calendar View", "Goal Analytics", "Settings"],
            icons=["calendar3", "bar-chart-line", "sliders"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#888", "font-size": "16px"},
                "nav-link": {"color": "#A3A3A3", "font-size": "14px", "text-align": "left", "margin": "4px 0", "border-radius": "8px"},
                "nav-link-selected": {"background-color": "#171717", "color": "#EDEDED", "font-weight": "500", "border": "1px solid #262626"},
            }
        )

    if menu_selection == "Calendar View":
        display_calendar_view()
    elif menu_selection == "Goal Analytics":
        display_goals_view()
    elif menu_selection == "Settings":
        display_settings_view()

# ==========================================
# CALENDAR VIEW
# ==========================================
def display_calendar_view():
    st.markdown("### Schedule")
    
    cats_df = get_categories()
    cat_names = cats_df['name'].tolist()
    cat_color_map = dict(zip(cats_df['name'], cats_df['color']))

    with st.expander("✨ Quick Add Event", expanded=False):
        with st.form("add_event_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                e_title = st.text_input("Event Title", placeholder="e.g., Deep Work Session")
            with col2:
                e_date = st.date_input("Date")
                e_category = st.selectbox("Category", cat_names if cat_names else ["Default"])
            with col3:
                e_start = st.time_input("Start Time")
            with col4:
                e_end = st.time_input("End Time")
            
            submitted = st.form_submit_button("Save to Calendar")
            if submitted:
                if not e_title:
                    st.error("Title is required.")
                else:
                    start_dt = datetime.combine(e_date, e_start).isoformat()
                    end_dt = datetime.combine(e_date, e_end).isoformat()
                    
                    if start_dt >= end_dt:
                        st.error("End time must be after start time.")
                    else:
                        color = cat_color_map.get(e_category, "#3B82F6")
                        if add_event(e_title, start_dt, end_dt, e_category, color):
                            st.success("Event added successfully!")
                            st.rerun()
                        else:
                            st.error("Schedule conflict detected.")

    # Format Calendar
    events_df = get_events()
    calendar_events = []
    for _, row in events_df.iterrows():
        calendar_events.append({
            "id": str(row['id']),
            "title": row['title'],
            "start": row['start_time'],
            "end": row['end_time'],
            "backgroundColor": row['color'],
            "borderColor": row['color'],
        })

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "timeGridDay,timeGridWeek,dayGridMonth",
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "24:00:00",
        "allDaySlot": False,
    }

    # Highly Customized FullCalendar CSS to fix the ugly red buttons
    calendar_css = """
        /* Calendar Background and Borders */
        .fc-theme-standard .fc-scrollgrid, .fc-theme-standard td, .fc-theme-standard th { 
            border-color: #262626 !important; 
        }
        .fc { color: #EDEDED; }
        
        /* Fix the Ugly Buttons */
        .fc .fc-button-primary {
            background-color: #171717 !important;
            border: 1px solid #333 !important;
            color: #EDEDED !important;
            text-transform: capitalize !important;
            font-weight: 500 !important;
            box-shadow: none !important;
            transition: all 0.2s ease;
        }
        .fc .fc-button-primary:hover {
            background-color: #262626 !important;
        }
        .fc .fc-button-primary:not(:disabled):active, 
        .fc .fc-button-primary:not(:disabled).fc-button-active {
            background-color: #3B82F6 !important;
            border-color: #3B82F6 !important;
            color: white !important;
        }
        
        /* Header styling */
        .fc-toolbar-title { font-weight: 600 !important; font-size: 1.25rem !important; }
        .fc-col-header-cell-cushion { color: #A3A3A3 !important; font-weight: 500 !important; padding: 8px !important;}
        
        /* Current time indicator */
        .fc-timegrid-now-indicator-line { border-color: #EF4444 !important; }
        .fc-timegrid-now-indicator-arrow { border-color: #EF4444 !important; border-top-color: transparent !important; border-bottom-color: transparent !important; }
    """

    calendar(events=calendar_events, options=calendar_options, custom_css=calendar_css)

# ==========================================
# GOALS VIEW
# ==========================================
def display_goals_view():
    st.markdown("### Analytics & Habits")
    
    goals_df = get_goals()
    if not goals_df.empty:
        total_goals = len(goals_df)
        completed = len(goals_df[goals_df['current'] >= goals_df['target']])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Active Habits", total_goals)
        m2.metric("Milestones Reached", completed)
        m3.metric("Global Progress", f"{int((completed/total_goals)*100)}%" if total_goals > 0 else "0%")
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([5, 3])
    
    with c1:
        st.markdown("#### Trackers")
        if goals_df.empty:
            st.info("No habits tracking yet. Setup your first one on the right.")
        else:
            for _, row in goals_df.iterrows():
                progress_val = min(row['current'] / row['target'], 1.0)
                st.write(f"<span style='font-weight: 500;'>{row['name']}</span> <span style='color: #888; font-size: 0.85em;'>• {row['category']}</span>", unsafe_allow_html=True)
                
                # Custom colored progress bar
                st.markdown(f"""
                <div style="width: 100%; background-color: #262626; border-radius: 6px; height: 10px; margin-bottom: 8px;">
                  <div style="width: {progress_val * 100}%; background-color: #3B82F6; height: 10px; border-radius: 6px;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn, col_txt = st.columns([1, 4])
                with col_btn:
                    if st.button("+ Log", key=f"add_{row['id']}"):
                        update_goal_progress(row['id'], min(row['current'] + 1, row['target']))
                        st.rerun()
                with col_txt:
                    st.write(f"<div style='padding-top: 6px; color: #A3A3A3; font-size: 0.9em;'>{row['current']} / {row['target']} logged</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    with c2:
        with st.form("add_goal_form", clear_on_submit=True):
            st.markdown("#### New Habit")
            cats_df = get_categories()
            cat_names = cats_df['name'].tolist() if not cats_df.empty else ["General"]
            
            g_name = st.text_input("Habit Name", placeholder="e.g., Read 20 Pages")
            g_target = st.number_input("Target Instances", min_value=1, value=30)
            g_cat = st.selectbox("Category", cat_names)
            
            if st.form_submit_button("Initialize Tracker"):
                if g_name:
                    add_goal(g_name, g_target, g_cat)
                    st.toast(f"Tracker '{g_name}' initialized!")
                    st.rerun()
                else:
                    st.error("Name is required.")

# ==========================================
# SETTINGS VIEW
# ==========================================
def display_settings_view():
    st.markdown("### Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Manage Categories")
        cats_df = get_categories()
        
        # Display existing categories nicely
        for _, row in cats_df.iterrows():
            st.markdown(f"""
            <div style='padding: 8px; border: 1px solid #262626; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center;'>
                <div style='width: 14px; height: 14px; border-radius: 50%; background-color: {row["color"]}; margin-right: 12px;'></div>
                <span>{row["name"]}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        with st.expander("+ Add New Category", expanded=False):
            with st.form("add_cat_form", clear_on_submit=True):
                new_cat_name = st.text_input("Category Name")
                new_cat_color = st.color_picker("Color Code", "#3B82F6")
                if st.form_submit_button("Save Category"):
                    if new_cat_name:
                        if add_category(new_cat_name, new_cat_color):
                            st.success("Added!")
                            st.rerun()
                        else:
                            st.error("Category already exists.")
                    else:
                        st.error("Name required.")

    with col2:
        st.markdown("#### Data Management")
        st.warning("These actions are irreversible.")
        if st.button("Delete All Events"):
            conn.cursor().execute("DELETE FROM events")
            conn.commit()
            st.toast("Events wiped.")
            
        if st.button("Delete All Habits"):
            conn.cursor().execute("DELETE FROM goals")
            conn.commit()
            st.toast("Habits wiped.")

if __name__ == "__main__":
    main()
