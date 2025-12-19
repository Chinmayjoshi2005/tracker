"""
LLM Service for General-Purpose AI Assistance using Ollama Mistral
This module handles communication with the Ollama API to provide
versatile AI assistance including task scheduling, programming help,
conversations, and more based on user requests.
"""


import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from llm_config import PROMPT_CONFIG

# Intent detection utility
def detect_intent(user_prompt: str) -> str:
    prompt = user_prompt.lower()
    if any(w in prompt for w in ["error", "bug", "fix", "not working"]):
        return "debug"
    if any(w in prompt for w in ["plan", "schedule", "routine"]):
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

RULES:
- Always adapt tone and depth based on user intent
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
    
    def generate_general_response(self, user_input: str, conversation_history: List[Dict] = None, user_profile: Dict = None) -> Optional[str]:
        """
        Generate a general response for conversation and assistance
        
        Args:
            user_input: The user's current input/request
            conversation_history: Previous conversation exchanges
            
        Returns:
            str: Generated response or None if failed
        """
        if not self.check_ollama_status():
            return None

        # Determine if this is a scheduling request
        scheduling_keywords = ['schedule', 'plan', 'organize', 'task', 'productivity', 'time', 'day', 'week', 'optimize']
        is_scheduling_request = any(keyword in user_input.lower() for keyword in scheduling_keywords)

        if is_scheduling_request:
            # Return a message directing user to the scheduling feature
            return "I notice you're asking about scheduling or task organization. For the best scheduling experience, please use the dedicated scheduling feature in the application. You can add your tasks in the 'Tasks' section and then generate a schedule in the 'Schedule' section. This will allow me to create a personalized schedule based on your profile and preferences."

        # Profile-awareness: inject profile and intent into prompt
        profile_text = ""
        if user_profile:
            profile_text = json.dumps(user_profile, indent=2)

        prompt = self.create_general_prompt(
            f"USER PROFILE:\n{profile_text}\n\nUSER INPUT:\n{user_input}",
            conversation_history
        )

        try:
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
            return None
    
    def generate_schedule(self, user_profile: Dict, tasks: List[Dict], user_prompt: str = "") -> Optional[Dict]:
        """
        Generate an optimized schedule using Ollama Mistral
        
        Args:
            user_profile: User profile information
            tasks: List of pending tasks
            user_prompt: Additional user context
            
        Returns:
            Dict containing the generated schedule or None if failed
        """
        if not self.check_ollama_status():
            return None
        
        # Calculate task complexity
        complexity = self._calculate_task_complexity(tasks)
        
        # Get optimal parameters based on complexity
        optimal_params = self._get_optimal_parameters(complexity, user_prompt)
        
        prompt = self.create_prompt(user_profile, tasks, user_prompt)
        
        try:
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
