/**
 * 粒子特效系统 - 为页面添加动态视觉效果
 */

class ParticleSystem {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.warn('Particle container not found:', containerId);
            return;
        }

        this.options = {
            particleCount: options.particleCount || 50,
            particleSize: options.particleSize || 2,
            particleSpeed: options.particleSpeed || 1,
            particleColor: options.particleColor || '#00d4ff',
            enableMouse: options.enableMouse !== false,
            connectionDistance: options.connectionDistance || 150,
            fadeDistance: options.fadeDistance || 200,
            ...options
        };

        this.particles = [];
        this.mouse = { x: 0, y: 0 };
        this.isActive = true;

        this.init();
    }

    init() {
        this.createCanvas();
        this.createParticles();
        this.bindEvents();
        this.animate();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';

        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);
        this.container.style.position = 'relative';

        this.resizeCanvas();
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
    }

    createParticles() {
        this.particles = [];
        for (let i = 0; i < this.options.particleCount; i++) {
            this.particles.push(this.createParticle());
        }
    }

    createParticle() {
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            vx: (Math.random() - 0.5) * this.options.particleSpeed,
            vy: (Math.random() - 0.5) * this.options.particleSpeed,
            size: Math.random() * this.options.particleSize + 1,
            opacity: Math.random() * 0.5 + 0.3,
            originalOpacity: Math.random() * 0.5 + 0.3
        };
    }

    bindEvents() {
        if (this.options.enableMouse) {
            this.container.addEventListener('mousemove', (e) => {
                const rect = this.container.getBoundingClientRect();
                this.mouse.x = e.clientX - rect.left;
                this.mouse.y = e.clientY - rect.top;
            });

            this.container.addEventListener('mouseleave', () => {
                this.mouse.x = -1000;
                this.mouse.y = -1000;
            });
        }

        window.addEventListener('resize', () => {
            this.resizeCanvas();
        });
    }

    updateParticle(particle) {
        // 粒子移动
        particle.x += particle.vx;
        particle.y += particle.vy;

        // 边界反弹
        if (particle.x < 0 || particle.x > this.canvas.width) {
            particle.vx *= -1;
        }
        if (particle.y < 0 || particle.y > this.canvas.height) {
            particle.vy *= -1;
        }

        // 鼠标交互
        if (this.options.enableMouse) {
            const dx = this.mouse.x - particle.x;
            const dy = this.mouse.y - particle.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < this.options.fadeDistance) {
                const force = (this.options.fadeDistance - distance) / this.options.fadeDistance;
                particle.vx += dx * force * 0.01;
                particle.vy += dy * force * 0.01;
                particle.opacity = particle.originalOpacity + force * 0.5;
            } else {
                particle.opacity = particle.originalOpacity;
            }
        }

        // 速度衰减
        particle.vx *= 0.99;
        particle.vy *= 0.99;
    }

    drawParticle(particle) {
        this.ctx.save();
        this.ctx.globalAlpha = particle.opacity;
        this.ctx.fillStyle = this.options.particleColor;
        this.ctx.beginPath();
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.restore();
    }

    drawConnections() {
        this.ctx.save();
        this.ctx.strokeStyle = this.options.particleColor;
        this.ctx.lineWidth = 0.5;

        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.options.connectionDistance) {
                    const opacity = (this.options.connectionDistance - distance) / this.options.connectionDistance;
                    this.ctx.globalAlpha = opacity * 0.3;
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }
        this.ctx.restore();
    }

    animate() {
        if (!this.isActive) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 更新和绘制粒子
        this.particles.forEach(particle => {
            this.updateParticle(particle);
            this.drawParticle(particle);
        });

        // 绘制连接线
        this.drawConnections();

        requestAnimationFrame(() => this.animate());
    }

    destroy() {
        this.isActive = false;
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }

    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        this.createParticles();
    }
}

class FloatingParticles {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.options = {
            count: options.count || 20,
            colors: options.colors || ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'],
            minSize: options.minSize || 4,
            maxSize: options.maxSize || 12,
            duration: options.duration || 3000,
            ...options
        };

