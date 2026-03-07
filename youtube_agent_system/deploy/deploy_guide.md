# Oracle Cloud Deployment Guide

## Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com/free](https://cloud.oracle.com/free)
2. Click **Start for Free**
3. Fill in your details (name, email, country)
4. **Credit card required** for verification only — Always Free tier is genuinely $0
5. Select your **Home Region** (choose closest to your audience — e.g., Mumbai for India)
6. Complete signup

## Step 2: Create Always Free VM

1. Go to **Compute > Instances > Create Instance**
2. Configure:
   - **Name**: `youtube-agent`
   - **Image**: Ubuntu 22.04 (Canonical)
   - **Shape**: Click **Change Shape** > **Ampere** > `VM.Standard.A1.Flex`
     - **OCPUs**: 4
     - **Memory**: 24 GB
     - (These are within the Always Free limits)
   - **Networking**: Create new VCN (default settings are fine)
   - **SSH Key**: Click **Generate a key pair** and **download both keys**
3. Click **Create**
4. Wait 2-3 minutes for the VM to provision

## Step 3: Connect via SSH

```bash
# Make your private key secure
chmod 400 ~/Downloads/ssh-key-*.key

# Connect (replace IP with your VM's public IP from the console)
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_VM_IP
```

## Step 4: Upload Project Files

From your LOCAL machine (Windows):

```powershell
# Upload the entire project
scp -i C:\path\to\ssh-key.key -r "C:\Projects\Automated Youtube\Automated_Youtube\*" ubuntu@YOUR_VM_IP:~/youtube_agent_system/

# Upload your .env file
scp -i C:\path\to\ssh-key.key "C:\Projects\Automated Youtube\Automated_Youtube\youtube_agent_system\.env" ubuntu@YOUR_VM_IP:~/youtube_agent_system/youtube_agent_system/.env

# Upload YouTube OAuth credentials
scp -i C:\path\to\ssh-key.key "C:\Projects\Automated Youtube\Automated_Youtube\client_secrets.json" ubuntu@YOUR_VM_IP:~/youtube_agent_system/
scp -i C:\path\to\ssh-key.key "C:\Projects\Automated Youtube\Automated_Youtube\token.pickle" ubuntu@YOUR_VM_IP:~/youtube_agent_system/

# Upload background video
scp -i C:\path\to\ssh-key.key "C:\Projects\Automated Youtube\Automated_Youtube\youtube_agent_system\Minecraft*.mp4" ubuntu@YOUR_VM_IP:~/youtube_agent_system/youtube_agent_system/
```

## Step 5: Run Setup Script

```bash
# SSH into the VM
ssh -i ~/Downloads/ssh-key-*.key ubuntu@YOUR_VM_IP

# Run the setup script
cd ~/youtube_agent_system
bash youtube_agent_system/deploy/setup_cloud.sh
```

## Step 6: First Test Run

```bash
# Activate the virtual environment
source venv/bin/activate

# Test a single video production (to verify everything works)
cd ~/youtube_agent_system
python -m youtube_agent_system.main quick

# If YouTube OAuth needs re-authentication, you'll need to do it once
# via SSH port forwarding (it opens a browser link)
```

## Step 7: Install as System Service

```bash
# Install the service
sudo cp youtube_agent_system/deploy/youtube_agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable youtube_agent
sudo systemctl start youtube_agent

# Check status
sudo systemctl status youtube_agent

# View logs
tail -f youtube_agent_system/youtube_agent_system/logs/scheduler.log
```

## Useful Commands

```bash
# Check scheduler status
python -m youtube_agent_system.smart_scheduler --status

# View live logs
tail -f ~/youtube_agent_system/youtube_agent_system/logs/scheduler.log

# Restart the service
sudo systemctl restart youtube_agent

# Stop the service
sudo systemctl stop youtube_agent

# Check service logs
journalctl -u youtube_agent -f
```

## Troubleshooting

**YouTube OAuth token expired**: SSH into VM, activate venv, run `python -m youtube_agent_system.main quick` to re-authenticate.

**VM runs out of disk**: Generated videos accumulate. Add a cron job to clean old ones:
```bash
# Add to crontab: delete videos older than 3 days
0 0 * * * find ~/youtube_agent_system/youtube_agent_system/generated_assets/ -name "*.mp4" -mtime +3 -delete
```

**Service keeps crashing**: Check error log:
```bash
cat ~/youtube_agent_system/youtube_agent_system/logs/service_error.log
```
