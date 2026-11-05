"""
Database module for Smart Health and Well-Being (DTPL Project)
Handles SQLite connection, schema initialization, migrations, scoring algorithm,
personalized suggestions generation, and data access methods.
"""

import os
import sqlite3
import json
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

# Database file path inside the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "smart_health.db")


def get_db_connection():
    """Establish and return a connection to SQLite with Row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes and safely migrates the SQLite database tables and indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Wellness logs table (one entry per user per day)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wellness_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date DATE NOT NULL,
            sleep_hours REAL DEFAULT 7.0,
            water_glasses INTEGER DEFAULT 8,
            exercise_mins INTEGER DEFAULT 30,
            screen_time_hours REAL DEFAULT 4.0,
            mood TEXT DEFAULT 'Good 🙂',
            wellness_score INTEGER DEFAULT 0,
            suggestions TEXT DEFAULT '',
            water_intake_ml INTEGER DEFAULT 2000,
            step_count INTEGER DEFAULT 6000,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, log_date)
        );
    """)

    # Safe Schema Migration: add any missing columns to existing tables
    cursor.execute("PRAGMA table_info(wellness_logs)")
    existing_cols = {col[1]: col for col in cursor.fetchall()}

    if "water_glasses" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN water_glasses INTEGER DEFAULT 8")
    if "exercise_mins" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN exercise_mins INTEGER DEFAULT 30")
    if "screen_time_hours" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN screen_time_hours REAL DEFAULT 4.0")
    if "suggestions" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN suggestions TEXT DEFAULT ''")
    if "sleep_hours" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN sleep_hours REAL DEFAULT 7.0")
    if "water_intake_ml" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN water_intake_ml INTEGER DEFAULT 2000")
    if "step_count" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN step_count INTEGER DEFAULT 6000")
    if "notes" not in existing_cols:
        cursor.execute("ALTER TABLE wellness_logs ADD COLUMN notes TEXT DEFAULT ''")

    # Backfill existing logs if needed
    cursor.execute("""
        UPDATE wellness_logs
        SET water_glasses = CASE
            WHEN water_glasses IS NULL OR water_glasses = 0 THEN MAX(1, ROUND(water_intake_ml / 250.0))
            ELSE water_glasses
        END,
        exercise_mins = CASE
            WHEN exercise_mins IS NULL OR exercise_mins = 0 THEN 30
            ELSE exercise_mins
        END,
        screen_time_hours = CASE
            WHEN screen_time_hours IS NULL OR screen_time_hours = 0.0 THEN 4.0
            ELSE screen_time_hours
        END
    """)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized and verified at: {DB_FILE}")


# -------------------------------------------------------------------
# User Authentication Helpers
# -------------------------------------------------------------------

