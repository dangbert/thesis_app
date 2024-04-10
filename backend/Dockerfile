FROM python:3.11-slim AS common
RUN apt-get update && apt-get install -y gcc
RUN apt install -y libpq-dev
RUN pip install poetry && poetry config virtualenvs.create false
COPY ./pyproject.toml ./poetry.lock ./

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
RUN echo "available locales:" && locale -a && echo "current locale:" && locale
WORKDIR /backend


FROM common as dev
RUN poetry install --with dev


FROM common as prod
RUN poetry export --format requirements.txt --output requirements_prod.txt --without-hashes --without=dev
RUN pip install --no-cache-dir --upgrade -r requirements_prod.txt
RUN apt remove -y gcc && apt autoremove -y && pip uninstall -y poetry && rm -f requirements_prod.txt
# copy whole backend folder
COPY ./ .
