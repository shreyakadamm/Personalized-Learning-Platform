# Configuration file for the Personalized Learning Platform

# Application Settings
APP_CONFIG = {
    'title': 'Personalized Learning Platform',
    'icon': '🎓',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Quiz Configuration
QUIZ_CONFIG = {
    'iq_test': {
        'total_questions': 20,
        'difficulty_distribution': {
            'Beginner': 5,
            'Intermediate': 10,
            'Advanced': 5
        },
        'passing_score': 60
    },
    'career_quiz': {
        'scoring_scale': {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        },
        'max_score': 4.0
    }
}

# IQ Score Calculation
IQ_CALCULATION = {
    'base_score': 85,
    'multiplier': 0.6,
    'min_iq': 70,
    'max_iq': 150
}

# Certificate Configuration
CERTIFICATE_CONFIG = {
    'achievement_thresholds': {
        'excellence': 75,
        'proficiency': 60,
        'participation': 0
    },
    'certificate_types': {
        'iq_test': {
            'excellent': 'IQ Assessment Excellence',
            'good': 'IQ Assessment Proficiency',
            'basic': 'IQ Assessment Participation'
        },
        'career_quiz': 'Career Path Discovery'
    }
}

# Progress Tracking
PROGRESS_CONFIG = {
    'activity_types': [
        'iq_test',
        'career_quiz',
        'study_plan',
        'course_completion',
        'skill_assessment'
    ],
    'milestone_activities': [5, 10, 25, 50, 100]
}

# Data File Mapping (adjust paths as needed for your laptop)
DATA_FILES = {
    'students': 'attached_assets/students.csv',
    'questions': 'attached_assets/questions.csv',
    'career_quiz': 'attached_assets/career quiz.csv',
    'recommendations': 'attached_assets/recommendation.csv',
    'streams': 'attached_assets/streams .csv',
    'user_progress': 'attached_assets/user_progress.csv'
}

# UI Configuration
UI_CONFIG = {
    'colors': {
        'primary': '#2E86AB',
        'success': '#28A745',
        'warning': '#FFC107',
        'danger': '#DC3545',
        'info': '#17A2B8'
    },
    'page_icons': {
        'dashboard': '📊',
        'iq_test': '🧠',
        'career_quiz': '💼',
        'study_planner': '📅',
        'recommendations': '📚',
        'certificates': '🏆'
    }
}

# Validation Rules
VALIDATION_RULES = {
    'username': {
        'min_length': 2,
        'max_length': 50
    },
    'password': {
        'min_length': 6,
        'max_length': 100
    },
    'study_hours': {
        'min_value': 1,
        'max_value': 40
    }
}