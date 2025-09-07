import streamlit as st

def authenticate_user(username, password, students_df):
    """
    Authenticate user against the students database
    """
    try:
        # Check if user exists and password matches
        user_row = students_df[students_df['Username'] == username]
        
        if not user_row.empty:
            stored_password = user_row.iloc[0]['Password']
            if stored_password == password:
                return user_row.iloc[0].to_dict()
        
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def logout_user():
    """
    Clear session state for logout
    """
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_data = None
    
    # Clear any other session state variables
    keys_to_clear = [key for key in st.session_state.keys() if key not in ['authenticated', 'username', 'user_data']]
    for key in keys_to_clear:
        del st.session_state[key]

def is_authenticated():
    """
    Check if user is currently authenticated
    """
    return st.session_state.get('authenticated', False)

def get_current_user():
    """
    Get current user data
    """
    if is_authenticated():
        return st.session_state.get('user_data', None)
    return None

def require_auth():
    """
    Decorator to require authentication for pages
    """
    if not is_authenticated():
        st.error("Please login to access this page")
        st.stop()
