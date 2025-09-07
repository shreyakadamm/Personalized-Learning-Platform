import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.data_handler import load_data
from utils.quiz_engine import QuizEngine 
from utils.data_handler import save_quiz_results
import random

# Require authentication
require_auth()

st.set_page_config(page_title="IQ Test", page_icon="🧠", layout="wide")

st.title("🧠 IQ Test")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Initialize session state for quiz
if 'iq_quiz_state' not in st.session_state:
    st.session_state.iq_quiz_state = 'start'
if 'iq_questions' not in st.session_state:
    st.session_state.iq_questions = []
if 'iq_current_question' not in st.session_state:
    st.session_state.iq_current_question = 0
if 'iq_answers' not in st.session_state:
    st.session_state.iq_answers = {}
if 'iq_start_time' not in st.session_state:
    st.session_state.iq_start_time = None

# Load questions data
questions_df = load_data('questions')
if questions_df is None:
    st.error("Unable to load questions data")
    st.stop()

# Initialize quiz engine
quiz_engine = QuizEngine(questions_df)

def start_quiz():
    """Initialize the IQ quiz"""
    # Get mixed questions from different streams and difficulties
    all_questions = []
    
    # Get questions from different difficulty levels
    beginner_questions = quiz_engine.get_random_questions(difficulty='Beginner', count=5)
    intermediate_questions = quiz_engine.get_random_questions(difficulty='Intermediate', count=10)
    advanced_questions = quiz_engine.get_random_questions(difficulty='Advanced', count=5)
    
    all_questions.extend(beginner_questions)
    all_questions.extend(intermediate_questions)
    all_questions.extend(advanced_questions)
    
    # Shuffle questions
    random.shuffle(all_questions)
    
    st.session_state.iq_questions = all_questions[:20]  # Take 20 questions
    st.session_state.iq_current_question = 0
    st.session_state.iq_answers = {}
    st.session_state.iq_quiz_state = 'in_progress'
    st.session_state.iq_start_time = st.session_state.get('iq_start_time', None)

def calculate_iq_score(correct_answers, total_questions, time_taken):
    """Calculate IQ score based on correct answers and time"""
    accuracy = (correct_answers / total_questions) * 100
    
    # Base score calculation
    base_score = 85 + (accuracy - 50) * 0.6  # Scale around average IQ of 100
    
    # Time bonus/penalty (optional, can be adjusted)
    # Assuming optimal time is 30 seconds per question
    optimal_time = total_questions * 30
    time_factor = min(1.2, optimal_time / max(time_taken, 1))  # Cap at 20% bonus
    
    final_score = base_score * time_factor
    
    # Ensure score is within reasonable IQ range
    final_score = max(70, min(150, final_score))
    
    return round(final_score)

