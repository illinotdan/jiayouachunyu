// 社区页面 - 纯API版本，无模拟数据

let allDiscussions = [];
let filteredDiscussions = [];
let currentTab = 'all';

document.addEventListener('DOMContentLoaded', function() {
    initCommunityPage();
});

function initCommunityPage() {
    // 初始化标签页
    initTabs();
    
    // 加载讨论数据
    loadAllDiscussions();
    
    // 加载社区统计
    loadCommunityStats();
}

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    // 更新标签按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active', 'border-dota-accent', 'text-dota-accent');
        btn.classList.add('text-gray-400');
    });
    
    const activeButton = document.querySelector(`[data-tab="${tab}"]`);
    if (activeButton) {
        activeButton.classList.remove('text-gray-400');
        activeButton.classList.add('active', 'border-dota-accent', 'text-dota-accent');
    }
    
    // 重新加载数据
    loadAllDiscussions();
}

async function loadAllDiscussions() {
    try {
        // 显示加载状态
        const loading = document.getElementById('discussions-loading');
        if (loading) loading.style.display = 'block';
        
        // 构建API请求参数
        const filters = {
            page: 1,
            page_size: 20,
            sort: 'latest'
        };
        
        if (currentTab !== 'all') {
            filters.category = currentTab;
        }
        
        // 调用真实API
        const response = await apiCall(api.getDiscussions, filters);
        
        DataAdapter.validateApiResponse(response, ['discussions']);
        
        allDiscussions = response.data.discussions || [];
        
        renderDiscussions(allDiscussions);
        
        // 更新统计信息
        if (response.data.stats) {
            updateCommunityStats(response.data.stats);
        }
        
    } catch (error) {
        console.error('加载讨论数据失败:', error);
        showDiscussionsError(error.message);
    } finally {
        // 隐藏加载状态
        const loading = document.getElementById('discussions-loading');
        if (loading) loading.style.display = 'none';
    }
}

async function loadCommunityStats() {
    try {
        const response = await apiCall(api.getDiscussionStats);
        
        if (response && response.data) {
            updateCommunityStatsDisplay(response.data);
        }
        
    } catch (error) {
        console.warn('加载社区统计失败:', error);
        // 统计数据失败不影响主要功能
    }
}

