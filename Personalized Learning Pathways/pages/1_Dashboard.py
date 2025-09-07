import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.progress_tracker import ProgressTracker
from utils.data_handler import load_data

# Require authentication
require_auth()

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Your Learning Dashboard")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Initialize progress tracker
progress_tracker = ProgressTracker(st.session_state.username)

# Get activity summary
summary = progress_tracker.get_activity_summary()

# Top metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Activities",
        value=summary['total_activities'],
        delta=summary['recent_activities']
    )

with col2:
    st.metric(
        label="Average Score",
        value=f"{summary['average_score']:.1f}%",
        delta="Target: 85%"
    )

with col3:
    learning_streak = progress_tracker.get_learning_streak()
    st.metric(
        label="Learning Streak",
        value=f"{learning_streak} days",
        delta="Keep it up!"
    )

with col4:
    total_streams = len(load_data('streams')) if load_data('streams') is not None else 0
    st.metric(
        label="Available Streams",
        value=total_streams,
        delta="Explore more"
    )

st.markdown("---")

# Charts section
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Progress Over Time")
    progress_chart = progress_tracker.create_progress_chart()
    if progress_chart:
        st.plotly_chart(progress_chart, use_container_width=True)
    else:
        st.info("Take some quizzes to see your progress chart!")

with col2:
    st.subheader("📊 Activity Distribution")
    activity_chart = progress_tracker.create_activity_distribution_chart()
    if activity_chart:
        st.plotly_chart(activity_chart, use_container_width=True)
    else:
        st.info("Complete activities to see distribution!")

# Performance gauge
st.subheader("🎯 Overall Performance")
performance_gauge = progress_tracker.create_performance_gauge()
if performance_gauge:
    st.plotly_chart(performance_gauge, use_container_width=True)
else:
    st.info("Complete scored activities to see your performance gauge!")

st.markdown("---")

# Recent achievements and suggestions
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Recent Achievements")
    achievements = progress_tracker.get_recent_achievements()
    
    if achievements:
        for achievement in achievements:
            st.success(f"**{achievement['type']}**: {achievement['description']} ({achievement['date']})")
    else:
        st.info("Complete activities to earn achievements!")

with col2:
    st.subheader("💡 Improvement Suggestions")
    suggestions = progress_tracker.get_improvement_suggestions()
    
    for suggestion in suggestions:
        st.info(suggestion)

st.markdown("---")

# Quick actions
st.subheader("🚀 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Take IQ Test", key="dashboard_iq_test"):
        st.switch_page("pages/2_IQ_Test.py")

with col2:
    if st.button("Career Quiz", key="dashboard_career_quiz"):
        st.switch_page("pages/3_Career_Quiz.py")

with col3:
    if st.button("Study Planner", key="dashboard_study_planner"):
        st.switch_page("pages/4_Study_Planner.py")

with col4:
    if st.button("View Recommendations", key="dashboard_recommendations"):
        st.switch_page("pages/5_Recommendations.py")

# Recent activity feed
st.markdown("---")
st.subheader("📝 Recent Activity")

progress_df = progress_tracker.progress_df
if not progress_df.empty:
    # Show last 5 activities
    recent_activities = progress_df.head(5)
    
    for _, activity in recent_activities.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{activity['activity_type'].replace('_', ' ').title()}**")
                if activity['details']:
                    st.caption(activity['details'])
            
            with col2:
                if activity['activity_type'] != 'study_plan':
                    st.write(f"Score: {activity['score']:.1f}%")
            
            with col3:
                st.write(activity['date'].strftime('%Y-%m-%d'))
            
            st.markdown("---")
else:
    st.info("No recent activities. Start learning to see your activity feed!")

# User profile summary
with st.sidebar:
    st.subheader("👤 Profile Summary")
    st.write(f"**Name:** {user_data['Name']}")
    st.write(f"**Age:** {user_data['Age']}")
    st.write(f"**Email:** {user_data['Email']}")
    
    st.markdown("---")
    
    st.subheader("📊 Quick Stats")
    st.write(f"Total Activities: {summary['total_activities']}")
    st.write(f"Average Score: {summary['average_score']:.1f}%")
    st.write(f"Learning Streak: {learning_streak} days")
