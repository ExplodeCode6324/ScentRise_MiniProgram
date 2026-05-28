import os

DEBUG = True

# MySQL 连接
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", '9CPcksGG')
db_address = os.environ.get(
    "MYSQL_ADDRESS",
    'sh-cynosdbmysql-grp-lq5288ye.sql.tencentcdb.com:21835'
)

# JWT 密钥（生产环境应通过环境变量覆盖）
JWT_SECRET = os.environ.get('JWT_SECRET', 'scentrise-admin-secret-2026')
