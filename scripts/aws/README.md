# AnalyzaX on AWS (single EC2 host)

Runs the full `docker-compose.prod.yml` stack — nginx edge proxy, static
frontend, FastAPI backend, job worker, PostgreSQL and Redis — on one Ubuntu
24.04 EC2 instance in `ap-south-1` (Mumbai).

| Script | What it does |
|---|---|
| `provision.sh` | Creates key pair, security group (SSH from your IP only; 80/443 public), a `t3.medium` with 40 GB gp3, and an Elastic IP. Idempotent. Writes `scripts/aws/.instance`. |
| `user-data.sh` | First-boot bootstrap: Docker Engine + Compose/Buildx from Docker's apt repo, 4 GB swap. |
| `deploy.sh` | Packs `git HEAD`, uploads it to `/opt/analyzax`, creates `.env` with generated secrets on first deploy, runs `docker compose up -d --build`, checks `/health/live`. |

## Deploy from AWS CloudShell

```bash
git clone https://github.com/beniwalravi1937-coder/AnalyzaX.git
cd AnalyzaX
bash scripts/aws/provision.sh && bash scripts/aws/deploy.sh
```

Re-deploy after pushing new commits: `git pull && bash scripts/aws/provision.sh && bash scripts/aws/deploy.sh`
(re-running `provision.sh` is safe and refreshes the SSH rule for CloudShell's current IP).

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

## Cost (ap-south-1, approx.)

t3.medium ~$30/month + 40 GB gp3 ~$4 + public IPv4 ~$4. To stop billing for compute:
`aws ec2 stop-instances --region ap-south-1 --instance-ids <id>` (disk and IP still bill).
