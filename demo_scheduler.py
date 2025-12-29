import json
import joblib
import pandas as pd
from datetime import datetime, timedelta

# Demo of the trained Intelligent Scheduling Assistant

class IntelligentScheduler:
    """Intelligent Scheduler class that uses the trained model"""

    def __init__(self, model, encoders):
        self.model = model
        self.encoders = encoders

    def predict_time_slot(self, profile, task):
        """Predict best time slot for a task"""
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

    def generate_schedule(self, profile, tasks, prompt=""):
        """Generate a full schedule using the model"""
        # Parse prompt for adjustments
        prompt_lower = prompt.lower()
        wants_morning = "morning" in prompt_lower
        wants_afternoon = "afternoon" in prompt_lower
        wants_evening = "evening" in prompt_lower

        schedule_items = []

        # Fixed items
        wake_time = profile.get('sleep_schedule', {}).get('wake_time', '7:00 AM')
        bed_time = profile.get('sleep_schedule', {}).get('bedtime', '11:00 PM')

        schedule_items.append({
            "time": f"{wake_time} - {self.add_time(wake_time, 30)}",
            "task": "Morning routine & breakfast",
            "reason": "Gentle start to energize your day",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Schedule tasks using model predictions
        current_time = self.add_time(wake_time, 60)  # Start after morning routine

        for task in tasks[:5]:  # Limit to 5 tasks
            predicted_slot = self.predict_time_slot(profile, task)

            # Adjust based on prompt
            if wants_morning and predicted_slot != 'morning':
                predicted_slot = 'morning'
            elif wants_afternoon and predicted_slot != 'afternoon':
                predicted_slot = 'afternoon'
            elif wants_evening and predicted_slot != 'evening':
                predicted_slot = 'evening'

            # Map to actual time
            if predicted_slot == 'morning':
                slot_start = current_time if current_time.endswith('AM') else '9:00 AM'
            elif predicted_slot == 'afternoon':
                slot_start = '1:00 PM'
            elif predicted_slot == 'evening':
                slot_start = '6:00 PM'
            else:
                slot_start = '8:00 PM'

            duration = task.get('duration', '1 hour')
            dur_minutes = self.parse_duration(duration)
            end_time = self.add_time(slot_start, dur_minutes)

            schedule_items.append({
                "time": f"{slot_start} - {end_time}",
                "task": task['description'],
                "reason": f"Scheduled in {predicted_slot} based on your energy pattern and task requirements",
                "type": task['type'].lower(),
                "priority": task['priority'].lower(),
                "flexibility": "semi-flexible"
            })

            current_time = self.add_time(end_time, 15)  # Buffer

        # Add breaks and fixed items
        schedule_items.append({
            "time": "12:00 PM - 1:00 PM",
            "task": "Lunch break",
            "reason": "Nutrition and rest",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        family_time = profile.get('family_time', '6:00 PM - 7:00 PM')
        schedule_items.append({
            "time": family_time,
            "task": "Family time",
            "reason": "Personal balance",
            "type": "family",
            "priority": "high",
            "flexibility": "fixed"
        })

        workout_time = "7:00 PM - 8:00 PM"
        schedule_items.append({
            "time": workout_time,
            "task": "Workout session",
            "reason": f"{profile.get('workout_preference', 'evening')} workout",
            "type": "health",
            "priority": "medium",
            "flexibility": "semi-flexible"
        })

        review_start = self.subtract_time(bed_time, 60)
        schedule_items.append({
            "time": f"{review_start} - {bed_time}",
            "task": "Review and plan tomorrow",
            "reason": "Reflect and prepare",
            "type": "personal",
            "priority": "medium",
            "flexibility": "fixed"
        })

        return schedule_items

    def add_time(self, time_str, minutes):
        """Add minutes to time"""
        try:
            from datetime import datetime, timedelta
            dt = datetime.strptime(time_str, "%I:%M %p")
            dt = dt + timedelta(minutes=minutes)
            return dt.strftime("%I:%M %p").lstrip('0')
        except:
            return time_str

    def subtract_time(self, time_str, minutes):
        """Subtract minutes from time"""
        try:
            from datetime import datetime, timedelta
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

def load_demo_data():
    """Load sample data for demo"""
    with open('user_profile.json', 'r') as f:
        profiles = json.load(f)

    with open('tasks.json', 'r') as f:
        tasks = json.load(f)

    return profiles[0], [t for t in tasks if t['user_id'] == 1][:3]

def demo_assistant():
    """Demonstrate the AI scheduling assistant"""
    print("🤖 AI-Powered Scheduling Assistant")
    print("=" * 50)

    # Load model
    data = joblib.load('intelligent_scheduler.pkl')
    model = data['model']
    encoders = data['encoders']
    scheduler = IntelligentScheduler(model, encoders)

    # Load sample user data
    profile, tasks = load_demo_data()

    print("📋 User Profile:")
    print(f"Role: {profile['role']}")
    print(f"Peak Energy: {profile['peak_energy']}")
    print(f"Goals: {profile['main_goals']}")
    print(f"Wake Time: {profile['sleep_schedule']['wake_time']}")
    print()

    print("📝 Pending Tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task['description']} (Priority: {task['priority']}, Duration: {task['duration']})")
    print()

    # Simulate user commands
    commands = [
        "make me productive today",
        "focus on morning work",
        "prioritize the high priority tasks",
        "i need evening study time"
    ]

    for cmd in commands:
        print(f"👤 User: {cmd}")
        schedule = scheduler.generate_schedule(profile, tasks, cmd)

        print("📅 Generated Schedule:")
        print("Task Name | Time Slot | Priority | Reason | Flexibility")
        print("-" * 60)

        for item in schedule:
            task_name = item['task'][:30]  # Truncate long names
            time_slot = item['time']
            priority = item.get('priority', 'medium').capitalize()
            reason = item['reason'][:40]  # Truncate
            flexibility = item.get('flexibility', 'flexible').capitalize()

            print(f"{task_name:<15} | {time_slot:<12} | {priority:<8} | {reason:<20} | {flexibility}")
        print()

if __name__ == "__main__":
    demo_assistant()