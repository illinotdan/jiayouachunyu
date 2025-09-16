/**
 * 实时数据同步管理
 * 处理用户触发的数据同步操作
 */

class RealtimeSyncManager {
    constructor() {
        this.isPolling = false;
        this.pollInterval = null;
        this.syncStatus = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkInitialStatus();
    }

    bindEvents() {
        // 获取最新数据按钮
        const syncBtn = document.getElementById('syncLatestBtn');
        if (syncBtn) {
            syncBtn.addEventListener('click', () => this.triggerLatestSync());
        }

        // 刷新数据按钮
        const refreshBtn = document.getElementById('refreshData');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshAllData());
        }
    }

    async checkInitialStatus() {
        try {
            const status = await api.getSyncStatus();
            this.syncStatus = status;
            
            if (status.is_running) {
                this.showSyncInProgress(status);
                this.startPolling();
            } else {
                this.hideSyncProgress();
            }
        } catch (error) {
            console.error('检查同步状态失败:', error);
        }
    }

    async triggerLatestSync() {
        try {
            // 显示同步选项对话框
            const options = await this.showSyncOptions();
            if (!options) return;

            // 禁用按钮
            this.setSyncButtonState(true);

            // 触发同步
            let response;
            switch (options.type) {
                case 'full':
                    response = await api.triggerFullSync(options.hoursBack);
                    break;
                case 'matches':
                    response = await api.triggerMatchesSync(options.hoursBack);
                    break;
                case 'heroes':
                    response = await api.triggerHeroesSync();
                    break;
                case 'items':
                    response = await api.triggerItemsSync();
                    break;
                default:
                    throw new Error('未知的同步类型');
            }

            // 显示成功消息
            this.showMessage('数据同步已启动', 'success');

            // 开始轮询状态
            this.startPolling();

        } catch (error) {
            console.error('触发数据同步失败:', error);
            this.showMessage('启动数据同步失败: ' + error.message, 'error');
            this.setSyncButtonState(false);
        }
    }

    async showSyncOptions() {
        return new Promise((resolve) => {
            // 创建选项对话框
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            modal.innerHTML = `
                <div class="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
                    <h3 class="text-xl font-bold text-white mb-4">选择同步类型</h3>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-300 mb-2">同步类型</label>
                            <select id="syncType" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white">
                                <option value="matches">最新比赛数据</option>
                                <option value="full">完整数据同步</option>
                                <option value="heroes">英雄数据</option>
                                <option value="items">物品数据</option>
                            </select>
                        </div>
                        
                        <div id="hoursBackContainer">
                            <label class="block text-sm font-medium text-gray-300 mb-2">时间范围（小时）</label>
                            <select id="hoursBack" class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white">
                                <option value="1">最近1小时</option>
                                <option value="3">最近3小时</option>
                                <option value="6" selected>最近6小时</option>
                                <option value="12">最近12小时</option>
                                <option value="24">最近24小时</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="flex justify-end space-x-3 mt-6">
                        <button id="cancelSync" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                            取消
                        </button>
                        <button id="confirmSync" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                            开始同步
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // 绑定事件
            const syncType = modal.querySelector('#syncType');
            const hoursBackContainer = modal.querySelector('#hoursBackContainer');
            const cancelBtn = modal.querySelector('#cancelSync');
            const confirmBtn = modal.querySelector('#confirmSync');

            // 根据同步类型显示/隐藏时间范围选择
            syncType.addEventListener('change', () => {
                const showHours = ['matches', 'full'].includes(syncType.value);
                hoursBackContainer.style.display = showHours ? 'block' : 'none';
            });

            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(null);
            });

            confirmBtn.addEventListener('click', () => {
                const type = syncType.value;
                const hoursBack = parseInt(hoursBackContainer.querySelector('#hoursBack').value);
                
                document.body.removeChild(modal);
                resolve({ type, hoursBack });
            });

            // 点击背景关闭
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    resolve(null);
                }
            });
        });
    }

    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        this.pollInterval = setInterval(async () => {
            try {
                const status = await api.getSyncStatus();
                this.syncStatus = status;
                
                if (status.is_running) {
                    this.updateSyncProgress(status);
                } else {
                    this.stopPolling();
                    this.onSyncComplete(status);
                }
            } catch (error) {
                console.error('轮询同步状态失败:', error);
                this.stopPolling();
            }
        }, 2000); // 每2秒轮询一次
    }

    stopPolling() {
        this.isPolling = false;
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    showSyncInProgress(status) {
        const syncStatus = document.getElementById('syncStatus');
        const progressContainer = document.getElementById('syncProgressContainer');
        
        if (syncStatus) {
            syncStatus.classList.remove('hidden');
        }
        
        if (progressContainer) {
            progressContainer.classList.remove('hidden');
        }
        
        this.updateSyncProgress(status);
    }

    updateSyncProgress(status) {
        const progressBar = document.getElementById('syncProgressBar');
        const progressPercent = document.getElementById('syncProgressPercent');
        const progressText = document.getElementById('syncProgressText');
        const currentTask = document.getElementById('syncCurrentTask');
        
        if (progressBar) {
            progressBar.style.width = `${status.progress || 0}%`;
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${status.progress || 0}%`;
        }
        
        if (progressText) {
            progressText.textContent = status.current_task || '同步中...';
        }
        
        if (currentTask) {
            const startTime = status.start_time ? new Date(status.start_time) : null;
            const elapsed = startTime ? Math.floor((Date.now() - startTime.getTime()) / 1000) : 0;
            currentTask.textContent = `已用时: ${elapsed}秒`;
        }
    }

    hideSyncProgress() {
        const syncStatus = document.getElementById('syncStatus');
        const progressContainer = document.getElementById('syncProgressContainer');
        
        if (syncStatus) {
            syncStatus.classList.add('hidden');
        }
        
        if (progressContainer) {
            progressContainer.classList.add('hidden');
        }
    }

    onSyncComplete(status) {
        this.setSyncButtonState(false);
        this.hideSyncProgress();
        
        if (status.error) {
            this.showMessage('数据同步失败: ' + status.error, 'error');
        } else {
            this.showMessage('数据同步完成！', 'success');
            // 自动刷新数据
            setTimeout(() => {
                this.refreshAllData();
            }, 1000);
        }
    }

    setSyncButtonState(disabled) {
        const syncBtn = document.getElementById('syncLatestBtn');
        if (syncBtn) {
            syncBtn.disabled = disabled;
            if (disabled) {
                syncBtn.classList.add('opacity-50', 'cursor-not-allowed');
                syncBtn.querySelector('span').textContent = '同步中...';
            } else {
                syncBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                syncBtn.querySelector('span').textContent = '获取最新数据';
            }
        }
    }

    async refreshAllData() {
        try {
            this.showMessage('正在刷新数据...', 'info');
            
            // 触发页面数据刷新
            if (window.analytics && typeof window.analytics.refreshAllCharts === 'function') {
                await window.analytics.refreshAllCharts();
            }
            
            this.showMessage('数据刷新完成！', 'success');
        } catch (error) {
            console.error('刷新数据失败:', error);
            this.showMessage('刷新数据失败: ' + error.message, 'error');
        }
    }

    showMessage(message, type = 'info') {
        // 使用现有的错误处理系统
        if (window.errorHandler) {
            if (type === 'error') {
                window.errorHandler.showError(message);
            } else if (type === 'success') {
                window.errorHandler.showSuccess(message);
            } else {
                window.errorHandler.showInfo(message);
            }
        } else {
            // 简单的消息显示
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// 初始化实时同步管理器
document.addEventListener('DOMContentLoaded', function() {
    window.realtimeSync = new RealtimeSyncManager();
});

// 导出到全局
window.RealtimeSyncManager = RealtimeSyncManager;
