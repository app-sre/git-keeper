FROM registry.access.redhat.com/ubi8/python-36
LABEL mainteiner="Serhii Kryzhnii"
COPY git-keeper.py .
RUN pip install --upgrade pip && pip install sh boto3 gnupg 
CMD ./git-keeper.py
