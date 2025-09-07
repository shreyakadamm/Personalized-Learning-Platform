import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io
import base64
import os
import subprocess

# ReportLab imports for certificate generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# Configuration
DATA_FILES = {
    'students': 'attached_assets/students.csv',
    'questions': 'attached_assets/questions.csv',
    'career_quiz': 'attached_assets/career quiz.csv',
    'recommendations': 'attached_assets/recommendation.csv',
    'streams': 'attached_assets/streams.csv',
    'user_progress': 'attached_assets/user_progress.csv'
}

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

# Data Loading Functions
@st.cache_data
def load_data(data_type):
    """Load data from CSV files"""
    try:
        if data_type not in DATA_FILES:
            st.error(f"Unknown data type: {data_type}")
            return pd.DataFrame()
        
        file_path = DATA_FILES[data_type]
        if os.path.exists(file_path):
            # Special handling for students file which has empty row at top
            if data_type == 'students':
                df = pd.read_csv(file_path, skiprows=1)  # Skip the empty first row
            else:
                df = pd.read_csv(file_path)
            
            # Remove empty columns if they exist
            df = df.dropna(axis=1, how='all')
            # Remove any completely empty rows
            df = df.dropna(how='all')
            return df
        else:
            st.warning(f"Data file not found: {file_path}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading {data_type} data: {str(e)}")
        return pd.DataFrame()

def save_user_progress(user_id, activity_type, score, details):
    """Save user progress"""
    try:
        progress_data = {
            'progress_id': f"{user_id}_{activity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'activity_type': activity_type,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'score': score,
            'details': details
        }
        
        progress_df = load_data('user_progress')
        if progress_df.empty:
            progress_df = pd.DataFrame([progress_data])
        else:
            progress_df = pd.concat([progress_df, pd.DataFrame([progress_data])], ignore_index=True)
        
        progress_df.to_csv(DATA_FILES['user_progress'], index=False)
        return True
    except Exception as e:
        st.error(f"Error saving progress: {str(e)}")
        return False

def get_user_progress():
    """Get user progress data"""
    return load_data('user_progress')

# Authentication Functions
def authenticate_user(username, password):
    """Authenticate user"""
    students_df = load_data('students')
    if students_df.empty:
        return None
    
    user_row = students_df[students_df['Username'] == username]
    if not user_row.empty:
        stored_password = user_row.iloc[0]['Password']
        if stored_password == password:
            return user_row.iloc[0].to_dict()
    return None

def logout_user():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_data = None
    st.session_state.current_page = 'dashboard'

# Quiz Engine Classes
class QuizEngine:
    def __init__(self, questions_df):
        self.questions_df = questions_df
    
    def get_random_questions(self, stream=None, difficulty=None, count=10):
        """Get random questions based on filters"""
        filtered_df = self.questions_df.copy()
        
        if stream:
            filtered_df = filtered_df[filtered_df['stream'] == stream]
        if difficulty:
            filtered_df = filtered_df[filtered_df['difficulty'] == difficulty]
        
        if len(filtered_df) > count:
            return filtered_df.sample(n=count).to_dict('records')
        return filtered_df.to_dict('records')
    
    def calculate_score(self, answers, questions):
        """Calculate quiz score"""
        correct_answers = 0
        total_questions = len(questions)
        
        for i, question in enumerate(questions):
            user_answer = answers.get(i, '')
            correct_answer = question.get('correct_answer', '')
            if user_answer.lower() == correct_answer.lower():
                correct_answers += 1
        
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        return score_percentage, correct_answers, total_questions

class CareerQuizEngine:
    def __init__(self, career_quiz_df):
        self.career_quiz_df = career_quiz_df
    
    def get_all_questions(self):
        """Get all career quiz questions"""
        return self.career_quiz_df.to_dict('records')
    
    def calculate_career_scores(self, answers):
        """Calculate career field scores"""
        career_scores = {}
        
        for i, answer in answers.items():
            if i < len(self.career_quiz_df):
                question_row = self.career_quiz_df.iloc[i]
                career_field = question_row['career_field']
                
                if career_field not in career_scores:
                    career_scores[career_field] = {'score': 0, 'count': 0}
                
                scale_mapping = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
                score = scale_mapping.get(answer.lower(), 0)
                career_scores[career_field]['score'] += score
                career_scores[career_field]['count'] += 1
        
        for field in career_scores:
            if career_scores[field]['count'] > 0:
                career_scores[field]['average'] = career_scores[field]['score'] / career_scores[field]['count']
            else:
                career_scores[field]['average'] = 0
        
        return career_scores

