// 专家详情页JavaScript

let currentExpert = null;
let currentTab = 'articles';

document.addEventListener('DOMContentLoaded', function() {
    initExpertPage();
});

function initExpertPage() {
    // 从URL获取专家ID
    const urlParams = new URLSearchParams(window.location.search);
    const expertId = urlParams.get('id');
    
    if (expertId) {
        loadExpertDetails(expertId);
    } else {
        showError('无效的专家ID');
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

async function loadExpertDetails(expertId) {
    try {
        // 模拟加载延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟专家详情数据
        currentExpert = generateMockExpertDetail(expertId);
        
        renderExpertHeader();
        renderTabContent(currentTab);
        
        // 显示标签页
        document.getElementById('expert-tabs').style.display = 'block';
        
    } catch (error) {
        console.error('加载专家详情失败:', error);
        showError('加载专家详情失败，请稍后重试');
    }
}

function generateMockExpertDetail(expertId) {
    // TODO: 从API获取真实专家数据
    console.warn('正在使用模拟专家数据，请实现API集成');
    return {
        id: expertId,
        name: '数据加载中...',
        title: '专家',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=loading',
        tier: 'bronze',
        expertise: [],
        followers: 0,
        articles: 0,
        accuracy: 0,
        bio: '正在从服务器加载专家信息...',
        verified: false,
        joinDate: new Date().toISOString(),
        achievements: [],
        recentActivity: Date.now()
    };
}

function renderExpertHeader() {
    const loading = document.getElementById('expert-loading');
    const container = document.getElementById('expert-header');
    const nameElement = document.getElementById('expert-name');
    
    if (loading) loading.style.display = 'none';
    if (nameElement) nameElement.textContent = currentExpert.name;
    
    const tierInfo = getTierInfo(currentExpert.tier);
    const lastActiveAgo = getTimeAgo(currentExpert.recentActivity);
    
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- 专家基本信息 -->
            <div class="lg:col-span-2">
                <div class="flex items-start space-x-6">
                    <div class="relative">
                        <div class="w-24 h-24 ${tierInfo.bgColor} rounded-full p-1 shadow-lg">
                            <img src="${currentExpert.avatar}" alt="${currentExpert.name}" class="w-full h-full rounded-full bg-dota-panel object-cover">
                        </div>
                        ${currentExpert.verified ? `
                            <div class="absolute -bottom-1 -right-1">
                                <span class="expert-badge flex items-center">
                                    <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                    </svg>
                                    认证
                                </span>
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-3 mb-2">
                            <h1 class="text-3xl font-bold text-white">${currentExpert.name}</h1>
                            <span class="text-lg ${tierInfo.textColor} font-medium">${tierInfo.name}</span>
                        </div>
                        <p class="text-lg text-gray-400 mb-4">${currentExpert.title}</p>
                        <p class="text-gray-300 leading-relaxed mb-4">${currentExpert.bio}</p>
                        
                        <!-- 专业领域 -->
                        <div class="mb-4">
                            <div class="flex flex-wrap gap-2">
                                ${currentExpert.expertise.map((area, index) => `
                                    <span class="tag ${getExpertiseColor(index)}">
                                        ${area}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                        
                        <!-- 成就 -->
                        <div class="mb-4">
                            <h4 class="text-sm font-medium text-gray-400 mb-2">主要成就</h4>
                            <div class="space-y-1">
                                ${currentExpert.achievements.map(achievement => `
                                    <div class="flex items-center space-x-2">
                                        <svg class="w-4 h-4 text-ancient-500" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                        </svg>
                                        <span class="text-sm text-gray-300">${achievement}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <div class="flex items-center space-x-4">
                            <button class="bg-radiant-600 hover:bg-radiant-700 text-white px-6 py-2 rounded-lg transition-colors font-medium">
                                关注专家
                            </button>
                            <button class="bg-dota-accent/20 hover:bg-dota-accent text-dota-accent hover:text-white border border-dota-accent/30 hover:border-dota-accent px-6 py-2 rounded-lg transition-colors font-medium">
                                私信
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- 快速统计 -->
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-dota-bg/50 rounded-lg p-4 text-center border border-dota-border">
                        <div class="text-2xl font-bold text-radiant-500 mb-1">${formatNumber(currentExpert.followers)}</div>
                        <div class="text-sm text-gray-400">关注者</div>
                    </div>
                    <div class="bg-dota-bg/50 rounded-lg p-4 text-center border border-dota-border">
                        <div class="text-2xl font-bold text-dota-accent mb-1">${currentExpert.articles}</div>
                        <div class="text-sm text-gray-400">发表文章</div>
                    </div>
                </div>
                
                <div class="bg-dota-bg/50 rounded-lg p-4 text-center border border-dota-border">
                    <div class="text-2xl font-bold text-ancient-500 mb-1">${currentExpert.accuracy.toFixed(1)}%</div>
                    <div class="text-sm text-gray-400">预测准确率</div>
                </div>
                
                <div class="bg-dota-bg/50 rounded-lg p-4 border border-dota-border">
                    <div class="text-sm text-gray-400 mb-1">最后活跃</div>
                    <div class="text-sm text-white">${lastActiveAgo}</div>
                </div>
            </div>
        </div>
    `;
}

function renderTabContent(tab) {
    const container = document.getElementById('expert-content');
    
    switch (tab) {
        case 'articles':
            renderArticles(container);
            break;
        case 'predictions':
            renderPredictions(container);
            break;
        case 'stats':
            renderStats(container);
            break;
    }
}

function renderArticles(container) {
    const articles = generateMockArticles();
    
    container.innerHTML = `
        <div class="space-y-6">
            <h3 class="text-2xl font-semibold">分析文章 (${articles.length})</h3>
            <div class="space-y-4">
                ${articles.map(article => `
                    <div class="bg-dota-panel border border-dota-border rounded-lg p-6 card-hover cursor-pointer">
                        <div class="flex justify-between items-start mb-3">
                            <h4 class="text-lg font-semibold text-white hover:text-dota-accent transition-colors">${article.title}</h4>
                            <span class="text-sm text-gray-400 whitespace-nowrap ml-4">${getTimeAgo(article.publishTime)}</span>
                        </div>
                        <p class="text-gray-400 mb-4 line-clamp-2">${article.summary}</p>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-4 text-sm text-gray-400">
                                <span class="flex items-center space-x-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                    </svg>
                                    <span>${formatNumber(article.views)}</span>
                                </span>
                                <span class="flex items-center space-x-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                    </svg>
                                    <span>${article.likes}</span>
                                </span>
                                <span class="flex items-center space-x-1">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                                    </svg>
                                    <span>${article.comments}</span>
                                </span>
                            </div>
                            <div class="flex space-x-2">
                                ${article.tags.map(tag => `
                                    <span class="tag bg-dota-accent/20 text-dota-accent border-dota-accent/30">
                                        ${tag}
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderPredictions(container) {
    const predictions = generateMockPredictions();
    
    container.innerHTML = `
        <div class="space-y-6">
            <div class="flex justify-between items-center">
                <h3 class="text-2xl font-semibold">预测记录</h3>
                <div class="text-sm text-gray-400">
                    总计 ${predictions.length} 次预测，准确率 ${currentExpert.accuracy.toFixed(1)}%
                </div>
            </div>
            
            <div class="space-y-4">
                ${predictions.map(prediction => `
                    <div class="bg-dota-panel border border-dota-border rounded-lg p-4">
                        <div class="flex justify-between items-start mb-3">
                            <div class="flex-1">
                                <h4 class="font-semibold text-white mb-1">${prediction.match}</h4>
                                <p class="text-sm text-gray-400">${prediction.prediction}</p>
                            </div>
                            <div class="text-right">
                                <span class="inline-block px-3 py-1 rounded-full text-xs font-medium ${
                                    prediction.result === 'correct' ? 'bg-radiant-600/20 text-radiant-400' :
                                    prediction.result === 'incorrect' ? 'bg-dire-600/20 text-dire-400' :
                                    'bg-ancient-600/20 text-ancient-400'
                                }">
                                    ${prediction.result === 'correct' ? '✅ 正确' : 
                                      prediction.result === 'incorrect' ? '❌ 错误' : 
                                      '⏳ 待定'}
                                </span>
                            </div>
                        </div>
                        <div class="flex justify-between items-center text-sm">
                            <span class="text-gray-400">${getTimeAgo(prediction.timestamp)}</span>
                            <div class="flex items-center space-x-2">
                                <span class="text-gray-400">置信度:</span>
                                <span class="font-medium text-dota-accent">${prediction.confidence}%</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

function renderStats(container) {
    container.innerHTML = `
        <div class="space-y-6">
            <h3 class="text-2xl font-semibold">统计数据</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <!-- 预测统计 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">预测表现</h4>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">总预测次数</span>
                            <span class="font-medium text-white">127</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">正确预测</span>
                            <span class="font-medium text-radiant-500">98</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">错误预测</span>
                            <span class="font-medium text-dire-500">29</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">准确率</span>
                            <span class="font-bold text-ancient-500">${currentExpert.accuracy.toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                
                <!-- 内容统计 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">内容贡献</h4>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">发表文章</span>
                            <span class="font-medium text-white">${currentExpert.articles}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">总阅读量</span>
                            <span class="font-medium text-dota-accent">${formatNumber(currentExpert.articles * 1250)}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">获得点赞</span>
                            <span class="font-medium text-radiant-500">${formatNumber(currentExpert.articles * 45)}</span>
                        </div>
                        <div class="flex justify-between items-center">
                            <span class="text-gray-400">加入时间</span>
                            <span class="font-medium text-white">${new Date(currentExpert.joinDate).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function generateMockArticles() {
    // TODO: 从API获取真实文章数据
    console.warn('正在使用模拟文章数据，请实现API集成');
    return [];
}

function generateMockPredictions() {
    // TODO: 从API获取真实预测数据
    console.warn('正在使用模拟预测数据，请实现API集成');
    return [];
}

function getTierInfo(tier) {
    // TODO: 从API获取真实专家等级配置
    const tierMap = {
        diamond: {
            name: '钻石专家', // TODO: 从API获取真实等级名称
            bgColor: 'bg-gradient-to-r from-purple-500 to-purple-600',
            textColor: 'text-purple-400'
        },
        platinum: {
            name: '铂金专家', // TODO: 从API获取真实等级名称
            bgColor: 'bg-gradient-to-r from-cyan-500 to-cyan-600',
            textColor: 'text-cyan-400'
        },
        gold: {
            name: '黄金专家', // TODO: 从API获取真实等级名称
            bgColor: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
            textColor: 'text-yellow-400'
        },
        silver: {
            name: '白银专家', // TODO: 从API获取真实等级名称
            bgColor: 'bg-gradient-to-r from-gray-400 to-gray-500',
            textColor: 'text-gray-400'
        }
    };
    
    return tierMap[tier] || tierMap.silver;
}

function getExpertiseColor(index) {
    const colors = [
        'bg-radiant-600/20 text-radiant-400 border-radiant-600/30',
        'bg-dota-accent/20 text-dota-accent border-dota-accent/30',
        'bg-ancient-600/20 text-ancient-400 border-ancient-600/30'
    ];
    return colors[index % colors.length];
}

function showError(message) {
    const container = document.getElementById('expert-header');
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
