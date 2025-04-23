project = "personal-ai-assistant"

# Variables for deployment configuration
variable "deployment_platform" {
  type    = string
  default = "kubernetes"  # Options: "kubernetes", "nomad"
  env     = ["WAYPOINT_DEPLOYMENT_PLATFORM"]
}

variable "registry_username" {
  type    = string
  default = ""
  env     = ["REGISTRY_USERNAME"]
  sensitive = true
}

variable "registry_password" {
  type    = string
  default = ""
  env     = ["REGISTRY_PASSWORD"]
  sensitive = true
}

variable "registry_url" {
  type    = string
  default = "docker.io"
  env     = ["REGISTRY_URL"]
}

variable "image_name" {
  type    = string
  default = "personal-ai-assistant"
  env     = ["IMAGE_NAME"]
}

variable "kubernetes_namespace" {
  type    = string
  default = "personal-assistant"
  env     = ["KUBERNETES_NAMESPACE"]
}

variable "nomad_datacenter" {
  type    = string
  default = "dc1"
  env     = ["NOMAD_DATACENTER"]
}

variable "db_volume_name" {
  type    = string
  default = "db-data"
  env     = ["DB_VOLUME_NAME"]
}

variable "whatsapp_port" {
  type    = number
  default = 5000
  env     = ["WHATSAPP_PORT"]
}

variable "enable_telegram" {
  type    = bool
  default = true
  env     = ["ENABLE_TELEGRAM"]
}

variable "enable_whatsapp" {
  type    = bool
  default = true
  env     = ["ENABLE_WHATSAPP"]
}

variable "cpu_request" {
  type    = string
  default = "200m"
  env     = ["CPU_REQUEST"]
}

variable "memory_request" {
  type    = string
  default = "256Mi"
  env     = ["MEMORY_REQUEST"]
}

variable "cpu_limit" {
  type    = string
  default = "500m"
  env     = ["CPU_LIMIT"]
}

variable "memory_limit" {
  type    = string
  default = "512Mi"
  env     = ["MEMORY_LIMIT"]
}

# Common build configuration for both bots
app "common" {
  build {
    use "docker" {
      buildkit    = true
      dockerfile  = "${path.app}/Dockerfile"
      disable_entrypoint = true
    }
    
    registry {
      use "docker" {
        image    = "${var.registry_url}/${var.registry_username}/${var.image_name}"
        tag      = gitrefpretty()
        username = var.registry_username
        password = var.registry_password
        local    = false
      }
    }
  }
}

# Telegram Bot Application
app "telegram-bot" {
  build {
    use "docker" {
      buildkit    = true
      dockerfile  = "${path.app}/Dockerfile"
      disable_entrypoint = true
    }
    
    registry {
      use "docker" {
        image    = "${var.registry_url}/${var.registry_username}/${var.image_name}"
        tag      = "telegram-${gitrefpretty()}"
        username = var.registry_username
        password = var.registry_password
        local    = false
      }
    }
  }

  # Kubernetes Deployment
  deploy {
    use "kubernetes" {
      probe_path = "/"
      
      namespace = var.kubernetes_namespace
      
      service_port = 80
      
      pod {
        container {
          name  = "telegram-bot"
          image = artifact.image
          
          args = ["telegram"]
          
          port {
            name = "http"
            port = 80
          }
          
          resources {
            cpu {
              request = var.cpu_request
              limit   = var.cpu_limit
            }
            memory {
              request = var.memory_request
              limit   = var.memory_limit
            }
          }
          
          volume {
            name      = "db-volume"
            path      = "/app/db"
            read_only = false
          }
          
          env {
            name  = "DEPLOYMENT_PLATFORM"
            value = "kubernetes"
          }
          
          # Add secret env vars from Kubernetes secrets
          secret {
            name = "personal-assistant-secrets"
            key  = "OPENAI_API_KEY"
            env  = "OPENAI_API_KEY"
          }
          
          secret {
            name = "personal-assistant-secrets"
            key  = "TELEGRAM_TOKEN"
            env  = "TELEGRAM_TOKEN"
          }
          
          secret {
            name = "personal-assistant-secrets"
            key  = "CHAT_ID"
            env  = "CHAT_ID"
          }
          
          # Add more secrets as needed
        }
        
        volume {
          name = "db-volume"
          persistent_volume_claim {
            name = var.db_volume_name
          }
        }
        
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/path"   = "/metrics"
          "prometheus.io/port"   = "80"
        }
      }
    }
  }

  # Nomad Deployment
  deploy {
    use "nomad" {
      // Only use this deploy block when the deployment_platform is nomad
      static_environment = {
        DEPLOYMENT_PLATFORM = "nomad"
      }
      
      job {
        datacenters = [var.nomad_datacenter]
        type        = "service"
        
        group "telegram" {
          count = 1
          
          volume "db-volume" {
            type      = "host"
            read_only = false
            source    = var.db_volume_name
          }
          
          task "app" {
            driver = "docker"
            
            config {
              image = artifact.image
              args  = ["telegram"]
            }
            
            resources {
              cpu    = 500
              memory = 512
            }
            
            volume_mount {
              volume      = "db-volume"
              destination = "/app/db"
              read_only   = false
            }
            
            vault {
              policies = ["personal-assistant"]
            }
            
            template {
              data = <<EOH
{{ with secret "secret/personal-assistant" }}
OPENAI_API_KEY={{ .Data.openai_api_key }}
TELEGRAM_TOKEN={{ .Data.telegram_token }}
CHAT_ID={{ .Data.chat_id }}
# Add more environment variables as needed
{{ end }}
EOH
              destination = "secrets/.env"
              env         = true
            }
          }
        }
      }
    }
  }
}

