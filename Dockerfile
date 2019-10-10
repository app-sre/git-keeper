FROM registry.access.redhat.com/ubi8/python-36
LABEL maintainer="Serhii Kryzhnii skryzhni@redhat.com"
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY git-keeper.py .
RUN ln -s  /config/.netrc ~/.netrc
ENTRYPOINT ["./git-keeper.py"]
