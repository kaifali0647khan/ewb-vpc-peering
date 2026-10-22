# EWB VPC Peering Kit: run these in order

## One-time setup (YOU do this, 15 min)
1. Use Mac, Linux or **Windows WSL (Ubuntu)**. Install the AWS CLI v2 and `python3`, then `pip install reportlab pillow`.
2. AWS Console -> IAM -> your user -> Security credentials -> **Create access key**. Run `aws configure` and paste the key, secret, region `ap-south-1`, output `json`.
3. Open `config.env`, set your real **STUDENT** and **BATCH**.
4. `chmod +x *.sh`

## Run order
| # | Command | What it does | Your job after |
|---|---|---|---|
| 1 | `./01-deploy.sh` | Builds both VPCs, subnets, IGW, route tables, security groups, key pair, 3 EC2 | Take Checkpoint 01 and 02 screenshots in the console |
| 2 | `./02-ssh-setup.sh` | Writes ~/.ssh/config, tests bastion + App-A | - |
| 3 | `./03-baseline-test.sh` | Test 01: ping fails before peering | - |
| 4 | `./04-peering.sh` | Creates and accepts peering, adds 3 routes | Checkpoint 03 and 04 screenshots |
| 5 | `./05-verify.sh` | Tests 02-05 + controlled failure | Screenshot the SG inbound rules page |
| 6 | `./06-inventory.sh` | Saves inventory evidence | - |
| 7 | `python3 make_report.py` | Builds `YourName_EWB_VPC_Peering.pdf` | Read it, submit it |
| 8 | `./99-cleanup.sh` | Deletes everything, saves cleanup proof | Screenshot empty lists; re-run step 7 |

## Screenshots to put in `screenshots/` (named in order, they are added to the PDF automatically)
01-vpc-a-and-b, 02-subnets, 03-route-table-a-public (Routes + Subnet associations), 04-route-table-a-private, 05-route-table-b-private, 06-security-groups (3 inbound rule screens), 07-instances-list (IDs + IPs), 08-app-a-no-public-ip, 09-app-b-no-public-ip, 10-peering-active, 11-cleanup-empty

## Problems
- Bastion SSH times out -> `./fix-my-ip.sh` (your internet IP changed)
- Script stops halfway -> read the red error, fix it, run `./99-cleanup.sh` and start again from 1
- Never share or upload the .pem file or ids.env
