const { composePlugins, withNx, withReact } = require('@nx/rspack');

module.exports = composePlugins(withNx(), withReact(), (config) => {
  // https://www.rspack.dev/guide/dev-server
  config.devServer.proxy = {
    '/api': {
      // TODO: update this when FastAPI is setup
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  };
  // single page application routing
  config.devServer.historyApiFallback = true;
  return config;
});
