import io
import base64
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None
from models import LoginHistory, Task, User, db
from datetime import datetime, timedelta
from sqlalchemy import func

class AnalyticsService:
    def __init__(self):
        pass

    def generate_login_chart(self, user_id):
        """Generate a line chart of login history for the last 7 days"""
        try:
            # Get data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            logins = db.session.query(
                func.date(LoginHistory.login_timestamp), 
                func.count(LoginHistory.id)
            ).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_timestamp >= start_date
            ).group_by(
                func.date(LoginHistory.login_timestamp)
            ).all()
            
            # Prepare data for plotting
            dates = []
            counts = []
            date_map = {str(day): count for day, count in logins}
            
            for i in range(7):
                d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                dates.append(d)
                counts.append(date_map.get(d, 0))
                
            # Plot
            plt.figure(figsize=(10, 5))
            plt.plot(dates, counts, marker='o')
            plt.title('Login Activity (Last 7 Days)')
            plt.xlabel('Date')
            plt.ylabel('Logins')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating login chart: {e}")
            return ""

    def generate_task_chart(self, user_id):
        """Generate a pie chart of task status"""
        try:
            # Get data
            tasks = Task.query.filter_by(user_id=user_id).all()
            if not tasks:
                return ""
                
            status_counts = {'pending': 0, 'completed': 0}
            for task in tasks:
                if task.status in status_counts:
                    status_counts[task.status] += 1
                else:
                    status_counts[task.status] = 1
            
            # Plot
            plt.figure(figsize=(6, 6))
            plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
            plt.title('Task Status Distribution')
            
            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close()
            
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error generating task chart: {e}")
            return ""

    def predict_completion_probability(self, user_id):
        """Predict probability of completing tasks based on history"""
        try:
            total_tasks = Task.query.filter_by(user_id=user_id).count()
            if total_tasks == 0:
                return 0
                
            completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
            
            # Simple probability based on completion rate
            # In a real ML model, this would use more features
            probability = (completed_tasks / total_tasks) * 100
            
            return int(probability)
        except Exception as e:
            print(f"Error predicting completion: {e}")
            return 0
    def calculate_login_streak(self, user_id):
        """Calculate the current login streak in days using User.login_dates"""
        try:
            # Get user to access login_dates
            user = db.session.get(User, user_id)
            if not user or not user.login_dates:
                return 0
                
            import json
            try:
                dates_list = json.loads(user.login_dates)
            except:
                return 0
                
            if not dates_list:
                return 0
                
            # Convert strings to date objects and sort unique
            login_dates = sorted(list(set(
                [datetime.strptime(d, "%Y-%m-%d").date() for d in dates_list]
            )), reverse=True)
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            current_streak = 0
            
            # Check if user logged in today or yesterday (to keep streak alive)
            if not login_dates:
                 return 0
                 
            # Find start of streak
            if login_dates[0] == today:
                current_streak = 1
                check_date = yesterday
                idx = 1
            elif login_dates[0] == yesterday:
                current_streak = 1
                check_date = yesterday - timedelta(days=1)
                idx = 1
            else:
                return 0  # Streak broken (last login was before yesterday)
                
            # Count consecutive days backwards
            while idx < len(login_dates):
                if login_dates[idx] == check_date:
                    current_streak += 1
                    check_date -= timedelta(days=1)
                    idx += 1
                else:
                    # Gap found
                    break
                    
            return current_streak
        except Exception as e:
            print(f"Error calculating streak: {e}")
            return 0

    def get_monthly_login_history(self, user_id, year, month):
        """Get set of days (int) the user logged in for a specific month"""
        try:
            # Calculate start and end date of the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            # Query login dates
            logins = db.session.query(
                func.date(LoginHistory.login_timestamp)
            ).filter(
                LoginHistory.user_id == user_id,
                LoginHistory.login_timestamp >= start_date,
                LoginHistory.login_timestamp < end_date
            ).distinct().all()
            
            # Extract day numbers
            login_days = set()
            for l in logins:
                dt = datetime.strptime(l[0], "%Y-%m-%d")
                login_days.add(dt.day)
                
            return list(login_days)
        except Exception as e:
            print(f"Error getting monthly history: {e}")
            return []
