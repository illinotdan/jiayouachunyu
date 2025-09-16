// 主要JavaScript功能文件 - 纯API版本，无任何硬编码数据

// 全局变量
let isLoggedIn = false;
let currentUser = null;

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initGlobalFeatures();
    checkAuthStatus();
    
    // 根据页面类型执行特定初始化
    const currentPage = getCurrentPage();
    switch (currentPage) {
        case 'index':
            loadHomePageData();
            break;
        // 其他页面由各自的JS文件处理
    }
});

// 初始化全局功能
function initGlobalFeatures() {
    initMobileMenu();
    initScrollToTop();
    initGlobalSearch();
    initTheme();
    initNotifications();
    initKeyboardShortcuts();
    initErrorHandling();
}

// 移动端菜单切换
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
        
        // 点击外部关闭菜单
        document.addEventListener('click', function(e) {
            if (!mobileMenuBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
}

// 获取当前页面类型
function getCurrentPage() {
    const path = window.location.pathname;
    const filename = path.split('/').pop().replace('.html', '');
    return filename || 'index';
}

// 检查登录状态
function checkAuthStatus() {
    const savedAuth = Storage.get('auth');
    if (savedAuth && savedAuth.token && savedAuth.expiresAt > Date.now()) {
        isLoggedIn = true;
        currentUser = savedAuth.user;
        updateAuthUI();
    }
}

// 更新认证相关UI
function updateAuthUI() {
    const loginButtons = document.querySelectorAll('[onclick*="login.html"]');
    loginButtons.forEach(btn => {
        if (isLoggedIn) {
            btn.textContent = currentUser?.username || '用户中心';
            btn.onclick = () => window.location.href = 'profile.html';
        }
    });
}

// 加载首页数据
async function loadHomePageData() {
    await Promise.all([
        loadRecentMatches(),
        loadHotDiscussions(),
        loadPlatformStats()
    ]);
}

// 加载最新比赛数据
async function loadRecentMatches() {
    const container = document.getElementById('matches-container');
    if (!container) return;
    
    try {
        showLoadingState(container);
        
        const response = await apiCall(api.getMatches, {
            page: 1,
            page_size: 6,
            sort: 'time_desc'
        });
        
        DataAdapter.validateApiResponse(response, ['matches']);
        
        const adaptedMatches = DataAdapter.adaptArrayData(
            response.data.matches,
            DataAdapter.adaptMatchData
        );
        
        renderMatches(adaptedMatches);
        
    } catch (error) {
        showErrorState(container, '无法加载比赛数据', 'loadRecentMatches');
    }
}

// 加载热门讨论
async function loadHotDiscussions() {
    // 这个函数将在首页显示热门技术讨论
    // 当前首页已经改为静态展示，如需要可以添加动态加载
}

// 加载平台统计数据
async function loadPlatformStats() {
    try {
        const response = await apiCall(api.getGeneralStats);
        
        if (response && response.data) {
            updatePlatformStats(response.data);
        }
        
    } catch (error) {
        console.warn('加载平台统计失败:', error);
        // 统计数据加载失败不影响主要功能
    }
}

// 更新平台统计显示
function updatePlatformStats(stats) {
    // 更新首页的统计数字
    const statsElements = {
        'total-users': stats.users?.total,
        'total-discussions': stats.content?.totalDiscussions,
        'total-matches': stats.matches?.total,
        'analysis-rate': stats.matches?.analysisRate
    };
    
    Object.entries(statsElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element && value !== undefined) {
            element.textContent = formatNumber(value);
        }
    });
}

