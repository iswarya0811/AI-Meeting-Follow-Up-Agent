from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def evaluate_model(y_true, y_pred, target_name):
    """
    Evaluates classification performance for a target and returns metrics.
    
    Uses macro-averaging to support both binary and multiclass classification.
    """
    accuracy = accuracy_score(y_true, y_pred)
    
    # Calculate precision, recall, f1-score with macro average
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average='macro', zero_division=0
    )
    
    return {
        "target": target_name,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1)
    }

def print_evaluation_summary(metrics):
    """
    Prints a formatted evaluation report for the console.
    """
    print(f"Training target: {metrics['target']}")
    print(f"  Accuracy:  {metrics['accuracy']:.2f}")
    print(f"  Precision: {metrics['precision']:.2f}")
    print(f"  Recall:    {metrics['recall']:.2f}")
    print(f"  F1-Score:  {metrics['f1_score']:.2f}")
    print("-" * 40)
