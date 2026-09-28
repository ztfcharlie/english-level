# 播放器是一个自包含的单文件页面 —— 27 个级别、2378 集的数据全部内嵌在 HTML 里，
# 所以这里没有 API、没有数据库、没有任何要配的东西。nginx 只负责发一个静态页。
FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 英语分级播放器.html 跟 index.html 是逐字节相同的两个文件，所以这里用同一个源
# COPY 两次就够了 —— 顺带让本文件里不出现中文路径（有些构建器处理非 ASCII 路径
# 仍然会出问题，能不碰就不碰）。
COPY index.html /usr/share/nginx/html/index.html
COPY index.html /usr/share/nginx/html/play.html

# 给人看的合集清单（缺口标注 + 备用源）。
COPY *.md /usr/share/nginx/html/

EXPOSE 80
