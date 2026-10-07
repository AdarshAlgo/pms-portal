/**
 * Capstone Project Progress Monitoring & Evaluation System
 * Global Chart.js Configuration & Reusable Chart Builders
 * Design Standard: Linear • Stripe • Vercel • Apple Synthesis
 * Features: Strictly Horizontal X-Axis Labels (0° Rotation), Auto-Wrapping, Glassmorphic Tooltips
 */

// Helper to check dark mode state
function isDarkModeActive() {
    return document.documentElement.classList.contains('dark');
}

// Dynamic theme palette for Chart.js
function getChartThemeColors() {
    const dark = isDarkModeActive();
    return {
        isDark: dark,
        textColor: dark ? '#94a3b8' : '#475569',
        titleColor: dark ? '#f8fafc' : '#0f172a',
        gridColor: dark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(15, 23, 42, 0.06)',
        borderColor: dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(226, 232, 240, 0.8)',
        tooltipBg: dark ? 'rgba(14, 16, 21, 0.94)' : 'rgba(15, 23, 42, 0.94)',
        indigo: '#6366f1',
        emerald: '#10b981',
        purple: '#a855f7',
        amber: '#f59e0b',
        rose: '#f43f5e',
        cyan: '#06b6d4',
        slateLight: dark ? '#1e293b' : '#f1f5f9'
    };
}

/**
 * Utility: Split long label strings into multi-line arrays to prevent slanting
 * When maxRotation: 0 is set, Chart.js neatly stacks array items vertically.
 */
function wrapLabel(label, maxChars = 15) {
    if (!label) return '';
    if (Array.isArray(label)) return label;
    
    // Check if label contains parentheses or colons for natural split points
    if (label.includes('(') && label.includes(')')) {
        const parts = label.split('(');
        return [parts[0].trim(), '(' + parts[1]];
    }
    if (label.includes(':')) {
        const parts = label.split(':');
        return [parts[0].trim(), parts.slice(1).join(':').trim()];
    }

    if (label.length <= maxChars) return label;

    const words = label.split(' ');
    const lines = [];
    let currentLine = '';

    words.forEach(word => {
        if ((currentLine + ' ' + word).trim().length <= maxChars) {
            currentLine = (currentLine + ' ' + word).trim();
        } else {
            if (currentLine) lines.push(currentLine);
            currentLine = word;
        }
    });
    if (currentLine) lines.push(currentLine);

    return lines.length > 0 ? lines : label;
}

// Global Chart.js Defaults
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.font.weight = '500';
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.color = '#64748b';

    // Global layout & element curves
    Chart.defaults.elements.bar.borderRadius = 8;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.elements.point.hoverRadius = 6;

    // Strict horizontal x-axis orientation (no slanting)
    if (!Chart.defaults.scales) Chart.defaults.scales = {};
    if (!Chart.defaults.scales.x) Chart.defaults.scales.x = {};
    if (!Chart.defaults.scales.x.ticks) Chart.defaults.scales.x.ticks = {};
    Chart.defaults.scales.x.ticks.maxRotation = 0;
    Chart.defaults.scales.x.ticks.minRotation = 0;
    Chart.defaults.scales.x.ticks.autoSkip = false;

    // Glassmorphic modern tooltip defaults
    if (!Chart.defaults.plugins) Chart.defaults.plugins = {};
    if (!Chart.defaults.plugins.tooltip) Chart.defaults.plugins.tooltip = {};
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(14, 16, 21, 0.92)';
    Chart.defaults.plugins.tooltip.titleFont = { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: '700' };
    Chart.defaults.plugins.tooltip.bodyFont = { family: "'Plus Jakarta Sans', sans-serif", size: 11, weight: '500' };
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.boxPadding = 4;
    Chart.defaults.plugins.tooltip.usePointStyle = true;
    Chart.defaults.plugins.tooltip.callbacks = {
        title: function(items) {
            if (!items || !items.length) return '';
            const raw = items[0].label;
            return Array.isArray(raw) ? raw.join(' ') : raw;
        }
    };
}

/**
 * Initialize milestone progress doughnut chart
 */
function initProgressChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const colors = getChartThemeColors();
    
    return new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'In Review', 'Revision Req', 'Pending'],
            datasets: [{
                data: [data.completed || 0, data.in_review || 0, data.revision || 0, data.pending || 0],
                backgroundColor: [colors.emerald, colors.amber, colors.rose, colors.slateLight],
                borderWidth: 0,
                borderRadius: 4,
                hoverOffset: 6
            }]
        },
        options: {
            cutout: '74%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 16,
                        color: colors.textColor,
                        font: { size: 11, weight: '600' }
                    }
                }
            }
        }
    });
}

/**
 * Initialize milestone burndown line chart  
 */
function initBurndownChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const colors = getChartThemeColors();
    
    return new Chart(canvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: (data.labels || []).map(l => wrapLabel(l)),
            datasets: [
                {
                    label: 'Ideal Target',
                    data: data.ideal || [],
                    borderColor: colors.isDark ? '#64748b' : '#94a3b8',
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0,
                    pointRadius: 0
                },
                {
                    label: 'Actual Burndown',
                    data: data.actual || [],
                    borderColor: colors.indigo,
                    backgroundColor: colors.isDark ? 'rgba(99, 102, 241, 0.15)' : 'rgba(99, 102, 241, 0.08)',
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: colors.indigo,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4
                }
            ]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: colors.textColor },
                    grid: { color: colors.gridColor },
                    title: { display: true, text: 'Milestones Remaining', color: colors.textColor }
                },
                x: {
                    ticks: { 
                        color: colors.textColor,
                        maxRotation: 0,
                        minRotation: 0,
                        autoSkip: false
                    },
                    grid: { color: colors.gridColor }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: colors.textColor,
                        usePointStyle: true,
                        font: { size: 11, weight: '600' }
                    }
                }
            }
        }
    });
}

/**
 * Initialize department distribution doughnut chart
 */
function initDepartmentChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const colors = getChartThemeColors();
    
    return new Chart(canvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: [colors.indigo, colors.purple, colors.emerald, colors.amber, colors.cyan],
                borderWidth: 0,
                hoverOffset: 6
            }]
        },
        options: {
            cutout: '72%',
            plugins: {
                legend: { 
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        color: colors.textColor,
                        usePointStyle: true,
                        font: { size: 10, weight: '600' }
                    }
                }
            }
        }
    });
}

// Global hook for page-specific initialization
window.ChartsHelper = {
    wrapLabel,
    getChartThemeColors,
    initProgressChart,
    initBurndownChart,
    initDepartmentChart
};
