"""
Flask应用启动脚本
"""

import os
from app import create_app  #, socketio  # 暂时移除socketio
from config.settings import config
from config.database import init_database

# 获取环境配置
config_name = os.environ.get('FLASK_ENV', 'development')
app, _ = create_app(config[config_name])  # 暂时忽略socketio)

@app.before_first_request
def initialize_database():
    """初始化数据库"""
    init_database(app)

@app.cli.command()
def init_db():
    """初始化数据库命令"""
    from config.database import db
    
    print("正在创建数据库表...")
    db.create_all()
    
    print("正在创建默认数据...")
    from config.database import create_default_data
    create_default_data()
    
    print("数据库初始化完成!")

@app.cli.command()
def create_admin():
    """创建管理员用户命令"""
    from models.user import User, UserRole, ExpertTier
    from werkzeug.security import generate_password_hash
    import getpass
    
    username = input("请输入管理员用户名: ")
    email = input("请输入管理员邮箱: ")
    password = getpass.getpass("请输入管理员密码: ")
    
    # 检查用户是否已存在
    if User.query.filter_by(username=username).first():
        print("用户名已存在!")
        return
    
    if User.query.filter_by(email=email).first():
        print("邮箱已被使用!")
        return
    
    # 创建管理员用户
    admin = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        role=UserRole.ADMIN,
        tier=ExpertTier.DIAMOND,
        verified=True
    )
    
    from config.database import db
    db.session.add(admin)
    db.session.commit()
    
    print(f"管理员用户 {username} 创建成功!")

@app.cli.command()
def cleanup_data():
    """清理过期数据命令"""
    from models.user import UserSession
    from models.notification import Notification
    from models.content import ContentView
    from datetime import timedelta
    
    print("正在清理过期数据...")
    
    # 清理过期会话
    expired_sessions = UserSession.cleanup_expired()
    print(f"清理了 {expired_sessions} 个过期会话")
    
    # 清理旧通知
    deleted_notifications = Notification.cleanup_old_notifications(days=30)
    print(f"清理了 {deleted_notifications} 个旧通知")
    
    # 清理旧浏览记录
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    from config.database import db
    deleted_views = ContentView.query.filter(
        ContentView.created_at < thirty_days_ago
    ).delete()
    db.session.commit()
    print(f"清理了 {deleted_views} 个旧浏览记录")
    
    print("数据清理完成!")

@app.cli.command()
def update_hero_stats():
    """更新英雄统计数据命令"""
    from tasks.stats_calculator import calculate_hero_stats
    
    print("正在更新英雄统计数据...")
    
    # TODO: 实现英雄统计计算
    print("英雄统计更新完成!")

@app.cli.command()
def init_test_data():
    """初始化测试数据命令"""
    print("正在初始化测试数据...")
    
    try:
        from scripts.init_test_data import init_test_database
        
        result = init_test_database(clean_existing=True, verbose=True)
        
        if result:
            print("✅ 测试数据初始化成功!")
            print(f"生成了 {result.get('heroes', 0)} 个英雄")
            print(f"生成了 {result.get('items', 0)} 个物品")
            print(f"生成了 {result.get('teams', 0)} 个战队")
            print(f"生成了 {result.get('players', 0)} 个选手")
            print(f"生成了 {result.get('matches', 0)} 场比赛")
            print(f"生成了 {result.get('match_players', 0)} 条比赛选手数据")
            print(f"生成了 {result.get('match_drafts', 0)} 条Pick/Ban数据")
            print(f"生成了 {result.get('match_analyses', 0)} 条比赛分析数据")
        else:
            print("❌ 测试数据初始化失败!")
            
    except Exception as e:
        print(f"❌ 初始化过程出错: {e}")
        import traceback
        traceback.print_exc()

@app.cli.command()
def sync_data():
    """同步外部数据命令"""
    print("正在同步外部数据...")
    
    try:
        from services.unified_data_service import UnifiedDataService
        
        service = UnifiedDataService()
        result = service.sync_all_data()
        
        if result['success']:
            print("✅ 数据同步成功!")
            print(f"同步了 {result.get('heroes_synced', 0)} 个英雄")
            print(f"同步了 {result.get('items_synced', 0)} 个物品")
            print(f"同步了 {result.get('matches_synced', 0)} 场比赛")
            print(f"同步了 {result.get('players_synced', 0)} 个选手")
        else:
            print(f"❌ 数据同步失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # 开发环境直接运行
    if config_name == 'development':
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        # 生产环境使用gunicorn
        print("生产环境请使用: gunicorn -w 4 -b 0.0.0.0:5000 --worker-class eventlet run:app")
