-- ============================================================
-- 企业人员资产管理后台系统 · 建表脚本（MySQL 8.0）
-- 阶段1：员工表、资产表
-- 阶段2：无新表（规范化改造）
-- 阶段3：用户表、角色表、用户角色关联表、领用记录表
-- 说明：使用 MySQL 时执行本脚本；使用 SQLite 时由程序自动建表
-- ============================================================

CREATE DATABASE IF NOT EXISTS `asset_admin` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `asset_admin`;

-- ------------------------------------------------------------
-- 员工表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `employee`;
CREATE TABLE `employee` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `emp_no`      VARCHAR(32)  NOT NULL                COMMENT '工号',
  `name`        VARCHAR(50)  NOT NULL                COMMENT '姓名',
  `gender`      VARCHAR(10)  DEFAULT '男'            COMMENT '性别',
  `department`  VARCHAR(50)  DEFAULT NULL            COMMENT '部门',
  `position`    VARCHAR(50)  DEFAULT NULL            COMMENT '职位',
  `phone`       VARCHAR(20)  DEFAULT NULL            COMMENT '手机号',
  `email`       VARCHAR(100) DEFAULT NULL            COMMENT '邮箱',
  `hire_date`   DATE         DEFAULT NULL            COMMENT '入职日期',
  `status`      VARCHAR(10)  DEFAULT '在职'          COMMENT '状态：在职/离职',
  `attachment_path` VARCHAR(255) DEFAULT NULL        COMMENT '附件存储路径',
  `attachment_name` VARCHAR(255) DEFAULT NULL        COMMENT '附件原始文件名',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_emp_no` (`emp_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='员工表';

