/**
 * PMS Portal - Elite Interactive Canvas & UI Motion Engine
 * Inspired by Stripe.com Modern Web Architecture
 * ------------------------------------------------------------------
 * 1. Interactive Ambient Mesh Gradient Canvas (Hero Background)
 * 2. Radial Particle Telemetry Network & Starburst Visual Canvas
 * 3. Viewport Scroll-Triggered Animated Counting Numbers
 * 4. Interactive Product Dashboard Mockup (Tabs, Hotspots, Rubric Sliders)
 * 5. GSAP Micro-Interactions & Scroll Entrance Animations
 */

(function () {
    'use strict';

    // =========================================================================
    // 1. DYNAMIC INTERACTIVE MESH GRADIENT CANVAS (HERO SECTION)
    // =========================================================================
    function initHeroMeshGradient() {
        const canvas = document.getElementById('hero-gradient-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = (canvas.width = canvas.parentElement.offsetWidth || window.innerWidth);
        let height = (canvas.height = canvas.parentElement.offsetHeight || 600);

        let mouse = { x: width / 2, y: height / 2, targetX: width / 2, targetY: height / 2 };
        let time = 0;

        function resize() {
            if (!canvas.parentElement) return;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            width = canvas.parentElement.offsetWidth || window.innerWidth;
            height = canvas.parentElement.offsetHeight || 600;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = width + 'px';
            canvas.style.height = height + 'px';
            ctx.scale(dpr, dpr);
        }

        window.addEventListener('resize', resize, { passive: true });
        resize();

        // Passive mouse tracking across window
        window.addEventListener('pointermove', function (e) {
            const rect = canvas.getBoundingClientRect();
            mouse.targetX = e.clientX - rect.left;
            mouse.targetY = e.clientY - rect.top;
        }, { passive: true });

        function isDark() {
            return document.documentElement.classList.contains('dark');
        }

        let animationFrameId;
        function render() {
            time += 0.015;

            // Ease mouse position
            mouse.x += (mouse.targetX - mouse.x) * 0.05;
            mouse.y += (mouse.targetY - mouse.y) * 0.05;

            ctx.clearRect(0, 0, width, height);

            const dark = isDark();

            // Render a smooth ambient mesh gradient wave (zero bubbles/orbs)
            const gradient = ctx.createLinearGradient(
                width * 0.1 + Math.sin(time * 0.4) * 80 + (mouse.x - width / 2) * 0.08,
                0,
                width * 0.9 + Math.cos(time * 0.3) * 80 + (mouse.x - width / 2) * 0.08,
                height
            );

            if (dark) {
                gradient.addColorStop(0, 'rgba(99, 102, 241, 0.12)');
                gradient.addColorStop(0.35, 'rgba(168, 85, 247, 0.09)');
                gradient.addColorStop(0.7, 'rgba(56, 189, 248, 0.08)');
                gradient.addColorStop(1, 'rgba(16, 185, 129, 0.05)');
            } else {
                gradient.addColorStop(0, 'rgba(99, 102, 241, 0.15)');
                gradient.addColorStop(0.35, 'rgba(168, 85, 247, 0.12)');
                gradient.addColorStop(0.7, 'rgba(6, 182, 212, 0.10)');
                gradient.addColorStop(1, 'rgba(16, 185, 129, 0.08)');
            }

            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);

            animationFrameId = requestAnimationFrame(render);
        }

        render();
    }

    // =========================================================================
    // 2. RADIAL PARTICLE NETWORK & STARBURST TELEMETRY CANVAS
    // =========================================================================
    function initTelemetryParticleNetwork() {
        const canvas = document.getElementById('telemetry-particles-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = (canvas.width = canvas.parentElement.offsetWidth || window.innerWidth);
        let height = (canvas.height = canvas.parentElement.offsetHeight || 500);

        function resize() {
            if (!canvas.parentElement) return;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            width = canvas.parentElement.offsetWidth || window.innerWidth;
            height = canvas.parentElement.offsetHeight || 500;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = width + 'px';
            canvas.style.height = height + 'px';
            ctx.scale(dpr, dpr);
        }

        window.addEventListener('resize', resize, { passive: true });
        resize();

        let mouse = { x: width / 2, y: height / 2, isHovered: false };
        canvas.parentElement.addEventListener('pointermove', function (e) {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            mouse.isHovered = true;
        }, { passive: true });

        canvas.parentElement.addEventListener('pointerleave', function () {
            mouse.isHovered = false;
        });

        // Initialize Telemetry Nodes (IoT, Code commits, ABET Rubric, AI)
        const nodeCount = 42;
        const nodes = [];
        const types = ['iot', 'commit', 'rubric', 'ai'];

        for (let i = 0; i < nodeCount; i++) {
            const angle = Math.random() * Math.PI * 2;
            const radius = 35 + Math.random() * (Math.min(width, height) * 0.46);
            nodes.push({
                x: width / 2 + Math.cos(angle) * radius,
                y: height / 2 + Math.sin(angle) * radius,
                baseRadius: radius,
                angle: angle,
                angularSpeed: (Math.random() - 0.5) * 0.005,
                size: 2.2 + Math.random() * 2.8,
                type: types[i % types.length],
                pulse: Math.random() * Math.PI
            });
        }

        function isDark() {
            return document.documentElement.classList.contains('dark');
        }

        let rot = 0;
        function render() {
            ctx.clearRect(0, 0, width, height);
            const dark = isDark();
            const cx = width / 2;
            const cy = height / 2;
            rot += 0.002;

            // Draw radiating starburst light beams
            const beamCount = 12;
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(rot);
            for (let b = 0; b < beamCount; b++) {
                const bAngle = (b / beamCount) * Math.PI * 2;
                const bLen = Math.min(width, height) * 0.5;
                ctx.strokeStyle = dark ? 'rgba(99, 102, 241, 0.06)' : 'rgba(99, 102, 241, 0.04)';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(Math.cos(bAngle) * bLen, Math.sin(bAngle) * bLen);
                ctx.stroke();
            }
            ctx.restore();

            // Draw glowing central burst star
            const centralGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 160);
            centralGrad.addColorStop(0, dark ? 'rgba(99, 102, 241, 0.32)' : 'rgba(99, 102, 241, 0.20)');
            centralGrad.addColorStop(0.4, dark ? 'rgba(168, 85, 247, 0.15)' : 'rgba(168, 85, 247, 0.10)');
            centralGrad.addColorStop(1, 'rgba(0,0,0,0)');

            ctx.fillStyle = centralGrad;
            ctx.beginPath();
            ctx.arc(cx, cy, 160, 0, Math.PI * 2);
            ctx.fill();

            // Connect nearby nodes with prominent glowing telemetry rays
            ctx.lineWidth = 1.35;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    const dx = nodes[i].x - nodes[j].x;
                    const dy = nodes[i].y - nodes[j].y;
                    const d = Math.sqrt(dx * dx + dy * dy);

                    if (d < 165) {
                        const proximity = 1 - d / 165;
                        const alpha = Math.max(0, Math.min(0.60, Math.pow(proximity, 0.70) * (dark ? 0.54 : 0.48)));
                        if (alpha > 0.02) {
                            ctx.strokeStyle = dark ? `rgba(0, 242, 254, ${alpha.toFixed(3)})` : `rgba(6, 182, 212, ${alpha.toFixed(3)})`;
                            ctx.beginPath();
                            ctx.moveTo(nodes[i].x, nodes[i].y);
                            ctx.lineTo(nodes[j].x, nodes[j].y);
                            ctx.stroke();
                        }
                    }
                }
            }

            // Draw and update each node
            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                node.angle += node.angularSpeed;
                node.pulse += 0.04;

                // Orbital drift around center
                node.x = cx + Math.cos(node.angle) * node.baseRadius;
                node.y = cy + Math.sin(node.angle) * node.baseRadius;

                // Mouse interactivity
                if (mouse.isHovered) {
                    const mdx = node.x - mouse.x;
                    const mdy = node.y - mouse.y;
                    const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
                    if (mDist < 95 && mDist > 0) {
                        const rep = (1 - mDist / 95) * 24;
                        node.x += (mdx / mDist) * rep;
                        node.y += (mdy / mDist) * rep;
                    }
                }

                // Choose color by node type
                let color;
                if (node.type === 'iot') color = '#06b6d4'; // Cyan (Sensors)
                else if (node.type === 'commit') color = '#6366f1'; // Indigo (Code)
                else if (node.type === 'rubric') color = '#10b981'; // Emerald (Rubric)
                else color = '#a855f7'; // Purple (AI)

                const pulseSize = node.size + Math.sin(node.pulse) * 0.8;

                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(node.x, node.y, Math.max(1, pulseSize), 0, Math.PI * 2);
                ctx.fill();
            }

            requestAnimationFrame(render);
        }

        render();
    }

    // =========================================================================
    // 3. REAL-TIME MILESTONE METRICS COUNTER ANIMATION
    // =========================================================================
    function initMetricsCounters() {
        const counterElements = document.querySelectorAll('[data-counter-target]');
        if (!counterElements.length) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const targetStr = el.getAttribute('data-counter-target');
                    const prefix = el.getAttribute('data-counter-prefix') || '';
                    const suffix = el.getAttribute('data-counter-suffix') || '';
                    const targetNum = parseFloat(targetStr);
                    const duration = 1400; // ms
                    const startTime = performance.now();

                    function updateCount(now) {
                        const progress = Math.min((now - startTime) / duration, 1);
                        // Ease-out cubic
                        const easeOut = 1 - Math.pow(1 - progress, 3);
                        const current = Math.floor(easeOut * targetNum);

                        if (targetStr.includes('.')) {
                            const decimals = targetStr.split('.')[1].length;
                            el.textContent = prefix + (easeOut * targetNum).toFixed(decimals) + suffix;
                        } else {
                            el.textContent = prefix + current + suffix;
                        }

                        if (progress < 1) {
                            requestAnimationFrame(updateCount);
                        } else {
                            el.textContent = prefix + targetStr + suffix;
                        }
                    }

                    requestAnimationFrame(updateCount);
                    obs.unobserve(el);
                }
            });
        }, { threshold: 0.3 });

        counterElements.forEach(el => observer.observe(el));
    }

    // =========================================================================
    // 4. INTERACTIVE CAPSTONE LIVE EVALUATION MOCKUP & CLICKABLE HOTSPOTS
    // =========================================================================
    function initShowcaseDashboard() {
        // Tab switcher
        const tabBtns = document.querySelectorAll('.mockup-tab-btn');
        const tabPanels = {
            burndown: document.getElementById('mockup-panel-burndown'),
            rubric: document.getElementById('mockup-panel-rubric'),
            copilot: document.getElementById('mockup-panel-copilot')
        };

        function switchMockupTab(tabKey) {
            tabBtns.forEach(b => {
                if (b.getAttribute('data-tab') === tabKey) {
                    b.classList.add('bg-indigo-600', 'text-white', 'shadow-xs');
                    b.classList.remove('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-200/60', 'dark:hover:bg-white/10');
                } else {
                    b.classList.remove('bg-indigo-600', 'text-white', 'shadow-xs');
                    b.classList.add('text-slate-600', 'dark:text-slate-400', 'hover:bg-slate-200/60', 'dark:hover:bg-white/10');
                }
            });

            Object.keys(tabPanels).forEach(key => {
                const panel = tabPanels[key];
                if (panel) {
                    if (key === tabKey) {
                        panel.classList.remove('hidden');
                        panel.classList.add('animate-fade-in');
                        if (key === 'burndown' && window.landingChart && typeof window.landingChart.resize === 'function') {
                            setTimeout(() => window.landingChart.resize(), 50);
                        }
                    } else {
                        panel.classList.add('hidden');
                        panel.classList.remove('animate-fade-in');
                    }
                }
            });
        }

        if (tabBtns.length) {
            tabBtns.forEach(btn => {
                btn.addEventListener('click', function () {
                    const tabKey = this.getAttribute('data-tab');
                    switchMockupTab(tabKey);
                });
            });
        }

        // Live Rubric Sliders Real-Time Calculator
        const sliders = [
            { id: 'rubric-slider-rigor', max: 40, weight: 0.40 },
            { id: 'rubric-slider-innov', max: 25, weight: 0.25 },
            { id: 'rubric-slider-code', max: 20, weight: 0.20 },
            { id: 'rubric-slider-viva', max: 15, weight: 0.15 }
        ];

        function calculateLiveRubric() {
            let totalMarks = 0;
            let maxMarks = 100;

            sliders.forEach(s => {
                const input = document.getElementById(s.id);
                const display = document.getElementById(s.id + '-val');
                if (input) {
                    const val = parseFloat(input.value) || 0;
                    totalMarks += val;
                    if (display) display.textContent = val.toFixed(1) + ' / ' + s.max;
                }
            });

            const pct = Math.min(100, Math.max(0, (totalMarks / maxMarks) * 100));
            const scoreDisplay = document.getElementById('mockup-rubric-total-score');
            const gradeBadge = document.getElementById('mockup-rubric-grade-badge');

            if (scoreDisplay) {
                scoreDisplay.textContent = pct.toFixed(1) + '%';
            }

            if (gradeBadge) {
                if (pct >= 90) {
                    gradeBadge.textContent = 'Grade: A+ (Exemplary)';
                    gradeBadge.className = 'px-2.5 py-1 rounded-full text-[10px] font-black bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 transition-all';
                } else if (pct >= 80) {
                    gradeBadge.textContent = 'Grade: A (Proficient)';
                    gradeBadge.className = 'px-2.5 py-1 rounded-full text-[10px] font-black bg-indigo-100 text-indigo-800 dark:bg-indigo-950/80 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-800 transition-all';
                } else if (pct >= 70) {
                    gradeBadge.textContent = 'Grade: B+ (Satisfactory)';
                    gradeBadge.className = 'px-2.5 py-1 rounded-full text-[10px] font-black bg-blue-100 text-blue-800 dark:bg-blue-950/80 dark:text-blue-300 border border-blue-300 dark:border-blue-800 transition-all';
                } else {
                    gradeBadge.textContent = 'Grade: Needs Revision';
                    gradeBadge.className = 'px-2.5 py-1 rounded-full text-[10px] font-black bg-rose-100 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-300 dark:border-rose-800 transition-all';
                }
            }
        }

        sliders.forEach(s => {
            const el = document.getElementById(s.id);
            if (el) {
                el.addEventListener('input', calculateLiveRubric);
            }
        });
        calculateLiveRubric();

        // Clickable & Hoverable Code Hotspots Engine (like Stripe Connect Instances)
        const hotspotCards = document.querySelectorAll('[data-highlight-target]');
        hotspotCards.forEach(card => {
            const targetId = card.getAttribute('data-highlight-target');
            const targetEl = document.getElementById(targetId);
            const tabTarget = card.getAttribute('data-hotspot-tab');

            function activateHotspot(isClick) {
                hotspotCards.forEach(c => c.classList.remove('hotspot-chip-active'));
                card.classList.add('hotspot-chip-active');

                // Remove existing active rings
                document.querySelectorAll('.hotspot-active-ring').forEach(el => {
                    el.classList.remove('hotspot-active-ring');
                });

                if (targetEl) {
                    targetEl.classList.add('hotspot-active-ring');
                }

                // If this hotspot maps to a specific tab, switch to it automatically
                if (tabTarget) {
                    switchMockupTab(tabTarget);
                }
            }

            card.addEventListener('mouseenter', () => {
                activateHotspot(false);
            });

            card.addEventListener('click', (e) => {
                activateHotspot(true);
            });

            card.addEventListener('mouseleave', () => {
                // Keep active if explicitly selected or remove preview highlight
                if (!card.classList.contains('active-pinned')) {
                    if (targetEl) targetEl.classList.remove('hotspot-active-ring');
                }
            });
        });
    }

    // =========================================================================
    // 5. GSAP MICRO-INTERACTIONS & ENTRANCE ANIMATIONS
    // =========================================================================
    function initGSAPAnimations() {
        if (typeof gsap === 'undefined') return;

        try {
            if (typeof ScrollTrigger !== 'undefined') {
                gsap.registerPlugin(ScrollTrigger);
            }

            // Smooth hero text entrance (never hidden or dimmed)
            gsap.fromTo('.gsap-hero-badge', 
                { opacity: 0.8, y: -8 },
                { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
            );

            gsap.fromTo('.gsap-hero-title', 
                { opacity: 0.85, y: 10 },
                { opacity: 1, y: 0, duration: 0.5, delay: 0.05, ease: 'power2.out' }
            );

            gsap.fromTo('.gsap-hero-desc', 
                { opacity: 0.85, y: 8 },
                { opacity: 1, y: 0, duration: 0.5, delay: 0.1, ease: 'power2.out' }
            );

            gsap.fromTo('.gsap-hero-cta', 
                { opacity: 0.9, y: 6 },
                { opacity: 1, y: 0, duration: 0.45, stagger: 0.08, delay: 0.15, ease: 'power2.out' }
            );

            // ScrollTrigger for Telemetry section elements
            if (typeof ScrollTrigger !== 'undefined') {
                gsap.from('.gsap-telemetry-reveal', {
                    scrollTrigger: {
                        trigger: '#telemetry',
                        start: 'top 85%'
                    },
                    opacity: 0,
                    y: 28,
                    duration: 0.7,
                    stagger: 0.1,
                    ease: 'power2.out'
                });
            }
        } catch (e) {
            console.warn('GSAP initialization skipped:', e);
        }
    }

    // Initialize all modules when DOM is ready
    document.addEventListener('DOMContentLoaded', function () {
        initHeroMeshGradient();
        initTelemetryParticleNetwork();
        initMetricsCounters();
        initShowcaseDashboard();
        initGSAPAnimations();
    });

})();
