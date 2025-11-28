"""
Advanced Hybrid VADER Training with XGBoost
============================================

Trains an improved ML component for Hybrid VADER using:
1. High-quality Financial PhraseBank data (gold standard)
2. Twitter Financial News data (real-world social media)
3. XGBoost classifier with optimized hyperparameters
4. Advanced feature engineering with financial domain knowledge
5. Class balancing and cross-validation

Target: 90%+ accuracy on financial sentiment
"""

import asyncio
import sys
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import pickle
from collections import Counter
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.utils.class_weight import compute_class_weight
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

from app.service.sentiment_processing.models.hybrid_vader_model import HybridVADERModel, HybridConfig


# =============================================================================
# Feature Engineering
# =============================================================================

def extract_financial_features(text: str) -> dict:
    """Extract financial-specific features from text."""
    text_lower = text.lower()
    
    # Financial action words
    bullish_actions = ['buy', 'upgrade', 'outperform', 'overweight', 'accumulate', 
                       'bullish', 'long', 'calls', 'raise', 'ups', 'starts at buy']
    bearish_actions = ['sell', 'downgrade', 'underperform', 'underweight', 'reduce',
                       'bearish', 'short', 'puts', 'cut', 'cuts', 'lower', 'weakness']
    neutral_actions = ['hold', 'neutral', 'maintain', 'equal-weight', 'in-line']
    
    bullish_count = sum(1 for word in bullish_actions if word in text_lower)
    bearish_count = sum(1 for word in bearish_actions if word in text_lower)
    neutral_count = sum(1 for word in neutral_actions if word in text_lower)
    
    # Price movement indicators
    price_up = any(w in text_lower for w in ['surge', 'soar', 'jump', 'gain', 'rise', 'climb', 'rally'])
    price_down = any(w in text_lower for w in ['fall', 'drop', 'slide', 'plunge', 'decline', 'tank', 'crash'])
    
    # Analyst actions
    has_ticker = '$' in text
    has_upgrade = 'upgrade' in text_lower or 'ups' in text_lower or 'raise' in text_lower
    has_downgrade = 'downgrade' in text_lower or 'cut' in text_lower or 'lower' in text_lower
    
    # Rating words
    has_buy_rating = any(w in text_lower for w in ['buy', 'outperform', 'overweight'])
    has_sell_rating = any(w in text_lower for w in ['sell', 'underperform', 'underweight'])
    has_hold_rating = any(w in text_lower for w in ['hold', 'neutral', 'equal-weight'])
    
    return {
        'bullish_count': bullish_count,
        'bearish_count': bearish_count,
        'neutral_count': neutral_count,
        'price_up': int(price_up),
        'price_down': int(price_down),
        'has_ticker': int(has_ticker),
        'has_upgrade': int(has_upgrade),
        'has_downgrade': int(has_downgrade),
        'has_buy_rating': int(has_buy_rating),
        'has_sell_rating': int(has_sell_rating),
        'has_hold_rating': int(has_hold_rating),
        'sentiment_direction': bullish_count - bearish_count,
    }


def create_feature_matrix(texts: list, vectorizer: TfidfVectorizer = None, 
                          fit: bool = False) -> tuple:
    """
    Create feature matrix combining TF-IDF and financial features.
    
    Returns:
        (feature_matrix, vectorizer)
    """
    # TF-IDF features
    if fit:
        vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
            stop_words='english'
        )
        tfidf_matrix = vectorizer.fit_transform(texts).toarray()
    else:
        tfidf_matrix = vectorizer.transform(texts).toarray()
    
    # Financial features
    financial_features = []
    for text in texts:
        features = extract_financial_features(text)
        financial_features.append(list(features.values()))
    
    financial_matrix = np.array(financial_features)
    
    # Combine features
    combined = np.hstack([tfidf_matrix, financial_matrix])
    
    return combined, vectorizer


# =============================================================================
# Training
# =============================================================================

