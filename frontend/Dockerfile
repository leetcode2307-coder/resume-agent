FROM ghcr.io/cirruslabs/flutter:stable

# Enable flutter web
RUN flutter config --enable-web

WORKDIR /app

# Copy dependency files first to cache them
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get

# Copy the rest of the app
COPY . .

# Expose port
EXPOSE 3000

# Run flutter web server
CMD ["flutter", "run", "-d", "web-server", "--web-port", "3000", "--web-hostname", "0.0.0.0"]
