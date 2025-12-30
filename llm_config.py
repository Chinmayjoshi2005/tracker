"""
LLM Fine-tuning Configuration
This file contains all tunable parameters for the Ollama Mistral model
"""

# Model Configuration
MODEL_CONFIG = {
    # Model selection
    'model_name': 'mistral',
    'base_url': 'http://localhost:11434',
    
    # Gemini Configuration
    'gemini': {
        'model_name': 'gemini-pro',
        'api_key_env': 'GEMINI_API_KEY',
    },
    
    # Generation parameters by complexity
    'parameters': {
        'simple': {
            'temperature': 0.5,      # Lower for more focused, deterministic output
            'top_p': 0.85,           # Nucleus sampling threshold
            'top_k': 35,             # Token selection limit
            'max_tokens': 1500,      # Maximum response length
            'repeat_penalty': 1.1,   # Penalty for repetition
        },
        'moderate': {
            'temperature': 0.7,      # Balanced creativity and consistency
            'top_p': 0.9,
            'top_k': 40,
            'max_tokens': 2048,
            'repeat_penalty': 1.1,
        },
        'complex': {
            'temperature': 0.8,      # Higher for more creative solutions
            'top_p': 0.95,
            'top_k': 50,
            'max_tokens': 2500,
            'repeat_penalty': 1.15,  # Slightly higher to avoid loops
        }
    },
    
    # API settings
    'timeout': 60,  # seconds
    'retry_attempts': 2,
}

# Prompt Engineering Settings
PROMPT_CONFIG = {
    # System role definition
    'system_role': 'Chinu Ai, a friendly, high-energy, and motivative AI assistant. You speak in simple, easy-to-understand English by default. If the user speaks Hinglish or asks for it, you switch to Hinglish (Indian context). You are short, direct, and to the point.',
    
    # Style guidelines
    'style_instructions': [
        'Keep answers extremely short and concise (max 2-3 sentences unless asked for more)',
        'Default to simple English. Use Hinglish ONLY if the user uses it first or asks for it.',
        'Be highly motivating and energetic (e.g., "You got this!", "Let\'s do it!")',
        'NEVER start with "Hello! I am..." or generic introductions',
        'Directly answer the question without fluff',
        'Use emojis to add vibe 🚀 🔥 💪'
    ],
    
    # Quality requirements
    'quality_checklist': [
        'Response is short and direct',
        'Uses English by default, Hinglish if requested',
        'Tone is motivating',
        'No generic AI introductions'
    ],
    
    # Time blocking rules
    'time_blocking': {
        'min_block_minutes': 30,
        'max_block_minutes': 120,
        'buffer_minutes': 15,
        'break_frequency_minutes': 60,
        'break_duration_minutes': 10,
    },
    
    # Energy management
    'energy_rules': {
        'max_intense_hours': 4,
        'peak_task_types': ['high-priority', 'cognitively demanding', 'creative work'],
        'low_energy_tasks': ['administrative', 'routine', 'email', 'planning'],
    },
    
    # Work-life balance
    'balance_rules': {
        'min_break_minutes_per_day': 60,
        'meal_break_minutes': [30, 60, 30],  # breakfast, lunch, dinner
        'buffer_for_unexpected_minutes': 45,
    }
}

# Schedule Validation Settings
VALIDATION_CONFIG = {
    # Scoring weights (must sum to 1.0)
    'score_weights': {
        'energy_alignment': 0.25,
        'task_coverage': 0.30,
        'work_life_balance': 0.20,
        'realism': 0.15,
        'time_management': 0.10,
    },
    
    # Quality thresholds
    'quality_thresholds': {
        'excellent': 90,
        'good': 75,
        'acceptable': 60,
        'needs_improvement': 45,
    },
    
    # Validation rules
    'rules': {
        'max_work_hours': 10,
        'min_break_hours': 1,
        'max_continuous_work_minutes': 120,
        'required_components': ['morning_routine', 'meals', 'breaks', 'workout'],
    }
}

# Few-shot Learning Examples
FEW_SHOT_EXAMPLES = [
    {
        'user_context': {
            'role': 'student',
            'peak_energy': 'morning',
            'tasks': [
                {'description': 'Study for exam', 'priority': 'high', 'duration': '3h', 'type': 'study'},
                {'description': 'Complete assignment', 'priority': 'medium', 'duration': '2h', 'type': 'study'}
            ],
            'wake_time': '6:30 AM',
            'bedtime': '10:30 PM'
        },
        'good_schedule_snippet': {
            'time': '7:00 AM - 10:00 AM',
            'task': 'Deep study session - Exam preparation (high priority)',
            'reason': 'Morning peak energy time, ideal for intensive learning and retention',
            'type': 'study',
            'priority': 'high'
        }
    },
    {
        'user_context': {
            'role': 'working professional',
            'peak_energy': 'afternoon',
            'tasks': [
                {'description': 'Project presentation', 'priority': 'high', 'duration': '2h', 'type': 'work'}
            ]
        },
        'good_schedule_snippet': {
            'time': '2:00 PM - 4:00 PM',
            'task': 'Prepare project presentation (high priority)',
            'reason': 'Afternoon peak energy - best time for creative and high-stakes work',
            'type': 'work',
            'priority': 'high'
        }
    }
]

# Feedback and Learning Settings
FEEDBACK_CONFIG = {
    'enable_user_feedback': True,
    'rating_scale': [1, 2, 3, 4, 5],  # 1=Poor, 5=Excellent
    'feedback_categories': [
        'accuracy',
        'realism',
        'helpfulness',
        'time_allocations',
        'break_frequency'
    ],
    
    # Adaptive learning
    'learning_rate': 0.1,  # How much to adjust based on feedback
    'min_feedback_count': 5,  # Minimum feedback before adjustment
}

# Advanced Optimization Settings
OPTIMIZATION_CONFIG = {
    # Task batching
    'enable_task_batching': True,
    'batch_similar_tasks': True,
    'max_context_switches': 5,
    
    # Pomodoro technique
    'suggest_pomodoro': True,
    'pomodoro_work_minutes': 25,
    'pomodoro_break_minutes': 5,
    'pomodoro_long_break_minutes': 15,
    
    # Time management techniques
    'techniques': [
        'Pomodoro Technique',
        'Time Blocking',
        'Eat the Frog (hardest task first)',
        'Batch Processing',
        '80/20 Rule (Pareto Principle)'
    ]
}

# User preference adaptation
PREFERENCE_ADAPTATION = {
    # Words indicating user wants more structure
    'structure_keywords': ['strict', 'exact', 'specific', 'must', 'required', 'fixed'],
    
    # Words indicating user wants flexibility
    'flexibility_keywords': ['flexible', 'creative', 'suggest', 'ideas', 'maybe', 'optional'],
    
    # Words indicating high stress/pressure
    'stress_keywords': ['urgent', 'deadline', 'critical', 'emergency', 'asap'],
    
    # Temperature adjustments based on keywords
    'keyword_temp_adjustments': {
        'structure': -0.1,
        'flexibility': +0.1,
        'stress': -0.15,  # More focused when stressed
    }
}

# Error handling and fallback
ERROR_CONFIG = {
    'max_retries': 2,
    'retry_delay_seconds': 2,
    'fallback_to_rules': True,
    'log_errors': True,
}
