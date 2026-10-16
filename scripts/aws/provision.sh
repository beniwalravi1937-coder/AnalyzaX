#!/usr/bin/env bash
# ==============================================================================
# AnalyzaX — Provision a single EC2 host for docker-compose.prod.yml
#
# Creates (idempotently, by name/tag):
#   - EC2 key pair "analyzax-prod"  -> private key saved to ~/.ssh/analyzax-prod.pem
#   - Security group "analyzax-prod-sg": SSH (22) from your current IP only,
#     HTTP (80) and HTTPS (443) from anywhere
#   - Ubuntu 24.04 t3.medium instance tagged Name=analyzax-prod, 40 GB gp3 disk
#   - Elastic IP associated with the instance (stable public address)
#
# Usage:  scripts/aws/provision.sh                (defaults to ap-south-1)
#         ANALYZAX_REGION=us-east-1 scripts/aws/provision.sh
# Requires: AWS CLI v2 with credentials (aws configure, aws login, or CloudShell).
# Note: AWS_REGION is deliberately not used — CloudShell sets it to whatever
# region the console happens to be showing.
# ==============================================================================
set -euo pipefail

REGION="${ANALYZAX_REGION:-ap-south-1}"
NAME="analyzax-prod"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.medium}"
KEY_FILE="$HOME/.ssh/${NAME}.pem"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$SCRIPT_DIR/.instance"

aws_() { aws --region "$REGION" --output text "$@"; }

echo "==> Region: $REGION"
aws_ sts get-caller-identity --query Account >/dev/null

# --- Key pair -----------------------------------------------------------------
if aws_ ec2 describe-key-pairs --key-names "$NAME" >/dev/null 2>&1; then
  echo "==> Key pair $NAME exists"
  [ -f "$KEY_FILE" ] || { echo "ERROR: key pair exists in AWS but $KEY_FILE is missing." >&2; exit 1; }
else
  echo "==> Creating key pair $NAME -> $KEY_FILE"
  mkdir -p "$HOME/.ssh"
  aws_ ec2 create-key-pair --key-name "$NAME" --key-type ed25519 \
    --query KeyMaterial > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
fi

# --- Security group -----------------------------------------------------------
VPC_ID=$(aws_ ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId')
SG_ID=$(aws_ ec2 describe-security-groups \
  --filters Name=group-name,Values="${NAME}-sg" Name=vpc-id,Values="$VPC_ID" \
  --query 'SecurityGroups[0].GroupId')
if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  echo "==> Creating security group ${NAME}-sg"
  SG_ID=$(aws_ ec2 create-security-group --group-name "${NAME}-sg" \
    --description "AnalyzaX production web host" --vpc-id "$VPC_ID" --query GroupId)
  aws_ ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 80 --cidr 0.0.0.0/0 >/dev/null
  aws_ ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 443 --cidr 0.0.0.0/0 >/dev/null
fi
MY_IP=$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')
aws_ ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 \
  --cidr "${MY_IP}/32" >/dev/null 2>&1 || true
echo "==> Security group $SG_ID (SSH allowed from ${MY_IP})"

# --- Instance -----------------------------------------------------------------
INSTANCE_ID=$(aws_ ec2 describe-instances \
  --filters Name=tag:Name,Values="$NAME" Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[0].Instances[0].InstanceId')
if [ "$INSTANCE_ID" = "None" ] || [ -z "$INSTANCE_ID" ]; then
  AMI_ID=$(aws_ ssm get-parameter \
    --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
    --query Parameter.Value)
  echo "==> Launching $INSTANCE_TYPE from $AMI_ID"
  INSTANCE_ID=$(aws_ ec2 run-instances \
    --image-id "$AMI_ID" --instance-type "$INSTANCE_TYPE" \
    --key-name "$NAME" --security-group-ids "$SG_ID" \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3,DeleteOnTermination=true}' \
    --metadata-options HttpTokens=required \
    --user-data "file://$SCRIPT_DIR/user-data.sh" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=app,Value=analyzax}]" \
    --query 'Instances[0].InstanceId')
else
  echo "==> Instance $INSTANCE_ID exists"
  aws_ ec2 start-instances --instance-ids "$INSTANCE_ID" >/dev/null 2>&1 || true
fi
aws_ ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# --- Elastic IP ---------------------------------------------------------------
ALLOC_ID=$(aws_ ec2 describe-addresses --filters Name=tag:Name,Values="$NAME" \
  --query 'Addresses[0].AllocationId')
if [ "$ALLOC_ID" = "None" ] || [ -z "$ALLOC_ID" ]; then
  ALLOC_ID=$(aws_ ec2 allocate-address --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$NAME}]" \
    --query AllocationId)
fi
aws_ ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID" >/dev/null
PUBLIC_IP=$(aws_ ec2 describe-addresses --allocation-ids "$ALLOC_ID" --query 'Addresses[0].PublicIp')

printf 'REGION=%s\nINSTANCE_ID=%s\nPUBLIC_IP=%s\nKEY_FILE=%s\n' \
  "$REGION" "$INSTANCE_ID" "$PUBLIC_IP" "$KEY_FILE" > "$STATE_FILE"

echo "==> Ready: $INSTANCE_ID at $PUBLIC_IP (details in $STATE_FILE)"
echo "    First boot installs Docker; allow ~2-3 minutes before deploying."
