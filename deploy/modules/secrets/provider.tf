provider "kubernetes" {
}

provider "vault" {
  address = "https://vault.corp.unity3d.com"
}

provider "google" {
  project = var.project
  region  = var.region
}
