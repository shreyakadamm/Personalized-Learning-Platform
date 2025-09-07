import streamlit as st
from utils.auth import require_auth, get_current_user
from utils.data_handler import load_data
from utils.certificate_generator import CertificateGenerator
import pandas as pd
from datetime import datetime
import base64

# Require authentication
require_auth()

st.set_page_config(page_title="Certificates", page_icon="🏆", layout="wide")

st.title("🏆 Your Certificates & Achievements")

# Get current user
user_data = get_current_user()
if not user_data:
    st.error("User data not found")
    st.stop()

# Initialize certificate generator
cert_generator = CertificateGenerator()

# Load user progress to determine achievements
progress_df = load_data('user_progress')
user_progress = progress_df[progress_df['user_id'] == st.session_state.username] if progress_df is not None else pd.DataFrame()

# Tabs for different certificate types
tab1, tab2, tab3 = st.tabs(["🏆 Available Certificates", "📜 My Certificates", "🎯 Achievement Tracker"])

with tab1:
    st.subheader("🎯 Earn Your Certificates")
    
    st.markdown("""
    Complete assessments and learning goals to earn certificates that showcase your achievements!
    
    ### Certificate Types Available:
    """)
    
    # Check eligibility for different certificates
    certificates_available = []
    
    # IQ Test Certificate
    iq_tests = user_progress[user_progress['activity_type'] == 'iq_test']
    if not iq_tests.empty:
        best_iq_score = iq_tests['score'].max()
        if best_iq_score >= 75:
            certificates_available.append({
                'type': 'IQ Assessment Excellence',
                'description': f'Outstanding performance in cognitive assessment (Score: {best_iq_score:.1f}%)',
                'earned': True,
                'score': best_iq_score,
                'date': iq_tests.loc[iq_tests['score'].idxmax(), 'date']
            })
        else:
            certificates_available.append({
                'type': 'IQ Assessment Participation',
                'description': f'Completed cognitive assessment (Score: {best_iq_score:.1f}%)',
                'earned': True,
                'score': best_iq_score,
                'date': iq_tests.loc[iq_tests['score'].idxmax(), 'date']
            })
    else:
        certificates_available.append({
            'type': 'IQ Assessment',
            'description': 'Complete the IQ test to earn this certificate',
            'earned': False,
            'requirement': 'Take IQ Test'
        })
    
    # Career Quiz Certificate
    career_quizzes = user_progress[user_progress['activity_type'] == 'career_quiz']
    if not career_quizzes.empty:
        latest_career = career_quizzes.iloc[-1]
        certificates_available.append({
            'type': 'Career Path Discovery',
            'description': 'Successfully completed career assessment and discovered your ideal path',
            'earned': True,
            'score': latest_career['score'],
            'date': latest_career['date']
        })
    else:
        certificates_available.append({
            'type': 'Career Path Discovery',
            'description': 'Complete the career quiz to earn this certificate',
            'earned': False,
            'requirement': 'Take Career Quiz'
        })
    
    # Activity Milestone Certificates
    total_activities = len(user_progress)
    
    milestones = [5, 10, 25, 50, 100]
    for milestone in milestones:
        if total_activities >= milestone:
            certificates_available.append({
                'type': f'{milestone} Activities Milestone',
                'description': f'Completed {milestone} learning activities on the platform',
                'earned': True,
                'score': 100,  # Milestone achievements get full score
                'date': datetime.now()
            })
        else:
            certificates_available.append({
                'type': f'{milestone} Activities Milestone',
                'description': f'Complete {milestone} activities to earn this certificate (Current: {total_activities})',
                'earned': False,
                'requirement': f'Complete {milestone - total_activities} more activities'
            })
    
    # High Performance Certificate
    scored_activities = user_progress[user_progress['activity_type'] != 'study_plan']
    if not scored_activities.empty:
        avg_score = scored_activities['score'].mean()
        high_scores = scored_activities[scored_activities['score'] >= 90]
        
        if len(high_scores) >= 3:
            certificates_available.append({
                'type': 'High Performance Excellence',
                'description': f'Achieved 90%+ scores in {len(high_scores)} assessments',
                'earned': True,
                'score': avg_score,
                'date': datetime.now()
            })
        elif avg_score >= 80:
            certificates_available.append({
                'type': 'Consistent Performance',
                'description': f'Maintained average score of {avg_score:.1f}% across all assessments',
                'earned': True,
                'score': avg_score,
                'date': datetime.now()
            })
    
    # Display certificates
    for cert in certificates_available:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if cert['earned']:
                    st.success(f"✅ **{cert['type']}**")
                    st.write(cert['description'])
                    if 'score' in cert:
                        st.caption(f"Score: {cert['score']:.1f}%")
                else:
                    st.info(f"🔒 **{cert['type']}**")
                    st.write(cert['description'])
                    if 'requirement' in cert:
                        st.caption(f"Requirement: {cert['requirement']}")
            
            with col2:
                if cert['earned']:
                    if st.button(f"Generate Certificate", key=f"gen_{cert['type']}", type="primary"):
                        # Generate certificate
                        cert_date = cert['date'].strftime('%B %d, %Y') if hasattr(cert['date'], 'strftime') else datetime.now().strftime('%B %d, %Y')
                        
                        if 'score' in cert and cert['score']:
                            pdf_data = cert_generator.generate_completion_certificate(
                                user_name=user_data['Name'],
                                course_name=cert['type'],
                                completion_date=cert_date,
                                score=cert['score']
                            )
                        else:
                            pdf_data = cert_generator.generate_achievement_certificate(
                                user_name=user_data['Name'],
                                achievement_type=cert['type'],
                                achievement_details=cert['description'],
                                date=cert_date
                            )
                        
                        # Create download link
                        filename = f"{cert['type'].replace(' ', '_')}_Certificate.pdf"
                        b64 = base64.b64encode(pdf_data).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Download Certificate</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success("Certificate generated successfully!")
                else:
                    if 'Take IQ Test' in cert.get('requirement', ''):
                        if st.button("Take IQ Test", key=f"iq_{cert['type']}"):
                            st.switch_page("pages/2_IQ_Test.py")
                    elif 'Take Career Quiz' in cert.get('requirement', ''):
                        if st.button("Take Career Quiz", key=f"career_{cert['type']}"):
                            st.switch_page("pages/3_Career_Quiz.py")
                    else:
                        st.button("Not Available", disabled=True, key=f"disabled_{cert['type']}")
            
            st.markdown("---")

