# Ollama Mistral Integration Setup Guide

This guide will help you set up Ollama with the Mistral model for AI-powered task scheduling.

## Prerequisites

- Python 3.8 or higher
- macOS, Linux, or Windows
- At least 8GB RAM (16GB recommended for better performance)

## Installation Steps

### 1. Install Ollama

#### For macOS:
```bash
# Download and install Ollama from the official website
# Or use Homebrew:
brew install ollama
```

#### For Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### For Windows:
Download the installer from [ollama.com](https://ollama.com/download)

### 2. Start Ollama Service

```bash
# Start the Ollama service
ollama serve
```

The service will start on `http://localhost:11434` by default.

### 3. Pull the Mistral Model

Open a new terminal window (keep the previous one running) and execute:

```bash
# Download the Mistral model
ollama pull mistral
```

This will download the Mistral model (~4GB). Wait for the download to complete.

### 4. Verify Installation

Test if Ollama is working correctly:

```bash
# Test the Mistral model
ollama run mistral "Hello, how are you?"
```

If you see a response, the installation is successful!

### 5. Install Python Dependencies

Navigate to your project directory and install the required packages:

```bash
cd /Users/chinmayjoshi/Desktop/projects/tracker
pip install -r requirements.txt
```

## Using the AI Task Optimizer

### 1. Complete Your Profile

Before using the AI optimizer, make sure to fill out your complete profile:

- **Personal Information**: Name, Role, Main Goals
- **Energy & Preferences**: Peak energy time, Study preference
- **Health & Wellness**: Workout preference, Sleep schedule
- **Weekly Schedule**: Your regular commitments

The more complete your profile, the better the AI can optimize your schedule!

### 2. Add Tasks

Navigate to the Tasks page and add your pending tasks with:
- Description
- Priority (High/Medium/Low)
- Duration
- Type (Study/Work/Personal/Health/Family)
- Preferences (optional)

### 3. Generate AI-Optimized Schedule

#### Option 1: Using the AI Optimizer Button (Floating Button)

1. Click the purple robot icon (🤖) at the bottom-right of any page
2. In the popup, describe your day or specific requirements:
   - Example: "I have college from 9 AM to 5 PM, need to study for an exam"
   - Example: "Focus on high-priority tasks in the morning"
   - Example: "Include extra breaks today"
3. Click "Optimize"
4. Your schedule will be generated and saved automatically
5. Navigate to the Schedule page to view it

#### Option 2: Quick Actions on Dashboard

1. Go to the Dashboard
2. Click "Generate Schedule" button
3. The AI will create a schedule based on your profile and tasks

### 4. View Your Schedule

Navigate to the Schedule page to see:
- Time-blocked schedule from wake time to bedtime
- Task assignments based on your energy levels
- Breaks, meals, and personal time
- Reasoning for each time block
- Helpful productivity tips

## How the AI Works

The Ollama Mistral model analyzes:

1. **Your Profile Data**:
   - Peak energy times
   - Sleep schedule (wake/bed times)
   - Workout preferences
   - Family time commitments
   - Main goals and role

2. **Your Tasks**:
   - Priority levels
   - Estimated durations
   - Task types
   - Special preferences

3. **Your Custom Prompt**:
   - Specific requirements for the day
   - Constraints or deadlines
   - Focus areas

Then it generates an optimized schedule that:
- ✅ Schedules high-priority tasks during peak energy hours
- ✅ Includes appropriate breaks and meals
- ✅ Respects your sleep schedule
- ✅ Balances work, study, health, and personal time
- ✅ Considers your weekly commitments
- ✅ Provides reasoning for each time block

## Troubleshooting

### Ollama Service Not Running

**Error**: "LLM service unavailable" or schedule uses fallback

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Mistral Model Not Found

**Error**: Model not available

**Solution**:
```bash
# Pull the model again
ollama pull mistral

# Verify it's installed
ollama list
```

### Slow Response Times

**Issue**: AI takes too long to generate schedules

**Solutions**:
1. Ensure your system has enough RAM (8GB minimum)
2. Close other resource-intensive applications
3. Consider using a smaller model if needed: `ollama pull mistral:7b`

### Fallback Mode

If Ollama is not available, the system automatically falls back to rule-based scheduling. This ensures you always get a schedule, even if the AI service is down.

The response will include `"source": "fallback"` to indicate this mode.

## Advanced Configuration

### Changing the Model

To use a different Ollama model, edit `llm_service.py`:

```python
def __init__(self, base_url: str = "http://localhost:11434"):
    self.base_url = base_url
    self.model = "mistral"  # Change this to another model
```

Available models:
- `mistral` (recommended, balanced performance)
- `llama2`
- `codellama`
- `mixtral`

### Adjusting Response Parameters

In `llm_service.py`, you can modify:

```python
"options": {
    "temperature": 0.7,  # Lower = more focused, Higher = more creative
    "top_p": 0.9,        # Nucleus sampling parameter
    "max_tokens": 2048   # Maximum response length
}
```

## Benefits of Using the LLM

### Compared to Rule-Based Scheduling:

- **Personalization**: Learns from your specific profile and preferences
- **Context Understanding**: Interprets natural language prompts
- **Flexibility**: Adapts to changing requirements and constraints
- **Intelligent Reasoning**: Provides explanations for scheduling decisions
- **Holistic Planning**: Considers multiple factors simultaneously

## Tips for Best Results

1. **Complete Profile**: Fill out all profile fields for better optimization
2. **Clear Prompts**: Be specific about your requirements
   - ❌ "Make me a schedule"
   - ✅ "I need to focus on exam preparation from 2-5 PM, and I have a meeting at 11 AM"

3. **Regular Updates**: Update your tasks and profile regularly
4. **Review & Adjust**: The AI provides suggestions - adjust as needed
5. **Provide Feedback**: If a schedule doesn't work, try refining your prompt

## Privacy & Data

- All processing happens **locally** on your machine
- No data is sent to external servers
- Ollama runs entirely offline once the model is downloaded
- Your profile and tasks remain in your local database

## Support

For issues or questions:
1. Check this guide first
2. Verify Ollama is running: `ollama list`
3. Check application logs for error messages
4. Ensure all profile fields are filled out

---

**Made with ❤️ by [chinu](https://chinmay-joshi-4au4ky2.gamma.site/)**
