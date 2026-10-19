# AnalyzaX on AWS (single EC2 host)

Runs the full `docker-compose.prod.yml` stack — nginx edge proxy, the
TanStack Start frontend (Node SSR server), FastAPI backend (with its in-process
job worker pool), PostgreSQL and Redis — on one Ubuntu
24.04 EC2 instance in `ap-southeast-2` (Sydney).

The AWS project uses the "new AWS experience": every resource must live in the
project's assigned Region (`ap-southeast-2`), and some actions (e.g. reading the
public SSM AMI parameters) are denied by the managed service control policy.
Override the Region with `ANALYZAX_REGION` and the size with `INSTANCE_TYPE`.

| Script | What it does |
|---|---|
| `provision.sh` | Creates key pair, security group (SSH from your IP only; 80/443 public), a `t3.small` with 30 GB gp3, and an Elastic IP. Idempotent. Writes `scripts/aws/.instance`. |
| `user-data.sh` | First-boot bootstrap: Docker Engine + Compose/Buildx from Docker's apt repo, 4 GB swap. |
| `deploy.sh` | Packs `git HEAD`, uploads it to `/opt/analyzax`, creates `.env` with generated secrets on first deploy, runs `docker compose up -d --build`, checks `/health/live`. |

## Deploy

Sign in first (`aws login --region ap-southeast-2`), then from Git Bash or AWS CloudShell:

```bash
bash scripts/aws/provision.sh && bash scripts/aws/deploy.sh
```

Re-deploy after committing new changes: `bash scripts/aws/provision.sh && bash scripts/aws/deploy.sh`
(re-running `provision.sh` is safe and refreshes the SSH rule for your current IP).

## After the first deploy

- **AI provider:** `.env` ships with `AI_PROVIDER=gemini` and an empty key. Add it on the host:
  `ssh -i ~/.ssh/analyzax-prod.pem ubuntu@<ip>`, edit `/opt/analyzax/.env` (`GEMINI_API_KEY=...`),
  then `cd /opt/analyzax && docker compose -f docker-compose.prod.yml up -d backend worker`.
- **HTTPS:** the site is served over plain HTTP on the Elastic IP, so `SECURE_COOKIES=false`.
  Once a domain points at the IP, add TLS (e.g. certbot) and set `SECURE_COOKIES=true` and
  `ALLOWED_CORS_ORIGINS` to the https origin.
- **Billing** is disabled (`BILLING_ENABLED=false`) until real Stripe keys are configured.
- **Backups:** Postgres and dataset files live in Docker volumes on the instance's EBS disk;
  snapshot the volume (or add `pg_dump` cron) — nothing is backed up automatically.

## Cost (ap-southeast-2, approx.)

t3.small ~$19/month + 30 GB gp3 ~$3 + public IPv4 ~$3.65 ≈ $26/month, paid from the
project's Free plan credits. To pause compute billing:
`aws ec2 stop-instances --region ap-southeast-2 --instance-ids <id>` (disk and IP still bill).
Resize: stop the instance, `aws ec2 modify-instance-attribute --instance-type t3.medium ...`, start it.
