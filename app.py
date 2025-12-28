from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import os
import logging
from datetime import datetime, timedelta

from llm_service import get_llm_service
from analytics_service import AnalyticsService
from models import db, User, Task, Schedule, ScheduleFeedback, ChatMessage, LoginHistory, Notification
from forms import LoginForm, RegistrationForm, ProfileForm, TaskForm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Use environment variable for secret key or fallback to a stable dev key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-prod')

# Database configuration
if os.environ.get('VERCEL'):
    # Vercel filesystem is read-only, so we use /tmp for SQLite
    # NOTE: Data will be lost on every redeploy/restart!
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/task_optimizer.db'
else:
    # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_optimizer.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

# Serve favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'templates', 'image'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')


# Helper function to get today's date
def get_today():
    return datetime.now().strftime("%Y-%m-%d")

# Helper methods for time calculations
def add_time(time_str, minutes):
    """Add minutes to time string and return new time string"""
    try:
        # Parse time string (e.g., "7:00 AM")
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
        else:
            time_obj = datetime.strptime(time_str.strip(), "%H:%M")
        
        # Add minutes
        new_time = time_obj + timedelta(minutes=minutes)
        
        # Return in same format
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            return new_time.strftime("%I:%M %p").lstrip('0')
        else:
            return new_time.strftime("%H:%M")
    except:
        # Fallback to simple addition if parsing fails
        return time_str

def subtract_time(time_str, minutes):
    """Subtract minutes from time string and return new time string"""
    try:
        # Parse time string (e.g., "7:00 AM")
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            time_obj = datetime.strptime(time_str.strip(), "%I:%M %p")
        else:
            time_obj = datetime.strptime(time_str.strip(), "%H:%M")
        
        # Subtract minutes
        new_time = time_obj - timedelta(minutes=minutes)
        
        # Return in same format
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            result = new_time.strftime("%I:%M %p").lstrip('0')
            # Fix formatting issue with single digit hours
            if result.startswith(':'):
                result = '12' + result
            return result
        else:
            return new_time.strftime("%H:%M")
    except:
        # Fallback to simple subtraction if parsing fails
        return time_str

def parse_time_str(time_str):
    try:
        if "AM" in time_str.upper() or "PM" in time_str.upper():
            return datetime.strptime(time_str.strip(), "%I:%M %p")
        return datetime.strptime(time_str.strip(), "%H:%M")
    except:
        return datetime.strptime("7:00 AM", "%I:%M %p")

@app.before_request
def update_login_streak():
    """Update login streak for specific routes if user is authenticated"""
    # List of routes that should count as a "daily visit"
    # Exempt static files and API calls that happen automatically
    exempt_prefixes = ['/static', '/api/calendar-data', '/api/chat/history', '/favicon.ico']
    
    if request.path.startswith('/static') or request.path == '/favicon.ico':
        return
        
    if current_user.is_authenticated:
        # Only update if accessing a page, not just a background API call
        # But for now, let's just update on any non-static request to be safe
        current_user.add_login_date()

# Routes for authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if user:  # After successful authentication
        user.add_login_date()  # Add this line
        login_user(user, remember=form.remember.data)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                # Check if banned
                if user.is_banned:
                    if user.banned_until and user.banned_until > datetime.utcnow():
                        flash(f'Your account has been suspended until {user.banned_until.strftime("%Y-%m-%d %H:%M")}.')
                        return render_template('login.html', form=form)
                    elif user.banned_until and user.banned_until <= datetime.utcnow():
                         # Ban expired
                         user.is_banned = False
                         user.banned_until = None
                         db.session.commit()
                    elif user.is_banned:
                        flash('Your account has been permanently suspended.')
                        return render_template('login.html', form=form)

                login_user(user, remember=form.remember_me.data)
                
                # Record login history
                login_record = LoginHistory(user_id=user.id)
                db.session.add(login_record)
                db.session.commit()
                
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
        except Exception as e:
            flash('An error occurred during login. Please try again.')
            logger.error(f"Login error: {e}")
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            # Check if it's a duplicate entry error
            if 'UNIQUE constraint failed' in str(e) or 'duplicate' in str(e).lower():
                flash('Username or email already exists. Please choose different credentials.')
            else:
                flash('An error occurred during registration. Please try again.')
            logger.error(f"Registration error: {e}")
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# Routes for the web application
@app.route('/')
@login_required
def index():
    # Redirect admin to admin dashboard
    if current_user.is_admin:
        return redirect(url_for('admin'))
        
    # Get user's tasks
    pending_tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status='completed').all()
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    
    tasks_data = {
        'pending': pending_tasks,
        'completed': completed_tasks,
        'schedules': {str(schedule.date): schedule.schedule_data for schedule in schedules}
    }
    
    # Analytics
    analytics = AnalyticsService()
    # login_chart = analytics.generate_login_chart(current_user.id)
    # task_chart = analytics.generate_task_chart(current_user.id)
    # completion_score = analytics.predict_completion_probability(current_user.id)
    login_streak = analytics.calculate_login_streak(current_user.id)
    
    return render_template('index.html', profile=current_user, tasks=tasks_data, 
                         login_streak=login_streak)

