module.exports = {
  apps: [
    {
      name: 'react-vite-app',
      script: 'serve',
      args: '-s dist -l 7077', // Serve the "dist" folder on port 3000
      env: {
        NODE_ENV: 'production',
      },
    },
  ],
};