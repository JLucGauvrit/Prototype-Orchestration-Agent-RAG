FROM nginx:alpine

WORKDIR /usr/share/nginx/html

# Création des répertoires
RUN mkdir -p styles js

# Copie des fichiers statiques
COPY . .

# Configuration nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposition du port
EXPOSE 8080

# Démarrage de nginx
CMD ["nginx", "-g", "daemon off;"]