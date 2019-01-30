FROM python:3.7.0-slim-stretch

LABEL maintainer.name="Lubo Obratil"
LABEL maintainer.email="lubomir.obratil@gmail.com"
LABEL image.source="https://github.com/LuboO/rtt-pyscript-base-docker"
LABEL project="https://github.com/crocs-muni/randomness-testing-toolkit"

RUN apt update && \
	apt -y install build-essential default-libmysqlclient-dev && \
	pip install fabric2 mysqlclient

COPY rtt_pyutils /rtt_pyutils/

ENV RTT_PYSCRIPT_BASE_LOGS_DIR=/script_logs \
	RTT_PYSCRIPT_BASE_CNF_DIR=/script_configuration

VOLUME ["$RTT_PYSCRIPT_BASE_LOGS_DIR", "$RTT_PYSCRIPT_BASE_CNF_DIR"]

