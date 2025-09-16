// 比赛详情页JavaScript

let currentMatch = null;
let currentTab = 'overview';

document.addEventListener('DOMContentLoaded', function() {
    initMatchPage();
});

function initMatchPage() {
    // 从URL获取比赛ID
    const urlParams = new URLSearchParams(window.location.search);
    const matchId = urlParams.get('id');
    
    if (matchId) {
        loadMatchDetails(matchId);
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
    activeButton.classList.remove('text-gray-400');
    activeButton.classList.add('active', 'border-dota-accent', 'text-dota-accent');
    
    // 渲染对应的标签页内容
    renderTabContent(tab);
}

async function loadMatchDetails(matchId) {
    try {
        // 模拟加载延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟比赛详情数据
        currentMatch = generateMockMatchDetail(matchId);
        
        renderMatchHeader();
        renderTabContent(currentTab);
        
        // 显示标签页
        document.getElementById('match-tabs').style.display = 'block';
        
    } catch (error) {
        console.error('加载比赛详情失败:', error);
        showError('加载比赛详情失败，请稍后重试');
    }
}

function generateMockMatchDetail(matchId) {
    // TODO: 从API获取真实比赛数据
    console.warn('正在使用模拟比赛数据，请实现API集成');
    return {
        match_id: matchId,
        league_name: "数据加载中...",
        radiant_team: {
            name: "队伍1",
            tag: "T1",
            logo: "https://api.dicebear.com/7.x/identicon/svg?seed=team1"
        },
        dire_team: {
            name: "队伍2",
            tag: "T2",
            logo: "https://api.dicebear.com/7.x/identicon/svg?seed=team2"
        },
        radiant_win: false,
        radiant_score: 0,
        dire_score: 0,
        start_time: Date.now(),
        duration: 0,
        status: 'upcoming',
        analysis: {
            keyMoments: [],
            mvp: '',
            turningPoint: '',
            prediction: {
                confidence: 0,
                reasoning: ''
            }
        },
        players: {
            radiant: [],
            dire: []
        },
        expertAnalysis: []
    };
}

function renderMatchHeader() {
    const loading = document.getElementById('match-loading');
    const container = document.getElementById('match-header');
    const titleElement = document.getElementById('match-title');
    
    if (loading) loading.style.display = 'none';
    if (titleElement) titleElement.textContent = currentMatch.league_name;
    
    const timeAgo = getTimeAgo(currentMatch.start_time);
    const duration = formatDuration(currentMatch.duration);
    
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- 比赛结果 -->
            <div class="lg:col-span-2">
                <div class="flex justify-between items-center mb-6">
                    <h1 class="text-2xl font-bold">${currentMatch.league_name}</h1>
                    <div class="flex items-center space-x-2">
                        <span class="bg-radiant-600 text-white px-3 py-1 rounded-full text-sm">已结束</span>
                        <span class="text-gray-400 text-sm">${timeAgo}</span>
                    </div>
                </div>
                
                <div class="bg-dota-bg/50 rounded-lg p-6 border border-dota-border">
                    <div class="grid grid-cols-3 gap-6 items-center">
                        <!-- 天辉 -->
                        <div class="text-center">
                            <img src="${currentMatch.radiant_team.logo}" alt="${currentMatch.radiant_team.name}" class="w-20 h-20 mx-auto mb-3 rounded-full bg-dota-panel p-2">
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
                            <img src="${currentMatch.dire_team.logo}" alt="${currentMatch.dire_team.name}" class="w-20 h-20 mx-auto mb-3 rounded-full bg-dota-panel p-2">
                            <h3 class="font-semibold text-lg ${!currentMatch.radiant_win ? 'text-dire-500' : 'text-gray-400'}">${currentMatch.dire_team.name}</h3>
                            <div class="text-3xl font-bold ${!currentMatch.radiant_win ? 'text-dire-500' : 'text-gray-400'} mt-2">
                                ${currentMatch.dire_score}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 快速统计 -->
            <div class="space-y-4">
                <div class="bg-dota-bg/50 rounded-lg p-4 border border-dota-border">
                    <h4 class="font-semibold mb-3">比赛统计</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span class="text-gray-400">比赛ID:</span>
                            <span class="font-mono">${currentMatch.match_id}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">开始时间:</span>
                            <span>${new Date(currentMatch.start_time).toLocaleString()}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">比赛时长:</span>
                            <span>${duration}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">MVP:</span>
                            <span class="text-radiant-500">${currentMatch.analysis.mvp}</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-dota-bg/50 rounded-lg p-4 border border-dota-border">
                    <h4 class="font-semibold mb-3">AI预测</h4>
                    <div class="text-center">
                        <div class="text-2xl font-bold text-radiant-500 mb-1">${currentMatch.analysis.prediction.confidence}%</div>
                        <div class="text-xs text-gray-400 mb-3">预测置信度</div>
                        <p class="text-sm text-gray-300">${currentMatch.analysis.prediction.reasoning}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderTabContent(tab) {
    const container = document.getElementById('tab-content');
    
    switch (tab) {
        case 'overview':
            renderOverview(container);
            break;
        case 'analysis':
            renderAnalysis(container);
            break;
        case 'data':
            renderData(container);
            break;
        case 'comments':
            renderComments(container);
            break;
    }
}

function renderOverview(container) {
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- 关键时刻 -->
            <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">关键时刻</h3>
                <div class="timeline">
                    ${currentMatch.analysis.keyMoments.map(moment => `
                        <div class="timeline-item">
                            <div class="flex items-start space-x-3">
                                <span class="bg-dota-accent text-white px-2 py-1 rounded text-sm font-mono">${moment.time}</span>
                                <div>
                                    <div class="font-medium text-white">${moment.event}</div>
                                    <div class="text-sm text-gray-400">${moment.description}</div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            
            <!-- 转折点分析 -->
            <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                <h3 class="text-xl font-semibold mb-4">转折点分析</h3>
                <div class="space-y-4">
                    <div class="bg-dota-bg/50 rounded-lg p-4">
                        <h4 class="font-medium text-radiant-500 mb-2">比赛MVP</h4>
                        <p class="text-gray-300">${currentMatch.analysis.mvp} - 关键时刻的出色发挥带领队伍获得胜利</p>
                    </div>
                    <div class="bg-dota-bg/50 rounded-lg p-4">
                        <h4 class="font-medium text-ancient-500 mb-2">转折点</h4>
                        <p class="text-gray-300">${currentMatch.analysis.turningPoint}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderAnalysis(container) {
    container.innerHTML = `
        <div class="space-y-6">
            <h3 class="text-2xl font-semibold">专家分析</h3>
            ${currentMatch.expertAnalysis.map(analysis => `
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <div class="flex items-start space-x-4 mb-4">
                        <div class="w-12 h-12 ${getTierInfo(analysis.tier).bgColor} rounded-full p-1">
                            <img src="${analysis.avatar}" alt="${analysis.expert}" class="w-full h-full rounded-full bg-dota-panel">
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center space-x-2 mb-1">
                                <h4 class="font-semibold">${analysis.expert}</h4>
                                <span class="expert-badge">专家认证</span>
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="text-sm text-gray-400">${getTimeAgo(analysis.timestamp)}</span>
                                <span class="text-sm text-radiant-500 font-medium">评分: ${analysis.rating}/10</span>
                            </div>
                        </div>
                    </div>
                    <p class="text-gray-300 leading-relaxed">${analysis.analysis}</p>
                    <div class="flex items-center space-x-4 mt-4 pt-4 border-t border-dota-border">
                        <button class="text-radiant-500 hover:text-radiant-400 text-sm flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2H4.5C3.67 3 3 3.67 3 4.5v0C3 5.33 3.67 6 4.5 6H7m7 4v6M7 20L3 16m4 4h.01M7 16h.01"></path>
                            </svg>
                            <span>有用 (23)</span>
                        </button>
                        <button class="text-gray-400 hover:text-white text-sm flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                            <span>回复</span>
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderData(container) {
    container.innerHTML = `
        <div class="space-y-8">
            <h3 class="text-2xl font-semibold">详细数据</h3>
            
            <!-- 选手数据表格 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- 天辉队伍 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold text-radiant-500 mb-4">天辉 (${currentMatch.radiant_team.name})</h4>
                    <div class="overflow-x-auto">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>选手</th>
                                    <th>英雄</th>
                                    <th>KDA</th>
                                    <th>净值</th>
                                    <th>GPM</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${currentMatch.players.radiant.map(player => `
                                    <tr>
                                        <td class="font-medium">${player.name}</td>
                                        <td class="text-radiant-500">${player.hero}</td>
                                        <td>${player.kills}/${player.deaths}/${player.assists}</td>
                                        <td class="text-ancient-500">${formatNumber(player.netWorth)}</td>
                                        <td>${player.gpm}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- 夜魇队伍 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold text-dire-500 mb-4">夜魇 (${currentMatch.dire_team.name})</h4>
                    <div class="overflow-x-auto">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>选手</th>
                                    <th>英雄</th>
                                    <th>KDA</th>
                                    <th>净值</th>
                                    <th>GPM</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${currentMatch.players.dire.map(player => `
                                    <tr>
                                        <td class="font-medium">${player.name}</td>
                                        <td class="text-dire-500">${player.hero}</td>
                                        <td>${player.kills}/${player.deaths}/${player.assists}</td>
                                        <td class="text-ancient-500">${formatNumber(player.netWorth)}</td>
                                        <td>${player.gpm}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderComments(container) {
    container.innerHTML = `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-2xl font-semibold">社区讨论</h3>
                <button class="bg-radiant-600 hover:bg-radiant-700 text-white px-4 py-2 rounded-lg transition-colors">
                    发表评论
                </button>
            </div>
            
            <!-- 评论列表 -->
            <div class="space-y-4">
                ${generateMockComments().map(comment => `
                    <div class="bg-dota-panel border border-dota-border rounded-lg p-4">
                        <div class="flex items-start space-x-3">
                            <img src="${comment.avatar}" alt="${comment.author}" class="w-10 h-10 rounded-full bg-dota-bg">
                            <div class="flex-1">
                                <div class="flex items-center space-x-2 mb-2">
                                    <span class="font-medium">${comment.author}</span>
                                    <span class="text-xs text-gray-400">${getTimeAgo(comment.timestamp)}</span>
                                </div>
                                <p class="text-gray-300 text-sm mb-2">${comment.content}</p>
                                <div class="flex items-center space-x-4 text-xs text-gray-400">
                                    <button class="hover:text-radiant-500 transition-colors">👍 ${comment.likes}</button>
                                    <button class="hover:text-dota-accent transition-colors">回复</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function generateMockComments() {
    // TODO: 从API获取真实评论数据
    console.warn('正在使用模拟评论数据，请实现API集成');
    return [];
}

function getTierInfo(tier) {
    const tierMap = {
        diamond: {
            bgColor: 'bg-gradient-to-r from-purple-500 to-purple-600'
        },
        platinum: {
            bgColor: 'bg-gradient-to-r from-cyan-500 to-cyan-600'
        },
        gold: {
            bgColor: 'bg-gradient-to-r from-yellow-500 to-yellow-600'
        },
        silver: {
            bgColor: 'bg-gradient-to-r from-gray-400 to-gray-500'
        }
    };
    
    return tierMap[tier] || tierMap.silver;
}

function showError(message) {
    const container = document.getElementById('match-header');
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
