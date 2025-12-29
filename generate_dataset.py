import json
import random
from datetime import datetime, timedelta

# Generate synthetic dataset for training the scheduling model

def generate_user_profiles(num_profiles=150):
    """Generate student-focused user profiles"""
    roles = ["Student (Engineering)", "Student (Computer Science)", "Student (Business)", "Student (Medical)", "Student (Arts)"]
    peak_energies = ["morning", "afternoon", "evening"]
    study_preferences = ["deep work", "flexible"]
    workout_preferences = ["morning", "evening", "flexible"]
    workout_impacts = ["energized", "tired", "neutral"]
    main_goals = [
        "Improve grades and academic performance",
        "Build technical skills for career",
        "Balance studies with health and social life",
        "Complete projects on time",
        "Develop leadership and communication skills"
    ]

    profiles = []
    for i in range(num_profiles):
        wake_hour = random.randint(6, 9)
        bed_hour = random.randint(22, 24)
        wake_time = f"{wake_hour}:00 AM" if wake_hour < 12 else f"{wake_hour-12}:00 PM"
        bed_time = f"{bed_hour-12}:00 PM" if bed_hour < 24 else "12:00 AM"

        profile = {
            "id": i+1,
            "name": f"Student_{i+1}",
            "role": random.choice(roles),
            "schedule_days": random.randint(5, 7),
            "peak_energy": random.choice(peak_energies),
            "study_preference": random.choice(study_preferences),
            "family_time": f"{random.randint(18,20)}:00 PM - {random.randint(19,21)}:00 PM",
            "workout_preference": random.choice(workout_preferences),
            "workout_impact": random.choice(workout_impacts),
            "main_goals": random.choice(main_goals),
            "sleep_schedule": {
                "wake_time": wake_time,
                "bedtime": bed_time
            },
            "weekly_schedule": {
                "Monday": {"start": "9:00 AM", "end": "5:00 PM"},
                "Tuesday": {"start": "9:00 AM", "end": "5:00 PM"},
                "Wednesday": {"start": "9:00 AM", "end": "5:00 PM"},
                "Thursday": {"start": "9:00 AM", "end": "5:00 PM"},
                "Friday": {"start": "9:00 AM", "end": "5:00 PM"},
                "Saturday": {"start": "10:00 AM", "end": "2:00 PM"},
                "Sunday": {"start": "None", "end": "None"}
            }
        }
        profiles.append(profile)
    return profiles

def generate_tasks(num_tasks=600):
    """Generate tasks with priorities, deadlines, durations, types"""
    descriptions = [
        "Complete math assignment", "Study for physics exam", "Write code for project",
        "Review lecture notes", "Prepare presentation", "Debug software bug",
        "Read research paper", "Practice coding problems", "Group study session",
        "Health checkup", "Gym workout", "Meal prep", "Family call",
        "Personal project", "Skill development", "Revision session"
    ]
    priorities = ["High", "Medium", "Low"]
    durations = ["30 min", "1 hour", "1.5 hours", "2 hours", "3 hours"]
    types = ["Study", "Coding", "Revision", "Health", "Personal", "College"]

    tasks = []
    for i in range(num_tasks):
        deadline = datetime.now() + timedelta(days=random.randint(1, 14))
        task = {
            "id": i+1,
            "user_id": random.randint(1, 150),
            "description": random.choice(descriptions),
            "priority": random.choice(priorities),
            "duration": random.choice(durations),
            "type": random.choice(types),
            "deadline": deadline.strftime("%Y-%m-%d"),
            "preferences": random.choice(["Morning focus", "Afternoon session", "Evening work", "Flexible"])
        }
        tasks.append(task)
    return tasks

