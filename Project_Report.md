# Project Report: AI-Powered Personal Schedule Optimizer

## 1. Abstract
The **AI-Powered Personal Schedule Optimizer** is a web-based application designed to revolutionize personal time management. By leveraging Local Large Language Models (LLMs) via Ollama, the application generates highly personalized daily schedules based on user energy levels, task priorities, and circadian rhythms. Unlike traditional calendar apps, this system actively optimizes the user's day for maximum productivity and work-life balance, offering features like intelligent task batching, dynamic break scheduling, and performance analytics.

## 2. Introduction
### 2.1 Problem Statement
In today's fast-paced environment, individuals struggle with time management, often leading to burnout, procrastination, and inefficient work patterns. Traditional to-do lists fail to account for "when" a task should be done based on cognitive capacity, and rigid calendars lack the flexibility to adapt to daily energy fluctuations.

### 2.2 Proposed Solution
This project introduces an intelligent "Tracker" that acts as a personal productivity assistant. It combines task management with AI-driven scheduling algorithms to create a daily plan that aligns with the user's biological clock (chronotype). The system learns from user preferences (e.g., "Deep work in the morning", "Workout in the evening") to suggest the optimal time for every activity.

## 3. System Architecture
The application follows a Model-View-Controller (MVC) architecture functionality:
- **Frontend:** HTML5, CSS3, and JavaScript served via Jinja2 templates.
- **Backend:** Python Flask framework handling routing, authentication, and business logic.
- **Database:** SQLite (dev) / PostgreSQL (prod) via SQLAlchemy ORM for storing users, tasks, schedules, and analytics.
- **AI Engine:** Integrated with **Ollama (Mistral Model)** running locally to process natural language prompts and generate JSON-structured schedules.

## 4. Key Features
### 4.1 Smart Profile Management
Users define a comprehensive profile including:
- **Peak Energy Times:** (e.g., Morning, Late Night)
- **Sleep Schedule:** (Wake up / Bedtime)
- **Habits:** Study preferences, workout impact, and family commitments.

### 4.2 AI Schedule Generation
The core feature uses a prompt engineering pipeline to generating schedules. The system:
- Analyzes pending tasks and their priorities.
- Respects constraints (classes, work hours, meals).
- Incorporates "Energy-Aligned Scheduling" to place high-cognitive tasks during peak hours.
- **Safety Mechanism:** Includes a rule-based fallback algorithm if the LLM service is unavailable.

### 4.3 Task Management & Analytics
- **CRUD Operations:** robust system to Create, Read, Update, and Delete tasks.
- **Visual Analytics:** Interactive charts displaying login frequency, task completion rates, and predicted completion probabilities using historical data.

### 4.4 Quality Scoring System
Every generated schedule is scored on:
- **Energy Alignment:** Matching difficult tasks to peak energy.
- **Realism:** Avoiding over-scheduling.
- **Work-Life Balance:** Ensuring adequate breaks and personal time.

## 5. Technical Implementation Details
### 5.1 The AI Pipeline (`llm_service.py`)
The system constructs a complex prompt containing the user's profile and tasks. It requests a strictly formatted JSON response from the Mistral model. A post-processing validation step parses this JSON, calculates a "Productivity Score," and inserts improvement suggestions (e.g., "Add more breaks").

### 5.2 Database Model (`models.py`)
Relational models link `Users` to `Tasks` and `Schedules`. The `Schedule` model stores the entire daily plan as a JSON blob, allowing for flexible schema changes in the generated output.

### 5.3 Security
- Password hashing using `werkzeug.security`.
- Session management via `flask_login`.
- CSRF protection for forms.

## 6. Future Scope
- **Google Calendar Integration:** Direct syncing of generated schedules to Google/Outlook/Apple Calendar.
- **Mobile Application:** A React Native version for on-the-go access.
- **Voice Interface:** Integration with generic voice assistants for adding tasks.

## 7. Conclusion
The AI-Powered Schedule Optimizer successfully demonstrates how local LLMs can be applied to practical, daily problems. By personalizing time management, it helps users maximize their potential while maintaining a healthy lifestyle.
