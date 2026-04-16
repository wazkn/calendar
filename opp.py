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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        /* Global Font & Dark Theme Colors */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            background-color: #0f172a !important; /* Deep Slate */
            color: #f8fafc !important;
        }

        /* Card-like containers for metrics */
        div[data-testid="metric-container"] {
            background-color: #1e293b;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            border-left: 5px solid #0ea5e9; /* Electric Blue */
        }

        /* Metric Value */
        div[data-testid="metric-container"] > div {
            color: #38bdf8 !important;
        }

        /* Inputs & Selectboxes */
        .stTextInput > div > div > input, 
        .stDateInput > div > div > input, 
        .stTimeInput > div > div > input,
        .stSelectbox > div > div > div {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
        }

        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #0b1120 !important;
            border-right: 1px solid #1e293b !important;
        }

        /* Buttons */
        .stButton > button {
            background-color: #0ea5e9 !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 600 !important;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #38bdf8 !important;
            box-shadow: 0 0 10px rgba(14, 165, 233, 0.5);
        }
        
        /* Progress bars */
        .stProgress > div > div > div > div {
            background-color: #10b981 !important; /* Mint Green */
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
    conn.commit()
    return conn

conn = init_db()

# DB Helper Functions
def get_events():
    return pd.read_sql_query("SELECT * FROM events", conn)

def add_event(title, start, end, category, color):
    c = conn.cursor()
    # Overlap check
    c.execute("""SELECT id FROM events WHERE 
                 (start_time < ? AND end_time > ?) OR
                 (start_time < ? AND end_time > ?) OR
                 (start_time >= ? AND end_time <= ?)""", 
              (end, start, end, start, start, end))
    if c.fetchone():
        return False # Overlap detected
    
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
# MAIN APP
# ==========================================
def main():
    inject_custom_css()

    with st.sidebar:
        st.markdown("<h2 style='text-align: center; color: #38bdf8;'>🌌 NEXUS</h2>", unsafe_allow_html=True)
        st.markdown("---")
        menu_selection = option_menu(
            menu_title=None,
            options=["Calendar View", "Goal Analytics", "Settings"],
            icons=["calendar3", "bar-chart-line", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#10b981", "font-size": "18px"},
                "nav-link": {"color": "#f8fafc", "font-size": "16px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#1e293b", "border-left": "4px solid #0ea5e9"},
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
    st.header("📅 Calendar & Schedule")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("Add Event")
        with st.form("add_event_form"):
            e_title = st.text_input("Event Title")
            e_date = st.date_input("Date")
            e_start = st.time_input("Start Time")
            e_end = st.time_input("End Time")
            e_category = st.selectbox("Category", ["Work", "Health", "Personal", "Social"])
            
            color_map = {"Work": "#0ea5e9", "Health": "#10b981", "Personal": "#f59e0b", "Social": "#8b5cf6"}
            
            submitted = st.form_submit_button("Save Event")
            if submitted:
                start_dt = datetime.combine(e_date, e_start).isoformat()
                end_dt = datetime.combine(e_date, e_end).isoformat()
                
                if start_dt >= end_dt:
                    st.error("End time must be after start time.")
                else:
                    success = add_event(e_title, start_dt, end_dt, e_category, color_map[e_category])
                    if success:
                        st.success("Event Added!")
                        st.rerun()
                    else:
                        st.error("Time overlap detected! Try another time.")

    with col1:
        # Load events from DB format them for streamlit-calendar
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
            "slotMaxTime": "22:00:00",
        }

        custom_css = """
            .fc-theme-standard .fc-scrollgrid { border-color: #334155; }
            .fc-theme-standard td, .fc-theme-standard th { border-color: #334155; }
            .fc-col-header-cell-cushion { color: #f8fafc; }
            .fc-daygrid-day-number { color: #f8fafc; }
            .fc-toolbar-title { color: #38bdf8; font-weight: 700; }
        """

        calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)

# ==========================================
# GOALS VIEW
# ==========================================
def display_goals_view():
    st.header("📈 Goal Analytics")
    
    # Top Metrics
    goals_df = get_goals()
    if not goals_df.empty:
        total_goals = len(goals_df)
        completed = len(goals_df[goals_df['current'] >= goals_df['target']])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Goals Tracked", total_goals)
        m2.metric("Goals Completed", completed)
        m3.metric("Completion Rate", f"{int((completed/total_goals)*100)}%" if total_goals > 0 else "0%")
    
    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Your Dashboard")
        if goals_df.empty:
            st.info("No goals tracked yet. Add one from the sidebar!")
        else:
            for _, row in goals_df.iterrows():
                progress_val = min(row['current'] / row['target'], 1.0)
                st.write(f"**{row['name']}** ({row['category']})")
                st.progress(progress_val)
                
                col_btn1, col_btn2, col_space = st.columns([1, 1, 4])
                with col_btn1:
                    if st.button("+1", key=f"add_{row['id']}"):
                        update_goal_progress(row['id'], min(row['current'] + 1, row['target']))
                        st.rerun()
                with col_btn2:
                    st.write(f"**{row['current']} / {row['target']}**")
                st.markdown("<br>", unsafe_allow_html=True)

    with c2:
        st.subheader("Add New Goal")
        with st.form("add_goal_form"):
            g_name = st.text_input("Goal Name (e.g., Read Pages)")
            g_target = st.number_input("Target Number", min_value=1, value=10)
            g_cat = st.selectbox("Category", ["Health", "Learning", "Finance", "Mindfulness"])
            if st.form_submit_button("Create Goal"):
                add_goal(g_name, g_target, g_cat)
                st.success("Goal added successfully!")
                st.rerun()

# ==========================================
# SETTINGS VIEW
# ==========================================
def display_settings_view():
    st.header("⚙️ Settings")
    st.markdown("Manage your local Nexus database.")
    
    if st.button("🚨 Clear All Events", type="primary"):
        c = conn.cursor()
        c.execute("DELETE FROM events")
        conn.commit()
        st.success("All events cleared.")
        
    if st.button("🚨 Clear All Goals", type="primary"):
        c = conn.cursor()
        c.execute("DELETE FROM goals")
        conn.commit()
        st.success("All goals cleared.")

if __name__ == "__main__":
    main()