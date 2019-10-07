FROM registry.access.redhat.com/ubi8/python-36
LABEL maintainer="Serhii Kryzhnii skryzhni@redhat.com"
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY git-keeper.py .
COPY git-keeper-entrypoint.sh /git-keeper-entrypoint.sh
ENTRYPOINT /git-keeper-entrypoint.sh
COPY gpgs/*.pub.asc /
