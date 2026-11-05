"""
Smart Health and Well-Being - DTPL Project
Main Flask Application Controller
"""

import os
from datetime import date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from database import (
    init_db, get_db_connection, create_user,
    verify_user_login, get_user_by_id, save_or_update_daily_log,
    quick_add_water, get_user_daily_log, get_user_history,
    delete_log_entry, calculate_wellbeing_score,
    generate_assessment_suggestions, generate_wellness_tips
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-health-dtpl-secret-key-2026'

# Ensure database tables and columns exist
with app.app_context():
    init_db()


def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access your health dashboard.', 'info')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------------
# Public Routes
# -------------------------------------------------------------------

@app.route('/')
def home():
    """Renders the landing / home page."""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Sign up / registration page route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return render_template('register.html', full_name=full_name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html', full_name=full_name, email=email)

        if password != confirm_password:
            flash('Passwords do not match. Please verify and try again.', 'error')
            return render_template('register.html', full_name=full_name, email=email)

        user_id = create_user(full_name, email, password)
        if not user_id:
            flash('An account with this email already exists. Please login instead.', 'error')
            return render_template('register.html', full_name=full_name, email=email)

        # Automatically log the user in upon successful registration
        session['user_id'] = user_id
        session['user_name'] = full_name
        flash(f'Account created successfully! Welcome to Smart Health, {full_name}.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both your email and password.', 'error')
            return render_template('login.html', email=email)

        user = verify_user_login(email, password)
        if not user:
            flash('Invalid email or password. Please check your credentials.', 'error')
            return render_template('login.html', email=email)

        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        flash(f'Welcome back, {user["full_name"]}!', 'success')

        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logs out current user and clears session."""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'You have been logged out. Stay healthy, {user_name}!', 'info')
    return redirect(url_for('home'))


# -------------------------------------------------------------------
# Protected Dashboard & Health Tracking Routes
# -------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """Renders the user's interactive health and wellness dashboard."""
    user_id = session['user_id']
    today_str = date.today().isoformat()

    # Retrieve today's log and historical records
    today_log = get_user_daily_log(user_id, today_str)
    history = get_user_history(user_id, limit=10)

    suggestions = []
    wellness_score = None
    if today_log:
        wellness_score = today_log.get('wellness_score')
        suggestions = today_log.get('suggestions_list', [])
        if not suggestions:
            suggestions = generate_assessment_suggestions(
                today_log.get('sleep_hours', 7.0),
                today_log.get('water_glasses', 8),
                today_log.get('exercise_mins', 30),
                today_log.get('screen_time_hours', 4.0),
                today_log.get('mood', 'Good 🙂')
            )
    else:
        # Initial guidance before submission
        suggestions = [
            "Enter your sleep, water, exercise, screen time and mood in the assessment form below to calculate your daily score.",
            "Aim for 7–9 hours of sleep, 8+ glasses of water, and 30+ minutes of daily physical exercise.",
            "Take regular screen breaks and practice mindful relaxation to support your well-being."
        ]

    return render_template(
        'dashboard.html',
        today_date=today_str,
        today_log=today_log,
        history=history,
        wellness_score=wellness_score,
        suggestions=suggestions,
        user_name=session.get('user_name')
    )


@app.route('/log-health', methods=['POST'])
@app.route('/assessment', methods=['POST'])
@login_required
def log_health():
    """
    Saves or updates daily health assessment metrics in SQLite,
    calculates the score out of 100, and generates personalized suggestions.
    """
    user_id = session['user_id']
    log_date = request.form.get('log_date') or date.today().isoformat()

    try:
        sleep_hours = float(request.form.get('sleep_hours', 7.0) or 7.0)
    except (ValueError, TypeError):
        sleep_hours = 7.0

    try:
        if request.form.get('water_glasses') is not None:
            water_glasses = int(float(request.form.get('water_glasses', 8) or 8))
        elif request.form.get('water_intake_ml') is not None:
            water_glasses = max(1, round(int(request.form.get('water_intake_ml', 2000)) / 250.0))
        else:
            water_glasses = 8
    except (ValueError, TypeError):
        water_glasses = 8

    try:
        if request.form.get('exercise_mins') is not None:
            exercise_mins = int(float(request.form.get('exercise_mins', 30) or 30))
        elif request.form.get('step_count') is not None:
            exercise_mins = max(10, round(int(request.form.get('step_count', 6000)) / 100.0))
        else:
            exercise_mins = 30
    except (ValueError, TypeError):
        exercise_mins = 30

    try:
        screen_time_hours = float(request.form.get('screen_time_hours', 4.0) or 4.0)
    except (ValueError, TypeError):
        screen_time_hours = 4.0

    mood = request.form.get('mood', 'Good 🙂').strip()
    notes = request.form.get('notes', '').strip()

    score, suggestions = save_or_update_daily_log(
        user_id=user_id,
        log_date=log_date,
        sleep_hours=sleep_hours,
        water_glasses=water_glasses,
        exercise_mins=exercise_mins,
        screen_time_hours=screen_time_hours,
        mood=mood,
        notes=notes
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'wellness_score': score,
            'display_score': f"Your Well-being Score: {score}/100",
            'suggestions': suggestions
        })

    flash(f"Daily Well-being Assessment saved! Your Well-being Score: {score}/100.", "success")
    return redirect(url_for('dashboard', _anchor='assessment-section'))


@app.route('/quick-water', methods=['POST'])
@login_required
def quick_water():
    """Quickly increments today's water intake by 250 mL (1 glass)."""
    user_id = session['user_id']
    today_str = date.today().isoformat()
    new_amount = quick_add_water(user_id, today_str, increment_ml=250)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'water_intake_ml': new_amount})

    flash(f'Added 1 glass (250 mL) of water! Current total: {new_amount} mL.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete-log/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    """Deletes a specific health log entry."""
    user_id = session['user_id']
    delete_log_entry(user_id, log_id)
    flash('Health entry deleted.', 'info')
    return redirect(url_for('dashboard'))


# -------------------------------------------------------------------
# Score Calculation API (Public preview for assessment calculations)
# -------------------------------------------------------------------

@app.route('/api/calculate-score', methods=['POST'])
def api_calculate_score():
    """Calculates Well-being Score and suggestions without saving (for live preview)."""
    data = request.get_json(silent=True) or request.form
    try:
        sleep_hours = float(data.get('sleep_hours', 7.5))
        water_glasses = int(float(data.get('water_glasses', 8)))
        exercise_mins = int(float(data.get('exercise_mins', 30)))
        screen_time_hours = float(data.get('screen_time_hours', 4.0))
        mood = str(data.get('mood', 'Good 🙂'))
    except Exception:
        sleep_hours, water_glasses, exercise_mins, screen_time_hours, mood = 7.5, 8, 30, 4.0, 'Good 🙂'

    score = calculate_wellbeing_score(sleep_hours, water_glasses, exercise_mins, screen_time_hours, mood)
    suggestions = generate_assessment_suggestions(sleep_hours, water_glasses, exercise_mins, screen_time_hours, mood)

    return jsonify({
        'success': True,
        'wellness_score': score,
        'display_score': f"Your Well-being Score: {score}/100",
        'suggestions': suggestions
    })


# -------------------------------------------------------------------
# System Health Check Endpoint
# -------------------------------------------------------------------

@app.route('/api/health-check')
def health_check():
    """API endpoint to verify backend status and database connectivity."""
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "project": "Smart Health and Well-Being (DTPL)",
        "database": db_status
    })


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" Smart Health and Well-Being - DTPL Project Server")
    print(" Running on: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
