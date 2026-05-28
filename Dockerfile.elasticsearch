ARG ELASTIC_VERSION=9.4.1

FROM docker.elastic.co/elasticsearch/elasticsearch:${ELASTIC_VERSION}

ARG ELASTIC_VERSION

RUN elasticsearch-plugin install --batch \
    https://get.infini.cloud/elasticsearch/analysis-ik/${ELASTIC_VERSION}
