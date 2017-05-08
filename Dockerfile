FROM node:6.4

WORKDIR /app
COPY ./package.json /app/package.json
RUN npm install --warn

COPY ./ /app

ENTRYPOINT ["/app/entrypoint.sh"]
