#!/bin/bash
cd /opt/ai_employee_vault

# Pull any new approvals you made on your laptop
git pull origin main

# Push any new drafts or logs the AI created in the cloud
git add .
git commit -m "Auto-sync: Cloud FTE update"
git push origin main
