/**
 * Capstone Project Progress Monitoring & Evaluation System
 * Dashboard Core Script: Drawer Inspection, Apple-Style Toasts, Sidebar & Micro-Interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // --------------------------------------------------------------------------
    // 1. Sidebar Toggle Functionality
    // --------------------------------------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarClose = document.getElementById('sidebar-close');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    
    function toggleSidebar() {
        if (!sidebar) return;
        if (sidebar.classList.contains('-translate-x-full')) {
            // Open
            sidebar.classList.remove('-translate-x-full');
            sidebar.classList.add('translate-x-0');
            if (sidebarOverlay) sidebarOverlay.classList.remove('hidden');
        } else {
            // Close
            sidebar.classList.add('-translate-x-full');
            sidebar.classList.remove('translate-x-0');
            if (sidebarOverlay) sidebarOverlay.classList.add('hidden');
        }
    }
    
    if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
    if (sidebarClose) sidebarClose.addEventListener('click', toggleSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', toggleSidebar);

    // --------------------------------------------------------------------------
    // 2. Apple-Style Slide-Over Drawer Controller
    // --------------------------------------------------------------------------
    const drawerBackdrop = document.getElementById('global-drawer-backdrop');
    const drawerPanel = document.getElementById('global-drawer-panel');
    const drawerTitle = document.getElementById('global-drawer-title');
    const drawerBody = document.getElementById('global-drawer-body');
    const drawerCloseBtn = document.getElementById('global-drawer-close');

    window.openSlideOver = function(title, contentHtml) {
        if (!drawerPanel) return;
        if (drawerTitle) drawerTitle.textContent = title || 'Inspection Details';
        if (drawerBody) {
            if (typeof contentHtml === 'string') {
                drawerBody.innerHTML = contentHtml;
            } else if (contentHtml instanceof HTMLElement) {
                drawerBody.innerHTML = '';
                drawerBody.appendChild(contentHtml);
            }
        }
        document.body.classList.add('drawer-open');
        document.body.style.overflow = 'hidden';
    };

    window.closeSlideOver = function() {
        document.body.classList.remove('drawer-open');
        document.body.style.overflow = '';
    };

    if (drawerCloseBtn) {
        drawerCloseBtn.addEventListener('click', window.closeSlideOver);
    }
    if (drawerBackdrop) {
        drawerBackdrop.addEventListener('click', window.closeSlideOver);
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.body.classList.contains('drawer-open')) {
                window.closeSlideOver();
            }
        }
    });

    // --------------------------------------------------------------------------
    // 3. Apple-Style Floating Toast Notification System
    // --------------------------------------------------------------------------
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    window.showToast = function(message, type = 'info', duration = 4000) {
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = 'toast-item pointer-events-auto';

        let iconClass = 'fa-info-circle text-indigo-500';
        let borderColor = 'border-indigo-200 dark:border-indigo-800';
        if (type === 'success') {
            iconClass = 'fa-check-circle text-emerald-500';
            borderColor = 'border-emerald-200 dark:border-emerald-800';
        } else if (type === 'error' || type === 'danger') {
            iconClass = 'fa-exclamation-triangle text-rose-500';
            borderColor = 'border-rose-200 dark:border-rose-800';
        } else if (type === 'warning') {
            iconClass = 'fa-exclamation-circle text-amber-500';
            borderColor = 'border-amber-200 dark:border-amber-800';
        }

        toast.innerHTML = `
            <div class="flex items-center space-x-3 pr-2 py-0.5">
                <i class="fas ${iconClass} text-base shrink-0"></i>
                <div class="text-xs font-semibold text-slate-800 dark:text-slate-100">${message}</div>
            </div>
            <button type="button" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs ml-3 focus:outline-none transition-colors">
                <i class="fas fa-times"></i>
            </button>
            <div class="toast-progress"></div>
        `;

        const closeBtn = toast.querySelector('button');
        const removeToast = () => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px) scale(0.95)';
            toast.style.transition = 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)';
            setTimeout(() => toast.remove(), 200);
        };

        if (closeBtn) closeBtn.addEventListener('click', removeToast);

        toastContainer.appendChild(toast);

        // Auto remove after duration
        setTimeout(removeToast, duration);
    };

    // --------------------------------------------------------------------------
    // 4. Auto-Dismiss Flash Messages
    // --------------------------------------------------------------------------
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        const closeBtn = msg.querySelector('.dismiss-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                msg.style.transition = 'all 0.25s ease';
                setTimeout(() => msg.remove(), 250);
            });
        }
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (document.body.contains(msg)) {
                msg.style.opacity = '0';
                msg.style.transform = 'translateY(-10px)';
                msg.style.transition = 'all 0.25s ease';
                setTimeout(() => msg.remove(), 250);
            }
        }, 5000);
    });

    // --------------------------------------------------------------------------
    // 5. Staggered Entrance Animations for elements with data-animate
    // --------------------------------------------------------------------------
    const animatedElements = document.querySelectorAll('[data-animate]');
    if (animatedElements.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08 });

        animatedElements.forEach(el => observer.observe(el));
    }
});
