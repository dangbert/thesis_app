FROM node:20.11-alpine as react_common
WORKDIR /frontend
RUN yarn global add nx@latest 
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile --network-timeout 1000000 # 1000 secs
COPY ./ ./

# FROM react_common as react_dev


FROM react_common as react_build
RUN nx run frontend:build:production --skip-nx-cache


FROM nginx:1.25-alpine as nginx_prod
RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx/thesis.conf.template /etc/nginx/templates/
RUN mkdir -p /var/www/thesis
# copy production build into nginx html dir
COPY --from=react_build /frontend/dist/apps/frontend /var/www/thesis/html
CMD ["nginx", "-g", "daemon off;"]
