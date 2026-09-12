# Use an official lightweight Ubuntu base image
FROM ubuntu:22.04

# Avoid prompts during apt installation
ENV DEBIAN_FRONTEND=noninteractive

# Update apt and install TeX Live and required fonts
RUN apt-get update && apt-get install -y \
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Set default working directory
WORKDIR /home/user
