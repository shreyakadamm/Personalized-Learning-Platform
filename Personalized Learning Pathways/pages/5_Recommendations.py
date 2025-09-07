import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.data_handler import load_data
import pandas as pd
import plotly.express as px

# Require authentication
require_auth()

st.set_page_config(page_title="Recommendations", page_icon="📚", layout="wide")

st.title("📚 Personalized Learning Recommendations")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Load data
recommendations_df = load_data('recommendations')
streams_df = load_data('streams')
progress_df = load_data('user_progress')

if recommendations_df is None:
    st.error("Unable to load recommendations data")
    st.stop()

# Check if user has taken career quiz
user_progress = progress_df[progress_df['user_id'] == st.session_state.username] if progress_df is not None else pd.DataFrame()
has_career_quiz = not user_progress[user_progress['activity_type'] == 'career_quiz'].empty
has_iq_test = not user_progress[user_progress['activity_type'] == 'iq_test'].empty

# Sidebar filters
with st.sidebar:
    st.markdown("### 🎯 Filter Recommendations")
    
    # Stream filter
    if streams_df is not None:
        available_streams = ['All'] + sorted(recommendations_df['stream'].unique().tolist())
        selected_stream = st.selectbox("Select Stream", available_streams)
    else:
        selected_stream = st.selectbox("Select Stream", ['All'])
    
    # Difficulty filter
    difficulty_levels = ['All'] + sorted(recommendations_df['difficulty_level'].unique().tolist())
    selected_difficulty = st.selectbox("Difficulty Level", difficulty_levels)
    
    # Resource type filter
    resource_types = ['All'] + sorted(recommendations_df['resource_type'].unique().tolist())
    selected_resource_type = st.selectbox("Resource Type", resource_types)
    
    # Duration filter
    st.markdown("#### Duration")
    show_self_paced = st.checkbox("Include Self-paced", value=True)
    max_weeks = st.slider("Maximum Duration (weeks)", 1, 20, 20)
    
    st.markdown("---")
    
    # Personalization status
    st.markdown("### 🎯 Personalization Status")
    
    if has_career_quiz:
        st.success("✅ Career preferences analyzed")
    else:
        st.warning("❌ Take career quiz for better recommendations")
        if st.button("Take Career Quiz"):
            st.switch_page("pages/3_Career_Quiz.py")
    
    if has_iq_test:
        st.success("✅ Skill level assessed")
    else:
        st.warning("❌ Take IQ test for difficulty matching")
        if st.button("Take IQ Test"):
            st.switch_page("pages/2_IQ_Test.py")

# Main content
if has_career_quiz or has_iq_test:
    st.markdown("### 🌟 Personalized for You")
    
    # Get user's career quiz results if available
    career_results = None
    iq_results = None
    
    if has_career_quiz:
        career_progress = user_progress[user_progress['activity_type'] == 'career_quiz'].iloc[-1]
        career_details = career_progress['details']
        # Extract top career from details
        if 'Top career:' in career_details:
            top_career = career_details.split('Top career:')[1].split(',')[0].strip()
            st.info(f"Based on your career quiz, you're interested in: **{top_career}**")
    
    if has_iq_test:
        iq_progress = user_progress[user_progress['activity_type'] == 'iq_test'].iloc[-1]
        iq_score = iq_progress['score']
        
        # Recommend difficulty based on IQ test performance
        if iq_score >= 85:
            recommended_difficulty = "Advanced"
        elif iq_score >= 70:
            recommended_difficulty = "Intermediate"
        else:
            recommended_difficulty = "Beginner"
        
        st.info(f"Based on your assessment score ({iq_score:.1f}%), we recommend **{recommended_difficulty}** level courses")

else:
    st.markdown("### 📚 General Recommendations")
    st.info("Take our assessments to get personalized recommendations!")

# Apply filters
filtered_recs = recommendations_df.copy()

if selected_stream != 'All':
    filtered_recs = filtered_recs[filtered_recs['stream'] == selected_stream]

