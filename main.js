/**
 * Smart Health and Well-Being - DTPL Project
 * Main Frontend Script: Interactive Well-being Assessment, Real-time Score Calculation,
 * Dynamic Suggestions, and Navigation Management.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Navigation Toggle
  const navToggle = document.getElementById('navToggle');
  const navbar = document.querySelector('.navbar');

  if (navToggle && navbar) {
    navToggle.addEventListener('click', () => {
      navbar.classList.toggle('menu-open');
      const expanded = navbar.classList.contains('menu-open');
      navToggle.setAttribute('aria-expanded', expanded);
    });

    // Close menu when clicking outside or clicking any nav link
    document.addEventListener('click', (e) => {
      if (!navbar.contains(e.target)) {
        navbar.classList.remove('menu-open');
      }
    });

    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach((link) => {
      link.addEventListener('click', () => {
        navbar.classList.remove('menu-open');
      });
    });
  }

  // Interactive Live Water Intake Demo in Hero Dashboard Preview
  const waterBtn = document.getElementById('quickWaterAddBtn');
  const waterValueEl = document.getElementById('previewWaterValue');
  const waterFillEl = document.getElementById('previewWaterFill');

  if (waterBtn && waterValueEl && waterFillEl) {
    let currentGlasses = 7;
    const targetGlasses = 8;

    waterBtn.addEventListener('click', () => {
      if (currentGlasses < 12) {
        currentGlasses += 1;
        waterValueEl.innerHTML = `${currentGlasses} <span style="font-size: 0.85rem; font-weight: 500;">glasses</span>`;
        const percentage = Math.min(100, Math.round((currentGlasses / targetGlasses) * 100));
        waterFillEl.style.width = `${percentage}%`;

        waterBtn.textContent = '✓ Added!';
        setTimeout(() => {
          waterBtn.textContent = '+ 1 Glass';
        }, 1200);
      } else {
        waterBtn.textContent = 'Target Met!';
      }
    });
  }

  // Auto-dismiss Flash Messages
  const flashMessages = document.querySelectorAll('.flash-message');
  flashMessages.forEach((msg) => {
    setTimeout(() => {
      msg.style.transition = 'opacity 0.5s ease';
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 500);
    }, 5000);
  });

  // -----------------------------------------------------------------
  // Well-being Score Calculation & Suggestions Helper Functions
  // -----------------------------------------------------------------
  function calculateScore(sleep, water, exercise, screen, mood) {
    let score = 0;

    // 1. Sleep (Max 25 pts)
    if (sleep >= 7.0 && sleep <= 9.0) {
      score += 25;
    } else if ((sleep >= 6.0 && sleep < 7.0) || (sleep > 9.0 && sleep <= 10.0)) {
      score += 18;
    } else if (sleep >= 5.0 && sleep < 6.0) {
      score += 12;
    } else if ((sleep >= 4.0 && sleep < 5.0) || (sleep > 10.0 && sleep <= 11.0)) {
      score += 7;
    } else if (sleep > 0) {
      score += 3;
    }

    // 2. Water Intake in glasses (Max 20 pts)
    if (water >= 8) {
      score += 20;
    } else if (water === 7) {
      score += 17;
    } else if (water === 6) {
      score += 14;
    } else if (water === 5) {
      score += 11;
    } else if (water >= 3) {
      score += 7;
    } else if (water >= 1) {
      score += 4;
    }

    // 3. Exercise in minutes (Max 20 pts)
    if (exercise >= 45) {
      score += 20;
    } else if (exercise >= 30) {
      score += 18;
    } else if (exercise >= 20) {
      score += 14;
    } else if (exercise >= 10) {
      score += 9;
    } else if (exercise > 0) {
      score += 4;
    }

    // 4. Screen Time in hours (Max 15 pts) - lower is better
    if (screen <= 2.0) {
      score += 15;
    } else if (screen <= 4.0) {
      score += 13;
    } else if (screen <= 6.0) {
      score += 10;
    } else if (screen <= 8.0) {
      score += 6;
    } else {
      score += 2;
    }

    // 5. Mood (Max 20 pts)
    const m = String(mood || '').toLowerCase();
    if (m.includes('excellent')) {
      score += 20;
    } else if (m.includes('good') || m.includes('great') || m.includes('energized')) {
      score += 17;
    } else if (m.includes('neutral') || m.includes('balanced') || m.includes('calm')) {
      score += 13;
    } else if (m.includes('stressed')) {
      score += 7;
    } else if (m.includes('sad') || m.includes('tired')) {
      score += 5;
    } else {
      score += 13;
    }

    return Math.min(100, Math.max(0, score));
  }

  function generateSuggestions(sleep, water, exercise, screen, mood) {
    const suggestions = [];

    // 1. Sleep
    if (sleep < 7.0) {
      suggestions.push(`Sleep duration is low (${sleep} hrs): Suggest maintaining a regular sleep schedule and winding down 30 minutes earlier without screens.`);
    } else if (sleep > 9.0) {
      suggestions.push(`Extended sleep logged (${sleep} hrs): Ensure a steady 7–9 hours sleep window for optimal daytime alertness.`);
    } else {
      suggestions.push(`Optimal sleep (${sleep} hrs): Excellent! 7–9 hours of sleep promotes immune health, cell repair, and mental focus.`);
    }

    // 2. Water
    if (water < 8) {
      suggestions.push(`Water intake is low (${water} glasses): Suggest drinking more water throughout the day to reach the recommended 8 glasses.`);
    } else {
      suggestions.push(`Great hydration (${water} glasses): You achieved your daily hydration goal, supporting digestion and stamina.`);
    }

    // 3. Exercise
    if (exercise < 30) {
      suggestions.push(`Exercise duration is low (${exercise} mins): Suggest increasing physical activity to at least 30 minutes daily (e.g. brisk walking, jogging, or cycling).`);
    } else {
      suggestions.push(`Active lifestyle (${exercise} mins): Superb exercise duration! Regular physical movement boosts cardiovascular fitness and relieves stress.`);
    }

    // 4. Screen Time
    if (screen > 6.0) {
      suggestions.push(`Screen time is high (${screen} hrs): Suggest taking regular screen breaks every 45–60 minutes (20-20-20 rule) to reduce eye strain and fatigue.`);
    } else if (screen > 4.0) {
      suggestions.push(`Moderate screen time (${screen} hrs): Remember to take brief pauses away from the monitor during long study/work periods.`);
    } else {
      suggestions.push(`Healthy screen exposure (${screen} hrs): Keeping screen time balanced helps protect vision and promotes better sleep quality.`);
    }

    // 5. Mood
    const m = String(mood || '').toLowerCase();
    if (m.includes('stressed')) {
      suggestions.push("Mind & Mood: You noted feeling stressed. Dedicate 10 minutes to deep breathing, gentle stretching, or listening to calming music.");
    } else if (m.includes('sad')) {
      suggestions.push("Mind & Mood: You noted feeling down. Be gentle with yourself today, speak with a supportive friend, or take a gentle nature walk.");
    } else if (m.includes('neutral')) {
      suggestions.push("Mind & Mood: A calm, steady mindset today. Consider an engaging activity or uplifting music to give your day a boost.");
    } else {
      suggestions.push("Mind & Mood: Positive and uplifting mindset! Channel this positive energy into your daily goals.");
    }

    return suggestions;
  }

  // -----------------------------------------------------------------
  // Landing Page Interactive Assessment Preview
  // -----------------------------------------------------------------
  const homeCalcBtn = document.getElementById('homeBtnCalculateScore');
  if (homeCalcBtn) {
    const homeSleep = document.getElementById('home_sleep_hours');
    const homeWater = document.getElementById('home_water_glasses');
    const homeExercise = document.getElementById('home_exercise_mins');
    const homeScreen = document.getElementById('home_screen_time_hours');
    const homeMood = document.getElementById('home_mood');

    const homeScoreHighlight = document.getElementById('homeScoreHighlight');
    const homeScoreBadge = document.getElementById('homeScoreBadge');
    const homeProgressBar = document.getElementById('homeScoreProgressBar');
    const homeSuggestionsList = document.getElementById('homeSuggestionsList');

    function updateHomeAssessment() {
      const sleep = parseFloat(homeSleep?.value || 8.0);
      const water = parseInt(homeWater?.value || 8, 10);
      const exercise = parseInt(homeExercise?.value || 35, 10);
      const screen = parseFloat(homeScreen?.value || 4.0);
      const mood = homeMood?.value || 'Good 🙂';

      const score = calculateScore(sleep, water, exercise, screen, mood);
      const tips = generateSuggestions(sleep, water, exercise, screen, mood);

      if (homeScoreHighlight) {
        homeScoreHighlight.textContent = `${score}/100`;
      }
      if (homeProgressBar) {
        homeProgressBar.style.width = `${score}%`;
      }
      if (homeScoreBadge) {
        if (score >= 80) {
          homeScoreBadge.innerHTML = '<span class="score-badge-sm score-optimal">Optimal Health Tier</span>';
        } else if (score >= 60) {
          homeScoreBadge.innerHTML = '<span class="score-badge-sm score-good">Good Balance Tier</span>';
        } else {
          homeScoreBadge.innerHTML = '<span class="score-badge-sm score-warning">Attention Needed</span>';
        }
      }

      if (homeSuggestionsList) {
        homeSuggestionsList.innerHTML = '';
        tips.forEach((tip) => {
          const li = document.createElement('li');
          li.className = 'suggestion-item';
          li.innerHTML = `<span class="suggestion-bullet">✓</span><span>${tip}</span>`;
          homeSuggestionsList.appendChild(li);
        });
      }
    }

    homeCalcBtn.addEventListener('click', updateHomeAssessment);
    [homeSleep, homeWater, homeExercise, homeScreen, homeMood].forEach((input) => {
      if (input) {
        input.addEventListener('input', updateHomeAssessment);
        input.addEventListener('change', updateHomeAssessment);
      }
    });
  }

  // -----------------------------------------------------------------
  // User Dashboard Assessment Form Real-time Preview & Submission
  // -----------------------------------------------------------------
  const dashForm = document.getElementById('assessmentForm');
  if (dashForm) {
    const sleepInput = document.getElementById('sleep_hours');
    const waterInput = document.getElementById('water_glasses');
    const exerciseInput = document.getElementById('exercise_mins');
    const screenInput = document.getElementById('screen_time_hours');
    const moodInput = document.getElementById('mood');

    const scoreHighlightVal = document.getElementById('scoreHighlightVal');
    const scoreBadgeIndicator = document.getElementById('scoreBadgeIndicator');
    const scoreProgressBar = document.getElementById('scoreProgressBar');
    const suggestionsList = document.getElementById('suggestionsList');

    function updateDashboardPreview() {
      const sleep = parseFloat(sleepInput?.value || 7.0);
      const water = parseInt(waterInput?.value || 8, 10);
      const exercise = parseInt(exerciseInput?.value || 30, 10);
      const screen = parseFloat(screenInput?.value || 4.0);
      const mood = moodInput?.value || 'Good 🙂';

      const score = calculateScore(sleep, water, exercise, screen, mood);
      const tips = generateSuggestions(sleep, water, exercise, screen, mood);

      if (scoreHighlightVal) {
        scoreHighlightVal.textContent = `${score}/100`;
      }
      if (scoreProgressBar) {
        scoreProgressBar.style.width = `${score}%`;
      }
      if (scoreBadgeIndicator) {
        if (score >= 80) {
          scoreBadgeIndicator.innerHTML = '<span class="score-badge-sm score-optimal">Optimal Health Tier</span>';
        } else if (score >= 60) {
          scoreBadgeIndicator.innerHTML = '<span class="score-badge-sm score-good">Good Balance Tier</span>';
        } else {
          scoreBadgeIndicator.innerHTML = '<span class="score-badge-sm score-warning">Attention Needed</span>';
        }
      }

      if (suggestionsList) {
        suggestionsList.innerHTML = '';
        tips.forEach((tip) => {
          const li = document.createElement('li');
          li.className = 'suggestion-item';
          li.innerHTML = `<span class="suggestion-bullet">✓</span><span>${tip}</span>`;
          suggestionsList.appendChild(li);
        });
      }
    }

    // Live update when user changes inputs
    [sleepInput, waterInput, exerciseInput, screenInput, moodInput].forEach((input) => {
      if (input) {
        input.addEventListener('input', updateDashboardPreview);
        input.addEventListener('change', updateDashboardPreview);
      }
    });
  }
});
