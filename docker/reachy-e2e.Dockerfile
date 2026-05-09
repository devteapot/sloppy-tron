FROM python:3.12-bookworm

ARG REACHY_MINI_SPEC="reachy_mini[mujoco]==1.7.1"
ARG BUN_VERSION=1.3.11

ENV DEBIAN_FRONTEND=noninteractive \
    BUN_INSTALL=/root/.bun \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_PROJECT_ENVIRONMENT=/tmp/sloppy-tron-venv \
    UV_LINK_MODE=copy \
    MUJOCO_GL=osmesa \
    PYOPENGL_PLATFORM=osmesa \
    PATH=/root/.bun/bin:$PATH

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    gir1.2-gst-plugins-base-1.0 \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-tools \
    libasound2 \
    libcairo2-dev \
    libdbus-1-dev \
    libegl1 \
    libffi-dev \
    libgl1 \
    libglew2.2 \
    libglib2.0-dev \
    libglfw3 \
    libgirepository1.0-dev \
    libosmesa6 \
    libpulse0 \
    libusb-1.0-0 \
    libx11-6 \
    pkg-config \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://bun.sh/install | bash -s "bun-v${BUN_VERSION}"

RUN python -m pip install --upgrade pip uv \
  && python -m pip install "${REACHY_MINI_SPEC}"

WORKDIR /workspace
CMD ["bash"]
