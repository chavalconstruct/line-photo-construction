# fetch_secrets.py
import oci
import base64
import os

# 1. กำหนด OCIDs ของ Secrets ทั้งหมด
SECRET_OCIDS = {
    "LINE_CHANNEL_SECRET": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyafmwx2cfqqco2f7abunjalomjbm45s3wsgv5ygyo5hhra",
    "LINE_CHANNEL_ACCESS_TOKEN": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyasalkoiqxfiobiyndhsmie2zp6tl2o4vil4vaxkexvkda",
    "CONFIG_JSON": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyaafr6dwjcmuv5b34gntpsrfkvwxvgzem2eyg3thzqgywa",
    "CREDENTIALS_JSON": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyali4mjdy6ystiwqq675cxzalxkb5pkyjkqog7axb7iwua",
    "TOKEN_JSON": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyaphwjudvbimnkvzoduwxpyarv43arqvluo7i3xrari5ga",
    "REDIS_URL": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyacndbfgd6tujmi2hblhhdmyq4asocuvqks2kd3d5brnjq",
    "SENTRY_DSN": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvya36goap4plp2ybhsbrvogh5go7sikbftxapu6ffe65jba",
    "PARENT_FOLDER_ID": "ocid1.vaultsecret.oc1.ap-singapore-1.amaaaaaacv36pvyauyvcag3rthy6mebc5p3mgv5xy3s4krrvgvu7xrak7iwq"
}

def get_signer_and_config():
    """
    ตรวจสอบ Environment เพื่อเลือกวิธีการยืนยันตัวตนที่เหมาะสม
    """
    # 2. ตรวจสอบ Environment Variable 'ENV'
    if os.getenv('ENV') == 'production':
        # --- โหมด Production (รันบน OCI) ---
        # ใช้ Instance Principals เหมือนเดิม
        print("Running in PRODUCTION mode. Using Instance Principals.", file=os.sys.stderr)
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return {}, signer # คืนค่า config ว่างๆ และ signer
    else:
        # --- โหมด Development (รันบนเครื่อง) ---
        # ใช้ไฟล์ config จาก OCI CLI (~/.oci/config)
        print("Running in DEVELOPMENT mode. Using local OCI config.", file=os.sys.stderr)
        config = oci.config.from_file()
        return config, None # คืนค่า config และ signer เป็น None

def fetch_secrets_from_vault():
    """
    ดึงข้อมูลลับจาก OCI Vault โดยใช้วิธีการยืนยันตัวตนที่เหมาะสม
    """
    try:
        config, signer = get_signer_and_config()

        # 3. สร้าง Client โดยเลือกใช้ config หรือ signer
        if signer:
            # ถ้ามี signer (Production) ให้ใช้ signer
            secrets_client = oci.secrets.SecretsClient(config={}, signer=signer)
        else:
            # ถ้าไม่มี signer (Development) ให้ใช้ config
            secrets_client = oci.secrets.SecretsClient(config=config)

        # 4. ส่วนที่เหลือทำงานเหมือนเดิม
        for key, secret_ocid in SECRET_OCIDS.items():
            get_secret_bundle_response = secrets_client.get_secret_bundle(secret_id=secret_ocid)
            
            secret_content = get_secret_bundle_response.data.secret_bundle_content.content
            decoded_secret = base64.b64decode(secret_content).decode('utf-8')

            print(f'{key}="{decoded_secret}"')

    except Exception as e:
        print(f"Error fetching secrets from OCI Vault: {e}", file=os.sys.stderr)
        exit(1)

if __name__ == "__main__":
    fetch_secrets_from_vault()