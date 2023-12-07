FROM python:3.8

ENV PYTHONUNBUFFERED 1

RUN useradd -m django

WORKDIR /home/django/

# i18n
RUN apt update && apt -y install gettext


# Copy cache contents (if any) from local machine
# ADD pip-cache.tar.gz .cache/

# Tab-completion feature to django-admin.py and manage.py.
ADD https://raw.githubusercontent.com/django/django/master/extras/django_bash_completion .
RUN echo "source ~/django_bash_completion" >> /home/django/.bashrc

COPY ./requirements.txt ./requirements.txt

RUN chown -R django:django /home/django/

# В моем случае, UID пользователя на хосте совпадает с UID django-юзера: 1000.
USER django:django


RUN pip install --user -r ./requirements.txt \
    && mkdir ~/app \
    && PATH=$PATH:~/home/django/.local/bin


WORKDIR /home/django/app/

ENV PATH "~/.local/bin/:$PATH"

ENTRYPOINT ["bash", "./docker/django/entrypoint.sh"]
