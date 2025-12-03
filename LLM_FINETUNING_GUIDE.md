# LLM Fine-Tuning Guide for Optimal Schedule Generation

This guide explains how the AI Task Optimizer has been fine-tuned to provide accurate, personalized schedules using Ollama Mistral.

## 🎯 Fine-Tuning Overview

The system has been enhanced with multiple fine-tuning techniques to deliver superior scheduling quality:

### 1. **Advanced Prompt Engineering** ✅

#### Enhanced System Instructions
The LLM now receives:
- **Detailed role definition**: Expert productivity optimization specialist
- **7 critical instruction categories**:
  1. Time Blocking rules (30-120 min blocks)
  2. Energy-Aligned Scheduling (peak hours optimization)
  3. Work-Life Balance requirements
  4. Task Prioritization strategies
  5. Context Awareness (user preferences)
  6. Reasoning & Tips generation
  7. Realism & Flexibility guidelines

#### Structured Examples
- Provides exact JSON format to follow
- Shows ideal schedule snippets
- Demonstrates proper reasoning format
- Includes quality checklist verification

---

### 2. **Dynamic Parameter Adjustment** ✅

#### Complexity-Based Optimization

The system automatically adjusts LLM parameters based on task complexity:

```python
Simple Tasks (1-4 tasks, <6 hours):
- Temperature: 0.5 (more focused)
- Top_p: 0.85
- Max tokens: 1500

Moderate Tasks (5-8 tasks, 6-10 hours):
- Temperature: 0.7 (balanced)
- Top_p: 0.9
- Max tokens: 2048

Complex Tasks (8+ tasks, >10 hours):
- Temperature: 0.8 (more creative)
- Top_p: 0.95
- Max tokens: 2500
```

#### Intent-Based Adjustments

Analyzes user prompts for keywords:

| User Intent | Keywords | Temperature Change |
|-------------|----------|-------------------|
| **Strict** | "strict", "exact", "specific", "must" | -0.1 (more deterministic) |
| **Flexible** | "flexible", "creative", "suggest" | +0.1 (more creative) |
| **Urgent** | "urgent", "deadline", "critical" | -0.15 (highly focused) |

---

### 3. **Schedule Quality Validation** ✅

#### Automated Quality Scoring (0-100)

Every generated schedule is automatically scored on 5 metrics:

1. **Energy Alignment (25% weight)**
   - Are high-priority tasks scheduled during peak energy hours?
   - Example: Morning person gets cognitively demanding tasks at 8-10 AM

2. **Task Coverage (30% weight)**
   - Are ALL pending tasks included in the schedule?
   - Highest weight because missing tasks defeats the purpose

3. **Work-Life Balance (20% weight)**
   - Appropriate ratio of work vs personal time (60-70% work ideal)
   - Adequate breaks (minimum 60 min/day)
   - Family time and workouts included

4. **Realism (15% weight)**
   - Not overpacked (total time < 120% of available hours)
   - No blocks longer than 3 hours (except sleep)
   - Sufficient break intervals

5. **Time Management (10% weight)**
   - Task batching (similar tasks grouped)
   - Buffer time included
   - Proper prioritization

#### Quality Feedback

Schedules with scores <70 receive specific improvement suggestions:
- "Consider scheduling more high-priority tasks during peak energy hours"
- "Schedule may be too packed - consider reducing tasks or extending time"

---

### 4. **User Feedback System** ✅

#### Rating Mechanism

Users can rate schedules on multiple dimensions (1-5 stars):
- **Overall Rating**: General satisfaction
- **Accuracy**: Did it match your needs?
- **Realism**: Could you actually follow it?
- **Helpfulness**: Did it improve your productivity?

#### Feedback Collection

The system stores:
- Numerical ratings
- Text feedback
- Positive aspects (what worked well)
- Negative aspects (what to improve)

#### Adaptive Learning (Future Enhancement)

Feedback data can be used to:
1. Adjust default parameters per user
2. Identify common issues
3. Refine prompt templates
4. Personalize scheduling strategies

---

## 📊 Configuration File

