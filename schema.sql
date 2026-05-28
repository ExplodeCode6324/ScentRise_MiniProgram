-- ScentRise 数据库建表脚本
-- 目标：MySQL @ sh-cynosdbmysql-grp-3c7a1auu.sql.tencentcdb.com:20699 / scentrise

DROP TABLE IF EXISTS collection_products;
DROP TABLE IF EXISTS product_tags;
DROP TABLE IF EXISTS collections;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS company_info;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS admins;

-- ============================================
-- 1. 产品系列表
-- ============================================
CREATE TABLE categories (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50)  NOT NULL COMMENT '系列名称',
    icon        VARCHAR(500) COMMENT '分类图标URL',
    sort_order  INT DEFAULT 0 COMMENT '首页宫格排序',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. 产品主表
-- ============================================
CREATE TABLE products (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    product_series  VARCHAR(50)  COMMENT '产品系列(冗余)',
    product_name    VARCHAR(200) NOT NULL COMMENT '产品名称',
    product_model   VARCHAR(100) NOT NULL UNIQUE COMMENT '产品型号(唯一键)',
    product_desc    TEXT         COMMENT '产品简介',
    product_image   VARCHAR(500) COMMENT '产品主图URL',
    product_images  TEXT         COMMENT '多张图片URL(JSON数组)',
    sort_order      INT DEFAULT 0,
    is_active       TINYINT(1) DEFAULT 1 COMMENT '1=上架 0=下架',
    category_id     INT COMMENT '所属系列FK',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 3. 合集表
-- ============================================
CREATE TABLE collections (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(100) NOT NULL COMMENT '合集名称',
    description     TEXT         COMMENT '合集描述',
    cover_image     VARCHAR(500) COMMENT '封面图URL',
    is_carousel     TINYINT(1) DEFAULT 0 COMMENT '1=首页轮播展示',
    sort_order      INT DEFAULT 0,
    carousel_sort   INT DEFAULT 0 COMMENT '轮播排序',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 4. 合集-产品中间表
-- ============================================
CREATE TABLE collection_products (
    collection_id   INT NOT NULL,
    product_id      INT NOT NULL,
    sort_order      INT DEFAULT 0 COMMENT '产品在合集中的展示顺序',
    PRIMARY KEY (collection_id, product_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)    REFERENCES products(id)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 5. 标签表
-- ============================================
CREATE TABLE tags (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(50)  NOT NULL UNIQUE COMMENT '标签名',
    category    VARCHAR(50)  COMMENT '标签分类(适用产品/产品形态/功效)',
    icon        VARCHAR(500) COMMENT '标签图标URL',
    banner_image VARCHAR(500) COMMENT '标签横幅大图URL',
    sort_order  INT DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 6. 产品-标签中间表
-- ============================================
CREATE TABLE product_tags (
    product_id  INT NOT NULL,
    tag_id      INT NOT NULL,
    PRIMARY KEY (product_id, tag_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id)     REFERENCES tags(id)     ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 7. 发现页文章表
-- ============================================
CREATE TABLE articles (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    title           VARCHAR(200) NOT NULL COMMENT '文章标题',
    author          VARCHAR(50)  COMMENT '作者',
    content         TEXT         NOT NULL COMMENT '正文(富文本)',
    cover_image     VARCHAR(500) COMMENT '封面图URL',
    is_published    TINYINT(1) DEFAULT 0 COMMENT '1=已发布 0=草稿',
    published_at    TIMESTAMP    NULL COMMENT '发布时间',
    sort_order      INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 8. 公司信息表(单条记录)
-- ============================================
CREATE TABLE company_info (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    logo            VARCHAR(500) COMMENT 'Logo URL',
    company_image   VARCHAR(500) COMMENT '公司实景图片URL',
    name            VARCHAR(200) COMMENT '公司名称',
    intro           TEXT         COMMENT '公司简介',
    phone           VARCHAR(20)  COMMENT '联系电话',
    wechat_qr       VARCHAR(500) COMMENT '微信二维码URL',
    wechat_id       VARCHAR(50)  COMMENT '微信号',
    email           VARCHAR(100) COMMENT '邮箱',
    address         VARCHAR(500) COMMENT '地址',
    business_hours  VARCHAR(200) COMMENT '营业时间',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 9. 管理员表
-- ============================================
CREATE TABLE admins (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    username    VARCHAR(50)  NOT NULL UNIQUE COMMENT '登录账号',
    passwd      VARCHAR(255) NOT NULL COMMENT '密码(bcrypt加密)',
    real_name   VARCHAR(50)  COMMENT '真实姓名',
    role        VARCHAR(20)  DEFAULT 'editor' COMMENT 'admin/editor',
    is_active   TINYINT(1)   DEFAULT 1,
    last_login  TIMESTAMP    NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 10. 产品图片表
-- ============================================
CREATE TABLE product_images (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    product_id  INT NOT NULL COMMENT '所属产品ID',
    image_url   VARCHAR(500) NOT NULL COMMENT '图片URL',
    sort_order  INT DEFAULT 0 COMMENT '排序(越小越前)',
    is_primary  TINYINT(1) DEFAULT 0 COMMENT '1=主图',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品图片表';