function renderDiscussions(discussions) {
    const container = document.getElementById('discussions-container');
    
    if (!discussions || discussions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">该分类下暂无讨论</p>
                <p class="text-gray-500 text-sm">成为第一个发起讨论的人</p>
                <button class="mt-4 bg-radiant-600 hover:bg-radiant-700 text-white px-6 py-2 rounded-lg transition-colors">
                    发布新讨论
                </button>
            </div>
        `;
        return;
    }
    
    container.innerHTML = discussions.map(discussion => {
        const timeAgo = getTimeAgo(discussion.createdAt);
        const lastActivityAgo = getTimeAgo(discussion.lastActivity || discussion.updatedAt);
        const categoryInfo = getCategoryInfo(discussion.category);
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewDiscussion(${discussion.id})">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2 flex-wrap">
                            <span class="tag ${categoryInfo.color}">
                                ${categoryInfo.name}
                            </span>
                            ${discussion.isHot ? `
                                <span class="tag bg-dire-600/20 text-dire-400 border-dire-600/30 animate-pulse">
                                    🔥 热门
                                </span>
                            ` : ''}
                            ${discussion.isPinned ? `
                                <span class="tag bg-ancient-600/20 text-ancient-400 border-ancient-600/30">
                                    📌 置顶
                                </span>
                            ` : ''}
                        </div>
                        
                        <h3 class="text-xl font-semibold mb-2 text-white hover:text-dota-accent transition-colors line-clamp-2">
                            ${discussion.title}
                        </h3>
                        
                        <p class="text-gray-400 mb-3 line-clamp-2 text-sm">
                            ${discussion.content || ''}
                        </p>
                        
                        <div class="flex items-center gap-2 mb-3 flex-wrap">
                            ${(discussion.tags || []).map(tag => `
                                <span class="text-xs bg-dota-panel/50 text-gray-400 px-2 py-1 rounded border border-dota-border">
                                    #${tag}
                                </span>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <div class="flex items-center gap-2">
                            <div class="w-8 h-8 bg-gradient-to-r from-radiant-500 to-radiant-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                                ${(discussion.author?.name || discussion.author?.username || 'U').charAt(0)}
                            </div>
                            <div>
                                <div class="text-sm font-medium text-white">${discussion.author?.name || discussion.author?.username || '匿名用户'}</div>
                                <div class="text-xs text-gray-400">声望: ${formatNumber(discussion.author?.reputation || 0)}</div>
                            </div>
                        </div>
                        
                        <div class="text-sm text-gray-400">
                            <div>发布于 ${timeAgo}</div>
                            <div class="text-xs">最后活动 ${lastActivityAgo}</div>
                        </div>
                    </div>

                    <div class="flex items-center gap-4 text-sm text-gray-400">
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                            <span>${formatNumber(discussion.viewCount || 0)}</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                            <span>${discussion.replyCount || 0}</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                            <span>${discussion.likeCount || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function showDiscussionsError(message) {
    const container = document.getElementById('discussions-container');
    container.innerHTML = `
        <div class="text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 mb-4">无法加载讨论数据</p>
            <p class="text-gray-400 text-sm mb-4">${message}</p>
            <p class="text-gray-500 text-xs mb-4">请确保后端服务已启动</p>
            <button onclick="loadAllDiscussions()" class="bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                重新加载
            </button>
        </div>
    `;
}

function getCategoryInfo(category) {
    // TODO: 从API获取真实分类配置
    const categoryMap = {
        analysis: {
            name: '技术分析', // TODO: 从API获取真实分类名称
            color: 'bg-radiant-600/20 text-radiant-400 border-radiant-600/30'
        },
        strategy: {
            name: '战术讨论', // TODO: 从API获取真实分类名称
            color: 'bg-dota-accent/20 text-dota-accent border-dota-accent/30'
        },
        guides: {
            name: '攻略分享', // TODO: 从API获取真实分类名称
            color: 'bg-ancient-600/20 text-ancient-400 border-ancient-600/30'
        },
        qa: {
            name: '问答互助', // TODO: 从API获取真实分类名称
            color: 'bg-purple-600/20 text-purple-400 border-purple-600/30'
        },
        news: {
            name: '游戏资讯', // TODO: 从API获取真实分类名称
            color: 'bg-blue-600/20 text-blue-400 border-blue-600/30'
        }
    };
    
    return categoryMap[category] || categoryMap.analysis;
}

function updateCommunityStats(stats) {
    // 更新统计卡片显示
    const statsMap = {
        'total-discussions': stats.totalDiscussions,
        'active-users': stats.activeUsers,
        'today-posts': stats.todayPosts,
        'total-replies': stats.totalReplies
    };
    
    Object.entries(statsMap).forEach(([className, value]) => {
        const elements = document.querySelectorAll(`.stat-number:contains("${className}")`);
        elements.forEach(element => {
            if (value !== undefined) {
                element.textContent = formatNumber(value);
            }
        });
    });
}

function updateCommunityStatsDisplay(stats) {
    // 更新页面上的统计数字
    const statElements = document.querySelectorAll('.stat-number');
    
    statElements.forEach((element, index) => {
        let value = 0;
        switch (index) {
            case 0: value = stats.totalDiscussions || 0; break;
            case 1: value = stats.activeUsers || 0; break;
            case 2: value = stats.todayPosts || 0; break;
            case 3: value = stats.totalReplies || 0; break;
        }
        element.textContent = formatNumber(value);
    });
}

function viewDiscussion(discussionId) {
    window.location.href = `discussion.html?id=${discussionId}`;
}

function likeDiscussion(discussionId, event) {
    event.stopPropagation();
    
    // 调用点赞API
    apiCall(api.likeDiscussion, discussionId)
        .then(response => {
            if (response && response.data) {
                showNotification(response.data.isLiked ? '已点赞' : '已取消点赞', 'success');
                // 重新加载讨论列表以更新点赞数
                loadAllDiscussions();
            }
        })
        .catch(error => {
            console.error('点赞操作失败:', error);
            showNotification('操作失败，请稍后重试', 'error');
        });
}
