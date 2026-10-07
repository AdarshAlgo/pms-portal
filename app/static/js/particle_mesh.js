/**
 * ==============================================================================
 * 🌌 GLOBAL TECH NODE CONSTELLATION & PARTICLE STARDUST ENGINE
 * ==============================================================================
 * Universal Persistent Architecture:
 * - Operates globally across ALL routes, portals, auth pages, and dashboards.
 * - Single-instance persistence: persists smoothly through page transitions.
 * - Dynamic scroll adaptation: measures full scrollable document height (min-height: 100vh)
 *   and maps particles seamlessly across all sections (Hero, Features, Telemetry, Footer).
 *
 * Fine-Tuned Physics (Per Specification):
 * - Base Drift Speed: 1.2 to 2.0 px/frame (active, alive, energetic, non-hyperactive).
 * - Mouse Reaction Lerp: 0.075 (within 0.05 - 0.1 spec).
 * - Mouse Nudge Displacement: 18px to 24px (within 15px - 25px spec).
 * - Interaction Radius: 100px with smooth quadratic falloff.
 * - Layering: pointer-events: none; z-index: 0; strictly non-blocking.
 * - Dynamic Theme Adaptation: Dark & Light mode palettes with MutationObserver.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.StripeParticleMesh = factory();
        root.GlobalParticleBackground = root.StripeParticleMesh;
    }
}(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    // --------------------------------------------------------------------------
    // 🎨 Theme Color Palettes (High-Contrast Tech Nodes / Stardust)
    // --------------------------------------------------------------------------
    const PALETTES = {
        dark: {
            nodes: [
                { r: 0,   g: 242, b: 254, baseAlpha: 0.95, name: 'neon-cyan'       }, // Vibrant Glowing Cyan #00f2fe
                { r: 168, g: 85,  b: 247, baseAlpha: 0.92, name: 'glowing-purple'  }, // Radiant Glowing Purple #a855f7
                { r: 251, g: 146, b: 60,  baseAlpha: 0.92, name: 'neon-orange'     }, // Soft Glowing Neon Orange #fb923c
                { r: 127, g: 0,   b: 255, baseAlpha: 0.90, name: 'electric-violet' }, // Vibrant Electric Violet #7f00ff
                { r: 56,  g: 189, b: 248, baseAlpha: 0.92, name: 'pastel-cyan'     }, // Sky Cyan #38bdf8
                { r: 52,  g: 211, b: 153, baseAlpha: 0.88, name: 'pastel-emerald'  }  // Mint Emerald #34d399
            ],
            lineRgb: '0, 242, 254',           // Glowing Cyan #00f2fe
            lineColor: '#00f2fe',
            lineAlphaMax: 0.55,               // Opacity 0.40 - 0.60 per specification
            glowRgb: '0, 242, 254'
        },
        light: {
            nodes: [
                { r: 6,   g: 182, b: 212, baseAlpha: 0.88, name: 'cyan'   }, // Sky Cyan #06b6d4
                { r: 147, g: 51,  b: 234, baseAlpha: 0.88, name: 'purple' }, // Radiant Violet #9333ea
                { r: 234, g: 88,  b: 12,  baseAlpha: 0.88, name: 'orange' }, // Warm Neon Orange #ea580c
                { r: 99,  g: 102, b: 241, baseAlpha: 0.88, name: 'indigo' }, // Royal Indigo #6366f1
                { r: 16,  g: 185, b: 129, baseAlpha: 0.82, name: 'emerald'}  // Jade Emerald #10b981
            ],
            lineRgb: '6, 182, 212',            // Radiant Cyan
            lineColor: '#06b6d4',
            lineAlphaMax: 0.50,               // Opacity 0.40 - 0.60 per specification
            glowRgb: '6, 182, 212'
        }
    };

    // --------------------------------------------------------------------------
    // ⚙️ Fine-Tuned Default Configuration (Prominent Constellation Lines)
    // --------------------------------------------------------------------------
    const DEFAULT_CONFIG = {
        canvasId: 'stripe-particle-mesh-canvas',
        baseSpeedMin: 1.3,              // Base drift speed min (~1.5 average pace)
        baseSpeedMax: 1.7,              // Base drift speed max
        mouseRepulseRadius: 100,        // Responsive interaction radius (~100px)
        maxNudgeDistance: 20,           // Controlled 15px - 25px gentle displacement
        interactivityLerp: 0.08,        // Smooth lerp/easing responsive push
        nudgeDamping: 0.08,             // Damping factor for smooth return to equilibrium
        connectionDistance: 165,        // Prominent linking distance (150px - 180px spec)
        maxDistance: 165,               // Direct alias for connection distance
        lineWidth: 1.35,                // Thicker stroke width (1.2px - 1.5px spec)
        lineOpacity: 0.54,              // Prominent connecting line opacity (0.4 - 0.6 spec)
        line_linked: {                  // Particles.js / Canvas API standard compliance
            enable: true,
            distance: 165,
            color: '#00f2fe',
            opacity: 0.54,
            width: 1.35
        },
        nodeDensityPer1000px: 30,       // Constellation density per 1000px height
        minTotalNodes: 65,
        maxTotalNodes: 190,
        parallaxFactor: 1.0             // 1:1 scroll synchronization with content
    };

    class TechNodeConstellation {
        constructor(userConfig = {}) {
            this.config = Object.assign({}, DEFAULT_CONFIG, userConfig);
            if (userConfig && userConfig.line_linked) {
                if (userConfig.line_linked.distance) {
                    this.config.connectionDistance = userConfig.line_linked.distance;
                    this.config.maxDistance = userConfig.line_linked.distance;
                }
                if (userConfig.line_linked.opacity) {
                    this.config.lineOpacity = userConfig.line_linked.opacity;
                }
                if (userConfig.line_linked.width) {
                    this.config.lineWidth = userConfig.line_linked.width;
                }
                if (userConfig.line_linked.color) {
                    this.config.lineColor = userConfig.line_linked.color;
                }
            }
            this.canvas = null;
            this.ctx = null;
            this.width = 0;
            this.height = 0;
            this.docHeight = 0;
            this.dpr = 1;

            this.particles = [];
            this.time = 0;

            // Scroll position tracking
            this.scrollY = 0;
            this.targetScrollY = 0;
            this.scrollContainer = null;

            // Mouse tracking
            this.mouse = {
                x: -9999,
                y: -9999,
                active: false,
                lastMoved: 0
            };

            this.isDark = this.detectDarkMode();
            this.palette = this.isDark ? PALETTES.dark : PALETTES.light;

            this.isRunning = false;
            this.animFrameId = null;
            this.lastFrameTime = performance.now();

            this._onResize = this.resize.bind(this);
            this._onScroll = this.onScroll.bind(this);
            this._onMouseMove = this.onMouseMove.bind(this);
            this._onTouchMove = this.onTouchMove.bind(this);
            this._onMouseLeave = this.onMouseLeave.bind(this);
            this._onVisibilityChange = this.onVisibilityChange.bind(this);

            this.init();
        }

        detectDarkMode() {
            if (typeof document === 'undefined') return false;
            return document.documentElement.classList.contains('dark') ||
                   (localStorage && localStorage.theme === 'dark') ||
                   (!localStorage.theme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
        }

        getDocHeight() {
            if (typeof document === 'undefined') return 1000;
            const mainEl = this.scrollContainer || document.querySelector('#main-content main') || document.querySelector('main');
            const mainScrollHeight = mainEl ? mainEl.scrollHeight : 0;
            const bodyScrollHeight = document.body ? document.body.scrollHeight : 0;
            const docScrollHeight = document.documentElement ? document.documentElement.scrollHeight : 0;
            return Math.max(
                bodyScrollHeight,
                docScrollHeight,
                mainScrollHeight,
                window.innerHeight || 800,
                this.height > 0 ? this.height : 1000
            );
        }

        getScrollY() {
            if (this.scrollContainer && typeof this.scrollContainer.scrollTop === 'number') {
                return this.scrollContainer.scrollTop;
            }
            const mainEl = document.querySelector('#main-content main') || document.querySelector('main');
            if (mainEl && mainEl.scrollTop > 0) {
                this.scrollContainer = mainEl;
                return mainEl.scrollTop;
            }
            return window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
        }

        init() {
            if (typeof document === 'undefined') return;

            // 1. Locate or create canvas element
            this.canvas = document.getElementById(this.config.canvasId);
            if (!this.canvas) {
                this.canvas = document.createElement('canvas');
                this.canvas.id = this.config.canvasId;
                this.canvas.className = 'particle-mesh-canvas';
                this.canvas.setAttribute('aria-hidden', 'true');
                document.body.insertBefore(this.canvas, document.body.firstChild);
            }

            // Fixed full-page container (pointer-events: none; z-index: 0;)
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100vw';
            this.canvas.style.height = '100vh';
            this.canvas.style.zIndex = '0';
            this.canvas.style.pointerEvents = 'none';

            this.ctx = this.canvas.getContext('2d', { alpha: true });
            if (!this.ctx) return;

            // Check if there is an inner scroll container (e.g., dashboard main view)
            const mainEl = document.querySelector('#main-content main') || document.querySelector('main');
            if (mainEl) {
                this.scrollContainer = mainEl;
                this.scrollContainer.addEventListener('scroll', this._onScroll, { passive: true });
            }

            // 2. Initial size & particles
            this.resize();

            // Render first frame immediately to prevent blank canvas flash on route transitions
            this.render();

            // 3. Event Listeners with global capturing for inner scroll containers (dashboards)
            window.addEventListener('resize', this._onResize, { passive: true });
            window.addEventListener('scroll', this._onScroll, { capture: true, passive: true });
            document.addEventListener('scroll', this._onScroll, { capture: true, passive: true });
            window.addEventListener('mousemove', this._onMouseMove, { passive: true });
            window.addEventListener('touchmove', this._onTouchMove, { passive: true });
            window.addEventListener('mouseleave', this._onMouseLeave, { passive: true });
            document.addEventListener('visibilitychange', this._onVisibilityChange);

            // 4. Dynamic Theme Observer
            this.initThemeObserver();

            // 5. Dynamic DOM Height Observer (tracks page expansion or tab changes)
            this.initHeightObserver();

            // 6. Start 60 FPS animation loop
            this.start();
        }

        initThemeObserver() {
            if (typeof MutationObserver === 'undefined') return;

            this.themeObserver = new MutationObserver((mutations) => {
                for (let mutation of mutations) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const newDark = this.detectDarkMode();
                        if (newDark !== this.isDark) {
                            this.isDark = newDark;
                            this.palette = this.isDark ? PALETTES.dark : PALETTES.light;
                        }
                    }
                }
            });

            this.themeObserver.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['class']
            });
        }

        initHeightObserver() {
            if (typeof ResizeObserver === 'undefined') return;

            this.heightObserver = new ResizeObserver(() => {
                const newDocHeight = this.getDocHeight();
                if (Math.abs(newDocHeight - this.docHeight) > 80) {
                    this.docHeight = newDocHeight;
                    // Dynamically distribute particles across new height without flickering
                    this.syncParticlesToHeight();
                }
            });

            if (document.body) {
                this.heightObserver.observe(document.body);
            }
            const mainEl = document.querySelector('#main-content main') || document.querySelector('main');
            if (mainEl) {
                this.heightObserver.observe(mainEl);
            }
        }

        resize() {
            if (!this.canvas || !this.ctx) return;

            this.dpr = Math.min(window.devicePixelRatio || 1, 2);
            this.width = window.innerWidth;
            this.height = window.innerHeight;
            this.docHeight = this.getDocHeight();

            this.canvas.width = Math.floor(this.width * this.dpr);
            this.canvas.height = Math.floor(this.height * this.dpr);
            this.canvas.style.width = this.width + 'px';
            this.canvas.style.height = this.height + 'px';

            this.ctx.scale(this.dpr, this.dpr);

            this.initParticles();
        }

        computeTargetCount() {
            const thousandsOfPx = Math.max(1, this.docHeight / 1000);
            return Math.max(
                this.config.minTotalNodes,
                Math.min(this.config.maxTotalNodes, Math.floor(thousandsOfPx * this.config.nodeDensityPer1000px))
            );
        }

        createParticle(index, total) {
            // Base drift speed: 1.2 to 2.0 px/frame (scaled per spec)
            const speed = this.config.baseSpeedMin + Math.random() * (this.config.baseSpeedMax - this.config.baseSpeedMin);
            const angle = Math.random() * Math.PI * 2;

            const worldX = Math.random() * this.width;
            const worldY = (index / total) * this.docHeight + (Math.random() - 0.5) * (this.docHeight / total);

            return {
                worldX: worldX,
                worldY: Math.max(0, Math.min(this.docHeight, worldY)),
                
                // Active linear drift velocity vector
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,

                // Subtle sinusoidal organic wander oscillation
                phase: Math.random() * Math.PI * 2,
                pulseSpeed: 0.02 + Math.random() * 0.03,

                // Interactive mouse displacement (nudge)
                dispX: 0,
                dispY: 0,

                // Appearance: Tiny glowing stars (1.5px to 3.5px)
                radius: 1.5 + Math.random() * 2.0,
                colorIndex: Math.floor(Math.random() * 5),
                twinklePhase: Math.random() * Math.PI * 2,

                // Cached screen projection
                screenX: 0,
                screenY: 0,
                isVisible: false
            };
        }

        initParticles() {
            this.docHeight = this.getDocHeight();
            const targetCount = this.computeTargetCount();
            this.particles = [];

            for (let i = 0; i < targetCount; i++) {
                this.particles.push(this.createParticle(i, targetCount));
            }
        }

        syncParticlesToHeight() {
            const targetCount = this.computeTargetCount();
            if (this.particles.length < targetCount) {
                const diff = targetCount - this.particles.length;
                for (let i = 0; i < diff; i++) {
                    this.particles.push(this.createParticle(this.particles.length, targetCount));
                }
            }
        }

        onScroll(e) {
            if (e && e.target && e.target !== window && e.target !== document && typeof e.target.scrollTop === 'number') {
                this.scrollContainer = e.target;
                this.targetScrollY = e.target.scrollTop;
                return;
            }
            this.targetScrollY = this.getScrollY();
        }

        onMouseMove(e) {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
            this.mouse.active = true;
            this.mouse.lastMoved = performance.now();
        }

        onTouchMove(e) {
            if (e.touches && e.touches.length > 0) {
                this.mouse.x = e.touches[0].clientX;
                this.mouse.y = e.touches[0].clientY;
                this.mouse.active = true;
                this.mouse.lastMoved = performance.now();
            }
        }

        onMouseLeave() {
            this.mouse.active = false;
        }

        onVisibilityChange() {
            if (document.hidden) {
                this.pause();
            } else {
                this.lastFrameTime = performance.now();
                this.start();
            }
        }

        update(dt) {
            this.time += dt * 0.001;
            // Frame normalization: lock to 60 FPS baseline (dt in ms / 16.67ms)
            const timeScale = Math.min(dt / 16.67, 2.0);

            // 1. Smooth Scroll Follow
            this.targetScrollY = this.getScrollY();
            this.scrollY += (this.targetScrollY - this.scrollY) * 0.22;

            const maxInteractionRad = this.config.mouseRepulseRadius;
            const maxNudge = this.config.maxNudgeDistance;
            const lerpSpeed = this.config.interactivityLerp;
            const isMouseActive = this.mouse.active && (performance.now() - this.mouse.lastMoved < 2200);

            // 2. Update each particle position with 1.2-2.0 px drift & boundary wrapping
            for (let i = 0; i < this.particles.length; i++) {
                const p = this.particles[i];

                // Active drift + gentle sinusoidal breathing
                p.phase += p.pulseSpeed * timeScale;
                const organicDriftX = Math.cos(p.phase) * 0.35;
                const organicDriftY = Math.sin(p.phase * 0.8) * 0.35;

                p.worldX += (p.vx + organicDriftX) * timeScale;
                p.worldY += (p.vy + organicDriftY) * timeScale;

                // Screen and document wrapping
                const pad = 25;
                if (p.worldX < -pad) p.worldX = this.width + pad;
                else if (p.worldX > this.width + pad) p.worldX = -pad;

                if (p.worldY < -pad) p.worldY = this.docHeight + pad;
                else if (p.worldY > this.docHeight + pad) p.worldY = -pad;

                // Project to viewport space based on scroll
                const projectedY = p.worldY - (this.scrollY * this.config.parallaxFactor);

                // Viewport Culling (-60px to height + 60px)
                if (projectedY < -60 || projectedY > this.height + 60) {
                    p.isVisible = false;
                    p.dispX += (0 - p.dispX) * this.config.nudgeDamping;
                    p.dispY += (0 - p.dispY) * this.config.nudgeDamping;
                    continue;
                }

                p.isVisible = true;

                // 3. Responsive Mouse Nudge (15px - 25px push with 0.05 - 0.1 lerp)
                let targetDispX = 0;
                let targetDispY = 0;

                if (isMouseActive) {
                    const currentScreenX = p.worldX + p.dispX;
                    const currentScreenY = projectedY + p.dispY;

                    const dx = currentScreenX - this.mouse.x;
                    const dy = currentScreenY - this.mouse.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < maxInteractionRad && dist > 0) {
                        // Smooth cubic falloff curve
                        const factor = 1 - (dist / maxInteractionRad);
                        const pushAmount = (factor * factor) * maxNudge;

                        targetDispX = (dx / dist) * pushAmount;
                        targetDispY = (dy / dist) * pushAmount;
                    }
                }

                // Smooth responsive lerp interpolation toward target displacement
                p.dispX += (targetDispX - p.dispX) * lerpSpeed;
                p.dispY += (targetDispY - p.dispY) * lerpSpeed;

                p.screenX = p.worldX + p.dispX;
                p.screenY = projectedY + p.dispY;
            }
        }

        render() {
            if (!this.ctx) return;
            const ctx = this.ctx;
            const palette = this.palette;

            ctx.clearRect(0, 0, this.width, this.height);

            // Filter down to visible nodes on current viewport
            const visibleNodes = [];
            for (let i = 0; i < this.particles.length; i++) {
                if (this.particles[i].isVisible) {
                    visibleNodes.push(this.particles[i]);
                }
            }

            const visibleCount = visibleNodes.length;
            const maxConnDist = this.config.connectionDistance || this.config.maxDistance || 165;
            const maxConnDistSq = maxConnDist * maxConnDist;
            const lineStrokeWidth = this.config.lineWidth || 1.35;
            const baseLineAlpha = this.config.lineOpacity || palette.lineAlphaMax || 0.54;

            // ------------------------------------------------------------------
            // A. Draw Prominent Glowing Constellation Connecting Lines
            // ------------------------------------------------------------------
            ctx.lineWidth = lineStrokeWidth;
            for (let i = 0; i < visibleCount; i++) {
                const p1 = visibleNodes[i];
                const n1 = palette.nodes[p1.colorIndex % palette.nodes.length];

                for (let j = i + 1; j < visibleCount; j++) {
                    const p2 = visibleNodes[j];
                    const dx = p1.screenX - p2.screenX;
                    const dy = p1.screenY - p2.screenY;
                    const distSq = dx * dx + dy * dy;

                    if (distSq < maxConnDistSq) {
                        const dist = Math.sqrt(distSq);
                        // Proximity: 1.0 (touching) down to 0.0 (at boundary)
                        const proximity = 1 - (dist / maxConnDist);
                        // Calculate prominent glowing line opacity between 0.40 and 0.60
                        // Using power curve so lines stay prominent across distances and taper smoothly to boundary
                        const alpha = Math.max(0, Math.min(0.60, Math.pow(proximity, 0.70) * baseLineAlpha));

                        if (alpha > 0.02) {
                            const n2 = palette.nodes[p2.colorIndex % palette.nodes.length];

                            // Vibrant Glowing Line Color Styling:
                            // Matches the connected nodes' accent colors (cyan #00f2fe, purple #7f00ff, soft neon orange)
                            if (p1.colorIndex === p2.colorIndex) {
                                ctx.strokeStyle = `rgba(${n1.r}, ${n1.g}, ${n1.b}, ${alpha.toFixed(3)})`;
                            } else {
                                const grad = ctx.createLinearGradient(p1.screenX, p1.screenY, p2.screenX, p2.screenY);
                                grad.addColorStop(0, `rgba(${n1.r}, ${n1.g}, ${n1.b}, ${alpha.toFixed(3)})`);
                                grad.addColorStop(1, `rgba(${n2.r}, ${n2.g}, ${n2.b}, ${alpha.toFixed(3)})`);
                                ctx.strokeStyle = grad;
                            }

                            ctx.beginPath();
                            ctx.moveTo(p1.screenX, p1.screenY);
                            ctx.lineTo(p2.screenX, p2.screenY);
                            ctx.stroke();
                        }
                    }
                }
            }

            // ------------------------------------------------------------------
            // B. Draw Tiny Glowing Tech Nodes / Stardust (1.5px - 3.5px)
            // ------------------------------------------------------------------
            for (let i = 0; i < visibleCount; i++) {
                const p = visibleNodes[i];
                const nodeDef = palette.nodes[p.colorIndex % palette.nodes.length];

                // Twinkle pulse
                const twinkle = Math.sin(this.time * 2.5 + p.twinklePhase) * 0.15;
                const alpha = Math.max(0.2, Math.min(1.0, nodeDef.baseAlpha + twinkle));

                ctx.save();
                // Radiant outer glow
                ctx.shadowBlur = this.isDark ? 6 : 3;
                ctx.shadowColor = `rgba(${nodeDef.r}, ${nodeDef.g}, ${nodeDef.b}, ${this.isDark ? 0.7 : 0.35})`;
                ctx.fillStyle = `rgba(${nodeDef.r}, ${nodeDef.g}, ${nodeDef.b}, ${alpha.toFixed(2)})`;

                ctx.beginPath();
                ctx.arc(p.screenX, p.screenY, p.radius, 0, Math.PI * 2);
                ctx.fill();

                // Bright star core pinpoint
                ctx.shadowBlur = 0;
                ctx.fillStyle = this.isDark ? 'rgba(255, 255, 255, 0.90)' : 'rgba(255, 255, 255, 0.70)';
                ctx.beginPath();
                ctx.arc(p.screenX, p.screenY, Math.max(0.6, p.radius * 0.38), 0, Math.PI * 2);
                ctx.fill();

                ctx.restore();
            }
        }

        loop(timestamp) {
            if (!this.isRunning) return;

            const dt = Math.min(timestamp - this.lastFrameTime, 64);
            this.lastFrameTime = timestamp;

            this.update(dt);
            this.render();

            this.animFrameId = requestAnimationFrame(this.loop.bind(this));
        }

        start() {
            if (this.isRunning) return;
            this.isRunning = true;
            this.lastFrameTime = performance.now();
            this.animFrameId = requestAnimationFrame(this.loop.bind(this));
        }

        pause() {
            this.isRunning = false;
            if (this.animFrameId) {
                cancelAnimationFrame(this.animFrameId);
                this.animFrameId = null;
            }
        }

        destroy() {
            this.pause();
            if (this.themeObserver) this.themeObserver.disconnect();
            if (this.heightObserver) this.heightObserver.disconnect();
            window.removeEventListener('resize', this._onResize);
            window.removeEventListener('scroll', this._onScroll);
            if (this.scrollContainer) {
                this.scrollContainer.removeEventListener('scroll', this._onScroll);
            }
            window.removeEventListener('mousemove', this._onMouseMove);
            window.removeEventListener('touchmove', this._onTouchMove);
            window.removeEventListener('mouseleave', this._onMouseLeave);
            document.removeEventListener('visibilitychange', this._onVisibilityChange);
            if (this.canvas && this.canvas.parentNode) {
                this.canvas.parentNode.removeChild(this.canvas);
            }
        }
    }

    // Persistent Global Auto-Initialization (Single Instance Safety across all routes)
    function autoInit() {
        if (typeof window === 'undefined' || typeof document === 'undefined') return;

        function start() {
            if (!window.__globalParticleInstance) {
                window.__globalParticleInstance = new TechNodeConstellation();
            } else {
                const inst = window.__globalParticleInstance;
                const canvas = document.getElementById(inst.config.canvasId);
                if (canvas && canvas !== inst.canvas) {
                    inst.canvas = canvas;
                    inst.ctx = canvas.getContext('2d', { alpha: true });
                    inst.resize();
                    inst.render();
                } else if (inst.canvas) {
                    inst.resize();
                    inst.render();
                }
            }
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', start);
        } else {
            start();
        }
        window.addEventListener('pageshow', start);
    }
    autoInit();

    return {
        create: (cfg) => new TechNodeConstellation(cfg),
        getInstance: () => window.__globalParticleInstance,
        Engine: TechNodeConstellation
    };
}));
