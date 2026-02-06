terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  credentials = file(var.keyfile_location)
  region      = var.region
}

module "kubernetes" {
  source = "./modules/kubernetes-k8s-agents-machine"

  master_sa_email             = var.master_sa_email
  master_sa_scopes            = var.master_sa_scopes
  master_preemptible          = var.master_preemptible
  master_additional_disk_type = var.master_additional_disk_type
  worker_sa_email             = var.worker_sa_email
  worker_sa_scopes            = var.worker_sa_scopes
  worker_preemptible          = var.worker_preemptible
  worker_additional_disk_type = var.worker_additional_disk_type

  ssh_whitelist        = var.ssh_whitelist
  api_server_whitelist = var.api_server_whitelist
  nodeport_whitelist   = var.nodeport_whitelist
}