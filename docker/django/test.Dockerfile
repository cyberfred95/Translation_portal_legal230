FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN useradd -m django

WORKDIR /home/django/

# Copy cache contents (if any) from local machine
# ADD pip-cache.tar.gz .cache/

COPY ./requirements.txt ./requirements.txt
COPY ./requirements_test.txt ./requirements_test.txt

RUN chown -R django:django /home/django/

# В моем случае, UID пользователя на хосте совпадает с UID django-юзера: 1000.
USER django:django

RUN pip install --user -r ./requirements_test.txt \
    && mkdir ~/app

WORKDIR /home/django/app/

ENV PATH "~/.local/bin/:$PATH"

ENTRYPOINT ["bash", "./docker/django/entrypoint.sh"]
