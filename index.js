require('dotenv').config();
const CubejsServer = require('@cubejs-backend/server-core');

const server = new CubejsServer();

const port = process.env.PORT || 4000;

server.listen({ port }).then(({ version, port: actualPort }) => {
    console.log(`🚀 Cube.js server (${version}) is listening on port ${actualPort}`);
    console.log(`📊 Playground: http://localhost:${actualPort}`);
    console.log(`🔗 API endpoint: http://localhost:${actualPort}/cubejs-api/v1`);

    if (process.env.CUBEJS_PG_SQL_PORT) {
        console.log(`🐘 SQL API: postgresql://${process.env.CUBEJS_SQL_USER}:${process.env.CUBEJS_SQL_PASSWORD}@localhost:${process.env.CUBEJS_PG_SQL_PORT}/cube`);
    }

    console.log('✅ Cube.js is ready to serve your LLM-generated models!');
}).catch(e => {
    console.error('❌ Error starting Cube.js server:', e);
    process.exit(1);
});
