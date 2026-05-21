# Instaclustr Managed Infrastructure
#
# Provider: instaclustr/instaclustr v2
# Docs: https://registry.terraform.io/providers/instaclustr/instaclustr/latest/docs
#
# Authentication: terraform_key = "Instaclustr-Terraform <username>:<api_key>"
# Obtain your Provisioning API key from: https://console2.instaclustr.com/account/api-keys

terraform {
  required_version = ">= 1.3"

  required_providers {
    instaclustr = {
      source  = "instaclustr/instaclustr"
      version = ">= 2.0.0, < 3.0.0"
    }
  }
}

provider "instaclustr" {
  terraform_key = "Instaclustr-Terraform ${var.instaclustr_username}:${var.instaclustr_api_key}"
}

# ── Kafka Cluster ───────────────────────────────────────────────────────────────
# NON_PRODUCTION SLA tier is used for the PoC to reduce cost.
# Kafka 3.9.1 uses KRaft (no separate Zookeeper nodes needed).
# Node size KFK-DEV-t4g.small-30 is the smallest available developer node for AWS_VPC.

resource "instaclustr_kafka_cluster_v2" "infra_kafka" {
  name = "${var.project_name}-kafka"

  kafka_version             = "3.9.1"
  sla_tier                  = "NON_PRODUCTION"
  auto_create_topics        = true
  allow_delete_topics       = true
  client_to_cluster_encryption = false
  default_replication_factor   = 3
  default_number_of_partitions = 3
  private_network_cluster  = false
  pci_compliance_mode      = false

  data_centre {
    cloud_provider   = var.cloud_provider
    name             = "${var.cloud_provider}_${var.region}"
    network          = var.network_cidr
    node_size        = "KFK-DEV-t4g.small-30"
    number_of_nodes  = 3
    region           = var.region
  }
}

# ── Cassandra Cluster ───────────────────────────────────────────────────────────
# Cassandra 4.1.9, single data centre, NON_PRODUCTION.
# Keyspace and tables are created by the consumer app on startup via CQL DDL
# (CREATE IF NOT EXISTS) so schema evolution stays in application code.

resource "instaclustr_cassandra_cluster_v2" "infra_cassandra" {
  name = "${var.project_name}-cassandra"

  cassandra_version       = "4.1.9"
  sla_tier                = "NON_PRODUCTION"
  lucene_enabled          = false
  password_and_user_auth  = true
  private_network_cluster = false
  pci_compliance_mode     = false

  data_centre {
    cloud_provider                    = var.cloud_provider
    name                              = "${var.cloud_provider}_${var.region}"
    network                           = "10.1.0.0/16"
    node_size                         = "CAS-DEV-t4g.medium-30"
    number_of_nodes                   = 3
    replication_factor                = 3
    region                            = var.region
    client_to_cluster_encryption      = false
    continuous_backup                 = false
    private_ip_broadcast_for_discovery = false
  }
}
