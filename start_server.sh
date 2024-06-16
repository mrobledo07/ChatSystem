#!/bin/bash

# Function to configure Redis
configure_redis() {
    sudo sed -i 's/^bind .*$/bind 0.0.0.0 ::1/' /etc/redis/redis.conf   # Allow connections from all interfaces
    sudo sed -i 's/^protected-mode .*$/protected-mode no/' /etc/redis/redis.conf  # Disable protected mode
    sudo systemctl restart redis
}

# Function to install Redis
install_redis() {
    sudo apt-get update
    sudo apt-get install -y redis
    if [ $? -eq 0 ]; then
        echo "Redis installed successfully."
        start_redis
        configure_redis
    else
        echo "Failed to install Redis."
        exit 1
    fi
}

# Function to start Redis
start_redis() {
    redis-server --daemonize yes
    if [ $? -eq 0 ]; then
        echo "Redis started successfully."
    else
        echo "Failed to start Redis."
        exit 1
    fi
}

# Function to check if Redis is installed and running
check_redis() {
    redis-server --version > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Redis is installed."
        redis-cli ping > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            echo "Redis is running."
        else
            echo "Redis is installed but not running. Configuring and starting Redis..."
            configure_redis
            start_redis
        fi
    else
        echo "Redis is not installed. Installing Redis..."
        install_redis
    fi
}

# Function to install Docker
install_docker() {
    sudo curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    if [ $? -eq 0 ]; then
        echo "Docker installed successfully."
    else
        echo "Failed to install Docker."
        exit 1
    fi
}

# Function to check if Docker is installed and running
check_docker() {
    docker --version > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Docker is installed."
    else
        echo "Docker is not installed. Installing Docker..."
        install_docker
    fi
}

# Function to stop RabbitMQ container if running
stop_rabbitmq() {
    if [ $(sudo docker ps -q -f name=rabbitmq) ]; then
        echo "Stopping RabbitMQ container..."
        sudo docker stop rabbitmq
    fi
}

# Function to start RabbitMQ container if not running
start_rabbitmq() {
    if [ $(sudo docker ps -a -q -f name=rabbitmq) ]; then
        echo "Starting existing RabbitMQ container..."
        sudo docker start rabbitmq
    else
        echo "Installing and starting new RabbitMQ container..."
        sudo docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
        if [ $? -eq 0 ]; then
            echo "RabbitMQ installed and started successfully."
        else
            echo "Failed to install and start RabbitMQ."
            exit 1
        fi
    fi
}

# Trap to stop RabbitMQ container on script exit
trap stop_rabbitmq EXIT

check_redis
check_docker
stop_rabbitmq  # Ensure any existing RabbitMQ container is stopped
start_rabbitmq

python3 server_daemon.py