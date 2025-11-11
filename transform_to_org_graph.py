#!/usr/bin/env python3
"""Transform person-centric graph to organization-centric graph."""

import json
from collections import defaultdict

# Load original data
with open('sigma_graph_data.json', 'r') as f:
    original_data = json.load(f)

# Build organization nodes
orgs = defaultdict(lambda: {
    'people': [],
    'statuses': set(),
    'priorities': set(),
    'types': set()
})

# Map person ID to organization
person_to_org = {}

for node in original_data['nodes']:
    org_name = node['attributes'].get('organization', '').strip()
    if not org_name:
        org_name = 'Unaffiliated'

    person_to_org[node['id']] = org_name

    person_info = {
        'id': node['id'],
        'name': node['label'],
        'title': node['attributes'].get('title', ''),
        'status': node['attributes'].get('status', ''),
        'priority': node['attributes'].get('priority', ''),
        'sentiment': node['attributes'].get('sentiment', ''),
        'stance': node['attributes'].get('stance', ''),
        'relationship_type': node['attributes'].get('relationship_type', ''),
        'steward': node['attributes'].get('steward', ''),
        'mentions': node['attributes'].get('mentions', '0'),
        'nodeType': node.get('type', 'Person')
    }

    orgs[org_name]['people'].append(person_info)

    if node['attributes'].get('status'):
        orgs[org_name]['statuses'].add(node['attributes']['status'])
    if node['attributes'].get('priority'):
        orgs[org_name]['priorities'].add(node['attributes']['priority'])
    orgs[org_name]['types'].add(node.get('type', 'Person'))

# Build organization-to-organization connections
org_connections = defaultdict(lambda: defaultdict(lambda: {
    'count': 0,
    'people_pairs': []
}))

for edge in original_data['edges']:
    source_org = person_to_org.get(edge['source'])
    target_org = person_to_org.get(edge['target'])

    if source_org and target_org and source_org != target_org:
        org_connections[source_org][target_org]['count'] += 1
        org_connections[source_org][target_org]['people_pairs'].append({
            'source': edge['source'],
            'target': edge['target']
        })

# Create new graph structure
new_graph = {
    'nodes': [],
    'edges': []
}

# Define org type colors
org_type_colors = {
    'Healthcare': '#2196F3',      # Blue
    'Government': '#9C27B0',       # Purple
    'Nonprofit': '#FF9800',        # Orange
    'Education': '#4CAF50',        # Green
    'Private': '#F44336',          # Red
    'Unaffiliated': '#999999'      # Gray
}

# Categorize organizations
def categorize_org(org_name, people):
    """Categorize organization by name and people types."""
    name_lower = org_name.lower()

    if 'unaffiliated' in name_lower:
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

# Create organization nodes
org_id_map = {}
for idx, (org_name, org_data) in enumerate(sorted(orgs.items())):
    org_id = f'org_{idx}'
    org_id_map[org_name] = org_id

    org_category = categorize_org(org_name, org_data['people'])

    # Calculate node size based on number of people
    node_size = 5 + len(org_data['people']) * 2

    new_graph['nodes'].append({
        'id': org_id,
        'label': org_name,
        'type': 'Organization',
        'size': node_size,
        'color': org_type_colors.get(org_category, '#999999'),
        'x': 0,
        'y': 0,
        'attributes': {
            'category': org_category,
            'people_count': len(org_data['people']),
            'people': org_data['people'],
            'statuses': list(org_data['statuses']),
            'priorities': list(org_data['priorities']),
            'person_types': list(org_data['types'])
        }
    })

# Create organization edges
edge_id = 0
for source_org, targets in org_connections.items():
    source_id = org_id_map.get(source_org)
    if not source_id:
        continue

    for target_org, connection_data in targets.items():
        target_id = org_id_map.get(target_org)
        if not target_id:
            continue

        # Edge weight based on number of connections
        edge_size = min(1 + connection_data['count'] * 0.5, 10)

        new_graph['edges'].append({
            'id': f'e_{edge_id}',
            'source': source_id,
            'target': target_id,
            'size': edge_size,
            'color': '#CCCCCC',
            'label': f"{connection_data['count']} connection(s)",
            'attributes': {
                'connection_count': connection_data['count'],
                'people_pairs': connection_data['people_pairs'][:10]  # Limit to first 10
            }
        })
        edge_id += 1

# Save new graph
with open('sigma_graph_data_orgs.json', 'w') as f:
    json.dump(new_graph, f, indent=2)

print(f"✅ Created organization-centric graph:")
print(f"   - {len(new_graph['nodes'])} organization nodes")
print(f"   - {len(new_graph['edges'])} inter-org connections")
print(f"   - Saved to: sigma_graph_data_orgs.json")

# Print summary by category
from collections import Counter
categories = Counter(node['attributes']['category'] for node in new_graph['nodes'])
print(f"\nOrganizations by category:")
for category, count in categories.most_common():
    print(f"   - {category}: {count}")
