# AMAD (Misère Dama / Suicide Checkers) ♟️📸

> A Python implementation of **AMAD** (Misère Dama) featuring webcam face tracking for custom piece textures and sound effects.

---

## 📌 Game Concept & Win Conditions

In **AMAD**, your objective is inverted: **your goal is to lose all your pieces first**.

* **Forced Captures:** If a jump is available on your turn, you **must** take it. Use this rule strategically to sacrifice your pieces.
* **Win Conditions:**
  1. **Lose All Pieces:** First player with zero pieces remaining on the board wins.
  2. **No Legal Moves:** If a player has no valid moves left on their turn, they win.
  3. **Time Out:** If a player's 5-minute timer hits zero, the opposing player wins.

---

## 💻 Prerequisites & Requirements

Ensure you have **Python 3.8+** installed along with a working webcam.

### Dependencies
* `pygame` (Game rendering & audio loop)
* `opencv-python` (Webcam video capture & face detection)

---

## 🚀 How to Run the Game

### 1. Clone the Repository
bash
   git clone [https://github.com/your-username/AMAD.git](https://github.com/your-username/AMAD.git)
   cd AMAD

### 2. Set Up Virtual Environment (Recommended)
Bash
# Create environment
   python -m venv venv

# Activate on Windows PowerShell:
   .\venv\Scripts\activate

# Activate on macOS/Linux:
   source venv/bin/activate

### 3. Install Required Packages
Bash
pip install pygame opencv-python

### 4. Start the Game
Run the entry point file from the root folder:

Bash
   python main.py