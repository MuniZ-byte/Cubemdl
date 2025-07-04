const path = require('path');

module.exports = {
    // Database configuration
    dbType: process.env.CUBEJS_DB_TYPE || 'postgres',

    driverFactory: ({ type }) => {
        if (type === 'postgres') {
            const PostgresDriver = require('@cubejs-backend/postgres-driver');
            return new PostgresDriver({
                host: process.env.CUBEJS_DB_HOST,
                port: process.env.CUBEJS_DB_PORT || 5432,
                database: process.env.CUBEJS_DB_NAME,
                user: process.env.CUBEJS_DB_USER,
                password: process.env.CUBEJS_DB_PASS,
                ssl: process.env.CUBEJS_DB_SSL === 'true' ? { rejectUnauthorized: false } : false,
            });
        }
        throw new Error(`Unsupported database type: ${type}`);
    },

    // API configuration
    apiSecret: process.env.CUBEJS_API_SECRET || 'SECRET',

    // Schema path - where your generated models are located
    schemaPath: path.join(__dirname, 'model'),

    // Web sockets
    webSocketsBasePath: process.env.CUBEJS_WEB_SOCKETS_BASE_PATH,

    // SQL API
    pgSqlPort: process.env.CUBEJS_PG_SQL_PORT,
    sqlUser: process.env.CUBEJS_SQL_USER,
    sqlPassword: process.env.CUBEJS_SQL_PASSWORD,

    // CORS settings for development
    checkAuth: (req, auth) => {
        // For development, allow all requests
        // In production, implement proper authentication
        return {};
    }
};
