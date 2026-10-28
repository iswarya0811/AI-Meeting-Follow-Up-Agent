import os
import re
import joblib

# Import local preprocessing
from ml.preprocess import preprocess_text

# Global variables to cache vectorizer and models in memory
_vectorizer = None
_models = {}

# Constants for Fallback Extraction
ASSIGNEES = [
    'Nikhil', 'Priya', 'Ananya', 'Sneha', 'Kiran', 'Maya', 'Vikram', 'Pooja', 
    'Divya', 'Sanjay', 'Rahul', 'Meera', 'Neha', 'Rohan', 'Ravi', 'Aditya', 
    'Arjun', 'Ishaan', 'Aisha', 'Varun'
]

ACTION_ITEMS_MAPPING = {
    'login module': 'Login module',
    'login flow': 'Login module',
    'login functionality': 'Login module',
    'login': 'Login module',
    
    'data pipeline': 'Data pipeline',
    'pipeline': 'Data pipeline',
    
    'presentation slides': 'Presentation slides',
    'presentation': 'Presentation slides',
    'slides': 'Presentation slides',
    
    'ui design': 'UI design',
    'design': 'UI design',
    
    'final dataset': 'Final dataset',
    'dataset': 'Final dataset',
    
    'completed changes': 'Completed changes',
    'merge': 'Completed changes',
    
    'api integration': 'API integration',
    'api': 'API integration',
    'integration': 'API integration',
    
    'project report': 'Project report',
    'report': 'Project report',
    
    'weekly progress': 'Weekly progress report',
    'progress report': 'Weekly progress report',
    
    'dashboard issues': 'Dashboard issues',
    'dashboard': 'Dashboard issues',
    
    'project documentation': 'Project documentation',
    'technical documentation': 'Project documentation',
    'documentation': 'Project documentation',
    'docs': 'Project documentation',
    
    'regression tests': 'Regression tests',
    'regression': 'Regression tests',
    'automated tests': 'Regression tests',
    
    'database schema': 'Database schema',
    'database': 'Database schema',
    'schema': 'Database schema',
    
    'api endpoints': 'API endpoints',
    'endpoints': 'API endpoints',
    
    'server configuration': 'Server configuration',
    'server': 'Server configuration',
    'configuration': 'Server configuration',
    
    'release notes': 'Release notes',
    
    'meeting summary': 'Meeting summary',
    'summary': 'Meeting summary',
    
    'final demo': 'Final demo',
    'demo': 'Final demo',
    
    'model results': 'Model results',
    'results': 'Model results',
    
    'client requirements': 'Client requirements',
    'requirements': 'Client requirements',
    
    'deployment checklist': 'Deployment checklist',
    'checklist': 'Deployment checklist',
    'deployment': 'Deployment checklist',
    
    'customer feedback': 'Customer feedback',
    
    'latest build': 'Latest build',
    'build': 'Latest build',
    
    'test cases': 'Test cases',
    'user feedback': 'User feedback'
}

DEADLINES_MAPPING = {
    'next sprint': 'by the next sprint',
    'sprint': 'by the next sprint',
    
    'two days': 'within two days',
    'within two days': 'within two days',
    
    'afternoon': 'this afternoon',
    'this afternoon': 'this afternoon',
    
    'monday': 'by Monday',
    'thursday': 'by Thursday',
    'wednesday': 'by Wednesday',
    'friday': 'by Friday',
    
    'tomorrow': 'tomorrow',
    
    'friday\'s review': 'before Friday\'s review',
    'fridays review': 'before Friday\'s review',
    
    'end of the day': 'by the end of the day',
    'next week': 'next week',
    
    'next meeting': 'before the next meeting',
    'next monday': 'by next Monday',
    
    'three working days': 'within three working days',
    'three days': 'within three working days'
}

