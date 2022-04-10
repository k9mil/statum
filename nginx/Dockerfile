FROM nginx

RUN apt update -y \
    && apt install nginx -y \
    && apt-get install software-properties-common -y \
    && add-apt-repository -r ppa:certbot/certbot -y \
    && apt-get update -y \
    && apt-get install python3-certbot-nginx -y \
    && apt-get clean

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/
