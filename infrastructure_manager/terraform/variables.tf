variable "server_count" {
  description = "Number of backend servers to run"
  type        = number
  default     = 3
}

variable "base_port" {
  description = "Starting port number for servers"
  type        = number
  default     = 8001
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}
