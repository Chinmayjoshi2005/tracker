// static/js/calendar.js
class DynamicCalendar {
    constructor(containerId = 'calendar-grid') {
        this.containerId = containerId;
        this.currentDate = new Date();
        this.currentYear = this.currentDate.getFullYear();
        this.currentMonth = this.currentDate.getMonth() + 1;
        
        this.init();
    }
    
    init() {
        this.loadCalendarData();
        this.setupEventListeners();
        this.updateMonthYearSelectors();
    }
    
    async loadCalendarData() {
        try {
            const response = await fetch(`/api/calendar-data/${this.currentYear}/${this.currentMonth}`);
            if (!response.ok) {
                throw new Error('Failed to fetch calendar data');
            }
            const data = await response.json();
            this.renderCalendar(data);
        } catch (error) {
            console.error('Error loading calendar data:', error);
            this.showError();
        }
    }
    
    showError() {
        const calendarGrid = document.getElementById(this.containerId);
        calendarGrid.innerHTML = `
            <div style="grid-column: span 7; text-align: center; padding: 40px; color: #666;">
                <p>Unable to load calendar data.</p>
                <button onclick="location.reload()" class="btn btn-secondary">Retry</button>
            </div>
        `;
    }
    
    renderCalendar(data) {
        const calendarGrid = document.getElementById(this.containerId);
        calendarGrid.innerHTML = '';
        
        // Add day headers
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        days.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            calendarGrid.appendChild(dayHeader);
        });
        
        // Calculate days in month
        const firstDay = new Date(data.year, data.month - 1, 1);
        const lastDay = new Date(data.year, data.month, 0);
        const daysInMonth = lastDay.getDate();
        const startingDay = firstDay.getDay();
        
        // Add empty days for padding
        for (let i = 0; i < startingDay; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day empty';
            calendarGrid.appendChild(emptyDay);
        }
        
        // Add actual days
        let loginCount = 0;
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
        
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'calendar-day';
            
            const dateStr = `${data.year}-${String(data.month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            
            // Check if logged in
            const isLoggedIn = data.login_dates && data.login_dates.includes(dateStr);
            const isToday = today === dateStr;
            
            if (isLoggedIn) {
                dayElement.classList.add('logged-in');
                loginCount++;
            } else {
                dayElement.classList.add('not-logged-in');
            }
            
            if (isToday) {
                dayElement.classList.add('today');
            }
            
            // Add tooltip
            dayElement.title = `${dateStr} - ${isLoggedIn ? 'Logged in' : 'Not logged in'}`;
            
            dayElement.innerHTML = `
                <div class="day-number">${day}</div>
                <div class="day-status"></div>
            `;
            
            calendarGrid.appendChild(dayElement);
        }
        
        // Update progress
        this.updateProgress(loginCount, daysInMonth);
        document.getElementById('current-month-year').textContent = 
            `${this.getMonthName(data.month)} ${data.year}`;
    }
    
    updateProgress(loginCount, totalDays) {
        const percentage = totalDays > 0 ? Math.round((loginCount / totalDays) * 100) : 0;
        
        const loginCountEl = document.getElementById('login-count');
        const totalDaysEl = document.getElementById('total-days');
        const progressPercentEl = document.getElementById('progress-percentage');
        
        if (loginCountEl) loginCountEl.textContent = loginCount;
        if (totalDaysEl) totalDaysEl.textContent = totalDays;
        if (progressPercentEl) progressPercentEl.textContent = `${percentage}%`;
        
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
            
            // Change color based on progress
            if (percentage >= 80) {
                progressFill.style.background = 'linear-gradient(to right, #2ecc71, #27ae60)';
            } else if (percentage >= 50) {
                progressFill.style.background = 'linear-gradient(to right, #f39c12, #e67e22)';
            } else {
                progressFill.style.background = 'linear-gradient(to right, #e74c3c, #c0392b)';
            }
        }
    }
    
    updateMonthYearSelectors() {
        const monthSelect = document.getElementById('month-select');
        const yearSelect = document.getElementById('year-select');
        
        if (monthSelect) monthSelect.value = this.currentMonth;
        if (yearSelect) yearSelect.value = this.currentYear;
    }
    
    getMonthName(month) {
        const months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        return months[month - 1] || 'Unknown';
    }
    
    setupEventListeners() {
        // Previous month button
        const prevBtn = document.getElementById('prev-month');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.currentMonth--;
                if (this.currentMonth < 1) {
                    this.currentMonth = 12;
                    this.currentYear--;
                }
                this.updateMonthYearSelectors();
                this.loadCalendarData();
            });
        }
        
        // Next month button
        const nextBtn = document.getElementById('next-month');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.currentMonth++;
                if (this.currentMonth > 12) {
                    this.currentMonth = 1;
                    this.currentYear++;
                }
                this.updateMonthYearSelectors();
                this.loadCalendarData();
            });
        }
        
        // Go button
        const goBtn = document.getElementById('go-date');
        if (goBtn) {
            goBtn.addEventListener('click', () => {
                const monthSelect = document.getElementById('month-select');
                const yearSelect = document.getElementById('year-select');
                
                if (monthSelect && yearSelect) {
                    this.currentMonth = parseInt(monthSelect.value);
                    this.currentYear = parseInt(yearSelect.value);
                    this.loadCalendarData();
                }
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if calendar container exists
    if (document.getElementById('calendar-grid')) {
        window.calendar = new DynamicCalendar();
    }
});