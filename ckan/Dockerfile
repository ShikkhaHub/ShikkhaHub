# ShikkhaHub CKAN image — extends the official CKAN image with scheming
# metadata config, seed scripts, and the recommended extensions.
#
#   docker build -t shikkhahub/ckan:2.10.5 -f ckan/Dockerfile ckan

ARG CKAN_VERSION=2.10.5
FROM ckan/ckan:${CKAN_VERSION}

# ckanext-scheming is bundled with the official image; ensure the optional
# extensions used by this deployment are present.
RUN pip install --no-cache-dir \
    ckanext-dcat \
    ckanext-harvest \
    ckanext-spatial \
    ckanext-xloader \
    ckanext-scheming

# Scheming metadata schemas + seed catalog (mounted read-only at runtime too)
COPY config/ckan.ini /srv/app/ckan.ini
COPY config/scheming /srv/app/scheming
COPY config/seed_catalog.json /srv/app/config/seed_catalog.json
COPY scripts /srv/app/scripts

RUN chmod +x /srv/app/scripts/bootstrap.sh /srv/app/scripts/seed_catalog.py