with tab2:
    st.subheader("📜 Certificate Gallery")
    
    # Show previously generated certificates (simulated)
    st.markdown("""
    This section would typically show certificates you've already generated and downloaded.
    
    ### How to Access Your Certificates:
    1. Generate certificates from the "Available Certificates" tab
    2. Download the PDF files to your device
    3. Use them for your portfolio, resume, or LinkedIn profile
    4. Share your achievements with employers and colleagues
    """)
    
    # Sample certificate preview
    if user_progress is not None and not user_progress.empty:
        st.markdown("#### 🖼️ Certificate Preview")
        
        if st.button("Preview Sample Certificate"):
            # Generate a sample certificate
            sample_pdf = cert_generator.generate_completion_certificate(
                user_name=user_data['Name'],
                course_name="Platform Participation",
                completion_date=datetime.now().strftime('%B %d, %Y'),
                score=85
            )
            
            # Display preview (in a real app, you'd show a preview image)
            st.success("Sample certificate generated! Download to view the full certificate.")
            
            b64 = base64.b64encode(sample_pdf).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="Sample_Certificate.pdf">📥 Download Sample Certificate</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Certificate sharing options
    st.markdown("---")
    st.markdown("#### 📤 Share Your Achievements")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **LinkedIn Profile**
        - Add certificates to your profile
        - Showcase your learning journey
        - Boost your professional credibility
        """)
    
    with col2:
        st.markdown("""
        **Resume/CV**
        - Include in education section
        - Highlight specific skills
        - Demonstrate continuous learning
        """)
    
    with col3:
        st.markdown("""
        **Social Media**
        - Share your achievements
        - Inspire others to learn
        - Build your personal brand
        """)

with tab3:
    st.subheader("🎯 Achievement Progress")
    
    # Progress towards various achievements
    if not user_progress.empty:
        st.markdown("### 📊 Your Learning Journey")
        
        # Activity progress
        total_activities = len(user_progress)
        st.markdown(f"**Total Activities Completed:** {total_activities}")
        
        # Progress bars for milestones
        milestones = [5, 10, 25, 50, 100]
        
        for milestone in milestones:
            progress = min(1.0, total_activities / milestone)
            st.markdown(f"**Progress to {milestone} Activities:**")
            st.progress(progress)
            
            if total_activities >= milestone:
                st.success(f"✅ {milestone} activities milestone achieved!")
            else:
                remaining = milestone - total_activities
                st.info(f"🎯 {remaining} more activities to reach {milestone} milestone")
            st.markdown("---")
        
        # Score achievements
        scored_activities = user_progress[user_progress['activity_type'] != 'study_plan']
        if not scored_activities.empty:
            avg_score = scored_activities['score'].mean()
            high_scores = scored_activities[scored_activities['score'] >= 90]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average Score", f"{avg_score:.1f}%")
            
            with col2:
                st.metric("High Scores (90%+)", len(high_scores))
            
            with col3:
                st.metric("Total Assessments", len(scored_activities))
            
            # Score distribution chart
            if len(scored_activities) > 1:
                st.markdown("#### 📈 Score Distribution")
                score_ranges = ['0-50%', '51-70%', '71-85%', '86-95%', '96-100%']
                score_counts = [
                    len(scored_activities[scored_activities['score'] <= 50]),
                    len(scored_activities[(scored_activities['score'] > 50) & (scored_activities['score'] <= 70)]),
                    len(scored_activities[(scored_activities['score'] > 70) & (scored_activities['score'] <= 85)]),
                    len(scored_activities[(scored_activities['score'] > 85) & (scored_activities['score'] <= 95)]),
                    len(scored_activities[scored_activities['score'] > 95])
                ]
                
                import plotly.express as px
                fig = px.bar(
                    x=score_ranges,
                    y=score_counts,
                    title='Score Distribution Across All Assessments',
                    labels={'x': 'Score Range', 'y': 'Number of Assessments'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Learning streak
        if 'date' in user_progress.columns:
            user_progress['date'] = pd.to_datetime(user_progress['date'])
            unique_dates = user_progress['date'].dt.date.unique()
            
            # Calculate current streak
            unique_dates.sort()
            current_streak = 0
            
            if len(unique_dates) > 0:
                last_date = unique_dates[-1]
                current_date = datetime.now().date()
                
                if (current_date - last_date).days <= 1:
                    # Count consecutive days
                    for i in range(len(unique_dates) - 1, -1, -1):
                        if i == len(unique_dates) - 1:
                            current_streak = 1
                        else:
                            days_diff = (unique_dates[i+1] - unique_dates[i]).days
                            if days_diff == 1:
                                current_streak += 1
                            else:
                                break
            
            st.markdown("#### 🔥 Learning Streak")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Streak", f"{current_streak} days")
            
            with col2:
                st.metric("Total Learning Days", len(unique_dates))
            
            # Streak achievements
            streak_milestones = [3, 7, 14, 30, 60]
            for milestone in streak_milestones:
                if current_streak >= milestone:
                    st.success(f"🔥 {milestone}-day learning streak achieved!")
                else:
                    st.info(f"🎯 Keep learning for {milestone - current_streak} more days to reach {milestone}-day streak")
    
    else:
        st.info("Start completing activities to track your achievement progress!")
        
        # Call to action
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Take IQ Test", type="primary"):
                st.switch_page("pages/2_IQ_Test.py")
        
        with col2:
            if st.button("Take Career Quiz", type="primary"):
                st.switch_page("pages/3_Career_Quiz.py")
    
    # Future achievements preview
    st.markdown("---")
    st.markdown("### 🚀 Upcoming Achievements")
    
    upcoming_achievements = [
        "🎓 Subject Matter Expert - Excel in 3 different streams",
        "🌟 Perfect Score - Achieve 100% in any assessment",
        "📚 Lifelong Learner - Complete 200 activities",
        "🏆 Learning Champion - Maintain 30-day streak",
        "🎯 Goal Achiever - Complete 10 study plans"
    ]
    
    for achievement in upcoming_achievements:
        st.info(achievement)

# Sidebar with quick stats
with st.sidebar:
    st.markdown("### 📊 Quick Stats")
    
    if not user_progress.empty:
        total_activities = len(user_progress)
        iq_tests = len(user_progress[user_progress['activity_type'] == 'iq_test'])
        career_quizzes = len(user_progress[user_progress['activity_type'] == 'career_quiz'])
        
        st.metric("Total Activities", total_activities)
        st.metric("IQ Tests Taken", iq_tests)
        st.metric("Career Assessments", career_quizzes)
        
        # Calculate potential certificates
        potential_certs = 0
        if iq_tests > 0:
            potential_certs += 1
        if career_quizzes > 0:
            potential_certs += 1
        
        # Milestone certificates
        milestones_achieved = sum(1 for m in [5, 10, 25, 50, 100] if total_activities >= m)
        potential_certs += milestones_achieved
        
        st.metric("Available Certificates", potential_certs)
    else:
        st.info("Complete activities to see your stats!")
    
    st.markdown("---")
    st.markdown("### 🎯 Quick Actions")
    
    if st.button("📊 View Dashboard", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
    
    if st.button("🧠 Take IQ Test", use_container_width=True):
        st.switch_page("pages/2_IQ_Test.py")
    
    if st.button("💼 Career Quiz", use_container_width=True):
        st.switch_page("pages/3_Career_Quiz.py")