// 渲染比赛列表
function renderMatches(matches) {
    const container = document.getElementById('matches-container');
    
    if (!matches || matches.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.034 0-3.9.785-5.291 2.073M6.343 6.343A8 8 0 1017.657 17.657 8 8 0 006.343 6.343z"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">暂无比赛数据</p>
                <p class="text-gray-500 text-sm">请等待数据同步或联系管理员</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = matches.map(match => {
        const timeAgo = getTimeAgo(match.start_time);
        const statusInfo = getMatchStatus(match);
        const duration = match.duration ? formatDuration(match.duration) : '';
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewMatch('${match.id}')">
                <div class="flex justify-between items-start mb-4">
                    <div class="text-sm text-gray-400 truncate flex-1 mr-2">${match.league_name || '未知联赛'}</div>
                    <div class="text-sm ${statusInfo.color} ${statusInfo.class} flex-shrink-0">${statusInfo.text}</div>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <div class="team-tag ${getTeamColor(match.radiant_win, true)} flex-shrink-0">
                                ${match.radiant_team?.tag || 'RAD'}
                            </div>
                            <span class="font-medium text-sm truncate">${match.radiant_team?.name || '天辉队伍'}</span>
                        </div>
                        <span class="font-bold ${getScoreColor(match.radiant_win, true)} ml-2">${match.radiant_score || 0}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <div class="team-tag ${getTeamColor(match.radiant_win, false)} flex-shrink-0">
                                ${match.dire_team?.tag || 'DIR'}
                            </div>
                            <span class="font-medium text-sm truncate">${match.dire_team?.name || '夜魇队伍'}</span>
                        </div>
                        <span class="font-bold ${getScoreColor(match.radiant_win, false)} ml-2">${match.dire_score || 0}</span>
                    </div>
                </div>
                <div class="mt-4 pt-4 border-t border-dota-border">
                    <div class="flex justify-between items-center text-sm">
                        <div class="text-gray-400">
                            <div>${timeAgo}</div>
                            ${duration ? `<div class="text-xs text-gray-500">${duration}</div>` : ''}
                        </div>
                        <div class="flex space-x-2 flex-wrap justify-end">
                            <span class="bg-ancient-600 text-white px-2 py-1 rounded text-xs whitespace-nowrap">${match.comments_count || 0}条讨论</span>
                            <span class="bg-dota-accent text-white px-2 py-1 rounded text-xs whitespace-nowrap cursor-pointer hover:bg-blue-600 transition-colors" onclick="event.stopPropagation(); window.location.href='match-discussion.html?id=${match.id}'">
                                💬 讨论版
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// 删除所有备用数据函数
// getFallbackMatches() 函数已删除

// 工具函数
function getMatchStatus(match) {
    // TODO: 从API获取真实状态文本配置
    switch (match.status) {
        case 'live':
            return {
                text: '直播中', // TODO: 从API获取真实状态文本
                color: 'text-dire-500',
                class: 'status-live'
            };
        case 'upcoming':
            return {
                text: '即将开始', // TODO: 从API获取真实状态文本
                color: 'text-ancient-500',
                class: ''
            };
        case 'finished':
        default:
            return {
                text: '已结束', // TODO: 从API获取真实状态文本
                color: 'text-radiant-500',
                class: ''
            };
    }
}

function getTeamColor(radiantWin, isRadiant) {
    if (radiantWin === null) return 'bg-gray-600';
    
    if (isRadiant) {
        return radiantWin ? 'bg-radiant-600' : 'bg-gray-600';
    } else {
        return !radiantWin ? 'bg-dire-600' : 'bg-gray-600';
    }
}

function getScoreColor(radiantWin, isRadiant) {
    if (radiantWin === null) return 'text-gray-400';
    
    if (isRadiant) {
        return radiantWin ? 'text-radiant-500' : 'text-gray-400';
    } else {
        return !radiantWin ? 'text-dire-500' : 'text-gray-400';
    }
}

function viewMatch(matchId) {
    window.location.href = `match-discussion.html?id=${matchId}`;
}

// 显示加载状态
function showLoadingState(container) {
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-dota-accent"></div>
            <p class="mt-4 text-gray-400">正在从服务器加载数据...</p>
        </div>
    `;
}

// 显示错误状态
function showErrorState(container, message, retryFunction = null) {
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 mb-4">${message}</p>
            <p class="text-gray-400 text-sm mb-4">请确保后端服务已启动并可访问</p>
            ${retryFunction ? `
                <button onclick="${retryFunction}()" class="bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                    重新加载
                </button>
            ` : ''}
        </div>
    `;
}

// 初始化全局搜索功能
function initGlobalSearch() {
    const searchInputs = document.querySelectorAll('input[placeholder*="搜索"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performGlobalSearch(e.target.value, e.target);
            }, 300);
        });
        
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performGlobalSearch(e.target.value, e.target);
            }
        });
    });
}

