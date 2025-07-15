import xml.etree.ElementTree as ET
import os
import sys
from html import escape

# Utility: strip namespace
def strip_namespace(tag):
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

# Detect Profile vs PermissionSet
def get_metadata_type(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    root_name = strip_namespace(root.tag)
    if root_name == 'Profile':
        return 'Profile'
    elif root_name == 'PermissionSet':
        return 'PermissionSet'
    else:
        return 'Unknown'

# Turn an element's immediate children into dict
def elem_to_dict(elem):
    d = {}
    for child in elem:
        key = strip_namespace(child.tag)
        if key in d:
            if not isinstance(d[key], list):
                d[key] = [d[key]]
            d[key].append(child.text.strip() if child.text else '')
        else:
            d[key] = child.text.strip() if child.text else ''
    return d

# Key fields for repeated sections
KEY_FIELDS = {
    'userPermissions': 'name',
    'fieldPermissions': 'field',
    'objectPermissions': 'object',
    'recordTypeVisibilities': 'recordType',
    'applicationVisibilities': 'application',
    'classAccesses': 'apexClass',
    'pageAccesses': 'apexPage',
    'tabVisibilities': 'tab',
    'tabSettings': 'tab',
    'customPermissions': 'name',
    'layoutAssignments': 'layout',
    'externalDataSourceAccesses': 'externalDataSource',
    'customMetadataTypeAccesses': 'name',
    'customSettingAccesses': 'name',
    'agentAccesses': 'agent',
    'emailRoutingAddressAccesses': 'emailRoutingAddress',
    'externalCredentialPrincipalAccesses': 'externalCredentialPrincipal',
    'flowAccesses': 'flow',
    'ServicePresenceStatusAccesses': 'servicePresenceStatus',
    'categoryGroupVisibilities': 'dataCategoryGroup',
    'loginIpRanges': 'startAddress',
    'profileActionOverrides': 'actionName'
}

# Single-occurrence tags we want to explicitly compare
SINGLE_TAGS = [
    'description',
    'hasActivationRequired',
    'label',
    'license',
    'userLicense',
    'fullName',
    'custom',
    'loginHours'
]

# Return a unique key for an element
def elem_key(elem):
    tag = strip_namespace(elem.tag)
    key_field = KEY_FIELDS.get(tag)
    if not key_field:
        return None
    for child in elem:
        if strip_namespace(child.tag) == key_field:
            return child.text.strip() if child.text else ''
    return None

# Parse into sections
def parse_metadata(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    sections = {}
    for child in root:
        tag = strip_namespace(child.tag)
        if tag not in sections:
            sections[tag] = []
        sections[tag].append(child)
    return sections

# Base filename without long extension
def base_filename(fname):
    base = os.path.basename(fname)
    for ext in ['.profile-meta.xml', '.permissionset-meta.xml', '.xml']:
        if base.endswith(ext):
            base = base[:-len(ext)]
            break
    base = base.split('.')[0]
    return base

# Compare
def compare_sections(sections1, sections2, file1, file2):
    all_sections = sorted(set(sections1.keys()) | set(sections2.keys()))
    report_data = {
        'summary': {},
        'sections': [],
        'file1_base': base_filename(file1),
        'file2_base': base_filename(file2)
    }

    for section in all_sections:
        elems1 = sections1.get(section, [])
        elems2 = sections2.get(section, [])

        dict1 = {elem_key(e): e for e in elems1 if elem_key(e) is not None}
        dict2 = {elem_key(e): e for e in elems2 if elem_key(e) is not None}

        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())

        only_in_1_keys = keys1 - keys2
        only_in_2_keys = keys2 - keys1
        in_both_keys = keys1 & keys2

        only_in_1 = [dict1[k] for k in sorted(only_in_1_keys)]
        only_in_2 = [dict2[k] for k in sorted(only_in_2_keys)]

        diffs = []

        # Compare keyed elements
        for k in sorted(in_both_keys):
            d1 = elem_to_dict(dict1[k])
            d2 = elem_to_dict(dict2[k])
            if d1 != d2:
                diffs.append({
                    'key': k,
                    'file1_dict': d1,
                    'file2_dict': d2
                })

        # If no keys, handle single-occurrence sections
        if not dict1 and not dict2:
            # Special handling only if section is in SINGLE_TAGS
            if section in SINGLE_TAGS:
                if len(elems1) == 1 and len(elems2) == 1:
                    d1 = elem_to_dict(elems1[0])
                    d2 = elem_to_dict(elems2[0])
                    if d1 != d2:
                        diffs.append({
                            'key': '(single)',
                            'file1_dict': d1,
                            'file2_dict': d2
                        })
                elif len(elems1) == 1 and len(elems2) == 0:
                    only_in_1.append(elems1[0])
                elif len(elems2) == 1 and len(elems1) == 0:
                    only_in_2.append(elems2[0])

        report_data['summary'][section] = {
            'only_in_1': len(only_in_1),
            'only_in_2': len(only_in_2),
            'diffs': len(diffs)
        }

        report_data['sections'].append({
            'section': section,
            'only_in_1': only_in_1,
            'only_in_2': only_in_2,
            'diffs': diffs
        })

    return report_data

# HTML generation
def generate_html_report(report_data):
    file1 = escape(report_data['file1_base'])
    file2 = escape(report_data['file2_base'])
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Metadata Comparison Report</title>
<style>
body {{ font-family: Arial, sans-serif; padding: 15px; background: #f5f5f5; }}
h1 {{ margin-bottom: 0; }}
.summary {{ margin-bottom: 15px; padding: 10px; background: #fff; border-radius: 5px; }}
.summary table {{ border-collapse: collapse; width: 100%; table-layout: fixed; word-wrap: break-word; }}
.summary th, .summary td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
.section {{ margin-bottom: 15px; background: #fff; border-radius: 5px; border: 1px solid #ccc; overflow-x: auto; }}
.header {{ background-color: #ddd; padding: 10px; cursor: pointer; user-select: none; font-weight: bold; }}
.content {{ display: none; padding: 10px; font-family: monospace; white-space: pre-wrap; background: #fafafa; border-top: 1px solid #ccc; }}
.filter-box {{ margin-bottom: 15px; }}
button {{ margin-right: 10px; padding: 6px 12px; font-size: 14px; }}
.diff-only1 {{ background-color: #c8e6c9; }}
.diff-only2 {{ background-color: #ffcdd2; }}
.diff-diff {{ background-color: #ffe0b2; }}
.sidebyside {{ display: flex; gap: 10px; }}
.sidebyside > div {{ flex: 1; padding: 5px; border: 1px solid #ccc; background: #fff; overflow-x: auto; }}
</style>
</head>
<body>
<h1>Metadata Comparison Report</h1>

<div class="filter-box">
  <label>Filter: <input type="text" id="filterInput" placeholder="Type to filter sections or keys..." style="width:300px"></label>
  <button onclick="expandAll()">Expand All</button>
  <button onclick="collapseAll()">Collapse All</button>
</div>

<div class="summary">
  <h2>Summary of Differences</h2>
  <table>
    <thead><tr><th>Section</th><th>Only in {file1}</th><th>Only in {file2}</th><th>Different Values</th></tr></thead>
    <tbody>
"""
    for section, counts in report_data['summary'].items():
        html += f"<tr><td>{escape(section)}</td><td>{counts['only_in_1']}</td><td>{counts['only_in_2']}</td><td>{counts['diffs']}</td></tr>"

    html += """
    </tbody>
  </table>
</div>
"""

    # Collapsible detail sections
    for section_data in report_data['sections']:
        section = section_data['section']
        only_in_1 = section_data['only_in_1']
        only_in_2 = section_data['only_in_2']
        diffs = section_data['diffs']

        html += f'<div class="section" data-section="{escape(section).lower()}">\n'
        html += f'<div class="header">{escape(section)}</div>\n'
        html += '<div class="content">\n'

        if only_in_1:
            html += f"<b>Only in {file1}:</b>\n"
            for elem in only_in_1:
                key = elem_key(elem) or "(single)"
                html += f'<div class="diff-only1">&lt;{escape(strip_namespace(elem.tag))}&gt; {escape(key)}</div>\n'

        if only_in_2:
            html += f"<b>Only in {file2}:</b>\n"
            for elem in only_in_2:
                key = elem_key(elem) or "(single)"
                html += f'<div class="diff-only2">&lt;{escape(strip_namespace(elem.tag))}&gt; {escape(key)}</div>\n'

        if diffs:
            html += f"<b>Different values:</b>\n"
            for d in diffs:
                key = d['key'] or "(single)"
                html += f'<div class="diff-diff"><b>{escape(key)}</b>\n<div class="sidebyside">\n'
                html += f'<div><u>{file1}</u><br>'
                for k, v in sorted(d['file1_dict'].items()):
                    html += f'<b>{escape(k)}</b>: {escape(str(v))}<br>'
                html += '</div>\n'
                html += f'<div><u>{file2}</u><br>'
                for k, v in sorted(d['file2_dict'].items()):
                    html += f'<b>{escape(k)}</b>: {escape(str(v))}<br>'
                html += '</div>\n</div></div>\n'

        if not only_in_1 and not only_in_2 and not diffs:
            html += "<i>(no differences)</i>\n"

        html += '</div></div>\n'

    html += """
<script>
document.querySelectorAll('.header').forEach(header => {
    header.addEventListener('click', () => {
        const content = header.nextElementSibling;
        content.style.display = content.style.display === 'block' ? 'none' : 'block';
    });
});
function expandAll(){document.querySelectorAll('.content').forEach(c=>c.style.display='block');}
function collapseAll(){document.querySelectorAll('.content').forEach(c=>c.style.display='none');}
document.getElementById('filterInput').addEventListener('input', function() {
    const filter = this.value.toLowerCase();
    document.querySelectorAll('.section').forEach(section => {
        const secName = section.getAttribute('data-section');
        const content = section.querySelector('.content').textContent.toLowerCase();
        section.style.display = (secName.includes(filter)||content.includes(filter)) ? '' : 'none';
    });
});
</script>

</body>
</html>
"""
    return html

def main():
    xml_files = [f for f in os.listdir('.') if f.lower().endswith('.xml')]
    if len(xml_files) != 2:
        print("❌ Please place exactly two XML files (Profiles or Permission Sets) in this folder.")
        sys.exit(1)

    file1, file2 = xml_files
    type1 = get_metadata_type(file1)
    type2 = get_metadata_type(file2)

    if type1 == 'Unknown' or type2 == 'Unknown':
        print("❌ One or both files are not recognized as Profile or PermissionSet.")
        sys.exit(1)

    if type1 != type2:
        print(f"❌ Mismatched types: {file1} is {type1}, {file2} is {type2}. Please compare two of the same type.")
        sys.exit(1)

    print(f"[LOG] Detected both files as {type1}s.")
    print(f"[LOG] Comparing {file1} and {file2}")

    sections1 = parse_metadata(file1)
    sections2 = parse_metadata(file2)

    report_data = compare_sections(sections1, sections2, file1, file2)

    html_report = generate_html_report(report_data)

    with open('comparison_report.html', 'w', encoding='utf-8') as f:
        f.write(html_report)

    print("✅ Comparison report written to comparison_report.html")

if __name__ == "__main__":
    main()
