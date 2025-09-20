/**
 * 前端安全防护库 - 世界级安全标准
 * 防护XSS、CSRF、数据泄露等安全威胁
 */

class SecurityManager {
    constructor() {
        this.csrfToken = null;
        this.nonces = new Set();
        this.contentSecurityPolicy = this.initCSP();
        this.sanitizer = new DOMSanitizer();

        // 初始化安全措施
        this.initSecurityMeasures();
    }

    /**
     * 初始化内容安全策略
     */
    initCSP() {
        const meta = document.createElement('meta');
        meta.httpEquiv = 'Content-Security-Policy';
        meta.content = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
            "img-src 'self' data: https:",
            "connect-src 'self' http://localhost:5000 ws://localhost:5000",
            "font-src 'self' data:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ].join('; ');

        if (!document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
            document.head.appendChild(meta);
        }

        return meta.content;
    }

    /**
     * 初始化安全措施
     */
    initSecurityMeasures() {
        // 禁用开发者工具提示（生产环境）
        if (location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            this.disableDevTools();
        }

        // 防止点击劫持
        this.preventClickjacking();

        // 设置安全响应头模拟
        this.setSecurityHeaders();

        // 初始化CSRF防护
        this.initCSRFProtection();

        // 监听可疑活动
        this.initSecurityMonitoring();
    }

