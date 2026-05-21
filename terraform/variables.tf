variable "instaclustr_username" {
  description = "Instaclustr account username (email address)"
  type        = string
  sensitive   = true
}

variable "instaclustr_api_key" {
  description = "Instaclustr Provisioning API key"
  type        = string
  sensitive   = true
}

variable "cloud_provider" {
  description = "Cloud provider for cluster nodes"
  type        = string
  default     = "AWS_VPC"
}

variable "region" {
  description = "Cloud region for cluster deployment"
  type        = string
  default     = "US_EAST_1"
}

variable "network_cidr" {
  description = "VPC network CIDR for cluster nodes"
  type        = string
  default     = "10.0.0.0/16"
}

variable "project_name" {
  description = "Prefix applied to all provisioned cluster names"
  type        = string
  default     = "infra-monitor"
}