def create_user(full_name, email, password):
    """Creates a new user with hashed password. Returns user id or None if email exists."""
    email_clean = email.strip().lower()
    password_hash = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
        """, (full_name.strip(), email_clean, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    """Fetches a user record by email address."""
    email_clean = email.strip().lower()
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email_clean,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Fetches a user record by user ID."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def verify_user_login(email, password):
    """Verifies email and password. Returns user row if valid, otherwise None."""
    user = get_user_by_email(email)
    if user and check_password_hash(user['password_hash'], password):
        return user
    return None


# -------------------------------------------------------------------
# Well-being Score Calculation & Personalized Suggestions
# -------------------------------------------------------------------

def get_mood_points(mood):
    """Returns scoring points (max 20) for given mood string."""
    m = str(mood or "").strip()
    if "Excellent" in m:
        return 20
    elif "Good" in m:
        return 17
    elif "Neutral" in m:
        return 13
    elif "Stressed" in m:
        return 7
    elif "Sad" in m:
        return 5
    elif "Energized" in m or "Great" in m:
        return 20
    elif "Balanced" in m or "Calm" in m:
        return 15
    elif "Tired" in m:
        return 8
    return 13


def calculate_wellbeing_score(sleep_hours, water_glasses, exercise_mins, screen_time_hours, mood):
    """
    Calculates a Well-being Score out of 100 based on 5 parameters:
    1. Sleep (hours)          - Max 25 points (optimal 7.0 - 9.0 hrs)
    2. Water Intake (glasses) - Max 20 points (optimal 8+ glasses)
    3. Exercise (minutes)     - Max 20 points (optimal 30 - 45+ mins)
    4. Screen Time (hours)    - Max 15 points (optimal <= 2.0 - 4.0 hrs)
    5. Mood                   - Max 20 points (Excellent: 20, Good: 17, Neutral: 13, Stressed: 7, Sad: 5)
    Total: 100 points
    """
    score = 0

    try:
        sleep = float(sleep_hours or 0.0)
    except (ValueError, TypeError):
        sleep = 0.0

    try:
        water = int(water_glasses or 0)
    except (ValueError, TypeError):
        water = 0

    try:
        exercise = int(exercise_mins or 0)
    except (ValueError, TypeError):
        exercise = 0

    try:
        screen = float(screen_time_hours or 0.0)
    except (ValueError, TypeError):
        screen = 0.0

    # 1. Sleep (Max 25 pts)
    if 7.0 <= sleep <= 9.0:
        score += 25
    elif 6.0 <= sleep < 7.0 or 9.0 < sleep <= 10.0:
        score += 18
    elif 5.0 <= sleep < 6.0:
        score += 12
    elif 4.0 <= sleep < 5.0 or 10.0 < sleep <= 11.0:
        score += 7
    elif sleep > 0:
        score += 3

    # 2. Water Intake in glasses (Max 20 pts)
    if water >= 8:
        score += 20
    elif water == 7:
        score += 17
    elif water == 6:
        score += 14
    elif water == 5:
        score += 11
    elif water >= 3:
        score += 7
    elif water >= 1:
        score += 4

    # 3. Exercise in minutes (Max 20 pts)
    if exercise >= 45:
        score += 20
    elif exercise >= 30:
        score += 18
    elif exercise >= 20:
        score += 14
    elif exercise >= 10:
        score += 9
    elif exercise > 0:
        score += 4

    # 4. Screen Time in hours (Max 15 pts) - lower is healthier
    if screen <= 2.0:
        score += 15
    elif screen <= 4.0:
        score += 13
    elif screen <= 6.0:
        score += 10
    elif screen <= 8.0:
        score += 6
    else:
        score += 2

    # 5. Mood (Max 20 pts)
    score += get_mood_points(mood)

    return max(0, min(100, score))


def generate_assessment_suggestions(sleep_hours, water_glasses, exercise_mins, screen_time_hours, mood):
    """
    Generates simple personalized wellness suggestions based on the entered values:
    - If exercise is low, suggest increasing physical activity.
    - If water intake is low, suggest drinking more water.
    - If sleep is low, suggest maintaining a regular sleep schedule.
    - If screen time is high, suggest taking regular screen breaks.
    - Also includes mood-supportive guidance.
    """
    suggestions = []

    try:
        sleep = float(sleep_hours or 0.0)
    except (ValueError, TypeError):
        sleep = 0.0

    try:
        water = int(water_glasses or 0)
    except (ValueError, TypeError):
        water = 0

    try:
        exercise = int(exercise_mins or 0)
    except (ValueError, TypeError):
        exercise = 0

    try:
        screen = float(screen_time_hours or 0.0)
    except (ValueError, TypeError):
        screen = 0.0

    # 1. Sleep suggestion
    if sleep < 7.0:
        suggestions.append(
            f"Sleep duration is low ({sleep} hrs): Suggest maintaining a regular sleep schedule and winding down 30 minutes earlier without screens."
        )
    elif sleep > 9.0:
        suggestions.append(
            f"Extended sleep logged ({sleep} hrs): Ensure a steady 7–9 hours sleep window to maintain balanced daytime energy."
        )
    else:
        suggestions.append(
            f"Optimal sleep ({sleep} hrs): Excellent! 7–9 hours of sleep promotes immune health, cell repair, and mental focus."
        )

    # 2. Water intake suggestion
    if water < 8:
        suggestions.append(
            f"Water intake is low ({water} glasses): Suggest drinking more water throughout the day to reach the recommended 8 glasses."
        )
    else:
        suggestions.append(
            f"Great hydration ({water} glasses): You achieved your daily hydration goal, supporting digestion and stamina."
        )

    # 3. Exercise suggestion
    if exercise < 30:
        suggestions.append(
            f"Exercise duration is low ({exercise} mins): Suggest increasing physical activity to at least 30 minutes daily (e.g. brisk walking, jogging, or cycling)."
        )
    else:
        suggestions.append(
            f"Active lifestyle ({exercise} mins): Superb exercise duration! Regular physical movement boosts cardiovascular fitness and relieves stress."
        )

    # 4. Screen time suggestion
    if screen > 6.0:
        suggestions.append(
            f"Screen time is high ({screen} hrs): Suggest taking regular screen breaks every 45–60 minutes (20-20-20 rule) to reduce eye strain and fatigue."
        )
    elif screen > 4.0:
        suggestions.append(
            f"Moderate screen time ({screen} hrs): Remember to take brief pauses away from the monitor during long study/work periods."
        )
    else:
        suggestions.append(
            f"Healthy screen exposure ({screen} hrs): Keeping screen time balanced helps protect vision and promotes better sleep quality."
        )

    # 5. Mood suggestion
    mood_str = str(mood or "").lower()
    if "stressed" in mood_str:
        suggestions.append(
            "Mind & Mood: You noted feeling stressed. Dedicate 10 minutes to deep breathing, gentle stretching, or listening to calming music."
        )
    elif "sad" in mood_str:
        suggestions.append(
            "Mind & Mood: You noted feeling down. Be kind to yourself today, speak with a supportive friend, or take a gentle nature walk."
        )
    elif "neutral" in mood_str:
        suggestions.append(
            "Mind & Mood: A calm, steady mindset today. Consider an engaging activity or uplifting music to give your day a boost."
        )
    elif "good" in mood_str or "excellent" in mood_str or "great" in mood_str:
        suggestions.append(
            "Mind & Mood: Positive and uplifting mindset! Channel this positive energy into your goals and share your optimism with others."
        )

    return suggestions


# Legacy alias
def calculate_wellness_score(water_ml, steps, sleep_hours, mood):
    """Backward compatibility wrapper."""
    water_glasses = max(1, round(float(water_ml or 0) / 250.0))
    exercise_mins = max(10, round(float(steps or 0) / 100.0))
    return calculate_wellbeing_score(sleep_hours, water_glasses, exercise_mins, 4.0, mood)


def generate_wellness_tips(today_log):
    """Backward compatibility tips helper for dashboard banner."""
    if not today_log:
        return [
            "🌟 Fill out the Daily Well-being Assessment below to calculate your Well-being Score!",
            "💧 Aim for at least 8 glasses of water throughout your day.",
            "🚶 Plan for at least 30 minutes of physical exercise today."
        ]
    return generate_assessment_suggestions(
        today_log.get('sleep_hours', 7.0),
        today_log.get('water_glasses', 8),
        today_log.get('exercise_mins', 30),
        today_log.get('screen_time_hours', 4.0),
        today_log.get('mood', 'Good 🙂')
    )


# -------------------------------------------------------------------
# Data Storage & Retrieval
# -------------------------------------------------------------------

def save_or_update_daily_log(
    user_id,
    log_date,
    sleep_hours=7.0,
    water_glasses=8,
    exercise_mins=30,
    screen_time_hours=4.0,
    mood="Good 🙂",
    notes="",
    water_ml=None,
    step_count=None
):
    """
    Inserts or updates a user's health log for a specific date in SQLite.
    Calculates the Well-being Score and generates personalized suggestions.
    """
    sleep = float(sleep_hours or 0.0)
    water = int(water_glasses or 0)
    exercise = int(exercise_mins or 0)
    screen = float(screen_time_hours or 0.0)
    mood_str = str(mood or "Good 🙂").strip()

    # Derived values for backward compatibility
    if water_ml is None:
        water_ml = water * 250
    if step_count is None:
        step_count = exercise * 100

    score = calculate_wellbeing_score(sleep, water, exercise, screen, mood_str)
    suggestions_list = generate_assessment_suggestions(sleep, water, exercise, screen, mood_str)
    suggestions_json = json.dumps(suggestions_list)

    conn = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("""
        SELECT id FROM wellness_logs WHERE user_id = ? AND log_date = ?
    """, (user_id, log_date)).fetchone()

    if existing:
        cursor.execute("""
            UPDATE wellness_logs
            SET sleep_hours = ?,
                water_glasses = ?,
                exercise_mins = ?,
                screen_time_hours = ?,
                mood = ?,
                wellness_score = ?,
                suggestions = ?,
                water_intake_ml = ?,
                step_count = ?,
                notes = ?
            WHERE id = ?
        """, (
            sleep, water, exercise, screen, mood_str, score,
            suggestions_json, int(water_ml), int(step_count),
            notes.strip() if notes else "", existing['id']
        ))
    else:
        cursor.execute("""
            INSERT INTO wellness_logs (
                user_id, log_date, sleep_hours, water_glasses, exercise_mins,
                screen_time_hours, mood, wellness_score, suggestions,
                water_intake_ml, step_count, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, log_date, sleep, water, exercise,
            screen, mood_str, score, suggestions_json,
            int(water_ml), int(step_count), notes.strip() if notes else ""
        ))

    conn.commit()
    conn.close()
    return score, suggestions_list