@app.route('/profile')
@login_required
def profile():
    # Convert user object to dictionary for JSON serialization
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'name': current_user.name,
        'role': current_user.role,
        'schedule_days': current_user.schedule_days,
        'peak_energy': current_user.peak_energy,
        'study_preference': current_user.study_preference,
        'family_time': current_user.family_time,
        'workout_preference': current_user.workout_preference,
        'workout_impact': current_user.workout_impact,
        'main_goals': current_user.main_goals,
        'sleep_schedule': current_user.sleep_schedule,
        'weekly_schedule': current_user.weekly_schedule,
        'is_admin': current_user.is_admin,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None
    }
    return render_template('profile.html', profile=user_data)

@app.route('/tasks')
@login_required
def tasks():
    pending_tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status='completed').all()
    
    tasks_data = {
        'pending': pending_tasks,
        'completed': completed_tasks,
        'schedules': {}
    }
    
    return render_template('tasks.html', tasks=tasks_data)

@app.route('/schedule')
@login_required
def schedule():
    today = get_today()
    schedules = Schedule.query.filter_by(user_id=current_user.id).all()
    
    tasks_data = {
        'pending': [],
        'completed': [],
        'schedules': {str(schedule.date): schedule.schedule_data for schedule in schedules}
    }
    
    return render_template('schedule.html', tasks=tasks_data, today=today)

# API routes for profile
@app.route('/api/profile', methods=['GET', 'POST'])
@login_required
def api_profile():
    if request.method == 'POST':
        data = request.json
        
        # Update user profile
        current_user.name = data.get('name', current_user.name)
        current_user.role = data.get('role', current_user.role)
        current_user.schedule_days = data.get('schedule_days', current_user.schedule_days)
        current_user.peak_energy = data.get('peak_energy', current_user.peak_energy)
        current_user.study_preference = data.get('study_preference', current_user.study_preference)
        current_user.family_time = data.get('family_time', current_user.family_time)
        current_user.workout_preference = data.get('workout_preference', current_user.workout_preference)
        current_user.workout_impact = data.get('workout_impact', current_user.workout_impact)
        current_user.main_goals = data.get('main_goals', current_user.main_goals)
        current_user.sleep_schedule = data.get('sleep_schedule', current_user.sleep_schedule)
        current_user.weekly_schedule = data.get('weekly_schedule', current_user.weekly_schedule)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Profile updated"})
    
    # Return current user profile
    profile_data = {
        'name': current_user.name,
        'role': current_user.role,
        'schedule_days': current_user.schedule_days,
        'peak_energy': current_user.peak_energy,
        'study_preference': current_user.study_preference,
        'family_time': current_user.family_time,
        'workout_preference': current_user.workout_preference,
        'workout_impact': current_user.workout_impact,
        'main_goals': current_user.main_goals,
        'sleep_schedule': current_user.sleep_schedule,
        'weekly_schedule': current_user.weekly_schedule
    }
    
    return jsonify(profile_data)

