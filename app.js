let renderer, graph, layout;
let selectedNode = null;
let activeFilters = {
    types: new Set(),
    statuses: new Set(),
    search: ''
};

// Load data from embedded variable
const data = GRAPH_DATA;
initializeGraph(data);

function initializeGraph(data) {
    // Create a new graph
    graph = new graphology.Graph();

    // Add nodes
    data.nodes.forEach(node => {
        graph.addNode(node.id, {
            label: node.label,
            type: node.type,
            size: node.size || 5,
            color: node.color || '#4CAF50',
            x: Math.random() * 1000,
            y: Math.random() * 1000,
            ...node.attributes,
            originalColor: node.color || '#4CAF50',
            hidden: false
        });
    });

    // Add edges
    data.edges.forEach(edge => {
        try {
            graph.addEdge(edge.source, edge.target, {
                size: edge.size || 1,
                color: edge.color || '#CCCCCC',
                type: edge.type || 'line',
                label: edge.label || '',
                hidden: false
            });
        } catch (e) {
            console.warn(`Could not add edge ${edge.id}:`, e);
        }
    });

    // Apply ForceAtlas2 layout
    console.log('Applying layout...');
    const settings = graphologyLibrary.layoutForceAtlas2;
    settings.assign(graph, {
        iterations: 50,
        settings: {
            barnesHutOptimize: true,
            strongGravityMode: false,
            gravity: 0.1,
            scalingRatio: 10
        }
    });

    // Initialize Sigma
    const container = document.getElementById('sigma-container');
    renderer = new Sigma(graph, container, {
        renderEdgeLabels: false,
        defaultNodeColor: '#4CAF50',
        defaultEdgeColor: '#CCCCCC',
        labelSize: 12,
        labelWeight: 'normal',
        labelColor: { color: '#000' }
    });

    // Hide loading message
    document.getElementById('loading').classList.add('hidden');

    // Update stats
    updateStats();

    // Setup filters
    setupTypeFilters();
    setupStatusFilters();

    // Setup event listeners
    setupEventListeners();

    console.log('Graph initialized with', graph.order, 'nodes and', graph.size, 'edges');
}

function setupTypeFilters() {
    const types = new Set();
    graph.forEachNode((node, attributes) => {
        types.add(attributes.type);
    });

    const container = document.getElementById('type-filters');
    const typeColors = {
        'Person': '#4CAF50',
        'Organization': '#FF9800',
        'Healthcare': '#2196F3',
        'Government': '#9C27B0',
        'Media': '#F44336'
    };

    Array.from(types).sort().forEach(type => {
        if (!type) return;
        const div = document.createElement('div');
        div.className = 'filter-item';
        div.innerHTML = `
            <input type="checkbox" id="type-${type}" value="${type}" checked>
            <label for="type-${type}">${type}</label>
            <div class="color-dot" style="background: ${typeColors[type] || '#999'}"></div>
        `;
        div.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                const checkbox = div.querySelector('input');
                checkbox.checked = !checkbox.checked;
            }
            updateFilters();
        });
        container.appendChild(div);
        activeFilters.types.add(type);
    });
}

function setupStatusFilters() {
    const statuses = new Set();
    graph.forEachNode((node, attributes) => {
        if (attributes.status) {
            statuses.add(attributes.status);
        }
    });

    const container = document.getElementById('status-filters');
    Array.from(statuses).sort().forEach(status => {
        const div = document.createElement('div');
        div.className = 'filter-item';
        div.innerHTML = `
            <input type="checkbox" id="status-${status}" value="${status}" checked>
            <label for="status-${status}">${status}</label>
        `;
        div.addEventListener('click', (e) => {
            if (e.target.tagName !== 'INPUT') {
                const checkbox = div.querySelector('input');
                checkbox.checked = !checkbox.checked;
            }
            updateFilters();
        });
        container.appendChild(div);
        activeFilters.statuses.add(status);
    });
}

function setupEventListeners() {
    // Search
    document.getElementById('search').addEventListener('input', (e) => {
        activeFilters.search = e.target.value.toLowerCase();
        updateFilters();
    });

    // Node click
    renderer.on('clickNode', ({ node }) => {
        selectNode(node);
    });

    // Stage click (deselect)
    renderer.on('clickStage', () => {
        deselectNode();
    });

    // Zoom controls
    document.getElementById('zoom-in').addEventListener('click', () => {
        const camera = renderer.getCamera();
        camera.animatedZoom({ duration: 200 });
    });

    document.getElementById('zoom-out').addEventListener('click', () => {
        const camera = renderer.getCamera();
        camera.animatedUnzoom({ duration: 200 });
    });

    document.getElementById('zoom-reset').addEventListener('click', () => {
        const camera = renderer.getCamera();
        camera.animatedReset({ duration: 400 });
    });

    // Reset filters
    document.getElementById('reset-filters').addEventListener('click', () => {
        document.querySelectorAll('#type-filters input, #status-filters input').forEach(input => {
            input.checked = true;
        });
        document.getElementById('search').value = '';
        activeFilters.types.clear();
        activeFilters.statuses.clear();
        activeFilters.search = '';

        graph.forEachNode((node, attributes) => {
            activeFilters.types.add(attributes.type);
            if (attributes.status) activeFilters.statuses.add(attributes.status);
        });

        updateFilters();
    });

    // Reset layout
    document.getElementById('reset-layout').addEventListener('click', () => {
        console.log('Resetting layout...');
        const settings = graphologyLibrary.layoutForceAtlas2;
        settings.assign(graph, {
            iterations: 50,
            settings: {
                barnesHutOptimize: true,
                strongGravityMode: false,
                gravity: 0.1,
                scalingRatio: 10
            }
        });
        renderer.refresh();
    });
}

