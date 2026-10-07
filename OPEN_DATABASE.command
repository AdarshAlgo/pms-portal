#!/bin/bash
# ==============================================================================
# 🗄️ 1-CLICK DATABASE VIEWER & EXPLORER FOR ALL USERS AND PROJECTS
# Double-click this file in Finder to view all database records!
# ==============================================================================

cd "$(dirname "$0")"

echo "======================================================================"
echo "         📊 OPENING VISUAL DATABASE EXPLORER & VIEWER"
echo "======================================================================"
echo ""

# Ensure latest database records are exported
if [ -d "venv" ]; then
    ./venv/bin/python export_db_viewer.py
else
    python3 export_db_viewer.py
fi

echo ""
echo "👉 Opening visual Database Viewer in your default web browser..."
open "DATABASE_EXPLORER.html"

echo ""
echo "----------------------------------------------------------------------"
echo "💡 TIP: You can also double-click 'DATABASE_EXPLORER.html' directly"
echo "        in this folder at any time to inspect all users & projects!"
echo "----------------------------------------------------------------------"
echo ""

# Also print terminal summary
if [ -d "venv" ]; then
    ./venv/bin/python view_db.py
fi

echo ""
echo "Press any key or close this window to exit."
read -n 1 -s
