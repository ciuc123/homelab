ARG PHP=8.4
FROM php:${PHP}-cli
COPY --chown=www-data:www-data app /app
WORKDIR /app
RUN printf "opcache.enable_cli=1\nopcache.jit=disable\nzend.assertions=-1\nmemory_limit=1G\nrealpath_cache_size=4096k\n" > /usr/local/etc/php/conf.d/zz-bench.ini
USER www-data