if selected_difficulty != 'All':
    filtered_recs = filtered_recs[filtered_recs['difficulty_level'] == selected_difficulty]

if selected_resource_type != 'All':
    filtered_recs = filtered_recs[filtered_recs['resource_type'] == selected_resource_type]

# Filter by duration
if not show_self_paced:
    filtered_recs = filtered_recs[filtered_recs['duration'] != 'Self-paced']

# Convert duration to numeric for filtering (simplified)
def parse_duration(duration_str):
    if 'Self-paced' in duration_str:
        return 0
    try:
        if 'week' in duration_str.lower():
            return int(duration_str.split()[0])
        elif 'month' in duration_str.lower():
            return int(duration_str.split()[0]) * 4
        else:
            return 0
    except:
        return 0

filtered_recs['duration_weeks'] = filtered_recs['duration'].apply(parse_duration)
if not show_self_paced:
    filtered_recs = filtered_recs[filtered_recs['duration_weeks'] <= max_weeks]

# Sort recommendations (prioritize based on user data)
if has_career_quiz and 'top_career' in locals():
    # Prioritize based on career interest (simplified mapping)
    career_to_stream = {
        'Technology': ['Computer Science', 'Data Science', 'Information Technology'],
        'Science': ['Mathematics', 'Physics', 'Chemistry', 'Biology'],
        'Business': ['Business Administration', 'Economics', 'Marketing'],
        'Creative Arts': ['Creative Arts', 'Graphic Design', 'Music'],
        'Healthcare': ['Medicine', 'Nursing', 'Biology'],
        'Engineering': ['Engineering', 'Mechanical Engineering', 'Electrical Engineering']
    }
    
    # This is a simplified prioritization
    filtered_recs = filtered_recs.sort_values(['stream', 'difficulty_level'])

# Display statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Recommendations", len(filtered_recs))

with col2:
    unique_streams = filtered_recs['stream'].nunique()
    st.metric("Unique Streams", unique_streams)

with col3:
    free_resources = len(filtered_recs[filtered_recs['url'] != 'N/A'])
    st.metric("Available Links", free_resources)

with col4:
    avg_duration = filtered_recs[filtered_recs['duration_weeks'] > 0]['duration_weeks'].mean()
    st.metric("Avg Duration", f"{avg_duration:.1f} weeks" if pd.notna(avg_duration) else "N/A")

# Visualization
if not filtered_recs.empty:
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Stream distribution
        stream_counts = filtered_recs['stream'].value_counts()
        fig1 = px.pie(
            values=stream_counts.values,
            names=stream_counts.index,
            title='Recommendations by Stream'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Difficulty distribution
        difficulty_counts = filtered_recs['difficulty_level'].value_counts()
        fig2 = px.bar(
            x=difficulty_counts.index,
            y=difficulty_counts.values,
            title='Recommendations by Difficulty Level',
            labels={'x': 'Difficulty Level', 'y': 'Count'}
        )
        st.plotly_chart(fig2, use_container_width=True)

# Display recommendations
st.markdown("---")
st.markdown("### 📖 Learning Resources")

if filtered_recs.empty:
    st.warning("No recommendations match your current filters. Try adjusting the filters.")
else:
    # Group by stream for better organization
    streams = filtered_recs['stream'].unique()
    
    for stream in sorted(streams):
        stream_recs = filtered_recs[filtered_recs['stream'] == stream]
        
        with st.expander(f"📚 {stream} ({len(stream_recs)} resources)", expanded=True):
            
            for idx, rec in stream_recs.iterrows():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"#### {rec['title']}")
                    st.write(f"**Description:** {rec['description']}")
                    
                    # Tags
                    tag_col1, tag_col2, tag_col3 = st.columns(3)
                    with tag_col1:
                        st.badge(f"📊 {rec['difficulty_level']}")
                    with tag_col2:
                        st.badge(f"📝 {rec['resource_type']}")
                    with tag_col3:
                        st.badge(f"⏱️ {rec['duration']}")
                
                with col2:
                    # Platform info
                    if rec['platform'] != 'N/A':
                        st.write(f"**Platform:** {rec['platform']}")
                    
                    # Action buttons
                    if rec['url'] != 'N/A':
                        st.link_button("🔗 View Resource", str(rec['url']), use_container_width=True) if pd.notna(rec['url']) else st.warning("No resource link available.")
                    
                    if st.button(f"📌 Add to Study Plan", key=f"add_{idx}", use_container_width=True):
                        # Add to study plan (redirect to study planner with pre-filled data)
                        st.session_state.prefill_goal = rec['title']
                        st.session_state.prefill_stream = rec['stream']
                        st.success(f"Added {rec['title']} to study goals!")
                        st.switch_page("pages/4_Study_Planner.py")
                
                st.markdown("---")

