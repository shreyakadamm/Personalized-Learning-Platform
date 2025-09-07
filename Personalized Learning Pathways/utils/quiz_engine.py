from utils.data_handler import save_user_progress

class QuizEngine:
    def __init__(self, questions_df):
        self.questions_df = questions_df
        self.current_question = 0
        self.score = 0
        self.answers = {}
        
    def get_question(self, question_id):
        """Get a specific question by ID"""
        question_row = self.questions_df[self.questions_df['question_id'] == question_id]
        if not question_row.empty:
            return question_row.iloc[0].to_dict()
        return None
    
    def get_random_questions(self, stream=None, difficulty=None, count=10):
        """Get random questions based on filters"""
        filtered_df = self.questions_df.copy()
        
        if stream:
            filtered_df = filtered_df[filtered_df['stream'] == stream]
        
        if difficulty:
            filtered_df = filtered_df[filtered_df['difficulty'] == difficulty]
        
        if len(filtered_df) > count:
            return filtered_df.sample(n=count).to_dict('records')
        else:
            return filtered_df.to_dict('records')
    
    def calculate_score(self, answers, questions):
        """Calculate quiz score based on answers"""
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
        self.career_scores = {}
    
    def get_all_questions(self):
        """Get all career quiz questions"""
        return self.career_quiz_df.to_dict('records')
    
    def calculate_career_scores(self, answers):
        """Calculate scores for different career fields based on answers"""
        career_scores = {}
        
        for i, answer in answers.items():
            question_row = self.career_quiz_df.iloc[i]
            career_field = question_row['career_field']
            question_type = question_row['question_type']
            
            # Initialize career field score if not exists
            if career_field not in career_scores:
                career_scores[career_field] = {'score': 0, 'count': 0}
            
            # Calculate score based on answer and question type
            if question_type == 'scale':
                # For scale questions, convert answer to numeric score
                scale_mapping = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
                score = scale_mapping.get(answer.lower(), 0)
            else:  # multiple_choice
                # For multiple choice, assign score based on relevance
                score = 3 if answer.lower() in ['a', 'b'] else 2
            
            career_scores[career_field]['score'] += score
            career_scores[career_field]['count'] += 1
        
        # Calculate average scores
        for field in career_scores:
            if career_scores[field]['count'] > 0:
                career_scores[field]['average'] = career_scores[field]['score'] / career_scores[field]['count']
            else:
                career_scores[field]['average'] = 0
        
        return career_scores
    
    def get_recommended_streams(self, career_scores, streams_df, top_n=5):
        """Get recommended streams based on career quiz results"""
        # Sort career fields by average score
        sorted_careers = sorted(career_scores.items(), key=lambda x: x[1]['average'], reverse=True)
        
        recommended_streams = []
        
        # Map career fields to streams
        field_to_category_mapping = {
            'Technology': 'Technology',
            'Science': 'Science',
            'Business': 'Business',
            'Social Services': 'Social Sciences',
            'Healthcare': 'Science',
            'Creative Arts': 'Arts',
            'Education': 'Social Sciences',
            'Engineering': 'Technology'
        }
        
        for career_field, scores in sorted_careers[:3]:  # Top 3 career fields
            category = field_to_category_mapping.get(career_field, career_field)
            
            # Find streams in this category
            matching_streams = streams_df[streams_df['category'] == category]
            
            for _, stream in matching_streams.iterrows():
                if len(recommended_streams) < top_n:
                    stream_data = stream.to_dict()
                    stream_data['match_score'] = scores['average']
                    stream_data['career_field'] = career_field
                    recommended_streams.append(stream_data)
        
        return recommended_streams

def save_quiz_results(user_id, quiz_type, score, details):
    """Save quiz results to user progress"""
    return save_user_progress(
        user_id=user_id,
        activity_type=quiz_type,
        score=score,
        details=details
    )
