terraform {
  source = "${get_parent_terragrunt_dir()}/../modules/${path_relative_to_include()}"
}

include {
  path = find_in_parent_folders()
}