All fine-tuning parameters are centralized in [`llm_config.py`](file:///Users/chinmayjoshi/Desktop/projects/tracker/llm_config.py):

### Key Sections:

1. **MODEL_CONFIG**
   - Model selection and API settings
   - Complexity-based parameters
   - Timeout and retry configuration

2. **PROMPT_CONFIG**
   - System role definition
   - Quality checklist
   - Time blocking rules
   - Energy management strategies

3. **VALIDATION_CONFIG**
   - Score weights
   - Quality thresholds
   - Validation rules

4. **FEEDBACK_CONFIG**
   - Rating scales
   - Learning rate for adaptations
   - Minimum feedback requirements

5. **OPTIMIZATION_CONFIG**
   - Task batching settings
   - Pomodoro technique configuration
   - Time management techniques

---

## 🔧 How to Fine-Tune Further

### 1. Adjust Model Parameters

Edit [`llm_config.py`](file:///Users/chinmayjoshi/Desktop/projects/tracker/llm_config.py):

```python
MODEL_CONFIG = {
    'parameters': {
        'moderate': {
            'temperature': 0.7,  # Increase for creativity, decrease for consistency
            'top_p': 0.9,        # Higher = more diverse, lower = more focused
            'max_tokens': 2048   # Increase if responses are cut off
        }
    }
}
```

**When to adjust**:
- **Temperature too low** → Schedules are repetitive
- **Temperature too high** → Schedules are inconsistent
- **Top_p too low** → Limited vocabulary, boring schedules
- **Max_tokens too low** → Responses are incomplete

### 2. Enhance Prompt Quality

Edit [`llm_service.py`](file:///Users/chinmayjoshi/Desktop/projects/tracker/llm_service.py) in the `create_prompt` method:

**Add more specific instructions**:
```python
prompt += """
ADDITIONAL RULE: 
Always include a 15-minute buffer before important meetings
```

**Add domain-specific examples**:
```python
For students: "Schedule study sessions in 2-hour blocks with 15-min breaks"
For professionals: "Reserve 9-11 AM for deep work, no meetings"
```

### 3. Modify Validation Weights

Edit `VALIDATION_CONFIG` in [`llm_config.py`](file:///Users/chinmayjoshi/Desktop/projects/tracker/llm_config.py):

```python
'score_weights': {
    'energy_alignment': 0.30,  # Increase if energy optimization is most important
    'task_coverage': 0.25,
    'work_life_balance': 0.25,
    'realism': 0.15,
    'time_management': 0.05,
}
```

### 4. Customize for Different User Types

Add user-type-specific rules in the prompt:

```python
if user_profile.get('role') == 'student':
    prompt += "\nPRIORITY: Optimize for learning retention and exam preparation"
elif user_profile.get('role') == 'working professional':
    prompt += "\nPRIORITY: Balance productivity with sustainable work pace"
```

---

## 📈 Quality Improvement Strategies

### Strategy 1: Increase Specificity

**Before**: "Schedule high-priority tasks in the morning"
**After**: "Schedule the most cognitively demanding task between 8:00-10:00 AM when cortisol and alertness peak"

### Strategy 2: Add Constraints

**Example**:
```python
"CONSTRAINT: No meetings before 10 AM (deep work time)"
"CONSTRAINT: Maximum 2 hours continuous screen time"
"CONSTRAINT: 30-minute lunch break is non-negotiable"
```

### Strategy 3: Provide Context

**Include WHY, not just WHAT**:
- "Morning routine prepares mind for focused work"
- "Breaks prevent decision fatigue and maintain performance"
- "Evening review consolidates learning and reduces next-day stress"

### Strategy 4: Use Negative Examples

Tell the LLM what NOT to do:
```
AVOID:
- Scheduling meetings back-to-back with no breaks
- Placing creative work after lunch (post-meal dip)
- Overpacking the schedule (causes stress and failure)
```

---

## 🧪 Testing and Iteration

### 1. Test with Edge Cases

Create test scenarios:
- **Heavy load**: 15 tasks, 8-hour workday
- **Minimal load**: 2 tasks, flexible day
- **Time constraints**: "College 9 AM - 5 PM"
- **Energy mismatch**: Night owl with morning commitments

### 2. Collect Feedback

After each schedule generation:
1. User rates the schedule
2. System logs rating + feedback
3. Analyze patterns in low-rated schedules
4. Identify common issues
5. Adjust prompts or parameters

### 3. A/B Testing

Compare two configurations:
- **Version A**: Temperature 0.7
- **Version B**: Temperature 0.8

Track which produces higher user ratings over 50 schedules.

### 4. Monitor Quality Scores

Track average scores over time:
```
Week 1: Avg Overall Quality = 72
Week 2: Avg Overall Quality = 78 (improved!)
Week 3: Avg Overall Quality = 81
```

---

## 🎓 Advanced Techniques

### 1. Few-Shot Learning (Planned)

Add example good schedules to the prompt:

```python
EXAMPLE 1:
User: Student, morning person, 3 study tasks
Good Schedule:
- 8:00 AM: Hardest subject (Math exam prep)
- 10:00 AM: Break
- 10:15 AM: Medium difficulty (Essay writing)
```

### 2. Chain-of-Thought Prompting

Ask LLM to think step-by-step:
```
First, identify all high-priority tasks
Then, map them to peak energy times
Next, insert breaks between intense blocks
Finally, add flexible tasks in remaining slots
```

### 3. Self-Critique

Ask LLM to validate its own output:
```
After generating the schedule, answer:
1. Are all high-priority tasks in peak hours? (Yes/No)
2. Is there a break every 90 minutes? (Yes/No)
3. Is the schedule realistic? (Yes/No)

If any answer is No, regenerate the schedule.
```

### 4. Persona-Based Prompting

Create user archetypes:
- **The Overachiever**: Needs realistic time limits
- **The Procrastinator**: Needs small, manageable tasks
- **The Perfectionist**: Needs buffer time and flexibility

---

## 📝 Best Practices

### DO:
✅ Provide complete user profile data  
✅ Be specific in user prompts ("I have a deadline at 3 PM")  
✅ Review and adjust generated schedules  
✅ Provide feedback to improve future schedules  
✅ Test different prompts to find what works  

### DON'T:
❌ Expect perfection on first try  
❌ Use vague prompts ("make me a schedule")  
❌ Skip profile completion  
❌ Overload with too many tasks (>15)  
❌ Ignore quality scores and feedback  

---

## 🔄 Continuous Improvement Cycle

```
1. Generate Schedule
     ↓
2. User Reviews & Rates
     ↓
3. Collect Feedback
     ↓
4. Analyze Patterns
     ↓
5. Adjust Parameters/Prompts
     ↓
6. Generate Better Schedule
     ↓
(Repeat)
```

---

## 📞 Support & Feedback

### Common Issues:

**Issue**: Schedule is too packed
**Solution**: Reduce temperature, add "realistic" keyword to prompt

**Issue**: Missing some tasks
**Solution**: Increase max_tokens, check task coverage score

**Issue**: Poor energy alignment
**Solution**: Verify peak_energy setting in profile

**Issue**: Too generic/not personalized
**Solution**: Complete ALL profile fields, add specific prompt details

---

## 🎯 Quality Metrics Goals

Target scores for excellent schedules:

| Metric | Target | Excellent |
|--------|--------|-----------|
| Energy Alignment | >75 | >90 |
| Task Coverage | 100 | 100 |
| Work-Life Balance | >70 | >85 |
| Realism | >75 | >90 |
| Time Management | >70 | >85 |
| **Overall Quality** | >**75** | >**90** |

---

## 🚀 Future Enhancements

Planned improvements:
1. **Reinforcement Learning**: Learn from user ratings over time
2. **Multi-Day Planning**: Generate week-long schedules
3. **Smart Rescheduling**: Automatically adjust when tasks change
4. **Collaborative Filtering**: Learn from similar users' preferences
5. **Natural Language Updates**: "Move my workout to 6 PM"

---

**Made with ❤️ by [chinu](https://chinmay-joshi-4au4ky2.gamma.site/)**

Fine-tuned for your success! 🎯
