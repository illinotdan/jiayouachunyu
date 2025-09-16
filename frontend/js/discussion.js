// 讨论详情页JavaScript

let currentDiscussion = null;

document.addEventListener('DOMContentLoaded', function() {
    initDiscussionPage();
});

function initDiscussionPage() {
    // 从URL获取讨论ID
    const urlParams = new URLSearchParams(window.location.search);
    const discussionId = urlParams.get('id');
    
    if (discussionId) {
        loadDiscussionDetails(discussionId);
    } else {
        showError('无效的讨论ID');
    }
    
    // 初始化回复表单
    initReplyForm();
}

async function loadDiscussionDetails(discussionId) {
    try {
        // 模拟加载延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 生成模拟讨论详情数据
        currentDiscussion = generateMockDiscussionDetail(discussionId);
        
        renderDiscussionContent();
        
        // 显示回复区域
        document.getElementById('reply-section').style.display = 'block';
        
    } catch (error) {
        console.error('加载讨论详情失败:', error);
        showError('加载讨论详情失败，请稍后重试');
    }
}

function generateMockDiscussionDetail(discussionId) {
    // TODO: 从API获取真实讨论数据
    console.warn('正在使用模拟数据，请实现API集成');
    return {
        id: discussionId,
        title: '数据加载中...',
        content: '正在从服务器获取讨论内容...',
        author: {
            name: '系统用户',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=system',
            reputation: 0,
            tier: 'bronze'
        },
        category: 'analysis',
        tags: [],
        createdAt: Date.now(),
        views: 0,
        likes: 0,
        replies: []
    };
}

function generateMockReplies() {
    // TODO: 从API获取真实回复数据
    console.warn('正在使用模拟回复数据，请实现API集成');
    return [];
}