        this.particles = [];
        this.init();
    }

    init() {
        this.container.style.position = 'relative';
        this.container.style.overflow = 'hidden';
    }

    createFloatingParticle() {
        const particle = document.createElement('div');
        const size = Math.random() * (this.options.maxSize - this.options.minSize) + this.options.minSize;
        const color = this.options.colors[Math.floor(Math.random() * this.options.colors.length)];

        particle.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            background: ${color};
            border-radius: 50%;
            pointer-events: none;
            opacity: 0;
            z-index: 10;
        `;

        // 随机起始位置
        const rect = this.container.getBoundingClientRect();
        particle.style.left = Math.random() * rect.width + 'px';
        particle.style.top = rect.height + 'px';

        this.container.appendChild(particle);

        // 动画效果
        const animation = particle.animate([
            {
                transform: 'translateY(0px) rotate(0deg)',
                opacity: 0
            },
            {
                transform: `translateY(-${rect.height + 100}px) rotate(360deg)`,
                opacity: 1,
                offset: 0.1
            },
            {
                transform: `translateY(-${rect.height + 200}px) rotate(720deg)`,
                opacity: 0
            }
        ], {
            duration: this.options.duration + Math.random() * 2000,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        });

        animation.onfinish = () => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        };

        return particle;
    }

    burst(x, y) {
        const burstCount = 8;
        for (let i = 0; i < burstCount; i++) {
            setTimeout(() => {
                const particle = this.createFloatingParticle();
                particle.style.left = x + 'px';
                particle.style.top = y + 'px';
            }, i * 100);
        }
    }

    startContinuous() {
        if (this.intervalId) return;

        this.intervalId = setInterval(() => {
            this.createFloatingParticle();
        }, 800);
    }

    stopContinuous() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

class MatrixEffect {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.options = {
            characters: options.characters || '01ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ',
            fontSize: options.fontSize || 14,
            speed: options.speed || 50,
            color: options.color || '#0f3',
            density: options.density || 0.02,
            ...options
        };

        this.drops = [];
        this.init();
    }

    init() {
        this.createCanvas();
        this.setupDrops();
        this.animate();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '0';
        this.canvas.style.opacity = '0.1';

        this.ctx = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);
        this.container.style.position = 'relative';

        this.resizeCanvas();
    }

    resizeCanvas() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;

        this.columns = Math.floor(this.canvas.width / this.options.fontSize);
        this.setupDrops();
    }

    setupDrops() {
        this.drops = [];
        for (let i = 0; i < this.columns; i++) {
            this.drops[i] = 1;
        }
    }

    animate() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        this.ctx.fillStyle = this.options.color;
        this.ctx.font = this.options.fontSize + 'px monospace';

        for (let i = 0; i < this.drops.length; i++) {
            const text = this.options.characters.charAt(
                Math.floor(Math.random() * this.options.characters.length)
            );

            this.ctx.fillText(
                text,
                i * this.options.fontSize,
                this.drops[i] * this.options.fontSize
            );

            if (this.drops[i] * this.options.fontSize > this.canvas.height &&
                Math.random() > 0.975) {
                this.drops[i] = 0;
            }

            this.drops[i]++;
        }

        setTimeout(() => {
            requestAnimationFrame(() => this.animate());
        }, this.options.speed);
    }
}

// 初始化粒子效果管理器
class EffectsManager {
    constructor() {
        this.effects = new Map();
    }

    addParticleSystem(id, containerId, options) {
        const effect = new ParticleSystem(containerId, options);
        this.effects.set(id, effect);
        return effect;
    }

    addFloatingParticles(id, containerId, options) {
        const effect = new FloatingParticles(containerId, options);
        this.effects.set(id, effect);
        return effect;
    }

    addMatrixEffect(id, containerId, options) {
        const effect = new MatrixEffect(containerId, options);
        this.effects.set(id, effect);
        return effect;
    }

    removeEffect(id) {
        const effect = this.effects.get(id);
        if (effect && effect.destroy) {
            effect.destroy();
        }
        this.effects.delete(id);
    }

    removeAllEffects() {
        this.effects.forEach((effect, id) => {
            this.removeEffect(id);
        });
    }

    getEffect(id) {
        return this.effects.get(id);
    }
}

// 创建全局效果管理器
window.effectsManager = new EffectsManager();

// 页面加载完成后自动初始化基础效果
document.addEventListener('DOMContentLoaded', () => {
    // 为主要容器添加粒子效果
    const mainContainers = ['main-content', 'hero-section', 'dashboard'];

    mainContainers.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            window.effectsManager.addParticleSystem(`particles-${id}`, id, {
                particleCount: 30,
                particleColor: '#00d4ff',
                enableMouse: true
            });
        }
    });
});