output "kafka_cluster_id" {
  description = "Instaclustr Kafka cluster ID"
  value       = instaclustr_kafka_cluster_v2.infra_kafka.id
}

output "kafka_cluster_status" {
  description = "Current status of the Kafka cluster"
  value       = instaclustr_kafka_cluster_v2.infra_kafka.status
}

output "cassandra_cluster_id" {
  description = "Instaclustr Cassandra cluster ID"
  value       = instaclustr_cassandra_cluster_v2.infra_cassandra.id
}

output "cassandra_cluster_status" {
  description = "Current status of the Cassandra cluster"
  value       = instaclustr_cassandra_cluster_v2.infra_cassandra.status
}

output "next_steps" {
  description = "Once clusters are RUNNING, retrieve connection details from the Instaclustr console"
  value       = <<-EOT
    After 'terraform apply' completes and clusters reach RUNNING status:

    1. Open https://console2.instaclustr.com
    2. Kafka cluster '${instaclustr_kafka_cluster_v2.infra_kafka.name}':
       - Go to Connection Info to get bootstrap brokers
       - Copy KAFKA_BOOTSTRAP_SERVERS and credentials to .env

    3. Cassandra cluster '${instaclustr_cassandra_cluster_v2.infra_cassandra.name}':
       - Go to Connection Info to get contact points
       - Copy CASSANDRA_CONTACT_POINTS, username, and password to .env

    4. Run: docker-compose up --build
  EOT
}
