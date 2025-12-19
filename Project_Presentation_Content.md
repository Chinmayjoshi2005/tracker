# Project Presentation: AI-Powered Schedule Optimizer

## Slide 1: Title Slide
**Title:** AI-Powered Schedule Optimizer
**Subtitle:** A Personalized Productivity Assistant using Local LLMs
**Presenter:** Chinmay Joshi
**Date:** December 2025

---

## Slide 2: The Problem
- **Inefficiency:** People list tasks but don't plan *when* to do them.
- **Burnout:** lack of scheduled breaks and over-commitment.
- **Decision Fatigue:** Wasting energy deciding "what to do next".
- **One-size-fits-all:** Traditional calendars ignore individual energy peaks and circadian rhythms.

---

## Slide 3: The Solution
**An Intelligent Task Tracker & Scheduler** that doesn't just list tasks, but **plans your day**.
- **Personalized:** Adapts to your sleep schedule, energy levels, and habits.
- **AI-Driven:** Uses Advanced LLMs (Ollama/Mistral) to reason about time and priority.
- **Adaptive:** Re-optimizes based on new tasks or changes in plans.

---

## Slide 4: Key Features
1.  **Smart Profile Engine:** Tracks wake/sleep times, peak energy windows, and workout preferences.
2.  **AI Schedule Generation:** Converts a list of tasks into a time-blocked itinerary.
3.  **Task Management:** Priority-based task organization (High/Medium/Low).
4.  **Analytics Dashboard:** Visual insights into productivity trends and completion predictions.
5.  **Interactive Chat:** Ask the AI for quick productivity tips or schedule adjustments.

---

## Slide 5: How It Works (The AI Engine)
1.  **Input:** User Profile + Pending Tasks + User Prompt (e.g., "I want a chill day").
2.  **Processing:** 
    - The system constructs a detailed "Context Prompt".
    - Sends it to the **Ollama Mistral** model running locally.
3.  **Validation:**
    - The generated JSON is validated for time conflicts.
    - A **Scoring Algorithm** rates the schedule (0-100) on "Realism" and "Balance".
4.  **Output:** A structured, easy-to-read timeline displayed on the dashboard.

---

## Slide 6: Technical Stack
- **Frontend:** HTML5, CSS3, JavaScript (Jinja2 Templates) - Responsive Design.
- **Backend:** Python Flask - Robust and scalable REST API.
- **Database:** SQLite/PostgreSQL with SQLAlchemy ORM.
- **AI/ML:** 
    - **Ollama:** For running LLMs locally.
    - **Mistral:** The underlying language model.
    - **Scikit-learn:** For basic predictive analytics (completion probability).

---

## Slide 7: User Interface (UI) Highlights
- **Dashboard:** At-a-glance view of "Pending vs Completed" tasks.
- **Schedule View:** A vertical timeline connecting tasks with specific time slots.
- **Dark Mode/Premium Theme:** Modern, aesthetic design for reduced eye strain.

---

## Slide 8: Future Extensions
- **Calendar Sync:** Two-way sync with Google Calendar.
- **Mobile App:** Dedicated iOS/Android application.
- **Team Mode:** Collaborative scheduling for group projects.
- **Voice Commands:** "Hey Tracker, schedule a meeting at 4 PM."

---

## Slide 9: Conclusion
This project bridges the gap between **Task Management** and **Time Management**. By offloading the planning effort to AI, users can focus entirely on execution, leading to higher productivity and better work-life balance.

---

## Slide 10: Thank You
**Questions?**
