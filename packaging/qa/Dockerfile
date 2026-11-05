ARG BASE=debian@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2
FROM ${BASE}
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends libgtk-3-0 libdbus-glib-1-2 libxt6 libasound2t64 libx11-xcb1 libxcb-shm0 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libglib2.0-0t64 libnss3 libnspr4 libstdc++6 libgcc-s1 libfontconfig1 fonts-dejavu-core ca-certificates python3 libnss3-tools xz-utils && rm -rf /var/lib/apt/lists/*
RUN if ! getent passwd 1000 >/dev/null; then useradd --uid 1000 --create-home aelthoren-test; fi
USER 1000:1000
WORKDIR /tmp