def quick_add_water(user_id, log_date, increment_ml=250):
    """Quickly increments water intake by 250 mL (1 glass) for a specific date."""
    conn = get_db_connection()
    cursor = conn.cursor()

    existing = cursor.execute("""
        SELECT * FROM wellness_logs WHERE user_id = ? AND log_date = ?
    """, (user_id, log_date)).fetchone()

    if existing:
        new_water_ml = (existing['water_intake_ml'] or 0) + increment_ml
        new_glasses = (existing['water_glasses'] or 0) + 1
        sleep = existing['sleep_hours'] or 7.0
        exercise = existing['exercise_mins'] or 30
        screen = existing['screen_time_hours'] or 4.0
        mood = existing['mood'] or 'Good 🙂'

        new_score = calculate_wellbeing_score(sleep, new_glasses, exercise, screen, mood)
        suggestions_list = generate_assessment_suggestions(sleep, new_glasses, exercise, screen, mood)
        suggestions_json = json.dumps(suggestions_list)

        cursor.execute("""
            UPDATE wellness_logs
            SET water_intake_ml = ?,
                water_glasses = ?,
                wellness_score = ?,
                suggestions = ?
            WHERE id = ?
        """, (new_water_ml, new_glasses, new_score, suggestions_json, existing['id']))
    else:
        new_water_ml = increment_ml
        new_glasses = 1
        new_score = calculate_wellbeing_score(7.0, new_glasses, 30, 4.0, 'Good 🙂')
        suggestions_list = generate_assessment_suggestions(7.0, new_glasses, 30, 4.0, 'Good 🙂')
        suggestions_json = json.dumps(suggestions_list)

        cursor.execute("""
            INSERT INTO wellness_logs (
                user_id, log_date, sleep_hours, water_glasses, exercise_mins,
                screen_time_hours, mood, wellness_score, suggestions,
                water_intake_ml, step_count, notes
            )
            VALUES (?, ?, 7.0, ?, 30, 4.0, 'Good 🙂', ?, ?, ?, 3000, '')
        """, (user_id, log_date, new_glasses, new_score, suggestions_json, new_water_ml))

    conn.commit()
    conn.close()
    return new_water_ml


