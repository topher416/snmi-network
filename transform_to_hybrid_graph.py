#!/usr/bin/env python3
"""Create hybrid graph with organizations as large nodes and individuals as smaller nodes."""

import json
from collections import defaultdict

# Load original data
with open('sigma_graph_data.json', 'r') as f:
    original_data = json.load(f)

# Define node type colors
org_type_colors = {
    'Healthcare': '#2196F3',      # Blue
    'Government': '#9C27B0',       # Purple
    'Nonprofit': '#FF9800',        # Orange
    'Education': '#4CAF50',        # Green
    'Private': '#F44336',          # Red
    'Unaffiliated': '#999999'      # Gray
}

person_status_colors = {
    'Hot': '#ff5722',
    'Warm': '#ff9800',
    'Cold': '#64b5f6',
    '': '#999999'
}

# Categorize organizations
def categorize_org(org_name):
    """Categorize organization by name."""
    name_lower = org_name.lower()

    if 'unaffiliated' in name_lower or not org_name.strip():
        return 'Unaffiliated'
    elif any(word in name_lower for word in ['hospital', 'health', 'medical', 'medicine', 'clinic', 'care']):
        return 'Healthcare'
    elif any(word in name_lower for word in ['state', 'county', 'city', 'government', 'governor', 'department', 'hfs']):
        return 'Government'
    elif any(word in name_lower for word in ['university', 'college', 'uic']):
        return 'Education'
    elif any(word in name_lower for word in ['foundation', 'trust', 'committee', 'association', 'network', 'coalition']):
        return 'Nonprofit'
    else:
        return 'Private'

# Build organization list and map
orgs = defaultdict(lambda: {'people': [], 'category': None})
person_to_org = {}

for node in original_data['nodes']:
    org_name = node['attributes'].get('organization', '').strip()
    if not org_name:
        org_name = 'Unaffiliated'

    person_to_org[node['id']] = org_name
    orgs[org_name]['people'].append(node)
    orgs[org_name]['category'] = categorize_org(org_name)

# Create new graph structure
new_graph = {
    'nodes': [],
    'edges': []
}

# Create organization nodes (large hubs)
org_id_map = {}
for idx, (org_name, org_data) in enumerate(sorted(orgs.items())):
    org_id = f'org_{idx}'
    org_id_map[org_name] = org_id

    # Large nodes for organizations
    org_size = 15 + len(org_data['people']) * 3

    new_graph['nodes'].append({
        'id': org_id,
        'label': org_name,
        'type': 'Organization',
        'size': org_size,
        'color': org_type_colors.get(org_data['category'], '#999999'),
        'x': 0,
        'y': 0,
        'attributes': {
            'nodeType': 'Organization',
            'category': org_data['category'],
            'people_count': len(org_data['people']),
            'isOrganization': True
        }
    })

# Create individual person nodes (smaller)
person_id_to_new_id = {}
for node in original_data['nodes']:
    # Keep original person ID or create new one
    person_id = node['id']
    person_id_to_new_id[person_id] = person_id

    # Smaller nodes for people
    person_size = 3 + (int(node['attributes'].get('mentions', 0)) * 0.3)

    # Color by status
    status = node['attributes'].get('status', '')
    person_color = person_status_colors.get(status, '#999999')

    new_graph['nodes'].append({
        'id': person_id,
        'label': node['label'],
        'type': 'Person',
        'size': person_size,
        'color': person_color,
        'x': 0,
        'y': 0,
        'attributes': {
            'nodeType': 'Person',
            'organization': node['attributes'].get('organization', ''),
            'title': node['attributes'].get('title', ''),
            'status': status,
            'priority': node['attributes'].get('priority', ''),
            'sentiment': node['attributes'].get('sentiment', ''),
            'stance': node['attributes'].get('stance', ''),
            'relationship_type': node['attributes'].get('relationship_type', ''),
            'steward': node['attributes'].get('steward', ''),
            'mentions': node['attributes'].get('mentions', '0'),
            'isPerson': True
        }
    })

# Create edges from people to their organizations
edge_id = 0
for node in original_data['nodes']:
    person_id = node['id']
    org_name = person_to_org.get(person_id)
    org_id = org_id_map.get(org_name)

    if org_id:
        new_graph['edges'].append({
            'id': f'e_{edge_id}',
            'source': person_id,
            'target': org_id,
            'size': 1,
            'color': '#E0E0E0',
            'label': 'member of',
            'attributes': {
                'edgeType': 'membership'
            }
        })
        edge_id += 1

# Create person-to-person edges (from original data)
for edge in original_data['edges']:
    source_id = person_id_to_new_id.get(edge['source'])
    target_id = person_id_to_new_id.get(edge['target'])

    if source_id and target_id:
        new_graph['edges'].append({
            'id': f'e_{edge_id}',
            'source': source_id,
            'target': target_id,
            'size': 2,
            'color': '#CCCCCC',
            'label': edge.get('label', ''),
            'attributes': {
                'edgeType': 'relationship',
                'original_type': edge.get('type', '')
            }
        })
        edge_id += 1

# Save new graph
with open('sigma_graph_data_hybrid.json', 'w') as f:
    json.dump(new_graph, f, indent=2)

print(f"✅ Created hybrid graph:")
print(f"   - {len(orgs)} organization nodes (large)")
print(f"   - {len(original_data['nodes'])} person nodes (small)")
print(f"   - Total nodes: {len(new_graph['nodes'])}")
print(f"   - {len(new_graph['edges'])} edges ({len(original_data['nodes'])} membership + {len(original_data['edges'])} relationships)")
print(f"   - Saved to: sigma_graph_data_hybrid.json")

# Print summary by category
from collections import Counter
categories = Counter(org_data['category'] for org_data in orgs.values())
print(f"\nOrganizations by category:")
for category, count in categories.most_common():
    print(f"   - {category}: {count}")
