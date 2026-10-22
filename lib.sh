#!/usr/bin/env bash
# Shared helpers. Not run directly.
set -uo pipefail
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$KIT_DIR"
source ./config.env
export AWS_DEFAULT_REGION="$REGION" AWS_PAGER=""
mkdir -p evidence screenshots
touch ids.env
source ./ids.env

save() { sed -i.bak "/^$1=/d" ids.env; rm -f ids.env.bak; echo "$1=\"$2\"" >> ids.env; eval "$1=\"$2\""; }

# Tag spec used on every resource: Name + Project + Student
ts() { echo "ResourceType=$1,Tags=[{Key=Name,Value=$2},{Key=Project,Value=EWB-VPC-Peering},{Key=Student,Value=$STUDENT}]"; }

stamp() { echo "# $1"; echo "# Run at : $(date '+%Y-%m-%d %H:%M:%S %Z')"; echo "# Region : $REGION"; echo; }

need_aws() {
  command -v aws >/dev/null || { echo "ERROR: AWS CLI not installed. See README step 1."; exit 1; }
  aws sts get-caller-identity >/dev/null 2>&1 || { echo "ERROR: AWS CLI not logged in. Run: aws configure   (see README step 1)"; exit 1; }
  if [ "$STUDENT" = "Your Name" ]; then echo "ERROR: Edit config.env and put your real name first."; exit 1; fi
}
