FROM node:22-alpine
RUN apk add --no-cache build-base python3
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 1337
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=1337
ENV APP_KEYS=key1,key2,key3,key4
ENV API_TOKEN_SALT=tokensalt123
ENV ADMIN_JWT_SECRET=adminjwt123
ENV JWT_SECRET=jwt123
ENV TRANSFER_TOKEN_SALT=transfer123
CMD ["npm", "run", "start"]