def generate_schedules(profiles, tasks, num_schedules=300):
    """Generate example schedules based on profiles and tasks"""
    schedules = []

    for i in range(num_schedules):
        user_id = random.randint(1, 150)
        profile = next(p for p in profiles if p["id"] == user_id)
        user_tasks = [t for t in tasks if t["user_id"] == user_id][:random.randint(3, 8)]

        # Generate schedule items
        schedule_items = []
        wake_time = profile["sleep_schedule"]["wake_time"]
        bed_time = profile["sleep_schedule"]["bedtime"]

        # Morning routine
        schedule_items.append({
            "time": f"{wake_time} - {add_time(wake_time, 30)}",
            "task": "Morning routine & breakfast",
            "reason": "Start day energized",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        # High energy block
        peak = profile["peak_energy"]
        if peak == "morning":
            start = add_time(wake_time, 60)
        elif peak == "afternoon":
            start = "1:00 PM"
        else:
            start = "7:00 PM"

        high_task = next((t for t in user_tasks if t["priority"] == "High"), user_tasks[0] if user_tasks else {"description": "Study session"})
        schedule_items.append({
            "time": f"{start} - {add_time(start, 120)}",
            "task": f"Deep work: {high_task['description'] if isinstance(high_task, dict) else high_task}",
            "reason": f"Peak energy time for {peak} focus",
            "type": "study",
            "priority": "high",
            "flexibility": "semi-flexible"
        })

        # Break
        break_start = add_time(start, 135)
        schedule_items.append({
            "time": f"{break_start} - {add_time(break_start, 15)}",
            "task": "Short break",
            "reason": "Reset and recharge",
            "type": "break",
            "priority": "medium",
            "flexibility": "flexible"
        })

        # More tasks
        for j, task in enumerate(user_tasks[1:3]):
            task_start = add_time(break_start, 15 + j*90)
            schedule_items.append({
                "time": f"{task_start} - {add_time(task_start, 90)}",
                "task": task["description"],
                "reason": f"Continue with {task['priority'].lower()} priority task",
                "type": task["type"].lower(),
                "priority": task["priority"].lower(),
                "flexibility": "flexible"
            })

        # Lunch
        schedule_items.append({
            "time": "12:00 PM - 1:00 PM",
            "task": "Lunch break",
            "reason": "Nutrition and rest",
            "type": "personal",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Family time
        family = profile["family_time"]
        schedule_items.append({
            "time": family,
            "task": "Family time",
            "reason": "Personal balance",
            "type": "family",
            "priority": "high",
            "flexibility": "fixed"
        })

        # Workout
        workout_pref = profile["workout_preference"]
        workout_time = "6:00 PM - 7:00 PM" if workout_pref == "evening" else "7:00 AM - 8:00 AM"
        schedule_items.append({
            "time": workout_time,
            "task": "Workout session",
            "reason": f"{workout_pref} workout",
            "type": "health",
            "priority": "medium",
            "flexibility": "semi-flexible"
        })

        # Evening review
        review_start = subtract_time(bed_time, 60)
        schedule_items.append({
            "time": f"{review_start} - {bed_time}",
            "task": "Review and plan tomorrow",
            "reason": "Reflect and prepare",
            "type": "personal",
            "priority": "medium",
            "flexibility": "fixed"
        })

        schedule = {
            "id": i+1,
            "user_id": user_id,
            "date": (datetime.now() + timedelta(days=random.randint(0,7))).strftime("%Y-%m-%d"),
            "schedule_data": {
                "schedule": schedule_items,
                "daily_summary": f"Optimized for {profile['role']} with {len(user_tasks)} tasks, focusing on {profile['peak_energy']} energy.",
                "tips": [
                    "Use Pomodoro for deep work",
                    "Stay hydrated",
                    "Take regular breaks"
                ]
            }
        }
        schedules.append(schedule)

    return schedules

def add_time(time_str, minutes):
    """Add minutes to time string"""
    from datetime import datetime
    try:
        dt = datetime.strptime(time_str, "%I:%M %p")
        dt = dt + timedelta(minutes=minutes)
        return dt.strftime("%I:%M %p").lstrip('0')
    except:
        return time_str

def subtract_time(time_str, minutes):
    """Subtract minutes from time string"""
    from datetime import datetime
    try:
        dt = datetime.strptime(time_str, "%I:%M %p")
        dt = dt - timedelta(minutes=minutes)
        return dt.strftime("%I:%M %p").lstrip('0')
    except:
        return time_str

if __name__ == "__main__":
    print("Generating dataset...")

    profiles = generate_user_profiles(150)
    with open("user_profile.json", "w") as f:
        json.dump(profiles, f, indent=2)

    tasks = generate_tasks(600)
    with open("tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

    schedules = generate_schedules(profiles, tasks, 300)
    with open("schedules.json", "w") as f:
        json.dump(schedules, f, indent=2)

    print("Dataset generated successfully!")
    print(f"Profiles: {len(profiles)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Schedules: {len(schedules)}")