FROM openjdk:8-alpine-0.2
# openjdk:8-alpine 70M
# github link https://github.com/docker-library/openjdk
WORKDIR /
ADD ./target/*.jar app.jar
EXPOSE 9151
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
