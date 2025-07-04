module.exports = {
    contextToAppId: ({ securityContext }) => `CUBEJS_APP_${securityContext.user_id || 'UNKNOWN'}`,
    contextToOrchestratorId: ({ securityContext }) => `CUBEJS_APP_${securityContext.user_id || 'UNKNOWN'}`,

    // Redis configuration for cache and queue
    cacheAndQueueDriver: 'memory', // Changed from 'redis' to 'memory'

    // API settings
    apiSecret: process.env.CUBEJS_API_SECRET || 'SECRET',

    // Scheduled refresh
    scheduledRefreshTimer: 30,

    // Pre-aggregations configuration
    preAggregationsSchema: process.env.CUBEJS_PRE_AGGREGATIONS_SCHEMA || 'pre_aggregations',
};
