#!/bin/bash
echo "Starting AI Meeting Summary Tool..."

# Check if concurrently is installed
if ! npm list | grep -q concurrently; then
    echo "Installing concurrently package..."
    npm install
fi

# Run the application
echo "Running both backend and frontend..."
npm run app 