# API routes for tasks
@app.route('/api/tasks', methods=['GET', 'POST'])
@login_required
def api_tasks():
    if request.method == 'POST':
        data = request.json
        if data.get('action') == 'add':
            task = Task(
                user_id=current_user.id,
                description=data.get('description'),
                priority=data.get('priority'),
                duration=data.get('duration'),
                type=data.get('type'),
                preferences=data.get('preferences'),
                status='pending'
            )
            db.session.add(task)
            db.session.commit()
            return jsonify({"status": "success", "message": "Task added"})
        elif data.get('action') == 'complete':
            task_id = data.get('id')
            task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
            if task:
                task.status = 'completed'
                task.completed_date = datetime.now()
                db.session.commit()
                return jsonify({"status": "success", "message": "Task completed"})
            return jsonify({"status": "error", "message": "Task not found"}), 404
        elif data.get('action') == 'delete':
            task_id = data.get('id')
            task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
            if task:
                db.session.delete(task)
                db.session.commit()
                return jsonify({"status": "success", "message": "Task deleted"})
            return jsonify({"status": "error", "message": "Task not found"}), 404
    else:
        # Get user's tasks
        pending_tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
        completed_tasks = Task.query.filter_by(user_id=current_user.id, status='completed').all()
        
        tasks_data = {
            'pending': [
                {
                    'id': task.id,
                    'description': task.description,
                    'priority': task.priority,
                    'duration': task.duration,
                    'type': task.type,
                    'preferences': task.preferences,
                    'status': task.status,
                    'added_date': task.added_date.strftime("%Y-%m-%d") if task.added_date else None
                } for task in pending_tasks
            ],
            'completed': [
                {
                    'id': task.id,
                    'description': task.description,
                    'type': task.type,
                    'completed_date': task.completed_date.strftime("%Y-%m-%d") if task.completed_date else None
                } for task in completed_tasks
            ]
        }
        
        return jsonify(tasks_data)

# AI optimize
@app.route('/api/ai_optimize', methods=['POST'])
@login_required
def api_ai_optimize():
    try:
        data = request.json or {}
        prompt = data.get('prompt', '').strip()
        date_str = data.get('date', get_today())

        # Check for pending tasks
        pending_tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
        # Allow optimization even without tasks (will use generic slots)

        # Get LLM service
        llm_service = get_llm_service()
        
        # Check if Ollama is available
        if llm_service.check_ollama_status():
            # Prepare user profile data
            user_profile = {
                'name': current_user.name,
                'role': current_user.role,
                'main_goals': current_user.main_goals,
                'peak_energy': current_user.peak_energy,
                'study_preference': current_user.study_preference,
                'workout_preference': current_user.workout_preference,
                'workout_impact': current_user.workout_impact,
                'family_time': current_user.family_time,
                'sleep_schedule': current_user.sleep_schedule,
                'weekly_schedule': current_user.weekly_schedule
            }
            
            # Prepare tasks data
            tasks_data = [
                {
                    'description': task.description,
                    'priority': task.priority,
                    'duration': task.duration,
                    'type': task.type,
                    'preferences': task.preferences
                } for task in pending_tasks
            ]
            
            # Generate schedule using LLM
            schedule_data = llm_service.generate_schedule(user_profile, tasks_data, prompt)
            
            if schedule_data:
                # Save schedule to database
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                existing = Schedule.query.filter_by(user_id=current_user.id, date=date_obj).first()
                
                if existing:
                    existing.schedule_data = schedule_data
                    db.session.commit()
                else:
                    new_schedule = Schedule(user_id=current_user.id, date=date_obj, schedule_data=schedule_data)
                    db.session.add(new_schedule)
                    db.session.commit()
                
                return jsonify({"status": "success", "date": date_str, "schedule": schedule_data, "source": "llm"})
        
        # Fallback to rule-based optimization if LLM is not available
        return _fallback_optimize(current_user, pending_tasks, prompt, date_str)
        
    except Exception as e:
        return jsonify({"error": "server_error", "message": f"Failed to optimize: {str(e)}"}), 500