def train_xgboost_model(X_train, y_train, X_val, y_val, class_weights):
    """
    Train XGBoost classifier with optimized hyperparameters.
    """
    print("\nTraining XGBoost classifier...")
    
    # Compute sample weights
    sample_weights = np.array([class_weights[y] for y in y_train])
    
    # XGBoost with optimized parameters
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1
    )
    
    # Train with early stopping
    model.fit(
        X_train, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    return model


def evaluate_model(model, X, y, split_name="Test"):
    """Evaluate model and print detailed metrics."""
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    
    print(f"\n{split_name} Results:")
    print(f"  Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    print(f"\n{split_name} Classification Report:")
    print(classification_report(y, y_pred, target_names=['Negative', 'Neutral', 'Positive']))
    
    print(f"\n{split_name} Confusion Matrix:")
    cm = confusion_matrix(y, y_pred)
    print(f"  {'':12} Pred_Neg  Pred_Neu  Pred_Pos")
    print(f"  {'Actual_Neg':12} {cm[0,0]:8}  {cm[0,1]:8}  {cm[0,2]:8}")
    print(f"  {'Actual_Neu':12} {cm[1,0]:8}  {cm[1,1]:8}  {cm[1,2]:8}")
    print(f"  {'Actual_Pos':12} {cm[2,0]:8}  {cm[2,1]:8}  {cm[2,2]:8}")
    
    return accuracy


async def main():
    print("=" * 70)
    print("ADVANCED HYBRID VADER TRAINING")
    print("=" * 70)
    
    # Load both high-quality datasets
    print("\n[1] Loading Financial Sentiment Datasets...")
    
    # Financial PhraseBank (gold standard - professionally annotated)
    df_fpb = pd.read_csv('data/training/financial_phrasebank.csv')
    print(f"  Financial PhraseBank: {len(df_fpb)} samples")
    
    # Twitter Financial News (real-world social media)
    df_twitter = pd.read_csv('data/training/twitter_financial_sentiment.csv')
    print(f"  Twitter Financial: {len(df_twitter)} samples")
    
    # Combine datasets
    df = pd.concat([df_fpb, df_twitter], ignore_index=True)
    
    # Map labels to integers
    label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
    df['label_int'] = df['label'].map(label_map)
    
    # Clean data
    df = df[df['text'].str.len() >= 10].dropna(subset=['label_int'])
    
    print(f"\n  Combined total: {len(df)} samples")
    print(f"  Distribution:")
    for label, count in df['label'].value_counts().items():
        print(f"    {label}: {count} ({count/len(df)*100:.1f}%)")
    
    X = df['text'].tolist()
    y = df['label_int'].values
    
    # Split data (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Further split train into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.15, random_state=42, stratify=y_train
    )
    
    print(f"\n  Training:   {len(X_train)} samples")
    print(f"  Validation: {len(X_val)} samples")
    print(f"  Test:       {len(X_test)} samples")
    
    # Compute class weights for imbalanced data
    class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weight_dict = dict(enumerate(class_weights))
    print(f"\n  Class weights: Neg={class_weight_dict[0]:.2f}, Neu={class_weight_dict[1]:.2f}, Pos={class_weight_dict[2]:.2f}")
    
    # Feature engineering
    print("\n[2] Feature Engineering...")
    X_train_features, vectorizer = create_feature_matrix(X_train, fit=True)
    X_val_features, _ = create_feature_matrix(X_val, vectorizer=vectorizer)
    X_test_features, _ = create_feature_matrix(X_test, vectorizer=vectorizer)
    
    print(f"  Feature dimensions: {X_train_features.shape[1]}")
    
    # Scale features
    print("\n[3] Scaling Features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_features)
    X_val_scaled = scaler.transform(X_val_features)
    X_test_scaled = scaler.transform(X_test_features)
    
    # Train XGBoost only (faster and often better)
    print("\n[4] Training XGBoost Model...")
    
    sample_weights = np.array([class_weight_dict[y] for y in y_train])
    
    # XGBoost with optimized parameters
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=2,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        use_label_encoder=False,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(
        X_train_scaled, y_train,
        sample_weight=sample_weights,
        eval_set=[(X_val_scaled, y_val)],
        verbose=False
    )
    
    # Evaluate
    print("\n[5] Evaluation...")
    
    train_acc = accuracy_score(y_train, model.predict(X_train_scaled))
    val_acc = accuracy_score(y_val, model.predict(X_val_scaled))
    test_acc = accuracy_score(y_test, model.predict(X_test_scaled))
    
    print(f"\n  XGBoost Results:")
    print(f"    Training:   {train_acc:.4f} ({train_acc*100:.2f}%)")
    print(f"    Validation: {val_acc:.4f} ({val_acc*100:.2f}%)")
    print(f"    Test:       {test_acc:.4f} ({test_acc*100:.2f}%)")
    
    best_model = model
    best_acc = test_acc
    best_name = "XGBoost"
    
    # Detailed evaluation of best model
    print(f"\n[6] Detailed {best_name} Results...")
    y_pred = best_model.predict(X_test_scaled)
    
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Negative', 'Neutral', 'Positive']))
    
    print(f"\n  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  {'':12} Pred_Neg  Pred_Neu  Pred_Pos")
    print(f"  {'Actual_Neg':12} {cm[0,0]:8}  {cm[0,1]:8}  {cm[0,2]:8}")
    print(f"  {'Actual_Neu':12} {cm[1,0]:8}  {cm[1,1]:8}  {cm[1,2]:8}")
    print(f"  {'Actual_Pos':12} {cm[2,0]:8}  {cm[2,1]:8}  {cm[2,2]:8}")
    
    # Cross-validation
    print("\n[7] Cross-Validation (5-fold)...")
    all_features, _ = create_feature_matrix(X, vectorizer=vectorizer)
    all_scaled = scaler.transform(all_features)
    
    cv_scores = cross_val_score(best_model, all_scaled, y, cv=5, scoring='accuracy')
    print(f"  CV Scores: {cv_scores}")
    print(f"  CV Mean:   {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    # Save model
    print("\n[8] Saving Model...")
    
    model_dir = Path('data/models')
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save best model
    model_path = model_dir / 'hybrid_vader_xgb.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"  Model saved: {model_path}")
    
    # Save vectorizer
    vectorizer_path = model_dir / 'hybrid_vader_vectorizer.pkl'
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"  Vectorizer saved: {vectorizer_path}")
    
    # Save scaler
    scaler_path = model_dir / 'hybrid_vader_scaler.pkl'
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"  Scaler saved: {scaler_path}")
    
    # Also save as the LR model path for compatibility
    lr_model_path = model_dir / 'hybrid_vader_lr.pkl'
    with open(lr_model_path, 'wb') as f:
        pickle.dump(best_model, f)
    print(f"  Compatibility save: {lr_model_path}")
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n  Best Model:       {best_name}")
    print(f"  Final Test Accuracy: {best_acc:.4f} ({best_acc*100:.2f}%)")
    print(f"  Cross-Validation:    {cv_scores.mean():.4f} ({cv_scores.mean()*100:.2f}%)")
    print("\n" + "=" * 70)
    
    # Test on sample texts
    print("\n[9] Sample Predictions...")
    test_texts = [
        "$AAPL: Morgan Stanley raises to Overweight with $200 price target",
        "$TSLA - Goldman cuts to Sell, sees 40% downside risk",
        "$MSFT reports earnings in line with expectations, maintains guidance",
        "Finnish airline Finnair is starting the temporary layoffs of cabin crews",
        "The company's operating profit rose to EUR 8.0 million from EUR 7.3 million",
        "$AMD - AMD's Navi shows strong adoption - BofA",
        "Net sales decreased to EUR 200 million from EUR 250 million",
    ]
    
    for text in test_texts:
        features, _ = create_feature_matrix([text], vectorizer=vectorizer)
        features_scaled = scaler.transform(features)
        pred = best_model.predict(features_scaled)[0]
        probs = best_model.predict_proba(features_scaled)[0]
        
        label_names = ['Negative', 'Neutral', 'Positive']
        print(f"\n  Text: {text[:65]}...")
        print(f"  Prediction: {label_names[pred]} (confidence: {max(probs):.2f})")
        print(f"  Probs: Neg={probs[0]:.2f}, Neu={probs[1]:.2f}, Pos={probs[2]:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
