FROM openjdk:8-alpine
RUN echo "http://mirrors.aliyun.com/alpine/v3.7/main/" > /etc/apk/repositories
RUN echo "http://mirrors.aliyun.com/alpine/v3.7/community/" >> /etc/apk/repositories

# install package
RUN apk add curl --no-cache

# install fonts
RUN apk add --no-cache font-adobe-100dpi ttf-dejavu fontconfig
