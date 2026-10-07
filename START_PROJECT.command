#!/bin/bash
# ==============================================================================
# 🚀 1-CLICK LAUNCHER FOR PROJECT PROGRESS MONITORING SYSTEM
# Double-click this file in Finder to launch the web app directly!
# ==============================================================================

cd "$(dirname "$0")"

echo "======================================================================"
echo "      🎓 LAUNCHING PROJECT PROGRESS MONITORING & EVALUATION SYSTEM"
echo "======================================================================"
echo ""

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "⚠️ Virtual environment not found. Creating one now..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python seed.py
fi

echo "✅ Database & Core Services Ready"
echo "🌐 Starting web server on http://127.0.0.1:5000 ..."
echo ""
echo "----------------------------------------------------------------------"
echo "🔑 PRE-CONFIGURED INDIAN DEMO CREDENTIALS (All Passwords: password123):"
echo "   🔴 Admin 1:   admin@university.edu    (Dr. Rajeshwar Sharma, Dean)"
echo "   🔴 Admin 2:   admin2@university.edu   (Prof. Sunita Rao, Coordinator)"
echo "   🟡 Faculty 1: dr.verma@university.edu (Dr. Anand Verma, CS Guide)"
echo "   🟡 Faculty 2: dr.iyer@university.edu  (Dr. Meenakshi Iyer, IT Guide)"
echo "   🟡 Faculty 3: dr.patel@university.edu (Dr. Vikram Patel, Robotics)"
echo "   🟢 Student 1: student1@university.edu (Aarav Sharma - Krishi-Drishti)"
echo "   🟢 Student 2: student2@university.edu (Priya Patel - Kavach Telemetry)"
echo "   🟢 Student 3: student3@university.edu (Rohan Kulkarni - Jal-Drishti)"
echo "   🟢 Student 4: student4@university.edu (Ananya Reddy - Urja-Net)"
echo "   🟢 Student 5: student5@university.edu (Vikramaditya Singh - Swasthya-AI)"
echo "----------------------------------------------------------------------"
echo ""
echo "👉 Opening your browser now..."
echo "ℹ️  To stop the project, simply close this terminal window."
echo ""

(sleep 1.5 && open "http://127.0.0.1:5000") &

./venv/bin/python run.py
