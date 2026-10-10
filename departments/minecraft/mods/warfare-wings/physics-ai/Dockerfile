# Headless source verification only. No Minecraft, Forge, or mod JARs enter this image.
FROM node:22.16.0-bookworm-slim@sha256:048ed02c5fd52e86fda6fbd2f6a76cf0d4492fd6c6fee9e2c463ed5108da0e34

ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk-headless python3 \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${TARGETARCH} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/physics-ai

# This positive allowlist excludes runtime-probe and user-owned local game artifacts.
COPY --chown=node:node check-microkernel.mjs ./
COPY --chown=node:node src/ src/
COPY --chown=node:node tools/ tools/
COPY --chown=node:node data/ data/
COPY --chown=node:node reports/ reports/

USER node
CMD ["python3", "tools/verify_headless.py"]
