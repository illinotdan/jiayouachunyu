/**
 * Node.js 后端配置 - 统一配置系统
 * 从项目根目录的 config.yaml 读取配置
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

class ConfigLoader {
    constructor(configFile = 'config.yaml') {
        this.configFile = configFile;
        this.configData = null;
        this.projectRoot = this.findProjectRoot();
        this.configPath = path.join(this.projectRoot, configFile);
        
        this.loadConfig();
    }
    
    findProjectRoot() {
        // 从当前文件向上查找，直到找到包含 config.yaml 的目录
        let currentPath = __dirname;
        
        while (currentPath !== path.dirname(currentPath)) {
            if (fs.existsSync(path.join(currentPath, this.configFile))) {
                return currentPath;
            }
            currentPath = path.dirname(currentPath);
        }
        
        // 如果没找到，默认返回项目根目录
        return path.resolve(__dirname, '../../../..');
    }
    
    loadConfig() {
        try {
            if (!fs.existsSync(this.configPath)) {
                console.warn(`配置文件不存在: ${this.configPath}`);
                this.configData = {};
                return;
            }
            
            const configContent = fs.readFileSync(this.configPath, 'utf8');
            this.configData = yaml.load(configContent) || {};
            
            console.log(`配置文件加载成功: ${this.configPath}`);
            
        } catch (error) {
            console.error(`加载配置文件失败: ${error.message}`);
            this.configData = {};
        }
    }
    
    resolveEnvVars(value) {
        if (typeof value === 'string' && value.startsWith('${') && value.endsWith('}')) {
            // 格式: ${VAR_NAME:-default_value}
            const envExpr = value.slice(2, -1);
            
            if (envExpr.includes(':-')) {
                const [varName, defaultValue] = envExpr.split(':-', 2);
                return process.env[varName] || defaultValue;
            } else {
                return process.env[envExpr] || '';
            }
        }
        
        return value;
    }
    
    get(keyPath, defaultValue = null) {
        if (!this.configData) {
            return defaultValue;
        }
        
        const keys = keyPath.split('.');
        let value = this.configData;
        
        try {
            for (const key of keys) {
                value = value[key];
            }
            
            // 解析环境变量
            value = this.resolveEnvVars(value);
            return value;
            
        } catch (error) {
            return defaultValue;
        }
    }
    
    getSection(section) {
        return this.configData[section] || {};
    }
    
    getDatabaseUrl(dbType = 'postgresql') {
        if (dbType === 'postgresql') {
            const host = this.get('database.postgresql.host', 'localhost');
            const port = this.get('database.postgresql.port', 5432);
            const database = this.get('database.postgresql.database', 'dota_analysis');
            const username = this.get('database.postgresql.username', 'postgres');
            const password = this.get('database.postgresql.password', 'password');
            
            return `postgresql://${username}:${password}@${host}:${port}/${database}`;
        }
        
        if (dbType === 'redis') {
            const host = this.get('database.redis.host', 'localhost');
            const port = this.get('database.redis.port', 6379);
            const password = this.get('database.redis.password', '');
            const dbNum = this.get('database.redis.databases.cache', 0);
            
            if (password) {
                return `redis://:${password}@${host}:${port}/${dbNum}`;
            } else {
                return `redis://${host}:${port}/${dbNum}`;
            }
        }
        
        return '';
    }
    
    getRedisUrl(purpose = 'cache') {
        const host = this.get('database.redis.host', 'localhost');
        const port = this.get('database.redis.port', 6379);
        const password = this.get('database.redis.password', '');
        const dbNum = this.get(`database.redis.databases.${purpose}`, 0);
        
        if (password) {
            return `redis://:${password}@${host}:${port}/${dbNum}`;
        } else {
            return `redis://${host}:${port}/${dbNum}`;
        }
    }
    
    getOssConfig() {
        return {
            accessKeyId: this.get('oss.access_key_id'),
            accessKeySecret: this.get('oss.access_key_secret'),
            endpoint: this.get('oss.endpoint'),
            bucketName: this.get('oss.bucket_name'),
            enabled: this.get('oss.enabled', true)
        };
    }
    
    getApiConfig(apiName) {
        return this.getSection(`external_apis.${apiName}`);
    }
    
    isEnvironment(env) {
        return this.get('application.environment', 'development') === env;
    }
    
    isDevelopment() {
        return this.isEnvironment('development');
    }
    
    isProduction() {
        return this.isEnvironment('production');
    }
    
    isTesting() {
        return this.isEnvironment('testing');
    }
    
    reload() {
        this.loadConfig();
        console.log('配置文件已重新加载');
    }
}

// 创建全局配置实例
const configLoader = new ConfigLoader();

// Express 应用配置
class ExpressConfig {
    constructor(configLoader) {
        this.configLoader = configLoader;
        this.setupConfig();
    }
    
    setupConfig() {
        // 应用基础配置
        this.app = {
            name: this.configLoader.get('application.name', 'Dota2 Analysis Platform'),
            version: this.configLoader.get('application.version', '1.0.0'),
            environment: this.configLoader.get('application.environment', 'development'),
            debug: this.configLoader.get('application.debug', true)
        };
        
        // 服务器配置
        this.server = {
            host: this.configLoader.get('application.server.host', '0.0.0.0'),
            port: this.configLoader.get('application.server.nodejs_port', 3000)
        };
        
        // 安全配置
        this.security = {
            secretKey: this.configLoader.get('application.security.secret_key', 'nodejs-secret-key'),
            jwtSecret: this.configLoader.get('application.security.jwt_secret_key', 'jwt-secret-key'),
            jwtExpiresIn: this.configLoader.get('application.security.jwt_access_token_expires', 86400),
            passwordHashRounds: this.configLoader.get('application.security.password_hash_rounds', 12)
        };
        
        // CORS 配置
        this.cors = {
            origins: this.configLoader.get('application.cors.origins', ['http://localhost:3000']),
            credentials: this.configLoader.get('application.cors.allow_credentials', true),
            allowedHeaders: this.configLoader.get('application.cors.allow_headers', ['Content-Type', 'Authorization']),
            allowedMethods: this.configLoader.get('application.cors.allow_methods', ['GET', 'POST', 'PUT', 'DELETE'])
        };
        
        // 数据库配置
        this.database = {
            postgresql: {
                url: this.configLoader.getDatabaseUrl('postgresql'),
                host: this.configLoader.get('database.postgresql.host', 'localhost'),
                port: this.configLoader.get('database.postgresql.port', 5432),
                database: this.configLoader.get('database.postgresql.database', 'dota_analysis'),
                username: this.configLoader.get('database.postgresql.username', 'postgres'),
                password: this.configLoader.get('database.postgresql.password', 'password')
            },
            redis: {
                url: this.configLoader.getRedisUrl('cache'),
                host: this.configLoader.get('database.redis.host', 'localhost'),
                port: this.configLoader.get('database.redis.port', 6379),
                password: this.configLoader.get('database.redis.password', '')
            }
        };
        
        // 外部 API 配置
        this.apis = {
            opendota: this.configLoader.getApiConfig('opendota'),
            stratz: this.configLoader.getApiConfig('stratz'),
            steam: this.configLoader.getApiConfig('steam')
        };
        
        // OSS 配置
        this.oss = this.configLoader.getOssConfig();
        
        // 文件上传配置
        this.upload = {
            maxFileSize: this.configLoader.get('oss.file_settings.max_file_size', 16777216),
            allowedExtensions: this.configLoader.get('oss.file_settings.allowed_extensions', {})
        };
        
        // 限流配置
        this.rateLimit = {
            enabled: this.configLoader.get('rate_limiting.enabled', true),
            windowMs: 15 * 60 * 1000, // 15分钟
            max: 100, // 每个窗口期最多100个请求
            standardHeaders: true,
            legacyHeaders: false
        };
        
        // 日志配置
        this.logging = {
            level: this.configLoader.get('logging.level', 'info'),
            format: this.configLoader.get('logging.format', 'combined'),
            directory: this.configLoader.get('logging.file.directory', 'logs'),
            filename: this.configLoader.get('logging.file.filename', 'nodejs.log')
        };
        
        // 监控配置
        this.monitoring = {
            sentry: {
                enabled: this.configLoader.get('monitoring.sentry.enabled', false),
                dsn: this.configLoader.get('monitoring.sentry.dsn', '')
            },
            prometheus: {
                enabled: this.configLoader.get('monitoring.prometheus.enabled', false),
                port: this.configLoader.get('monitoring.prometheus.port', 9090)
            }
        };
        
        // 分页配置
        this.pagination = {
            defaultPageSize: this.configLoader.get('pagination.default_page_size', 20),
            maxPageSize: this.configLoader.get('pagination.max_page_size', 100)
        };
        
        // 缓存配置
        this.cache = this.configLoader.getSection('database.redis.cache');
        
        // 功能开关
        this.features = this.configLoader.getSection('features');
    }
}

// 环境特定配置
class DevelopmentConfig extends ExpressConfig {
    constructor(configLoader) {
        super(configLoader);
        this.app.debug = true;
        this.server.host = '0.0.0.0';
        
        // 开发环境特定配置
        const devConfig = configLoader.getSection('development');
        this.development = {
            autoReload: devConfig.auto_reload || true,
            createTestData: devConfig.create_test_data || true,
            testDataSize: devConfig.test_data_size || 100
        };
    }
}

class ProductionConfig extends ExpressConfig {
    constructor(configLoader) {
        super(configLoader);
        this.app.debug = false;
        
        // 生产环境特定配置
        const prodConfig = configLoader.getSection('production');
        this.production = {
            workers: prodConfig.workers || 4,
            workerConnections: prodConfig.worker_connections || 1000
        };
        
        // 安全增强
        this.security.sessionCookieSecure = true;
        this.security.sessionCookieHttpOnly = true;
        this.security.sessionCookieSameSite = 'Lax';
    }
}

class TestingConfig extends ExpressConfig {
    constructor(configLoader) {
        super(configLoader);
        this.app.debug = false;
        this.app.testing = true;
        
        // 测试环境配置
        const testConfig = configLoader.getSection('testing');
        this.testing = {
            externalApisEnabled: testConfig.external_apis_enabled || false,
            ossEnabled: testConfig.oss_enabled || false,
            mailEnabled: testConfig.mail_enabled || false
        };
        
        // 使用内存数据库进行测试
        this.database.postgresql.url = testConfig.database_url || 'sqlite:///:memory:';
        this.security.jwtExpiresIn = 300; // 5分钟
    }
}

// 根据环境返回对应的配置
function getConfig() {
    const env = configLoader.get('application.environment', 'development');
    
    switch (env) {
        case 'production':
            return new ProductionConfig(configLoader);
        case 'testing':
            return new TestingConfig(configLoader);
        case 'development':
        default:
            return new DevelopmentConfig(configLoader);
    }
}

// 导出配置
module.exports = {
    ConfigLoader,
    ExpressConfig,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    configLoader,
    config: getConfig()
};
