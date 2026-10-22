#!/usr/bin/env bash
# Creates VPC A, VPC B, subnets, IGW, route tables, security groups, key pair, 3 EC2 instances.
# Does NOT create peering yet (so you can capture the baseline failure first).
source "$(dirname "$0")/lib.sh"; need_aws
set -e
[ -n "${VPC_A:-}" ] && { echo "Already deployed (ids.env has VPC_A). Run 99-cleanup.sh first to start over."; exit 1; }

MY_IP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
[[ "$MY_IP" =~ ^[0-9.]+$ ]] || { echo "Could not detect your public IP."; exit 1; }
save MY_IP "$MY_IP"
AZ="${REGION}a"
echo "==> Your public IP: $MY_IP  | AZ: $AZ"

echo "==> VPC A"
save VPC_A "$(aws ec2 create-vpc --cidr-block 10.10.0.0/16 --tag-specifications "$(ts vpc ewb-vpc-a)" --query Vpc.VpcId --output text)"
save SUBNET_A_PUB  "$(aws ec2 create-subnet --vpc-id $VPC_A --cidr-block 10.10.1.0/24 --availability-zone $AZ --tag-specifications "$(ts subnet ewb-a-public)"  --query Subnet.SubnetId --output text)"
save SUBNET_A_PRIV "$(aws ec2 create-subnet --vpc-id $VPC_A --cidr-block 10.10.2.0/24 --availability-zone $AZ --tag-specifications "$(ts subnet ewb-a-private)" --query Subnet.SubnetId --output text)"
save IGW "$(aws ec2 create-internet-gateway --tag-specifications "$(ts internet-gateway ewb-igw-a)" --query InternetGateway.InternetGatewayId --output text)"
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC_A

save RT_A_PUB  "$(aws ec2 create-route-table --vpc-id $VPC_A --tag-specifications "$(ts route-table ewb-rt-a-public)"  --query RouteTable.RouteTableId --output text)"
save RT_A_PRIV "$(aws ec2 create-route-table --vpc-id $VPC_A --tag-specifications "$(ts route-table ewb-rt-a-private)" --query RouteTable.RouteTableId --output text)"
save ASSOC_A_PUB  "$(aws ec2 associate-route-table --route-table-id $RT_A_PUB  --subnet-id $SUBNET_A_PUB  --query AssociationId --output text)"
save ASSOC_A_PRIV "$(aws ec2 associate-route-table --route-table-id $RT_A_PRIV --subnet-id $SUBNET_A_PRIV --query AssociationId --output text)"
aws ec2 create-route --route-table-id $RT_A_PUB --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW >/dev/null

echo "==> VPC B"
save VPC_B "$(aws ec2 create-vpc --cidr-block 10.20.0.0/16 --tag-specifications "$(ts vpc ewb-vpc-b)" --query Vpc.VpcId --output text)"
save SUBNET_B_PRIV "$(aws ec2 create-subnet --vpc-id $VPC_B --cidr-block 10.20.1.0/24 --availability-zone $AZ --tag-specifications "$(ts subnet ewb-b-private)" --query Subnet.SubnetId --output text)"
save RT_B_PRIV "$(aws ec2 create-route-table --vpc-id $VPC_B --tag-specifications "$(ts route-table ewb-rt-b-private)" --query RouteTable.RouteTableId --output text)"
save ASSOC_B_PRIV "$(aws ec2 associate-route-table --route-table-id $RT_B_PRIV --subnet-id $SUBNET_B_PRIV --query AssociationId --output text)"

echo "==> Security groups"
mksg() { aws ec2 create-security-group --group-name "$1" --description "$2" --vpc-id "$3" --tag-specifications "$(ts security-group $1)" --query GroupId --output text; }
save SG_BASTION "$(mksg ewb-sg-bastion 'Bastion SSH from my IP' $VPC_A)"
save SG_APP_A   "$(mksg ewb-sg-app-a   'App-A SSH from bastion, ping from App-B' $VPC_A)"
save SG_APP_B   "$(mksg ewb-sg-app-b   'App-B SSH from bastion, ping from App-A' $VPC_B)"
ssh_rule()  { aws ec2 authorize-security-group-ingress --group-id "$1" --protocol tcp --port 22 --cidr "$2" >/dev/null; }
icmp_rule() { aws ec2 authorize-security-group-ingress --group-id "$1" --ip-permissions "IpProtocol=icmp,FromPort=8,ToPort=0,IpRanges=[{CidrIp=$2,Description=Echo-request}]" >/dev/null; }
ssh_rule  $SG_BASTION "$MY_IP/32"
ssh_rule  $SG_APP_A   10.10.1.10/32
icmp_rule $SG_APP_A   10.20.1.10/32
ssh_rule  $SG_APP_B   10.10.1.10/32
icmp_rule $SG_APP_B   10.10.2.10/32

echo "==> Key pair ewb-lab"
if aws ec2 describe-key-pairs --key-names ewb-lab >/dev/null 2>&1; then
  echo "Key pair ewb-lab already exists in AWS. Delete it in the console (EC2 > Key Pairs) and re-run."; exit 1
fi
mkdir -p ~/.ssh
aws ec2 create-key-pair --key-name ewb-lab --key-type rsa --key-format pem --tag-specifications "$(ts key-pair ewb-lab)" --query KeyMaterial --output text > ~/.ssh/ewb-lab.pem
chmod 400 ~/.ssh/ewb-lab.pem

echo "==> Launching 3 instances (Amazon Linux 2023, $INSTANCE_TYPE)"
AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text 2>/dev/null || \
      aws ec2 describe-images --owners amazon --filters "Name=name,Values=al2023-ami-2023*-x86_64" "Name=state,Values=available" --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
save AMI "$AMI"
launch() { aws ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name ewb-lab \
  --network-interfaces "DeviceIndex=0,SubnetId=$2,PrivateIpAddress=$3,Groups=$4,AssociatePublicIpAddress=$5" \
  --block-device-mappings "DeviceName=/dev/xvda,Ebs={VolumeSize=8,VolumeType=gp3,DeleteOnTermination=true}" \
  --metadata-options HttpTokens=required \
  --tag-specifications "$(ts instance $1)" "$(ts volume $1-root)" --query 'Instances[0].InstanceId' --output text; }
save I_BASTION "$(launch ewb-bastion $SUBNET_A_PUB  10.10.1.10 $SG_BASTION true)"
save I_APP_A   "$(launch ewb-app-a   $SUBNET_A_PRIV 10.10.2.10 $SG_APP_A   false)"
save I_APP_B   "$(launch ewb-app-b   $SUBNET_B_PRIV 10.20.1.10 $SG_APP_B   false)"

echo "==> Waiting for status checks (2-4 minutes)..."
aws ec2 wait instance-status-ok --instance-ids $I_BASTION $I_APP_A $I_APP_B
save BASTION_IP "$(aws ec2 describe-instances --instance-ids $I_BASTION --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)"

echo; echo "DONE. All 3 instances are running. Bastion public IP: $BASTION_IP"
echo "NEXT: ./02-ssh-setup.sh"