# WhatsApp Bot Application
app "whatsapp-bot" {
  build {
    use "docker" {
      buildkit    = true
      dockerfile  = "${path.app}/Dockerfile"
      disable_entrypoint = true
    }
    
    registry {
      use "docker" {
        image    = "${var.registry_url}/${var.registry_username}/${var.image_name}"
        tag      = "whatsapp-${gitrefpretty()}"
        username = var.registry_username
        password = var.registry_password
        local    = false
      }
    }
  }

  # Kubernetes Deployment
  deploy {
    use "kubernetes" {
      probe_path = "/health"
      
      namespace = var.kubernetes_namespace
      
      service_port = var.whatsapp_port
      
      pod {
        container {
          name  = "whatsapp-bot"
          image = artifact.image
          
          args = ["whatsapp"]
          
          port {
            name = "http"
            port = var.whatsapp_port
          }
          
          resources {
            cpu {
              request = var.cpu_request
              limit   = var.cpu_limit
            }
            memory {
              request = var.memory_request
              limit   = var.memory_limit
            }
          }
          
          volume {
            name      = "db-volume"
            path      = "/app/db"
            read_only = false
          }
          
          env {
            name  = "DEPLOYMENT_PLATFORM"
            value = "kubernetes"
          }
          
          # Add secret env vars from Kubernetes secrets
          secret {
            name = "personal-assistant-secrets"
            key  = "OPENAI_API_KEY"
            env  = "OPENAI_API_KEY"
          }
          
          secret {
            name = "personal-assistant-secrets"
            key  = "TWILIO_ACCOUNT_SID"
            env  = "TWILIO_ACCOUNT_SID"
          }
          
          secret {
            name = "personal-assistant-secrets"
            key  = "TWILIO_AUTH_TOKEN"
            env  = "TWILIO_AUTH_TOKEN"
          }
          
          secret {
            name = "personal-assistant-secrets"
            key  = "FROM_WHATSAPP_NUMBER"
            env  = "FROM_WHATSAPP_NUMBER"
          }
          
          # Add more secrets as needed
          
          health_check {
            http {
              path = "/health"
              port = var.whatsapp_port
            }
            initial_delay = 5
            period        = 10
          }
        }
        
        volume {
          name = "db-volume"
          persistent_volume_claim {
            name = var.db_volume_name
          }
        }
        
        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/path"   = "/metrics"
          "prometheus.io/port"   = "${var.whatsapp_port}"
        }
      }
    }
  }

  # Nomad Deployment
  deploy {
    use "nomad" {
      // Only use this deploy block when the deployment_platform is nomad
      static_environment = {
        DEPLOYMENT_PLATFORM = "nomad"
      }
      
      job {
        datacenters = [var.nomad_datacenter]
        type        = "service"
        
        group "whatsapp" {
          count = 1
          
          volume "db-volume" {
            type      = "host"
            read_only = false
            source    = var.db_volume_name
          }
          
          task "app" {
            driver = "docker"
            
            config {
              image = artifact.image
              args  = ["whatsapp"]
              ports = ["http"]
            }
            
            resources {
              cpu    = 500
              memory = 512
            }
            
            volume_mount {
              volume      = "db-volume"
              destination = "/app/db"
              read_only   = false
            }
            
            vault {
              policies = ["personal-assistant"]
            }
            
            template {
              data = <<EOH
{{ with secret "secret/personal-assistant" }}
OPENAI_API_KEY={{ .Data.openai_api_key }}
TWILIO_ACCOUNT_SID={{ .Data.twilio_account_sid }}
TWILIO_AUTH_TOKEN={{ .Data.twilio_auth_token }}
FROM_WHATSAPP_NUMBER={{ .Data.from_whatsapp_number }}
# Add more environment variables as needed
{{ end }}
EOH
              destination = "secrets/.env"
              env         = true
            }
            
            service {
              name = "whatsapp-bot"
              port = "http"
              
              check {
                type     = "http"
                path     = "/health"
                interval = "10s"
                timeout  = "2s"
              }
              
              tags = [
                "traefik.enable=true",
                "traefik.http.routers.whatsapp.rule=Host(`whatsapp.yourdomain.com`)",
                "traefik.http.routers.whatsapp.tls=true"
              ]
            }
          }
          
          network {
            port "http" {
              static = var.whatsapp_port
              to     = var.whatsapp_port
            }
          }
        }
      }
    }
  }

  # Release configuration for WhatsApp bot
  release {
    use "kubernetes" {
      namespace = var.kubernetes_namespace
      
      ingress {
        class_name = "nginx"
        
        tls {
          hosts       = ["whatsapp.yourdomain.com"]
          secret_name = "whatsapp-tls"
        }
        
        rule {
          host = "whatsapp.yourdomain.com"
          path {
            path     = "/"
            path_type = "Prefix"
          }
        }
      }
    }
  }
}

