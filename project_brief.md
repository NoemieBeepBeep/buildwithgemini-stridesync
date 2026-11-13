# My agent: StrideSync (Mindful Run Coach)
One-liner: A conversational running coach that helps busy women run for mental wellbeing while dynamically adapting workouts to daily friction (cramps, fatigue, low mood) with zero-research simplicity, layered consent-first privacy, and an anti-guilt mindset.

## Target Audience & Core Principles
- **Audience:** Busy women who lack time to research sports physiology or pay for coaching, running primarily for mental health and stress relief while navigating daily friction (menstrual cramps, PMS fatigue, hormonal fluctuations, overwhelmed bandwidth).
- **Zero-Research Simplicity:** Bite-sized actions, clear RPE targets, and 10-second practical care tips—never sports jargon or long paragraphs.
- **Anti-Guilt "Compassionate Consistency":** A 10-minute walk/jog or cramp rest day counts as showing up and preserves momentum.
- **Privacy by Design:** Layered, purpose-specific consent; zero silent data extraction; granular user-controlled data deletion.

## Agent Architecture (Single Fast ADK Root Coordinator)
Implement ONE fast ADK root agent with structured internal roles (avoid slow multi-agent chains):
1. **The Gatherer & Gatekeeper:** Enforces consent gates, manages profile setup, and executes granular data deletion.
2. **The Scientist (Female Physiology):** Translates cycle phase, symptoms, life stage, and recovery metrics into load adjustments and a "10-Second Body Tip".
3. **The Psychologist (Sports & Mood Advisor):** Prevents toxic positivity, explains how today's movement regulates mood/cortisol, and prescribes one concrete in-run mental trick (e.g., 5-4-3-2-1 grounding, cadence counting, 10-minute trial run). Strictly non-diagnostic.
4. **The Coach (Workout Builder):** Formats structured runs (Warm-up, Main Set, Cool-down, RPE) with a 1-tap "Make it gentler" bailout.
5. **The Cheerleader (Voice & Tone):** Delivers responses in a warm, grounded, empathetic tone.

## 5-Step Sequential Onboarding Flow
1. **Step 1 — Privacy Notice & Core Consent Gate:** Plain-English Privacy Notice explaining what is collected, why, where it lives (Firestore / user-controlled app memory, never sold), and deletion rights, with `I Agree & Continue` vs. `Decline` buttons.
2. **Step 2 — Running Goals & Availability:** Primary goal (mental wellbeing, 5K, consistency) and weekly days available.
3. **Step 3 — Voluntary Health & Cycle Profile:** Optional fields (health issues/injuries, life stage, last period start date) with a prominent `Skip this step` button.
4. **Step 4 — Optional Google Health Sync:** Separate consent card asking permission to connect to Google Health.
   - `Connect & Sync Google Health`: Imports a realistic 14-day dummy Google Health dataset (`dummy_google_health_profile.json` containing 6 past walks/runs plus slightly elevated resting HR and short sleep) into user memory.
   - `Skip & Enter Manually`: Keeps synced feed empty and uses local/Firestore manual logging only.
5. **Step 5 — Personalized Home Page Dashboard:** Full web app home page (not a chat-only view) featuring:
   - Top bar with **"Privacy & Data Vault"** button (Privacy Notice + disconnect Google Health + granular deletion by category, date range, or full wipe).
   - **Today's Mindful Check-In Hero:** 1-Tap "Excuse Translator" quick chips (`Cramps / Heavy`, `PMS / Low Mood`, `Zero Sleep / Overwhelmed`, `Feeling Good`) + **3-Block Daily Run Card** (Mood & Body Check, Coach's Workout + `"Make it gentler"` bailout, Psychologist's Mind Trick & Scientist's 10-Second Care Tip).
   - **Activity History & Patterns:** Feed of walks and runs (from Google Health sync or manual `+ Log Workout` entries) + Compassionate Consistency momentum tracker.
   - **Slide-Over "Ask Coach" Chat Drawer:** Full conversational access to StrideSync without cluttering the dashboard.

## Tool Coverage
- **Memory & Storage:** Firestore persistence via Firebase MCP storing user profile, goals, consented logs, synced health datasets, and session context.
- **Tools:**
  - `record_consent`: Records upfront explicit consent decision.
  - `save_user_profile`: Stores running goals, availability, and optional voluntary health/cycle info.
  - `sync_google_health_demo`: Imports 14-day dummy Google Health dataset (walks, runs, sleep, resting HR).
  - `log_manual_workout`: Records manual workout entries (`+ Log Workout`).
  - `save_session_context`: Logs daily check-ins (symptoms, mood, friction).
  - `delete_user_data`: Granular deletion tool supporting `all`, `by_category` (e.g., `symptoms_and_mood`, `workout_logs`, `profile`), `by_date_range` (`start_date`, `end_date`), and `disconnect_google_health`.
- **Catalog/UI (A2UI & Web Dashboard):**
  - Upfront Privacy Notice & Consent Gate Card
  - Goal & Availability Card
  - Voluntary Health/Cycle Card (with `Skip`)
  - Google Health Sync Permission Card (with `Connect & Sync` vs. `Skip & Enter Manually`)
  - 1-Tap "Excuse Translator" quick chips
  - 3-Block Daily Run Card with "Make it gentler" bailout
  - Privacy & Data Vault modal/drawer
  - Slide-Over "Ask Coach" Chat Drawer
- **Image gen:** Calming visual course preview or milestone badges celebrating consistency (n/a for core daily text loop, stretch visual).
- **Sandbox:** n/a (Calculations are straightforward pacing/RPE adjustments, avoiding sandbox latency).

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Firestore persistence via Firebase MCP, Google Health sync demo, A2UI cards for 5-step onboarding, Privacy Vault, and personalized dashboard.
