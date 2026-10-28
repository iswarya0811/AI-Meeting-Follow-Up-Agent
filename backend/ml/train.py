import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Import local modules
from preprocess import preprocess_text
from evaluate import evaluate_model, print_evaluation_summary

def main():
    print("=" * 40)
    print("AI Meeting Follow-Up Agent")
    print("Model Training Pipeline")
    print("=" * 40)
    
    # 1. Paths and Directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # backend/
    dataset_path = os.path.join(base_dir, "..", "dataset", "AI_Meeting_Follow_Up_Preprocessed_Clean.xlsx")
    dataset_path = os.path.abspath(dataset_path)
    models_dir = os.path.join(base_dir, "models")
    
    os.makedirs(models_dir, exist_ok=True)
    
    # 2. Load Dataset
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset not found at {dataset_path}")
        return
        
    print(f"Dataset found: {dataset_path}")
    df = pd.read_excel(dataset_path)
    print(f"Loaded {df.shape[0]} rows and {df.shape[1]} columns.")
    
    # 3. Preprocess Sentences
    print("\nPreprocessing sentences...")
    df['clean_sentence'] = df['sentence'].apply(preprocess_text)
    
    # 4. Train / Test Split
    # We split the dataframe itself. This ensures we use the exact same splits for all models
    # and fit TF-IDF vectorizer strictly on training text.
    # We stratify by the 'label' target to ensure clean distribution of action/non-action.
    print("Splitting dataset (80% train, 20% test)...")
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df['label']
    )
    
    # 5. Fit TF-IDF Vectorizer ONLY on training data
    print("Fitting TF-IDF Vectorizer on training data...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_train = vectorizer.fit_transform(train_df['clean_sentence'])
    X_test = vectorizer.transform(test_df['clean_sentence'])
    
    # Save the TF-IDF vectorizer
    vectorizer_path = os.path.join(models_dir, "tfidf_vectorizer.pkl")
    joblib.dump(vectorizer, vectorizer_path)
    print(f"Saved TF-IDF Vectorizer to {vectorizer_path}")
    
    # 6. Targets to Train
    targets = {
        "label": "label_model.pkl",
        "action_item": "action_item_model.pkl",
        "assignee": "assignee_model.pkl",
        "deadline": "deadline_model.pkl",
        "priority": "priority_model.pkl",
        "decision": "decision_model.pkl"
    }
    
    # 7. Train and Evaluate each target
    print("\nTraining models...")
    for target, filename in targets.items():
        print(f"\nTraining target: {target}")
        
        # Check class counts to confirm suitability
        y_train = train_df[target]
        y_test = test_df[target]
        
        unique_classes = y_train.nunique()
        if unique_classes < 2:
            print(f"Skipping {target}: Target must have at least 2 classes (found {unique_classes}).")
            continue
            
        # Check minimum samples per class (excluding Not Applicable/not applicable)
        class_counts = y_train.value_counts()
        min_class_samples = class_counts.min()
        print(f"Classes: {unique_classes}, Min samples per class in training: {min_class_samples}")
        
        # Train model
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        metrics = evaluate_model(y_test, y_pred, target)
        print_evaluation_summary(metrics)
        
        # Save model
        model_path = os.path.join(models_dir, filename)
        joblib.dump(model, model_path)
        print(f"Saved {target} model to {model_path}")
        
        # Add warning for priority
        if target == 'priority' and metrics['accuracy'] < 0.60:
            print("[WARNING] priority model has low accuracy. This target is uncorrelated with sentence keywords in the dataset.")
            
    print("\n========================================")
    print("Training process finished successfully!")
    print("All trained models are stored in backend/models/")
    print("========================================")

if __name__ == "__main__":
    main()