-- ------------------------------------------------------------
-- 资产表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `asset`;
CREATE TABLE `asset` (
  `id`            INT           NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `asset_no`      VARCHAR(32)   NOT NULL                COMMENT '资产编号',
  `name`          VARCHAR(100)  NOT NULL                COMMENT '资产名称',
  `category`      VARCHAR(50)   DEFAULT NULL            COMMENT '资产类别',
  `brand`         VARCHAR(50)   DEFAULT NULL            COMMENT '品牌',
  `model`         VARCHAR(50)   DEFAULT NULL            COMMENT '型号',
  `price`         DECIMAL(10,2) DEFAULT 0.00            COMMENT '购置价格',
  `purchase_date` DATE          DEFAULT NULL            COMMENT '购置日期',
  `status`        VARCHAR(10)   DEFAULT '空闲'          COMMENT '状态：空闲/已领用/维修/报废',
  `user_id`       INT           DEFAULT NULL            COMMENT '领用人员工ID（关联employee.id）',
  `remark`        VARCHAR(255)  DEFAULT NULL            COMMENT '备注',
  `create_time`   DATETIME      DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_asset_no` (`asset_no`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产表';

-- ------------------------------------------------------------
-- 角色表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `code`        VARCHAR(32)  NOT NULL                COMMENT '角色编码：admin/employee',
  `name`        VARCHAR(50)  NOT NULL                COMMENT '角色名称',
  `description` VARCHAR(255) DEFAULT NULL            COMMENT '描述',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色表';

-- ------------------------------------------------------------
-- 用户表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id`            INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `username`      VARCHAR(50)  NOT NULL                COMMENT '登录账号',
  `password_hash` VARCHAR(100) NOT NULL                COMMENT '密码哈希（bcrypt）',
  `real_name`     VARCHAR(50)  DEFAULT NULL            COMMENT '姓名',
  `status`        VARCHAR(10)  DEFAULT '启用'          COMMENT '状态：启用/禁用',
  `create_time`   DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ------------------------------------------------------------
-- 用户角色关联表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `user_role`;
CREATE TABLE `user_role` (
  `user_id` INT NOT NULL COMMENT '用户ID（关联user.id）',
  `role_id` INT NOT NULL COMMENT '角色ID（关联role.id）',
  PRIMARY KEY (`user_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联表';

-- ------------------------------------------------------------
-- 资产领用记录表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `asset_record`;
CREATE TABLE `asset_record` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `asset_id`    INT          NOT NULL                COMMENT '资产ID（关联asset.id）',
  `employee_id` INT          NOT NULL                COMMENT '领用人员工ID（关联employee.id）',
  `action`      VARCHAR(10)  NOT NULL                COMMENT '动作：领用/归还',
  `operator_id` INT          DEFAULT NULL            COMMENT '操作人用户ID（关联user.id）',
  `remark`      VARCHAR(255) DEFAULT NULL            COMMENT '备注',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `idx_asset_id` (`asset_id`),
  KEY `idx_employee_id` (`employee_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资产领用记录表';

-- ------------------------------------------------------------
-- AI 知识库文档表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `ai_document`;
CREATE TABLE `ai_document` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `filename`    VARCHAR(255) NOT NULL                COMMENT '原始文件名（项目资料为相对路径）',
  `file_path`   VARCHAR(255) NOT NULL                COMMENT '存储路径',
  `file_size`   INT          DEFAULT 0               COMMENT '文件大小(字节)',
  `chunk_count` INT          DEFAULT 0               COMMENT '切片数量',
  `category`    VARCHAR(20)  DEFAULT 'upload'        COMMENT '来源：upload 上传 / project 项目资料',
  `uploader_id` INT          DEFAULT NULL            COMMENT '上传人用户ID（关联user.id）',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI知识库文档表';

-- ------------------------------------------------------------
-- AI 知识库切片表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `ai_chunk`;
CREATE TABLE `ai_chunk` (
  `id`          INT  NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `document_id` INT  NOT NULL                COMMENT '文档ID（关联ai_document.id）',
  `seq`         INT  DEFAULT 0               COMMENT '切片序号',
  `content`     TEXT NOT NULL                COMMENT '切片内容',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_document_id` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI知识库切片表';

-- ------------------------------------------------------------
-- AI 工作流运行记录表
-- ------------------------------------------------------------
DROP TABLE IF EXISTS `ai_workflow_run`;
CREATE TABLE `ai_workflow_run` (
  `id`            INT          NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `requirement`   TEXT         NOT NULL                COMMENT '开发需求',
  `status`        VARCHAR(20)  DEFAULT '成功'          COMMENT '状态：成功/失败',
  `review_rounds` INT          DEFAULT 0               COMMENT '评审循环轮次',
  `steps`         TEXT         DEFAULT NULL            COMMENT '步骤日志(JSON)',
  `result`        TEXT         DEFAULT NULL            COMMENT '最终产出代码',
  `duration_ms`   INT          DEFAULT 0               COMMENT '总耗时(毫秒)',
  `operator_id`   INT          DEFAULT NULL            COMMENT '操作人用户ID（关联user.id）',
  `create_time`   DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '运行时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI工作流运行记录表';

-- ------------------------------------------------------------
-- 演示数据（可选）
-- ------------------------------------------------------------
INSERT INTO `employee` (`emp_no`, `name`, `gender`, `department`, `position`, `phone`, `email`, `hire_date`, `status`) VALUES
('E001', '张伟', '男', '技术部', '后端工程师', '13800000001', 'zhangwei@example.com', '2022-03-01', '在职'),
('E002', '李娜', '女', '人事部', 'HR主管',     '13800000002', 'lina@example.com',     '2021-07-15', '在职'),
('E003', '王强', '男', '技术部', '前端工程师', '13800000003', 'wangqiang@example.com','2023-02-20', '在职'),
('E004', '刘洋', '男', '财务部', '会计',       '13800000004', 'liuyang@example.com',  '2020-11-05', '在职'),
('E005', '陈静', '女', '市场部', '市场专员',   '13800000005', 'chenjing@example.com', '2024-06-01', '在职');

INSERT INTO `asset` (`asset_no`, `name`, `category`, `brand`, `model`, `price`, `purchase_date`, `status`, `user_id`, `remark`) VALUES
('ZC20260001', '联想笔记本',   '电脑设备', 'Lenovo',  'ThinkPad X1', 8999.00, '2023-05-10', '空闲',   NULL, '技术部备用机'),
('ZC20260002', '戴尔显示器',   '电脑设备', 'Dell',    'U2723QE',     3299.00, '2023-06-18', '已领用', 1,    '张伟领用'),
('ZC20260003', '惠普打印机',   '办公用品', 'HP',      'M479fdw',     4599.00, '2022-09-01', '维修',   NULL, '进纸器故障送修'),
('ZC20260004', '群晖NAS服务器','网络设备', 'Synology','DS1823xs+',  12999.00, '2023-01-12', '空闲',   NULL, '存放项目资料'),
('ZC20260005', '人体工学办公椅','办公用品', 'ErgoPro', 'EP-2023',     1299.00, '2023-03-25', '已领用', 4,    '刘洋领用'),
('ZC20260006', '爱普生投影仪', '办公用品', 'Epson',   'CB-L630U',   18999.00, '2020-04-08', '报废',   NULL, '已到报废年限');

INSERT INTO `role` (`code`, `name`, `description`) VALUES
('admin',    '管理员',   '系统管理员，可增删改查全部数据'),
('employee', '普通员工', '只读权限，仅可查看数据');

-- 密码均为 123456（bcrypt 哈希）
INSERT INTO `user` (`username`, `password_hash`, `real_name`, `status`) VALUES
('admin',    '$2b$12$dJPVgnCOm2RZGLgIaPguy.mcD0cli2bppgvODBIolKLgCt3nxsxQO', '系统管理员', '启用'),
('zhangsan', '$2b$12$dJPVgnCOm2RZGLgIaPguy.mcD0cli2bppgvODBIolKLgCt3nxsxQO', '张伟',       '启用');

INSERT INTO `user_role` (`user_id`, `role_id`) VALUES
(1, 1),
(2, 2);
