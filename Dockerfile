# syntax=docker/dockerfile:1
FROM node:22-alpine

LABEL org.opencontainers.image.title="Hong Kong Company MCP Server" \
      org.opencontainers.image.description="Hong Kong Company MCP Server (com.86hc/hongkong-company) - Search 3.9M+ HK companies (CR No, BRN, UBO) & order ICRIS filings via Stripe." \
      org.opencontainers.image.url="https://www.86hc.com" \
      org.opencontainers.image.documentation="https://www.86hc.com/mcp" \
      org.opencontainers.image.source="https://github.com/86hc-compliance/hongkong-company-mcp" \
      org.opencontainers.image.vendor="HC Business (恒诚商务)" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# 仅拷贝必需的运行文件（零 npm 外部依赖，体积仅 ~45MB）
COPY package.json index.js README.md LICENSE ./

# 非 root 用户运行，确保金融级容器安全
USER node

ENV NODE_ENV=production

ENTRYPOINT ["node", "index.js"]
