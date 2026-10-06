# syntax=docker/dockerfile:1.7

# Thulpoff — skill distillation from agent sessions.
# Pure-Rust single binary (thulpoff CLI). No native deps (no protoc/openssl/
# build.rs), so the builder needs only the Rust toolchain. Stable toolchain
# (repo carries no rust-toolchain pin), matching CI.

FROM rust:1.98-bookworm AS builder

WORKDIR /app

# Dependency manifest first for layer caching; then the workspace sources.
COPY Cargo.toml Cargo.lock ./
COPY crates/ ./crates/

RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/app/target \
    cargo build --release --locked --bin thulpoff && \
    cp /app/target/release/thulpoff /tmp/thulpoff

FROM debian:bookworm-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --uid 1000 --shell /usr/sbin/nologin thulpoff

WORKDIR /app

COPY --from=builder /tmp/thulpoff /usr/local/bin/thulpoff

RUN chown -R thulpoff:thulpoff /app

USER thulpoff

ENV RUST_LOG=info

# thulpoff is a CLI (distillation runs), not a long-running server:
# no EXPOSE / HEALTHCHECK. Default to --help so a bare `docker run` is safe.
ENTRYPOINT ["thulpoff"]
CMD ["--help"]
