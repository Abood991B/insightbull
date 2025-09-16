#!/bin/bash
echo "Creating Python virtual environment..."
python -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Virtual environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate"