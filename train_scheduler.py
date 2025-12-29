import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import joblib
from datetime import datetime

# Train an intelligent scheduling model

def load_data():
    """Load the generated dataset"""
    with open('user_profile.json', 'r') as f:
        profiles = json.load(f)

    with open('tasks.json', 'r') as f:
        tasks = json.load(f)

    with open('schedules.json', 'r') as f:
        schedules = json.load(f)

    return profiles, tasks, schedules

def prepare_training_data(profiles, tasks, schedules):
    """Prepare data for training - predict optimal time slot for tasks"""
    data = []

    # Create training examples from schedules
    for schedule in schedules:
        user_id = schedule['user_id']
        profile = next(p for p in profiles if p['id'] == user_id)
        schedule_items = schedule['schedule_data']['schedule']

        for item in schedule_items:
            if 'task' in item and item['task'] not in ['Morning routine & breakfast', 'Short break', 'Lunch break', 'Family time', 'Workout session', 'Review and plan tomorrow']:
                # Find corresponding task
                task_desc = item['task'].replace('Deep work: ', '')
                task = next((t for t in tasks if t['user_id'] == user_id and t['description'] in task_desc), None)

                if task:
                    time_str = item['time'].split(' - ')[0]
                    hour = int(time_str.split(':')[0])
                    if 'PM' in time_str and hour != 12:
                        hour += 12
                    elif 'AM' in time_str and hour == 12:
                        hour = 0

                    # Time slot categories
                    if 6 <= hour < 12:
                        time_slot = 'morning'
                    elif 12 <= hour < 17:
                        time_slot = 'afternoon'
                    elif 17 <= hour < 21:
                        time_slot = 'evening'
                    else:
                        time_slot = 'night'

                    data.append({
                        'role': profile['role'],
                        'peak_energy': profile['peak_energy'],
                        'study_preference': profile['study_preference'],
                        'workout_preference': profile['workout_preference'],
                        'workout_impact': profile['workout_impact'],
                        'task_priority': task['priority'],
                        'task_type': task['type'],
                        'task_duration': task['duration'],
                        'time_slot': time_slot,
                        'flexibility': item.get('flexibility', 'flexible')
                    })

    return pd.DataFrame(data)

def train_model(df):
    """Train a model to predict optimal time slots"""
    # Encode categorical variables
    encoders = {}
    for col in ['role', 'peak_energy', 'study_preference', 'workout_preference', 'workout_impact', 'task_priority', 'task_type', 'task_duration', 'flexibility']:
        encoders[col] = LabelEncoder()
        df[col] = encoders[col].fit_transform(df[col])

    # Features and target
    X = df.drop('time_slot', axis=1)
    y = df['time_slot']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy:.2f}")

    return model, encoders

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

        return {
            "schedule": schedule_items,
            "daily_summary": f"AI-optimized schedule for {profile.get('role', 'student')} with {len(tasks)} tasks, aligned to your {profile.get('peak_energy', 'morning')} energy pattern.",
            "tips": [
                "Focus high-priority tasks during your peak energy time",
                "Take short breaks between tasks to maintain productivity",
                "Adjust schedule as needed while maintaining work-life balance"
            ]
        }

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

def create_scheduler_class(model, encoders):
    """Create a Scheduler instance"""
    return IntelligentScheduler(model, encoders)

def main():
    print("Loading data...")
    profiles, tasks, schedules = load_data()

    print("Preparing training data...")
    df = prepare_training_data(profiles, tasks, schedules)
    print(f"Training samples: {len(df)}")

    print("Training model...")
    model, encoders = train_model(df)

    print("Creating scheduler...")
    scheduler = create_scheduler_class(model, encoders)

    # Save model
    joblib.dump({'model': model, 'encoders': encoders}, 'intelligent_scheduler.pkl')

    print("Model trained and saved!")

    # Test with sample
    sample_profile = profiles[0]
    sample_tasks = [t for t in tasks if t['user_id'] == sample_profile['id']][:3]

    schedule = scheduler.generate_schedule(sample_profile, sample_tasks)
    print("\nSample Schedule Generated:")
    for item in schedule['schedule'][:3]:
        print(f"- {item['time']}: {item['task']}")

if __name__ == "__main__":
    main()