# General AI chat
@app.route('/api/ai_chat', methods=['POST'])
@login_required
def api_ai_chat():
    try:
        data = request.json or {}
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "message_required", "message": "Message is required"}), 400

        # Get LLM service
        llm_service = get_llm_service()
        
        # Check if Ollama is available
        if llm_service.check_ollama_status():
            # Save user message
            user_msg = ChatMessage(user_id=current_user.id, role='user', content=user_message)
            db.session.add(user_msg)
            db.session.commit()
            
            # Get recent history
            history = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
            history.reverse() # Oldest first
            
            conversation_history = []
            current_exchange = {}
            for msg in history:
                if msg.role == 'user':
                    current_exchange['user'] = msg.content
                elif msg.role == 'assistant':
                    current_exchange['assistant'] = msg.content
                    if 'user' in current_exchange:
                        conversation_history.append(current_exchange)
                        current_exchange = {}
            
            # Generate response using LLM
            user_profile = {
                'name': current_user.name,
                'role': current_user.role,
                'main_goals': current_user.main_goals,
                'peak_energy': current_user.peak_energy,
                'study_preference': current_user.study_preference,
            }
            response = llm_service.generate_general_response(
                user_message,
                conversation_history,
                user_profile
            )
            
            if response:
                # Save AI response
                ai_msg = ChatMessage(user_id=current_user.id, role='assistant', content=response)
                db.session.add(ai_msg)
                db.session.commit()
                
                return jsonify({"status": "success", "response": response})
        
        # Fallback response if LLM is not available
        return jsonify({
            "status": "fallback",
            "response": "I'm currently unable to access the AI service. Please try again later or use the scheduling feature which can work without AI assistance."
        })
        
    except Exception as e:
        return jsonify({"error": "server_error", "message": f"Failed to process message: {str(e)}"}), 500

@app.route('/api/chat/history', methods=['GET'])
@login_required
def api_get_chat_history():
    """Get chat history for the current user"""
    try:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.timestamp.asc()).all()
        return jsonify({
            "status": "success",
            "messages": [msg.to_dict() for msg in messages]
        })
    except Exception as e:
        return jsonify({"error": "server_error", "message": str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def api_clear_chat():
    """Clear chat history for the current user"""
    try:
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"status": "success", "message": "Chat history cleared"})
    except Exception as e:
        return jsonify({"error": "server_error", "message": str(e)}), 500

def _fallback_optimize(user, pending_tasks, prompt, date_str):
    """Fallback rule-based optimization when LLM is unavailable"""
    try:
        sleep_schedule = json.loads(user.sleep_schedule) if isinstance(user.sleep_schedule, str) else (user.sleep_schedule or {})
    except Exception:
        sleep_schedule = {}
    wake_time = (sleep_schedule or {}).get('wake_time', '7:00 AM')
    bedtime = (sleep_schedule or {}).get('bedtime', '11:00 PM')

    # Simple prompt parsing to adjust blocks
    p = prompt.lower()
    wants_morning_focus = "morning" in p and ("focus" in p or "deep" in p)

    schedule_items = []

    def fmt(dt):
        return dt.strftime("%I:%M %p").lstrip('0')

    wake_dt = parse_time_str(wake_time)
    cursor = wake_dt

    morning_end_dt = cursor + timedelta(minutes=30)
    schedule_items.append({"time": f"{fmt(cursor)} - {fmt(morning_end_dt)}", "task": "Morning routine & light stretching", "reason": "Gentle start", "type": "health"})
    cursor = morning_end_dt

    he_target = wake_dt + timedelta(minutes=(60 if wants_morning_focus else 90))
    he_start_dt = max(cursor, he_target)
    he_end_dt = he_start_dt + timedelta(minutes=120)

    task_desc = pending_tasks[0].description if pending_tasks else "Focus on key objectives"
    task_type = pending_tasks[0].type if pending_tasks else "work"
    schedule_items.append({"time": f"{fmt(he_start_dt)} - {fmt(he_end_dt)}", "task": f"Deep work - {task_desc}", "reason": "High-energy block aligned to your prompt", "type": task_type})
    cursor = he_end_dt

    break_start_dt = cursor + timedelta(minutes=15)
    break_end_dt = break_start_dt + timedelta(minutes=15)
    schedule_items.append({"time": f"{fmt(break_start_dt)} - {fmt(break_end_dt)}", "task": "Break", "reason": "Short reset", "type": "break"})
    cursor = break_end_dt
    work_start_dt = cursor + timedelta(minutes=15)
    work_end_dt = work_start_dt + timedelta(minutes=90)
    
    if len(pending_tasks) > 1:
        task2 = f"Project work - {pending_tasks[1].description}"
        type2 = pending_tasks[1].type
    elif pending_tasks:
        task2 = "Review and refine work"
        type2 = "work"
    else:
        task2 = "Project work - Advance your goals"
        type2 = "work"
        
    schedule_items.append({"time": f"{fmt(work_start_dt)} - {fmt(work_end_dt)}", "task": task2, "reason": "Continued focus", "type": type2})
    cursor = work_end_dt

    lunch_start_dt = cursor + timedelta(minutes=60)
    lunch_end_dt = lunch_start_dt + timedelta(minutes=60)
    schedule_items.append({"time": f"{fmt(lunch_start_dt)} - {fmt(lunch_end_dt)}", "task": "Lunch break", "reason": "Nourishment", "type": "personal"})
    cursor = lunch_end_dt

    afternoon_start_dt = cursor + timedelta(minutes=60)
    afternoon_end_dt = afternoon_start_dt + timedelta(minutes=90)
    schedule_items.append({"time": f"{fmt(afternoon_start_dt)} - {fmt(afternoon_end_dt)}", "task": "Task review & planning", "reason": "Aligned with prompt", "type": "work"})
    cursor = afternoon_end_dt

    # Family
    family_time = user.family_time or "6:00 PM - 7:00 PM"
    schedule_items.append({"time": family_time, "task": "Family time", "reason": "Preferences", "type": "family"})

    # Workout
    workout_pref = (user.workout_preference or "evening").lower()
    workout_time = "7:00 PM - 8:00 PM"
    if "morning" in workout_pref:
        workout_time = f"{add_time(wake_time, 30)} - {add_time(wake_time, 90)}"
    schedule_items.append({"time": workout_time, "task": "Workout session", "reason": f"{workout_pref.title()} workout", "type": "health"})

    # Evening review
    review_time_start = subtract_time(bedtime, 60)
    schedule_items.append({"time": f"{review_time_start} - {bedtime}", "task": "Review and plan for tomorrow", "reason": "Reflect and prepare", "type": "personal"})

    schedule_data = {
        "schedule": schedule_items,
        "daily_summary": f"Optimized using profile and {len(pending_tasks)} tasks. Prompt: {prompt}",
        "tips": [
            "Use high-energy blocks for deep work",
            "Take short breaks every hour",
            "Hydrate and move regularly"
        ]
    }

    # Save
    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    existing = Schedule.query.filter_by(user_id=user.id, date=date_obj).first()
    if existing:
        existing.schedule_data = schedule_data
        db.session.commit()
    else:
        new_schedule = Schedule(user_id=user.id, date=date_obj, schedule_data=schedule_data)
        db.session.add(new_schedule)
        db.session.commit()
    return jsonify({"status": "success", "date": date_str, "schedule": schedule_data, "source": "fallback"})