    /**
     * 禁用开发者工具（生产环境）
     */
    disableDevTools() {
        // 检测开发者工具
        setInterval(() => {
            const threshold = 160;
            if (window.outerHeight - window.innerHeight > threshold ||
                window.outerWidth - window.innerWidth > threshold) {
                this.handleSecurityViolation('Developer tools detected');
            }
        }, 1000);

        // 禁用右键菜单
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            return false;
        });

        // 禁用F12等快捷键
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F12' ||
                (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'C' || e.key === 'J')) ||
                (e.ctrlKey && e.key === 'U')) {
                e.preventDefault();
                this.handleSecurityViolation('Prohibited key combination');
                return false;
            }
        });
    }

    /**
     * 防止点击劫持
     */
    preventClickjacking() {
        // 检查是否在iframe中
        if (window.self !== window.top) {
            // 可能被嵌入到其他页面中
            document.body.style.display = 'none';
            this.handleSecurityViolation('Potential clickjacking detected');
        }
    }

    /**
     * 设置安全响应头模拟
     */
    setSecurityHeaders() {
        // X-Frame-Options 模拟
        const frameOptions = document.createElement('meta');
        frameOptions.httpEquiv = 'X-Frame-Options';
        frameOptions.content = 'DENY';
        document.head.appendChild(frameOptions);

        // X-Content-Type-Options 模拟
        const contentTypeOptions = document.createElement('meta');
        contentTypeOptions.httpEquiv = 'X-Content-Type-Options';
        contentTypeOptions.content = 'nosniff';
        document.head.appendChild(contentTypeOptions);

        // Referrer Policy
        const referrerPolicy = document.createElement('meta');
        referrerPolicy.name = 'referrer';
        referrerPolicy.content = 'strict-origin-when-cross-origin';
        document.head.appendChild(referrerPolicy);
    }

    /**
     * 初始化CSRF防护
     */
    async initCSRFProtection() {
        try {
            // 从服务器获取CSRF token
            this.csrfToken = await this.getCSRFToken();

            // 为所有表单添加CSRF token
            this.addCSRFTokenToForms();

        } catch (error) {
            console.warn('CSRF token initialization failed:', error);
            // 生成客户端token作为后备
            this.csrfToken = this.generateSecureToken();
        }
    }

    /**
     * 获取CSRF Token
     */
    async getCSRFToken() {
        try {
            const response = await fetch('/api/csrf-token', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                return data.token;
            }
        } catch (error) {
            console.warn('Failed to fetch CSRF token from server');
        }

        return this.generateSecureToken();
    }

    /**
     * 生成安全令牌
     */
    generateSecureToken() {
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    /**
     * 为表单添加CSRF Token
     */
    addCSRFTokenToForms() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            let csrfInput = form.querySelector('input[name="csrf_token"]');
            if (!csrfInput) {
                csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                form.appendChild(csrfInput);
            }
            csrfInput.value = this.csrfToken;
        });
    }

    /**
     * 初始化安全监控
     */
    initSecurityMonitoring() {
        // 监控异常的网络请求
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.logRequest(args[0], args[1]);
            return originalFetch.apply(window, args);
        };

        // 监控DOM修改
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                this.checkForMaliciousContent(mutation);
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true
        });

        // 监控localStorage/sessionStorage访问
        this.monitorStorageAccess();
    }

    /**
     * 记录网络请求
     */
    logRequest(url, options = {}) {
        // 检查可疑的外部请求
        if (typeof url === 'string' && !url.startsWith('/') &&
            !url.startsWith(window.location.origin) &&
            !url.startsWith('http://localhost') &&
            !url.includes('tailwindcss.com')) {

            this.handleSecurityViolation(`Suspicious external request: ${url}`);
        }
    }

    /**
     * 检查恶意内容
     */
    checkForMaliciousContent(mutation) {
        mutation.addedNodes.forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                // 检查脚本注入
                if (node.tagName === 'SCRIPT' && !this.isAllowedScript(node)) {
                    this.handleSecurityViolation('Unauthorized script injection detected');
                    node.remove();
                }

                // 检查iframe注入
                if (node.tagName === 'IFRAME') {
                    this.handleSecurityViolation('Iframe injection detected');
                    node.remove();
                }

                // 检查危险属性
                this.checkDangerousAttributes(node);
            }
        });
    }

    /**
     * 检查是否为允许的脚本
     */
    isAllowedScript(scriptElement) {
        const src = scriptElement.src;
        const allowedSources = [
            window.location.origin,
            'https://cdn.tailwindcss.com'
        ];

        return !src || allowedSources.some(allowed => src.startsWith(allowed));
    }

    /**
     * 检查危险属性
     */
    checkDangerousAttributes(element) {
        const dangerousAttributes = ['onclick', 'onload', 'onerror', 'onmouseover'];

        dangerousAttributes.forEach(attr => {
            if (element.hasAttribute(attr)) {
                this.handleSecurityViolation(`Dangerous attribute detected: ${attr}`);
                element.removeAttribute(attr);
            }
        });
    }

    /**
     * 监控存储访问
     */
    monitorStorageAccess() {
        const sensitiveKeys = ['token', 'password', 'secret', 'auth'];

        const originalSetItem = Storage.prototype.setItem;
        Storage.prototype.setItem = function(key, value) {
            // 检查敏感数据存储
            if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
                console.warn(`Storing sensitive data in ${this === localStorage ? 'localStorage' : 'sessionStorage'}: ${key}`);
            }

            return originalSetItem.apply(this, arguments);
        };
    }

    /**
     * 处理安全违规
     */
    handleSecurityViolation(violation) {
        console.error('Security violation detected:', violation);

        // 记录安全事件
        this.logSecurityEvent(violation);

        // 可以选择性地通知服务器
        if (typeof api !== 'undefined') {
            try {
                api.request('/security/violation', {
                    method: 'POST',
                    body: {
                        violation,
                        timestamp: new Date().toISOString(),
                        userAgent: navigator.userAgent,
                        url: window.location.href
                    }
                }).catch(() => {}); // 静默失败
            } catch (e) {
                // 静默处理
            }
        }
    }

    /**
     * 记录安全事件
     */
    logSecurityEvent(event) {
        const securityLog = JSON.parse(sessionStorage.getItem('securityLog') || '[]');
        securityLog.push({
            event,
            timestamp: new Date().toISOString(),
            url: window.location.href
        });

        // 只保留最近50条记录
        if (securityLog.length > 50) {
            securityLog.splice(0, securityLog.length - 50);
        }

        sessionStorage.setItem('securityLog', JSON.stringify(securityLog));
    }

    /**
     * 获取CSRF Token
     */
    getCSRFTokenForRequest() {
        return this.csrfToken;
    }

    /**
     * 验证请求来源
     */
    validateRequestOrigin(request) {
        const origin = request.headers?.get?.(origin) || document.referrer;
        const allowedOrigins = [
            window.location.origin,
            'http://localhost:5000',
            'http://127.0.0.1:5000'
        ];

        return allowedOrigins.includes(origin);
    }
}

/**
 * DOM内容清理器
 */
class DOMSanitizer {
    constructor() {
        this.allowedTags = new Set([
            'div', 'span', 'p', 'br', 'strong', 'em', 'b', 'i', 'u',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'a', 'img',
            'table', 'thead', 'tbody', 'tr', 'td', 'th'
        ]);

        this.allowedAttributes = new Set([
            'class', 'id', 'href', 'src', 'alt', 'title'
        ]);
    }

    /**
     * 清理HTML内容
     */
    sanitizeHTML(html) {
        const div = document.createElement('div');
        div.innerHTML = html;

        this.cleanElement(div);
        return div.innerHTML;
    }

