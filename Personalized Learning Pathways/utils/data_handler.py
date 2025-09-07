import pandas as pd
import streamlit as st
import os
from datetime import datetime

def load_data(data_type):
    """
    Load data from CSV files based on data type
    """
    try:
        file_mapping = {
            'students': 'data/students.csv',
            'questions': 'data/questions.csv',
            'career_quiz': 'data/career_quiz.csv',
            'recommendations': 'data/recommendations.csv',
            'streams': 'data/streams.csv',
            'user_progress': 'data/user_progress.csv'
        }
        
        if data_type not in file_mapping:
            st.error(f"Unknown data type: {data_type}")
            return None
        
        file_path = file_mapping[data_type]
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            return df
        else:
            st.warning(f"Data file not found: {file_path}")
            return None
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def save_user_progress(user_id, activity_type, score, details):
    """
    Save user progress to CSV file
    """
    try:
        progress_data = {
            'progress_id': f"{user_id}_{activity_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'user_id': user_id,
            'activity_type': activity_type,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'score': score,
            'details': details
        }
        
        # Load existing progress data
        progress_df = load_data('user_progress')
        
        if progress_df is None or progress_df.empty:
            # Create new dataframe if file doesn't exist
            progress_df = pd.DataFrame([progress_data])
        else:
            # Append new progress
            progress_df = pd.concat([progress_df, pd.DataFrame([progress_data])], ignore_index=True)
        
        # Save to file
        progress_df.to_csv('data/user_progress.csv', index=False)
        return True
        
    except Exception as e:
        st.error(f"Error saving progress: {str(e)}")
        return False

def get_user_recommendations(user_id, streams_of_interest=None):
    """
    Get personalized recommendations for a user
    """
    try:
        recommendations_df = load_data('recommendations')
        
        if recommendations_df is None:
            return None
        
        if streams_of_interest:
            # Filter recommendations by streams of interest
            filtered_recs = recommendations_df[recommendations_df['stream'].isin(streams_of_interest)]
            return filtered_recs
        
        return recommendations_df
        
    except Exception as e:
        st.error(f"Error getting recommendations: {str(e)}")
        return None

def save_study_plan(user_id, plan_data):
    """
    Save study plan for a user
    """
    try:
        # For simplicity, we'll save study plans as user progress with type 'study_plan'
        details = f"Goal: {plan_data.get('goal', 'N/A')}, Deadline: {plan_data.get('deadline', 'N/A')}, Status: {plan_data.get('status', 'Active')}"
        
        return save_user_progress(
            user_id=user_id,
            activity_type='study_plan',
            score=0,  # Study plans don't have scores
            details=details
        )
        
    except Exception as e:
        st.error(f"Error saving study plan: {str(e)}")
        return False

def get_user_study_plans(user_id):
    """
    Get study plans for a user
    """
    try:
        progress_df = load_data('user_progress')
        
        if progress_df is None:
            return pd.DataFrame()
        
        # Filter for study plans
        study_plans = progress_df[
            (progress_df['user_id'] == user_id) & 
            (progress_df['activity_type'] == 'study_plan')
        ]
        
        return study_plans
        
    except Exception as e:
        st.error(f"Error getting study plans: {str(e)}")
        return pd.DataFrame()
    
def save_quiz_results(user_id, quiz_type, score, details, file_path="data/quiz_results.csv"):
    """Save quiz results to CSV file"""
    new_result = {
        "user_id": user_id,
        "quiz_type": quiz_type,
        "score": score,
        "details": details
    }

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, pd.DataFrame([new_result])], ignore_index=True)
    else:
        df = pd.DataFrame([new_result])

    df.to_csv(file_path, index=False)
    return True
