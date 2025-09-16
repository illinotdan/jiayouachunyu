// 比赛讨论版JavaScript - 纯API版本

let currentMatch = null;
let currentTab = 'general';
let discussions = [];

document.addEventListener('DOMContentLoaded', function() {
    initMatchDiscussionPage();
});

function initMatchDiscussionPage() {
    // 从URL获取比赛ID
    const urlParams = new URLSearchParams(window.location.search);
    const matchId = urlParams.get('id');
    
    if (matchId) {
        loadMatchInfo(matchId);
        loadMatchDiscussions(matchId);
    } else {
        showError('无效的比赛ID');
    }
    
    // 初始化标签页
    initTabs();
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
    
    // 筛选和显示对应内容
    filterDiscussions();
}

async function loadMatchInfo(matchId) {
    try {
        // 从API获取真实比赛信息
        const response = await apiCall(api.getMatchDetail, matchId);
        DataAdapter.validateApiResponse(response, ['match']);
        currentMatch = DataAdapter.adaptMatchData(response.data.match);
        
        renderMatchInfo();
        generateAIAnalysis();
        
    } catch (error) {
        console.error('加载比赛信息失败:', error);
        showError('无法加载比赛信息，请确保后端服务已启动');
    }
}

async function loadMatchDiscussions(matchId) {
    try {
        // 从API获取真实讨论数据
        const response = await apiCall(api.getMatchDiscussions, matchId);
        DataAdapter.validateApiResponse(response, ['discussions']);
        discussions = response.data.discussions || [];
        
        // 更新统计信息
        updateDiscussionStats();
        
        // 渲染讨论列表
        filterDiscussions();
        
    } catch (error) {
        console.error('加载讨论失败:', error);
        showDiscussionsError('无法加载讨论数据');
    }
}

