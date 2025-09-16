// 错误处理和状态管理工具
// 提供统一的错误处理、loading状态、通知等功能

class ErrorHandler {
    static showError(message, type = 'error', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg text-white font-medium max-w-sm ${
            type === 'error' ? 'bg-dire-600' :
            type === 'warning' ? 'bg-ancient-600' :
            type === 'success' ? 'bg-radiant-600' :
            'bg-dota-accent'
        }`;
        
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <span class="mr-2">
                        ${type === 'error' ? '❌' :
                          type === 'warning' ? '⚠️' :
                          type === 'success' ? '✅' :
                          'ℹ️'}
                    </span>
                    <span>${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    ✕
                </button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, duration);
        }
        
        return toast;
    }
    
    static showSuccess(message, duration = 3000) {
        return this.showError(message, 'success', duration);
    }
    
    static showWarning(message, duration = 4000) {
        return this.showError(message, 'warning', duration);
    }
    
    static showInfo(message, duration = 3000) {
        return this.showError(message, 'info', duration);
    }
    
    // 处理API错误
    static handleApiError(error, context = '') {
        console.error(`API错误 ${context}:`, error);
        
        if (error.code === 'NETWORK_ERROR') {
            this.showError('网络连接失败，请检查网络设置');
        } else if (error.code === 'TIMEOUT_ERROR') {
            this.showError('请求超时，请稍后重试');
        } else if (error.code === 'AUTH_ERROR') {
            this.showError('认证失败，请重新登录');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else if (error.code === 'RATE_LIMIT_EXCEEDED') {
            this.showWarning('请求过于频繁，请稍后再试');
        } else {
            this.showError(error.message || '操作失败，请稍后重试');
        }
    }
}

class LoadingManager {
    constructor() {
        this.loadingStates = new Map();
    }
    
    show(containerId, message = '正在加载...') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        this.loadingStates.set(containerId, true);
        
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full">
                <div class="relative">
                    <div class="w-12 h-12 border-4 border-gray-600 border-t-dota-accent rounded-full animate-spin"></div>
                    <div class="absolute inset-0 w-12 h-12 border-4 border-transparent border-r-dota-accent rounded-full animate-spin animation-delay-150"></div>
                </div>
                <p class="text-gray-400 mt-4 text-center">${message}</p>
            </div>
        `;
    }
    
    hide(containerId) {
        this.loadingStates.set(containerId, false);
        // 内容会被实际数据替换，这里不需要特别处理
    }
    
    isLoading(containerId) {
        return this.loadingStates.get(containerId) || false;
    }
    
    showGlobalLoading(message = '正在处理...') {
        const existing = document.getElementById('global-loading');
        if (existing) existing.remove();
        
        const overlay = document.createElement('div');
        overlay.id = 'global-loading';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-dota-panel rounded-lg p-8 max-w-sm mx-4 text-center border border-dota-border">
                <div class="relative mb-4">
                    <div class="w-16 h-16 border-4 border-gray-600 border-t-dota-accent rounded-full animate-spin mx-auto"></div>
                </div>
                <p class="text-white font-medium">${message}</p>
                <p class="text-gray-400 text-sm mt-2">请稍候...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }
    
    hideGlobalLoading() {
        const overlay = document.getElementById('global-loading');
        if (overlay) {
            overlay.remove();
        }
    }
}

class StateManager {
    constructor() {
        this.states = new Map();
        this.listeners = new Map();
    }
    
    setState(key, value) {
        const oldValue = this.states.get(key);
        this.states.set(key, value);
        
        // 触发监听器
        const listeners = this.listeners.get(key) || [];
        listeners.forEach(listener => {
            try {
                listener(value, oldValue);
            } catch (error) {
                console.error(`状态监听器错误 ${key}:`, error);
            }
        });
    }
    
    getState(key, defaultValue = null) {
        return this.states.get(key) || defaultValue;
    }
    
    subscribe(key, listener) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        this.listeners.get(key).push(listener);
        
        // 返回取消订阅函数
        return () => {
            const listeners = this.listeners.get(key) || [];
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        };
    }
    
    // 批量更新状态
    updateStates(states) {
        Object.entries(states).forEach(([key, value]) => {
            this.setState(key, value);
        });
    }
}

class NetworkMonitor {
    constructor() {
        this.isOnline = navigator.onLine;
        this.listeners = [];
        
        this.init();
    }
    
    init() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.notifyListeners('online');
            ErrorHandler.showSuccess('网络连接已恢复');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.notifyListeners('offline');
            ErrorHandler.showWarning('网络连接已断开', 0);
        });
    }
    
    addListener(listener) {
        this.listeners.push(listener);
    }
    
    removeListener(listener) {
        const index = this.listeners.indexOf(listener);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }
    
    notifyListeners(status) {
        this.listeners.forEach(listener => {
            try {
                listener(status, this.isOnline);
            } catch (error) {
                console.error('网络状态监听器错误:', error);
            }
        });
    }
}

class PerformanceMonitor {
    constructor() {
        this.metrics = new Map();
        this.enabled = CONFIG?.features?.performanceMonitoring || false;
    }
    
    startTiming(label) {
        if (!this.enabled) return;
        
        this.metrics.set(label, {
            start: performance.now(),
            label: label
        });
    }
    
    endTiming(label) {
        if (!this.enabled) return;
        
        const metric = this.metrics.get(label);
        if (metric) {
            const duration = performance.now() - metric.start;
            console.log(`⏱️ ${label}: ${duration.toFixed(2)}ms`);
            
            // 记录慢操作
            if (duration > 1000) {
                console.warn(`🐌 慢操作检测: ${label} 耗时 ${duration.toFixed(2)}ms`);
            }
            
            this.metrics.delete(label);
            return duration;
        }
    }
    
    measureAsync(label, asyncFn) {
        if (!this.enabled) return asyncFn();
        
        this.startTiming(label);
        return asyncFn().finally(() => {
            this.endTiming(label);
        });
    }
}

// 全局实例
const errorHandler = ErrorHandler;
const loadingManager = new LoadingManager();
const stateManager = new StateManager();
const networkMonitor = new NetworkMonitor();
const performanceMonitor = new PerformanceMonitor();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ErrorHandler,
        LoadingManager,
        StateManager,
        NetworkMonitor,
        PerformanceMonitor,
        errorHandler,
        loadingManager,
        stateManager,
        networkMonitor,
        performanceMonitor
    };
}
