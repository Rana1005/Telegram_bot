module.exports = {
  apps: [
    {
      name: "telegram-joshua-8000",
      script: "app.py",
      args: "runserver 0.0.0.0:8000",
      interpreter: "/usr/bin/python3",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
    },
  ],
};

