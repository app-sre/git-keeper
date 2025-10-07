FROM        registry.access.redhat.com/ubi9/python-312@sha256:9b84a91c94aa7e7ebfcd416db7857610bc7872ba6170cfa7b0753590d4b71dd0 AS builder
LABEL       maintainer="Serhii Kryzhnii skryzhni@redhat.com"
WORKDIR     /git-keeper
COPY        --from=ghcr.io/astral-sh/uv:0.8.24@sha256:1d31be550ff927957472b2a491dc3de1ea9b5c2d319a9cea5b6a48021e2990a6 /uv /bin/uv
COPY        --chown=1001:0 pyproject.toml uv.lock ./
RUN         uv lock --locked
COPY        --chown=1001:0 git-keeper.py ./git-keeper.py
RUN         uv sync --frozen --no-cache --compile-bytecode --no-group dev --python /usr/bin/python3.12

FROM        registry.access.redhat.com/ubi9/ubi-minimal:9.4-1227@sha256:f182b500ff167918ca1010595311cf162464f3aa1cab755383d38be61b4d30aa AS prod
RUN         microdnf upgrade -y && \
            microdnf install -y python3.12 git tar && \
            microdnf clean all
WORKDIR     /git-keeper
RUN         ln -s  /config/.netrc /git-keeper/.netrc
RUN         chown -R 1001:0 /git-keeper
USER        1001
ENV         VIRTUAL_ENV=/git-keeper/.venv
ENV         PATH="$VIRTUAL_ENV/bin:$PATH"
COPY        --from=builder /git-keeper /git-keeper

ENTRYPOINT  ["python3", "git-keeper.py"]

FROM        prod AS test
COPY        --from=ghcr.io/astral-sh/uv:0.8.24@sha256:1d31be550ff927957472b2a491dc3de1ea9b5c2d319a9cea5b6a48021e2990a6 /uv /bin/uv
USER        1001
COPY        --chown=1001:0 repos.py ./
ENV         UV_NO_CACHE=true
RUN         uv sync --frozen
RUN         uv run ruff check --no-fix -v
RUN         uv run ruff format --check