# API routes for schedule
@app.route('/api/schedule', methods=['POST'])
@login_required
def api_schedule():
    data = request.json
    date_str = data.get('date', get_today())
    
    # Check if schedule already exists for this date
    existing_schedule = Schedule.query.filter_by(user_id=current_user.id, date=datetime.strptime(date_str, "%Y-%m-%d").date()).first()
    if existing_schedule:
        return jsonify(existing_schedule.schedule_data)
    
    # Check if user has completed their profile
    if not current_user.name or not current_user.sleep_schedule:
        return jsonify({
            "error": "Profile incomplete",
            "message": "Please complete your profile before generating a schedule. We need your wake up and sleep times to create an optimized schedule."
        }), 400
    
    # Check if user has any pending tasks
    pending_tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
    # Allow generation without tasks
    
    # Parse sleep schedule
    try:
        sleep_schedule = json.loads(current_user.sleep_schedule) if isinstance(current_user.sleep_schedule, str) else current_user.sleep_schedule
        wake_time = sleep_schedule.get('wake_time', '7:00 AM')
        bedtime = sleep_schedule.get('bedtime', '11:00 PM')
    except:
        wake_time = '7:00 AM'
        bedtime = '11:00 PM'
    
    # Generate schedule based on user's actual tasks and preferences
    schedule_items = []
    
    # Morning routine based on wake time
    morning_end = add_time(wake_time, 30)
    schedule_items.append({
        "time": f"{wake_time} - {morning_end}",
        "task": "Morning routine & light stretching",
        "reason": "Gentle start to energize your day based on your wake up time",
        "type": "health"
    })
    
    # High energy time for important tasks
    high_energy_start = add_time(wake_time, 60)  # 1 hour after waking
    high_energy_end = add_time(high_energy_start, 120)  # 2 hours block
    
    schedule_items.append({
        "time": f"{high_energy_start} - {high_energy_end}",
        "task": f"Deep work session - {pending_tasks[0].description}" if pending_tasks else "Focused work",
        "reason": "High energy time for demanding tasks based on your preferences",
        "type": pending_tasks[0].type if pending_tasks else "work"
    })
    
    # Break
    break_time_start = add_time(high_energy_end, 15)
    break_time_end = add_time(break_time_start, 15)
    
    schedule_items.append({
        "time": f"{break_time_start} - {break_time_end}",
        "task": "Break",
        "reason": "Short break to refresh your mind",
        "type": "break"
    })
    
    # Continue with tasks
    work_time_start = add_time(break_time_end, 15)
    work_time_end = add_time(work_time_start, 90)  # 1.5 hours
    
    schedule_items.append({
        "time": f"{work_time_start} - {work_time_end}",
        "task": f"Project work - {pending_tasks[1].description if len(pending_tasks) > 1 else 'Additional tasks'}",
        "reason": "Continued focus time for complex tasks",
        "type": pending_tasks[1].type if len(pending_tasks) > 1 else "work"
    })
    
    # Lunch break
    lunch_start = add_time(work_time_end, 60)
    lunch_end = add_time(lunch_start, 60)
    
    schedule_items.append({
        "time": f"{lunch_start} - {lunch_end}",
        "task": "Lunch break",
        "reason": "Nourishment and rest based on your schedule",
        "type": "personal"
    })
    
    # Afternoon work
    afternoon_start = add_time(lunch_end, 60)
    afternoon_end = add_time(afternoon_start, 90)
    
    schedule_items.append({
        "time": f"{afternoon_start} - {afternoon_end}",
        "task": "College/Work commitments",
        "reason": "Scheduled college/work time based on your weekly schedule",
        "type": "college/work"
    })
    
    # Family time
    family_time = current_user.family_time or "6:00 PM - 7:00 PM"
    schedule_items.append({
        "time": family_time,
        "task": "Family time",
        "reason": "Dedicated family time as per your preferences",
        "type": "family"
    })
    
    # Workout time based on user preference
    workout_pref = current_user.workout_preference or "evening"
    workout_time = "7:00 PM - 8:00 PM"  # Default evening
    if "morning" in workout_pref.lower():
        workout_time = f"{add_time(wake_time, 30)} - {add_time(wake_time, 90)}"
    
    schedule_items.append({
        "time": workout_time,
        "task": "Workout session",
        "reason": f"{workout_pref.capitalize()} workout as per your preferences",
        "type": "health"
    })
    
    # Evening review before bedtime
    review_time_start = subtract_time(bedtime, 60)
    schedule_items.append({
        "time": f"{review_time_start} - {bedtime}",
        "task": "Review and plan for tomorrow",
        "reason": "Reflect on the day and prepare for tomorrow based on your bedtime",
        "type": "personal"
    })
    
    # Create schedule data
    schedule_data = {
        "schedule": schedule_items,
        "daily_summary": f"Personalized schedule based on your wake time ({wake_time}), bedtime ({bedtime}), and {len(pending_tasks)} pending tasks.",
        "tips": [
            "Take 5-min breaks every hour",
            "Stay hydrated throughout the day",
            "Maintain good posture while working"
        ]
    }
    
    # Save schedule to database
    new_schedule = Schedule(
        user_id=current_user.id,
        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        schedule_data=schedule_data
    )
    db.session.add(new_schedule)
    db.session.commit()
    
    return jsonify(schedule_data)

