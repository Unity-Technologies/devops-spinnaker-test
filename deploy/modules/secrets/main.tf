data "vault_generic_secret" "secrets" {
  path = "${var.vault_base_path}/${var.env}/prometheus-rules-exporter/inventory-token"
}

resource "kubernetes_secret" "config" {
  metadata {
    name      = "prometheus-rules-exporter-secrets"
    namespace = var.namespace
  }

  data = data.vault_generic_secret.secrets.data
}
