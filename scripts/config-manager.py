#!/usr/bin/env python3
"""
配置管理工具
用于管理和验证统一配置文件
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """初始化配置管理器"""
        self.config_file = config_file
        self.project_root = self._find_project_root()
        self.config_path = self.project_root / config_file
        
    def _find_project_root(self) -> Path:
        """查找项目根目录"""
        current_path = Path(__file__).resolve()
        
        # 从当前文件向上查找，直到找到包含config.yaml的目录
        for parent in current_path.parents:
            if (parent / self.config_file).exists():
                return parent
        
        # 如果没找到，返回当前脚本的父目录
        return current_path.parent
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if not self.config_path.exists():
                print(f"❌ 配置文件不存在: {self.config_path}")
                return {}
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
                
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
            
            print(f"✅ 配置文件已保存: {self.config_path}")
            return True
            
        except Exception as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """验证配置文件"""
        config = self.load_config()
        errors = []
        
        if not config:
            errors.append("配置文件为空或无法加载")
            return errors
        
        # 必需的配置段落
        required_sections = [
            'application',
            'database',
            'external_apis',
            'oss',
            'celery',
            'data_sync',
            'logging'
        ]
        
        for section in required_sections:
            if section not in config:
                errors.append(f"缺少必需的配置段落: {section}")
        
        # 验证应用配置
        if 'application' in config:
            app_config = config['application']
            required_app_fields = ['name', 'version', 'environment']
            
            for field in required_app_fields:
                if field not in app_config:
                    errors.append(f"应用配置缺少字段: {field}")
        
        # 验证数据库配置
        if 'database' in config:
            db_config = config['database']
            
            if 'postgresql' not in db_config:
                errors.append("缺少PostgreSQL数据库配置")
            else:
                pg_config = db_config['postgresql']
                required_pg_fields = ['host', 'port', 'database', 'username', 'password']
                
                for field in required_pg_fields:
                    if field not in pg_config:
                        errors.append(f"PostgreSQL配置缺少字段: {field}")
            
            if 'redis' not in db_config:
                errors.append("缺少Redis数据库配置")
        
        # 验证OSS配置
        if 'oss' in config:
            oss_config = config['oss']
            required_oss_fields = ['access_key_id', 'access_key_secret', 'endpoint', 'bucket_name']
            
            for field in required_oss_fields:
                if field not in oss_config:
                    errors.append(f"OSS配置缺少字段: {field}")
        
        return errors
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """检查环境变量"""
        config = self.load_config()
        env_vars = {}
        missing_vars = []
        
        def extract_env_vars(obj, path=""):
            """递归提取环境变量"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    extract_env_vars(value, current_path)
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                # 解析环境变量格式: ${VAR_NAME:-default_value}
                env_expr = obj[2:-1]
                
                if ":-" in env_expr:
                    var_name, default_value = env_expr.split(":-", 1)
                else:
                    var_name = env_expr
                    default_value = None
                
                current_value = os.getenv(var_name)
                env_vars[var_name] = {
                    'current_value': current_value,
                    'default_value': default_value,
                    'is_set': current_value is not None,
                    'used_in': path
                }
                
                if current_value is None and default_value is None:
                    missing_vars.append(var_name)
        
        extract_env_vars(config)
        
        return {
            'env_vars': env_vars,
            'missing_vars': missing_vars,
            'total_vars': len(env_vars),
            'set_vars': len([v for v in env_vars.values() if v['is_set']])
        }
    
    def generate_env_template(self) -> str:
        """生成环境变量模板"""
        env_info = self.check_environment_variables()
        template_lines = [
            "# Dota2 战队分析系统 - 环境变量配置",
            "# 请根据实际情况填写以下环境变量",
            ""
        ]
        
        # 按类别组织环境变量
        categories = {
            'SECRET_KEY': '# 安全配置',
            'JWT_SECRET_KEY': '',
            'POSTGRES_': '# 数据库配置',
            'REDIS_': '',
            'OPENDOTA_': '# 外部API配置',
            'STRATZ_': '',
            'STEAM_': '',
            'ALIYUN_': '# 阿里云OSS配置',
            'MAIL_': '# 邮件配置',
            'SENTRY_': '# 监控配置'
        }
        
        current_category = None
        
        for var_name, var_info in sorted(env_info['env_vars'].items()):
            # 检查是否需要添加类别注释
            for prefix, comment in categories.items():
                if var_name.startswith(prefix) and comment and current_category != comment:
                    if current_category is not None:
                        template_lines.append("")
                    template_lines.append(comment)
                    current_category = comment
                    break
            
            # 添加环境变量
            default_value = var_info['default_value'] or ""
            current_value = var_info['current_value']
            
            if current_value:
                # 如果已设置，显示当前值（敏感信息只显示前几位）
                if any(sensitive in var_name.lower() for sensitive in ['key', 'secret', 'password']):
                    display_value = current_value[:8] + "..." if len(current_value) > 8 else current_value
                else:
                    display_value = current_value
                template_lines.append(f"{var_name}={display_value}")
            else:
                # 如果未设置，显示默认值或占位符
                template_lines.append(f"{var_name}={default_value}")
        
        return "\n".join(template_lines)
    
    def show_status(self):
        """显示配置状态"""
        print("🔧 Dota2 战队分析系统 - 配置状态")
        print("=" * 60)
        
        # 配置文件状态
        print(f"📁 配置文件: {self.config_path}")
        print(f"   存在: {'✅' if self.config_path.exists() else '❌'}")
        
        if self.config_path.exists():
            file_size = self.config_path.stat().st_size
            print(f"   大小: {file_size} bytes")
        
        # 验证配置
        print("\n🔍 配置验证:")
        errors = self.validate_config()
        
        if not errors:
            print("   ✅ 配置文件验证通过")
        else:
            print("   ❌ 发现配置问题:")
            for error in errors:
                print(f"      - {error}")
        
        # 环境变量状态
        print("\n🌍 环境变量状态:")
        env_info = self.check_environment_variables()
        
        print(f"   总计: {env_info['total_vars']} 个")
        print(f"   已设置: {env_info['set_vars']} 个")
        print(f"   未设置: {len(env_info['missing_vars'])} 个")
        
        if env_info['missing_vars']:
            print("   ❌ 缺少的环境变量:")
            for var in env_info['missing_vars']:
                print(f"      - {var}")
        else:
            print("   ✅ 所有必需的环境变量都已设置")
        
        # 服务状态检查
        print("\n🔧 服务依赖检查:")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查服务依赖"""
        dependencies = [
            ("Python", "python --version"),
            ("Java", "java -version"),
            ("PostgreSQL", "psql --version"),
            ("Redis", "redis-cli --version"),
            ("Docker", "docker --version"),
            ("Docker Compose", "docker-compose --version")
        ]
        
        for name, command in dependencies:
            try:
                import subprocess
                result = subprocess.run(
                    command.split(), 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                
                if result.returncode == 0:
                    # 提取版本信息
                    version_output = result.stdout.strip() or result.stderr.strip()
                    version_line = version_output.split('\n')[0]
                    print(f"   ✅ {name}: {version_line}")
                else:
                    print(f"   ❌ {name}: 未安装或不可用")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                print(f"   ❌ {name}: 检查失败")
    
    def backup_config(self) -> bool:
        """备份配置文件"""
        if not self.config_path.exists():
            print("❌ 配置文件不存在，无法备份")
            return False
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config_path.parent / f"config_backup_{timestamp}.yaml"
        
        try:
            import shutil
            shutil.copy2(self.config_path, backup_path)
            print(f"✅ 配置文件已备份到: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {e}")
            return False
    
    def restore_config(self, backup_file: str) -> bool:
        """恢复配置文件"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_path}")
            return False
        
        try:
            import shutil
            shutil.copy2(backup_path, self.config_path)
            print(f"✅ 配置文件已从备份恢复: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Dota2 战队分析系统配置管理工具")
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 状态命令
    subparsers.add_parser('status', help='显示配置状态')
    
    # 验证命令
    subparsers.add_parser('validate', help='验证配置文件')
    
    # 环境变量命令
    env_parser = subparsers.add_parser('env', help='环境变量管理')
    env_parser.add_argument('--check', action='store_true', help='检查环境变量')
    env_parser.add_argument('--template', action='store_true', help='生成环境变量模板')
    env_parser.add_argument('--output', '-o', help='输出文件路径')
    
    # 备份命令
    backup_parser = subparsers.add_parser('backup', help='备份配置文件')
    
    # 恢复命令
    restore_parser = subparsers.add_parser('restore', help='恢复配置文件')
    restore_parser.add_argument('backup_file', help='备份文件路径')
    
    # 配置文件参数
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 创建配置管理器
    config_manager = ConfigManager(args.config)
    
    if args.command == 'status':
        config_manager.show_status()
        
    elif args.command == 'validate':
        errors = config_manager.validate_config()
        if not errors:
            print("✅ 配置文件验证通过")
        else:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
            
    elif args.command == 'env':
        if args.check:
            env_info = config_manager.check_environment_variables()
            print(f"环境变量统计:")
            print(f"  总计: {env_info['total_vars']}")
            print(f"  已设置: {env_info['set_vars']}")
            print(f"  未设置: {len(env_info['missing_vars'])}")
            
            if env_info['missing_vars']:
                print("未设置的环境变量:")
                for var in env_info['missing_vars']:
                    print(f"  - {var}")
        
        elif args.template:
            template = config_manager.generate_env_template()
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(template)
                print(f"✅ 环境变量模板已保存到: {args.output}")
            else:
                print(template)
        
        else:
            env_info = config_manager.check_environment_variables()
            print(json.dumps(env_info, indent=2, ensure_ascii=False))
            
    elif args.command == 'backup':
        config_manager.backup_config()
        
    elif args.command == 'restore':
        config_manager.restore_config(args.backup_file)

if __name__ == "__main__":
    main()
