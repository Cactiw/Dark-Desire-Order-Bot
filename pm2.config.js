module.exports = {
  apps : [{
    name: 'Castle bot',
    script: 'castle_bot.py',
    interpreter: 'python3',
    log_file: 'pm2_castle.log',
    min_uptime: 5000,
    kill_timeout: 15000,
    max_restarts: 3,


    // Options reference: https://pm2.keymetrics.io/docs/usage/application-declaration/
    args: '-u',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1500M',
    env: {
      NODE_ENV: 'production'
    },
    env_production: {
      NODE_ENV: 'production'
    }
  },

  {
    name: 'Order bot',
    script: 'order_bot.py',
    interpreter: 'python3',
    log_file: 'pm2_order.log',
    min_uptime: 3000,
    kill_timeout: 10000,
    max_restarts: 3,


    // Options reference: https://pm2.keymetrics.io/docs/usage/application-declaration/
    args: '-u',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1500M',
    env: {
      NODE_ENV: 'production'
    },
    env_production: {
      NODE_ENV: 'production'
    }
  },
  ],

  deploy : {
    production : {
      user : 'node',
      host : '212.83.163.1',
      ref  : 'origin/master',
      repo : 'git@github.com:repo.git',
      path : '/var/www/production',
      'post-deploy' : 'npm install && pm2 reload ecosystem.config.js --env production'
    }
  }
};