function updateFilters() {
    // Update active filters from checkboxes
    activeFilters.types.clear();
    document.querySelectorAll('#type-filters input:checked').forEach(input => {
        activeFilters.types.add(input.value);
    });

    activeFilters.statuses.clear();
    document.querySelectorAll('#status-filters input:checked').forEach(input => {
        activeFilters.statuses.add(input.value);
    });

    // Apply filters
    graph.forEachNode((node, attributes) => {
        const matchesType = activeFilters.types.has(attributes.type);
        const matchesStatus = activeFilters.statuses.size === 0 ||
                             !attributes.status ||
                             activeFilters.statuses.has(attributes.status);
        const matchesSearch = !activeFilters.search ||
                             attributes.label.toLowerCase().includes(activeFilters.search) ||
                             (attributes.organization && attributes.organization.toLowerCase().includes(activeFilters.search));

        const shouldShow = matchesType && matchesStatus && matchesSearch;

        graph.setNodeAttribute(node, 'hidden', !shouldShow);
    });

    // Hide edges where either node is hidden
    graph.forEachEdge((edge, attributes, source, target) => {
        const sourceHidden = graph.getNodeAttribute(source, 'hidden');
        const targetHidden = graph.getNodeAttribute(target, 'hidden');
        graph.setEdgeAttribute(edge, 'hidden', sourceHidden || targetHidden);
    });

    renderer.refresh();
    updateStats();
}

function selectNode(nodeId) {
    // Deselect previous node
    if (selectedNode) {
        graph.setNodeAttribute(selectedNode, 'color', graph.getNodeAttribute(selectedNode, 'originalColor'));
    }

    selectedNode = nodeId;
    const attributes = graph.getNodeAttributes(nodeId);

    // Highlight selected node
    graph.setNodeAttribute(nodeId, 'color', '#FF5722');

    // Show node info
    const infoDiv = document.getElementById('node-info');
    infoDiv.classList.remove('hidden');

    let html = `<h3>${attributes.label}</h3>`;
    html += `<p><strong>Type:</strong> ${attributes.type || 'N/A'}</p>`;

    if (attributes.organization) html += `<p><strong>Organization:</strong> ${attributes.organization}</p>`;
    if (attributes.title) html += `<p><strong>Title:</strong> ${attributes.title}</p>`;
    if (attributes.industry) html += `<p><strong>Industry:</strong> ${attributes.industry}</p>`;
    if (attributes.status) html += `<p><strong>Status:</strong> ${attributes.status}</p>`;
    if (attributes.priority) html += `<p><strong>Priority:</strong> ${attributes.priority}</p>`;
    if (attributes.sentiment) html += `<p><strong>Sentiment:</strong> ${attributes.sentiment}</p>`;
    if (attributes.stance) html += `<p><strong>Stance:</strong> ${attributes.stance}</p>`;
    if (attributes.relationship_type) html += `<p><strong>Relationship:</strong> ${attributes.relationship_type}</p>`;
    if (attributes.steward) html += `<p><strong>Steward:</strong> ${attributes.steward}</p>`;
    if (attributes.mentions) html += `<p><strong>Mentions:</strong> ${attributes.mentions}</p>`;

    // Show connections
    const neighbors = graph.neighbors(nodeId);
    html += `<p><strong>Connections:</strong> ${neighbors.length}</p>`;

    infoDiv.innerHTML = html;

    renderer.refresh();
}

function deselectNode() {
    if (selectedNode) {
        graph.setNodeAttribute(selectedNode, 'color', graph.getNodeAttribute(selectedNode, 'originalColor'));
        selectedNode = null;
        document.getElementById('node-info').classList.add('hidden');
        renderer.refresh();
    }
}

function updateStats() {
    const totalNodes = graph.order;
    const totalEdges = graph.size;
    let visibleNodes = 0;

    graph.forEachNode((node, attributes) => {
        if (!attributes.hidden) visibleNodes++;
    });

    document.getElementById('total-nodes').textContent = totalNodes;
    document.getElementById('total-edges').textContent = totalEdges;
    document.getElementById('visible-nodes').textContent = visibleNodes;
}
