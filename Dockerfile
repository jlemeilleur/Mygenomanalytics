FROM python:3.9
LABEL maintainer = "mygenomanalytics.com"
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
COPY ./my_snp_api /my_snp_api
COPY ./scripts /scripts
#COPY ./static /static

WORKDIR /my_snp_api
EXPOSE 8000

RUN chmod -R +x /my_snp_api/*
    #chmod -R 775 /my_snp_api/static/media/csvs/work

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /requirements.txt && \
    adduser --disabled-password --no-create-home user

RUN mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chown -R user:user /vol && \
    #chmod -R +rwx /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

#ENV PATH="/py/bin:$PATH"
ENV PATH="/scripts:/py/bin:$PATH"
#RUN adduser -D user
#RUN chown -R user:user /vol

#RUN chown -R user:user /my_snp_api/db.sqlite3 && \
#    chmod +rwx /my_snp_api/db.sqlite3

#RUN chown user:user /my_snp_api/db.sqlite3 && \
#    chmod +rwx /my_snp_api/db.sqlite3

USER user

CMD ["run.sh"]
#CMD ["/scripts/run.sh"]