# Admin route
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('index'))
    
    users = User.query.all()
    
    # Attach last active time
    for user in users:
        last_login = LoginHistory.query.filter_by(user_id=user.id).order_by(LoginHistory.login_timestamp.desc()).first()
        user.last_active = last_login.login_timestamp if last_login else None
        
    return render_template('admin.html', users=users)

# Admin Actions
@app.route('/admin/user/<int:user_id>/ban', methods=['POST'])
@login_required
def admin_ban_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if user.is_admin:
        return jsonify({'error': 'Cannot ban admin'}), 400
        
    data = request.json
    duration = data.get('duration') # days
    
    user.is_banned = True
    if duration and duration != 'permanent':
        try:
            days = int(duration)
            user.banned_until = datetime.utcnow() + timedelta(days=days)
        except:
            pass
            
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User banned successfully'})

@app.route('/admin/user/<int:user_id>/unban', methods=['POST'])
@login_required
def admin_unban_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if user:
        user.is_banned = False
        user.banned_until = None
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User unbanned'})
    return jsonify({'error': 'User not found'}), 404

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    if user.is_admin:
        return jsonify({'error': 'Cannot delete admin'}), 400
        
    # Delete related data logic would go here (or rely on cascade delete if configured)
    # Since we didn't confirm cascades, we'll just delete the user and let SQLite handle foreign keys if set, 
    # or leave orphans if not strict. For this prototype, straightforward delete.
    db.session.delete(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User deleted'})

@app.route('/admin/notify', methods=['POST'])
@login_required
def admin_notify():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.json
    logger.info(f"DEBUG: Admin Notify Data: {data}")
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
        
    try:
        if user_id == 'all':
            users = User.query.filter_by(is_admin=False).all()
            logger.info(f"DEBUG: Notifying {len(users)} users")
            for u in users:
                n = Notification(user_id=u.id, message=message, type='info')
                db.session.add(n)
        else:
            logger.info(f"DEBUG: Notifying user {user_id}")
            n = Notification(user_id=int(user_id), message=message, type='info')
            db.session.add(n)
            
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Notification sent'})
    except Exception as e:
        logger.error(f"DEBUG: Notify Error: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/notification/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Notification not found or access denied'}), 404

# Schedule feedback endpoint
@app.route('/api/schedule/feedback', methods=['POST'])
@login_required
def submit_schedule_feedback():
    """Submit user feedback for a schedule"""
    try:
        data = request.json
        schedule_id = data.get('schedule_id')
        
        if not schedule_id:
            return jsonify({"error": "Schedule ID required"}), 400
        
        # Verify schedule exists and belongs to user
        schedule = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
        if not schedule:
            return jsonify({"error": "Schedule not found"}), 404
        
        # Update schedule with user rating
        overall_rating = data.get('overall_rating')
        if overall_rating:
            schedule.user_rating = overall_rating
            schedule.user_feedback = data.get('feedback_text', '')
        
        # Create detailed feedback record
        feedback = ScheduleFeedback(
            schedule_id=schedule_id,
            user_id=current_user.id,
            overall_rating=overall_rating or 3,
            accuracy_rating=data.get('accuracy_rating'),
            realism_rating=data.get('realism_rating'),
            helpfulness_rating=data.get('helpfulness_rating'),
            feedback_text=data.get('feedback_text'),
            positive_aspects=data.get('positive_aspects', []),
            negative_aspects=data.get('negative_aspects', [])
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback! This helps improve AI scheduling."
        })
        
    except Exception as e:
        return jsonify({"error": "server_error", "message": str(e)}), 500

@app.route('/api/login-history', methods=['GET'])
@login_required
def api_login_history():
    """Get login history for a specific month"""
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        analytics = AnalyticsService()
        login_days = analytics.get_monthly_login_history(current_user.id, year, month)
        
        return jsonify({
            "status": "success",
            "year": year,
            "month": month,
            "login_days": login_days,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        })
    except Exception as e:
        return jsonify({"error": "server_error", "message": str(e)}), 500

import traceback

@app.errorhandler(500)
def internal_error(error):
    return f"<h1>Internal Server Error (Debug Mode)</h1><pre>{traceback.format_exc()}</pre>", 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin', email='admin@example.com', is_admin=True)
            admin_user.set_password(os.environ.get("ADMIN_PASSWORD", "change_me_now"))
            db.session.add(admin_user)
            db.session.commit()
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        print(f"Database initialization error: {e}")


@app.route('/api/calendar-data/<int:year>/<int:month>')
@login_required
def calendar_data(year, month):
    """Get login data for calendar display"""
    user = current_user
    import json
    from datetime import date
    
    # Parse user's login dates
    try:
        login_dates = json.loads(user.login_dates) if user.login_dates else []
    except:
        login_dates = []
    
    # Prepare response
    data = {
        'year': year,
        'month': month,
        'login_dates': login_dates,
        'today': str(date.today())
    }
    
    return jsonify(data)

@app.route('/calendar')
@login_required
def calendar_view():
    """Enhanced calendar page"""
    return render_template('calendar_page.html')

if __name__ == '__main__':
    app.run(debug=False, port=5000)