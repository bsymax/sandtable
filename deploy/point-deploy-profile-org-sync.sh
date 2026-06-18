#!/bin/bash
# 热修 · 关键人物 ↔ 组织架构联动 + 增删人员/编辑层级
# 用法: bash deploy/point-deploy-profile-org-sync.sh [IP]
set -euo pipefail
IP="${1:-117.72.211.51}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_OPTS=(-o ConnectTimeout=30)

echo "==> 档案组织架构联动热修 → root@${IP}"
scp "${SSH_OPTS[@]}" "$ROOT/server/routers/profile.py" "$ROOT/server/schemas.py" "root@${IP}:/opt/sandtable/server/"
scp "${SSH_OPTS[@]}" "$ROOT/server/routers/profile.py" "root@${IP}:/opt/sandtable/server/routers/"
scp "${SSH_OPTS[@]}" "$ROOT/web/profile.html" "root@${IP}:/opt/sandtable/web/"
ssh "${SSH_OPTS[@]}" "root@${IP}" bash -s <<'REMOTE'
set -euo pipefail
cd /opt/sandtable/server
source venv/bin/activate
python3 - <<'PY'
from database import SessionLocal
from models import Brand, BrandContact, BrandProfile
from routers.profile import _sync_org_nodes_from_contacts

db = SessionLocal()
try:
    n = 0
    for brand in db.query(Brand).all():
        profile = db.query(BrandProfile).filter(BrandProfile.brand_id == brand.id).first()
        if not profile:
            continue
        contacts = db.query(BrandContact).filter(
            BrandContact.brand_id == brand.id, BrandContact.is_active == True
        ).all()
        _sync_org_nodes_from_contacts(profile, contacts)
        n += 1
    db.commit()
    print(f"OK: 已同步 {n} 个品牌 org_structure.nodes")
finally:
    db.close()
PY
chmod -R a+rX /opt/sandtable/web
systemctl restart sandtable
sleep 3
systemctl is-active sandtable
REMOTE
echo "✅ 外网 profile Tab2 品牌简介：改关键人物后架构图应同步更新"
