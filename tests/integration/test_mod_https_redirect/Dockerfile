ARG PHP_HASH_TAG=':8.1-apache'
FROM php${PHP_HASH_TAG}
EXPOSE 443 80 8443 8080

# bullseye-security's live pool no longer serves the exact point releases this
# image's dpkg status expects (index/pool desync on deb.debian.org since
# bullseye went EOL), causing 404s. Pin apt to the snapshot.debian.org mirror
# already referenced (commented out) in this image's own sources.list, dated
# to the image's build day, instead of the live mirror.
RUN sed -i "s|# deb http://snapshot.debian.org|deb [check-valid-until=no] http://snapshot.debian.org|g; s|^deb http://deb.debian.org|# deb http://deb.debian.org|g" /etc/apt/sources.list

RUN apt-get -y update && \
    apt-get -y install openssl -y && \
    apt-get -y clean && \
    apt-get -y autoremove && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    truncate -s 0 /var/log/*log

RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/apache2/server.key -out /etc/apache2/server.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

RUN /usr/sbin/a2enmod rewrite ssl

COPY ./apache_conf/000-default.conf /etc/apache2/sites-available/000-default.conf

# Start Apache
CMD ["apache2-foreground"]
