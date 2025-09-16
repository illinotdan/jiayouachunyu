// 真实API调用和数据管理 - v1.0.1 (修复重复声明问题)

class API {
    constructor() {
        this.baseUrl = CONFIG?.api?.baseUrl || 'http://localhost:5000/api';
        this.cache = new Map();
        this.authToken = this.getAuthToken();
    }
    
    // 获取认证Token
    getAuthToken() {
        const auth = Storage.get('auth');
        return auth?.token || null;
    }
    
    // 设置认证Token
    setAuthToken(token) {
        this.authToken = token;
        const auth = Storage.get('auth') || {};
        auth.token = token;
        Storage.set('auth', auth);
    }
    
    // 清除认证Token
    clearAuthToken() {
        this.authToken = null;
        Storage.remove('auth');
    }
    
    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        // 处理查询参数
        if (options.params) {
            const params = new URLSearchParams();
            Object.entries(options.params).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                    params.append(key, value);
                }
            });
            const paramString = params.toString();
            if (paramString) {
                endpoint += (endpoint.includes('?') ? '&' : '?') + paramString;
            }
        }
        
        const finalUrl = `${this.baseUrl}${endpoint}`;
        const cacheKey = `${finalUrl}_${JSON.stringify(options)}`;
        
        // 检查缓存（只对GET请求缓存）
        if (!options.method || options.method === 'GET') {
            if (this.cache.has(cacheKey)) {
                const cached = this.cache.get(cacheKey);
                if (Date.now() - cached.timestamp < (CONFIG?.cache?.matchesTTL || 300000)) {
                    return cached.data;
                }
            }
        }
        
        try {
            // 准备请求配置
            const requestConfig = {
                method: options.method || 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            };
            
            // 添加认证头
            if (this.authToken) {
                requestConfig.headers['Authorization'] = `Bearer ${this.authToken}`;
            }
            
            // 添加请求体
            if (options.body && typeof options.body === 'object') {
                requestConfig.body = JSON.stringify(options.body);
            }
            
            // 发送请求
            const response = await fetch(url, requestConfig);
            
            // 检查响应状态
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                
                // 处理认证错误
                if (response.status === 401) {
                    this.clearAuthToken();
                    window.location.href = 'login.html';
                    return;
                }
                
                throw new APIError(
                    errorData.error?.message || `HTTP ${response.status}`,
                    errorData.error?.code || 'HTTP_ERROR',
                    response.status,
                    errorData.error?.details
                );
            }
            
            const data = await response.json();
            
            // 缓存GET请求结果
            if (requestConfig.method === 'GET') {
                this.cache.set(cacheKey, {
                    data,
                    timestamp: Date.now()
                });
            }
            
            return data;
            
        } catch (error) {
            console.error('API请求失败:', error);
            
            if (error instanceof APIError) {
                throw error;
            }
            
            // 网络错误或其他错误
            throw new APIError('网络请求失败，请检查网络连接', 'NETWORK_ERROR', 0);
        }
    }
    
    // 认证相关API
    async register(userData) {
        return this.request('/auth/register', {
            method: 'POST',
            body: userData
        });
    }
    
    async login(credentials) {
        return this.request('/auth/login', {
            method: 'POST',
            body: credentials
        });
    }
    
    async logout() {
        return this.request('/auth/logout', {
            method: 'POST'
        });
    }
    
    async getCurrentUser() {
        return this.request('/auth/me');
    }
    
    // 比赛相关API
    async getMatches(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/matches${queryString ? '?' + queryString : ''}`);
    }
    
    async getMatchDetail(matchId) {
        return this.request(`/matches/${matchId}`);
    }
    
    async getLiveMatches() {
        return this.request('/matches/live');
    }
    
    async getMatchStats(matchId) {
        return this.request(`/matches/${matchId}/stats`);
    }
    
    // 比赛讨论相关API
    async getMatchDiscussions(matchId, filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/learning/match-discussions/${matchId}${queryString ? '?' + queryString : ''}`);
    }
    
    async createMatchDiscussion(discussionData) {
        return this.request('/learning/match-discussions', {
            method: 'POST',
            body: discussionData
        });
    }
    
    // 专家/技术分享者API
    async getExperts(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/experts${queryString ? '?' + queryString : ''}`);
    }
    
    async getExpertDetail(expertId) {
        return this.request(`/experts/${expertId}`);
    }
    
    async followExpert(expertId) {
        return this.request(`/experts/${expertId}/follow`, {
            method: 'POST'
        });
    }
    
    // 社区讨论API
    async getDiscussions(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/discussions${queryString ? '?' + queryString : ''}`);
    }
    
    async getDiscussionDetail(discussionId) {
        return this.request(`/discussions/${discussionId}`);
    }
    
    async createDiscussion(discussionData) {
        return this.request('/discussions', {
            method: 'POST',
            body: discussionData
        });
    }
    
    async createReply(discussionId, replyData) {
        return this.request(`/discussions/${discussionId}/replies`, {
            method: 'POST',
            body: replyData
        });
    }
    
    async likeDiscussion(discussionId) {
        return this.request(`/discussions/${discussionId}/like`, {
            method: 'POST'
        });
    }
    
    // 学习相关API
    async getLearningContent(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/learning/content${queryString ? '?' + queryString : ''}`);
    }
    
    async getLearningContentDetail(contentId) {
        return this.request(`/learning/content/${contentId}`);
    }
    
    async updateLearningProgress(contentId, progressData) {
        return this.request(`/learning/content/${contentId}/progress`, {
            method: 'POST',
            body: progressData
        });
    }
    
    async getUserLearningProgress() {
        return this.request('/learning/progress');
    }
    
    async requestAIAnalysis(analysisData) {
        return this.request('/learning/ai-analysis', {
            method: 'POST',
            body: analysisData
        });
    }
    
    async getAIAnalysisResult(requestId) {
        return this.request(`/learning/ai-analysis/${requestId}`);
    }
    
    // 统计数据API - 完整版
    async getHeroStats(filters = {}) {
        return this.request('/stats/heroes', { params: filters });
    }
    
    // 英雄Meta分析API
    async getHeroWinrateRanking(filters = {}) {
        return this.request('/stats/hero/winrate-ranking', { params: filters });
    }
    
    async getHeroPickrateHeatmap(filters = {}) {
        return this.request('/stats/hero/pickrate-heatmap', { params: filters });
    }
    
    async getHeroRoleDistribution(filters = {}) {
        return this.request('/stats/hero/role-distribution', { params: filters });
    }
    
    async getHeroCounterNetwork(filters = {}) {
        return this.request('/stats/hero/counter-network', { params: filters });
    }
    
    // 物品经济分析API
    async getItemPurchaseTrends(filters = {}) {
        return this.request('/stats/item/purchase-trends', { params: filters });
    }
    
    // 比赛数据分析API
    async getMatchDurationDistribution(filters = {}) {
        return this.request('/stats/match/duration-distribution', { params: filters });
    }
    
    async getFirstBloodTiming(filters = {}) {
        return this.request('/stats/match/first-blood-timing', { params: filters });
    }
    
    async getEconomyWinrate(filters = {}) {
        return this.request('/stats/match/economy-winrate', { params: filters });
    }
    
    // 选手表现分析API
    async getPlayerKDADistribution(filters = {}) {
        return this.request('/stats/player/kda-distribution', { params: filters });
    }
    
    async getFarmEfficiencyComparison(filters = {}) {
        return this.request('/stats/player/farm-efficiency', { params: filters });
    }
    
    // 综合分析API
    async getComprehensiveDashboard(filters = {}) {
        return this.request('/stats/dashboard', { params: filters });
    }
    
    async getStatisticsSummary() {
        return this.request('/stats/summary');
    }
    
    // 数据导出API
    async exportChartData(chartType) {
        return this.request(`/stats/export/${chartType}`);
    }
    
    async getStatsHealth() {
        return this.request('/stats/health');
    }
    
    // 兼容旧方法
    async getTeamStats() {
        return this.request('/stats/teams');
    }
    
    async getGeneralStats() {
        return this.getStatisticsSummary();
    }
    
    async getMetaTrends() {
        return this.getHeroPickrateHeatmap({ days: 90 });
    }
    
    // 搜索API
    async search(query, filters = {}) {
        const searchParams = { q: query, ...filters };
        const queryString = new URLSearchParams(searchParams).toString();
        return this.request(`/search?${queryString}`);
    }
    
    // 通知API
    async getNotifications(filters = {}) {
        const queryString = new URLSearchParams(filters).toString();
        return this.request(`/notifications${queryString ? '?' + queryString : ''}`);
    }
    
    async markNotificationRead(notificationId) {
        return this.request(`/notifications/${notificationId}/read`, {
            method: 'PUT'
        });
    }
    
    // 文件上传API
    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/upload/avatar', {
            method: 'POST',
            body: formData,
            headers: {} // 不设置Content-Type，让浏览器自动设置
        });
    }
    
    async uploadImage(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/upload/image', {
            method: 'POST',
            body: formData,
            headers: {} // 不设置Content-Type，让浏览器自动设置
        });
    }
    
    // 清除缓存
    clearCache() {
        this.cache.clear();
    }
    
    // 清除过期缓存
    clearExpiredCache() {
        const now = Date.now();
        for (const [key, value] of this.cache.entries()) {
            if (now - value.timestamp > (CONFIG?.cache?.matchesTTL || 300000)) {
                this.cache.delete(key);
            }
        }
    }
    
    
}

// API错误类
class APIError extends Error {
    constructor(message, code = 'UNKNOWN_ERROR', status = 0, details = null) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.status = status;
        this.details = details;
    }
}

// API状态管理
class APIStatus {
    constructor() {
        this.isOnline = navigator.onLine;
        this.lastError = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        // 监听网络状态
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.retryCount = 0;
            showNotification('网络连接已恢复', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            showNotification('网络连接已断开', 'warning');
        });
    }
    
    canRetry() {
        return this.isOnline && this.retryCount < this.maxRetries;
    }
    
    incrementRetry() {
        this.retryCount++;
    }
    
    resetRetry() {
        this.retryCount = 0;
    }
}

// 创建全局API实例
const api = new API();

// 创建全局API状态管理实例
const apiStatus = new APIStatus();

// API调用包装器，添加重试机制
async function apiCall(apiMethod, ...args) {
    try {
        apiStatus.resetRetry();
        const result = await apiMethod.apply(api, args);
        
        // 检查响应格式
        if (result && result.success === false) {
            throw new APIError(
                result.error?.message || '请求失败',
                result.error?.code || 'API_ERROR',
                0,
                result.error?.details
            );
        }
        
        return result;
        
    } catch (error) {
        apiStatus.lastError = error;
        
        // 如果是网络错误且可以重试
        if (error.code === 'NETWORK_ERROR' && apiStatus.canRetry()) {
            apiStatus.incrementRetry();
            
            // 等待一段时间后重试
            await new Promise(resolve => setTimeout(resolve, 1000 * apiStatus.retryCount));
            
            console.log(`API重试 ${apiStatus.retryCount}/${apiStatus.maxRetries}`);
            return apiCall(apiMethod, ...args);
        }
        
        // 显示错误通知
        if (typeof showNotification === 'function') {
            showNotification(error.message, 'error');
        }
        
        throw error;
    }
}

// 批量API调用
async function batchApiCall(calls) {
    try {
        const results = await Promise.allSettled(calls.map(call => 
            apiCall(call.method, ...call.args)
        ));
        
        return results.map((result, index) => ({
            success: result.status === 'fulfilled',
            data: result.status === 'fulfilled' ? result.value : null,
            error: result.status === 'rejected' ? result.reason : null,
            call: calls[index]
        }));
        
    } catch (error) {
        console.error('批量API调用失败:', error);
        return [];
    }
}

// 定期清理过期缓存
setInterval(() => {
    api.clearExpiredCache();
}, 60000); // 每分钟清理一次

    // ==================== 实时数据同步 API ====================
    
    // 获取同步状态
    async getSyncStatus() {
        try {
            const response = await this.request('/api/realtime/status');
            return response.data;
        } catch (error) {
            console.error('获取同步状态失败:', error);
            throw error;
        }
    }

    // 触发完整数据同步
    async triggerFullSync(hoursBack = 24) {
        try {
            const response = await this.request('/api/realtime/trigger', {
                method: 'POST',
                body: JSON.stringify({
                    type: 'full',
                    hours_back: hoursBack
                })
            });
            return response.data;
        } catch (error) {
            console.error('触发完整数据同步失败:', error);
            throw error;
        }
    }

    // 触发比赛数据同步
    async triggerMatchesSync(hoursBack = 6) {
        try {
            const response = await this.request('/api/realtime/latest-matches', {
                method: 'POST',
                body: JSON.stringify({
                    hours_back: hoursBack
                })
            });
            return response.data;
        } catch (error) {
            console.error('触发比赛数据同步失败:', error);
            throw error;
        }
    }

    // 触发英雄数据同步
    async triggerHeroesSync() {
        try {
            const response = await this.request('/api/realtime/heroes', {
                method: 'POST'
            });
            return response.data;
        } catch (error) {
            console.error('触发英雄数据同步失败:', error);
            throw error;
        }
    }

    // 触动物品数据同步
    async triggerItemsSync() {
        try {
            const response = await this.request('/api/realtime/items', {
                method: 'POST'
            });
            return response.data;
        } catch (error) {
            console.error('触动物品数据同步失败:', error);
            throw error;
        }
    }
}

// 导出全局API实例
window.api = api;
window.apiCall = apiCall;
window.batchApiCall = batchApiCall;
window.APIError = APIError;
