use awesome;
grant select,insert,update,delete on awesome.* to 'root'@'localhost' identified by '151480';
create table tags(
	`blog_id` varchar(50) not null,
	`tag_id` varchar(50) not null,
	`tag_name` varchar(50) not null,
	primary key(`blog_id`,`tag_id`)
)engine=innodb default charset=utf8;

alter table blogs add count bigint not null default 0 after content;