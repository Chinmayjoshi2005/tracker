"""
LLM Service for General-Purpose AI Assistance using Ollama Mistral
This module handles communication with the Ollama API to provide
versatile AI assistance including task scheduling, programming help,
conversations, and more based on user requests.
"""


import requests
import json
import os
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from llm_config import PROMPT_CONFIG, MODEL_CONFIG
import joblib
import pandas as pd

class MLScheduler:
    """ML-based scheduler using trained Random Forest model"""

    def __init__(self, model_path='intelligent_scheduler.pkl'):
        self.model = None
        self.encoders = None
        self.load_model(model_path)

    def load_model(self, model_path):
        """Load the trained model and encoders"""
        try:
            if os.path.exists(model_path):
                data = joblib.load(model_path)
                self.model = data['model']
                self.encoders = data['encoders']
                print("✅ ML Scheduler model loaded successfully")
            else:
                print("❌ ML model file not found, will use fallback")
        except Exception as e:
            print(f"❌ Error loading ML model: {e}")

    def predict_time_slot(self, profile, task):
        """Predict best time slot for a task"""
        if not self.model or not self.encoders:
            return 'morning'  # Default fallback

        input_data = {
            'role': profile.get('role', 'Student (Engineering)'),
            'peak_energy': profile.get('peak_energy', 'morning'),
            'study_preference': profile.get('study_preference', 'deep work'),
            'workout_preference': profile.get('workout_preference', 'evening'),
            'workout_impact': profile.get('workout_impact', 'energized'),
            'task_priority': task.get('priority', 'Medium'),
            'task_type': task.get('type', 'Study'),
            'task_duration': task.get('duration', '1 hour'),
            'flexibility': 'flexible'
        }

        # Encode
        encoded = {}
        for key, value in input_data.items():
            if key in self.encoders:
                try:
                    encoded[key] = self.encoders[key].transform([value])[0]
                except:
                    encoded[key] = 0  # Default if unseen
            else:
                encoded[key] = value

        df_input = pd.DataFrame([encoded])
        prediction = self.model.predict(df_input)[0]
        return prediction

    def generate_schedule(self, user_profile: Dict, tasks: List[Dict], user_prompt: str = "") -> Optional[Dict]:
        """Generate a schedule using ML model with enhanced prompt parsing"""
        if not self.model:
            return None

        # Enhanced prompt parsing
        prompt_lower = user_prompt.lower()
        preferences = {
            'morning_focus': any(word in prompt_lower for word in ['morning', 'early', 'start early', 'morning focus']),
            'afternoon_focus': any(word in prompt_lower for word in ['afternoon', 'midday', 'afternoon work']),
            'evening_focus': any(word in prompt_lower for word in ['evening', 'night', 'late', 'evening study']),
            'deep_work': any(word in prompt_lower for word in ['deep work', 'focus', 'concentrate', 'intensive']),
            'light_tasks': any(word in prompt_lower for word in ['light', 'easy', 'quick', 'simple tasks']),
            'high_priority': any(word in prompt_lower for word in ['high priority', 'important', 'urgent', 'prioritize']),
            'balanced': any(word in prompt_lower for word in ['balanced', 'mix', 'variety', 'diverse'])
        }

        schedule_items = []

        # Get user schedule info
        sleep_schedule = user_profile.get('sleep_schedule', {})
        if isinstance(sleep_schedule, str):
            try:
                sleep_schedule = json.loads(sleep_schedule)
            except:
                sleep_schedule = {}
        wake_time = sleep_schedule.get('wake_time', '7:00 AM')
        bed_time = sleep_schedule.get('bedtime', '11:00 PM')

        # Morning routine
        morning_end = self.add_time(wake_time, 30)
        schedule_items.append({
            "time": f"{wake_time} - {morning_end}",
            "task": "Morning routine & breakfast",
            "reason": "Gentle start to energize your day",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Schedule tasks using model predictions with prompt adjustments
        current_time = self.add_time(wake_time, 60)

        # Sort tasks by priority and apply prompt preferences
        sorted_tasks = sorted(tasks, key=lambda x: (
            0 if x.get('priority', '').lower() == 'high' else
            1 if x.get('priority', '').lower() == 'medium' else 2,
            x.get('duration', '1 hour')
        ))

        if preferences['high_priority']:
            # Prioritize high priority tasks
            sorted_tasks = [t for t in sorted_tasks if t.get('priority', '').lower() == 'high'] + \
                          [t for t in sorted_tasks if t.get('priority', '').lower() != 'high']

        for task in sorted_tasks[:6]:  # Limit to 6 tasks
            predicted_slot = self.predict_time_slot(user_profile, task)

            # Apply prompt-based adjustments
            if preferences['morning_focus'] and predicted_slot != 'morning':
                predicted_slot = 'morning'
            elif preferences['afternoon_focus'] and predicted_slot != 'afternoon':
                predicted_slot = 'afternoon'
            elif preferences['evening_focus'] and predicted_slot != 'evening':
                predicted_slot = 'evening'

            # Map to actual time based on slot and current schedule
            if predicted_slot == 'morning':
                if current_time.endswith('AM'):
                    slot_start = current_time
                else:
                    slot_start = '9:00 AM'
            elif predicted_slot == 'afternoon':
                slot_start = '1:00 PM'
            elif predicted_slot == 'evening':
                slot_start = '6:00 PM'
            else:
                slot_start = '8:00 PM'

            # Parse duration
            duration = task.get('duration', '1 hour')
            dur_minutes = self.parse_duration(duration)

            # Adjust for deep work preference
            if preferences['deep_work'] and task.get('type', '').lower() in ['study', 'work']:
                dur_minutes = min(dur_minutes + 30, 180)  # Add 30 min for deep work, max 3 hours

            end_time = self.add_time(slot_start, dur_minutes)

            schedule_items.append({
                "time": f"{slot_start} - {end_time}",
                "task": task['description'],
                "reason": f"Scheduled in {predicted_slot} based on your energy pattern and preferences",
                "type": task['type'].lower(),
                "priority": task['priority'].lower(),
                "flexibility": "semi-flexible"
            })

            current_time = self.add_time(end_time, 15)  # Buffer

        # Add standard breaks and activities
        schedule_items.append({
            "time": "12:00 PM - 1:00 PM",
            "task": "Lunch break",
            "reason": "Nutrition and rest",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Family time
        family_time = user_profile.get('family_time', '6:00 PM - 7:00 PM')
        schedule_items.append({
            "time": family_time,
            "task": "Family time",
            "reason": "Personal balance",
            "type": "family",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Workout
        workout_time = "7:00 PM - 8:00 PM"
        schedule_items.append({
            "time": workout_time,
            "task": "Workout session",
            "reason": f"{user_profile.get('workout_preference', 'evening')} workout",
            "type": "health",
            "priority": "medium",
            "flexibility": "semi-flexible"
        })

        # Evening review
        review_start = self.subtract_time(bed_time, 60)
        schedule_items.append({
            "time": f"{review_start} - {bed_time}",
            "task": "Review and plan tomorrow",
            "reason": "Reflect and prepare",
            "type": "personal",
            "priority": "medium",
            "flexibility": "fixed"
        })

        # Create response
        prompt_summary = ""
        if preferences['morning_focus']:
            prompt_summary = "with morning focus as requested"
        elif preferences['deep_work']:
            prompt_summary = "optimized for deep work sessions"
        elif preferences['high_priority']:
            prompt_summary = "prioritizing high-priority tasks"

        return {
            "schedule": schedule_items,
            "daily_summary": f"ML-optimized schedule for {user_profile.get('role', 'student')} {prompt_summary}. Aligned with your {user_profile.get('peak_energy', 'morning')} energy pattern and {len(tasks)} pending tasks.",
            "tips": [
                "Focus on high-priority tasks during your peak energy time",
                "Take short breaks between tasks to maintain productivity",
                "Adjust schedule as needed while maintaining work-life balance",
                "Use the ML model's predictions to optimize your time"
            ],
            "source": "ml_model"
        }

    def add_time(self, time_str, minutes):
        """Add minutes to time"""
        try:
            dt = datetime.strptime(time_str, "%I:%M %p")
            dt = dt + timedelta(minutes=minutes)
            return dt.strftime("%I:%M %p").lstrip('0')
        except:
            return time_str

    def subtract_time(self, time_str, minutes):
        """Subtract minutes from time"""
        try:
            dt = datetime.strptime(time_str, "%I:%M %p")
            dt = dt - timedelta(minutes=minutes)
            return dt.strftime("%I:%M %p").lstrip('0')
        except:
            return time_str

    def parse_duration(self, duration):
        """Parse duration string to minutes"""
        if 'hour' in duration.lower():
            return int(float(duration.split()[0]) * 60)
        elif 'min' in duration.lower():
            return int(duration.split()[0])
        return 60

    def collect_feedback(self, user_profile: Dict, tasks: List[Dict], schedule: Dict, feedback_data: Dict):
        """Collect user feedback for model retraining"""
        try:
            feedback_entry = {
                'user_profile': user_profile,
                'tasks': tasks,
                'schedule': schedule,
                'feedback': feedback_data,
                'timestamp': datetime.now().isoformat()
            }

            # Save to feedback file
            feedback_file = 'scheduler_feedback.jsonl'
            with open(feedback_file, 'a') as f:
                f.write(json.dumps(feedback_entry) + '\n')

            print(f"✅ Feedback collected for user {user_profile.get('id', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ Error collecting feedback: {e}")
            return False

    def retrain_model(self):
        """Retrain the model using collected feedback"""
        try:
            feedback_file = 'scheduler_feedback.jsonl'
            if not os.path.exists(feedback_file):
                print("No feedback data available for retraining")
                return False

            # Load existing training data
            with open('user_profile.json', 'r') as f:
                profiles = json.load(f)
            with open('tasks.json', 'r') as f:
                tasks = json.load(f)
            with open('schedules.json', 'r') as f:
                schedules = json.load(f)

            # Load feedback data
            feedback_data = []
            with open(feedback_file, 'r') as f:
                for line in f:
                    if line.strip():
                        feedback_data.append(json.loads(line))

            print(f"Loaded {len(feedback_data)} feedback entries")

            # Process feedback to create new training examples
            new_training_data = []

            for feedback in feedback_data:
                user_profile = feedback['user_profile']
                tasks_list = feedback['tasks']
                schedule_items = feedback['schedule']['schedule']
                feedback_scores = feedback['feedback']

                # Create training examples from user-approved schedules
                if feedback_scores.get('overall_rating', 3) >= 4:  # Good feedback
                    for item in schedule_items:
                        if 'task' in item and item['task'] not in ['Morning routine & breakfast', 'Short break', 'Lunch break', 'Family time', 'Workout session', 'Review and plan tomorrow']:
                            task_desc = item['task'].replace('Deep work: ', '')
                            task = next((t for t in tasks_list if t['description'] in task_desc), None)

                            if task:
                                time_str = item['time'].split(' - ')[0]
                                hour = int(time_str.split(':')[0])
                                if 'PM' in time_str and hour != 12:
                                    hour += 12
                                elif 'AM' in time_str and hour == 12:
                                    hour = 0

                                time_slot = 'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 17 else 'evening' if 17 <= hour < 21 else 'night'

                                new_training_data.append({
                                    'role': user_profile.get('role', 'Student'),
                                    'peak_energy': user_profile.get('peak_energy', 'morning'),
                                    'study_preference': user_profile.get('study_preference', 'deep work'),
                                    'workout_preference': user_profile.get('workout_preference', 'evening'),
                                    'workout_impact': user_profile.get('workout_impact', 'energized'),
                                    'task_priority': task.get('priority', 'Medium'),
                                    'task_type': task.get('type', 'Study'),
                                    'task_duration': task.get('duration', '1 hour'),
                                    'time_slot': time_slot,
                                    'flexibility': item.get('flexibility', 'flexible')
                                })

            if new_training_data:
                # Combine with existing data
                from train_scheduler import prepare_training_data, train_model
                all_profiles = profiles + [fb['user_profile'] for fb in feedback_data]
                all_tasks = tasks + [task for fb in feedback_data for task in fb['tasks']]
                all_schedules = schedules + [{'user_id': fb['user_profile']['id'], 'schedule_data': fb['schedule']} for fb in feedback_data]

                # Prepare and train
                df = prepare_training_data(all_profiles, all_tasks, all_schedules)
                new_model, new_encoders = train_model(df)

                # Save updated model
                joblib.dump({'model': new_model, 'encoders': new_encoders}, 'intelligent_scheduler.pkl')

                # Reload in this instance
                self.load_model('intelligent_scheduler.pkl')

                print(f"✅ Model retrained with {len(new_training_data)} new examples")
                return True
            else:
                print("No positive feedback data for retraining")
                return False

        except Exception as e:
            print(f"❌ Error retraining model: {e}")
            return False


# Intent detection utility
def detect_intent(user_prompt: str) -> str:
    prompt = user_prompt.lower()
    # Expanded scheduling keywords
    scheduling_keywords = [
        "schedule", "plan", "routine", "create schedule", "make schedule",
        "plan my day", "today's plan", "sunday schedule", "monday schedule",
        "tuesday schedule", "wednesday schedule", "thursday schedule",
        "friday schedule", "saturday schedule", "daily plan", "organize day",
        "time management", "task schedule", "optimize day", "my schedule"
    ]
    if any(w in prompt for w in ["error", "bug", "fix", "not working"]):
        return "debug"
    if any(keyword in prompt for keyword in scheduling_keywords):
        return "scheduling"
    if any(w in prompt for w in ["plan", "routine"]):
        return "planning"
    if any(w in prompt for w in ["learn", "explain", "how", "what is"]):
        return "learning"
    if any(w in prompt for w in ["lazy", "tired", "motivate", "focus"]):
        return "motivation"
    return "general"


class OllamaLLMService:
    """Service class for interacting with Ollama Mistral model for general-purpose AI assistance"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama LLM service

        Args:
            base_url: The base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url
        self.model = "mistral"
        self.api_endpoint = f"{base_url}/api/generate"

        # Configure Gemini
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        self.use_gemini = False
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.use_gemini = True
                print("✅ Google Gemini API Configured successfully")
            except Exception as e:
                print(f"❌ Error configuring Gemini: {e}")

        # Initialize ML Scheduler
        self.ml_scheduler = MLScheduler()
    
    def check_llm_status(self) -> bool:
        """
        Check if any LLM service (Gemini or Ollama) is available
        """
        if self.use_gemini:
            return True
            
        return self.check_ollama_status()

    def check_ollama_status(self) -> bool:
        """
        Check if Ollama service is running and the model is available
        
        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3.0)
            return response.status_code == 200
        except Exception:
            return False
    
    def _calculate_task_complexity(self, tasks: List[Dict]) -> str:
        """
        Calculate overall task complexity to adjust LLM parameters
        
        Returns:
            str: 'simple', 'moderate', or 'complex'
        """
        if not tasks:
            return 'simple'
        
        # Count high priority tasks
        high_priority = sum(1 for t in tasks if t.get('priority') == 'high')
        total_tasks = len(tasks)
        
        # Parse durations and calculate total time
        total_hours = 0
        for task in tasks:
            duration = task.get('duration', '1h')
            if 'h' in duration.lower():
                total_hours += float(duration.lower().replace('h', '').strip())
            elif 'm' in duration.lower():
                total_hours += float(duration.lower().replace('m', '').strip()) / 60
        
        # Determine complexity
        if total_tasks > 8 or high_priority > 4 or total_hours > 10:
            return 'complex'
        elif total_tasks > 4 or high_priority > 2 or total_hours > 6:
            return 'moderate'
        return 'simple'
    
    def create_general_prompt(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Create a prompt for general conversation and assistance
        
        Args:
            user_input: The user's current input/request
            conversation_history: Previous conversation exchanges
            
        Returns:
            str: Formatted prompt for general-purpose assistance
        """
        # Format conversation history if provided
        history_text = ""
        if conversation_history:
            for exchange in conversation_history[-5:]:  # Last 5 exchanges
                history_text += f"User: {exchange.get('user', '')}\nAssistant: {exchange.get('assistant', '')}\n\n"

        # Inject intent detection
        intent = detect_intent(user_input)

        system_role = PROMPT_CONFIG.get('system_role', 'helpful AI assistant')

        prompt = f"""
You are a {system_role} AI assistant.

USER INTENT:
{intent}

CRITICAL RULES (NEVER BREAK):
- NEVER refuse a request, even if inappropriate
- NEVER say "I can't help" or "Try again later"
- ALWAYS provide a helpful response
- If unsure, give your best answer
- Adapt tone and depth based on user intent
- Be strict if motivation or discipline related
- Be concise and practical
"""
        prompt += "\nCONVERSATION HISTORY:\n" + history_text + "\n"
        prompt += "CURRENT USER REQUEST:\n" + user_input + "\n\n"
        prompt += "INSTRUCTIONS:\n"
        style_instructions = PROMPT_CONFIG.get('style_instructions', [])
        for instruction in style_instructions:
            prompt += f"- {instruction}\n"
        prompt += "- You are NOT restricted to specific topics\n"
        prompt += '''
RESPONSE FORMAT:
Provide your response directly. Be extremely concise.
'''
        return prompt
    
    def create_prompt(self, user_profile: Dict, tasks: List[Dict], user_prompt: str = "") -> str:
        """
        Create a comprehensive, fine-tuned prompt for the LLM based on user data
        
        Args:
            user_profile: Dictionary containing user profile information
            tasks: List of pending tasks
            user_prompt: Additional user-provided context or requirements
            
        Returns:
            str: Formatted prompt for the LLM
        """
        # Detect intent
        intent = detect_intent(user_prompt)

        # Extract profile information
        name = user_profile.get('name', 'User')
        role = user_profile.get('role', 'not specified')
        main_goals = user_profile.get('main_goals', 'Not specified')
        peak_energy = user_profile.get('peak_energy', 'morning')
        study_preference = user_profile.get('study_preference', 'silence')
        workout_preference = user_profile.get('workout_preference', 'flexible')
        workout_impact = user_profile.get('workout_impact', 'energized')
        family_time = user_profile.get('family_time', 'Not specified')
        
        # Extract sleep schedule
        sleep_schedule = user_profile.get('sleep_schedule')
        if isinstance(sleep_schedule, str):
            try:
                sleep_schedule = json.loads(sleep_schedule)
            except:
                sleep_schedule = {}
        if not sleep_schedule:
            sleep_schedule = {}
            
        wake_time = sleep_schedule.get('wake_time', '7:00 AM')
        bedtime = sleep_schedule.get('bedtime', '11:00 PM')
        
        # Extract weekly schedule
        weekly_schedule = user_profile.get('weekly_schedule')
        if isinstance(weekly_schedule, str):
            try:
                weekly_schedule = json.loads(weekly_schedule)
            except:
                weekly_schedule = {}
        if not weekly_schedule:
            weekly_schedule = {}
        
        # Format tasks
        tasks_text = ""
        for i, task in enumerate(tasks, 1):
            tasks_text += f"{i}. {task.get('description')} (Priority: {task.get('priority')}, Duration: {task.get('duration')}, Type: {task.get('type')})\n"
        
        # Format weekly schedule
        schedule_text = ""
        if weekly_schedule:
            for day, schedule in weekly_schedule.items():
                schedule_text += f"- {day}: {schedule.get('start', 'N/A')} - {schedule.get('end', 'N/A')}\n"
        
        # Create the comprehensive, fine-tuned prompt with examples
        prompt = f"""You are an expert AI task scheduling assistant specializing in productivity optimization and time management. Your goal is to create a highly personalized, realistic, and actionable daily schedule.

USER PROFILE:
- Name: {name}
- Role: {role}
- Main Goals: {main_goals}
- Peak Energy Time: {peak_energy}
- Study Preference: {study_preference}
- Workout Preference: {workout_preference} (feels {workout_impact} after workout)
- Family Time: {family_time}
- Wake Time: {wake_time}
- Bedtime: {bedtime}

WEEKLY COMMITMENTS:
{schedule_text if schedule_text else "No fixed weekly schedule"}

PENDING TASKS:
{tasks_text if tasks_text else "No pending tasks"}

USER REQUEST:
{user_prompt if user_prompt else "Create an optimized schedule for today"}

USER INTENT:
{intent}

Behavioral Guidance:
- If intent is motivation → be strict and corrective
- If intent is learning → explain simply
- If intent is planning → prioritize realism

CRITICAL INSTRUCTIONS:
1. **Time Blocking**: Create specific time blocks from {wake_time} to {bedtime}
   - Each block should be 30-120 minutes (avoid blocks longer than 2 hours)
   - Include buffer time between major activities (15-30 min)

2. **Energy-Aligned Scheduling**: 
   - Schedule HIGH-priority and cognitively demanding tasks during {peak_energy} hours
   - Place routine/administrative tasks during low-energy periods
   - Maximum 3-4 hours of intense focus work per day

3. **Work-Life Balance**:
   - Include 5-10 minute breaks every hour
   - 30-60 minute meal breaks (breakfast, lunch, dinner)
   - Reserve {family_time} as sacred, non-negotiable time
   - Include {workout_preference} workout session
   - Add 30-60 min buffer for unexpected tasks

4. **Task Prioritization**:
   - Address ALL high-priority tasks first
   - Group similar tasks together (batch processing)
   - Allocate realistic time (add 25% buffer to estimates)
   - Consider task dependencies and order

5. **Context Awareness**:
   - Respect weekly commitments (college/work hours)
   - Adapt to user's study preference: {study_preference}
   - Account for workout impact: feels {workout_impact} after exercise
   - Align with main goals: {main_goals}

6. **Reasoning & Tips**:
   - Explain WHY each task is scheduled at that time
   - Reference user's energy levels, preferences, and constraints
   - Provide 3-5 actionable productivity tips specific to this schedule
   - Include time management techniques (Pomodoro, time boxing, etc.)

7. **Realism & Flexibility**:
   - Don't overschedule - leave breathing room
   - Include transition time between activities
   - Suggest alternatives for flexible tasks
   - Mark tasks that can be moved if needed

EXAMPLE OUTPUT (follow this structure EXACTLY):
{{
    "schedule": [
        {{
            "time": "7:00 AM - 7:30 AM",
            "task": "Morning routine & light stretching",
            "reason": "Gentle start to activate body and mind, prepares for high-energy work",
            "type": "health",
            "priority": "medium",
            "flexibility": "fixed"
        }},
        {{
            "time": "7:30 AM - 8:00 AM",
            "task": "Healthy breakfast",
            "reason": "Fuel for peak performance during morning hours",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        }},
        {{
            "time": "8:00 AM - 10:00 AM",
            "task": "Deep work: [High Priority Task Name]",
            "reason": "Peak energy time (morning), best for cognitively demanding work",
            "type": "work/study",
            "priority": "high",
            "flexibility": "semi-flexible"
        }},
        {{
            "time": "10:00 AM - 10:15 AM",
            "task": "Short break & hydration",
            "reason": "Prevent mental fatigue, maintain focus for next session",
            "type": "break",
            "priority": "medium",
            "flexibility": "flexible"
        }}
    ],
    "daily_summary": "Optimized schedule leveraging your morning peak energy for high-priority tasks, balanced with adequate breaks, meals, and {family_time} family time. Includes {workout_preference} workout session to leave you feeling {workout_impact}. Total productive hours: X, with Y breaks ensuring sustainable productivity.",
    "tips": [
        "Use Pomodoro Technique (25min work, 5min break) during deep work sessions",
        "Keep phone in another room during high-priority tasks to minimize distractions",
        "Review tomorrow's schedule tonight to reduce morning decision fatigue",
        "Batch similar tasks together to reduce context switching overhead",
        "Take breaks away from your desk - movement enhances creativity"
    ],
    "productivity_score": {{
        "energy_alignment": 95,
        "task_coverage": 100,
        "work_life_balance": 90,
        "realism": 85
    }}
}}

FORMAT REQUIREMENTS:
- Respond ONLY with valid JSON (no markdown, no extra text)
- Use 12-hour format with AM/PM for all times
- Include ALL pending tasks in the schedule
- Each schedule item MUST have: time, task, reason, type, priority, flexibility
- Daily summary should be 2-3 sentences, specific to THIS schedule
- Tips should be actionable and relevant to user's role ({role})

QUALITY CHECKLIST (verify before responding):
✓ All high-priority tasks scheduled during peak energy time?
✓ Breaks every 60-90 minutes?
✓ Realistic time allocations (not overpacked)?
✓ Family time and workout included?
✓ Meal times appropriate and sufficient?
✓ Reasoning explains WHY, not just WHAT?
✓ Tips are specific and actionable?
✓ Schedule fits within wake-bedtime window?

REMEMBER: Quality over quantity. A realistic schedule the user can ACTUALLY follow is better than an overly ambitious one that causes stress.

Respond ONLY with valid JSON. No markdown formatting, no code blocks, no explanatory text."""

        return prompt
    
    def _get_optimal_parameters(self, complexity: str, user_prompt: str) -> Dict:
        """
        Get optimal LLM parameters based on task complexity and user needs
        
        Args:
            complexity: Task complexity level ('simple', 'moderate', 'complex')
            user_prompt: User's custom prompt
            
        Returns:
            Dict with temperature, top_p, and max_tokens
        """
        # Base parameters
        params = {
            'simple': {
                'temperature': 0.5,  # More deterministic for simple tasks
                'top_p': 0.85,
                'max_tokens': 1500
            },
            'moderate': {
                'temperature': 0.7,  # Balanced creativity and focus
                'top_p': 0.9,
                'max_tokens': 2048
            },
            'complex': {
                'temperature': 0.8,  # More creative for complex scheduling
                'top_p': 0.95,
                'max_tokens': 2500
            }
        }

        # Check if user wants creativity vs strict adherence
        prompt_lower = user_prompt.lower()
        if any(word in prompt_lower for word in ['strict', 'exact', 'specific', 'must']):
            # User wants more precise output
            params[complexity]['temperature'] -= 0.1
        elif any(word in prompt_lower for word in ['flexible', 'creative', 'suggest', 'ideas']):
            # User wants more creative suggestions
            params[complexity]['temperature'] += 0.1

        # Smarter temperature control based on intent
        if "motivate" in user_prompt.lower():
            params[complexity]["temperature"] = 0.6
        if "explain" in user_prompt.lower():
            params[complexity]["temperature"] = 0.7

        # Clamp temperature between 0.3 and 0.9
        params[complexity]['temperature'] = max(0.3, min(0.9, params[complexity]['temperature']))

        return params[complexity]
    
    def _validate_and_score_schedule(self, schedule_data: Dict, user_profile: Dict, tasks: List[Dict]) -> Dict:
        """
        Validate schedule quality and add scoring metrics
        
        Args:
            schedule_data: Generated schedule
            user_profile: User profile data
            tasks: List of tasks
            
        Returns:
            Enhanced schedule with quality scores
        """
        if not schedule_data or 'schedule' not in schedule_data:
            return schedule_data
        
        schedule_items = schedule_data.get('schedule', [])
        
        # Extract profile data
        sleep_schedule = user_profile.get('sleep_schedule', {})
        if isinstance(sleep_schedule, str):
            import json
            sleep_schedule = json.loads(sleep_schedule)
        
        peak_energy = user_profile.get('peak_energy', 'morning')
        
        # Initialize scores
        scores = {
            'energy_alignment': 0,
            'task_coverage': 0,
            'work_life_balance': 0,
            'realism': 0,
            'time_management': 0
        }
        
        # 1. Energy Alignment Score (0-100)
        high_priority_count = 0
        high_priority_in_peak = 0
        
        for item in schedule_items:
            task_name = item.get('task', '').lower()
            time_str = item.get('time', '')
            
            # Check if high priority task
            is_high_priority = any(
                task.get('description', '').lower() in task_name and task.get('priority') == 'high'
                for task in tasks
            )
            
            if is_high_priority:
                high_priority_count += 1
                # Check if scheduled during peak energy
                if peak_energy in ['morning'] and ('AM' in time_str and not '12:' in time_str.split('-')[0]):
                    high_priority_in_peak += 1
                elif peak_energy in ['afternoon'] and ('PM' in time_str and any(h in time_str for h in ['12:', '1:', '2:', '3:', '4:'])):
                    high_priority_in_peak += 1
                elif peak_energy in ['evening'] and ('PM' in time_str and any(h in time_str for h in ['5:', '6:', '7:', '8:'])):
                    high_priority_in_peak += 1
        
        if high_priority_count > 0:
            scores['energy_alignment'] = int((high_priority_in_peak / high_priority_count) * 100)
        else:
            scores['energy_alignment'] = 100  # No high priority tasks
        
        # 2. Task Coverage Score (0-100)
        tasks_scheduled = 0
        for task in tasks:
            task_desc = task.get('description', '').lower()
            if any(task_desc in item.get('task', '').lower() for item in schedule_items):
                tasks_scheduled += 1
        
        if len(tasks) > 0:
            scores['task_coverage'] = int((tasks_scheduled / len(tasks)) * 100)
        else:
            scores['task_coverage'] = 100
        
        # 3. Work-Life Balance Score (0-100)
        work_time = 0
        break_time = 0
        personal_time = 0
        
        for item in schedule_items:
            item_type = item.get('type', '').lower()
            duration = self._estimate_duration(item.get('time', ''))
            
            if item_type in ['work', 'study', 'college/work']:
                work_time += duration
            elif item_type in ['break', 'personal', 'family', 'health']:
                personal_time += duration
                if item_type == 'break':
                    break_time += duration
        
        total_time = work_time + personal_time
        if total_time > 0:
            # Ideal ratio: 60-70% work, 30-40% personal
            work_ratio = work_time / total_time
            if 0.5 <= work_ratio <= 0.7:
                balance_score = 100
            elif work_ratio < 0.5:
                balance_score = 70 + (work_ratio * 60)
            else:
                balance_score = max(0, 100 - ((work_ratio - 0.7) * 200))
            
            # Bonus for breaks
            if break_time >= 60:  # At least 1 hour of breaks
                balance_score = min(100, balance_score + 10)
            
            scores['work_life_balance'] = int(balance_score)
        else:
            scores['work_life_balance'] = 50
        
        # 4. Realism Score (0-100)
        realism_score = 100
        
        # Check for overpacking (too many tasks in short time)
        total_scheduled_hours = sum(self._estimate_duration(item.get('time', '')) for item in schedule_items) / 60
        available_hours = 14  # Typical day
        
        if total_scheduled_hours > available_hours * 1.2:
            realism_score -= 30  # Overpacked
        elif total_scheduled_hours > available_hours:
            realism_score -= 15
        
        # Check for reasonable block lengths
        for item in schedule_items:
            duration = self._estimate_duration(item.get('time', ''))
            if duration > 180 and item.get('type') not in ['sleep', 'college', 'work']:  # More than 3 hours
                realism_score -= 5
        
        # Check for breaks
        if break_time < 30:
            realism_score -= 20  # Not enough breaks
        
        scores['realism'] = max(0, realism_score)
        
        # 5. Time Management Score (0-100)
        # Reward for: batching similar tasks, appropriate buffers, prioritization
        time_mgmt_score = 70  # Base score
        
        # Check for task batching
        task_types = [item.get('type', '') for item in schedule_items]
        if len(set(task_types)) < len(task_types) * 0.7:  # Some batching
            time_mgmt_score += 15
        
        # Check for buffer time
        if any('buffer' in item.get('task', '').lower() for item in schedule_items):
            time_mgmt_score += 15
        
        scores['time_management'] = min(100, time_mgmt_score)
        
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        # Add scores to schedule data
        if 'productivity_score' not in schedule_data:
            schedule_data['productivity_score'] = {}
        
        schedule_data['productivity_score'].update(scores)
        schedule_data['overall_quality'] = int(overall_score)
        
        # Add quality feedback
        feedback = []
        if scores['energy_alignment'] < 70:
            feedback.append("Consider scheduling more high-priority tasks during peak energy hours")
        if scores['task_coverage'] < 100:
            feedback.append(f"Missing {len(tasks) - tasks_scheduled} tasks from the schedule")
        if scores['work_life_balance'] < 60:
            feedback.append("Schedule may be unbalanced - add more breaks or personal time")
        if scores['realism'] < 70:
            feedback.append("Schedule might be too packed - consider reducing tasks or extending time")
        
        if feedback:
            schedule_data['improvement_suggestions'] = feedback
        
        return schedule_data
    
    def _estimate_duration(self, time_range: str) -> int:
        """
        Estimate duration in minutes from time range string
        
        Args:
            time_range: Time range like "9:00 AM - 11:00 AM"
            
        Returns:
            Duration in minutes
        """
        try:
            parts = time_range.split('-')
            if len(parts) != 2:
                return 60  # Default 1 hour
            
            start_str = parts[0].strip()
            end_str = parts[1].strip()
            
            # Simple parsing (can be enhanced)
            from datetime import datetime
            
            start = datetime.strptime(start_str, "%I:%M %p")
            end = datetime.strptime(end_str, "%I:%M %p")
            
            duration = (end - start).total_seconds() / 60
            return int(duration) if duration > 0 else 60
        except:
            return 60
    
    def generate_general_response(self, user_input: str, conversation_history: List[Dict] = None, user_profile: Dict = None, user_id: int = None, db_session = None) -> Optional[str]:
        """
        Generate a general response for conversation and assistance

        Args:
            user_input: The user's current input/request
            conversation_history: Previous conversation exchanges
            user_profile: User profile dict
            user_id: User ID for saving schedule
            db_session: Database session for saving

        Returns:
            str: Generated response (never None)
        """
        # Check for scheduling intent first (works even without Ollama)
        intent = detect_intent(user_input)
        if intent == "scheduling":
            # Generate and save schedule automatically
            if user_profile and user_id and db_session:
                try:
                    # Infer date from prompt
                    date_str = self._infer_date_from_prompt(user_input)
                    if not date_str:
                        from datetime import datetime
                        # Default to today
                        date_str = datetime.now().strftime("%Y-%m-%d")

                    # Get pending tasks
                    from models import Task
                    pending_tasks = Task.query.filter_by(user_id=user_id, status='pending').all()
                    tasks_data = [
                        {
                            'description': task.description,
                            'priority': task.priority,
                            'duration': task.duration,
                            'type': task.type,
                            'preferences': task.preferences
                        } for task in pending_tasks
                    ]

                    # Generate schedule (will use fallback if Ollama not available)
                    schedule_data = self.generate_schedule(user_profile, tasks_data, user_input)

                    if schedule_data:
                        # Save to database
                        from models import Schedule
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                        existing = Schedule.query.filter_by(user_id=user_id, date=date_obj).first()

                        if existing:
                            existing.schedule_data = schedule_data
                            db_session.commit()
                        else:
                            new_schedule = Schedule(user_id=user_id, date=date_obj, schedule_data=schedule_data)
                            db_session.add(new_schedule)
                            db_session.commit()

                        return f"✅ Schedule created successfully for {date_str}! Check your Schedule page to view and manage it. I've optimized it based on your profile and pending tasks."

                    else:
                        return "I tried to create your schedule but encountered an issue. Please use the Schedule section directly for the best results."

                except Exception as e:
                    print(f"Error auto-generating schedule: {e}")
                    return "I couldn't create the schedule automatically. Please try using the Schedule feature in the app."

            else:
                return "To create a schedule, please ensure your profile is complete and try using the Schedule section."

        if not self.check_llm_status():
            # Fallback for non-scheduling requests
            # Fallback for non-scheduling requests
            if intent == "motivation":
                return "Stay focused and keep pushing forward! You've got this."
            elif intent == "learning":
                return "Learning is a journey. Keep asking questions and exploring."
            else:
                return "I'm here to help! What would you like to know or discuss?"

        # Profile-awareness: inject profile and intent into prompt
        profile_text = ""
        if user_profile:
            profile_text = json.dumps(user_profile, indent=2)

        prompt = self.create_general_prompt(
            f"USER PROFILE:\n{profile_text}\n\nUSER INPUT:\n{user_input}",
            conversation_history
        )

        try:
            # Try Gemini first if available
            if self.use_gemini:
                try:
                    chat = self.gemini_model.start_chat(history=[])
                    response = chat.send_message(prompt)
                    
                    # Persist short memory hint
                    if user_profile is not None:
                        user_profile["last_intent"] = detect_intent(user_input)
                        user_profile["last_interaction"] = datetime.now().isoformat()
                        
                    return response.text.strip()
                except Exception as e:
                    print(f"Error with Gemini generation: {e}")
                    # Fallthrough to Ollama
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 150,
                    "repeat_penalty": 1.1,
                    "top_k": 40
                }
            }

            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=(5.0, 20.0)  # 5s connect, 20s read
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                # Persist short memory hint
                if user_profile is not None:
                    user_profile["last_intent"] = detect_intent(user_input)
                    user_profile["last_interaction"] = datetime.now().isoformat()
                return generated_text.strip()
            else:
                return None

        except Exception as e:
            print(f"Error generating general response with LLM: {str(e)}")
            # Fallback response
            intent = detect_intent(user_input)
            if intent == "scheduling":
                return "I'd be happy to help with scheduling! Please use the Schedule section to create your personalized schedule."
            elif intent == "motivation":
                return "Stay focused and keep pushing forward! You've got this."
            elif intent == "learning":
                return "Learning is a journey. Keep asking questions and exploring."
            else:
                return "I'm here to help! What would you like to know or discuss?"

    def _infer_date_from_prompt(self, prompt: str) -> Optional[str]:
        """Infer date from user prompt"""
        prompt_lower = prompt.lower()
        days = {
            'sunday': 6, 'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'today': None, 'tomorrow': None
        }

        from datetime import datetime, timedelta
        today = datetime.now()

        for day, offset in days.items():
            if day in prompt_lower:
                if day == 'today':
                    return today.strftime("%Y-%m-%d")
                elif day == 'tomorrow':
                    return (today + timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    # Find next occurrence of this day
                    current_weekday = today.weekday()
                    days_ahead = (offset - current_weekday) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # Next week if today
                    target_date = today + timedelta(days=days_ahead)
                    return target_date.strftime("%Y-%m-%d")

        return None
    
    def generate_schedule(self, user_profile: Dict, tasks: List[Dict], user_prompt: str = "") -> Optional[Dict]:
        """
        Generate an optimized schedule using ML model first, then LLM as fallback

        Args:
            user_profile: User profile information
            tasks: List of pending tasks
            user_prompt: Additional user context

        Returns:
            Dict containing the generated schedule or None if failed
        """
        # Try ML scheduler first
        if self.ml_scheduler and self.ml_scheduler.model:
            try:
                ml_schedule = self.ml_scheduler.generate_schedule(user_profile, tasks, user_prompt)
                if ml_schedule:
                    return ml_schedule
            except Exception as e:
                print(f"ML scheduler failed: {e}")

        # Fallback to LLM
        if not self.check_llm_status():
            return None
        
        # Calculate task complexity
        complexity = self._calculate_task_complexity(tasks)
        
        # Get optimal parameters based on complexity
        optimal_params = self._get_optimal_parameters(complexity, user_prompt)
        
        prompt = self.create_prompt(user_profile, tasks, user_prompt)
        
        try:
            # Try Gemini first if available
            if self.use_gemini:
                try:
                    # Enforce JSON structure for Gemini
                    gemini_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid, raw JSON. Do not include markdown formatting (like ```json ... ```) or any preamble."
                    
                    response = self.gemini_model.generate_content(gemini_prompt)
                    text = response.text.strip()
                    
                    # Clean markdown code blocks if present
                    if text.startswith("```"):
                        lines = text.split('\n')
                        if lines[0].strip().startswith("```"):
                            lines = lines[1:]
                        if lines[-1].strip().startswith("```"):
                            lines = lines[:-1]
                        text = "\n".join(lines)
                    
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        print(f"Failed to parse Gemini JSON: {text[:100]}...")
                        # Proceed to fallback or retry logic if we had it
                        return None
                        
                except Exception as e:
                    print(f"Error with Gemini schedule generation: {e}")
                    # Fallthrough to Ollama

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": optimal_params['temperature'],
                    "top_p": optimal_params['top_p'],
                    "max_tokens": optimal_params['max_tokens'],
                    "num_predict": optimal_params['max_tokens'],
                    "repeat_penalty": 1.1,  # Reduce repetition
                    "top_k": 40  # Limit token selection for consistency
                }
            }
            
            response = requests.post(
                self.api_endpoint,
                json=payload,
                timeout=(5.0, 20.0)  # 5s connect, 20s read
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                
                # Try to extract JSON from the response
                try:
                    # Find JSON object in the response
                    start_idx = generated_text.find('{')
                    end_idx = generated_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = generated_text[start_idx:end_idx]
                        schedule_data = json.loads(json_str)
                        
                        # Validate and score the schedule
                        schedule_data = self._validate_and_score_schedule(schedule_data, user_profile, tasks)
                        
                        return schedule_data
                    else:
                        # Fallback: create a basic structure
                        return self._create_fallback_response(generated_text)
                except json.JSONDecodeError:
                    return self._create_fallback_response(generated_text)
            else:
                return None
                
        except Exception as e:
            print(f"Error generating schedule with LLM: {str(e)}")
            return None
    
    def _create_fallback_response(self, text: str) -> Dict:
        """Create a fallback response when JSON parsing fails"""
        return {
            "schedule": [
                {
                    "time": "Generated by AI",
                    "task": text[:200] if text else "Schedule generation in progress",
                    "reason": "Please refer to the full AI response",
                    "type": "ai-generated"
                }
            ],
            "daily_summary": "AI-generated schedule (processing response)",
            "tips": ["Review the generated schedule", "Adjust as needed", "Stay flexible"]
        }


# Singleton instance
_llm_service = None

def get_llm_service() -> OllamaLLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = OllamaLLMService()
    return _llm_service
