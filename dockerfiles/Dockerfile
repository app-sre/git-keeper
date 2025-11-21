FROM        registry.access.redhat.com/ubi9/python-312@sha256:e151f5a3319d75dec2a7d57241ba7bb75f1b09bc3f7092d7615ea9c5aedb114c AS builder
LABEL       maintainer="Serhii Kryzhnii skryzhni@redhat.com"
WORKDIR     /git-keeper
COPY        --from=ghcr.io/astral-sh/uv:0.9.11@sha256:5aa820129de0a600924f166aec9cb51613b15b68f1dcd2a02f31a500d2ede568 /uv /bin/uv
COPY        --chown=1001:0 pyproject.toml uv.lock ./
RUN         uv lock --locked
COPY        --chown=1001:0 git-keeper.py ./git-keeper.py
RUN         uv sync --frozen --no-cache --compile-bytecode --no-group dev --python /usr/bin/python3.12

FROM        registry.access.redhat.com/ubi9/ubi-minimal:9.7-1763362218@sha256:61d5ad475048c2e655cd46d0a55dfeaec182cc3faa6348cb85989a7c9e196483 AS prod
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
COPY        --from=ghcr.io/astral-sh/uv:0.9.11@sha256:5aa820129de0a600924f166aec9cb51613b15b68f1dcd2a02f31a500d2ede568 /uv /bin/uv
USER        1001
COPY        --chown=1001:0 repos.py ./
ENV         UV_NO_CACHE=true
RUN         uv sync --frozen
RUN         uv run ruff check --no-fix -v
RUN         uv run ruff format --check
