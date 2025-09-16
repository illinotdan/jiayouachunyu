"""
数据库配置和初始化
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

# 创建数据库实例
db = SQLAlchemy()

# 数据库性能监控
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录SQL执行开始时间"""
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute") 
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """记录SQL执行时间"""
    total = time.time() - context._query_start_time
    
    # 记录慢查询
    if total > 1.0:  # 超过1秒的查询
        logging.warning(f"慢查询 ({total:.2f}s): {statement[:200]}...")

def init_database(app):
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 创建默认数据
        create_default_data()

def create_default_data():
    """创建默认数据"""
    from models.user import User, UserRole, ExpertTier
    from models.league import League
    from models.team import Team
    from werkzeug.security import generate_password_hash
    
    try:
        # 检查是否已有管理员用户
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if not admin:
            # 创建默认管理员
            admin_user = User(
                username='admin',
                email='admin@dotaanalysis.com',
                password_hash=generate_password_hash('admin123456'),
                role=UserRole.ADMIN,
                tier=ExpertTier.DIAMOND,
                verified=True
            )
            db.session.add(admin_user)
        
        # 注意：联赛和战队数据应该从外部API同步
        # 这里不创建任何默认的联赛和战队数据
        # 请使用数据同步任务从OpenDota API或Liquipedia获取真实数据
        
        db.session.commit()
        logging.info("默认数据创建完成")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"创建默认数据失败: {e}")

class DatabaseManager:
    """数据库管理工具类"""
    
    @staticmethod
    def backup_database():
        """备份数据库"""
        import subprocess
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backup_{timestamp}.sql"
        
        try:
            # 执行pg_dump
            subprocess.run([
                'pg_dump',
                '-h', 'localhost',
                '-U', 'postgres',
                '-d', 'dota_analysis',
                '-f', f'backups/{backup_file}'
            ], check=True)
            
            logging.info(f"数据库备份完成: {backup_file}")
            return backup_file
            
        except subprocess.CalledProcessError as e:
            logging.error(f"数据库备份失败: {e}")
            return None
    
    @staticmethod
    def optimize_database():
        """优化数据库性能"""
        try:
            # 更新表统计信息
            db.session.execute("ANALYZE;")
            
            # 清理过期数据
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            # 清理过期的用户活动日志
            db.session.execute(
                "DELETE FROM user_activity_logs WHERE created_at < :date",
                {'date': thirty_days_ago}
            )
            
            # 清理过期的内容浏览记录
            db.session.execute(
                "DELETE FROM content_views WHERE created_at < :date",
                {'date': thirty_days_ago}
            )
            
            db.session.commit()
            logging.info("数据库优化完成")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"数据库优化失败: {e}")
    
    @staticmethod
    def get_database_stats():
        """获取数据库统计信息"""
        try:
            result = db.session.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC;
            """)
            
            return [dict(row) for row in result]
            
        except Exception as e:
            logging.error(f"获取数据库统计失败: {e}")
            return []
