drop database if exists twathit;
create database twathit;
use twathit;
# 赋给用户权限
grant select,insert,update,delete on twathit.* to 'root'@'localhost' identified by '151480';
create table users(
     `id` varchar(50) not null,
     `email` varchar(50) not null,
     `password` varchar(50) not null,
     `admin` bool not null,
     `name` varchar(50) not null,
     `image` varchar(500) not null,
     `created_at` real not null,
     unique key `idx_email` (`email`),
     key `idx_created_at` (`created_at`),
     primary key(`id`)
)engine=innodb default charset=utf8;
create table blogs(
     `id` varchar(50) not null,
     `user_id` varchar(50) not null,
     `user_name` varchar(50) not null,
     `user_image` varchar(500) not null,
     `name` varchar(50) not null,
     `summary` varchar(200) not null,
     `content` mediumtext not null,
     `tags` varchar(50) not null,
     `count` bigint not null,
     `created_at` real not null,
     key `idx_created_at` (`created_at`),
     primary key(`id`)
)engine=innodb default charset=utf8;
create table comments(
     `id` varchar(50) not null,
     `blog_id` varchar(50) not null,
     `user_id` varchar(50) not null,
     `user_name` varchar(50) not null,
     `user_image` varchar(500) not null,
     `content` mediumtext not null,
     `created_at` real not null,
     key `idx_created_at` (`created_at`),
     primary key(`id`)
)engine=innodb default charset=utf8;