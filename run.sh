#!/bin/bash

echo "Starting LA Zoning Lookup..."
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt

echo "Starting backend server..."
python main.py &
BACKEND_PID=$!

echo "Backend running on http://localhost:8000"
echo "Opening frontend..."

cd ../frontend
if command -v open &> /dev/null; then
    open index.html
elif command -v xdg-open &> /dev/null; then
    xdg-open index.html
else
    echo "Please open frontend/index.html in your browser"
fi

echo "Press Ctrl+C to stop the server"
wait $BACKEND_PID