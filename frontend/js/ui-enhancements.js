/**
 * UI交互增强系统
 */

class UIEnhancements {
    constructor() {
        this.observers = new Map();
        this.isInitialized = false;
        this.init();
    }

    init() {
        if (this.isInitialized) return;

        this.setupScrollReveal();
        this.setupParallax();
        this.setupRippleEffects();
        this.setupSmoothenScrolling();
        this.setupLazyLoading();
        this.setupTooltips();
        this.setupCountUp();

        this.isInitialized = true;
        console.log('UI Enhancements initialized');
    }

    // 滚动显示动画
    setupScrollReveal() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');

                    // 为子元素添加延迟动画
                    const children = entry.target.querySelectorAll('.animate-delay');
                    children.forEach((child, index) => {
                        setTimeout(() => {
                            child.classList.add('animate-fadeInUp');
                        }, index * 100);
                    });
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        document.querySelectorAll('.scroll-reveal').forEach(el => {
            observer.observe(el);
        });

        this.observers.set('scrollReveal', observer);
    }

    // 视差滚动效果
    setupParallax() {
        const parallaxElements = document.querySelectorAll('.parallax');
        if (parallaxElements.length === 0) return;

        const handleScroll = () => {
            const scrollTop = window.pageYOffset;

            parallaxElements.forEach(element => {
                const speed = element.dataset.speed || 0.5;
                const yPos = -(scrollTop * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });
        };

        window.addEventListener('scroll', this.throttle(handleScroll, 16));
    }

    // 波纹点击效果
    setupRippleEffects() {
        document.addEventListener('click', (e) => {
            const target = e.target.closest('.ripple');
            if (!target) return;

            const rect = target.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-animation 0.6s linear;
                background-color: rgba(255, 255, 255, 0.6);
                left: ${x}px;
                top: ${y}px;
                width: ${size}px;
                height: ${size}px;
                pointer-events: none;
            `;

            target.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });

        // 添加波纹动画CSS
        if (!document.getElementById('ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple-animation {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // 平滑滚动
    setupSmoothenScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // 懒加载图片
    setupLazyLoading() {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    const src = img.dataset.src;

                    if (src) {
                        img.src = src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                        imageObserver.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            img.classList.add('lazy');
            imageObserver.observe(img);
        });

        this.observers.set('lazyLoading', imageObserver);
    }

    // 工具提示
    setupTooltips() {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            pointer-events: none;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 200px;
            word-wrap: break-word;
        `;
        document.body.appendChild(tooltip);

        document.addEventListener('mouseover', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (!target) return;

            const text = target.dataset.tooltip;
            tooltip.textContent = text;
            tooltip.style.opacity = '1';

            const updatePosition = (e) => {
                tooltip.style.left = e.pageX + 10 + 'px';
                tooltip.style.top = e.pageY - 30 + 'px';
            };

            updatePosition(e);
            target.addEventListener('mousemove', updatePosition);

            target.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
                target.removeEventListener('mousemove', updatePosition);
            }, { once: true });
        });
    }

    // 数字计数动画
    setupCountUp() {
        const countUpElements = document.querySelectorAll('[data-countup]');
        if (countUpElements.length === 0) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCountUp(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        });

        countUpElements.forEach(el => observer.observe(el));
    }

    animateCountUp(element) {
        const target = parseInt(element.dataset.countup);
        const duration = parseInt(element.dataset.duration) || 2000;
        const increment = target / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current).toLocaleString();
        }, 16);
    }

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // 添加粒子爆炸效果
    createParticleExplosion(x, y, color = '#00d4ff') {
        const colors = Array.isArray(color) ? color : [color];
        const particleCount = 15;

        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            const selectedColor = colors[Math.floor(Math.random() * colors.length)];

            particle.style.cssText = `
                position: fixed;
                width: 6px;
                height: 6px;
                background: ${selectedColor};
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                left: ${x}px;
                top: ${y}px;
            `;

            document.body.appendChild(particle);

            const angle = (Math.PI * 2 * i) / particleCount;
            const velocity = 50 + Math.random() * 50;
            const vx = Math.cos(angle) * velocity;
            const vy = Math.sin(angle) * velocity;

            particle.animate([
                {
                    transform: 'translate(0, 0) scale(1)',
                    opacity: 1
                },
                {
                    transform: `translate(${vx}px, ${vy}px) scale(0)`,
                    opacity: 0
                }
            ], {
                duration: 800 + Math.random() * 400,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            }).onfinish = () => {
                particle.remove();
            };
        }
    }

    // 成功反馈动画
    showSuccessAnimation(element) {
        element.classList.add('animate-pulse');
        this.createParticleExplosion(
            element.offsetLeft + element.offsetWidth / 2,
            element.offsetTop + element.offsetHeight / 2,
            ['#4ade80', '#22c55e', '#16a34a']
        );

        setTimeout(() => {
            element.classList.remove('animate-pulse');
        }, 1000);
    }

    // 错误反馈动画
    showErrorAnimation(element) {
        element.classList.add('shake');

        setTimeout(() => {
            element.classList.remove('shake');
        }, 600);
    }

    // 加载状态动画
    showLoadingState(element, text = '加载中') {
        const originalContent = element.innerHTML;
        element.innerHTML = `
            <span class="loading-spinner"></span>
            <span>${text}</span>
        `;
        element.disabled = true;

        // 添加加载样式
        if (!document.getElementById('loading-styles')) {
            const style = document.createElement('style');
            style.id = 'loading-styles';
            style.textContent = `
                .loading-spinner {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid #f3f3f3;
                    border-top: 2px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-right: 8px;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                .shake {
                    animation: shake 0.6s;
                }

                @keyframes shake {
                    0%, 20%, 40%, 60%, 80% {
                        transform: translateX(0);
                    }
                    10%, 30%, 50%, 70%, 90% {
                        transform: translateX(-5px);
                    }
                }
            `;
            document.head.appendChild(style);
        }

        return {
            hide: () => {
                element.innerHTML = originalContent;
                element.disabled = false;
            }
        };
    }

    // 清理资源
    destroy() {
        this.observers.forEach(observer => {
            observer.disconnect();
        });
        this.observers.clear();
        this.isInitialized = false;
    }
}

