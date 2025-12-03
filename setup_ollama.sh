#!/bin/bash

# Ollama Installation and Setup Script for Task Optimizer

echo "======================================"
echo "  Ollama Mistral Setup for Task Optimizer"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Ollama is installed
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
else
    echo -e "${RED}✗ Ollama is not installed${NC}"
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS: brew install ollama"
    echo "  Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: Download from ollama.com/download"
    echo ""
    exit 1
fi

# Check if Ollama service is running
echo ""
echo "Checking Ollama service..."
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✓ Ollama service is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama service is not running${NC}"
    echo "Starting Ollama service in background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✓ Ollama service started successfully${NC}"
    else
        echo -e "${RED}✗ Failed to start Ollama service${NC}"
        echo "Please start it manually: ollama serve"
        exit 1
    fi
fi

# Check if Mistral model is installed
echo ""
echo "Checking Mistral model..."
if ollama list | grep -q "mistral"; then
    echo -e "${GREEN}✓ Mistral model is installed${NC}"
else
    echo -e "${YELLOW}⚠ Mistral model not found${NC}"
    echo "Downloading Mistral model (this may take a few minutes)..."
    ollama pull mistral
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Mistral model downloaded successfully${NC}"
    else
        echo -e "${RED}✗ Failed to download Mistral model${NC}"
        exit 1
    fi
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install Python dependencies${NC}"
    echo "Please run: pip install -r requirements.txt"
fi

# Test Ollama connection
echo ""
echo "Testing Ollama connection..."
RESPONSE=$(curl -s -X POST http://localhost:11434/api/generate \
    -d '{
        "model": "mistral",
        "prompt": "Say hello in 3 words",
        "stream": false
    }')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Ollama is responding correctly${NC}"
else
    echo -e "${RED}✗ Ollama test failed${NC}"
fi

# Summary
echo ""
echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Run the application: python app.py"
echo "2. Open your browser: http://localhost:5012"
echo "3. Complete your profile with all details"
echo "4. Add some tasks"
echo "5. Click the AI robot icon (🤖) to optimize your schedule"
echo ""
echo -e "${GREEN}Ollama Mistral is ready to optimize your tasks!${NC}"
echo ""