def load_prediction_assets():
    """
    Loads TF-IDF vectorizer and trained models from backend/models/ if they aren't already loaded.
    """
    global _vectorizer, _models
    
    # Only load once
    if _vectorizer is not None and len(_models) > 0:
        return
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend/
    models_dir = os.path.join(base_dir, "models")
    
    # Load Vectorizer
    vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")
    if not os.path.exists(vectorizer_path):
        raise FileNotFoundError(f"TF-IDF Vectorizer file not found at {vectorizer_path}. Please run train.py first.")
    _vectorizer = joblib.load(vectorizer_path)
    
    # Load Models
    targets = {
        "label": "label_model.pkl",
        "action_item": "action_item_model.pkl",
        "assignee": "assignee_model.pkl",
        "deadline": "deadline_model.pkl",
        "priority": "priority_model.pkl",
        "decision": "decision_model.pkl"
    }
    
    for target, filename in targets.items():
        model_path = os.path.join(models_dir, filename)
        if os.path.exists(model_path):
            _models[target] = joblib.load(model_path)
        else:
            print(f"[WARNING] Model for target '{target}' not found at {model_path}.")
            _models[target] = None

def fallback_extract_assignee(text):
    """Scans text to find any known assignee name."""
    text_lower = text.lower()
    for name in ASSIGNEES:
        # Use regex boundary check to avoid substring matches (e.g. 'Ravi' matching 'Travis')
        if re.search(r'\b' + re.escape(name.lower()) + r'\b', text_lower):
            return name
    return "Not Applicable"

def fallback_extract_action_item(text):
    """Scans text to find matching keywords for action items."""
    text_lower = text.lower()
    # Sort keys by length in descending order to match longest phrases first
    sorted_keys = sorted(ACTION_ITEMS_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
            return ACTION_ITEMS_MAPPING[key]
    return "Not Applicable"

def fallback_extract_deadline(text):
    """Scans text for temporal phrases to extract deadline."""
    text_lower = text.lower()
    sorted_keys = sorted(DEADLINES_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if re.search(r'\b' + re.escape(key) + r'\b', text_lower):
            return DEADLINES_MAPPING[key]
    return "Not Applicable"

def predict_text(text):
    """
    Preprocesses the input text and runs all available models.
    Applies rule-based Fallbacks when predictions are 'Not Applicable' on action sentences.
    """
    # Make sure models are loaded
    load_prediction_assets()
    
    # Preprocess the text
    clean_text = preprocess_text(text)
    
    # Return default empty dict if clean text is empty
    if not clean_text:
        return {
            "label": "NON_ACTION",
            "action_item": "Not Applicable",
            "assignee": "Not Applicable",
            "deadline": "Not Applicable",
            "priority": "not applicable",
            "decision": "discussion only"
        }
        
    # Transform using vectorizer
    text_features = _vectorizer.transform([clean_text])
    
    predictions = {}
    
    # Predict with each available model
    for target, model in _models.items():
        if model is not None:
            pred_class = model.predict(text_features)[0]
            predictions[target] = pred_class
        else:
            predictions[target] = "Not Applicable" if target != "priority" and target != "decision" else "not applicable"
            
    # Apply rule fallbacks if the label is ACTION but targets got Not Applicable
    is_action = predictions.get("label") == "ACTION"
    
    # Fallback to keyword matching if label is ACTION but models failed to extract specific fields
    if is_action:
        if predictions.get("assignee") == "Not Applicable":
            predictions["assignee"] = fallback_extract_assignee(clean_text)
            
        if predictions.get("action_item") == "Not Applicable":
            predictions["action_item"] = fallback_extract_action_item(clean_text)
            
        if predictions.get("deadline") == "Not Applicable":
            predictions["deadline"] = fallback_extract_deadline(clean_text)
            
        # If priority was predicted as not applicable, default it to a valid action priority
        if predictions.get("priority") == "not applicable":
            # If the sentence contains words like 'important', 'urgent', 'asap', default to 'high'
            if any(w in clean_text for w in ['important', 'urgent', 'asap', 'critical', 'emergency']):
                predictions["priority"] = "high"
            else:
                predictions["priority"] = "medium"
                
        # If decision was predicted as not applicable, set to a valid decision type
        if predictions.get("decision") in ["not applicable", "discussion only"]:
            predictions["decision"] = "action item assigned"
            
    # Post-processing safety: If label is predicted as NON_ACTION, align other targets to Not Applicable
    if predictions.get("label") == "NON_ACTION":
        predictions["action_item"] = "Not Applicable"
        predictions["assignee"] = "Not Applicable"
        predictions["deadline"] = "Not Applicable"
        predictions["priority"] = "not applicable"
        predictions["decision"] = "discussion only"
        
    return predictions