// 页面切换管理器
class PageTransitionManager {
    constructor() {
        this.isTransitioning = false;
        this.init();
    }

    init() {
        // 监听页面内导航
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (!link || link.hostname !== location.hostname) return;

            e.preventDefault();
            this.navigateTo(link.href);
        });

        // 浏览器前进后退
        window.addEventListener('popstate', () => {
            this.loadPage(location.href, false);
        });
    }

    async navigateTo(url) {
        if (this.isTransitioning) return;

        this.isTransitioning = true;

        // 页面退出动画
        document.body.classList.add('page-transition-exit');

        await this.delay(300);

        // 加载新页面
        await this.loadPage(url, true);

        // 页面进入动画
        document.body.classList.remove('page-transition-exit');
        document.body.classList.add('page-transition-enter');

        await this.delay(50);

        document.body.classList.remove('page-transition-enter');
        this.isTransitioning = false;
    }

    async loadPage(url, updateHistory = true) {
        try {
            const response = await fetch(url);
            const html = await response.text();

            // 解析新页面内容
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');

            // 更新页面内容
            document.title = newDoc.title;
            document.getElementById('main-content').innerHTML =
                newDoc.getElementById('main-content').innerHTML;

            // 更新历史记录
            if (updateHistory) {
                history.pushState(null, '', url);
            }

            // 重新初始化UI增强
            window.uiEnhancements.init();

        } catch (error) {
            console.error('页面加载失败:', error);
            location.href = url; // 降级到正常导航
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 全局初始化
document.addEventListener('DOMContentLoaded', () => {
    window.uiEnhancements = new UIEnhancements();
    window.pageTransitionManager = new PageTransitionManager();

    // 添加全局CSS类用于动画控制
    document.body.classList.add('ui-enhanced');
});

// 导出工具函数
window.UIUtils = {
    showSuccess: (element) => window.uiEnhancements.showSuccessAnimation(element),
    showError: (element) => window.uiEnhancements.showErrorAnimation(element),
    showLoading: (element, text) => window.uiEnhancements.showLoadingState(element, text),
    createExplosion: (x, y, colors) => window.uiEnhancements.createParticleExplosion(x, y, colors)
};