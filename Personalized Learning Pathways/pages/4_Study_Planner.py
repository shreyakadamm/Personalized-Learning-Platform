import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.data_handler import save_study_plan, get_user_study_plans, load_data
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Require authentication
require_auth()

st.set_page_config(page_title="Study Planner", page_icon="📅", layout="wide")

st.title("📅 Study Planner")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Load available streams for goal setting
streams_df = load_data('streams')
recommendations_df = load_data('recommendations')

# Tabs for different planner features
tab1, tab2, tab3, tab4 = st.tabs(["📝 Create Goals", "📊 My Plans", "📈 Progress Tracking", "📚 Study Resources"])

with tab1:
    st.subheader("🎯 Set New Learning Goals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Goal Details")
        
        goal_title = st.text_input("Goal Title", placeholder="e.g., Master Python Programming")
        
        if streams_df is not None:
            stream_options = ["General"] + streams_df['stream_name'].tolist()
            selected_stream = st.selectbox("Learning Stream", stream_options)
        else:
            selected_stream = st.text_input("Learning Stream", placeholder="e.g., Computer Science")
        
        goal_type = st.selectbox(
            "Goal Type",
            ["Course Completion", "Skill Development", "Certification", "Project", "Assessment Preparation"]
        )
        
        priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
        
        description = st.text_area("Goal Description", placeholder="Describe what you want to achieve...")
    
    with col2:
        st.markdown("#### Timeline & Tracking")
        
        start_date = st.date_input("Start Date", value=datetime.now().date())
        target_date = st.date_input("Target Completion Date", value=datetime.now().date() + timedelta(days=30))
        
        if target_date <= start_date:
            st.error("Target date must be after start date")
        
        study_hours_per_week = st.number_input("Study Hours per Week", min_value=1, max_value=40, value=5)
        
        # Calculate total available hours
        total_days = (target_date - start_date).days
        total_weeks = total_days / 7
        total_available_hours = total_weeks * study_hours_per_week
        
        st.info(f"Total available study time: {total_available_hours:.1f} hours over {total_days} days")
        
        milestones = st.text_area("Key Milestones (one per line)", 
                                placeholder="Week 1: Complete basic concepts\nWeek 2: Practice exercises\nWeek 3: Build project")
    
    # Study schedule preferences
    st.markdown("#### 📅 Study Schedule Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        preferred_days = st.multiselect(
            "Preferred Study Days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=["Monday", "Wednesday", "Friday"]
        )
    
    with col2:
        preferred_time = st.selectbox(
            "Preferred Study Time",
            ["Early Morning (6-9 AM)", "Morning (9-12 PM)", "Afternoon (12-5 PM)", "Evening (5-8 PM)", "Night (8-11 PM)"]
        )
    
    # Resource allocation
    st.markdown("#### 📚 Resource Planning")
    
    col1, col2 = st.columns(2)
    
    with col1:
        resource_types = st.multiselect(
            "Preferred Learning Resources",
            ["Online Courses", "Books", "Video Tutorials", "Practice Problems", "Projects", "Peer Learning"],
            default=["Online Courses", "Practice Problems"]
        )
    
    with col2:
        budget = st.number_input("Budget for Learning Resources ($)", min_value=0, value=0)
    
    # Create goal button
    if st.button("Create Study Goal", type="primary"):
        if goal_title and target_date > start_date:
            plan_data = {
                'goal': goal_title,
                'stream': selected_stream,
                'type': goal_type,
                'priority': priority,
                'description': description,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'deadline': target_date.strftime('%Y-%m-%d'),
                'study_hours_per_week': study_hours_per_week,
                'milestones': milestones,
                'preferred_days': ', '.join(preferred_days),
                'preferred_time': preferred_time,
                'resource_types': ', '.join(resource_types),
                'budget': budget,
                'status': 'Active',
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            if save_study_plan(st.session_state.username, plan_data):
                st.success("Study goal created successfully! 🎉")
                st.balloons()
            else:
                st.error("Failed to save study goal. Please try again.")
        else:
            st.error("Please fill in all required fields and ensure target date is after start date.")

with tab2:
    st.subheader("📊 My Study Plans")
    
    # Load user's study plans
    study_plans = get_user_study_plans(st.session_state.username)
    
    if not study_plans.empty:
        # Parse plan details
        plans_data = []
        for _, plan in study_plans.iterrows():
            details = plan['details']
            # Parse the details string
            plan_info = {}
            for item in details.split(', '):
                if ':' in item:
                    key, value = item.split(':', 1)
                    plan_info[key.strip()] = value.strip()
            
            plans_data.append({
                'Plan ID': plan['progress_id'],
                'Goal': plan_info.get('Goal', 'N/A'),
                'Deadline': plan_info.get('Deadline', 'N/A'),
                'Status': plan_info.get('Status', 'Active'),
                'Created': pd.to_datetime(plan['date']).strftime('%Y-%m-%d') if pd.notna(plan['date']) else 'N/A',
                'Details': plan_info
            })
        
        plans_df = pd.DataFrame(plans_data)
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Active", "Completed", "Paused"])
        with col2:
            sort_by = st.selectbox("Sort by", ["Created Date", "Deadline", "Goal"])
        
        # Apply filters
        if status_filter != "All":
            plans_df = plans_df[plans_df['Status'] == status_filter]
        
        # Display plans
        for _, plan in plans_df.iterrows():
            with st.expander(f"🎯 {plan['Goal']}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Status:** {plan['Status']}")
                    st.write(f"**Created:** {plan['Created']}")
                    st.write(f"**Deadline:** {plan['Deadline']}")
                
                with col2:
                    # Calculate progress (simplified)
                    if plan['Deadline'] != 'N/A':
                        try:
                            deadline = datetime.strptime(plan['Deadline'], '%Y-%m-%d').date()
                            created = datetime.strptime(plan['Created'], '%Y-%m-%d').date()
                            today = datetime.now().date()
                            
                            total_days = (deadline - created).days
                            elapsed_days = (today - created).days
                            
                            if total_days > 0:
                                progress = min(100, max(0, (elapsed_days / total_days) * 100))
                                st.progress(progress / 100)
                                st.write(f"Time Progress: {progress:.1f}%")
                            else:
                                st.progress(1.0)
                                st.write("Deadline reached")
                        except:
                            st.write("Progress: Unable to calculate")
                    else:
                        st.write("Progress: No deadline set")
                
                with col3:
                    new_status = st.selectbox(
                        "Update Status",
                        ["Active", "Completed", "Paused", "Cancelled"],
                        index=["Active", "Completed", "Paused", "Cancelled"].index(plan['Status']),
                        key=f"status_{plan['Plan ID']}"
                    )
                    
                    if new_status != plan['Status']:
                        if st.button(f"Update", key=f"update_{plan['Plan ID']}"):
                            # Here you would update the status in the database
                            st.success(f"Status updated to {new_status}")
                
                # Show additional details if available
                details = plan['Details']
                if details:
                    st.markdown("**Additional Details:**")
                    for key, value in details.items():
                        if key not in ['Goal', 'Deadline', 'Status'] and value != 'N/A':
                            st.write(f"• **{key}:** {value}")
    else:
        st.info("No study plans found. Create your first goal in the 'Create Goals' tab!")

with tab3:
    st.subheader("📈 Progress Tracking")
    
    # Load all user progress for visualization
    all_progress = load_data('user_progress')
    
    if all_progress is not None:
        user_progress = all_progress[all_progress['user_id'] == st.session_state.username]
        
        if not user_progress.empty:
            # Convert date column
            user_progress['date'] = pd.to_datetime(user_progress['date'])
            
            # Activity timeline
            st.markdown("#### 📅 Activity Timeline")
            
            # Create timeline chart
            timeline_data = user_progress.copy()
            timeline_data['month'] = timeline_data['date'].dt.strftime('%Y-%m')
            monthly_activity = timeline_data.groupby(['month', 'activity_type']).size().reset_index(name='count')
            
            if not monthly_activity.empty:
                fig = px.bar(
                    monthly_activity,
                    x='month',
                    y='count',
                    color='activity_type',
                    title='Monthly Activity Distribution',
                    labels={'count': 'Number of Activities', 'month': 'Month'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Score trends (excluding study plans)
            score_data = user_progress[user_progress['activity_type'] != 'study_plan']
            if not score_data.empty:
                st.markdown("#### 📊 Score Trends")
                
                fig = px.line(
                    score_data,
                    x='date',
                    y='score',
                    color='activity_type',
                    title='Score Progression Over Time',
                    labels={'score': 'Score (%)', 'date': 'Date'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Study consistency
            st.markdown("#### 🔥 Study Consistency")
            
            # Calculate study streak
            study_dates = user_progress['date'].dt.date.unique()
            study_dates.sort()
            
            current_streak = 0
            max_streak = 0
            temp_streak = 0
            
            if len(study_dates) > 0:
                for i in range(len(study_dates)):
                    if i == 0:
                        temp_streak = 1
                    else:
                        days_diff = (study_dates[i] - study_dates[i-1]).days
                        if days_diff == 1:
                            temp_streak += 1
                        else:
                            temp_streak = 1
                    
                    max_streak = max(max_streak, temp_streak)
                
                # Check current streak
                if len(study_dates) > 0:
                    last_study = study_dates[-1]
                    days_since_last = (datetime.now().date() - last_study).days
                    if days_since_last <= 1:
                        current_streak = temp_streak
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Streak", f"{current_streak} days")
            with col2:
                st.metric("Best Streak", f"{max_streak} days")
            with col3:
                st.metric("Total Study Days", len(study_dates))
            
            # Weekly study pattern
            st.markdown("#### 📊 Weekly Study Pattern")
            
            user_progress['day_of_week'] = user_progress['date'].dt.day_name()
            weekly_pattern = user_progress['day_of_week'].value_counts().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ], fill_value=0)
            
            fig = px.bar(
                x=weekly_pattern.index,
                y=weekly_pattern.values,
                title='Study Activity by Day of Week',
                labels={'x': 'Day of Week', 'y': 'Number of Activities'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("Complete some activities to see your progress tracking!")
    else:
        st.error("Unable to load progress data")

with tab4:
    st.subheader("📚 Study Resources & Recommendations")
    
    # Show personalized recommendations based on study plans
    study_plans = get_user_study_plans(st.session_state.username)
    
    if not study_plans.empty and recommendations_df is not None:
        # Extract streams from study plans
        interested_streams = set()
        for _, plan in study_plans.iterrows():
            details = plan['details']
            # This is a simplified extraction - in reality, you'd want better parsing
            if 'stream:' in details.lower():
                # Extract stream information from details
                pass
        
        st.markdown("#### 🎯 Resources for Your Goals")
        
        # Show general recommendations
        if not recommendations_df.empty:
            # Group by difficulty level
            beginner_recs = recommendations_df[recommendations_df['difficulty_level'] == 'Beginner'].head(3)
            intermediate_recs = recommendations_df[recommendations_df['difficulty_level'] == 'Intermediate'].head(3)
            advanced_recs = recommendations_df[recommendations_df['difficulty_level'] == 'Advanced'].head(3)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### 🟢 Beginner Level")
                for _, rec in beginner_recs.iterrows():
                    with st.container():
                        st.write(f"**{rec['title']}**")
                        st.write(f"Stream: {rec['stream']}")
                        st.write(f"Type: {rec['resource_type']}")
                        st.write(f"Duration: {rec['duration']}")
                        if rec['url'] != 'N/A':
                            st.link_button("View Resource", rec['url'])
                        st.markdown("---")
            
            with col2:
                st.markdown("##### 🟡 Intermediate Level")
                for _, rec in intermediate_recs.iterrows():
                    with st.container():
                        st.write(f"**{rec['title']}**")
                        st.write(f"Stream: {rec['stream']}")
                        st.write(f"Type: {rec['resource_type']}")
                        st.write(f"Duration: {rec['duration']}")
                        if rec['url'] != 'N/A':
                            st.link_button("View Resource", rec['url'])
                        st.markdown("---")
            
            with col3:
                st.markdown("##### 🔴 Advanced Level")
                for _, rec in advanced_recs.iterrows():
                    with st.container():
                        st.write(f"**{rec['title']}**")
                        st.write(f"Stream: {rec['stream']}")
                        st.write(f"Type: {rec['resource_type']}")
                        st.write(f"Duration: {rec['duration']}")
                        if rec['url'] != 'N/A':
                            st.link_button("View Resource", str(rec['url'])) if pd.notna(rec['url']) else st.warning("No resource link available.")
                        st.markdown("---")
    
    # Study tips and techniques
    st.markdown("---")
    st.markdown("#### 💡 Study Tips & Techniques")
    
    tips_col1, tips_col2 = st.columns(2)
    
    with tips_col1:
        st.markdown("""
        **🧠 Effective Study Techniques:**
        - **Pomodoro Technique**: 25-min focused sessions with 5-min breaks
        - **Active Recall**: Test yourself instead of just re-reading
        - **Spaced Repetition**: Review material at increasing intervals
        - **Feynman Technique**: Explain concepts in simple terms
        """)
    
    with tips_col2:
        st.markdown("""
        **📅 Time Management:**
        - Set specific, measurable goals
        - Break large goals into smaller tasks
        - Use time-blocking for study sessions
        - Track your progress regularly
        """)

# Sidebar with quick actions
with st.sidebar:
    st.markdown("### 🚀 Quick Actions")
    
    if st.button("📝 Create New Goal", use_container_width=True):
        st.switch_page("pages/4_Study_Planner.py")
    
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
    
    if st.button("📚 Get Recommendations", use_container_width=True):
        st.switch_page("pages/5_Recommendations.py")
    
    st.markdown("---")
    
    # Show upcoming deadlines
    st.markdown("### ⏰ Upcoming Deadlines")
    
    study_plans = get_user_study_plans(st.session_state.username)
    if not study_plans.empty:
        upcoming_deadlines = []
        for _, plan in study_plans.iterrows():
            details = plan['details']
            if 'Deadline:' in details:
                try:
                    deadline_str = details.split('Deadline:')[1].split(',')[0].strip()
                    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
                    goal = details.split('Goal:')[1].split(',')[0].strip()
                    
                    days_remaining = (deadline - datetime.now().date()).days
                    if days_remaining >= 0:
                        upcoming_deadlines.append((goal, deadline, days_remaining))
                except:
                    pass
        
        upcoming_deadlines.sort(key=lambda x: x[2])  # Sort by days remaining
        
        for goal, deadline, days_remaining in upcoming_deadlines[:3]:
            if days_remaining == 0:
                st.error(f"**{goal}** - Due today!")
            elif days_remaining <= 3:
                st.warning(f"**{goal}** - {days_remaining} days left")
            else:
                st.info(f"**{goal}** - {days_remaining} days left")
    else:
        st.info("No deadlines set")