# Quiz start screen
if st.session_state.iq_quiz_state == 'start':
    st.markdown("""
    ### Welcome to the IQ Assessment Test! 🧠
    
    This comprehensive test will evaluate your cognitive abilities across multiple domains:
    
    - **Logical Reasoning**: Problem-solving and pattern recognition
    - **Mathematical Skills**: Numerical and analytical thinking
    - **Verbal Comprehension**: Language and communication skills
    - **Scientific Knowledge**: Understanding of scientific concepts
    - **General Knowledge**: Broad intellectual awareness
    
    #### Test Details:
    - **Duration**: Approximately 20-30 minutes
    - **Questions**: 20 carefully selected questions
    - **Difficulty**: Mixed levels (Beginner to Advanced)
    - **Scoring**: Based on accuracy and time efficiency
    
    #### Instructions:
    1. Read each question carefully
    2. Select the best answer from the given options
    3. You cannot go back to previous questions
    4. Take your time but work efficiently
    5. Your final IQ score will be calculated automatically
    
    Are you ready to begin?
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Start IQ Test", type="primary", use_container_width=True):
            start_quiz()
            st.rerun()

# Quiz in progress
elif st.session_state.iq_quiz_state == 'in_progress':
    questions = st.session_state.iq_questions
    current_q = st.session_state.iq_current_question
    
    if current_q < len(questions):
        question = questions[current_q]
        
        # Progress bar
        progress = (current_q + 1) / len(questions)
        st.progress(progress)
        st.write(f"Question {current_q + 1} of {len(questions)}")
        
        # Display question
        st.markdown(f"### {question['question']}")
        
        # Show difficulty and stream
        col1, col2 = st.columns(2)
        with col1:
            st.badge(f"Difficulty: {question['difficulty']}")
        with col2:
            st.badge(f"Subject: {question['stream']}")
        
        # Display options
        options = ['a', 'b', 'c', 'd']
        option_texts = []
        
        for opt in options:
            option_key = f'option_{opt}'
            if option_key in question and question[option_key]:
                option_texts.append(f"{opt.upper()}) {question[option_key]}")
        
        if option_texts:
            selected_answer = st.radio(
                "Select your answer:",
                options=option_texts,
                index=None,
                key=f"iq_q_{current_q}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if current_q > 0:
                    st.write("Previous questions cannot be modified")
            
            with col2:
                if selected_answer and st.button("Next Question", type="primary"):
                    # Extract the letter from selected answer
                    answer_letter = selected_answer[0].lower()
                    st.session_state.iq_answers[current_q] = answer_letter
                    st.session_state.iq_current_question += 1
                    
                    if st.session_state.iq_current_question >= len(questions):
                        st.session_state.iq_quiz_state = 'completed'
                    
                    st.rerun()
        
        # Show explanation for previous question if available
        if current_q > 0 and 'explanation' in questions[current_q - 1]:
            with st.expander("Previous Question Explanation"):
                prev_q = questions[current_q - 1]
                st.write(f"**Question:** {prev_q['question']}")
                st.write(f"**Correct Answer:** {prev_q['correct_answer'].upper()}")
                st.write(f"**Explanation:** {prev_q['explanation']}")

# Quiz completed
elif st.session_state.iq_quiz_state == 'completed':
    st.balloons()
    
    # Calculate results
    questions = st.session_state.iq_questions
    answers = st.session_state.iq_answers
    
    score_percentage, correct_answers, total_questions = quiz_engine.calculate_score(answers, questions)
    
    # Calculate IQ score (mock calculation for demo)
    # In a real IQ test, this would be much more sophisticated
    time_taken = 1200  # Assume 20 minutes for demo
    iq_score = calculate_iq_score(correct_answers, total_questions, time_taken)
    
    st.markdown("### 🎉 IQ Test Completed!")
    
    # Display results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Correct Answers", f"{correct_answers}/{total_questions}")
    
    with col2:
        st.metric("Accuracy", f"{score_percentage:.1f}%")
    
    with col3:
        st.metric("Estimated IQ Score", iq_score)
    
    # IQ Score interpretation
    st.markdown("---")
    st.markdown("### 📊 IQ Score Interpretation")
  
    if iq_score >= 130:
        interpretation = "Highly Gifted - Exceptional intellectual ability"
        color = "🟢"
    elif iq_score >= 120:
        interpretation = "Superior - Well above average intelligence"
        color = "🔵"
    elif iq_score >= 110:
        interpretation = "High Average - Above average intelligence"
        color = "🟡"
    elif iq_score >= 90:
        interpretation = "Average - Normal intellectual functioning"
        color = "🟠"
    elif iq_score >= 80:
        interpretation = "Low Average - Below average but within normal range"
        color = "🟤"
    else:
        interpretation = "Below Average - May need additional support"
        color = "🔴"
    
    st.markdown(f"{color} **{interpretation}**")
    
    # Detailed breakdown
    st.markdown("---")
    st.markdown("### 📈 Detailed Analysis")
    
    # Analyze performance by subject
    subject_performance = {}
    for i, question in enumerate(questions):
        subject = question['stream']
        if subject not in subject_performance:
            subject_performance[subject] = {'correct': 0, 'total': 0}
        
        subject_performance[subject]['total'] += 1
        if i in answers and answers[i].lower() == question['correct_answer'].lower():
            subject_performance[subject]['correct'] += 1
    
    # Display subject performance
    for subject, performance in subject_performance.items():
        accuracy = (performance['correct'] / performance['total']) * 100
        st.metric(
            label=f"{subject}",
            value=f"{performance['correct']}/{performance['total']}",
            delta=f"{accuracy:.1f}%"
        )
    
    # Save results
    details = f"IQ Score: {iq_score}, Accuracy: {score_percentage:.1f}%, Questions: {total_questions}"
    save_success = save_quiz_results(
        user_id=st.session_state.username,
        quiz_type='iq_test',
        score=score_percentage,
        details=details
    )
    
    if save_success:
        st.success("Results saved to your progress!")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Take Another Test"):
            # Reset quiz state
            for key in ['iq_quiz_state', 'iq_questions', 'iq_current_question', 'iq_answers']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("View Dashboard"):
            st.switch_page("pages/1_Dashboard.py")
    
    with col3:
        if st.button("Get Recommendations"):
            st.switch_page("pages/5_Recommendations.py")

# Sidebar with tips
with st.sidebar:
    st.markdown("### 💡 Test Taking Tips")
    st.markdown("""
    - **Stay calm** and focused
    - **Read questions** carefully
    - **Think logically** about each problem
    - **Don't overthink** - go with your first instinct
    - **Manage your time** effectively
    - **Learn from** each question
    """)
    
    if st.session_state.iq_quiz_state == 'in_progress':
        st.markdown("---")
        st.markdown("### 📊 Progress")
        questions = st.session_state.iq_questions
        current_q = st.session_state.iq_current_question
        
        st.write(f"Questions completed: {current_q}/{len(questions)}")
        st.write(f"Remaining: {len(questions) - current_q}")
        
        # Show subject distribution
        subjects = [q['stream'] for q in questions]
        unique_subjects = list(set(subjects))
        st.write(f"Subjects covered: {len(unique_subjects)}")
