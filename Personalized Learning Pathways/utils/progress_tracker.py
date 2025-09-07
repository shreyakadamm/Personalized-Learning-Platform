import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.data_handler import load_data

class ProgressTracker:
    def __init__(self, user_id):
        self.user_id = user_id
        self.progress_df = self.load_user_progress()
    
    def load_user_progress(self):
        """Load progress data for the user"""
        all_progress = load_data('user_progress')
        if all_progress is not None and not all_progress.empty:
            user_progress = all_progress[all_progress['user_id'] == self.user_id].copy()
            if not user_progress.empty:
                user_progress['date'] = pd.to_datetime(user_progress['date'])
            return user_progress
        return pd.DataFrame()
    
    def get_activity_summary(self):
        """Get summary of user activities"""
        if self.progress_df.empty:
            return {
                'total_activities': 0,
                'average_score': 0,
                'recent_activities': 0,
                'activity_types': {}
            }
        
        # Calculate summary statistics
        total_activities = len(self.progress_df)
        average_score = self.progress_df['score'].mean() if 'score' in self.progress_df.columns else 0
        
        # Recent activities (last 7 days)
        recent_date = datetime.now() - timedelta(days=7)
        recent_activities = len(self.progress_df[self.progress_df['date'] >= recent_date])
        
        # Activity types breakdown
        activity_types = self.progress_df['activity_type'].value_counts().to_dict()
        
        return {
            'total_activities': total_activities,
            'average_score': average_score,
            'recent_activities': recent_activities,
            'activity_types': activity_types
        }
    
    def create_progress_chart(self):
        """Create a progress chart showing scores over time"""
        if self.progress_df.empty:
            return None
        
        # Filter out study plans (they don't have meaningful scores)
        score_data = self.progress_df[self.progress_df['activity_type'] != 'study_plan'].copy()
        
        if score_data.empty:
            return None
        
        fig = px.line(
            score_data,
            x='date',
            y='score',
            color='activity_type',
            title='Your Learning Progress Over Time',
            labels={'score': 'Score (%)', 'date': 'Date', 'activity_type': 'Activity Type'}
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Score (%)",
            legend_title="Activity Type",
            hovermode='x unified'
        )
        
        return fig
    
    def create_activity_distribution_chart(self):
        """Create a pie chart showing distribution of activities"""
        if self.progress_df.empty:
            return None
        
        activity_counts = self.progress_df['activity_type'].value_counts()
        
        fig = px.pie(
            values=activity_counts.values,
            names=activity_counts.index,
            title='Distribution of Your Activities'
        )
        
        return fig
    
    def create_performance_gauge(self):
        """Create a gauge chart for overall performance"""
        if self.progress_df.empty:
            return None
        
        # Calculate overall performance (excluding study plans)
        score_data = self.progress_df[self.progress_df['activity_type'] != 'study_plan']
        
        if score_data.empty:
            overall_score = 0
        else:
            overall_score = score_data['score'].mean()
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = overall_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Overall Performance"},
            delta = {'reference': 75},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 75], 'color': "gray"},
                    {'range': [75, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        return fig
    
    def get_learning_streak(self):
        """Calculate current learning streak"""
        if self.progress_df.empty:
            return 0
        
        # Sort by date
        sorted_progress = self.progress_df.sort_values('date', ascending=False)
        
        # Calculate streak
        current_date = datetime.now().date()
        streak = 0
        
        for _, activity in sorted_progress.iterrows():
            activity_date = activity['date'].date()
            
            # Check if activity is from today or consecutive days
            if (current_date - activity_date).days <= streak + 1:
                if (current_date - activity_date).days == streak:
                    streak += 1
                    current_date = activity_date
            else:
                break
        
        return streak
    
    def get_recent_achievements(self, days=30):
        """Get recent achievements and milestones"""
        if self.progress_df.empty:
            return []
        
        recent_date = datetime.now() - timedelta(days=days)
        recent_activities = self.progress_df[self.progress_df['date'] >= recent_date]
        
        achievements = []
        
        # High score achievements
        high_scores = recent_activities[recent_activities['score'] >= 90]
        for _, activity in high_scores.iterrows():
            achievements.append({
                'type': 'High Score',
                'description': f"Scored {activity['score']:.1f}% in {activity['activity_type']}",
                'date': activity['date'].strftime('%Y-%m-%d')
            })
        
        # Activity milestones
        total_activities = len(self.progress_df)
        if total_activities >= 10 and total_activities % 5 == 0:
            achievements.append({
                'type': 'Milestone',
                'description': f"Completed {total_activities} total activities!",
                'date': datetime.now().strftime('%Y-%m-%d')
            })
        
        return achievements
    
    def get_improvement_suggestions(self):
        """Get personalized improvement suggestions"""
        if self.progress_df.empty:
            return ["Start taking quizzes to get personalized suggestions!"]
        
        suggestions = []
        summary = self.get_activity_summary()
        
        # Score-based suggestions
        if summary['average_score'] < 70:
            suggestions.append("Focus on reviewing fundamental concepts before taking advanced quizzes.")
        elif summary['average_score'] < 85:
            suggestions.append("Great progress! Try tackling more challenging topics to improve further.")
        else:
            suggestions.append("Excellent performance! Consider exploring new subject areas.")
        
        # Activity frequency suggestions
        if summary['recent_activities'] < 3:
            suggestions.append("Try to maintain regular study sessions - aim for at least 3 activities per week.")
        
        # Activity diversity suggestions
        activity_types = summary['activity_types']
        if len(activity_types) == 1:
            suggestions.append("Diversify your learning by trying different types of assessments.")
        
        # Subject-specific suggestions
        score_data = self.progress_df[self.progress_df['activity_type'] != 'study_plan']
        if not score_data.empty:
            low_performing_areas = score_data[score_data['score'] < 75]['activity_type'].unique()
            if len(low_performing_areas) > 0:
                suggestions.append(f"Consider spending more time on: {', '.join(low_performing_areas)}")
        
        return suggestions