# Observability Application (Prometheus, Grafana, etc.)
app "observability" {
  build {
    use "null" {}
  }
  
  deploy {
    use "kubernetes" {
      namespace = var.kubernetes_namespace
      
      helm {
        chart     = "kube-prometheus-stack"
        repo      = "https://prometheus-community.github.io/helm-charts"
        version   = "45.7.1"
        
        values = {
          grafana = {
            adminPassword = "admin"
            persistence = {
              enabled = true
              size    = "5Gi"
            }
          }
          prometheus = {
            prometheusSpec = {
              retention     = "15d"
              storageSpec = {
                volumeClaimTemplate = {
                  spec = {
                    storageClassName = "standard"
                    accessModes      = ["ReadWriteOnce"]
                    resources = {
                      requests = {
                        storage = "50Gi"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

# Database Migration Application
app "db-migrations" {
  build {
    use "docker" {
      buildkit    = true
      dockerfile  = "${path.app}/Dockerfile"
      disable_entrypoint = true
    }
    
    registry {
      use "docker" {
        image    = "${var.registry_url}/${var.registry_username}/${var.image_name}"
        tag      = "migrations-${gitrefpretty()}"
        username = var.registry_username
        password = var.registry_password
        local    = false
      }
    }
  }
  
  deploy {
    use "kubernetes" {
      namespace = var.kubernetes_namespace
      
      job {
        name     = "db-migrations"
        image    = artifact.image
        command  = ["python", "migrations.py"]
        
        volume {
          name      = "db-volume"
          path      = "/app/db"
          read_only = false
        }
        
        volume {
          name = "db-volume"
          persistent_volume_claim {
            name = var.db_volume_name
          }
        }
        
        restart_policy {
          policy = "OnFailure"
          limit  = 3
        }
        
        # Add secret env vars from Kubernetes secrets
        secret {
          name = "personal-assistant-secrets"
          key  = "OPENAI_API_KEY"
          env  = "OPENAI_API_KEY"
        }
        
        # Add more secrets as needed
      }
    }
  }
}

# Backup Application
app "backup" {
  build {
    use "null" {}
  }
  
  deploy {
    use "kubernetes" {
      namespace = var.kubernetes_namespace
      
      cron_job {
        name            = "db-backup"
        image           = "bitnami/kubectl:latest"
        schedule        = "0 1 * * *"  # Daily at 1 AM
        concurrency_policy = "Forbid"
        
        command = [
          "/bin/sh",
          "-c",
          "kubectl -n ${var.kubernetes_namespace} exec -it $(kubectl -n ${var.kubernetes_namespace} get pods -l app=telegram-bot -o jsonpath='{.items[0].metadata.name}') -- tar -czf - /app/db | aws s3 cp - s3://your-backup-bucket/personal-assistant/$(date +%Y-%m-%d).tar.gz"
        ]
        
        restart_policy {
          policy = "OnFailure"
          limit  = 3
        }
        
        # Add AWS credentials as environment variables
        secret {
          name = "aws-credentials"
          key  = "AWS_ACCESS_KEY_ID"
          env  = "AWS_ACCESS_KEY_ID"
        }
        
        secret {
          name = "aws-credentials"
          key  = "AWS_SECRET_ACCESS_KEY"
          env  = "AWS_SECRET_ACCESS_KEY"
        }
        
        secret {
          name = "aws-credentials"
          key  = "AWS_REGION"
          env  = "AWS_REGION"
        }
      }
    }
  }
}

# Waypoint Runner Configuration
runner {
  enabled = true
  
  data_source "git" {
    url = "https://github.com/yourusername/personal-ai-assistant.git"
  }
}