    /**
     * 清理元素
     */
    cleanElement(element) {
        const children = Array.from(element.children);

        children.forEach(child => {
            // 检查标签是否允许
            if (!this.allowedTags.has(child.tagName.toLowerCase())) {
                child.remove();
                return;
            }

            // 清理属性
            const attributes = Array.from(child.attributes);
            attributes.forEach(attr => {
                if (!this.allowedAttributes.has(attr.name.toLowerCase())) {
                    child.removeAttribute(attr.name);
                }
            });

            // 递归清理子元素
            this.cleanElement(child);
        });
    }

    /**
     * 转义HTML字符
     */
    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 清理用户输入
     */
    sanitizeInput(input) {
        if (typeof input !== 'string') {
            return input;
        }

        // 移除脚本标签
        input = input.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

        // 移除事件处理器
        input = input.replace(/on\w+\s*=\s*"[^"]*"/gi, '');
        input = input.replace(/on\w+\s*=\s*'[^']*'/gi, '');

        // 移除javascript: 协议
        input = input.replace(/javascript:/gi, '');

        return input;
    }
}

/**
 * 安全存储管理器
 */
class SecureStorage {
    constructor() {
        this.prefix = 'secure_';
        this.encryptionKey = this.generateEncryptionKey();
    }

    /**
     * 生成加密密钥
     */
    generateEncryptionKey() {
        // 使用浏览器指纹作为密钥的一部分
        const fingerprint = [
            navigator.userAgent,
            navigator.language,
            screen.width + 'x' + screen.height,
            new Date().getTimezoneOffset()
        ].join('|');

        return btoa(fingerprint).substring(0, 32);
    }

    /**
     * 简单加密（仅混淆，不是真正的加密）
     */
    encrypt(data) {
        const jsonString = JSON.stringify(data);
        const encrypted = btoa(jsonString);
        return encrypted;
    }

    /**
     * 简单解密
     */
    decrypt(encryptedData) {
        try {
            const jsonString = atob(encryptedData);
            return JSON.parse(jsonString);
        } catch (e) {
            return null;
        }
    }

    /**
     * 安全存储
     */
    setItem(key, value, expiry = null) {
        const data = {
            value,
            timestamp: Date.now(),
            expiry: expiry ? Date.now() + expiry : null
        };

        const encrypted = this.encrypt(data);
        localStorage.setItem(this.prefix + key, encrypted);
    }

    /**
     * 安全获取
     */
    getItem(key) {
        const encrypted = localStorage.getItem(this.prefix + key);
        if (!encrypted) return null;

        const data = this.decrypt(encrypted);
        if (!data) return null;

        // 检查过期时间
        if (data.expiry && Date.now() > data.expiry) {
            this.removeItem(key);
            return null;
        }

        return data.value;
    }

    /**
     * 移除项目
     */
    removeItem(key) {
        localStorage.removeItem(this.prefix + key);
    }

    /**
     * 清除所有安全存储项目
     */
    clear() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith(this.prefix)) {
                localStorage.removeItem(key);
            }
        });
    }
}

// 初始化安全管理器
const securityManager = new SecurityManager();
const domSanitizer = new DOMSanitizer();
const secureStorage = new SecureStorage();

// 导出到全局作用域
window.securityManager = securityManager;
window.domSanitizer = domSanitizer;
window.secureStorage = secureStorage;

// 安全工具函数
window.SecurityUtils = {
    /**
     * 安全地设置innerHTML
     */
    safeSetHTML: (element, html) => {
        const cleaned = domSanitizer.sanitizeHTML(html);
        element.innerHTML = cleaned;
    },

    /**
     * 安全地添加事件监听器
     */
    safeAddEventListener: (element, event, handler) => {
        // 移除内联事件处理器
        element.removeAttribute('on' + event);
        element.addEventListener(event, handler);
    },

    /**
     * 验证URL安全性
     */
    isURLSafe: (url) => {
        try {
            const urlObj = new URL(url, window.location.origin);
            const allowedProtocols = ['http:', 'https:'];
            const allowedHosts = [
                window.location.hostname,
                'localhost',
                '127.0.0.1',
                'cdn.tailwindcss.com'
            ];

            return allowedProtocols.includes(urlObj.protocol) &&
                   allowedHosts.includes(urlObj.hostname);
        } catch (e) {
            return false;
        }
    },

    /**
     * 安全重定向
     */
    safeRedirect: (url) => {
        if (SecurityUtils.isURLSafe(url)) {
            window.location.href = url;
        } else {
            console.warn('Unsafe redirect blocked:', url);
        }
    }
};

console.log('🔐 前端安全防护系统已初始化');