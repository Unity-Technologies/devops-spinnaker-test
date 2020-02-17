variable "project" {
  type        = string
  description = "Project ID to use."
}

variable "env" {
  type        = string
  description = "The environment where we are deploying."
}

variable "vault_base_path" {
  type        = string
  description = "The base path of the vault secret."
  default     = "secret/common-devops"
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace where we will deploy the container"
  default     = "devops-monitoring"
}
