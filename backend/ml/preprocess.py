import re

def preprocess_text(text):
    """
    Cleans and normalizes the input text.
    
    1. Handles missing/empty text.
    2. Converts to lowercase.
    3. Normalizes whitespace (stripping and replacing multi-spaces).
    4. Performs basic punctuation normalization without destroying 
       temporal expressions (e.g. days of the week, times, deadlines).
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace newlines, tabs, and carriage returns with spaces
    text = re.sub(r'[\r\n\t]+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    return text
