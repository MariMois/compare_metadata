# 🛠️ Salesforce Profile / Permission Set Comparator

This Python script compares **two Salesforce Profile or Permission Set XML files** placed in the same folder and outputs a **detailed, collapsible HTML report** of all differences.

---

## ✨ Features

✅ Supports **Profiles** and **Permission Sets**.  
✅ Detects:
- Items only in file 1
- Items only in file 2
- Items present in both but with different values  
✅ Covers all known metadata sections:
`agentAccesses, applicationVisibilities, classAccesses, customMetadataTypeAccesses, customPermissions, customSettingAccesses, description, emailRoutingAddressAccesses, externalCredentialPrincipalAccesses, externalDataSourceAccesses, fieldPermissions, flowAccesses, hasActivationRequired, label, license, objectPermissions, pageAccesses, recordTypeVisibilities, ServicePresenceStatusAccesses, tabSettings, userLicense, userPermissions, categoryGroupVisibilities, custom, fieldLevelSecurities, fullName, layoutAssignments, loginFlows, loginHours, loginIpRanges, profileActionOverrides, tabVisibilities`

✅ Generates a **summary table** with counts, and **collapsible sections** with details.  
✅ Filter box to quickly search through results.

---

## 📦 Requirements

- Python 3.8+ installed
- Two `.xml` files (Profile or PermissionSet) in the same folder as the script

---

## 🚀 Usage

1. Place `compare_metadata.py` in a folder with **exactly two** XML files:
