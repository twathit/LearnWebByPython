# 开发日志
此分支为将前任分支bug充分修复后的分支，算是第一个功能完整的分支，所以将此分支设为默认分支。daybyday分支为最早版本的代码，第一版比较完备的代码是在day11.2分支。day11.2分支代码也是最早部署在服务器上的代码,此后分支的代码跟更新日志对应。day5.5分支开始使用bootstrap，界面变好看很多。  

**2017-11-2**  
此个人博客基于python3.6的asyncio，aiohttp库开发，实现异步响应，以及jinja2模板，实现模板复用。前端使用Vue+Bootstrap框架。
自行构建了Web和ORM框架，数据库使用MySQL。网站部署在virtualbox上的Ubuntu server上，其实断断续续花在部署上的事间很久，期间学到很多东西，具体操作写在个人网站上。（2018-6-4注：将网站由原来自己电脑上的virtualbox迁移到阿里云服务器上，网址http://47.106.181.226/ ，第一篇博客仍然是我的部署过程。）
  
**2018-1-9**    
修复了网站的登录功能。

**2018-3-4**  
修复了日志不能编辑bug

**2018-3-16**  
更新了markdown和日志界面

**2018-5-5**  
将前端更新为使用bootstrap，外加自己的一些修改，详见main.css

**2018-5-22**  
更新使用VUE2.5，并且增添了标签功能，可以编辑日志时添加标签，并且查询同一标签下的文章。  

**2018-5-31**  
增加了markdown编辑器[mavon-editor](https://github.com/hinesboy/mavonEditor)

**2018-6-8**  
基于Bootstrap的响应式工具增加了移动端支持，主要隐藏导航栏，增加了侧拉菜单。
