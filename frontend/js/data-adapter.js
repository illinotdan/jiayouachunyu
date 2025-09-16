// 数据适配器 - 处理前后端数据格式转换

class DataAdapter {
    
    // 适配比赛数据格式
    static adaptMatchData(apiMatch) {
        if (!apiMatch) return null;
        
        return {
            id: apiMatch.id || apiMatch.match_id,
            match_id: apiMatch.id || apiMatch.match_id,
            league_name: apiMatch.league?.name || '未知联赛',
            radiant_team: {
                name: apiMatch.radiant?.name || '天辉队伍',
                tag: apiMatch.radiant?.tag || 'RAD',
                logo: apiMatch.radiant?.logo || 'images/placeholder.svg'
            },
            dire_team: {
                name: apiMatch.dire?.name || '夜魇队伍', 
                tag: apiMatch.dire?.tag || 'DIR',
                logo: apiMatch.dire?.logo || 'images/placeholder.svg'
            },
            radiant_win: apiMatch.radiantWin,
            radiant_score: apiMatch.radiant?.score || 0,
            dire_score: apiMatch.dire?.score || 0,
            start_time: apiMatch.startTime,
            duration: apiMatch.duration,
            status: apiMatch.status || 'finished',
            comments_count: apiMatch.commentCount || apiMatch.analysisCount || 0,
            has_expert_analysis: (apiMatch.expertReviews || 0) > 0,
            view_count: apiMatch.viewCount || 0
        };
    }
    
