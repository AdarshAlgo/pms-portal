"""
HTML Database Viewer Generator.
Reads all database tables and outputs a standalone, beautiful HTML dashboard (DATABASE_VIEWER.html)
that displays all tables, rows, columns, and records visually with search & filtering.
"""

import os
import sqlite3
import json
from datetime import datetime

def generate_html_viewer():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'project_monitoring.db')

    if not os.path.exists(db_path):
        from seed import seed_database
        seed_database()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]

    db_data = {}
    total_records = 0

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [col[1] for col in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        total_records += len(rows)

        formatted_rows = []
        for r in rows:
            formatted_rows.append([str(item) if item is not None else '<span class="text-gray-400 italic">NULL</span>' for item in r])

        db_data[table] = {
            'columns': columns,
            'rows': formatted_rows,
            'count': len(rows)
        }

    conn.close()

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Viewer - Project Monitoring System</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .table-tab.active {{
            background-color: #4f46e5;
            color: #ffffff;
            font-weight: 600;
        }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col font-sans">
    
    <!-- Top Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md">
                    <i class="fas fa-database text-lg"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg text-slate-900 leading-tight">Database Viewer & Explorer</h1>
                    <p class="text-xs text-slate-500">Project Progress Monitoring & Evaluation System &bull; Live Snapshot</p>
                </div>
            </div>

            <div class="flex items-center space-x-4">
                <div class="text-right">
                    <span class="text-xs text-slate-500">Total Tables: <strong class="text-indigo-600">{len(tables)}</strong></span>
                    <span class="mx-1 text-slate-300">|</span>
                    <span class="text-xs text-slate-500">Total Rows: <strong class="text-emerald-600">{total_records}</strong></span>
                </div>
                <button onclick="window.location.reload()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors flex items-center">
                    <i class="fas fa-sync-alt mr-1.5"></i> Refresh
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        <!-- Sidebar Table List -->
        <div class="lg:col-span-1 space-y-4">
            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <h2 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Database Tables</h2>
                
                <div class="space-y-1" id="tableList">
                    <!-- Populated by JS -->
                </div>
            </div>

            <!-- Database Info Box -->
            <div class="bg-indigo-50/70 border border-indigo-100 rounded-xl p-4 text-xs text-indigo-900 space-y-2">
                <div class="font-bold flex items-center">
                    <i class="fas fa-info-circle mr-1.5 text-indigo-600"></i> Database Details
                </div>
                <p>File: <code class="bg-white/80 px-1 py-0.5 rounded text-indigo-800 font-mono">project_monitoring.db</code></p>
                <p>Generated: <span class="text-slate-600">{datetime.now().strftime('%b %d, %Y - %I:%M %p')}</span></p>
                <p>Engine: <span class="font-semibold text-indigo-700">SQLite 3 / MySQL Compatible</span></p>
            </div>
        </div>

        <!-- Table Data Content Area -->
        <div class="lg:col-span-3 space-y-4">
            
            <!-- Controls bar -->
            <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 class="text-xl font-bold text-slate-900 flex items-center">
                        <i class="fas fa-table mr-2 text-indigo-500"></i>
                        <span id="currentTableName">Table</span>
                        <span id="currentRowCount" class="ml-3 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-100 text-indigo-700">0 rows</span>
                    </h2>
                </div>

                <div class="w-full sm:w-72 relative">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                        <i class="fas fa-search text-xs"></i>
                    </div>
                    <input type="text" id="searchInput" oninput="filterTable()" placeholder="Search in this table..." class="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                </div>
            </div>

            <!-- Table Card -->
            <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div class="overflow-x-auto max-h-[650px]" id="tableContainer">
                    <!-- Populated by JS -->
                </div>
            </div>

        </div>

    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        Project Progress Monitoring & Evaluation System &bull; UN SDG 9 Aligned
    </footer>

    <!-- Data Injection -->
    <script>
        const rawDbData = {json.dumps(db_data)};
        let activeTable = Object.keys(rawDbData)[0] || '';

        function renderSidebar() {{
            const listEl = document.getElementById('tableList');
            listEl.innerHTML = '';

            Object.keys(rawDbData).forEach(tableName => {{
                const info = rawDbData[tableName];
                const btn = document.createElement('button');
                btn.className = `w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex justify-between items-center table-tab ${{tableName === activeTable ? 'active' : 'text-slate-600 hover:bg-slate-100'}}`;
                btn.innerHTML = `
                    <span class="truncate"><i class="fas fa-table text-xs mr-2 opacity-60"></i>${{tableName}}</span>
                    <span class="text-xs px-2 py-0.5 rounded-full ${{tableName === activeTable ? 'bg-indigo-700 text-white' : 'bg-slate-100 text-slate-600'}} font-medium">${{info.count}}</span>
                `;
                btn.onclick = () => {{
                    activeTable = tableName;
                    document.getElementById('searchInput').value = '';
                    renderSidebar();
                    renderTable();
                }};
                listEl.appendChild(btn);
            }});
        }}

        function renderTable(filterText = '') {{
            if (!activeTable || !rawDbData[activeTable]) return;

            const info = rawDbData[activeTable];
            document.getElementById('currentTableName').textContent = activeTable;
            document.getElementById('currentRowCount').textContent = `${{info.count}} records`;

            const container = document.getElementById('tableContainer');
            
            if (info.count === 0) {{
                container.innerHTML = `
                    <div class="p-12 text-center text-slate-400">
                        <i class="fas fa-inbox text-4xl mb-3 opacity-40"></i>
                        <p class="font-medium text-sm">Table '${{activeTable}}' is empty</p>
                    </div>
                `;
                return;
            }}

            const lowerFilter = filterText.toLowerCase();
            const filteredRows = info.rows.filter(row => {{
                if (!lowerFilter) return true;
                return row.some(cell => cell.toLowerCase().includes(lowerFilter));
            }});

            let html = `
                <table class="w-full text-left border-collapse text-xs">
                    <thead>
                        <tr class="bg-slate-50 border-b border-slate-200 text-slate-600 uppercase tracking-wider font-semibold sticky top-0 z-10">
                            ${{info.columns.map(col => `<th class="px-4 py-3 whitespace-nowrap bg-slate-100">${{col}}</th>`).join('')}}
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
            `;

            if (filteredRows.length === 0) {{
                html += `
                    <tr>
                        <td colspan="${{info.columns.length}}" class="p-8 text-center text-slate-400">
                            No records matching "${{filterText}}"
                        </td>
                    </tr>
                `;
            }} else {{
                filteredRows.forEach((row, idx) => {{
                    html += `<tr class="${{idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}} hover:bg-indigo-50/40 transition-colors">`;
                    row.forEach(cell => {{
                        let cellContent = cell;
                        if (cell.length > 100) {{
                            cellContent = `<span title="${{cell.replace(/"/g, '&quot;')}}">${{cell.substring(0, 95)}}...</span>`;
                        }}
                        html += `<td class="px-4 py-3 whitespace-nowrap text-slate-700 font-mono">${{cellContent}}</td>`;
                    }});
                    html += `</tr>`;
                }});
            }}

            html += `</tbody></table>`;
            container.innerHTML = html;
        }}

        function filterTable() {{
            const text = document.getElementById('searchInput').value;
            renderTable(text);
        }}

        // Initial setup
        renderSidebar();
        renderTable();
    </script>
</body>
</html>
"""

    output_path = os.path.join(base_dir, 'DATABASE_VIEWER.html')
    explorer_path = os.path.join(base_dir, 'DATABASE_EXPLORER.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    with open(explorer_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✅ Generated standalone database viewer: {output_path}")
    print(f"✅ Generated standalone database explorer: {explorer_path}")
    return output_path

if __name__ == '__main__':
    generate_html_viewer()
