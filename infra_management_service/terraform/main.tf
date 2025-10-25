terraform {
	required_providers {
		docker = {
			source  = "kreuzwerker/docker"
			version = "~> 3.0.2"
		}
	}
}

provider "docker" {
	host = "unix:///var/run/docker.sock"
}

# Build the FastAPI Docker image
resource "docker_image" "fastapi_app" {
	name = "fastapi-terraform-app:latest"
	build {
		context    = "../app"
		dockerfile = "Dockerfile"
		tag        = ["fastapi-terraform-app:latest"]
		label = {
			author      = "terraform"
			environment = var.environment
		}
	}
	keep_locally = true
}

# Create a custom network
resource "docker_network" "app_network" {
	name   = "fastapi_demo_network"
	driver = "bridge"

	labels {
		label = "environment"
		value = var.environment
	}
}

# Create multiple FastAPI containers dynamically using count
resource "docker_container" "fastapi_backends" {
	count = var.server_count

	name  = "fastapi-server-${count.index + 1}"
	image = docker_image.fastapi_app.name

	ports {
		internal = 8000
		external = var.base_port + count.index
	}

	networks_advanced {
		name = docker_network.app_network.name
	}

	env = [
		"SERVER_ID=server-${count.index + 1}",
		"SERVER_PORT=${var.base_port + count.index}",
		"ENVIRONMENT=${var.environment}",
		"MANAGED_BY=terraform"
	]

	restart = "unless-stopped"

	labels {
		label = "app"
		value = "fastapi-demo"
	}

	labels {
		label = "server_id"
		value = "server-${count.index + 1}"
	}

	labels {
		label = "provisioned_by"
		value = "terraform"
	}

	# Prevent unnecessary recreation
	lifecycle {
		ignore_changes = [
			image,
			network_mode,
			working_dir,
			command,
			entrypoint,
		]
	}
}

# Outputs
output "server_count" {
	value       = var.server_count
	description = "Total number of servers running"
}

output "backend_servers" {
	value = [
		for i in range(var.server_count) : {
			name = "fastapi-server-${i + 1}"
			port = var.base_port + i
			url  = "http://localhost:${var.base_port + i}"
		}
	]
	description = "List of all backend servers"
}

output "port_range" {
	value       = "${var.base_port} - ${var.base_port + var.server_count - 1}"
	description = "Port range used by servers"
}

output "network_name" {
	value       = docker_network.app_network.name
	description = "Docker network name"
}
