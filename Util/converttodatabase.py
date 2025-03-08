import sqlite3
import csv


TXT_FILE = "G:/MedScan/device.txt"
DB_FILE = "gudid_devices.db"


conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS devices (
    PrimaryDI TEXT PRIMARY KEY,
    publicDeviceRecordKey TEXT,
    publicVersionStatus TEXT,
    deviceRecordStatus TEXT,
    publicVersionNumber INTEGER,
    publicVersionDate TEXT,
    devicePublishDate TEXT,
    deviceCommDistributionEndDate TEXT,
    deviceCommDistributionStatus TEXT,
    brandName TEXT,
    versionModelNumber TEXT,
    catalogNumber TEXT,
    dunsNumber TEXT,
    companyName TEXT,
    deviceCount INTEGER,
    deviceDescription TEXT,
    DMExempt BOOLEAN,
    premarketExempt BOOLEAN,
    deviceHCTP BOOLEAN,
    deviceKit BOOLEAN,
    deviceCombinationProduct BOOLEAN,
    singleUse BOOLEAN,
    lotBatch BOOLEAN,
    serialNumber BOOLEAN,
    manufacturingDate BOOLEAN,
    expirationDate BOOLEAN,
    donationIdNumber BOOLEAN,
    labeledContainsNRL BOOLEAN,
    labeledNoNRL BOOLEAN,
    MRISafetyStatus TEXT,
    rx BOOLEAN,
    otc BOOLEAN,
    deviceSterile BOOLEAN,
    sterilizationPriorToUse BOOLEAN
);
''')

conn.commit()

def safe_int(value, default=0):
    """Convert value to int safely, return default if empty or invalid."""
    return int(value) if value.isdigit() else default

def safe_bool(value):
    """Convert field to boolean (True/False)."""
    return value.lower() == "true"


with open(TXT_FILE, "r", encoding="utf-8") as file:
    reader = csv.DictReader(file, delimiter="|")
    for row in reader:
        data = {
            "PrimaryDI": row["PrimaryDI"],
            "publicDeviceRecordKey": row["publicDeviceRecordKey"],
            "publicVersionStatus": row["publicVersionStatus"],
            "deviceRecordStatus": row["deviceRecordStatus"],
            "publicVersionNumber": safe_int(row["publicVersionNumber"]),
            "publicVersionDate": row["publicVersionDate"],
            "devicePublishDate": row["devicePublishDate"],
            "deviceCommDistributionEndDate": row["deviceCommDistributionEndDate"],
            "deviceCommDistributionStatus": row["deviceCommDistributionStatus"],
            "brandName": row["brandName"],
            "versionModelNumber": row["versionModelNumber"],
            "catalogNumber": row["catalogNumber"],
            "dunsNumber": row["dunsNumber"],
            "companyName": row["companyName"],
            "deviceCount": safe_int(row["deviceCount"]),
            "deviceDescription": row["deviceDescription"],
            "DMExempt": safe_bool(row["DMExempt"]),
            "premarketExempt": safe_bool(row["premarketExempt"]),
            "deviceHCTP": safe_bool(row["deviceHCTP"]),
            "deviceKit": safe_bool(row["deviceKit"]),
            "deviceCombinationProduct": safe_bool(row["deviceCombinationProduct"]),
            "singleUse": safe_bool(row["singleUse"]),
            "lotBatch": safe_bool(row["lotBatch"]),
            "serialNumber": safe_bool(row["serialNumber"]),
            "manufacturingDate": safe_bool(row["manufacturingDate"]),
            "expirationDate": safe_bool(row["expirationDate"]),
            "donationIdNumber": safe_bool(row["donationIdNumber"]),
            "labeledContainsNRL": safe_bool(row["labeledContainsNRL"]),
            "labeledNoNRL": safe_bool(row["labeledNoNRL"]),
            "MRISafetyStatus": row["MRISafetyStatus"],
            "rx": safe_bool(row["rx"]),
            "otc": safe_bool(row["otc"]),
            "deviceSterile": safe_bool(row["deviceSterile"]),
            "sterilizationPriorToUse": safe_bool(row["sterilizationPriorToUse"])
        }

        cursor.execute('''
            INSERT OR REPLACE INTO devices VALUES (
                :PrimaryDI, :publicDeviceRecordKey, :publicVersionStatus, :deviceRecordStatus, 
                :publicVersionNumber, :publicVersionDate, :devicePublishDate, 
                :deviceCommDistributionEndDate, :deviceCommDistributionStatus, :brandName, 
                :versionModelNumber, :catalogNumber, :dunsNumber, :companyName, 
                :deviceCount, :deviceDescription, :DMExempt, :premarketExempt, :deviceHCTP, 
                :deviceKit, :deviceCombinationProduct, :singleUse, :lotBatch, 
                :serialNumber, :manufacturingDate, :expirationDate, :donationIdNumber, 
                :labeledContainsNRL, :labeledNoNRL, :MRISafetyStatus, :rx, :otc, 
                :deviceSterile, :sterilizationPriorToUse
            )
        ''', data)

conn.commit()
conn.close()

print("Database successfully created with all records from the TXT file.")
