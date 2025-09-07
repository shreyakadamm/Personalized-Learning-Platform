import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.data_handler import load_data
from utils.quiz_engine import CareerQuizEngine, save_quiz_results
import plotly.express as px
import pandas as pd

# Require authentication
require_auth()

st.set_page_config(page_title="Career Quiz", page_icon="💼", layout="wide")

st.title("💼 Career Discovery Quiz")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Initialize session state for career quiz
if 'career_quiz_state' not in st.session_state:
    st.session_state.career_quiz_state = 'start'
if 'career_questions' not in st.session_state:
    st.session_state.career_questions = []
if 'career_current_question' not in st.session_state:
    st.session_state.career_current_question = 0
if 'career_answers' not in st.session_state:
    st.session_state.career_answers = {}

# Load data
career_quiz_df = load_data('career_quiz')
streams_df = load_data('streams')

if career_quiz_df is None:
    st.error("Unable to load career quiz data")
    st.stop()

if streams_df is None:
    st.error("Unable to load streams data")
    st.stop()

# Initialize career quiz engine
career_engine = CareerQuizEngine(career_quiz_df)

def start_career_quiz():
    """Initialize the career quiz"""
    questions = career_engine.get_all_questions()
    st.session_state.career_questions = questions
    st.session_state.career_current_question = 0
    st.session_state.career_answers = {}
    st.session_state.career_quiz_state = 'in_progress'