function renderDiscussionContent() {
    const loading = document.getElementById('discussion-loading');
    const container = document.getElementById('discussion-content');
    const titleElement = document.getElementById('discussion-title');
    
    if (loading) loading.style.display = 'none';
    if (titleElement) titleElement.textContent = currentDiscussion.title;
    
    const timeAgo = getTimeAgo(currentDiscussion.createdAt);
    const categoryInfo = getCategoryInfo(currentDiscussion.category);
    const tierInfo = getTierInfo(currentDiscussion.author.tier);
    
    container.innerHTML = `
        <!-- 讨论主体 -->
        <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
            <!-- 标题和标签 -->
            <div class="mb-6">
                <div class="flex items-center gap-2 mb-4 flex-wrap">
                    <span class="tag ${categoryInfo.color}">
                        ${categoryInfo.name}
                    </span>
                    ${currentDiscussion.tags.map(tag => `
                        <span class="tag bg-dota-accent/20 text-dota-accent border-dota-accent/30">
                            #${tag}
                        </span>
                    `).join('')}
                </div>
                
                <h1 class="text-3xl font-bold text-white mb-4">${currentDiscussion.title}</h1>
                
                <!-- 作者信息 -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-12 h-12 ${tierInfo.bgColor} rounded-full p-1">
                            <img src="${currentDiscussion.author.avatar}" alt="${currentDiscussion.author.name}" class="w-full h-full rounded-full bg-dota-panel">
                        </div>
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="font-semibold text-white">${currentDiscussion.author.name}</span>
                                <span class="expert-badge">认证用户</span>
                            </div>
                            <div class="text-sm text-gray-400">声望: ${formatNumber(currentDiscussion.author.reputation)} • ${timeAgo}</div>
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-4 text-sm text-gray-400">
                        <span class="flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                            <span>${formatNumber(currentDiscussion.views)}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                            <span>${currentDiscussion.likes}</span>
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- 内容 -->
            <div class="prose prose-invert max-w-none">
                ${formatContent(currentDiscussion.content)}
            </div>
            
            <!-- 操作按钮 -->
            <div class="flex items-center space-x-4 mt-6 pt-6 border-t border-dota-border">
                <button class="flex items-center space-x-2 text-radiant-500 hover:text-radiant-400 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2H4.5C3.67 3 3 3.67 3 4.5v0C3 5.33 3.67 6 4.5 6H7m7 4v6M7 20L3 16m4 4h.01M7 16h.01"></path>
                    </svg>
                    <span>点赞 (${currentDiscussion.likes})</span>
                </button>
                <button class="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z"></path>
                    </svg>
                    <span>分享</span>
                </button>
                <button class="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                    </svg>
                    <span>收藏</span>
                </button>
            </div>
        </div>
        
        <!-- 回复列表 -->
        <div class="space-y-4">
            <h3 class="text-xl font-semibold">回复 (${currentDiscussion.replies.length})</h3>
            ${currentDiscussion.replies.map(reply => `
                <div class="bg-dota-panel border border-dota-border rounded-lg p-4">
                    <div class="flex items-start space-x-3">
                        <div class="w-10 h-10 ${getTierInfo(reply.author.tier).bgColor} rounded-full p-1">
                            <img src="${reply.author.avatar}" alt="${reply.author.name}" class="w-full h-full rounded-full bg-dota-panel">
                        </div>
                        <div class="flex-1">
                            <div class="flex items-center space-x-2 mb-2">
                                <span class="font-medium text-white">${reply.author.name}</span>
                                <span class="text-xs text-gray-400">声望: ${formatNumber(reply.author.reputation)}</span>
                                <span class="text-xs text-gray-400">•</span>
                                <span class="text-xs text-gray-400">${getTimeAgo(reply.timestamp)}</span>
                            </div>
                            <p class="text-gray-300 text-sm mb-3 leading-relaxed">${reply.content}</p>
                            <div class="flex items-center space-x-4 text-xs">
                                <button class="text-radiant-500 hover:text-radiant-400 transition-colors flex items-center space-x-1">
                                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2H4.5C3.67 3 3 3.67 3 4.5v0C3 5.33 3.67 6 4.5 6H7m7 4v6M7 20L3 16m4 4h.01M7 16h.01"></path>
                                    </svg>
                                    <span>有用 (${reply.likes})</span>
                                </button>
                                <button class="text-gray-400 hover:text-white transition-colors">回复</button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function formatContent(content) {
    // 简单的Markdown格式化
    return content
        .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-white mt-6 mb-3">$1</h3>')
        .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold text-white mt-8 mb-4">$1</h2>')
        .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-white mt-8 mb-4">$1</h1>')
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-gray-300">$1</em>')
        .replace(/\n\n/g, '</p><p class="text-gray-300 leading-relaxed mb-4">')
        .replace(/^/, '<p class="text-gray-300 leading-relaxed mb-4">')
        .replace(/$/, '</p>');
}

function initReplyForm() {
    const form = document.getElementById('reply-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const content = document.getElementById('reply-content').value;
            if (content.trim()) {
                addReply(content);
                document.getElementById('reply-content').value = '';
            } else {
                showNotification('请输入回复内容', 'warning');
            }
        });
    }
}

function addReply(content) {
    const newReply = {
        id: currentDiscussion.replies.length + 1,
        author: {
            name: '当前用户',
            avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=currentuser',
            reputation: 1000,
            tier: 'silver'
        },
        content: content,
        timestamp: Date.now(),
        likes: 0
    };
    
    currentDiscussion.replies.unshift(newReply);
    renderDiscussionContent();
    showNotification('回复发布成功！', 'success');
}

function getCategoryInfo(category) {
    const categoryMap = {
        analysis: {
            name: '深度分析',
            color: 'bg-radiant-600/20 text-radiant-400 border-radiant-600/30'
        },
        prediction: {
            name: '比赛预测',
            color: 'bg-ancient-600/20 text-ancient-400 border-ancient-600/30'
        },
        strategy: {
            name: '战术讨论',
            color: 'bg-dota-accent/20 text-dota-accent border-dota-accent/30'
        },
        news: {
            name: '最新资讯',
            color: 'bg-dire-600/20 text-dire-400 border-dire-600/30'
        }
    };
    
    return categoryMap[category] || categoryMap.analysis;
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
    const container = document.getElementById('discussion-content');
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
