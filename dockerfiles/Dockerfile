FROM        registry.access.redhat.com/ubi10/python-314-minimal@sha256:c089357da10fef8abd0ba8893b6b90a7bf9ab66253e310b76a750d9f856124cb AS builder
WORKDIR     /git-keeper
COPY        --from=ghcr.io/astral-sh/uv:0.11.27@sha256:4d01caf3b22dfd11003455e2e68153da08c4ee1fa54fdbd166c6282d22693419 /uv /bin/uv
COPY        --chown=1001:0 pyproject.toml uv.lock ./
RUN         uv lock --locked
COPY        --chown=1001:0 git-keeper.py ./git-keeper.py
RUN         uv sync --frozen --no-cache --compile-bytecode --no-group dev --python /usr/bin/python3.14

FROM        registry.access.redhat.com/ubi10/python-314-minimal@sha256:c089357da10fef8abd0ba8893b6b90a7bf9ab66253e310b76a750d9f856124cb AS prod
USER        0
RUN         microdnf upgrade -y && \
    microdnf install -y gpg git tar && \
    microdnf clean all
WORKDIR     /git-keeper
RUN         ln -s  /config/.netrc /git-keeper/.netrc
RUN         chown -R 1001:0 /git-keeper
USER        1001
ENV         HOME=/git-keeper
ENV         VIRTUAL_ENV=/git-keeper/.venv
ENV         PATH="$VIRTUAL_ENV/bin:$PATH"
COPY        --from=builder /git-keeper /git-keeper

ENTRYPOINT  ["python3", "git-keeper.py"]

FROM        prod AS test
COPY        --from=ghcr.io/astral-sh/uv:0.11.27@sha256:4d01caf3b22dfd11003455e2e68153da08c4ee1fa54fdbd166c6282d22693419 /uv /bin/uv
USER        1001
COPY        --chown=1001:0 repos.py ./
ENV         UV_NO_CACHE=true
RUN         uv sync --frozen
RUN         uv run ruff check --no-fix -v
RUN         uv run ruff format --check
RUN         git --version && tar --version && gpg --version