# Featured recommendations
st.markdown("---")
st.markdown("### ⭐ Featured Recommendations")

# Show top recommendations based on user profile
featured_recs = filtered_recs.head(6) if not filtered_recs.empty else pd.DataFrame()

if not featured_recs.empty:
    cols = st.columns(3)
    
    for idx, (_, rec) in enumerate(featured_recs.iterrows()):
        col_idx = idx % 3
        
        with cols[col_idx]:
            with st.container():
                st.markdown(f"##### {rec['title']}")
                st.write(f"**{rec['stream']}**")
                st.write(f"{rec['description'][:100]}...")
                
                # Quick stats
                st.caption(f"⏱️ {rec['duration']} | 📊 {rec['difficulty_level']}")
                
                url = rec.get("url")
if isinstance(url, str) and url.strip():
    st.link_button("View", url)


# Learning path suggestions
st.markdown("---")
st.markdown("### 🛣️ Suggested Learning Paths")

if streams_df is not None and not filtered_recs.empty:
    # Create learning paths based on difficulty progression
    popular_streams = filtered_recs['stream'].value_counts().head(3).index
    
    for stream in popular_streams:
        stream_recs = filtered_recs[filtered_recs['stream'] == stream]
        
        if len(stream_recs) >= 2:
            with st.expander(f"🎯 {stream} Learning Path"):
                st.write(f"Complete learning journey in {stream}")
                
                # Sort by difficulty
                difficulty_order = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3}
                stream_recs['difficulty_order'] = stream_recs['difficulty_level'].map(difficulty_order)
                path_recs = stream_recs.sort_values('difficulty_order').head(4)
                
                for idx, (_, rec) in enumerate(path_recs.iterrows()):
                    step_num = idx + 1
                    st.markdown(f"**Step {step_num}: {rec['title']}**")
                    st.write(f"• {rec['description']}")
                    st.write(f"• Duration: {rec['duration']} | Difficulty: {rec['difficulty_level']}")
                    
                    if rec['url'] != 'N/A':
                        url = rec.get('url') if isinstance(rec, dict) else None

                    if pd.notna(url) and isinstance(url, str) and url.strip():
                        st.link_button(f"Start Step {step_num}", url.strip(), key=f"path_{stream}_{idx}")
                    else:
                        st.warning(f"⚠️ No valid URL for Step {step_num}.")                    
                    if idx < len(path_recs) - 1:
                        st.write("↓")

# Call-to-action for assessments
if not has_career_quiz or not has_iq_test:
    st.markdown("---")
    st.markdown("### 🎯 Get Better Recommendations")
    
    col1, col2 = st.columns(2)
    
    if not has_career_quiz:
        with col1:
            st.markdown("""
            #### 💼 Take Career Quiz
            Discover your ideal career path and get targeted course recommendations.
            """)
            if st.button("Start Career Assessment", type="primary"):
                st.switch_page("pages/3_Career_Quiz.py")
    
    if not has_iq_test:
        with col2:
            st.markdown("""
            #### 🧠 Take IQ Test
            Assess your skills to get difficulty-matched learning resources.
            """)
            if st.button("Start Skill Assessment", type="primary"):
                st.switch_page("pages/2_IQ_Test.py")