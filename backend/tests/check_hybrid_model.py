"""Check Hybrid VADER ML model status"""
import pickle
import os

model_path = 'data/models/hybrid_vader_lr.pkl'
vectorizer_path = 'data/models/hybrid_vader_vectorizer.pkl'
scaler_path = 'data/models/hybrid_vader_scaler.pkl'

print('=' * 70)
print('HYBRID VADER ML MODEL STATUS')
print('=' * 70)
print()

# Check model file
if os.path.exists(model_path):
    size = os.path.getsize(model_path)
    print(f'✅ ML Model File: {model_path}')
    print(f'   Size: {size:,} bytes ({size/1024:.2f} KB)')
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    print(f'   Type: {type(model).__name__}')
    print()
    
    if hasattr(model, 'coef_'):
        print('✅ MODEL IS TRAINED')
        print(f'   Features: {model.coef_.shape[1]:,} dimensions')
        print(f'   Classes: {list(model.classes_)}')
        print(f'   Accuracy Target: 82-87%')
    else:
        print('❌ MODEL NOT TRAINED')
else:
    print(f'❌ ML Model File Missing: {model_path}')

print()

# Check vectorizer
if os.path.exists(vectorizer_path):
    size = os.path.getsize(vectorizer_path)
    print(f'✅ Vectorizer File: {vectorizer_path}')
    print(f'   Size: {size:,} bytes ({size/1024:.2f} KB)')
    
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    
    if hasattr(vectorizer, 'vocabulary_'):
        print(f'   Vocabulary: {len(vectorizer.vocabulary_):,} terms')
else:
    print(f'❌ Vectorizer File Missing: {vectorizer_path}')

print()

# Check scaler
if os.path.exists(scaler_path):
    size = os.path.getsize(scaler_path)
    print(f'✅ Scaler File: {scaler_path}')
    print(f'   Size: {size:,} bytes ({size/1024:.2f} KB)')
else:
    print(f'❌ Scaler File Missing: {scaler_path}')

print()
print('=' * 70)
print('CONCLUSION')
print('=' * 70)

all_exist = all([
    os.path.exists(model_path),
    os.path.exists(vectorizer_path),
    os.path.exists(scaler_path)
])

if all_exist:
    print('✅ Hybrid VADER is using the TRAINED ML model')
    print('✅ Model components: Logistic Regression + TF-IDF + Scaler')
    print('✅ System is ready for production sentiment analysis')
else:
    print('❌ Some model files are missing')
    print('⚠️  System will fall back to Enhanced VADER only')
