#!/bin/bash
echo "Starting AI Meeting Summary Tool..."

# Start the Python backend
cd backend
python summary.py &
BACKEND_PID=$!
cd ..

# Wait a moment for the backend to initialize
sleep 3

# Start the React frontend
npm start

# When npm start is terminated, also kill the Python process
kill $BACKEND_PID 