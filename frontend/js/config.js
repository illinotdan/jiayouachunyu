// 网站配置文件

const CONFIG = {
    // 网站基本信息
    site: {
        name: '刀塔情书',
        description: '专业的Dota2比赛分析平台',
        version: '1.0.0',
        author: 'Dota2专业解析社区'
    },
    
    // API配置
    api: {
        baseUrl: 'http://localhost:5000/api',
        timeout: 10000,
        retryAttempts: 3,
        fallbackMode: true  // 是否启用备用数据模式
    },
    
    // 分页配置
    pagination: {
        matchesPerPage: 12,
        expertsPerPage: 16,
        discussionsPerPage: 10,
        commentsPerPage: 20
    },
    
    // 缓存配置
    cache: {
        matchesTTL: 5 * 60 * 1000, // 5分钟
        expertsTTL: 10 * 60 * 1000, // 10分钟
        statsTTL: 15 * 60 * 1000 // 15分钟
    },
    
    // 主题配置
    theme: {
        colors: {
            radiant: '#22c55e',
            dire: '#ef4444',
            ancient: '#eab308',
            accent: '#4299e1'
        },
        animations: {
            duration: 300,
            easing: 'ease'
        }
    },
    
    // 功能开关
    features: {
        realTimeUpdates: true,
        notifications: true,
        darkMode: true,
        expertVerification: true,
        communityFeatures: true,
        advancedStats: true,
        dataExport: true,
        interactiveCharts: true
    },
    
    // 图表配置
    charts: {
        defaultTimeRange: 30,
        maxTimeRange: 365,
        refreshInterval: 300000, // 5分钟
        supportedTypes: [
            'bar_chart', 'line_chart', 'pie_chart', 'heatmap', 
            'network_graph', 'histogram', 'boxplot', 'radar_chart'
        ],
        colors: {
            primary: '#4299e1',
            radiant: '#22c55e',
            dire: '#ef4444',
            neutral: '#94a3b8',
            gradient: ['#4299e1', '#22c55e', '#eab308', '#ef4444']
        }
    },
    
    // 外部链接
    links: {
        steam: 'https://steamcommunity.com',
        opendota: 'https://www.opendota.com',
        stratz: 'https://stratz.com',
        github: 'https://github.com',
        discord: 'https://discord.gg'
    },
    
    // 默认头像和图片
    defaults: {
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=default',
        teamLogo: 'images/placeholder.svg',
        heroImage: 'images/placeholder.svg'
    }
};

// 导出配置对象
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}

// 本地存储工具 - 移动到config.js以便在api.js之前定义
const Storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('存储失败:', e);
        }
    },
    
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('读取存储失败:', e);
            return defaultValue;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('删除存储失败:', e);
        }
    }
};