def get_user_daily_log(user_id, log_date):
    """Returns the log dict for a specific user and date, or None."""
    conn = get_db_connection()
    row = conn.execute("""
        SELECT * FROM wellness_logs WHERE user_id = ? AND log_date = ?
    """, (user_id, log_date)).fetchone()
    conn.close()

    if not row:
        return None

    row_dict = dict(row)
    # Parse suggestions JSON if present, or dynamically compute
    if row_dict.get('suggestions'):
        try:
            row_dict['suggestions_list'] = json.loads(row_dict['suggestions'])
        except Exception:
            row_dict['suggestions_list'] = generate_assessment_suggestions(
                row_dict.get('sleep_hours', 7.0),
                row_dict.get('water_glasses', 8),
                row_dict.get('exercise_mins', 30),
                row_dict.get('screen_time_hours', 4.0),
                row_dict.get('mood', 'Good 🙂')
            )
    else:
        row_dict['suggestions_list'] = generate_assessment_suggestions(
            row_dict.get('sleep_hours', 7.0),
            row_dict.get('water_glasses', 8),
            row_dict.get('exercise_mins', 30),
            row_dict.get('screen_time_hours', 4.0),
            row_dict.get('mood', 'Good 🙂')
        )

    return row_dict


def get_user_history(user_id, limit=10):
    """Returns the most recent health logs for a user ordered by date descending."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT * FROM wellness_logs 
        WHERE user_id = ? 
        ORDER BY log_date DESC, id DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        # Ensure fallback defaults for older rows
        if not d.get('water_glasses') and d.get('water_intake_ml'):
            d['water_glasses'] = max(1, round(d['water_intake_ml'] / 250.0))
        elif not d.get('water_glasses'):
            d['water_glasses'] = 8

        if not d.get('exercise_mins') and d.get('step_count'):
            d['exercise_mins'] = max(10, round(d['step_count'] / 100.0))
        elif not d.get('exercise_mins'):
            d['exercise_mins'] = 30

        if d.get('screen_time_hours') is None or d.get('screen_time_hours') == 0.0:
            d['screen_time_hours'] = 4.0

        if not d.get('sleep_hours'):
            d['sleep_hours'] = 7.0

        result.append(d)

    return result


def delete_log_entry(user_id, log_id):
    """Deletes a health log entry belonging to the user."""
    conn = get_db_connection()
    conn.execute("DELETE FROM wellness_logs WHERE id = ? AND user_id = ?", (log_id, user_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
