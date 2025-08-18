import streamlit as st
import pandas as pd
import json
import datetime
from typing import Dict, List, Optional
import plotly.express as px

# ===============================================================
# PAGE CONFIG
# ===============================================================
st.set_page_config(
    page_title="Legal Doc AI - Hackathon Log",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================================
# CUSTOM CSS (kept from your original, trimmed a bit for size)
# ===============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem; font-weight: bold; text-align: center; color: #1f77b4;
        margin-bottom: 2rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .team-member-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem; border-radius: 15px; margin: 1rem 0; color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2); font-weight: 500;
    }
    .log-entry {
        background: #ffffff; padding: 1.5rem; border-left: 6px solid #1f77b4;
        margin: 1rem 0; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        font-size: 16px; line-height: 1.6;
    }
    .stats-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 2rem;
        border-radius: 15px; text-align: center; margin: 1rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); font-weight: bold;
    }
    .stats-card h3 { font-size: 2.5rem; color: #1565c0; margin-bottom: 0.5rem; }
    .stats-card p { font-size: 1.2rem; color: #424242; font-weight: 600; }
    .task-status { font-size: 18px; font-weight: bold; padding: 0.3rem 0.8rem; border-radius: 20px; display: inline-block; margin: 0.2rem; }
    .status-not-started { background: #ffebee; color: #c62828; }
    .status-in-progress { background: #fff3e0; color: #ef6c00; }
    .status-completed { background: #e8f5e8; color: #2e7d32; }
    .status-blocked { background: #fce4ec; color: #ad1457; }
    .member-duties { background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0; border: 2px solid #e0e0e0; }
    .duty-item { background: white; padding: 0.8rem; margin: 0.5rem 0; border-radius: 8px; border-left: 4px solid #4caf50; font-size: 14px; line-height: 1.5; }
    .export-section { background: #f1f8e9; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border: 2px solid #8bc34a; }
</style>
""", unsafe_allow_html=True)

# ===============================================================
# DEMO USERS (usernames/passwords) — Member 4 is the Leader
# ===============================================================
USERS = {
    "Arryan":   {"password": "123",     "role": "API/Data Fetch", "is_leader": False},
    "Arth":     {"password": "123",     "role": "Backend 1",      "is_leader": False},
    "Shashwat": {"password": "123",     "role": "Backend 2",      "is_leader": False},
    "Member 4": {"password": "leader",  "role": "Team Leader",    "is_leader": True},
}

TEAM_MEMBERS = {u: USERS[u]["role"] for u in USERS}

# ===============================================================
# STATE INIT
# ===============================================================
def _init_state():
    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    if "logs" not in st.session_state:
        st.session_state.logs: List[Dict] = []  # time-stamped log entries

    if "member_duties" not in st.session_state:
        st.session_state.member_duties = {
            "Arryan": [
                "Study Indian Kanoon API / scraping terms and documentation",
                "Implement script to fetch sample judgments/contracts with metadata",
                "Clean and store fetched data in temporary JSON/CSV format",
            ],
            "Arth": [
                "Set up backend environment (Node.js/Python), connect to DB (PostgreSQL/Cloud SQL)",
                "Create API endpoints for CRUD operations on legal docs",
                "Integrate secure storage (PDP Act compliance)",
            ],
            "Shashwat": [
                "Design DB schema for multi-language legal documents",
                "Implement schema and migrations",
                "Add search/filter functionality for stored docs",
            ],
            "Member 4": [
                "Research clause segmentation & summarization techniques for Indian legal docs",
                "Build prototype model/module for plain-language summaries in Hindi/English",
                "Integrate risk flagging logic (penalty interest, unlimited liability)",
            ],
        }

    # Central tasks list: created by Leader, visible to members
    if "tasks" not in st.session_state:
        st.session_state.tasks: List[Dict] = []
        # structure:
        # {id, member, task, deadline (date), status: "Assigned|In Progress|Completed|Approved",
        #  approved: bool, created_at, updated_at}

    # Project timeline (leader adds milestones)
    if "timeline" not in st.session_state:
        st.session_state.timeline: List[Dict] = []  # {title, start, end, notes}

    if "id_counter" not in st.session_state:
        st.session_state.id_counter = 0

_init_state()

# ===============================================================
# HELPERS
# ===============================================================
def _new_id(prefix="T"):
    st.session_state.id_counter += 1
    return f"{prefix}-{int(datetime.datetime.now().timestamp())}-{st.session_state.id_counter}"

def add_log_entry(member: str, task: str, status: str, time_spent: int, notes: str, task_type: str = "Custom", linked_task_id: Optional[str] = None):
    entry = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'member': member,
        'role': TEAM_MEMBERS.get(member, "Member"),
        'task': task,
        'task_type': task_type,          # "Assigned Duty" | "Assigned Task" | "Custom"
        'status': status,                # "Not Started" | "In Progress" | "Completed" | "Blocked"
        'time_spent': time_spent,
        'notes': notes,
        'linked_task_id': linked_task_id
    }
    st.session_state.logs.append(entry)

    # If this log is for an assigned task, update task status accordingly
    if linked_task_id:
        for t in st.session_state.tasks:
            if t["id"] == linked_task_id:
                t["updated_at"] = datetime.datetime.now()
                # Sync task status with log status (up to Completed)
                if status in ["In Progress"] and t["status"] == "Assigned":
                    t["status"] = "In Progress"
                if status == "Completed":
                    t["status"] = "Completed"
                break

def get_member_stats(member: str) -> Dict:
    member_logs = [log for log in st.session_state.logs if log['member'] == member]
    total_time = sum(log['time_spent'] for log in member_logs)
    total_tasks = len(member_logs)
    completed_tasks = len([log for log in member_logs if log['status'] == 'Completed'])
    return {
        'total_time': total_time,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

def export_to_google_docs_format():
    """Export logs + tasks + timeline in a Google Docs friendly .txt content."""
    if not st.session_state.logs:
        base_stats = "No logs available to export."
    content = f"""
LEGAL DOCUMENT AI - HACKATHON LOG REPORT
Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

========================================
TEAM OVERVIEW
========================================

Team Members:
{chr(10).join([f"• {member} ({role})" for member, role in TEAM_MEMBERS.items()])}

========================================
DETAILED LOG ENTRIES
========================================
"""

    # Group logs by member
    for member in TEAM_MEMBERS.keys():
        member_logs = [log for log in st.session_state.logs if log['member'] == member]
        if member_logs:
            stats = get_member_stats(member)
            content += f"""
--- {member.upper()} ({TEAM_MEMBERS[member]}) ---
Stats: {stats['completed_tasks']}/{stats['total_tasks']} tasks completed | {stats['total_time']} minutes total

"""
            for log in sorted(member_logs, key=lambda x: x['timestamp'], reverse=True):
                content += f"""
[{log['timestamp']}] {log['status'].upper()}
Task: {log['task']}  {'(Linked Task: '+log['linked_task_id']+')' if log.get('linked_task_id') else ''}
Type: {log.get('task_type','Custom')}
Time Spent: {log['time_spent']} minutes
Notes: {log['notes'] if log['notes'] else 'No additional notes'}
---
"""

    # Summary statistics
    total_logs = len(st.session_state.logs)
    total_time = sum(log['time_spent'] for log in st.session_state.logs)
    completed_tasks = len([log for log in st.session_state.logs if log['status'] == 'Completed'])
    team_completion_rate = (completed_tasks / total_logs * 100) if total_logs else 0.0

    content += f"""
========================================
SUMMARY STATISTICS
========================================

Total Tasks Logged: {total_logs}
Completed Tasks: {completed_tasks}
Total Time Invested: {total_time // 60} hours {total_time % 60} minutes
Team Completion Rate: {team_completion_rate:.1f}% 

========================================
PROJECT DUTIES STATUS
========================================
"""
    for member, duties in st.session_state.member_duties.items():
        content += f"""
{member} ({TEAM_MEMBERS[member]}):
{chr(10).join([f"  • {duty}" for duty in duties])}
"""

    content += f"""

========================================
ASSIGNED TASKS (LEADER)
========================================
"""
    if st.session_state.tasks:
        for t in sorted(st.session_state.tasks, key=lambda x: (x.get("deadline") or datetime.date.today())):
            content += f"""
ID: {t['id']} | {t['task']}
Assigned To: {t['member']} | Deadline: {t['deadline']} | Status: {t['status']} | Approved: {t['approved']}
"""
    else:
        content += "No leader-assigned tasks.\n"

    content += f"""

========================================
PROJECT TIMELINE
========================================
"""
    if st.session_state.timeline:
        for m in st.session_state.timeline:
            content += f"""
• {m['title']} | {m['start']} → {m['end']}
  Notes: {m.get('notes','-')}
"""
    else:
        content += "No timeline items yet.\n"

    return content

# ===============================================================
# AUTH
# ===============================================================
def login_view():
    st.markdown('<h1 class="main-header">⚖ Legal Document AI - Hackathon Log</h1>', unsafe_allow_html=True)
    st.subheader("🔐 Team Login")
    c1, c2 = st.columns(2)
    with c1:
        username = st.text_input("👤 Username", value="")
    with c2:
        password = st.text_input("🔑 Password", type="password", value="")
    if st.button("Login", type="primary"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.current_user = username
            st.success(f"Welcome, {username}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ===============================================================
# SHARED WIDGETS
# ===============================================================
def header_and_banner():
    st.markdown('<h1 class="main-header">⚖ Legal Document AI - Hackathon Log</h1>', unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; background: linear-gradient(90deg, #e3f2fd, #bbdefb); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h3 style='color: #1565c0; margin: 0;'>🎯 Mission: AI-Powered Legal Document Analysis & Risk Detection</h3>
        <p style='margin: 0.5rem 0 0 0; color: #424242; font-weight: 500;'>3-Day Sprint | Multi-language Support | Indian Legal Framework</p>
    </div>
    """, unsafe_allow_html=True)

def sidebar_block(is_leader: bool):
    with st.sidebar:
        st.header("👥 Team & Duties")

        # Duties list

        if st.button("📋 Generate Google Docs Report"):
            report_content = export_to_google_docs_format()
            st.download_button(
                label="📥 Download Report",
                data=report_content,
                file_name=f"Legal_AI_Hackathon_Log_{datetime.date.today()}.txt",
                mime="text/plain",
                help="Download as .txt file - Copy content to Google Docs"
            )

        if st.button("📊 Export Raw JSON"):
            json_data = json.dumps(st.session_state.logs, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"hackathon_logs_{datetime.date.today()}.json",
                mime="application/json"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.current_user = None
            st.rerun()

        if is_leader:
            st.info("👑 You are viewing the Leader tools.")

# ===============================================================
# ANALYTICS / DASHBOARD (kept from your original)
# ===============================================================
def dashboard_tab():
    st.header("📊 Team Dashboard")
    if st.session_state.logs:
        col1, col2, col3, col4 = st.columns(4)

        total_logs = len(st.session_state.logs)
        total_time = sum(log['time_spent'] for log in st.session_state.logs)
        completed_tasks = len([log for log in st.session_state.logs if log['status'] == 'Completed'])

        with col1:
            st.markdown(f"""<div class="stats-card"><h3>📋 {total_logs}</h3><p>Total Tasks</p></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="stats-card"><h3>⏰ {total_time // 60}h {total_time % 60}m</h3><p>Total Time</p></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="stats-card"><h3>✅ {completed_tasks}</h3><p>Completed</p></div>""", unsafe_allow_html=True)
        with col4:
            completion_rate = (completed_tasks / total_logs * 100) if total_logs > 0 else 0
            st.markdown(f"""<div class="stats-card"><h3>📈 {completion_rate:.1f}%</h3><p>Completion Rate</p></div>""", unsafe_allow_html=True)

        st.divider()

        # Charts
        df = pd.DataFrame(st.session_state.logs)
        colA, colB = st.columns(2)

        with colA:
            df['member_role'] = df['member'].map(lambda x: f"{x} ({TEAM_MEMBERS[x]})")
            time_by_member = df.groupby('member_role')['time_spent'].sum()
            fig_pie = px.pie(values=time_by_member.values, names=time_by_member.index, title="⏰ Time Distribution by Member",
                             color_discrete_sequence=px.colors.qualitative.Set3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with colB:
            status_counts = df['status'].value_counts()
            colors = {'Completed': '#4caf50', 'In Progress': '#ff9800', 'Not Started': '#f44336', 'Blocked': '#9c27b0'}
            fig_bar = px.bar(x=status_counts.index, y=status_counts.values, title="📈 Task Status Overview",
                             color=status_counts.index, color_discrete_map=colors)
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        # Timeline chart
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        daily_member_tasks = df.groupby([df['timestamp'].dt.date, 'member']).size().unstack(fill_value=0)
        fig_timeline = px.line(daily_member_tasks, title="📅 Daily Progress by Member", markers=True)
        fig_timeline.update_layout(xaxis_title="Date", yaxis_title="Tasks Completed", legend_title="Team Member")
        st.plotly_chart(fig_timeline, use_container_width=True)

    else:
        st.markdown("""
        <div style='text-align: center; padding: 3rem; background: #f5f5f5; border-radius: 15px;'>
            <h3>🚀 Ready to start logging?</h3>
            <p style='font-size: 18px; color: #666;'>No logs yet! Head to the "Add Log Entry" tab to begin tracking your hackathon progress.</p>
        </div>
        """, unsafe_allow_html=True)

# ===============================================================
# LOGS VIEW (FILTERS) — kept from your original, slightly trimmed
# ===============================================================
def all_logs_tab():
    st.header("📋 Complete Log History")
    if st.session_state.logs:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filter_member = st.selectbox("👤 Filter by Member:", ["All"] + list(TEAM_MEMBERS.keys()))
        with col2:
            filter_status = st.selectbox("📈 Filter by Status:", ["All", "Not Started", "In Progress", "Completed", "Blocked"])
        with col3:
            filter_task_type = st.selectbox("📋 Filter by Task Type:", ["All", "Assigned Duty", "Assigned Task", "Custom"])
        with col4:
            sort_by = st.selectbox("🔄 Sort by:", ["Timestamp (Latest)", "Timestamp (Oldest)", "Member", "Status"])

        filtered_logs = st.session_state.logs.copy()
        if filter_member != "All":
            filtered_logs = [l for l in filtered_logs if l['member'] == filter_member]
        if filter_status != "All":
            filtered_logs = [l for l in filtered_logs if l['status'] == filter_status]
        if filter_task_type != "All":
            filtered_logs = [l for l in filtered_logs if l.get('task_type', 'Custom') == filter_task_type]

        if sort_by == "Timestamp (Latest)":
            filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        elif sort_by == "Timestamp (Oldest)":
            filtered_logs.sort(key=lambda x: x['timestamp'])
        elif sort_by == "Member":
            filtered_logs.sort(key=lambda x: x['member'])
        else:  # Status
            filtered_logs.sort(key=lambda x: x['status'])

        st.write(f"*Showing {len(filtered_logs)} of {len(st.session_state.logs)} log entries*")

        for log in filtered_logs:
            status_emoji = {"Not Started": "⭕", "In Progress": "🔄", "Completed": "✅", "Blocked": "🚫"}
            role = log.get('role', 'Unknown Role')
            task_type = log.get('task_type', 'Custom')
            task_badge = "🎯" if task_type in ["Assigned Duty", "Assigned Task"] else "🔧"
            linked = f" <em>(Linked: {log['linked_task_id']})</em>" if log.get('linked_task_id') else ""

            st.markdown(f"""
            <div class="log-entry">
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                    <h3 style='margin: 0; color: #1565c0;'>{status_emoji[log['status']]} {log['task']}{linked}</h3>
                    <span style='background: #e3f2fd; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 14px; color: #1565c0;'>
                        {task_badge} {task_type}
                    </span>
                </div>
                <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;'>
                    <div><strong>👤 Member:</strong> {log['member']} ({role})</div>
                    <div><strong>⏰ Time:</strong> {log['time_spent']} minutes</div>
                    <div><strong>📅 Date:</strong> {log['timestamp']}</div>
                    <div><strong>📈 Status:</strong> <span class='task-status status-{log['status'].lower().replace(' ', '-')}'>{log['status']}</span></div>
                </div>
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 8px;'>
                    <strong>📝 Notes:</strong> {log['notes'] if log['notes'] else '<em>No additional notes provided</em>'}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📝 No logs to display yet! Start by adding your first log entry.")

# ===============================================================
# TEAM PROGRESS (CARDS) — kept, uses duties + stats
# ===============================================================
def team_progress_tab():
    st.header("👥 Individual Team Progress")
    if st.session_state.logs:
        cols = st.columns(2)
        for i, (member, role) in enumerate(TEAM_MEMBERS.items()):
            stats = get_member_stats(member)
            with cols[i % 2]:
                assigned_duties = len(st.session_state.member_duties.get(member, []))
                completed_duties = len([l for l in st.session_state.logs
                                        if l['member'] == member and l['status'] == 'Completed'
                                        and l.get('task_type') in ('Assigned Duty','Assigned Task')])
                duty_progress = (completed_duties / assigned_duties * 100) if assigned_duties else 0

                st.markdown(f"""
                <div class="team-member-card">
                    <h3>👤 {member}</h3>
                    <p style='font-size: 18px; margin-bottom: 1rem;'>🎯 {role}</p>
                    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                        <div>📊 Total Tasks: {stats['total_tasks']}</div>
                        <div>✅ Completed: {stats['completed_tasks']}</div>
                        <div>⏰ Total Time: {stats['total_time']} min</div>
                        <div>📈 Completion: {stats['completion_rate']:.1f}%</div>
                    </div>
                    <div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.3);'>
                        <strong>🎯 Duty Progress: {duty_progress:.0f}% ({completed_duties}/{assigned_duties})</strong>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Recent activity
                member_logs = [l for l in st.session_state.logs if l['member'] == member][-4:]
                if member_logs:
                    st.write(f"📋 Recent Activity for {member}:")
                    for l in reversed(member_logs):
                        status_emoji = {"Not Started":"⭕","In Progress":"🔄","Completed":"✅","Blocked":"🚫"}
                        task_type_emoji = "🎯" if l.get('task_type') in ('Assigned Duty','Assigned Task') else "🔧"
                        task_display = l['task'][:50] + "..." if len(l['task']) > 50 else l['task']
                        st.markdown(
                            f"<div style='background: white; padding: 0.8rem; margin: 0.3rem 0; border-radius: 8px; border-left: 4px solid #2196f3;'>"
                            f"{status_emoji[l['status']]} {task_type_emoji} {task_display} "
                            f"<span style='color: #666; font-size: 14px;'>({l['time_spent']} min)</span></div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info(f"No logs yet for {member}")
    else:
        st.info("📊 No data available for team stats! Start logging your progress to see individual statistics.")

# ===============================================================
# MEMBER VIEW
# ===============================================================
def member_tabs(username: str):
    header_and_banner()
    sidebar_block(is_leader=False)
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Log Entry", "📊 Dashboard", "📋 View My Logs", "🗂 My Assigned Tasks"])

    # ---- Add Log Entry
    with tab1:
        st.header("🚀 Log Your Progress")
        col1, col2 = st.columns(2)
        with col1:
            # Member can choose from: Assigned Duty (duties list), Assigned Task (leader), or Custom
            task_type = st.radio("📋 Task Type:", ["Assigned Duty", "Assigned Task", "Custom Task"])
            if task_type == "Assigned Duty":
                duties = st.session_state.member_duties.get(username, [])
                task_description = st.selectbox("Select Duty:", duties) if duties else st.text_input("No predefined duty found. Enter task:")
                linked_task_id = None
            elif task_type == "Assigned Task":
                my_tasks = [t for t in st.session_state.tasks if t["member"] == username and t["status"] in ("Assigned","In Progress","Completed") and not t["approved"]]
                if my_tasks:
                    chosen = st.selectbox("Select Assigned Task:", [f"{t['id']} | {t['task']} (due {t['deadline']})" for t in my_tasks])
                    chosen_id = chosen.split(" | ")[0]
                    chosen_task = next(t for t in my_tasks if t["id"] == chosen_id)
                    task_description = chosen_task["task"]
                    linked_task_id = chosen_task["id"]
                else:
                    st.info("No active assigned tasks. Use Custom/Duty.")
                    task_description = st.text_input("📝 Task Description:")
                    linked_task_id = None
            else:
                task_description = st.text_input("📝 Task Description:")
                linked_task_id = None

            status = st.selectbox("📈 Status:", ["Not Started", "In Progress", "Completed", "Blocked"])
        with col2:
            time_spent = st.number_input("⏱ Time Spent (minutes):", min_value=0, value=30, step=15)
            notes = st.text_area("📋 Notes/Details/Challenges:", height=120, placeholder="Describe what you accomplished, blockers, next steps...")

        if st.button("➕ Add Log Entry", type="primary", use_container_width=True):
            if task_description and task_description.strip():
                add_log_entry(username, task_description, status, time_spent, notes,
                              task_type="Assigned Task" if linked_task_id else task_type,
                              linked_task_id=linked_task_id)
                st.success("✅ Log entry added!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Please enter a task description!")

    # ---- Dashboard
    with tab2:
        dashboard_tab()

    # ---- View My Logs
    with tab3:
        if st.session_state.logs:
            my_logs = [l for l in st.session_state.logs if l['member'] == username]
            if not my_logs:
                st.info("No logs yet — add one in the first tab.")
            else:
                for log in sorted(my_logs, key=lambda x: x['timestamp'], reverse=True):
                    status_emoji = {"Not Started":"⭕","In Progress":"🔄","Completed":"✅","Blocked":"🚫"}
                    linked = f" <em>(Linked: {log['linked_task_id']})</em>" if log.get('linked_task_id') else ""
                    st.markdown(f"""
                    <div class="log-entry">
                        <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;'>
                            <h3 style='margin:0;color:#1565c0;'>{status_emoji[log['status']]} {log['task']}{linked}</h3>
                            <span style='background:#e3f2fd;padding:0.3rem 0.8rem;border-radius:15px;font-size:14px;color:#1565c0;'>{log.get('task_type','Custom')}</span>
                        </div>
                        <div>⏰ {log['time_spent']} min | 📅 {log['timestamp']} | 📈 {log['status']}</div>
                        <div style='background:#f8f9fa;padding:1rem;border-radius:8px;margin-top:0.7rem;'><strong>📝 Notes:</strong> {log['notes'] or '<em>-</em>'}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No logs yet.")

    # ---- My Assigned Tasks
    with tab4:
        st.subheader("🗂 Assigned Tasks")
        my_tasks = [t for t in st.session_state.tasks if t["member"] == username]
        if not my_tasks:
            st.info("You have no assigned tasks yet.")
        else:
            # Quick status update
            for t in sorted(my_tasks, key=lambda x: (x['approved'], x['status']!="Approved", x.get("deadline") or datetime.date.today())):
                st.write(f"**{t['id']}** — {t['task']}  \n"
                         f"Deadline: `{t['deadline']}` | Status: **{t['status']}** | Approved: **{t['approved']}**")
                if t["status"] in ("Assigned","In Progress"):
                    if st.button(f"Mark In Progress ({t['id']})", key=f"mip-{t['id']}"):
                        t["status"] = "In Progress"; t["updated_at"] = datetime.datetime.now(); st.rerun()
                    if st.button(f"Mark Completed ({t['id']})", key=f"mc-{t['id']}"):
                        t["status"] = "Completed"; t["updated_at"] = datetime.datetime.now(); st.rerun()
                st.divider()

# ===============================================================
# LEADER VIEW
# ===============================================================
def leader_tabs():
    header_and_banner()
    sidebar_block(is_leader=True)

    tab_assign, tab_dashboard, tab_all_logs, tab_progress, tab_tasks = st.tabs(
        ["📅 Assign & Timeline", "📊 Dashboard", "📋 View All Logs", "👥 Team Progress", "🗂 Tasks & Approvals"]
    )

    # ---- Assign & Timeline
    with tab_assign:
        st.subheader("📝 Assign Tasks (Bulk / Round-Robin)")
        c1, c2 = st.columns([2,1])
        with c1:
            members = st.multiselect("Assign to members:", [m for m in TEAM_MEMBERS.keys() if m != "Member 4"], default=["Arryan","Arth","Shashwat"])
            bulk_tasks_text = st.text_area("Enter one task per line:", height=120,
                                           placeholder="e.g.\nFetch 50 judgments from Indian Kanoon\nDesign DB schema for case metadata\nBuild endpoint for doc upload ...")
        with c2:
            deadline = st.date_input("📅 Default Deadline", value=datetime.date.today() + datetime.timedelta(days=2))
            if st.button("📌 Create Tasks", type="primary", use_container_width=True):
                lines = [l.strip() for l in bulk_tasks_text.splitlines() if l.strip()]
                if not lines or not members:
                    st.error("Please enter at least one task and select members.")
                else:
                    # Round-robin assignment to selected members
                    for i, task in enumerate(lines):
                        assigned_to = members[i % len(members)]
                        st.session_state.tasks.append({
                            "id": _new_id("TASK"),
                            "member": assigned_to,
                            "task": task,
                            "deadline": deadline,
                            "status": "Assigned",
                            "approved": False,
                            "created_at": datetime.datetime.now(),
                            "updated_at": datetime.datetime.now()
                        })
                    st.success(f"✅ Created {len(lines)} tasks for {len(members)} member(s).")

        st.markdown("---")
        st.subheader("🧭 Project Timeline (Milestones)")
        t1, t2, t3 = st.columns(3)
        with t1:
            tl_title = st.text_input("Milestone Title")
        with t2:
            tl_start = st.date_input("Start", value=datetime.date.today())
        with t3:
            tl_end = st.date_input("End", value=datetime.date.today() + datetime.timedelta(days=1))
        tl_notes = st.text_area("Notes (optional)", height=80)
        if st.button("➕ Add Milestone"):
            st.session_state.timeline.append({
                "title": tl_title or "Untitled",
                "start": tl_start,
                "end": tl_end,
                "notes": tl_notes
            })
            st.success("Milestone added.")

        # Simple timeline table
        if st.session_state.timeline:
            tl_df = pd.DataFrame(st.session_state.timeline)
            st.dataframe(tl_df)

    # ---- Dashboard
    with tab_dashboard:
        dashboard_tab()

    # ---- All Logs
    with tab_all_logs:
        all_logs_tab()

    # ---- Team Progress
    with tab_progress:
        team_progress_tab()

    # ---- Tasks & Approvals
    with tab_tasks:
        st.subheader("🗂 All Assigned Tasks")
        if not st.session_state.tasks:
            st.info("No tasks have been assigned yet.")
        else:
            # Filters
            f1, f2, f3 = st.columns(3)
            with f1:
                f_member = st.selectbox("Filter by Member", ["All"] + [m for m in TEAM_MEMBERS.keys() if m!="Member 4"])
            with f2:
                f_status = st.selectbox("Filter by Status", ["All", "Assigned", "In Progress", "Completed", "Approved"])
            with f3:
                f_approved = st.selectbox("Filter by Approval", ["All", "Approved", "Pending"])

            tasks = st.session_state.tasks
            if f_member != "All":
                tasks = [t for t in tasks if t["member"] == f_member]
            if f_status != "All":
                tasks = [t for t in tasks if t["status"] == f_status]
            if f_approved != "All":
                want = (f_approved == "Approved")
                tasks = [t for t in tasks if t["approved"] == want]

            # Approvals list
            for t in sorted(tasks, key=lambda x: (x["approved"], x["status"] != "Approved", x.get("deadline") or datetime.date.today())):
                st.write(f"**{t['id']}** — {t['task']}  \n"
                         f"👤 {t['member']} | 📅 Deadline: `{t['deadline']}` | 📈 Status: **{t['status']}** | ✅ Approved: **{t['approved']}**")

                cA, cB, cC, cD = st.columns(4)
                with cA:
                    if t["status"] != "Approved" and st.button(f"Approve ({t['id']})", key=f"appr-{t['id']}"):
                        t["status"] = "Approved"
                        t["approved"] = True
                        t["updated_at"] = datetime.datetime.now()
                        st.success(f"Task {t['id']} approved.")
                        st.rerun()
                with cB:
                    if t["status"] in ("Assigned","In Progress") and st.button(f"Mark Completed ({t['id']})", key=f"done-{t['id']}"):
                        t["status"] = "Completed"
                        t["updated_at"] = datetime.datetime.now()
                        st.rerun()
                with cC:
                    if t["status"] != "Assigned" and st.button(f"Reset to Assigned ({t['id']})", key=f"reset-{t['id']}"):
                        t["status"] = "Assigned"
                        t["approved"] = False
                        t["updated_at"] = datetime.datetime.now()
                        st.rerun()
                with cD:
                    if st.button(f"❌ Delete ({t['id']})", key=f"del-{t['id']}"):
                        st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != t["id"]]
                        st.rerun()
                st.divider()

# ===============================================================
# MAIN
# ===============================================================
def main():
    user = st.session_state.current_user
    if not user:
        login_view()
        return

    # Route based on role
    if USERS[user]["is_leader"]:
        leader_tabs()
    else:
        member_tabs(user)

if __name__ == "__main__":
    main()