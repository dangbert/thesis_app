const { composePlugins, withNx, withReact } = require('@nx/rspack');

module.exports = composePlugins(withNx(), withReact(), (config) => {
  config.devServer = {
    ...config.devServer,
    port: process.env.DEV_HOST_PORT || 3000,
    proxy: {
      '/api': {
        target: 'http://flask:5000',
        changeOrigin: true,
      },
    },
    historyApiFallback: {
      // full settings: https://github.com/bripkens/connect-history-api-fallback
      index: '/index.html',
      verbose: 'true',
      disableDotRule: true, // avoid "Not rewriting GET /p/example.md because the path includes a dot (.) character."
    },
    client: {
      logging: 'verbose',
    },
  };

  return config;
});