    // 适配讨论数据格式
    static adaptDiscussionData(apiDiscussion) {
        if (!apiDiscussion) return null;
        
        return {
            id: apiDiscussion.id,
            title: apiDiscussion.title,
            content: apiDiscussion.content,
            author: {
                id: apiDiscussion.author?.id,
                name: apiDiscussion.author?.username || apiDiscussion.author?.name,
                avatar: apiDiscussion.author?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${apiDiscussion.author?.username}`,
                reputation: apiDiscussion.author?.reputation || 0,
                tier: apiDiscussion.author?.tier || 'silver'
            },
            category: apiDiscussion.category,
            tags: apiDiscussion.tags || [],
            createdAt: new Date(apiDiscussion.createdAt).getTime(),
            updatedAt: new Date(apiDiscussion.updatedAt || apiDiscussion.createdAt).getTime(),
            replies: apiDiscussion.replyCount || 0,
            views: apiDiscussion.viewCount || 0,
            likes: apiDiscussion.likeCount || 0,
            lastActivity: new Date(apiDiscussion.lastActivity || apiDiscussion.updatedAt || apiDiscussion.createdAt).getTime(),
            isHot: apiDiscussion.isHot || false,
            isPinned: apiDiscussion.isPinned || false,
            isLocked: apiDiscussion.isLocked || false
        };
    }
    
    // 适配专家数据格式
    static adaptExpertData(apiExpert) {
        if (!apiExpert) return null;
        
        return {
            id: apiExpert.id,
            name: apiExpert.username || apiExpert.name,
            title: apiExpert.title || '技术分享者',
            avatar: apiExpert.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${apiExpert.username}`,
            tier: apiExpert.tier || 'silver',
            expertise: apiExpert.expertise || ['技术分析'],
            followers: apiExpert.stats?.followers || 0,
            articles: apiExpert.stats?.articles || 0,
            accuracy: apiExpert.stats?.accuracy || 0,
            bio: apiExpert.bio || '这位技术分享者还没有填写简介',
            verified: apiExpert.verified || false,
            joinDate: apiExpert.createdAt,
            reputation: apiExpert.reputation || 0
        };
    }
    
    // 适配学习内容数据格式
    static adaptLearningContentData(apiContent) {
        if (!apiContent) return null;
        
        return {
            id: apiContent.id,
            title: apiContent.title,
            description: apiContent.description,
            type: apiContent.type,
            category: apiContent.category,
            difficulty: apiContent.difficulty,
            author: apiContent.author?.username || apiContent.author?.name || '匿名',
            views: apiContent.viewCount || 0,
            likes: apiContent.likeCount || 0,
            comments: apiContent.commentCount || 0,
            tags: apiContent.tags || [],
            thumbnail: apiContent.thumbnail || 'images/placeholder.svg',
            createdAt: new Date(apiContent.createdAt).getTime(),
            isVerified: apiContent.isVerified || false,
            isFeatured: apiContent.isFeatured || false,
            qualityScore: apiContent.qualityScore || 0
        };
    }
    
    // 适配统计数据格式
    static adaptStatsData(apiStats) {
        if (!apiStats) return null;
        
        return {
            users: {
                total: apiStats.users?.total || 0,
                experts: apiStats.users?.experts || 0,
                activeWeekly: apiStats.users?.activeWeekly || 0
            },
            content: {
                totalDiscussions: apiStats.content?.totalDiscussions || 0,
                totalArticles: apiStats.content?.totalArticles || 0,
                weeklyDiscussions: apiStats.content?.weeklyDiscussions || 0,
                todayDiscussions: apiStats.content?.todayDiscussions || 0
            },
            matches: {
                total: apiStats.matches?.total || 0,
                analyzed: apiStats.matches?.analyzed || 0,
                analysisRate: apiStats.matches?.analysisRate || 0
            }
        };
    }
    
    // 适配英雄统计数据格式
    static adaptHeroStatsData(apiHeroStats) {
        if (!apiHeroStats) return null;
        
        return apiHeroStats.map(heroStat => ({
            id: heroStat.heroId,
            name: heroStat.hero?.displayName || heroStat.hero?.name,
            role: heroStat.hero?.roles?.[0] || 'Unknown',
            winRate: heroStat.stats?.winRate || 0,
            pickRate: heroStat.stats?.pickRate || 0,
            banRate: heroStat.stats?.banRate || 0,
            totalMatches: heroStat.stats?.totalMatches || 0,
            gradient: DataAdapter.getHeroGradient(heroStat.hero?.primaryAttribute)
        }));
    }
    
    // 获取英雄渐变色
    static getHeroGradient(attribute) {
        const gradients = {
            'strength': 'from-red-500 to-red-600',
            'agility': 'from-green-500 to-green-600',
            'intelligence': 'from-blue-500 to-blue-600',
            'universal': 'from-purple-500 to-purple-600'
        };
        return gradients[attribute] || 'from-gray-500 to-gray-600';
    }
    
    // 适配战队统计数据格式
    static adaptTeamStatsData(apiTeamStats) {
        if (!apiTeamStats) return null;
        
        return apiTeamStats.map((teamStat, index) => ({
            id: teamStat.id,
            name: teamStat.name,
            tag: teamStat.tag,
            logo: teamStat.logo || 'images/placeholder.svg',
            region: teamStat.region,
            ranking: index + 1,
            stats: {
                wins: teamStat.stats?.wins || 0,
                losses: teamStat.stats?.losses || 0,
                winRate: teamStat.stats?.winRate || 0,
                points: teamStat.stats?.points || 0
            },
            trend: teamStat.trend || 'stable'
        }));
    }
    
    // 适配通知数据格式
    static adaptNotificationData(apiNotification) {
        if (!apiNotification) return null;
        
        return {
            id: apiNotification.id,
            type: apiNotification.type,
            title: apiNotification.title,
            content: apiNotification.content,
            data: apiNotification.data || {},
            read: apiNotification.read || false,
            readAt: apiNotification.readAt,
            createdAt: new Date(apiNotification.createdAt).getTime()
        };
    }
    
    // 适配图表数据格式 - 新增
    static adaptChartData(chartResponse) {
        if (!chartResponse || !chartResponse.data) return null;
        
        const chartData = chartResponse.data;
        
        switch (chartData.chart_type) {
            case 'bar_chart':
                return this.adaptBarChartData(chartData);
            case 'heatmap':
                return this.adaptHeatmapData(chartData);
            case 'pie_chart':
                return this.adaptPieChartData(chartData);
            case 'histogram':
                return this.adaptHistogramData(chartData);
            case 'curve_chart':
                return this.adaptCurveChartData(chartData);
            case 'boxplot':
                return this.adaptBoxplotData(chartData);
            case 'radar_chart':
                return this.adaptRadarChartData(chartData);
            case 'network_graph':
                return this.adaptNetworkGraphData(chartData);
            default:
                return chartData;
        }
    }
    
    static adaptBarChartData(chartData) {
        return {
            type: 'bar',
            title: chartData.title,
            categories: chartData.data.overall?.map(item => item.hero_name) || [],
            values: chartData.data.overall?.map(item => item.winrate) || [],
            metadata: chartData.data.meta,
            raw_data: chartData.data.overall
        };
    }
    
    static adaptHeatmapData(chartData) {
        return {
            type: 'heatmap',
            title: chartData.title,
            matrix: chartData.data.matrix || [],
            x_labels: chartData.data.x_labels || [],
            y_labels: chartData.data.y_labels || [],
            metadata: chartData.data.meta
        };
    }
    
    static adaptPieChartData(chartData) {
        return {
            type: 'pie',
            title: chartData.title,
            segments: chartData.data.segments || [],
            total: chartData.data.total_picks,
            metadata: chartData.data.meta
        };
    }
    
    static adaptHistogramData(chartData) {
        return {
            type: 'histogram',
            title: chartData.title,
            bins: chartData.data.bins || [],
            statistics: chartData.data.statistics,
            metadata: chartData.data.meta || {}
        };
    }
    
    static adaptCurveChartData(chartData) {
        return {
            type: 'curve',
            title: chartData.title,
            curve_points: chartData.data.curve_points || [],
            metadata: chartData.data.meta
        };
    }
    
    static adaptBoxplotData(chartData) {
        return {
            type: 'boxplot',
            title: chartData.title,
            statistics: chartData.data.statistics,
            raw_data: chartData.data.raw_data,
            metadata: chartData.data.meta
        };
    }
    
    static adaptRadarChartData(chartData) {
        return {
            type: 'radar',
            title: chartData.title,
            players: chartData.data.players || [],
            dimensions: chartData.data.dimensions || [],
            metadata: chartData.data.meta
        };
    }
    
    static adaptNetworkGraphData(chartData) {
        return {
            type: 'network',
            title: chartData.title,
            nodes: chartData.data.nodes || [],
            edges: chartData.data.edges || [],
            metadata: chartData.data.meta
        };
    }
    
    // 批量适配数据
    static adaptArrayData(apiArray, adaptMethod) {
        if (!Array.isArray(apiArray)) return [];
        
        return apiArray.map(item => adaptMethod(item)).filter(item => item !== null);
    }
    
    // 处理分页数据
    static adaptPaginationData(apiPagination) {
        if (!apiPagination) return null;
        
        return {
            page: apiPagination.page || 1,
            pageSize: apiPagination.pageSize || 20,
            total: apiPagination.total || 0,
            totalPages: apiPagination.totalPages || 1,
            hasNext: apiPagination.hasNext || false,
            hasPrev: apiPagination.hasPrev || false
        };
    }
    
    // 检查数据完整性
    static validateApiResponse(response, requiredFields = []) {
        if (!response) {
            throw new Error('API响应为空');
        }
        
        if (response.success === false) {
            throw new APIError(
                response.error?.message || 'API请求失败',
                response.error?.code || 'API_ERROR',
                0,
                response.error?.details
            );
        }
        
        if (!response.data) {
            throw new Error('API响应缺少data字段');
        }
        
        // 检查必需字段
        for (const field of requiredFields) {
            if (!(field in response.data)) {
                throw new Error(`API响应缺少必需字段: ${field}`);
            }
        }
        
        return true;
    }
    
    // 格式化时间显示
    static formatTimeAgo(timestamp) {
        const now = Date.now();
        const diff = now - (typeof timestamp === 'string' ? new Date(timestamp).getTime() : timestamp);
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return '刚刚';
        if (minutes < 60) return `${minutes}分钟前`;
        if (hours < 24) return `${hours}小时前`;
        if (days < 30) return `${days}天前`;
        
        return new Date(timestamp).toLocaleDateString();
    }
    
    // 格式化数字显示
    static formatNumber(num) {
        if (typeof num !== 'number') return '0';
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    // 格式化时长显示
    static formatDuration(seconds) {
        if (typeof seconds !== 'number') return '00:00';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
}

// 全局错误处理包装器
function withErrorHandling(asyncFunction) {
    return async function(...args) {
        try {
            return await asyncFunction.apply(this, args);
        } catch (error) {
            console.error('操作失败:', error);
            
            if (typeof showNotification === 'function') {
                let message = '操作失败，请稍后重试';
                
                if (error instanceof APIError) {
                    message = error.message;
                } else if (error.message) {
                    message = error.message;
                }
                
                showNotification(message, 'error');
            }
            
            throw error;
        }
    };
}

// 数据加载状态管理
class LoadingState {
    constructor() {
        this.loadingElements = new Map();
    }
    
    show(elementId, message = '正在加载...') {
        const element = document.getElementById(elementId);
        if (element) {
            this.loadingElements.set(elementId, element.innerHTML);
            element.innerHTML = `
                <div class="text-center py-8">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-dota-accent"></div>
                    <p class="mt-4 text-gray-400">${message}</p>
                </div>
            `;
        }
    }
    
    hide(elementId) {
        const element = document.getElementById(elementId);
        const originalContent = this.loadingElements.get(elementId);
        
        if (element && originalContent) {
            element.innerHTML = originalContent;
            this.loadingElements.delete(elementId);
        }
    }
    
    showError(elementId, message, retryCallback = null) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-12">
                    <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                    </svg>
                    <p class="text-dire-500 text-lg mb-2">加载失败</p>
                    <p class="text-gray-400 text-sm mb-4">${message}</p>
                    ${retryCallback ? `
                        <button onclick="${retryCallback.name}()" class="bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                            重新加载
                        </button>
                    ` : ''}
                </div>
            `;
        }
    }
}

// 创建全局实例
const loadingState = new LoadingState();

// 导出全局使用
window.DataAdapter = DataAdapter;
window.withErrorHandling = withErrorHandling;
window.loadingState = loadingState;

// 重写常用的格式化函数，使用DataAdapter
window.getTimeAgo = DataAdapter.formatTimeAgo;
window.formatNumber = DataAdapter.formatNumber;
window.formatDuration = DataAdapter.formatDuration;