# Certificate Generator Class
class CertificateGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for certificate"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB')
        )
        
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_CENTER
        )
    
    def generate_certificate(self, user_name, course_name, completion_date, score=None):
        """Generate certificate PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        elements = []
        elements.append(Spacer(1, 0.5*inch))
        
        # Title
        title = Paragraph("CERTIFICATE OF COMPLETION", self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # User name
        name_style = ParagraphStyle(
            'UserName',
            parent=self.styles['Normal'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E86AB'),
            fontName='Helvetica-Bold'
        )
        user_name_para = Paragraph(user_name, name_style)
        elements.append(user_name_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Course completion text
        completion_text = Paragraph(f"has successfully completed the {course_name}", self.body_style)
        elements.append(completion_text)
        
        if score is not None:
            score_text = Paragraph(f"with a score of {score:.1f}%", self.body_style)
            elements.append(score_text)
        
        elements.append(Spacer(1, 0.2*inch))
        date_text = Paragraph(f"on {completion_date}", self.body_style)
        elements.append(date_text)
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer
        footer = Paragraph("Personalized Learning Platform", self.body_style)
        elements.append(footer)
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data

# Page Functions
def show_login_page():
    """Display login page"""
    st.title("🎓 Personalized Learning Platform")
    st.markdown("### Please login to continue")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if username and password:
                    user_data = authenticate_user(username, password)
                    if user_data:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_data = user_data
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        st.info("Sample login: Username: 'Shreya Kadam', Password: '2306SK25'")

def show_dashboard():
    """Display dashboard"""
    st.title("📊 Your Learning Dashboard")
    
    user_progress = get_user_progress()
    user_activities = user_progress[user_progress['user_id'] == st.session_state.username] if not user_progress.empty else pd.DataFrame()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_activities = len(user_activities)
        st.metric("Total Activities", total_activities)
    
    with col2:
        avg_score = user_activities['score'].mean() if not user_activities.empty else 0
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with col3:
        unique_activity_types = user_activities['activity_type'].nunique() if not user_activities.empty else 0
        st.metric("Activity Types", unique_activity_types)
    
    with col4:
        recent_activities = len(user_activities[user_activities['date'] >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')]) if not user_activities.empty else 0
        st.metric("This Week", recent_activities)
    
    st.markdown("---")
    
    # Charts
    if not user_activities.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Activity Distribution")
            activity_counts = user_activities['activity_type'].value_counts()
            fig = px.pie(values=activity_counts.values, names=activity_counts.index, title="Activity Types")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Score Trends")
            user_activities['date'] = pd.to_datetime(user_activities['date'])
            score_trend = user_activities.groupby(user_activities['date'].dt.date)['score'].mean().reset_index()
            fig = px.line(score_trend, x='date', y='score', title="Score Over Time")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Take some quizzes to see your progress charts!")

def show_iq_test():
    """Display IQ test"""
    st.title("🧠 IQ Assessment Test")
    
    questions_df = load_data('questions')
    if questions_df.empty:
        st.error("Questions data not available")
        return
    
    quiz_engine = QuizEngine(questions_df)
    
    if 'iq_questions' not in st.session_state:
        # Get mixed difficulty questions
        beginner_q = quiz_engine.get_random_questions(difficulty='Beginner', count=5)
        intermediate_q = quiz_engine.get_random_questions(difficulty='Intermediate', count=10)
        advanced_q = quiz_engine.get_random_questions(difficulty='Advanced', count=5)
        
        st.session_state.iq_questions = beginner_q + intermediate_q + advanced_q
        st.session_state.iq_answers = {}
        st.session_state.iq_submitted = False
    
    if not st.session_state.iq_submitted:
        st.markdown("### Answer all 20 questions to complete your IQ assessment")
        
        with st.form("iq_test_form"):
            for i, question in enumerate(st.session_state.iq_questions):
                st.markdown(f"**Question {i+1}:** {question['question']}")
                
                options = [question['option_a'], question['option_b'], question['option_c'], question['option_d']]
                answer = st.radio(
                    f"Select your answer for question {i+1}:",
                    options,
                    key=f"q_{i}"
                )
                st.session_state.iq_answers[i] = answer[0].lower()  # Store as a, b, c, d
                st.markdown("---")
            
            submit_button = st.form_submit_button("Submit IQ Test", type="primary")
            
            if submit_button:
                score_percentage, correct, total = quiz_engine.calculate_score(
                    st.session_state.iq_answers, 
                    st.session_state.iq_questions
                )
                
                # Calculate IQ score
                iq_score = min(max(85 + (score_percentage * 0.6), 70), 150)
                
                # Save results
                save_user_progress(
                    st.session_state.username,
                    'iq_test',
                    score_percentage,
                    f"IQ Score: {iq_score:.0f}, Correct: {correct}/{total}"
                )
                
                st.session_state.iq_submitted = True
                st.session_state.iq_score = iq_score
                st.session_state.iq_percentage = score_percentage
                st.rerun()
    
    else:
        # Show results
        st.success("🎉 IQ Test Completed!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Your IQ Score", f"{st.session_state.iq_score:.0f}")
        with col2:
            st.metric("Percentage Score", f"{st.session_state.iq_percentage:.1f}%")
        with col3:
            if st.session_state.iq_score >= 120:
                st.metric("Rating", "Superior")
            elif st.session_state.iq_score >= 110:
                st.metric("Rating", "Above Average")
            elif st.session_state.iq_score >= 90:
                st.metric("Rating", "Average")
            else:
                st.metric("Rating", "Below Average")
        
        if st.button("Take Another Test"):
            del st.session_state.iq_questions
            del st.session_state.iq_answers
            st.session_state.iq_submitted = False
            st.rerun()

def show_career_quiz():
    """Display career quiz"""
    st.title("💼 Career Discovery Quiz")
    
    career_quiz_df = load_data('career_quiz')
    if career_quiz_df.empty:
        st.error("Career quiz data not available")
        return
    
    career_engine = CareerQuizEngine(career_quiz_df)
    
    if 'career_questions' not in st.session_state:
        st.session_state.career_questions = career_engine.get_all_questions()
        st.session_state.career_answers = {}
        st.session_state.career_submitted = False
    
    if not st.session_state.career_submitted:
        st.markdown("### Discover your ideal career path")
        
        with st.form("career_quiz_form"):
            for i, question in enumerate(st.session_state.career_questions):
                st.markdown(f"**Question {i+1}:** {question['question']}")
                
                options = [question['option_a'], question['option_b'], question['option_c'], question['option_d']]
                answer = st.radio(
                    f"Select your answer:",
                    options,
                    key=f"career_q_{i}"
                )
                st.session_state.career_answers[i] = answer[0].lower()
                st.markdown("---")
            
            submit_button = st.form_submit_button("Submit Career Quiz", type="primary")
            
            if submit_button:
                career_scores = career_engine.calculate_career_scores(st.session_state.career_answers)
                
                # Save results
                top_career = max(career_scores.items(), key=lambda x: x[1]['average'])
                save_user_progress(
                    st.session_state.username,
                    'career_quiz',
                    top_career[1]['average'] * 25,  # Convert to percentage
                    f"Top match: {top_career[0]}"
                )
                
                st.session_state.career_scores = career_scores
                st.session_state.career_submitted = True
                st.rerun()
    
    else:
        # Show results
        st.success("🎉 Career Quiz Completed!")
        
        sorted_careers = sorted(st.session_state.career_scores.items(), key=lambda x: x[1]['average'], reverse=True)
        
        st.subheader("🏆 Your Career Matches")
        for i, (career, data) in enumerate(sorted_careers[:5]):
            match_percentage = (data['average'] / 4.0) * 100
            st.write(f"**{i+1}. {career}** - {match_percentage:.1f}% match")
            st.progress(match_percentage / 100)
        
        if st.button("Take Another Quiz"):
            del st.session_state.career_questions
            del st.session_state.career_answers
            st.session_state.career_submitted = False
            st.rerun()

def show_study_planner():
    """Display study planner"""
    st.title("📅 Study Planner")
    
    st.markdown("### Create Your Learning Goals")
    
    with st.form("study_plan_form"):
        goal = st.text_input("Learning Goal", placeholder="e.g., Master Python Programming")
        subject = st.selectbox("Subject Area", ["Technology", "Science", "Business", "Arts", "Social Sciences"])
        duration = st.slider("Study Duration (weeks)", 1, 52, 12)
        hours_per_week = st.slider("Hours per week", 1, 40, 10)
        
        if st.form_submit_button("Create Study Plan"):
            if goal:
                plan_data = {
                    'goal': goal,
                    'subject': subject,
                    'duration': duration,
                    'hours_per_week': hours_per_week,
                    'total_hours': duration * hours_per_week,
                    'deadline': (datetime.now() + timedelta(weeks=duration)).strftime('%Y-%m-%d')
                }
                
                save_user_progress(
                    st.session_state.username,
                    'study_plan',
                    0,
                    f"Goal: {goal}, Subject: {subject}, Duration: {duration} weeks"
                )
                
                st.success("Study plan created successfully!")
                st.balloons()
    
    # Show existing plans
    user_progress = get_user_progress()
    study_plans = user_progress[
        (user_progress['user_id'] == st.session_state.username) & 
        (user_progress['activity_type'] == 'study_plan')
    ] if not user_progress.empty else pd.DataFrame()
    
    if not study_plans.empty:
        st.subheader("📋 Your Study Plans")
        for _, plan in study_plans.iterrows():
            with st.expander(f"📚 {plan['details'].split(',')[0].replace('Goal: ', '')}", expanded=False):
                st.write(f"**Created:** {plan['date']}")
                st.write(f"**Details:** {plan['details']}")

def show_recommendations():
    """Display learning recommendations"""
    st.title("📚 Learning Recommendations")
    
    recommendations_df = load_data('recommendations')
    if recommendations_df.empty:
        st.error("Recommendations data not available")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stream_filter = st.selectbox("Filter by Stream", ['All'] + list(recommendations_df['stream'].unique()) if 'stream' in recommendations_df.columns else ['All'])
    
    with col2:
        difficulty_filter = st.selectbox("Filter by Difficulty", ['All'] + list(recommendations_df['difficulty_level'].unique()) if 'difficulty_level' in recommendations_df.columns else ['All'])
    
    with col3:
        resource_type_filter = st.selectbox("Filter by Type", ['All'] + list(recommendations_df['resource_type'].unique()) if 'resource_type' in recommendations_df.columns else ['All'])
    
    # Apply filters
    filtered_recs = recommendations_df.copy()
    
    if stream_filter != 'All' and 'stream' in filtered_recs.columns:
        filtered_recs = filtered_recs[filtered_recs['stream'] == stream_filter]
    
    if difficulty_filter != 'All' and 'difficulty_level' in filtered_recs.columns:
        filtered_recs = filtered_recs[filtered_recs['difficulty_level'] == difficulty_filter]
    
    if resource_type_filter != 'All' and 'resource_type' in filtered_recs.columns:
        filtered_recs = filtered_recs[filtered_recs['resource_type'] == resource_type_filter]
    
    # Display recommendations
    st.markdown(f"### 📖 Learning Resources ({len(filtered_recs)} found)")
    
    for idx, rec in filtered_recs.iterrows():
        with st.expander(f"📚 {rec.get('title', 'Untitled')}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if 'stream' in rec:
                    st.write(f"**Stream:** {rec['stream']}")
                if 'description' in rec:
                    st.write(f"**Description:** {rec['description']}")
                if 'platform' in rec:
                    st.write(f"**Platform:** {rec['platform']}")
                if 'duration' in rec:
                    st.write(f"**Duration:** {rec['duration']}")
            
            with col2:
                if 'difficulty_level' in rec:
                    st.write(f"📊 {rec['difficulty_level']}")
                if 'resource_type' in rec:
                    st.write(f"📝 {rec['resource_type']}")
                
                if 'url' in rec and rec['url'] != 'N/A':
                    st.link_button("🔗 View Resource", rec['url'])
        
        if idx >= 9:  # Limit display for performance
            break

def show_certificates():
    """Display certificates and achievements"""
    st.title("🏆 Your Certificates & Achievements")
    
    cert_generator = CertificateGenerator()
    user_progress = get_user_progress()
    user_activities = user_progress[user_progress['user_id'] == st.session_state.username] if not user_progress.empty else pd.DataFrame()
    
    tab1, tab2, tab3 = st.tabs(["🏆 Available Certificates", "📊 Achievement Progress", "📄 Project Documentation"])
    
    with tab1:
        st.subheader("🎯 Earn Your Certificates")
        
        certificates = []
        
        # IQ Test Certificate
        iq_tests = user_activities[user_activities['activity_type'] == 'iq_test']
        if not iq_tests.empty:
            best_score = iq_tests['score'].max()
            cert_type = "IQ Assessment Excellence" if best_score >= 75 else "IQ Assessment Participation"
            certificates.append({
                'type': cert_type,
                'description': f'Cognitive assessment completed (Score: {best_score:.1f}%)',
                'earned': True,
                'score': best_score
            })
        else:
            certificates.append({
                'type': 'IQ Assessment',
                'description': 'Complete the IQ test to earn this certificate',
                'earned': False
            })
        
        # Career Quiz Certificate
        career_quizzes = user_activities[user_activities['activity_type'] == 'career_quiz']
        if not career_quizzes.empty:
            certificates.append({
                'type': 'Career Path Discovery',
                'description': 'Successfully completed career assessment',
                'earned': True,
                'score': career_quizzes.iloc[-1]['score']
            })
        else:
            certificates.append({
                'type': 'Career Path Discovery',
                'description': 'Complete the career quiz to earn this certificate',
                'earned': False
            })
        
        # Display certificates
        for cert in certificates:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if cert['earned']:
                    st.success(f"✅ **{cert['type']}**")
                    st.write(cert['description'])
                else:
                    st.info(f"🔒 **{cert['type']}**")
                    st.write(cert['description'])
            
            with col2:
                if cert['earned']:
                    if st.button(f"Generate Certificate", key=f"cert_{cert['type']}", type="primary"):
                        pdf_data = cert_generator.generate_certificate(
                            user_name=st.session_state.user_data['Name'],
                            course_name=cert['type'],
                            completion_date=datetime.now().strftime('%B %d, %Y'),
                            score=cert.get('score')
                        )
                        
                        b64 = base64.b64encode(pdf_data).decode()
                        filename = f"{cert['type'].replace(' ', '_')}_Certificate.pdf"
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Download Certificate</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success("Certificate generated!")
    
    with tab2:
        st.subheader("📊 Your Progress")
        
        total_activities = len(user_activities)
        avg_score = user_activities['score'].mean() if not user_activities.empty else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Activities", total_activities)
        with col2:
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col3:
            st.metric("Certificates Earned", len([c for c in certificates if c['earned']]))
        
        # Progress towards milestones
        st.markdown("### 🎯 Achievement Milestones")
        for milestone in [5, 10, 25, 50]:
            progress = min(1.0, total_activities / milestone)
            st.markdown(f"**{milestone} Activities:**")
            st.progress(progress)
            if total_activities >= milestone:
                st.success(f"✅ Milestone achieved!")
            else:
                st.info(f"🎯 {milestone - total_activities} more to go")
    
    with tab3:
        st.subheader("📄 Complete Project Documentation")
        
        st.markdown("""
        ### 📋 Comprehensive Project PDF
        
        Download the complete technical documentation for the Personalized Learning Platform project. 
        This comprehensive document includes:
        
        **📊 Project Overview & Architecture**
        - Executive summary and business objectives
        - System architecture and technical specifications
        - Technology stack and implementation details
        
        **🔧 Features & Implementation**
        - Detailed feature documentation
        - Code architecture and design patterns
        - Database structure and data relationships
        
        **🚀 Deployment & Future Plans**
        - Step-by-step deployment guide
        - Testing and quality assurance procedures
        - Future enhancements and roadmap
        """)
        
        # Check if PDF exists
        pdf_path = "Personalized_Learning_Platform_Documentation.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            
            st.download_button(
                label="📥 Download Project Documentation PDF",
                data=pdf_data,
                file_name="Personalized_Learning_Platform_Documentation.pdf",
                mime="application/pdf",
                type="primary"
            )
            
            st.success("✅ Documentation is ready for download!")
        else:
            if st.button("🔄 Generate Project Documentation", type="primary"):
                with st.spinner("Generating comprehensive project documentation..."):
                    try:
                        result = subprocess.run(["python", "generate_project_pdf.py"], capture_output=True, text=True)
                        if result.returncode == 0:
                            st.success("✅ Documentation generated successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error generating PDF: {result.stderr}")
                    except Exception as e:
                        st.error(f"Error generating documentation: {str(e)}")
            
            st.info("📝 Click the button above to generate your complete project documentation.")

def main():
    """Main application logic"""
    st.set_page_config(
        page_title="Personalized Learning Platform",
        page_icon="🎓",
        layout="wide"
    )
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🎓 Learning Platform")
        st.write(f"Welcome, {st.session_state.user_data['Name']}")
        
        if st.button("Logout"):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        pages = {
            "📊 Dashboard": "dashboard",
            "🧠 IQ Test": "iq_test", 
            "💼 Career Quiz": "career_quiz",
            "📅 Study Planner": "study_planner",
            "📚 Recommendations": "recommendations",
            "🏆 Certificates": "certificates"
        }
        
        for page_name, page_key in pages.items():
            if st.button(page_name, key=f"nav_{page_key}"):
                st.session_state.current_page = page_key
                st.rerun()
    
    # Display selected page
    current_page = st.session_state.current_page
    
    if current_page == 'dashboard':
        show_dashboard()
    elif current_page == 'iq_test':
        show_iq_test()
    elif current_page == 'career_quiz':
        show_career_quiz()
    elif current_page == 'study_planner':
        show_study_planner()
    elif current_page == 'recommendations':
        show_recommendations()
    elif current_page == 'certificates':
        show_certificates()

if __name__ == "__main__":
    main()