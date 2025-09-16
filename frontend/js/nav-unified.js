// 导航栏统一修复脚本 - 最终版
// 确保所有页面导航栏完全一致

document.addEventListener('DOMContentLoaded', function() {
    unifyNavigation();
});

function unifyNavigation() {
    const currentPage = getCurrentPageName();
    
    // 1. 统一所有导航链接的样式
    const navLinks = document.querySelectorAll('nav a[href*=".html"]');
    navLinks.forEach(link => {
        // 移除所有现有样式类
        link.className = '';
        
        // 添加统一的nav-item类
        link.classList.add('nav-item');
        
        // 检查是否是当前页面
        const linkHref = link.getAttribute('href');
        const linkPage = linkHref.replace('.html', '').replace('./', '').replace('index', '');
        
        if (isCurrentPage(linkPage, currentPage)) {
            link.classList.add('nav-active');
        }
    });
    
    // 2. 统一Logo样式
    const logos = document.querySelectorAll('nav [onclick*="index.html"], nav .gradient-text');
    logos.forEach(logo => {
        logo.className = 'text-2xl font-bold gradient-text cursor-pointer hover:opacity-80 transition-opacity';
        logo.setAttribute('onclick', "window.location.href='index.html'");
        logo.textContent = '刀塔情书';
    });
    
    // 3. 统一导航栏容器样式
    const nav = document.querySelector('nav');
    if (nav) {
        nav.className = 'bg-dota-panel/90 backdrop-blur-sm border-b border-dota-border sticky top-0 z-50';
    }
    
    // 4. 统一移动端菜单
    setupUnifiedMobileMenu();
    
    console.log('✅ 导航栏样式统一完成');
}

function getCurrentPageName() {
    const path = window.location.pathname;
    const filename = path.split('/').pop().replace('.html', '');
    return filename || 'index';
}

function isCurrentPage(linkPage, currentPage) {
    // 处理各种页面名称匹配
    if (linkPage === currentPage) return true;
    if (linkPage === '' && currentPage === 'index') return true;
    if (linkPage === 'index' && currentPage === '') return true;
    
    // 特殊页面映射
    const pageMapping = {
        'stats': 'analytics',
        'experts': 'learning'
    };
    
    return pageMapping[linkPage] === currentPage || pageMapping[currentPage] === linkPage;
}

function setupUnifiedMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        // 确保移动端按钮样式统一
        mobileMenuBtn.className = 'md:hidden text-dota-text p-2';
        mobileMenuBtn.innerHTML = `
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
        `;
        
        // 重新设置事件监听器
        mobileMenuBtn.replaceWith(mobileMenuBtn.cloneNode(true));
        const newBtn = document.getElementById('mobile-menu-btn');
        
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            mobileMenu.classList.toggle('hidden');
        });
        
        // 点击外部关闭
        document.addEventListener('click', function(e) {
            if (!newBtn.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
        
        // 统一移动端菜单项样式
        const mobileLinks = mobileMenu.querySelectorAll('a[href*=".html"]');
        mobileLinks.forEach(link => {
            link.className = 'mobile-nav-item';
            
            const linkPage = link.getAttribute('href').replace('.html', '').replace('./', '');
            if (isCurrentPage(linkPage, getCurrentPageName())) {
                link.classList.add('active');
            }
        });
    }
}

// 手动修复函数（可在控制台调用）
window.fixAllNavigation = function() {
    unifyNavigation();
    console.log('🔧 手动导航修复完成');
};

// 监听页面变化，自动修复
window.addEventListener('popstate', function() {
    setTimeout(unifyNavigation, 100);
});
