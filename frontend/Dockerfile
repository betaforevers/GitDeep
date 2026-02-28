FROM nginx:alpine

# Copy static frontend files to nginx default html directory
COPY . /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
