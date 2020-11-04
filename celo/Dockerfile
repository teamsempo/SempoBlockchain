# node:alpine will be our base image to create this image
FROM node:12-alpine
# Set the /app directory as working directory
# Install ganache-cli globally
RUN npm i -g @celo/ganache-cli
EXPOSE 8545


ENTRYPOINT ["ganache-cli"]

