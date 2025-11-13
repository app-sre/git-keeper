FROM        registry.access.redhat.com/ubi9/python-312@sha256:c798f775119a2e9c676fcfdb14a0d24cb562790b1a4c1bb49d0966aec039c673 AS builder
LABEL       maintainer="Serhii Kryzhnii skryzhni@redhat.com"
WORKDIR     /git-keeper
COPY        --from=ghcr.io/astral-sh/uv:0.9.9@sha256:f6e3549ed287fee0ddde2460a2a74a2d74366f84b04aaa34c1f19fec40da8652 /uv /bin/uv
COPY        --chown=1001:0 pyproject.toml uv.lock ./
RUN         uv lock --locked
COPY        --chown=1001:0 git-keeper.py ./git-keeper.py
RUN         uv sync --frozen --no-cache --compile-bytecode --no-group dev --python /usr/bin/python3.12

FROM        registry.access.redhat.com/ubi9/ubi-minimal:9.7-1762956380@sha256:53ea1f6d835898acda5becdb3f8b1292038a480384bbcf994fc0bcf1f7e8eaf7 AS prod
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
COPY        --from=ghcr.io/astral-sh/uv:0.9.9@sha256:f6e3549ed287fee0ddde2460a2a74a2d74366f84b04aaa34c1f19fec40da8652 /uv /bin/uv
USER        1001
COPY        --chown=1001:0 repos.py ./
ENV         UV_NO_CACHE=true
RUN         uv sync --frozen
RUN         uv run ruff check --no-fix -v
RUN         uv run ruff format --check
