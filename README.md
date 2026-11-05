# Smart Health and Well-Being (DTPL Project)
**SDG 3: Good Health and Well-being**

A modern, responsive web application built with **Python**, **Flask**, **HTML5**, **CSS3**, **JavaScript**, and **SQLite**. The system empowers users to monitor, assess, and improve their daily wellness through a comprehensive **Daily Well-being Assessment**, real-time **Well-being Score** calculation out of 100, dynamic personalized health suggestions, and persistent health history.

---

## 📁 Project Directory Structure

```text
smart_health_wellbeing/
│
├── app.py                 # Main Flask application controller (routes, auth, assessment calculation)
├── database.py            # SQLite schema, migrations, Well-being scoring algorithm & suggestions
├── requirements.txt       # Project dependencies (Flask, Werkzeug)
├── smart_health.db        # SQLite database with user and health assessment tables
├── run.bat                # 1-click Windows batch launcher
├── run.ps1                # PowerShell launcher script
├── README.md              # Project documentation and user guide
│
├── static/
│   ├── css/
│   │   └── style.css      # Healthcare design system, assessment styling & responsive layouts
│   └── js/
│       └── main.js        # Real-time score calculator, dynamic suggestions, & mobile navigation
│
└── templates/
    ├── base.html          # Base layout template with SDG 3 footer & clean scripts
    ├── index.html         # Modern landing page with interactive Daily Assessment preview
    ├── login.html         # User sign-in interface
    ├── register.html      # User registration interface
    └── dashboard.html     # User dashboard with Assessment form, Score display, Suggestions & History
```

---

## 🛠️ Technology Stack

- **Backend:** Python 3.12, Flask Framework
- **Security:** Password hashing via `werkzeug.security` (`pbkdf2:sha256`)
- **Database:** SQLite3 with relational tables (`users`, `wellness_logs`)
- **Frontend:** Semantic HTML5, Custom Healthcare CSS3 (Flexbox & CSS Grid), Vanilla JavaScript
- **Icons & Graphics:** Clean inline SVG vectors (zero external CDN dependencies)

---

## 🌟 Key Features

### 1. Daily Well-being Assessment
Users can enter five core daily health metrics:
1. **Sleep (hours):** Number input for daily sleep duration (ideal target: 7.0 – 9.0 hours).
2. **Water Intake (glasses):** Number input for daily water consumption (target: 8+ glasses / ~250 mL each).
3. **Exercise (minutes):** Number input for daily physical activity (target: 30+ minutes).
4. **Screen Time (hours):** Number input for daily screen exposure.
5. **Mood:** Dropdown selector with options:
   - Excellent 😊
   - Good 🙂
   - Neutral 😐
   - Stressed 😟
   - Sad 😔
6. **"Calculate Well-being Score" Button:** Evaluates all metrics and computes a score out of 100.
7. **Score Display:** Clearly rendered score (e.g. `Your Well-being Score: 93/100`).
8. **Personalized Suggestions Section:** Dynamic recommendations generated directly beneath the score:
   - *Low Exercise:* Suggests increasing physical activity to at least 30 minutes daily.
   - *Low Water:* Suggests drinking more water throughout the day.
   - *Low Sleep:* Suggests maintaining a regular sleep schedule and winding down earlier.
   - *High Screen Time:* Suggests taking regular screen breaks every 45–60 minutes (20-20-20 rule).
   - *Mood Support:* Mindful guidance tailored to the user's emotional state.
9. **SQLite Persistence:** All submitted daily assessments and calculated scores are saved securely in SQLite for the logged-in user.

### 2. Recent Health History
An interactive, responsive table displaying previously saved records:
- **Date**
- **Sleep** (hours)
- **Water** (glasses)
- **Exercise** (minutes)
- **Screen Time** (hours)
- **Mood**
- **Well-being Score** (with colored tier badge)
- **Action** (option to delete an entry)

### 3. User Authentication & Session Security
- User registration (`/register`) with full name, email, and password confirmation.
- Secure sign-in (`/login`) with session management.
- Dynamic navigation bar adjusting between guest links and member actions.
- Route protection (`@login_required`) guarding personal wellness data.
- User logout (`/logout`).

### 4. DTPL & SDG 3 Footer
Includes the dedicated project footer on every page:
**"DTPL Lab Project - SDG 3: Good Health and Well-being"**

---

## 🚀 How to Run the Project

### Option 1: Quick Launch (Windows)
Double-click [**`run.bat`**](file:///C:/Users/CHARMIKA/.gemini/antigravity/scratch/smart_health_wellbeing/run.bat) inside the project folder, or run:
```powershell
cd C:\Users\CHARMIKA\.gemini\antigravity\scratch\smart_health_wellbeing
.\run.bat
```

### Option 2: Standard Command Line
1. Open PowerShell or Command Prompt.
2. Navigate to the project directory:
   ```powershell
   cd C:\Users\CHARMIKA\.gemini\antigravity\scratch\smart_health_wellbeing
   ```
3. Run the application:
   ```powershell
   python app.py
   ```
   *(Or if using the installed Python 3.12 path: `& "$env:LOCALAPPDATA\Programs\Python\Python312-arm64\python.exe" app.py`)*
4. Open your web browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```

---

## 🧪 Verification & Testing Checklist

- [x] **Form Works:** Accepts numeric inputs for Sleep, Water, Exercise, Screen Time, and dropdown for Mood.
- [x] **Score Calculation:** Correctly computes score out of 100 based on all 5 parameters (e.g. 93/100).
- [x] **Suggestions Appear:** Dynamic suggestions appear beneath the score reflecting entered values.
- [x] **SQLite Persistence:** Submitting saves records to `smart_health.db` under the logged-in user's account.
- [x] **Recent Health History:** Displays Date, Sleep, Water, Exercise, Screen Time, Mood, and Well-being Score.
- [x] **Clean DOM:** No Python, JavaScript, or Firebase code is displayed as visible text at the bottom or anywhere on the page.
- [x] **SDG 3 Footer:** "DTPL Lab Project - SDG 3: Good Health and Well-being" displayed prominently in the footer.
