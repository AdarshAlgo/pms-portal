import React, { useEffect, useRef } from 'react';

/**
 * GlobalParticleBackground - High-Performance Global Particle Stardust Component
 * Compatible with React, Next.js (App Router / Pages Router), and SPA Architectures.
 *
 * Universal Specifications:
 * - Persistent across all routes and client-side page transitions.
 * - Dynamic scroll adaptation across full document height (min-height: 100vh).
 * - Layering: pointer-events: none; z-index: 0; strictly non-blocking for all inputs/cards.
 * - Fine-Tuned Speed: Base drift speed 1.2 to 2.0 px/frame (active and lively).
 * - Mouse Reaction Lerp: 0.075 with 18px - 24px responsive push displacement.
 * - Tech Stardust: 1.5px - 3.5px neon nodes (cyan, purple, orange, indigo) with connecting lines.
 * - Dynamic Dark & Light theme detection via MutationObserver.
 *
 * @param {Object} props
 * @param {number} [props.baseSpeedMin=1.2] - Minimum drift speed
 * @param {number} [props.baseSpeedMax=2.0] - Maximum drift speed
 * @param {number} [props.maxNudgeDistance=20] - Maximum mouse push displacement in px (15-25px)
 * @param {number} [props.interactivityLerp=0.075] - Easing factor for mouse response (0.05-0.10)
 * @param {number} [props.mouseRepulseRadius=100] - Interaction radius in px
 * @param {number} [props.connectionDistance=95] - Line connection threshold
 * @param {string} [props.className=""] - Extra CSS classes
 * @param {React.CSSProperties} [props.style={}] - Extra inline styles
 */
