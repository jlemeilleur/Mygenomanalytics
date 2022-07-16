limit_req_zone binary_remote_addr zone=limitreqsbyaddr:10m rate=40r/m;
limit_req_status 429;

server {
    listen ${LISTEN_PORT};

    location /static {
        alias /vol/static;
    }

    location / {
        uwsgi_pass              ${APP_HOST}:${APP_PORT};
        include                 /etc/nginx/uwsgi_params;
        client_max_body_size    50M;
        uwsgi_read_timeout      200;
    }
}