FROM node:20-alpine

# Set the working directory in the container
WORKDIR /app

COPY . .

# Install any dependencies
RUN npm ci

CMD ["npx", "ts-node", "tasks/e2eCron.ts"]