# Quiz start screen
if st.session_state.career_quiz_state == 'start':
    st.markdown("""
    ### Discover Your Ideal Career Path! 🚀
    
    This comprehensive career assessment will help you identify career fields that match your:
    
    - **Interests and Passions**: What truly motivates you
    - **Skills and Abilities**: Your natural strengths
    - **Work Preferences**: How you like to work
    - **Values and Goals**: What matters most to you
    
    #### What You'll Get:
    - **Personalized Career Recommendations**: Fields that match your profile
    - **Learning Path Suggestions**: Courses and resources to get started
    - **Skills Assessment**: Understanding of your strengths
    - **Future Planning**: Guidance for your educational journey
    
    #### Assessment Details:
    - **Duration**: 10-15 minutes
    - **Questions**: 15 thoughtfully designed questions
    - **Format**: Mix of scales and multiple choice
    - **Results**: Detailed career field analysis
    
    #### Instructions:
    - Answer honestly based on your true preferences
    - Consider what genuinely interests you, not what others expect
    - Think about your ideal work environment and activities
    - There are no right or wrong answers
    
    Ready to discover your career path?
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Start Career Quiz", type="primary", use_container_width=True):
            start_career_quiz()
            st.rerun()

# Quiz in progress
elif st.session_state.career_quiz_state == 'in_progress':
    questions = st.session_state.career_questions
    current_q = st.session_state.career_current_question
    
    if current_q < len(questions):
        question = questions[current_q]
        
        # Progress bar
        progress = (current_q + 1) / len(questions)
        st.progress(progress)
        st.write(f"Question {current_q + 1} of {len(questions)}")
        
        # Display question
        st.markdown(f"### {question['question']}")
        
        # Show career field this question relates to
        st.info(f"This question helps assess your fit for: **{question['career_field']}**")
        
        # Display options based on question type
        options = ['a', 'b', 'c', 'd']
        option_texts = []
        
        for opt in options:
            option_key = f'option_{opt}'
            if option_key in question and question[option_key]:
                option_texts.append(f"{question[option_key]}")
        
        if option_texts:
            if question['question_type'] == 'scale':
                st.markdown("**Rate your level of agreement or interest:**")
                selected_answer = st.radio(
                    "Select your answer:",
                    options=option_texts,
                    index=None,
                    key=f"career_q_{current_q}"
                )
            else:  # multiple_choice
                st.markdown("**Choose the option that best describes you:**")
                selected_answer = st.radio(
                    "Select your answer:",
                    options=option_texts,
                    index=None,
                    key=f"career_q_{current_q}"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if current_q > 0:
                    if st.button("← Previous", key=f"prev_{current_q}"):
                        st.session_state.career_current_question -= 1
                        st.rerun()
            
            with col2:
                if selected_answer:
                    button_text = "Finish Quiz" if current_q == len(questions) - 1 else "Next Question →"
                    if st.button(button_text, type="primary", key=f"next_{current_q}"):
                        # Find the option letter
                        answer_letter = None
                        for i, opt_text in enumerate(option_texts):
                            if opt_text == selected_answer:
                                answer_letter = options[i]
                                break
                        
                        st.session_state.career_answers[current_q] = answer_letter
                        
                        if current_q == len(questions) - 1:
                            st.session_state.career_quiz_state = 'completed'
                        else:
                            st.session_state.career_current_question += 1
                        
                        st.rerun()

# Quiz completed
elif st.session_state.career_quiz_state == 'completed':
    st.balloons()
    
    # Calculate career scores
    answers = st.session_state.career_answers
    career_scores = career_engine.calculate_career_scores(answers)
    
    # Get recommended streams
    recommended_streams = career_engine.get_recommended_streams(career_scores, streams_df)
    
    st.markdown("### 🎉 Career Assessment Complete!")
    
    # Display career field scores
    st.markdown("---")
    st.markdown("### 📊 Your Career Field Scores")
    
    # Create a dataframe for visualization
    career_data = []
    for field, scores in career_scores.items():
        career_data.append({
            'Career Field': field,
            'Score': scores['average'],
            'Questions': scores['count']
        })
    
    career_df = pd.DataFrame(career_data)
    career_df = career_df.sort_values('Score', ascending=True)
    
    # Create horizontal bar chart
    fig = px.bar(
        career_df,
        x='Score',
        y='Career Field',
        orientation='h',
        title='Your Career Field Compatibility Scores',
        labels={'Score': 'Compatibility Score (1-4)', 'Career Field': 'Career Fields'},
        color='Score',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top career recommendations
    st.markdown("---")
    st.markdown("### 🌟 Your Top Career Matches")
    
    sorted_careers = sorted(career_scores.items(), key=lambda x: x[1]['average'], reverse=True)
    
    for i, (field, scores) in enumerate(sorted_careers[:3]):
        rank_emoji = ["🥇", "🥈", "🥉"][i]
        st.markdown(f"""
        **{rank_emoji} {field}** - Score: {scores['average']:.1f}/4.0
        
        Based on your responses, you show strong alignment with {field.lower()} careers.
        """)
    
    # Recommended learning streams
    st.markdown("---")
    st.markdown("### 📚 Recommended Learning Streams")
    
    if recommended_streams:
        for i, stream in enumerate(recommended_streams):
            with st.expander(f"🎓 {stream['stream_name']}", expanded=i < 2):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {stream['description']}")
                    st.write(f"**Category:** {stream['category']}")
                    st.write(f"**Difficulty:** {stream['difficulty_level']}")
                    st.write(f"**Match Reason:** Based on your high score in {stream['career_field']}")
                
                with col2:
                    st.metric("Match Score", f"{stream['match_score']:.1f}/4.0")
                    
                    if st.button(f"Explore {stream['stream_name']}", key=f"explore_{i}"):
                        # Save interest and redirect to recommendations
                        st.session_state.interested_stream = stream['stream_name']
                        st.switch_page("pages/5_Recommendations.py")
    else:
        st.info("No specific stream recommendations available. Explore our general courses!")
    
    # Detailed insights
    st.markdown("---")
    st.markdown("### 🔍 Detailed Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💪 Your Strengths")
        top_fields = sorted_careers[:2]
        for field, scores in top_fields:
            st.success(f"**{field}**: You show strong aptitude and interest")
    
    with col2:
        st.markdown("#### 🌱 Growth Areas")
        bottom_fields = sorted_careers[-2:]
        for field, scores in reversed(bottom_fields):
            st.info(f"**{field}**: Consider exploring to broaden your horizons")
    
    # Career advice
    st.markdown("---")
    st.markdown("### 💡 Personalized Career Advice")
    
    top_field = sorted_careers[0][0]
    top_score = sorted_careers[0][1]['average']
    
    if top_score >= 3.5:
        advice = f"You have a very strong match with {top_field}! Consider pursuing specialized courses and certifications in this area."
    elif top_score >= 3.0:
        advice = f"You show good alignment with {top_field}. Explore this field further through online courses and projects."
    elif top_score >= 2.5:
        advice = f"You have some interest in {top_field}. Consider taking introductory courses to see if it's right for you."
    else:
        advice = "Your interests span multiple areas. Consider exploring different fields to find your true passion."
    
    st.info(advice)
    
    # Save results
    details = f"Top career: {top_field}, Score: {top_score:.1f}, Total fields assessed: {len(career_scores)}"
    save_success = save_quiz_results(
        user_id=st.session_state.username,
        quiz_type='career_quiz',
        score=top_score * 25,  # Convert to percentage
        details=details
    )
    
    if save_success:
        st.success("Career assessment results saved to your profile!")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Retake Assessment"):
            # Reset quiz state
            for key in ['career_quiz_state', 'career_questions', 'career_current_question', 'career_answers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("View Learning Resources"):
            st.switch_page("pages/5_Recommendations.py")
    
    with col3:
        if st.button("Create Study Plan"):
            st.switch_page("pages/4_Study_Planner.py")

# Sidebar information
with st.sidebar:
    st.markdown("### 💼 About Career Assessment")
    st.markdown("""
    This quiz evaluates your compatibility with different career fields based on:
    
    - **Work preferences**
    - **Skill interests**
    - **Value alignment**
    - **Learning style**
    """)
    
    if st.session_state.career_quiz_state == 'in_progress':
        st.markdown("---")
        st.markdown("### 📊 Progress")
        questions = st.session_state.career_questions
        current_q = st.session_state.career_current_question
        
        st.write(f"Completed: {current_q}/{len(questions)}")
        st.write(f"Remaining: {len(questions) - current_q}")
        
        # Show career fields covered so far
        fields_covered = set()
        for i in range(current_q):
            if i < len(questions):
                fields_covered.add(questions[i]['career_field'])
        
        if fields_covered:
            st.write("**Fields assessed:**")
            for field in fields_covered:
                st.write(f"• {field}")
    
    st.markdown("---")
    st.markdown("### 🎯 Tips for Best Results")
    st.markdown("""
    - Be honest about your preferences
    - Think about what energizes you
    - Consider your natural strengths
    - Don't overthink - go with your gut
    """)
