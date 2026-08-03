variable "bucket_name" { type = string }
variable "tags" { type = map(string) }
variable "replication_enabled" {
  type    = bool
  default = false
}
variable "replication_destination_bucket_arn" {
  type    = string
  default = ""
}
