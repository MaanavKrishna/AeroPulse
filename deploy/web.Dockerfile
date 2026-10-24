# AeroPulse website (Next.js). Pages are prerendered from the API, so the build runs when the
# container starts, after the API is up, not when the image is built.
FROM node:22-alpine

ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /web

COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN chown -R node:node /web

USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=300s CMD wget -qO- http://127.0.0.1:3000/ >/dev/null || exit 1
CMD ["sh", "-c", "npm run build && npm start -- --port 3000"]