function performGlobalSearch(query, inputElement) {
    if (!query.trim()) return;
    
    console.log('全局搜索:', query);
    
    // 根据当前页面执行不同的搜索逻辑
    const currentPage = getCurrentPage();
    switch (currentPage) {
        case 'matches':
            if (typeof filterMatches === 'function') filterMatches();
            break;
        case 'experts':
            if (typeof filterExperts === 'function') filterExperts();
            break;
        case 'community':
            if (typeof filterDiscussions === 'function') filterDiscussions();
            break;
        default:
            // 跳转到搜索结果页面
            window.location.href = `search.html?q=${encodeURIComponent(query)}`;
    }
}

// 滚动到顶部功能
function initScrollToTop() {
    let scrollTopBtn = null;
    
    window.addEventListener('scroll', function() {
        if (!scrollTopBtn) {
            scrollTopBtn = document.createElement('button');
            scrollTopBtn.id = 'scroll-top-btn';
            scrollTopBtn.innerHTML = `
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path>
                </svg>
            `;
            scrollTopBtn.className = 'fixed bottom-8 right-8 bg-dota-accent hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-all duration-300 z-50';
            scrollTopBtn.style.display = 'none';
            scrollTopBtn.onclick = scrollToTop;
            document.body.appendChild(scrollTopBtn);
        }
        
        if (window.scrollY > 300) {
            scrollTopBtn.style.display = 'block';
        } else {
            scrollTopBtn.style.display = 'none';
        }
    });
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// 通知系统
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="flex items-start space-x-3">
            <div class="flex-1">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-white">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动消失
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 3000);
}

// 初始化通知系统
function initNotifications() {
    // 检查浏览器通知权限
    if ('Notification' in window && Notification.permission === 'default') {
        // 可以在适当时机请求权限
    }
}

// 键盘快捷键
function initKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K 打开搜索
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[placeholder*="搜索"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // ESC 关闭模态框
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal-overlay');
    modals.forEach(modal => modal.remove());
    
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) mobileMenu.classList.add('hidden');
}

// 错误监控
function initErrorHandling() {
    window.addEventListener('error', function(e) {
        console.error('JavaScript错误:', e.error);
        
        // 在开发环境显示错误通知
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            showNotification(`JavaScript错误: ${e.error.message}`, 'error');
        }
    });
    
    window.addEventListener('unhandledrejection', function(e) {
        console.error('未处理的Promise拒绝:', e.reason);
        showNotification('操作失败，请稍后重试', 'error');
    });
}

// 主题切换（如果需要）
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.classList.contains('dark') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    html.classList.remove(currentTheme);
    html.classList.add(newTheme);
    
    Storage.set('theme', newTheme);
}

// 初始化主题
function initTheme() {
    const savedTheme = Storage.get('theme', 'dark');
    document.documentElement.classList.add(savedTheme);
}

// 数据格式化工具
function formatNumber(num) {
    if (typeof num !== 'number') return '0';
    
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDuration(seconds) {
    if (typeof seconds !== 'number') return '00:00';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

function getTimeAgo(timestamp) {
    const now = Date.now();
    const time = typeof timestamp === 'string' ? new Date(timestamp).getTime() : timestamp;
    const diff = now - time;
    
    if (diff < 0) {
        // 未来时间
        const absDiff = Math.abs(diff);
        const minutes = Math.floor(absDiff / (1000 * 60));
        const hours = Math.floor(absDiff / (1000 * 60 * 60));
        
        if (minutes < 60) return `${minutes}分钟后开始`;
        return `${hours}小时后开始`;
    }
    
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
}

// 本地存储工具已移动到config.js中，在此不再重复定义

// 网络状态监控
window.addEventListener('online', function() {
    showNotification('网络连接已恢复', 'success');
});

window.addEventListener('offline', function() {
    showNotification('网络连接已断开', 'warning');
});