function renderMatchInfo() {
    const loading = document.getElementById('match-loading');
    const container = document.getElementById('match-info');
    const titleElement = document.getElementById('match-title');
    
    if (loading) loading.style.display = 'none';
    if (titleElement) titleElement.textContent = `${currentMatch.radiant_team.name} vs ${currentMatch.dire_team.name}`;
    
    const timeAgo = getTimeAgo(currentMatch.start_time);
    const duration = formatDuration(currentMatch.duration);
    
    container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold">${currentMatch.league_name}</h2>
            <div class="flex items-center space-x-2">
                <span class="bg-radiant-600 text-white px-3 py-1 rounded-full text-sm">已结束</span>
                <span class="text-gray-400 text-sm">${timeAgo}</span>
            </div>
        </div>
        
        <div class="grid grid-cols-3 gap-6 items-center bg-dota-bg/50 rounded-lg p-6">
            <!-- 天辉 -->
            <div class="text-center">
                <img src="${currentMatch.radiant_team.logo}" alt="${currentMatch.radiant_team.name}" class="w-16 h-16 mx-auto mb-3 rounded-full bg-dota-panel p-2">
                <h3 class="font-semibold text-lg ${currentMatch.radiant_win ? 'text-radiant-500' : 'text-gray-400'}">${currentMatch.radiant_team.name}</h3>
                <div class="text-3xl font-bold ${currentMatch.radiant_win ? 'text-radiant-500' : 'text-gray-400'} mt-2">
                    ${currentMatch.radiant_score}
                </div>
            </div>
            
            <!-- VS -->
            <div class="text-center">
                <div class="text-gray-400 text-lg font-bold mb-2">VS</div>
                <div class="text-gray-400 text-sm">比赛时长</div>
                <div class="text-dota-accent font-medium">${duration}</div>
            </div>
            
            <!-- 夜魇 -->
            <div class="text-center">
                <img src="${currentMatch.dire_team.logo}" alt="${currentMatch.dire_team.name}" class="w-16 h-16 mx-auto mb-3 rounded-full bg-dota-panel p-2">
                <h3 class="font-semibold text-lg ${!currentMatch.radiant_win ? 'text-dire-500' : 'text-gray-400'}">${currentMatch.dire_team.name}</h3>
                <div class="text-3xl font-bold ${!currentMatch.radiant_win ? 'text-dire-500' : 'text-gray-400'} mt-2">
                    ${currentMatch.dire_score}
                </div>
            </div>
        </div>
    `;
}

// 其他函数保持不变，但移除所有模拟数据生成
function filterDiscussions() {
    let filteredDiscussions = discussions;
    
    if (currentTab !== 'general') {
        filteredDiscussions = discussions.filter(d => d.category === currentTab);
    }
    
    renderDiscussions(filteredDiscussions);
}

function renderDiscussions(discussionsToRender) {
    const container = document.getElementById('discussions-container');
    const loading = document.getElementById('discussions-loading');
    
    if (loading) loading.style.display = 'none';
    
    if (!discussionsToRender || discussionsToRender.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">这个版块还没有讨论</p>
                <p class="text-gray-500 text-sm">成为第一个发帖的人</p>
                <button class="mt-4 bg-radiant-600 hover:bg-radiant-700 text-white px-6 py-2 rounded-lg transition-colors">
                    📝 发表新帖子
                </button>
            </div>
        `;
        return;
    }
    
    // 渲染讨论列表的代码保持不变
    container.innerHTML = discussionsToRender.map(discussion => {
        const timeAgo = getTimeAgo(discussion.createdAt);
        const categoryInfo = getCategoryInfo(discussion.category);
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewDiscussion(${discussion.id})">
                <!-- 讨论内容渲染 -->
                <h3 class="text-lg font-semibold text-white">${discussion.title}</h3>
                <p class="text-gray-400 text-sm">${discussion.content}</p>
                <div class="text-xs text-gray-500 mt-2">${timeAgo} • ${discussion.author?.name || '匿名'}</div>
            </div>
        `;
    }).join('');
}

function generateAIAnalysis() {
    // 这个函数可以保留，因为它是基于当前比赛生成AI建议
    const aiContainer = document.getElementById('ai-analysis');
    const suggestionsContainer = document.getElementById('ai-suggestions');
    
    if (!currentMatch || !aiContainer) return;
    
    // 基于真实比赛数据生成AI分析建议
    const suggestions = [
        {
            type: 'tactical',
            title: '战术要点',
            content: `分析 ${currentMatch.radiant_team.name} vs ${currentMatch.dire_team.name} 的战术执行细节`
        },
        {
            type: 'learning',
            title: '学习建议',
            content: '观察比赛中的关键决策点，学习职业队伍的团队配合'
        },
        {
            type: 'discussion',
            title: '讨论话题',
            content: '可以讨论两队在不同游戏阶段的战术选择和执行效果'
        }
    ];
    
    if (suggestionsContainer) {
        suggestionsContainer.innerHTML = suggestions.map(suggestion => `
            <div class="bg-dota-bg/30 rounded-lg p-3 border border-dota-border/50">
                <h4 class="font-medium text-blue-400 mb-1">${suggestion.title}</h4>
                <p class="text-sm">${suggestion.content}</p>
            </div>
        `).join('');
        
        aiContainer.style.display = 'block';
    }
}

function updateDiscussionStats() {
    const discussionCount = document.getElementById('discussion-count');
    const activeUsers = document.getElementById('active-users');
    
    if (discussionCount) {
        discussionCount.textContent = discussions.length;
    }
    
    if (activeUsers) {
        // 这个数字应该从API获取，暂时显示0
        activeUsers.textContent = '0';
    }
}

function getCategoryInfo(category) {
    const categoryMap = {
        general: {
            name: '综合讨论',
            icon: '💬',
            color: 'bg-dota-accent/20 text-dota-accent border-dota-accent/30'
        },
        tactics: {
            name: '战术分析',
            icon: '🎯',
            color: 'bg-radiant-600/20 text-radiant-400 border-radiant-600/30'
        },
        highlights: {
            name: '精彩时刻',
            icon: '⭐',
            color: 'bg-ancient-600/20 text-ancient-400 border-ancient-600/30'
        },
        learning: {
            name: '学习要点',
            icon: '📚',
            color: 'bg-blue-600/20 text-blue-400 border-blue-600/30'
        },
        qa: {
            name: '问答互助',
            icon: '❓',
            color: 'bg-purple-600/20 text-purple-400 border-purple-600/30'
        }
    };
    
    return categoryMap[category] || categoryMap.general;
}

function viewDiscussion(discussionId) {
    window.location.href = `discussion.html?id=${discussionId}&match=${currentMatch.match_id}`;
}

function showError(message) {
    const container = document.getElementById('discussions-container');
    container.innerHTML = `
        <div class="text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 text-lg">${message}</p>
            <button onclick="window.history.back()" class="mt-4 bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                返回上一页
            </button>
        </div>
    `;
}

function showDiscussionsError(message) {
    const container = document.getElementById('discussions-container');
    container.innerHTML = `
        <div class="text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 text-lg">${message}</p>
            <p class="text-gray-400 text-sm mb-4">请确保后端服务已启动</p>
            <button onclick="loadMatchDiscussions(currentMatch?.match_id)" class="mt-4 bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                重新加载
            </button>
        </div>
    `;
}
