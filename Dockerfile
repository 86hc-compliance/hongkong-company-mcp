# syntax=docker/dockerfile:1
# -----------------------------------------------------------------------------
# Hong Kong Company MCP Server (com.86hc/hongkong-company)
# Official Docker Container Image for 86hc.com (HC Business / 恒诚商务)
# Licensed TCSP: TC006431 | CR No.: 2442486 | BRN: 66820292
# -----------------------------------------------------------------------------

FROM node:22-alpine

# Set OpenContainers metadata for Docker Hub discovery and attribution
LABEL org.opencontainers.image.title="Hong Kong Company MCP Server" \
      org.opencontainers.image.description="Hong Kong Company MCP Server (com.86hc/hongkong-company) - Search 3.9M+ HK companies (CR No, BRN, UBO) & order ICRIS filings via Stripe." \
      org.opencontainers.image.url="https://www.86hc.com" \
      org.opencontainers.image.documentation="https://www.86hc.com/mcp" \
      org.opencontainers.image.source="https://github.com/86hc-compliance/hongkong-company-mcp" \
      org.opencontainers.image.vendor="HC Business (恒诚商务)" \
      org.opencontainers.image.licenses="MIT"

# Set non-root working directory
WORKDIR /app

# Copy essential runtime files (zero external npm dependencies required)
COPY package.json index.js README.md LICENSE ./

# Run as built-in non-root user (node) for enterprise container security
USER node

# Production environment flag
ENV NODE_ENV=production

# Stdio JSON-RPC protocol entrypoint
ENTRYPOINT ["node", "index.js"]