export default function GlobalParticleBackground({
  baseSpeedMin = 1.2,
  baseSpeedMax = 2.0,
  maxNudgeDistance = 20,
  interactivityLerp = 0.075,
  mouseRepulseRadius = 100,
  connectionDistance = 95,
  nodeDensityPer1000px = 26,
  minTotalNodes = 50,
  maxTotalNodes = 170,
  parallaxFactor = 1.0,
  className = '',
  style = {},
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    const PALETTES = {
      dark: {
        nodes: [
          { r: 168, g: 85,  b: 247, baseAlpha: 0.85 }, // Neon Purple
          { r: 6,   g: 182, b: 212, baseAlpha: 0.90 }, // Electric Cyan
          { r: 249, g: 115, b: 22,  baseAlpha: 0.85 }, // Soft Orange
          { r: 99,  g: 102, b: 241, baseAlpha: 0.85 }, // Electric Indigo
          { r: 16,  g: 185, b: 129, baseAlpha: 0.80 }  // Vivid Emerald
        ],
        lineRgb: '129, 140, 248',
        lineAlphaMax: 0.16
      },
      light: {
        nodes: [
          { r: 147, g: 51,  b: 234, baseAlpha: 0.75 }, // Deep Violet
          { r: 8,   g: 145, b: 178, baseAlpha: 0.80 }, // Azure Cyan
          { r: 234, g: 88,  b: 12,  baseAlpha: 0.75 }, // Warm Amber
          { r: 79,  g: 70,  b: 229, baseAlpha: 0.75 }, // Royal Indigo
          { r: 5,   g: 150, b: 105, baseAlpha: 0.70 }  // Jade Emerald
        ],
        lineRgb: '99, 102, 241',
        lineAlphaMax: 0.12
      }
    };

    function isDarkMode() {
      return (
        document.documentElement.classList.contains('dark') ||
        (typeof localStorage !== 'undefined' && localStorage.theme === 'dark') ||
        (!localStorage?.theme && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches)
      );
    }

    let isDark = isDarkMode();
    let palette = isDark ? PALETTES.dark : PALETTES.light;

    let width = window.innerWidth;
    let height = window.innerHeight;
    let docHeight = Math.max(
      document.body?.scrollHeight || 0,
      document.documentElement?.scrollHeight || 0,
      height > 0 ? height : 1000
    );
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    let particles = [];
    let time = 0;
    let isRunning = true;
    let animId = null;
    let lastFrameTime = performance.now();

    let scrollY = window.scrollY || 0;
    let targetScrollY = scrollY;

    const mouse = {
      x: -9999,
      y: -9999,
      active: false,
      lastMoved: 0
    };

    function getDocHeight() {
      return Math.max(
        document.body?.scrollHeight || 0,
        document.documentElement?.scrollHeight || 0,
        height > 0 ? height : 1000
      );
    }

    function createParticle(index, total) {
      const speed = baseSpeedMin + Math.random() * (baseSpeedMax - baseSpeedMin);
      const angle = Math.random() * Math.PI * 2;
      const worldX = Math.random() * width;
      const worldY = (index / total) * docHeight + (Math.random() - 0.5) * (docHeight / total);

      return {
        worldX: worldX,
        worldY: Math.max(0, Math.min(docHeight, worldY)),
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        phase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.02 + Math.random() * 0.03,
        dispX: 0,
        dispY: 0,
        radius: 1.5 + Math.random() * 2.0,
        colorIndex: Math.floor(Math.random() * 5),
        twinklePhase: Math.random() * Math.PI * 2,
        screenX: 0,
        screenY: 0,
        isVisible: false
      };
    }

    function computeTargetCount() {
      const thousandsOfPx = Math.max(1, docHeight / 1000);
      return Math.max(
        minTotalNodes,
        Math.min(maxTotalNodes, Math.floor(thousandsOfPx * nodeDensityPer1000px))
      );
    }

    function initParticles() {
      docHeight = getDocHeight();
      const count = computeTargetCount();
      particles = [];
      for (let i = 0; i < count; i++) {
        particles.push(createParticle(i, count));
      }
    }

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      docHeight = getDocHeight();

      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';

      ctx.scale(dpr, dpr);
      initParticles();
    }

    resize();

    function onScroll() {
      targetScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
    }

    function onMouseMove(e) {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      mouse.active = true;
      mouse.lastMoved = performance.now();
    }

    function onTouchMove(e) {
      if (e.touches && e.touches.length > 0) {
        mouse.x = e.touches[0].clientX;
        mouse.y = e.touches[0].clientY;
        mouse.active = true;
        mouse.lastMoved = performance.now();
      }
    }

    function onMouseLeave() {
      mouse.active = false;
    }

    function onVisibilityChange() {
      if (document.hidden) {
        isRunning = false;
        if (animId) cancelAnimationFrame(animId);
      } else {
        isRunning = true;
        lastFrameTime = performance.now();
        animId = requestAnimationFrame(loop);
      }
    }

    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('mousemove', onMouseMove, { passive: true });
    window.addEventListener('touchmove', onTouchMove, { passive: true });
    window.addEventListener('mouseleave', onMouseLeave, { passive: true });
    document.addEventListener('visibilitychange', onVisibilityChange);

    let observer = null;
    if (typeof MutationObserver !== 'undefined') {
      observer = new MutationObserver((mutations) => {
        for (let mutation of mutations) {
          if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
            const nextDark = isDarkMode();
            if (nextDark !== isDark) {
              isDark = nextDark;
              palette = isDark ? PALETTES.dark : PALETTES.light;
            }
          }
        }
      });
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
      });
    }

    function update(dt) {
      time += dt * 0.001;
      const timeScale = Math.min(dt / 16.67, 2.0);

      targetScrollY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
      scrollY += (targetScrollY - scrollY) * 0.22;

      const isMouseActive = mouse.active && (performance.now() - mouse.lastMoved < 2200);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Active drift + gentle sinusoidal breathing
        p.phase += p.pulseSpeed * timeScale;
        const organicDriftX = Math.cos(p.phase) * 0.35;
        const organicDriftY = Math.sin(p.phase * 0.8) * 0.35;

        p.worldX += (p.vx + organicDriftX) * timeScale;
        p.worldY += (p.vy + organicDriftY) * timeScale;

        // Boundary wrapping
        const pad = 25;
        if (p.worldX < -pad) p.worldX = width + pad;
        else if (p.worldX > width + pad) p.worldX = -pad;
        if (p.worldY < -pad) p.worldY = docHeight + pad;
        else if (p.worldY > docHeight + pad) p.worldY = -pad;

        const projectedY = p.worldY - (scrollY * parallaxFactor);

        if (projectedY < -60 || projectedY > height + 60) {
          p.isVisible = false;
          p.dispX += (0 - p.dispX) * 0.075;
          p.dispY += (0 - p.dispY) * 0.075;
          continue;
        }

        p.isVisible = true;

        let targetDispX = 0;
        let targetDispY = 0;

        if (isMouseActive) {
          const currentScreenX = p.worldX + p.dispX;
          const currentScreenY = projectedY + p.dispY;
          const dx = currentScreenX - mouse.x;
          const dy = currentScreenY - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < mouseRepulseRadius && dist > 0) {
            const factor = 1 - (dist / mouseRepulseRadius);
            const pushAmount = (factor * factor) * maxNudgeDistance;
            targetDispX = (dx / dist) * pushAmount;
            targetDispY = (dy / dist) * pushAmount;
          }
        }

        p.dispX += (targetDispX - p.dispX) * interactivityLerp;
        p.dispY += (targetDispY - p.dispY) * interactivityLerp;

        p.screenX = p.worldX + p.dispX;
        p.screenY = projectedY + p.dispY;
      }
    }

    function render() {
      ctx.clearRect(0, 0, width, height);

      const visibleNodes = [];
      for (let i = 0; i < particles.length; i++) {
        if (particles[i].isVisible) {
          visibleNodes.push(particles[i]);
        }
      }

      const visibleCount = visibleNodes.length;
      const maxConnDistSq = connectionDistance * connectionDistance;

      ctx.lineWidth = 0.75;
      for (let i = 0; i < visibleCount; i++) {
        const p1 = visibleNodes[i];
        for (let j = i + 1; j < visibleCount; j++) {
          const p2 = visibleNodes[j];
          const dx = p1.screenX - p2.screenX;
          const dy = p1.screenY - p2.screenY;
          const distSq = dx * dx + dy * dy;

          if (distSq < maxConnDistSq) {
            const dist = Math.sqrt(distSq);
            const alpha = (1 - dist / connectionDistance) * palette.lineAlphaMax;
            ctx.strokeStyle = `rgba(${palette.lineRgb}, ${alpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.moveTo(p1.screenX, p1.screenY);
            ctx.lineTo(p2.screenX, p2.screenY);
            ctx.stroke();
          }
        }
      }

      for (let i = 0; i < visibleCount; i++) {
        const p = visibleNodes[i];
        const nodeDef = palette.nodes[p.colorIndex % palette.nodes.length];
        const twinkle = Math.sin(time * 2.5 + p.twinklePhase) * 0.15;
        const alpha = Math.max(0.2, Math.min(1.0, nodeDef.baseAlpha + twinkle));

        ctx.save();
        ctx.shadowBlur = isDark ? 6 : 3;
        ctx.shadowColor = `rgba(${nodeDef.r}, ${nodeDef.g}, ${nodeDef.b}, ${isDark ? 0.7 : 0.35})`;
        ctx.fillStyle = `rgba(${nodeDef.r}, ${nodeDef.g}, ${nodeDef.b}, ${alpha.toFixed(2)})`;

        ctx.beginPath();
        ctx.arc(p.screenX, p.screenY, p.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0;
        ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.90)' : 'rgba(255, 255, 255, 0.70)';
        ctx.beginPath();
        ctx.arc(p.screenX, p.screenY, Math.max(0.6, p.radius * 0.38), 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }

    function loop(timestamp) {
      if (!isRunning) return;
      const dt = Math.min(timestamp - lastFrameTime, 64);
      lastFrameTime = timestamp;

      update(dt);
      render();

      animId = requestAnimationFrame(loop);
    }

    animId = requestAnimationFrame(loop);

    return () => {
      isRunning = false;
      if (animId) cancelAnimationFrame(animId);
      if (observer) observer.disconnect();
      window.removeEventListener('resize', resize);
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('touchmove', onTouchMove);
      window.removeEventListener('mouseleave', onMouseLeave);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, [
    baseSpeedMin,
    baseSpeedMax,
    maxNudgeDistance,
    interactivityLerp,
    mouseRepulseRadius,
    connectionDistance,
    nodeDensityPer1000px,
    minTotalNodes,
    maxTotalNodes,
    parallaxFactor
  ]);

  return (
    <canvas
      ref={canvasRef}
      id="stripe-particle-mesh-canvas"
      className={`particle-mesh-canvas ${className}`}
      aria-hidden="true"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        minHeight: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
        ...style
      }}
    />
  );
}
