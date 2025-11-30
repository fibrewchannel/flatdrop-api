from fastapi import APIRouter
from collections import Counter, defaultdict
from pathlib import Path
import re
import json
from typing import Optional, List, Dict, Any
from fastapi.responses import HTMLResponse


from app.schemas import BatchMoveRequest

router = APIRouter()

# Fixed imports - note the comma after VAULT_PATH and proper line continuation
from app.utils import (
    # Existing imports...
    validate_markdown, write_markdown_file, parse_yaml_frontmatter,
    fix_yaml_frontmatter, generate_obsidian_yaml, apply_tag_consolidation,
    extract_all_tags, analyze_consolidation_opportunities, create_backup_snapshot,
    CRITICAL_CONSOLIDATIONS,
    VAULT_PATH,  # Add comma here
    
    # NEW: Tesseract 4D functions
    extract_tesseract_position, calculate_memoir_priority, calculate_4d_coherence,
    find_tesseract_clusters, generate_tesseract_folder_path,
    
    # NEW: Content intelligence functions
    identify_document_archetype, extract_content_signature, count_internal_references,
    analyze_folder_content_types, measure_tag_coherence, extract_naming_patterns,
    calculate_urgency_score, group_by_archetype, generate_folder_path,
    calculate_priority, find_orphaned_files, chunked
)
# ============================================================================
# TESSERACT 4D COORDINATE SYSTEM ENDPOINTS
# ============================================================================

async def create_emergency_backup():
    """Create emergency backup before major operations"""
    try:
        backup_path = create_backup_snapshot(VAULT_PATH)
        return {
            "status": "success",
            "backup_path": str(backup_path)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/api/chunks/review-batch")
async def get_smart_review_batch(
    batch_size: int = 10,
    focus_area: str = "memoir-priority"  # memoir-priority, recovery, survival, etc.
):
    """
    Get a smart batch of chunks that need human review,
    pre-sorted by AI analysis with suggested tags
    """

    # Load chunks from training output
    training_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    all_chunks = []

    for batch_dir in (training_dir / "batch_outputs").glob("batch_*"):
        chunks_file = batch_dir / "extracted_chunks.json"
        if chunks_file.exists():
            with open(chunks_file, 'r') as f:
                all_chunks.extend(json.load(f))

    # Filter by focus area and quality threshold
    if focus_area == "memoir-priority":
        candidates = [c for c in all_chunks if c.get('quality_score', 0) >= 50]
        candidates.sort(key=lambda x: x['quality_score'], reverse=True)
    elif focus_area == "recovery":
        candidates = [c for c in all_chunks if 'recovery' in c.get('theme', '')]
    # ... other focus areas

    # Take batch
    batch = candidates[:batch_size]

    # Enrich with AI suggestions
    enriched_batch = []
    for chunk in batch:
        coords = chunk.get('coordinates', {})

        suggested_tags = generate_smart_tags(chunk)
        suggested_destination = suggest_chunk_destination(coords, chunk['quality_score'])

        enriched_batch.append({
            **chunk,
            'suggested_tags': suggested_tags,
            'suggested_destination': suggested_destination,
            'review_notes': generate_review_notes(chunk)
        })

    return {
        'batch_size': len(enriched_batch),
        'focus_area': focus_area,
        'chunks': enriched_batch,
        'remaining_count': len(candidates) - batch_size
    }

@router.get("/viz-clusters", response_class=HTMLResponse)
async def serve_cluster_visualization():
    """Serve the cluster view"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tesseract Cluster View</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            overflow-x: hidden;
        }
        
        #container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #4f9eff, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 12px;
            align-items: center;
        }
        
        .filter-group {
            flex: 1;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4f9eff;
        }
        
        select {
            width: 100%;
            padding: 10px;
            border: 2px solid rgba(79, 158, 255, 0.3);
            background: rgba(0,0,0,0.5);
            color: #fff;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid rgba(79, 158, 255, 0.2);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        #cluster-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .cluster-box {
            background: rgba(0,0,0,0.4);
            border: 2px solid rgba(79, 158, 255, 0.3);
            border-radius: 12px;
            padding: 15px;
            min-height: 250px;
            position: relative;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .cluster-box:hover {
            border-color: #4f9eff;
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(79, 158, 255, 0.2);
        }
        
        .cluster-header {
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid rgba(79, 158, 255, 0.2);
        }
        
        .cluster-key {
            font-family: 'Monaco', monospace;
            font-size: 0.85em;
            color: #ffd93d;
            margin-bottom: 8px;
            word-break: break-word;
            line-height: 1.4;
        }
        
        .cluster-count {
            font-size: 1.5em;
            font-weight: bold;
            color: #4f9eff;
        }
        
        .cluster-viz {
            position: relative;
            height: 150px;
            overflow: hidden;
        }
        
        .mini-bubble {
            position: absolute;
            border-radius: 50%;
            opacity: 0.8;
            transition: opacity 0.3s;
        }
        
        .mini-bubble:hover {
            opacity: 1;
        }
        
        .cluster-stats {
            margin-top: 10px;
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .quality-bar {
            height: 4px;
            background: rgba(79, 158, 255, 0.2);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }
        
        .quality-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f);
            border-radius: 2px;
            transition: width 0.5s ease;
        }
        
        .tooltip {
            position: fixed;
            background: rgba(0,0,0,0.95);
            border: 2px solid #4f9eff;
            border-radius: 8px;
            padding: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
            max-width: 300px;
        }
        
        .tooltip.active {
            opacity: 1;
        }
        
        .chapter-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            background: #6bcf7f;
            color: #000;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: bold;
        }
        
        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #4f9eff;
            z-index: 2000;
        }
    </style>
</head>
<body>
    <div id="container">
        <header>
            <h1>Tesseract Coordinate Clusters</h1>
            <p class="subtitle" id="chunk-count">Loading training data...</p>
            <p style="opacity: 0.8; margin-top: 10px;">Natural content groupings by 4D coordinates</p>
        </header>
        
        <div class="controls">
            <div class="filter-group">
                <label>Sort Clusters By</label>
                <select id="sort-by">
                    <option value="size">Chunk Count (Largest First)</option>
                    <option value="quality">Average Quality</option>
                    <option value="memoir">Memoir Gold Count</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Show Only</label>
                <select id="filter-purpose">
                    <option value="all">All Purposes</option>
                    <option value="tell-story">Tell My Story</option>
                    <option value="help-addict">Help Another Addict</option>
                    <option value="prevent-death">Prevent Death/Poverty</option>
                    <option value="financial-amends">Financial Amends</option>
                    <option value="help-world">Help the World</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Minimum Cluster Size</label>
                <select id="min-size">
                    <option value="1">Show All (1+)</option>
                    <option value="5">5+ chunks</option>
                    <option value="10" selected>10+ chunks (Chapter-sized)</option>
                    <option value="20">20+ chunks</option>
                    <option value="50">50+ chunks</option>
                </select>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-clusters">0</div>
                <div class="stat-label">Coordinate Clusters</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="chapter-candidates">0</div>
                <div class="stat-label">Chapter Candidates (20+)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="largest-cluster">0</div>
                <div class="stat-label">Largest Cluster</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avg-cluster-size">0</div>
                <div class="stat-label">Avg Cluster Size</div>
            </div>
        </div>
        
        <div id="cluster-grid"></div>
        
        <div class="tooltip" id="tooltip"></div>
    </div>
    
    <div class="status-indicator" id="status">Loading data...</div>
    
    <script>
        let trainingData = [];
        let clusters = {};
        const apiEndpoint = '/api/training/chunks/search?max_results=500&min_score=0';
        
        const purposeColors = {
            'tell-story': '#ff6b6b',
            'help-addict': '#4f9eff',
            'prevent-death': '#ffd93d',
            'financial-amends': '#6bcf7f',
            'help-world': '#a78bfa'
        };
        
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    trainingData = data.results.map(chunk => {
                        const coords = chunk.coordinates || {};
                        return {
                            id: chunk.chunk_id || chunk.id,
                            coordinates: {
                                x_structure: coords.x_structure || 'unknown',
                                y_transmission: coords.y_transmission || 'unknown',
                                z_purpose: coords.z_purpose || 'tell-story',
                                w_terrain: coords.w_terrain || 'complex',
                                tesseract_key: coords.tesseract_key || 'unknown'
                            },
                            quality_score: chunk.quality_score || 0,
                            theme: chunk.theme || 'unknown',
                            word_count: chunk.word_count || 0,
                            file_path: chunk.source_file || chunk.file_path || 'unknown'
                        };
                    });
                    
                    document.getElementById('status').innerHTML = 'Loaded ' + trainingData.length + ' chunks';
                    document.getElementById('chunk-count').textContent = trainingData.length + ' chunks organized into coordinate clusters';
                    setTimeout(() => document.getElementById('status').style.opacity = '0', 3000);
                    
                    buildClusters();
                    updateVisualization();
                }
            })
            .catch(error => {
                console.error('API fetch failed:', error);
                document.getElementById('status').innerHTML = 'Failed to load data';
            });
        
        function buildClusters() {
            clusters = {};
            
            trainingData.forEach(chunk => {
                const key = chunk.coordinates.tesseract_key;
                if (!clusters[key]) {
                    clusters[key] = {
                        key: key,
                        chunks: [],
                        coordinates: chunk.coordinates,
                        avgQuality: 0,
                        memoirGold: 0,
                        totalWords: 0
                    };
                }
                clusters[key].chunks.push(chunk);
            });
            
            // Calculate stats for each cluster
            Object.values(clusters).forEach(cluster => {
                cluster.avgQuality = cluster.chunks.reduce((sum, c) => sum + c.quality_score, 0) / cluster.chunks.length;
                cluster.memoirGold = cluster.chunks.filter(c => c.quality_score >= 80).length;
                cluster.totalWords = cluster.chunks.reduce((sum, c) => sum + c.word_count, 0);
            });
        }
        
        function updateVisualization() {
            const sortBy = document.getElementById('sort-by').value;
            const filterPurpose = document.getElementById('filter-purpose').value;
            const minSize = parseInt(document.getElementById('min-size').value);
            
            // Filter clusters
            let filteredClusters = Object.values(clusters).filter(cluster => {
                const matchesPurpose = filterPurpose === 'all' || cluster.coordinates.z_purpose === filterPurpose;
                const meetsMinSize = cluster.chunks.length >= minSize;
                return matchesPurpose && meetsMinSize;
            });
            
            // Sort clusters
            filteredClusters.sort((a, b) => {
                if (sortBy === 'size') return b.chunks.length - a.chunks.length;
                if (sortBy === 'quality') return b.avgQuality - a.avgQuality;
                if (sortBy === 'memoir') return b.memoirGold - a.memoirGold;
                return 0;
            });
            
            // Update stats
            document.getElementById('total-clusters').textContent = filteredClusters.length;
            document.getElementById('chapter-candidates').textContent = filteredClusters.filter(c => c.chunks.length >= 20).length;
            document.getElementById('largest-cluster').textContent = filteredClusters.length > 0 ? filteredClusters[0].chunks.length : 0;
            const avgSize = filteredClusters.reduce((sum, c) => sum + c.chunks.length, 0) / filteredClusters.length;
            document.getElementById('avg-cluster-size').textContent = avgSize ? avgSize.toFixed(1) : 0;
            
            // Render clusters
            const grid = document.getElementById('cluster-grid');
            grid.innerHTML = '';
            
            filteredClusters.forEach(cluster => {
                const box = createClusterBox(cluster);
                grid.appendChild(box);
            });
        }
        
        function createClusterBox(cluster) {
            const box = document.createElement('div');
            box.className = 'cluster-box';
            
            const isChapterCandidate = cluster.chunks.length >= 20;
            const chapterBadge = isChapterCandidate ? '<div class="chapter-indicator">CHAPTER</div>' : '';
            
            const qualityPercent = (cluster.avgQuality / 100) * 100;
            
            box.innerHTML = 
                chapterBadge +
                '<div class="cluster-header">' +
                    '<div class="cluster-key">' + cluster.key + '</div>' +
                    '<div class="cluster-count">' + cluster.chunks.length + ' chunks</div>' +
                '</div>' +
                '<div class="cluster-viz" id="viz-' + cluster.key.replace(/[^a-z0-9]/g, '_') + '"></div>' +
                '<div class="cluster-stats">' +
                    'Avg Quality: <strong>' + cluster.avgQuality.toFixed(1) + '</strong><br>' +
                    'Memoir Gold: <strong>' + cluster.memoirGold + '</strong><br>' +
                    'Total Words: <strong>' + cluster.totalWords.toLocaleString() + '</strong>' +
                '</div>' +
                '<div class="quality-bar">' +
                    '<div class="quality-fill" style="width: ' + qualityPercent + '%"></div>' +
                '</div>';
            
            box.addEventListener('click', () => showClusterDetails(cluster));
            
            // Render mini bubbles
            setTimeout(() => renderMiniBubbles(cluster), 50);
            
            return box;
        }
        
        function renderMiniBubbles(cluster) {
            const vizId = 'viz-' + cluster.key.replace(/[^a-z0-9]/g, '_');
            const container = document.getElementById(vizId);
            if (!container) return;
            
            const width = container.clientWidth;
            const height = 150;
            const color = purposeColors[cluster.coordinates.z_purpose] || '#999';
            
            // Simple force simulation for mini bubbles
            const bubbles = cluster.chunks.map((chunk, i) => {
                const size = Math.sqrt(chunk.quality_score) * 1.5 + 2;
                return {
                    x: Math.random() * width,
                    y: Math.random() * height,
                    r: size,
                    chunk: chunk
                };
            });
            
            // Simple physics iteration
            for (let i = 0; i < 50; i++) {
                bubbles.forEach((b1, idx1) => {
                    // Center attraction
                    b1.x += (width / 2 - b1.x) * 0.02;
                    b1.y += (height / 2 - b1.y) * 0.02;
                    
                    // Collision
                    bubbles.forEach((b2, idx2) => {
                        if (idx1 === idx2) return;
                        const dx = b2.x - b1.x;
                        const dy = b2.y - b1.y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        const minDist = b1.r + b2.r;
                        if (dist < minDist && dist > 0) {
                            const angle = Math.atan2(dy, dx);
                            const overlap = minDist - dist;
                            b1.x -= Math.cos(angle) * overlap * 0.5;
                            b1.y -= Math.sin(angle) * overlap * 0.5;
                        }
                    });
                    
                    // Keep in bounds
                    b1.x = Math.max(b1.r, Math.min(width - b1.r, b1.x));
                    b1.y = Math.max(b1.r, Math.min(height - b1.r, b1.y));
                });
            }
            
            // Render bubbles
            bubbles.forEach(b => {
                const bubble = document.createElement('div');
                bubble.className = 'mini-bubble';
                bubble.style.left = (b.x - b.r) + 'px';
                bubble.style.top = (b.y - b.r) + 'px';
                bubble.style.width = (b.r * 2) + 'px';
                bubble.style.height = (b.r * 2) + 'px';
                bubble.style.background = color;
                
                bubble.addEventListener('mouseenter', (e) => showBubbleTooltip(e, b.chunk));
                bubble.addEventListener('mouseleave', hideTooltip);
                
                container.appendChild(bubble);
            });
        }
        
        function showBubbleTooltip(event, chunk) {
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = 
                '<strong>Quality: ' + chunk.quality_score.toFixed(1) + '</strong><br>' +
                'Theme: ' + chunk.theme + '<br>' +
                'Words: ' + chunk.word_count;
            tooltip.style.left = event.pageX + 10 + 'px';
            tooltip.style.top = event.pageY - 10 + 'px';
            tooltip.classList.add('active');
        }
        
        function hideTooltip() {
            document.getElementById('tooltip').classList.remove('active');
        }
        
        function showClusterDetails(cluster) {
            const summary = 'Cluster: ' + cluster.key + '\\n' +
                           cluster.chunks.length + ' chunks\\n' +
                           'Avg Quality: ' + cluster.avgQuality.toFixed(1) + '\\n' +
                           'Memoir Gold: ' + cluster.memoirGold;
            alert(summary);
        }
        
        document.getElementById('sort-by').addEventListener('change', updateVisualization);
        document.getElementById('filter-purpose').addEventListener('change', updateVisualization);
        document.getElementById('min-size').addEventListener('change', updateVisualization);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@router.post("/api/process/incremental")
async def run_incremental_processing(dry_run: bool = True):
    """Run incremental processing on _inload directory"""
    SOURCE_DIR = "/Users/rickshangle/Vaults/flatline-codex/_inload"
    OUTPUT_BASE = "/Users/rickshangle/Vaults/flatline-codex"
    BACKUP_DIR = "/Users/rickshangle/Vaults/flatline-codex/_backups"
    PROCESSED_LOG = "/Users/rickshangle/Vaults/flatline-codex/_relocation_logs/processed_sources.json"
    
    processor = IncrementalProcessor(SOURCE_DIR, OUTPUT_BASE, BACKUP_DIR, PROCESSED_LOG)
    results = processor.process_new_files(dry_run=dry_run)
    
    return results



@router.get("/viz", response_class=HTMLResponse)
async def serve_tesseract_visualization():
    """Serve the Tesseract 4D visualization directly from the API (bypasses CORS)"""
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tesseract 4D Memoir Explorer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #fff;
            overflow-x: hidden;
        }
        
        #container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            padding-right: 470px; /* Space for inspector panel */
        }
        
        header {
            text-align: center;
            padding: 30px 0;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #4f9eff, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 1.1em;
            opacity: 0.8;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 12px;
        }
        
        .filter-group {
            flex: 1;
            min-width: 200px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #4f9eff;
        }
        
        select, input {
            width: 100%;
            padding: 10px;
            border: 2px solid rgba(79, 158, 255, 0.3);
            background: rgba(0,0,0,0.5);
            color: #fff;
            border-radius: 8px;
            font-size: 1em;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #4f9eff;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid rgba(79, 158, 255, 0.2);
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        #visualization {
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            border: 2px solid rgba(79, 158, 255, 0.2);
            position: relative;
            min-height: 600px;
        }
        
        .node {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .node:hover {
            stroke: #fff;
            stroke-width: 3px;
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0,0,0,0.9);
            border: 2px solid #4f9eff;
            border-radius: 8px;
            padding: 15px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 400px;
            z-index: 1000;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .tooltip.active {
            opacity: 1;
        }
        
        #inspector-panel {
            position: fixed;
            right: -450px;
            top: 0;
            width: 450px;
            height: 100vh;
            background: rgba(10,10,30,0.98);
            border-left: 3px solid #4f9eff;
            padding: 30px;
            overflow-y: auto;
            transition: right 0.3s ease;
            z-index: 3000;
            box-shadow: -5px 0 20px rgba(0,0,0,0.5);
        }
        
        #inspector-panel.active {
            right: 0;
        }
        
        #inspector-panel .close-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: transparent;
            border: 2px solid #ff6b6b;
            color: #ff6b6b;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 24px;
            line-height: 36px;
            text-align: center;
            transition: all 0.3s;
        }
        
        #inspector-panel .close-btn:hover {
            background: #ff6b6b;
            color: white;
            transform: rotate(90deg);
        }
        
        .inspector-section {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(79, 158, 255, 0.2);
        }
        
        .inspector-section:last-child {
            border-bottom: none;
        }
        
        .inspector-section h3 {
            color: #4f9eff;
            margin-bottom: 12px;
            font-size: 1.2em;
        }
        
        .quality-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .quality-high { background: #6bcf7f; color: #000; }
        .quality-medium { background: #ffd93d; color: #000; }
        .quality-low { background: #ff6b6b; color: #fff; }
        
        .coord-box {
            background: rgba(0,0,0,0.5);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 3px solid #4f9eff;
        }
        
        .content-preview {
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 8px;
            font-size: 0.95em;
            line-height: 1.6;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }
        
        .file-link {
            color: #4f9eff;
            text-decoration: none;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
            word-break: break-all;
        }
        
        .obsidian-btn {
            display: block;
            width: 100%;
            padding: 12px;
            margin-top: 15px;
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .obsidian-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(124, 58, 237, 0.4);
        }
        
        .legend {
            margin-top: 20px;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 50%;
        }
        
        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #4f9eff;
            z-index: 2000;
            transition: opacity 0.3s;
        }
    </style>
</head>
<body>
    <div id="container">
        <header>
            <h1>🎲 Tesseract 4D Memoir Explorer</h1>
            <p class="subtitle" id="chunk-count">Loading training data...</p>
            <p class="subtitle">Rick's Flatline Codex visualized across Structure × Transmission × Purpose × Terrain</p>
        </header>
        
        <div class="controls">
            <div class="filter-group">
                <label>Z-Axis: Purpose Filter</label>
                <select id="purpose-filter">
                    <option value="all">All Purposes</option>
                    <option value="tell-story">📖 Tell My Story</option>
                    <option value="help-addict">🔄 Help Another Addict</option>
                    <option value="prevent-death">⚕️ Prevent Death/Poverty</option>
                    <option value="financial-amends">💼 Financial Amends</option>
                    <option value="help-world">🌍 Help the World</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>W-Axis: Cognitive Terrain</label>
                <select id="terrain-filter">
                    <option value="all">All Terrain Types</option>
                    <option value="obvious">💡 Obvious (Clear)</option>
                    <option value="complicated">🔧 Complicated (Structured)</option>
                    <option value="complex">🧠 Complex (Thoughtful)</option>
                    <option value="chaotic">💥 Chaotic (Crisis)</option>
                    <option value="confused">❓ Confused (Mixed)</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Quality Threshold</label>
                <input type="range" id="quality-slider" min="0" max="100" value="0" step="5">
                <span id="quality-value">0</span>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-visible">0</div>
                <div class="stat-label">Visible Chunks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="avg-quality">0</div>
                <div class="stat-label">Avg Quality Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="memoir-gold">0</div>
                <div class="stat-label">Memoir Gold (80+)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="dominant-theme">Loading</div>
                <div class="stat-label">Dominant Theme</div>
            </div>
        </div>
        
        <div id="visualization"></div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #ff6b6b;"></div>
                <span>Tell My Story</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #4f9eff;"></div>
                <span>Help Addict</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffd93d;"></div>
                <span>Prevent Death</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #6bcf7f;"></div>
                <span>Financial Amends</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #a78bfa;"></div>
                <span>Help World</span>
            </div>
            <div style="margin-left: auto;">
                <strong>Click bubble</strong> to inspect | <strong>Size</strong> = Quality
            </div>
        </div>
        
        <div class="tooltip" id="tooltip"></div>
    </div>
    
    <div id="inspector-panel">
        <button class="close-btn" onclick="closeInspector()">×</button>
        <div id="inspector-content">
            <p style="text-align: center; opacity: 0.5; margin-top: 50px;">Click a bubble to inspect details</p>
        </div>
    </div>
    
    <div class="status-indicator" id="status">🔄 Loading data...</div>
    
    <script>
        let trainingData = [];
        const apiEndpoint = '/api/training/chunks/search?max_results=500&min_score=0';
        const statusEl = document.getElementById('status');
        
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                if (data.results && data.results.length > 0) {
                    trainingData = data.results.map(chunk => {
                        const coords = chunk.coordinates || {};
                        return {
                            id: chunk.chunk_id || chunk.id,
                            coordinates: {
                                x_structure: coords.x_structure || 'unknown',
                                y_transmission: coords.y_transmission || 'unknown',
                                z_purpose: coords.z_purpose || 'tell-story',
                                w_terrain: coords.w_terrain || 'complex',
                                tesseract_key: coords.tesseract_key || 'unknown'
                            },
                            quality_score: chunk.quality_score || 0,
                            theme: chunk.theme || 'unknown',
                            word_count: chunk.word_count || 0,
                            file_path: chunk.source_file || chunk.file_path || 'unknown',
                            content: chunk.content || ''
                        };
                    });
                    
                    statusEl.innerHTML = `✅ Loaded ${trainingData.length} chunks`;
                    statusEl.style.borderColor = '#6bcf7f';
                    document.getElementById('chunk-count').textContent = `${trainingData.length} chunks extracted from training`;
                    setTimeout(() => statusEl.style.opacity = '0', 3000);
                    updateVisualization();
                }
            })
            .catch(error => {
                console.error('API fetch failed:', error);
                statusEl.innerHTML = '⚠️ Failed to load data';
                statusEl.style.borderColor = '#ff6b6b';
            });
        
        const purposeColors = {
            'tell-story': '#ff6b6b',
            'help-addict': '#4f9eff',
            'prevent-death': '#ffd93d',
            'financial-amends': '#6bcf7f',
            'help-world': '#a78bfa'
        };
        
        const width = Math.min(document.getElementById('visualization').clientWidth, 1400);
        const height = 600;
        
        const svg = d3.select('#visualization')
            .append('svg')
            .attr('width', width)
            .attr('height', height);
        
        let currentData = [];
        
        function updateVisualization() {
            const purposeFilter = document.getElementById('purpose-filter').value;
            const terrainFilter = document.getElementById('terrain-filter').value;
            const qualityThreshold = +document.getElementById('quality-slider').value;
            
            currentData = trainingData.filter(d => {
                const matchesPurpose = purposeFilter === 'all' || d.coordinates.z_purpose === purposeFilter;
                const matchesTerrain = terrainFilter === 'all' || d.coordinates.w_terrain === terrainFilter;
                const matchesQuality = d.quality_score >= qualityThreshold;
                return matchesPurpose && matchesTerrain && matchesQuality;
            });
            
            document.getElementById('total-visible').textContent = currentData.length;
            const avgQuality = currentData.reduce((sum, d) => sum + d.quality_score, 0) / currentData.length;
            document.getElementById('avg-quality').textContent = avgQuality ? avgQuality.toFixed(1) : '0';
            const memoirGold = currentData.filter(d => d.quality_score >= 80).length;
            document.getElementById('memoir-gold').textContent = memoirGold;
            
            const themeCounts = {};
            currentData.forEach(d => {
                themeCounts[d.theme] = (themeCounts[d.theme] || 0) + 1;
            });
            const dominantTheme = Object.entries(themeCounts).sort((a, b) => b[1] - a[1])[0];
            document.getElementById('dominant-theme').textContent = dominantTheme ? dominantTheme[0] : 'None';
            
            const simulation = d3.forceSimulation(currentData)
                .force('charge', d3.forceManyBody().strength(-30))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(d => Math.sqrt(d.quality_score) * 2 + 5));
            
            svg.selectAll('*').remove();
            
            const nodes = svg.selectAll('.node')
                .data(currentData)
                .join('circle')
                .attr('class', 'node')
                .attr('r', d => Math.sqrt(d.quality_score) * 2 + 3)
                .attr('fill', d => purposeColors[d.coordinates.z_purpose] || '#999')
                .attr('opacity', d => {
                    const terrainOpacity = {
                        'obvious': 1.0,
                        'complicated': 0.8,
                        'complex': 0.7,
                        'chaotic': 0.5,
                        'confused': 0.3
                    };
                    return terrainOpacity[d.coordinates.w_terrain] || 0.7;
                })
                .on('mouseover', showTooltip)
                .on('mouseout', hideTooltip)
                .on('click', openInspector);
            
            simulation.on('tick', () => {
                nodes
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);
            });
        }
        
        function showTooltip(event, d) {
            const tooltip = document.getElementById('tooltip');
            const quality = d.quality_score || 0;
            const coordKey = d.coordinates?.tesseract_key || 'unknown';
            const theme = d.theme || 'unknown';
            
            tooltip.innerHTML = `
                <strong>Quality: ${quality.toFixed(1)}</strong><br>
                <span style="color: #ffd93d; font-family: Monaco; font-size: 0.9em;">${coordKey}</span><br>
                <strong>Theme:</strong> ${theme}<br>
                <em style="opacity: 0.7;">Click for full details</em>
            `;
            tooltip.style.left = (event.pageX + 10) + 'px';
            tooltip.style.top = (event.pageY - 10) + 'px';
            tooltip.classList.add('active');
        }
        
        function hideTooltip() {
            document.getElementById('tooltip').classList.remove('active');
        }
        
        function openInspector(event, d) {
            const panel = document.getElementById('inspector-panel');
            const content = document.getElementById('inspector-content');
            
            const quality = d.quality_score || 0;
            let qualityClass = 'quality-low';
            let qualityLabel = 'Low Quality';
            if (quality >= 80) {
                qualityClass = 'quality-high';
                qualityLabel = 'Memoir Gold';
            } else if (quality >= 50) {
                qualityClass = 'quality-medium';
                qualityLabel = 'Medium Quality';
            }
            
            content.innerHTML = `
                <div class="inspector-section">
                    <div class="quality-badge ${qualityClass}">${quality.toFixed(1)}</div>
                    <div style="font-size: 0.9em; opacity: 0.8;">${qualityLabel}</div>
                </div>
                
                <div class="inspector-section">
                    <h3>Tesseract Coordinates</h3>
                    <div class="coord-box">
                        <div style="color: #ffd93d; font-family: Monaco; font-size: 1.1em; margin-bottom: 12px;">
                            ${d.coordinates?.tesseract_key || 'unknown'}
                        </div>
                        <div style="font-size: 0.9em; opacity: 0.9; line-height: 1.8;">
                            <strong>X-Structure:</strong> ${d.coordinates?.x_structure || 'unknown'}<br>
                            <strong>Y-Transmission:</strong> ${d.coordinates?.y_transmission || 'unknown'}<br>
                            <strong>Z-Purpose:</strong> ${d.coordinates?.z_purpose || 'unknown'}<br>
                            <strong>W-Terrain:</strong> ${d.coordinates?.w_terrain || 'unknown'}
                        </div>
                    </div>
                </div>
                
                <div class="inspector-section">
                    <h3>Content Details</h3>
                    <div style="margin-bottom: 8px;"><strong>Theme:</strong> ${d.theme || 'unknown'}</div>
                    <div style="margin-bottom: 8px;"><strong>Word Count:</strong> ${d.word_count || 0}</div>
                    <div style="margin-bottom: 12px;"><strong>Source File:</strong><br>
                        <span class="file-link">${d.file_path || 'unknown'}</span>
                    </div>
                    <button class="obsidian-btn" onclick="openInObsidian('${d.file_path}')">
                        🔮 Open in Obsidian
                    </button>
                </div>
                
                <div class="inspector-section">
                    <h3>Content Preview</h3>
                    <div class="content-preview">${d.content || 'No preview available'}</div>
                </div>
                
                <div class="inspector-section">
                    <h3>Memoir Relevance</h3>
                    <div style="opacity: 0.9; line-height: 1.8;">
                        ${getMemoirRelevanceText(d.coordinates?.z_purpose, quality)}
                    </div>
                </div>
            `;
            
            panel.classList.add('active');
        }
        
        function closeInspector() {
            document.getElementById('inspector-panel').classList.remove('active');
        }
        
        function getMemoirRelevanceText(purpose, quality) {
            const purposeTexts = {
                'tell-story': 'CRITICAL for memoir - this is your story content',
                'help-addict': 'HIGH value - recovery narratives are central to your memoir',
                'prevent-death': 'MEDIUM value - survival context adds depth',
                'financial-amends': 'LOW direct value - but shows responsibility growth',
                'help-world': 'MEDIUM value - creative/philosophical contributions'
            };
            
            let text = purposeTexts[purpose] || 'Value unclear - review for memoir fit';
            
            if (quality >= 80) {
                text += '<br><br><strong style="color: #6bcf7f;">✨ Memoir Gold</strong> - Definitely include this!';
            } else if (quality >= 50) {
                text += '<br><br><strong style="color: #ffd93d;">Worth keeping</strong> for potential memoir use.';
            }
            
            return text;
        }
        
        function openInObsidian(filePath) {
            if (!filePath || filePath === 'unknown') {
                alert('File path not available');
                return;
            }
            
            const vaultName = 'flatline-codex';
            const encodedPath = encodeURIComponent(filePath);
            const obsidianUrl = `obsidian://open?vault=${vaultName}&file=${encodedPath}`;
            window.location.href = obsidianUrl;
        }
        
        document.getElementById('purpose-filter').addEventListener('change', updateVisualization);
        document.getElementById('terrain-filter').addEventListener('change', updateVisualization);
        document.getElementById('quality-slider').addEventListener('input', (e) => {
            document.getElementById('quality-value').textContent = e.target.value;
            updateVisualization();
        });
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=html_content)
@router.get("/api/training/summary")
async def get_training_summary():
    """Get overall training results summary from the 30-file analysis"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        # Load aggregate analysis
        summary_file = training_output_dir / "aggregate_analysis" / "training_summary.json"
        if not summary_file.exists():
            return {"error": "Training summary not found. Run training nibbler first."}
        
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
        
        # Enhance with calculated insights
        total_chunks = summary_data.get("total_chunks_extracted", 0)
        total_files = summary_data.get("total_files_analyzed", 0)
        
        return {
            "training_results": summary_data,
            "key_insights": {
                "chunks_per_file": round(total_chunks / total_files, 1) if total_files > 0 else 0,
                "processing_complexity": calculate_processing_complexity(summary_data),
                "memoir_potential": assess_memoir_potential(summary_data),
                "recommended_production_threshold": summary_data.get("threshold_recommendations", {}).get("suggested_production_threshold", 47.85)
            },
            "status": "complete",
            "training_date": summary_data.get("analysis_date", "unknown")
        }
        
    except Exception as e:
        return {"error": f"Failed to load training summary: {str(e)}"}

@router.get("/api/training/high-quality")
async def get_high_quality_chunks(
    min_score: float = 60.0,
    max_results: int = 50,
    theme_filter: Optional[str] = None
):
    """Get chunks above quality threshold, optionally filtered by theme"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        all_chunks = []
        
        # Load chunks from all batches
        batch_dirs = list((training_output_dir / "batch_outputs").glob("batch_*"))
        for batch_dir in batch_dirs:
            chunks_file = batch_dir / "extracted_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    batch_chunks = json.load(f)
                    all_chunks.extend(batch_chunks)
        
        # Filter by quality score
        high_quality = [
            chunk for chunk in all_chunks
            if chunk.get("quality_score", 0) >= min_score
        ]
        
        # Filter by theme if specified
        if theme_filter:
            high_quality = [
                chunk for chunk in high_quality
                if chunk.get("theme", "").lower() == theme_filter.lower()
            ]
        
        # Sort by quality score (highest first)
        high_quality.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        # Limit results
        high_quality = high_quality[:max_results]
        
        # Calculate statistics
        if high_quality:
            scores = [chunk.get("quality_score", 0) for chunk in high_quality]
            stats = {
                "total_found": len(high_quality),
                "score_range": [min(scores), max(scores)],
                "average_score": round(sum(scores) / len(scores), 2),
                "themes_present": list(set(chunk.get("theme", "unknown") for chunk in high_quality))
            }
        else:
            stats = {"total_found": 0, "message": "No chunks found above threshold"}
        
        return {
            "filter_criteria": {
                "min_score": min_score,
                "theme_filter": theme_filter,
                "max_results": max_results
            },
            "statistics": stats,
            "high_quality_chunks": high_quality
        }
        
    except Exception as e:
        return {"error": f"Failed to load high-quality chunks: {str(e)}"}

@router.get("/api/training/batches")
async def get_training_batches():
    """List all processed batches with summary statistics"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        batch_summaries = []
        batch_dirs = list((training_output_dir / "batch_outputs").glob("batch_*"))
        batch_dirs.sort()  # Ensure consistent ordering
        
        for batch_dir in batch_dirs:
            batch_id = batch_dir.name
            
            # Load batch statistics
            stats_file = batch_dir / "batch_stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    batch_stats = json.load(f)
                
                # Load processing log for additional details
                log_file = batch_dir / "processing_log.json"
                log_summary = {"files_processed": 0, "avg_quality": 0}
                if log_file.exists():
                    with open(log_file, 'r') as f:
                        log_data = json.load(f)
                        quality_scores = [entry.get("quality_score", 0) for entry in log_data if entry.get("quality_score")]
                        log_summary = {
                            "files_processed": len(log_data),
                            "avg_quality": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0
                        }
                
                batch_summaries.append({
                    "batch_id": batch_id,
                    "file_count": batch_stats.get("file_count", 0),
                    "chunks_extracted": batch_stats.get("total_chunks_extracted", 0),
                    "processing_date": batch_stats.get("processing_date", "unknown"),
                    "status_distribution": batch_stats.get("status_distribution", {}),
                    "quality_range": [
                        batch_stats.get("quality_distribution", {}).get("min", 0),
                        batch_stats.get("quality_distribution", {}).get("max", 0)
                    ],
                    "dominant_themes": get_top_themes(batch_stats.get("theme_distribution", {})),
                    "avg_quality": log_summary["avg_quality"]
                })
        
        return {
            "total_batches": len(batch_summaries),
            "batch_summaries": batch_summaries,
            "overall_stats": calculate_overall_batch_stats(batch_summaries)
        }
        
    except Exception as e:
        return {"error": f"Failed to load batch information: {str(e)}"}


@router.get("/api/training/batch/{batch_id}")
async def get_batch_details(batch_id: str):
    """Get detailed information about a specific batch"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    batch_dir = training_output_dir / "batch_outputs" / batch_id
    
    if not batch_dir.exists():
        return {"error": f"Batch {batch_id} not found"}
    
    try:
        batch_details = {}
        
        # Load batch statistics
        stats_file = batch_dir / "batch_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                batch_details["statistics"] = json.load(f)
        
        # Load processing log
        log_file = batch_dir / "processing_log.json"
        if log_file.exists():
            with open(log_file, 'r') as f:
                batch_details["processing_log"] = json.load(f)
        
        # Load extracted chunks
        chunks_file = batch_dir / "extracted_chunks.json"
        if chunks_file.exists():
            with open(chunks_file, 'r') as f:
                chunks_data = json.load(f)
                batch_details["extracted_chunks"] = chunks_data
                batch_details["chunk_analysis"] = analyze_batch_chunks(chunks_data)
        
        return {
            "batch_id": batch_id,
            "batch_details": batch_details,
            "files_in_batch": batch_details.get("statistics", {}).get("files_processed", [])
        }
        
    except Exception as e:
        return {"error": f"Failed to load batch {batch_id}: {str(e)}"}

@router.get("/api/training/chunks/search")
async def search_chunks(
    query: Optional[str] = None,
    theme: Optional[str] = None,
    min_score: Optional[float] = None,
    coordinate: Optional[str] = None,
    max_results: int = 100
):
    """Search training chunks with multiple filter criteria"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        all_chunks = []
        
        # Load all chunks
        batch_dirs = list((training_output_dir / "batch_outputs").glob("batch_*"))
        for batch_dir in batch_dirs:
            chunks_file = batch_dir / "extracted_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    batch_chunks = json.load(f)
                    all_chunks.extend(batch_chunks)
        
        # Apply filters
        filtered_chunks = all_chunks
        
        if min_score is not None:
            filtered_chunks = [c for c in filtered_chunks if c.get("quality_score", 0) >= min_score]
        
        if theme:
            filtered_chunks = [c for c in filtered_chunks if c.get("theme", "").lower() == theme.lower()]
        
        if coordinate:
            filtered_chunks = [c for c in filtered_chunks if coordinate in c.get("coordinates", {}).get("tesseract_key", "")]
        
        if query:
            # Simple text search in content
            query_lower = query.lower()
            filtered_chunks = [
                c for c in filtered_chunks
                if query_lower in c.get("content", "").lower()
            ]
        
        # Sort by quality score
        filtered_chunks.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        filtered_chunks = filtered_chunks[:max_results]
        
        return {
            "search_criteria": {
                "query": query,
                "theme": theme,
                "min_score": min_score,
                "coordinate": coordinate,
                "max_results": max_results
            },
            "total_found": len(filtered_chunks),
            "results": filtered_chunks
        }
        
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

@router.get("/api/training/coordinates/distribution")
async def get_coordinate_distribution():
    """Analyze distribution of Tesseract coordinates in training data"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        all_coordinates = []
        
        # Collect coordinates from all chunks
        batch_dirs = list((training_output_dir / "batch_outputs").glob("batch_*"))
        for batch_dir in batch_dirs:
            chunks_file = batch_dir / "extracted_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    chunks = json.load(f)
                    for chunk in chunks:
                        coords = chunk.get("coordinates", {})
                        if coords:
                            all_coordinates.append(coords)
        
        # Analyze distribution
        from collections import Counter
        
        structure_dist = Counter(coord.get("x_structure") for coord in all_coordinates)
        transmission_dist = Counter(coord.get("y_transmission") for coord in all_coordinates)
        purpose_dist = Counter(coord.get("z_purpose") for coord in all_coordinates)
        terrain_dist = Counter(coord.get("w_terrain") for coord in all_coordinates)
        tesseract_keys = Counter(coord.get("tesseract_key") for coord in all_coordinates)
        
        return {
            "total_coordinates": len(all_coordinates),
            "dimensional_distributions": {
                "x_structure": dict(structure_dist.most_common()),
                "y_transmission": dict(transmission_dist.most_common()),
                "z_purpose": dict(purpose_dist.most_common()),
                "w_terrain": dict(terrain_dist.most_common())
            },
            "coordinate_combinations": dict(tesseract_keys.most_common(20)),
            "4d_insights": {
                "most_common_structure": structure_dist.most_common(1)[0] if structure_dist else ("none", 0),
                "most_common_transmission": transmission_dist.most_common(1)[0] if transmission_dist else ("none", 0),
                "dominant_purpose": purpose_dist.most_common(1)[0] if purpose_dist else ("none", 0),
                "primary_terrain": terrain_dist.most_common(1)[0] if terrain_dist else ("none", 0)
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze coordinates: {str(e)}"}

@router.get("/api/training/patterns/effectiveness")
async def analyze_pattern_effectiveness():
    """Analyze which content patterns are most effective at predicting quality"""
    training_output_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    
    try:
        pattern_quality_data = []
        
        # Collect pattern data from all chunks
        batch_dirs = list((training_output_dir / "batch_outputs").glob("batch_*"))
        for batch_dir in batch_dirs:
            chunks_file = batch_dir / "extracted_chunks.json"
            if chunks_file.exists():
                with open(chunks_file, 'r') as f:
                    chunks = json.load(f)
                    for chunk in chunks:
                        patterns = chunk.get("patterns", {})
                        quality = chunk.get("quality_score", 0)
                        pattern_quality_data.append({
                            "patterns": patterns,
                            "quality": quality,
                            "theme": chunk.get("theme", "unknown")
                        })
        
        # Analyze pattern effectiveness
        pattern_analysis = {}
        
        for data in pattern_quality_data:
            for pattern_name, pattern_count in data["patterns"].items():
                if pattern_name not in pattern_analysis:
                    pattern_analysis[pattern_name] = {
                        "total_files": 0,
                        "total_quality": 0,
                        "high_quality_files": 0,
                        "avg_count_per_file": 0,
                        "total_count": 0
                    }
                
                if pattern_count > 0:  # Only count files that have this pattern
                    pattern_analysis[pattern_name]["total_files"] += 1
                    pattern_analysis[pattern_name]["total_quality"] += data["quality"]
                    pattern_analysis[pattern_name]["total_count"] += pattern_count
                    
                    if data["quality"] > 50:  # Arbitrary high quality threshold
                        pattern_analysis[pattern_name]["high_quality_files"] += 1
        
        # Calculate effectiveness metrics
        for pattern_name, stats in pattern_analysis.items():
            if stats["total_files"] > 0:
                stats["avg_quality"] = round(stats["total_quality"] / stats["total_files"], 2)
                stats["avg_count_per_file"] = round(stats["total_count"] / stats["total_files"], 2)
                stats["high_quality_ratio"] = round(stats["high_quality_files"] / stats["total_files"], 3)
                
                # Effectiveness score combines quality prediction and prevalence
                stats["effectiveness_score"] = round(
                    (stats["avg_quality"] / 100) * 0.6 +
                    stats["high_quality_ratio"] * 0.4, 3
                )
        
        # Sort by effectiveness
        effective_patterns = sorted(
            pattern_analysis.items(),
            key=lambda x: x[1].get("effectiveness_score", 0),
            reverse=True
        )
        
        return {
            "total_patterns_analyzed": len(pattern_analysis),
            "most_effective_patterns": effective_patterns[:10],
            "pattern_recommendations": generate_pattern_recommendations(effective_patterns),
            "all_pattern_stats": dict(effective_patterns)
        }
        
    except Exception as e:
        return {"error": f"Failed to analyze pattern effectiveness: {str(e)}"}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_processing_complexity(summary_data: dict) -> str:
    """Calculate how complex the processing will be based on training data"""
    status_dist = summary_data.get("processing_distribution", {})
    complex_ratio = status_dist.get("complex", 0) / sum(status_dist.values()) if status_dist else 0
    
    if complex_ratio > 0.6:
        return "high - many files need AI processing"
    elif complex_ratio > 0.3:
        return "medium - balanced mix of processing types"
    else:
        return "low - mostly simple files"

def assess_memoir_potential(summary_data: dict) -> str:
    """Assess memoir potential based on training results"""
    theme_dist = summary_data.get("theme_distribution", {})
    
    memoir_themes = theme_dist.get("ai_collaboration", 0) + theme_dist.get("recovery", 0)
    total_themes = sum(theme_dist.values()) if theme_dist else 1
    
    memoir_ratio = memoir_themes / total_themes
    
    if memoir_ratio > 0.6:
        return "high - strong memoir themes present"
    elif memoir_ratio > 0.3:
        return "medium - moderate memoir content"
    else:
        return "developing - needs more memoir-focused content"

def get_top_themes(theme_distribution: dict, limit: int = 3) -> list:
    """Get top themes from distribution"""
    if not theme_distribution:
        return []
    
    sorted_themes = sorted(theme_distribution.items(), key=lambda x: x[1], reverse=True)
    return [theme[0] for theme in sorted_themes[:limit]]

def calculate_overall_batch_stats(batch_summaries: list) -> dict:
    """Calculate overall statistics across all batches"""
    if not batch_summaries:
        return {}
    
    total_files = sum(batch.get("file_count", 0) for batch in batch_summaries)
    total_chunks = sum(batch.get("chunks_extracted", 0) for batch in batch_summaries)
    
    quality_scores = [batch.get("avg_quality", 0) for batch in batch_summaries if batch.get("avg_quality", 0) > 0]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    return {
        "total_files_processed": total_files,
        "total_chunks_extracted": total_chunks,
        "avg_chunks_per_file": round(total_chunks / total_files, 2) if total_files > 0 else 0,
        "avg_quality_across_batches": round(avg_quality, 2)
    }

def analyze_batch_chunks(chunks_data: list) -> dict:
    """Analyze chunks within a specific batch"""
    if not chunks_data:
        return {}
    
    qualities = [chunk.get("quality_score", 0) for chunk in chunks_data]
    themes = [chunk.get("theme", "unknown") for chunk in chunks_data]
    word_counts = [chunk.get("word_count", 0) for chunk in chunks_data]
    
    from collections import Counter
    theme_counter = Counter(themes)
    
    return {
        "chunk_count": len(chunks_data),
        "quality_stats": {
            "min": min(qualities) if qualities else 0,
            "max": max(qualities) if qualities else 0,
            "avg": round(sum(qualities) / len(qualities), 2) if qualities else 0
        },
        "theme_distribution": dict(theme_counter.most_common()),
        "word_count_stats": {
            "min": min(word_counts) if word_counts else 0,
            "max": max(word_counts) if word_counts else 0,
            "avg": round(sum(word_counts) / len(word_counts), 1) if word_counts else 0
        },
        "high_quality_chunks": len([q for q in qualities if q > 70])
    }

def generate_pattern_recommendations(effective_patterns: list) -> list:
    """Generate recommendations based on pattern effectiveness analysis"""
    recommendations = []
    
    if not effective_patterns:
        return ["No pattern data available for recommendations"]
    
    # Find most effective pattern
    top_pattern = effective_patterns[0]
    recommendations.append(f"'{top_pattern[0]}' is your most effective quality predictor - consider weighting it higher")
    
    # Find patterns with high quality but low prevalence
    for pattern_name, stats in effective_patterns[:5]:
        if stats.get("avg_quality", 0) > 60 and stats.get("total_files", 0) < 5:
            recommendations.append(f"'{pattern_name}' shows high quality but appears rarely - look for more content with this pattern")
    
    # Find patterns with many files but low quality
    for pattern_name, stats in effective_patterns[-3:]:
        if stats.get("total_files", 0) > 10 and stats.get("avg_quality", 0) < 30:
            recommendations.append(f"'{pattern_name}' is common but low quality - consider reducing its weight")
    
    return recommendations
    
@router.get("/api/files/content")
async def get_file_content(file_path: str):
    """Retrieve the full content of a specific file"""
    try:
        full_path = VAULT_PATH / file_path
        
        if not full_path.exists():
            return {"error": f"File not found: {file_path}"}
        
        if not full_path.is_file():
            return {"error": f"Path is not a file: {file_path}"}
            
        content = full_path.read_text(encoding="utf-8")
        
        return {
            "file_path": file_path,
            "content": content,
            "size": len(content),
            "exists": True
        }
        
    except Exception as e:
        return {"error": f"Error reading file: {str(e)}"}

# Add these updates to your existing app/routes.py file

# Update the TESSERACT_REDUNDANT_MAPPINGS to include missing coordinate-redundant tags
TESSERACT_REDUNDANT_MAPPINGS = {
    # Existing mappings...
    "flatline-codex/flatline": "REMOVE_SYSTEM_REDUNDANT",
    "flatline": "REMOVE_SYSTEM_REDUNDANT",
    
    # X-axis structure redundancies
    "protocol": "REMOVE_X_AXIS_REDUNDANT",
    "summonings": "REMOVE_X_AXIS_REDUNDANT",
    "shadowcast": "REMOVE_X_AXIS_REDUNDANT",
    "archetype": "REMOVE_X_AXIS_REDUNDANT",
    
    # MISSING TAGS DISCOVERED DURING CONSOLIDATION:
    "ritual": "REMOVE_X_AXIS_REDUNDANT",     # 13 instances - X-axis structure
    "chaos": "REMOVE_W_AXIS_REDUNDANT",      # 8 instances - W-axis terrain
    "tarot": "REMOVE_Y_AXIS_REDUNDANT",      # 7 instances - Y-axis transmission
    
    # Z-axis purpose redundancies
    "recovery": "REMOVE_Z_AXIS_REDUNDANT",
    "memoir": "REMOVE_Z_AXIS_REDUNDANT",
    "survival": "REMOVE_Z_AXIS_REDUNDANT",
    
    # Y-axis transmission redundancies
    "narrative": "REMOVE_Y_AXIS_REDUNDANT"
}

# Enhanced TECHNICAL_REMOVALS for more complete cleanup
TECHNICAL_REMOVALS = {
    # Number tags (discovered in consolidation)
    1: "REMOVE_NUMBER_TAG",
    2: "REMOVE_NUMBER_TAG",
    3: "REMOVE_NUMBER_TAG",
    4: "REMOVE_NUMBER_TAG",
    5: "REMOVE_NUMBER_TAG",
    6: "REMOVE_NUMBER_TAG",
    7: "REMOVE_NUMBER_TAG",
    8: "REMOVE_NUMBER_TAG",
    9: "REMOVE_NUMBER_TAG",
    10: "REMOVE_NUMBER_TAG",
    111: "REMOVE_NUMBER_TAG",
    222: "REMOVE_NUMBER_TAG",
    222129: "REMOVE_NUMBER_TAG",
    320: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    102: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    220: "REMOVE_NUMBER_TAG",  # Discovered in final audit
    
    # Placeholder remnants
    "REMOVE_SYSTEM_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_X_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_Y_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_Z_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    "REMOVE_W_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
    
    # Null values
    "None": "REMOVE_NULL",
    "null": "REMOVE_NULL"
}

# Enhanced FORMAT_CONSOLIDATIONS with discovered variations
FORMAT_CONSOLIDATIONS = {
    # Format variations discovered during consolidation
    "thread-dump": "threaddump",        # 15 instances → merge with threaddump (18)
    "_import": "import",                # 14 instances → merge with import (18)
    "ritual/ritual-nourishment": "ritual-nourishment",  # 10 instances
    
    # Color codes - standardize to color-HEXCODE format
    "colors/8A91C5": "color-8a91c5",
    "colors/FFA86A": "color-ffa86a",
    "colors/": "color-generic",
    "b9f5d8": "color-b9f5d8",
    "bc8d6b": "color-bc8d6b",
    "colors-0a0a23": "color-0a0a23",
    "colors-1a1a1a": "color-1a1a1a",
    "colors-47c6a6": "color-47c6a6",
    "colors-6e5ba0": "color-6e5ba0",
    "colors-80ffd3": "color-80ffd3",
    "colors-8c9b3e": "color-8c9b3e",
    "colors-a34726": "color-a34726",
    "colors-c1a837": "color-c1a837",
    
    # Case standardizations
    "UX": "ux",
    "Codex": "codex",
    "Tags": "tags",
    "AI": "ai",
    "LTR": "ltr"
}

# Add new endpoint for comprehensive final cleanup
@router.post("/api/tags/final-consolidation-cleanup")
async def final_consolidation_cleanup(dry_run: bool = True):
    """
    Comprehensive final cleanup targeting remaining issues discovered in consolidation
    Combines missing coordinate mappings + format consolidations
    """
    
    files_processed = 0
    total_changes = 0
    coordinate_removals = 0
    format_consolidations = 0
    changes_log = []
    
    # Combine all remaining cleanup mappings
    final_cleanup_mappings = {
        # Missing coordinate-redundant tags
        "ritual": "",           # Remove completely
        "chaos": "",            # Remove completely
        "tarot": "",            # Remove completely
        
        # Format consolidations
        "thread-dump": "threaddump",
        "_import": "import",
        "ritual/ritual-nourishment": "ritual-nourishment",
    }
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in final_cleanup_mappings:
                                new_value = final_cleanup_mappings[tag]
                                if new_value == "":
                                    # Remove tag completely
                                    file_changes.append(f"REMOVED: {tag}")
                                    coordinate_removals += 1
                                else:
                                    # Consolidate format
                                    updated_tags.append(new_value)
                                    file_changes.append(f"CONSOLIDATED: {tag} → {new_value}")
                                    format_consolidations += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            total_changes += len(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "coordinate_removals": coordinate_removals,
        "format_consolidations": format_consolidations,
        "total_changes": total_changes,
        "sample_changes": changes_log[:20],
        "estimated_tag_reduction": coordinate_removals + (format_consolidations // 2),
        "message": "Preview mode - no files changed" if dry_run else "Final consolidation cleanup completed"
    }

# Add endpoint to verify consolidation completion
@router.get("/api/tags/consolidation-status")
async def check_consolidation_status():
    """Check the current status of tag consolidation and identify remaining issues"""
    
    # Get current tag state
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Check for remaining consolidation targets
    remaining_coordinate_redundant = []
    remaining_format_issues = []
    remaining_technical_artifacts = []
    
    coordinate_redundant_patterns = ["ritual", "chaos", "tarot", "protocol", "archetype", "narrative", "shadowcast"]
    format_issue_patterns = ["thread-dump", "_import", "ritual/", "colors/"]
    technical_artifact_patterns = [111, 222, 320, 102, 220, "REMOVE_"]
    
    for tag, count in tag_counter.items():
        tag_str = str(tag)
        
        # Check coordinate redundancy
        if any(pattern in tag_str for pattern in coordinate_redundant_patterns):
            remaining_coordinate_redundant.append({"tag": tag, "count": count})
        
        # Check format issues
        elif any(pattern in tag_str for pattern in format_issue_patterns):
            remaining_format_issues.append({"tag": tag, "count": count})
        
        # Check technical artifacts
        elif any(str(pattern) in tag_str for pattern in technical_artifact_patterns):
            remaining_technical_artifacts.append({"tag": tag, "count": count})
    
    # Calculate consolidation completeness
    total_remaining_issues = len(remaining_coordinate_redundant) + len(remaining_format_issues) + len(remaining_technical_artifacts)
    consolidation_completeness = max(0, 100 - (total_remaining_issues * 2))  # Rough estimate
    
    return {
        "current_tag_count": len(tag_counter),
        "total_instances": sum(tag_counter.values()),
        "consolidation_completeness_percent": round(consolidation_completeness, 1),
        "remaining_issues": {
            "coordinate_redundant": remaining_coordinate_redundant,
            "format_inconsistencies": remaining_format_issues,
            "technical_artifacts": remaining_technical_artifacts
        },
        "total_remaining_issues": total_remaining_issues,
        "recommendations": [
            "Run final-consolidation-cleanup to address remaining coordinate redundancy" if remaining_coordinate_redundant else None,
            "Apply format standardization for remaining inconsistencies" if remaining_format_issues else None,
            "Clean technical artifacts with execute-technical-cleanup" if remaining_technical_artifacts else None,
            "Consolidation appears complete!" if total_remaining_issues == 0 else None
        ],
        "next_step": (
            "POST /api/tags/final-consolidation-cleanup?dry_run=false" if total_remaining_issues > 0
            else "Consolidation complete - system optimized"
        )
    }
    
@router.post("/api/tags/consolidate")
async def consolidate_tesseract_redundant_tags(dry_run: bool = True):
    """Consolidate tags that are redundant with Tesseract coordinates"""
    
    # Define Tesseract redundant tags based on your analysis
    TESSERACT_REDUNDANT_MAPPINGS = {
        # Flatline system redundancies
        "flatline-codex/flatline": "REMOVE_SYSTEM_REDUNDANT",
        "flatline": "REMOVE_SYSTEM_REDUNDANT",
        
        # X-axis structure redundancies
        "protocol": "REMOVE_X_AXIS_REDUNDANT",
        "summonings": "REMOVE_X_AXIS_REDUNDANT",
        "shadowcast": "REMOVE_X_AXIS_REDUNDANT",
        "archetype": "REMOVE_X_AXIS_REDUNDANT",
        
        # Z-axis purpose redundancies
        "recovery": "REMOVE_Z_AXIS_REDUNDANT",
        "memoir": "REMOVE_Z_AXIS_REDUNDANT",
        "survival": "REMOVE_Z_AXIS_REDUNDANT",
        
        # Y-axis transmission redundancies
        "narrative": "REMOVE_Y_AXIS_REDUNDANT"
    }
    
    files_processed = 0
    tags_removed = 0
    changes_made = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            updated_content, file_changes = apply_tag_consolidation(content, TESSERACT_REDUNDANT_MAPPINGS)
            
            if file_changes and not dry_run:
                md_file.write_text(updated_content, encoding="utf-8")
                
            files_processed += 1
            tags_removed += len(file_changes)
            changes_made.extend(file_changes)
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "estimated_tags_removed": tags_removed,
        "sample_changes": changes_made[:20],
        "total_changes": len(changes_made),
        "message": "Preview mode - no files changed" if dry_run else "Tags consolidated successfully"
    }
    
@router.post("/api/tags/consolidate-singletons")
async def consolidate_singletons(dry_run: bool = True):
    """Consolidate singleton tags into established tags for semantic compression"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons and established tags
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    established = {tag: count for tag, count in tag_counter.items() if count > 3}
    
    # Define consolidation mappings
    consolidation_map = {}
    
    # Recovery-related consolidations
    recovery_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                          for keyword in ['step', 'resentment', 'amends', 'inventory', 'spiritual'])]
    for tag in recovery_singletons:
        if 'aa' in established:
            consolidation_map[tag] = 'aa'
        elif 'recovery' in established:
            consolidation_map[tag] = 'recovery'
    
    # Emotional/psychological consolidations
    emotional_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                           for keyword in ['rage', 'grief', 'authenticity', 'validation', 'burnout'])]
    for tag in emotional_singletons:
        if 'emotion' in established:
            consolidation_map[tag] = 'emotion'
        elif 'psych' in established:
            consolidation_map[tag] = 'psych'
    
    # Technical/tool consolidations
    tech_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                      for keyword in ['api', 'python', 'code', 'system', 'tech'])]
    for tag in tech_singletons:
        if 'obsidian' in established:
            consolidation_map[tag] = 'obsidian'
        elif 'ai' in established:
            consolidation_map[tag] = 'ai'
    
    # Creative/artistic consolidations
    creative_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                          for keyword in ['art', 'music', 'creative', 'design', 'aesthetic'])]
    for tag in creative_singletons:
        if 'aiart' in established:
            consolidation_map[tag] = 'aiart'
        elif 'creative' in established:
            consolidation_map[tag] = 'creative'
    
    # Work/career consolidations
    work_singletons = [tag for tag in singletons if any(keyword in str(tag).lower()
                      for keyword in ['job', 'interview', 'resume', 'career', 'work'])]
    for tag in work_singletons:
        if 'resume' in established:
            consolidation_map[tag] = 'resume'
    
    # Apply consolidations
    files_processed = 0
    consolidations_made = 0
    changes_log = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in consolidation_map:
                                new_tag = consolidation_map[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"CONSOLIDATED: {tag} -> {new_tag}")
                                consolidations_made += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "total_singletons": len(singletons),
        "consolidation_opportunities": len(consolidation_map),
        "consolidations_made": consolidations_made,
        "sample_consolidations": changes_log[:20],
        "consolidation_groups": {
            "recovery": len(recovery_singletons),
            "emotional": len(emotional_singletons),
            "technical": len(tech_singletons),
            "creative": len(creative_singletons),
            "work": len(work_singletons)
        },
        "estimated_tag_reduction": len(consolidation_map),
        "message": "Preview mode - no consolidations applied" if dry_run else "Singleton consolidation completed"
    }
    
@router.post("/api/inload/mine-memoir-content")
async def mine_inload_memoir_content():
    """Extract memoir-worthy content from _inload directories using Tesseract analysis"""
    
    inload_analysis = {
        "high_priority_finds": [],
        "memoir_candidates": [],
        "recovery_narratives": [],
        "temporal_content": [],
        "character_development": [],
        "low_priority": []
    }
    
    files_processed = 0
    
    # Scan all _inload directories
    for inload_path in VAULT_PATH.rglob("*inload*"):
        if inload_path.is_dir():
            for md_file in inload_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    file_path_str = str(md_file.relative_to(VAULT_PATH))
                    
                    # Extract Tesseract coordinates
                    coordinates = extract_tesseract_position(content)
                    memoir_priority = calculate_memoir_priority(coordinates, content)
                    
                    file_info = {
                        "file": file_path_str,
                        "coordinates": coordinates,
                        "memoir_priority": memoir_priority,
                        "word_count": len(content.split()),
                        "has_narrative_markers": check_narrative_markers(content),
                        "temporal_indicators": extract_temporal_indicators(content),
                        "emotional_intensity": assess_emotional_content(content)
                    }
                    
                    # Categorize based on memoir value
                    if memoir_priority > 0.7:
                        inload_analysis["high_priority_finds"].append(file_info)
                    elif coordinates["z_purpose"] == "tell-story" and coordinates["y_transmission"] == "narrative":
                        inload_analysis["memoir_candidates"].append(file_info)
                    elif coordinates["z_purpose"] == "help-addict" and memoir_priority > 0.4:
                        inload_analysis["recovery_narratives"].append(file_info)
                    elif file_info["temporal_indicators"]["has_dates"] or file_info["temporal_indicators"]["has_timeline"]:
                        inload_analysis["temporal_content"].append(file_info)
                    elif file_info["has_narrative_markers"]["character_references"] > 2:
                        inload_analysis["character_development"].append(file_info)
                    else:
                        inload_analysis["low_priority"].append(file_info)
                    
                    files_processed += 1
                    
                except Exception as e:
                    print(f"Error processing {md_file}: {e}")
    
    # Generate rescue recommendations
    rescue_candidates = []
    
    # High priority files (immediate rescue)
    for file_info in inload_analysis["high_priority_finds"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "immediate",
            "reason": f"High memoir priority ({file_info['memoir_priority']:.2f})",
            "suggested_destination": generate_tesseract_folder_path(
                file_info["coordinates"]["z_purpose"],
                file_info["coordinates"]["x_structure"]
            )
        })
    
    # Strong memoir candidates
    for file_info in inload_analysis["memoir_candidates"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "high",
            "reason": "Story-focused narrative content",
            "suggested_destination": "memoir/narratives"
        })
    
    # Recovery narratives worth preserving
    for file_info in inload_analysis["recovery_narratives"]:
        rescue_candidates.append({
            "file": file_info["file"],
            "priority": "medium",
            "reason": "Recovery narrative with memoir potential",
            "suggested_destination": "memoir/recovery-narratives"
        })
    
    return {
        "files_scanned": files_processed,
        "inload_analysis": inload_analysis,
        "rescue_recommendations": rescue_candidates,
        "summary": {
            "high_priority_finds": len(inload_analysis["high_priority_finds"]),
            "memoir_candidates": len(inload_analysis["memoir_candidates"]),
            "recovery_narratives": len(inload_analysis["recovery_narratives"]),
            "total_rescue_worthy": len(rescue_candidates)
        },
        "next_steps": [
            "Review high priority finds for immediate rescue",
            "Evaluate memoir candidates for narrative value",
            "Consider recovery narratives for memoir integration",
            "Execute rescue operations in priority order"
        ]
    }

def check_narrative_markers(content: str) -> dict:
    """Check for narrative storytelling markers"""
    markers = {
        "first_person_narrative": content.lower().count("i ") + content.lower().count("me "),
        "character_references": len(re.findall(r'\b[A-Z][a-z]+\b', content)),
        "dialogue_markers": content.count('"') + content.count("'"),
        "scene_setting": any(word in content.lower() for word in ["when ", "where ", "scene", "setting"]),
        "emotional_language": sum(content.lower().count(word) for word in ["felt", "emotion", "remember", "experience"])
    }
    return markers

def extract_temporal_indicators(content: str) -> dict:
    """Extract temporal/chronological markers"""
    indicators = {
        "has_dates": bool(re.search(r'\b(19|20)\d{2}\b', content)),
        "has_timeline": any(word in content.lower() for word in ["then", "next", "after", "before", "during"]),
        "childhood_markers": any(word in content.lower() for word in ["childhood", "growing up", "as a kid"]),
        "age_references": len(re.findall(r'\b\d{1,2}\s*years?\s*old\b', content.lower())),
        "recovery_timeline": any(word in content.lower() for word in ["sobriety", "clean time", "relapse"])
    }
    return indicators

def assess_emotional_content(content: str) -> float:
    """Assess emotional intensity for memoir potential"""
    emotional_words = ["pain", "joy", "fear", "love", "anger", "hope", "despair", "peace", "rage", "grief"]
    intensity_words = ["overwhelming", "devastating", "incredible", "amazing", "terrible", "beautiful"]
    
    emotion_score = sum(content.lower().count(word) for word in emotional_words)
    intensity_score = sum(content.lower().count(word) for word in intensity_words)
    
    return min(10.0, (emotion_score + intensity_score * 2) / max(len(content.split()) / 100, 1))

@router.post("/api/tags/execute-singleton-consolidation")
async def execute_singleton_consolidation(dry_run: bool = True):
    """Execute singleton consolidation with corrected therapeutic content mapping"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    
    # Define corrected consolidation mappings
    consolidation_map = {}
    
    for tag in singletons:
        tag_str = str(tag).lower()
        
        # Therapeutic/DBT content - corrected mapping
        if 'dbt' in tag_str or 'distress-tolerance' in tag_str or 'worksheet' in tag_str:
            consolidation_map[tag] = 'dbt'
        
        # Recovery/AA content
        elif any(keyword in tag_str for keyword in ['step', 'resentment', 'amends', 'inventory', 'spiritual-practice']):
            consolidation_map[tag] = 'aa'
        
        # Emotional/psychological (non-DBT)
        elif any(keyword in tag_str for keyword in ['rage', 'grief', 'authenticity', 'validation', 'burnout']):
            consolidation_map[tag] = 'psych'
        
        # Technical/system content
        elif any(keyword in tag_str for keyword in ['api', 'python', 'code', 'system', 'flatline-codex']):
            consolidation_map[tag] = 'obsidian'
        
        # Creative/artistic content
        elif any(keyword in tag_str for keyword in ['art', 'music', 'creative', 'design', 'aesthetic']):
            consolidation_map[tag] = 'aiart'
        
        # Work/career content (but not therapy)
        elif any(keyword in tag_str for keyword in ['job', 'interview', 'resume', 'career', 'work']) and 'dbt' not in tag_str:
            consolidation_map[tag] = 'resume'
    
    # Execute consolidations
    files_processed = 0
    consolidations_made = 0
    changes_log = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            if tag in consolidation_map:
                                new_tag = consolidation_map[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"CONSOLIDATED: {tag} -> {new_tag}")
                                consolidations_made += 1
                            else:
                                updated_tags.append(tag)
                        
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_log.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "consolidations_made": consolidations_made,
        "sample_consolidations": changes_log[:20],
        "estimated_tag_reduction": len(consolidation_map),
        "message": "Preview mode" if dry_run else "Corrected singleton consolidation completed"
    }

@router.post("/api/tags/execute-technical-cleanup")
async def execute_technical_cleanup(dry_run: bool = True):
    """Execute technical cleanup: remove artifacts, standardize formats, fix case variants"""
    
    # Define technical cleanup mappings
    TECHNICAL_REMOVALS = {
        # Number tags
        1: "REMOVE_NUMBER_TAG",
        2: "REMOVE_NUMBER_TAG",
        3: "REMOVE_NUMBER_TAG",
        4: "REMOVE_NUMBER_TAG",
        5: "REMOVE_NUMBER_TAG",
        6: "REMOVE_NUMBER_TAG",
        7: "REMOVE_NUMBER_TAG",
        8: "REMOVE_NUMBER_TAG",
        9: "REMOVE_NUMBER_TAG",
        10: "REMOVE_NUMBER_TAG",
        111: "REMOVE_NUMBER_TAG",
        222: "REMOVE_NUMBER_TAG",
        222129: "REMOVE_NUMBER_TAG",
        888: "REMOVE_NUMBER_TAG",
        
        # Placeholder remnants
        "REMOVE_SYSTEM_REDUNDANT": "REMOVE_PLACEHOLDER",
        "REMOVE_X_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
        "REMOVE_Z_AXIS_REDUNDANT": "REMOVE_PLACEHOLDER",
        
        # Null values
        "None": "REMOVE_NULL",
        "null": "REMOVE_NULL"
    }
    
    # Format standardizations
    FORMAT_CONSOLIDATIONS = {
        # Color codes - standardize to color-HEXCODE format
        "colors/8A91C5": "color-8a91c5",
        "colors/FFA86A": "color-ffa86a",
        "colors/": "color-generic",
        "b9f5d8": "color-b9f5d8",
        "bc8d6b": "color-bc8d6b",
        "colors-0a0a23": "color-0a0a23",
        "colors-1a1a1a": "color-1a1a1a",
        "colors-47c6a6": "color-47c6a6",
        "colors-6e5ba0": "color-6e5ba0",
        "colors-80ffd3": "color-80ffd3",
        "colors-8c9b3e": "color-8c9b3e",
        "colors-a34726": "color-a34726",
        "colors-c1a837": "color-c1a837",
        
        # Case standardizations - choose lowercase
        "UX": "ux",
        "Codex": "codex",
        "Tags": "tags",
        "AI": "ai",
        "LTR": "ltr"
    }
    
    files_processed = 0
    total_removals = 0
    total_consolidations = 0
    changes_made = []
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        updated_tags = []
                        file_changes = []
                        
                        for tag in original_tags:
                            # Check for technical removals
                            if tag in TECHNICAL_REMOVALS:
                                file_changes.append(f"REMOVED: {tag} ({TECHNICAL_REMOVALS[tag]})")
                                total_removals += 1
                                continue  # Skip adding to updated_tags
                                
                            # Check for format consolidations
                            elif tag in FORMAT_CONSOLIDATIONS:
                                new_tag = FORMAT_CONSOLIDATIONS[tag]
                                updated_tags.append(new_tag)
                                file_changes.append(f"STANDARDIZED: {tag} -> {new_tag}")
                                total_consolidations += 1
                            else:
                                updated_tags.append(tag)
                        
                        # Apply changes if any were made
                        if file_changes:
                            yaml_data['tags'] = sorted(set(updated_tags))
                            changes_made.extend(file_changes)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "technical_removals": total_removals,
        "format_consolidations": total_consolidations,
        "total_changes": len(changes_made),
        "sample_changes": changes_made[:20],
        "estimated_tag_reduction": total_removals + (total_consolidations // 2),
        "message": "Preview mode - no files changed" if dry_run else "Technical cleanup completed successfully"
    }

@router.get("/api/tags/identify-reduction-candidates")
async def identify_tag_reduction_candidates():
    """Identify specific tags for reduction using strategic criteria"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    reduction_candidates = {
        "technical_artifacts": [],
        "format_consolidations": {},
        "over_granular": [],
        "case_variants": {},
        "low_value_singletons": [],
        "concept_duplicates": {}
    }
    
    all_tags = list(tag_counter.keys())
    
    # 1. Technical artifacts (easy removals)
    for tag in all_tags:
        tag_str = str(tag)
        if (isinstance(tag, int) or
            tag in ['null', 'None', ''] or
            tag_str.startswith('REMOVE_') or
            tag_str.isdigit()):
            reduction_candidates["technical_artifacts"].append({
                "tag": tag,
                "count": tag_counter[tag],
                "reason": "technical_artifact"
            })
    
    # 2. Format consolidations
    # Color codes
    color_tags = [tag for tag in all_tags if 'color' in str(tag).lower()]
    if len(color_tags) > 1:
        reduction_candidates["format_consolidations"]["color_codes"] = {
            "tags": color_tags,
            "suggestion": "Standardize to 'color-HEXCODE' format",
            "potential_removals": len(color_tags) - 1
        }
    
    # Ritual format variations
    ritual_tags = [tag for tag in all_tags if 'ritual' in str(tag).lower()]
    slash_rituals = [tag for tag in ritual_tags if '/' in str(tag)]
    hyphen_rituals = [tag for tag in ritual_tags if '-' in str(tag) and '/' not in str(tag)]
    if slash_rituals and hyphen_rituals:
        reduction_candidates["format_consolidations"]["ritual_separators"] = {
            "slash_format": slash_rituals,
            "hyphen_format": hyphen_rituals,
            "suggestion": "Standardize separator format",
            "potential_removals": min(len(slash_rituals), len(hyphen_rituals))
        }
    
    # 3. Case variants
    case_groups = {}
    for tag in all_tags:
        if isinstance(tag, str):
            lower_key = tag.lower()
            if lower_key not in case_groups:
                case_groups[lower_key] = []
            case_groups[lower_key].append(tag)
    
    for key, variants in case_groups.items():
        if len(variants) > 1:
            total_instances = sum(tag_counter[tag] for tag in variants)
            reduction_candidates["case_variants"][key] = {
                "variants": variants,
                "total_instances": total_instances,
                "potential_removals": len(variants) - 1
            }
    
    # 4. Over-granular tags (length and complexity)
    for tag in all_tags:
        tag_str = str(tag)
        if (len(tag_str) > 50 or
            (tag_counter[tag] == 1 and len(tag_str.split('-')) > 4) or
            ' ' in tag_str and len(tag_str.split()) > 5):
            reduction_candidates["over_granular"].append({
                "tag": tag,
                "count": tag_counter[tag],
                "length": len(tag_str),
                "reason": "overly_specific"
            })
    
    # 5. Low-value singletons (appear once, not memoir-critical)
    memoir_critical_patterns = ['nyx', 'mayo', 'rochester', 'draw-things', 'sponsor', 'therapy', 'aa', 'recovery']
    for tag in all_tags:
        if tag_counter[tag] == 1:
            tag_str = str(tag).lower()
            is_memoir_critical = any(pattern in tag_str for pattern in memoir_critical_patterns)
            is_date = any(char.isdigit() for char in tag_str) and ('202' in tag_str or 'day' in tag_str)
            
            if not is_memoir_critical and not is_date and len(tag_str) > 3:
                reduction_candidates["low_value_singletons"].append({
                    "tag": tag,
                    "reason": "singleton_not_memoir_critical"
                })
    
    # Calculate total reduction potential
    total_removals = (
        len(reduction_candidates["technical_artifacts"]) +
        sum(item.get("potential_removals", 0) for item in reduction_candidates["format_consolidations"].values()) +
        sum(item.get("potential_removals", 0) for item in reduction_candidates["case_variants"].values()) +
        len(reduction_candidates["over_granular"]) +
        len(reduction_candidates["low_value_singletons"])
    )
    
    return {
        "current_total_tags": len(all_tags),
        "target_reduction": len(all_tags) // 3,
        "identified_reduction_potential": total_removals,
        "reduction_categories": reduction_candidates,
        "meets_target": total_removals >= len(all_tags) // 3,
        "next_steps": [
            "Review technical artifacts for immediate removal",
            "Choose format standards (color codes, separators)",
            "Consolidate case variants",
            "Evaluate over-granular tags for memoir relevance",
            "Remove low-value singletons"
        ]
    }

@router.get("/api/tags/analyze-singletons")
async def analyze_singleton_tags():
    """Analyze singleton tags to categorize by value and identify cleanup opportunities"""
    
    # Get current tag counts
    tag_counter = Counter()
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception:
            continue
    
    # Identify singletons (tags appearing exactly once)
    singletons = [tag for tag, count in tag_counter.items() if count == 1]
    
    # Categorize singletons
    categorized = {
        "high_value_preservation": [],
        "format_consolidation": [],
        "cleanup_candidates": [],
        "case_variants": [],
        "technical_artifacts": []
    }
    
    for tag in singletons:
        tag_str = str(tag).lower()
        
        # High-value preservation candidates
        if any(marker in tag_str for marker in ['nyx', 'mayo', 'rochester', 'draw-things', 'sponsor', 'therapy']):
            categorized["high_value_preservation"].append(tag)
        
        # Case variants (same word, different case)
        elif any(variant in [t.lower() for t in tag_counter.keys() if t != tag] for variant in [tag_str]):
            categorized["case_variants"].append(tag)
        
        # Technical artifacts
        elif tag in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] or tag in ['null', 'None', '']:
            categorized["technical_artifacts"].append(tag)
        
        # Format inconsistencies (color codes, slashes vs hyphens)
        elif 'color' in tag_str or '/' in str(tag) or tag_str.startswith(('#', 'remove_')):
            categorized["format_consolidation"].append(tag)
        
        # Over-granular or experimental tags
        elif len(str(tag)) > 50 or '-' in str(tag) and len(str(tag).split('-')) > 5:
            categorized["cleanup_candidates"].append(tag)
        
        # Default to preservation if unclear
        else:
            categorized["high_value_preservation"].append(tag)
    
    # Generate consolidation suggestions
    consolidation_suggestions = []
    
    # Color code standardization
    color_tags = [tag for tag in tag_counter.keys() if 'color' in str(tag).lower()]
    if len(color_tags) > 1:
        consolidation_suggestions.append({
            "type": "color_standardization",
            "tags": color_tags,
            "suggestion": "Standardize to 'color-HEXCODE' format"
        })
    
    # Case variant consolidation
    case_groups = defaultdict(list)
    for tag in tag_counter.keys():
        case_groups[str(tag).lower()].append(tag)
    
    case_variants = {key: tags for key, tags in case_groups.items() if len(tags) > 1}
    for key, variants in case_variants.items():
        consolidation_suggestions.append({
            "type": "case_consolidation",
            "tags": variants,
            "suggestion": f"Consolidate to single case format"
        })
    
    return {
        "total_singletons": len(singletons),
        "categorized_singletons": {k: len(v) for k, v in categorized.items()},
        "detailed_categories": categorized,
        "consolidation_suggestions": consolidation_suggestions,
        "estimated_cleanup_impact": {
            "technical_artifacts": len(categorized["technical_artifacts"]),
            "format_consolidations": len(categorized["format_consolidation"]),
            "potential_removals": len(categorized["cleanup_candidates"])
        }
    }

@router.post("/api/tags/cleanup-placeholders")
async def cleanup_consolidation_artifacts(dry_run: bool = True):
    """Remove placeholder tags left by consolidation process"""
    
    PLACEHOLDER_REMOVALS = [
        "REMOVE_SYSTEM_REDUNDANT",
        "REMOVE_X_AXIS_REDUNDANT",
        "REMOVE_Y_AXIS_REDUNDANT",
        "REMOVE_Z_AXIS_REDUNDANT"
    ]
    
    files_processed = 0
    tags_removed = 0
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                yaml_data = parse_yaml_frontmatter(content)
                if yaml_data and 'tags' in yaml_data:
                    original_tags = yaml_data['tags']
                    if isinstance(original_tags, list):
                        # Remove placeholder tags completely
                        cleaned_tags = [tag for tag in original_tags if tag not in PLACEHOLDER_REMOVALS]
                        
                        if len(cleaned_tags) != len(original_tags):
                            yaml_data['tags'] = sorted(set(cleaned_tags))
                            tags_removed += len(original_tags) - len(cleaned_tags)
                            
                            if not dry_run:
                                lines = content.split('\n')
                                yaml_end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), -1)
                                if yaml_end > 0:
                                    new_yaml = generate_obsidian_yaml(yaml_data)
                                    updated_content = new_yaml + '\n' + '\n'.join(lines[yaml_end + 1:])
                                    md_file.write_text(updated_content, encoding="utf-8")
            
            files_processed += 1
            
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "dry_run": dry_run,
        "files_processed": files_processed,
        "placeholder_tags_removed": tags_removed,
        "message": "Preview mode" if dry_run else "Placeholders cleaned successfully"
    }

@router.get("/api/tags/audit")
async def audit_tags():
    """Comprehensive tag analysis"""
    tag_counter = Counter()
    
    # Collect all tags from all files
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            tags = extract_all_tags(md_file)
            tag_counter.update(tags)
        except Exception as e:
            print(f"Error processing {md_file}: {e}")
    
    return {
        "total_tags": len(tag_counter),
        "total_instances": sum(tag_counter.values()),
        "top_50_tags": tag_counter.most_common(50),
        "unique_tags": list(tag_counter.keys())
    }

@router.post("/api/tesseract/extract-coordinates")
async def extract_tesseract_coordinates():
    """Map entire codex into 4D Tesseract coordinate system"""
    tesseract_map = {
        "x_structure_distribution": Counter(),
        "y_transmission_distribution": Counter(),
        "z_purpose_distribution": Counter(),
        "w_terrain_distribution": Counter(),
        "coordinate_combinations": {},
        "high_dimensional_clusters": {},
        "memoir_spine_candidates": []
    }
    
    processed_files = 0
    error_files = 0
    
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            file_path_str = str(md_file.relative_to(VAULT_PATH))
            
            # Extract 4D coordinates
            coordinates = extract_tesseract_position(content)
            tesseract_map["coordinate_combinations"][file_path_str] = coordinates
            
            # Update dimensional distributions
            tesseract_map["x_structure_distribution"][coordinates["x_structure"]] += 1
            tesseract_map["y_transmission_distribution"][coordinates["y_transmission"]] += 1
            tesseract_map["z_purpose_distribution"][coordinates["z_purpose"]] += 1
            tesseract_map["w_terrain_distribution"][coordinates["w_terrain"]] += 1
            
            # Identify memoir spine candidates (high Purpose + Narrative alignment)
            if coordinates["z_purpose"] in ["tell-story", "help-addict"] and coordinates["y_transmission"] == "narrative":
                memoir_priority = calculate_memoir_priority(coordinates, content)
                tesseract_map["memoir_spine_candidates"].append({
                    "file": file_path_str,
                    "coordinates": coordinates,
                    "memoir_priority": memoir_priority
                })
            
            processed_files += 1
            
            # Progress tracking
            if processed_files % 50 == 0:
                print(f"Processed {processed_files} files into 4D space...")
                
        except Exception as e:
            error_files += 1
            print(f"Error processing {md_file}: {e}")
    
    # Find high-dimensional clusters
    tesseract_map["high_dimensional_clusters"] = find_tesseract_clusters(tesseract_map)
    
    # Calculate 4D statistics
    total_coordinates = len(tesseract_map["coordinate_combinations"])
    unique_tesseract_keys = len(set(
        coords["tesseract_key"] for coords in tesseract_map["coordinate_combinations"].values()
    ))
    
    return {
        "tesseract_analysis_summary": {
            "total_files_mapped": processed_files,
            "processing_errors": error_files,
            "unique_4d_coordinates": unique_tesseract_keys,
            "coordinate_density": round(unique_tesseract_keys / total_coordinates, 3) if total_coordinates > 0 else 0
        },
        "dimensional_distributions": {
            "x_structure": dict(tesseract_map["x_structure_distribution"].most_common()),
            "y_transmission": dict(tesseract_map["y_transmission_distribution"].most_common()),
            "z_purpose": dict(tesseract_map["z_purpose_distribution"].most_common()),
            "w_terrain": dict(tesseract_map["w_terrain_distribution"].most_common())
        },
        "memoir_spine_analysis": {
            "total_candidates": len(tesseract_map["memoir_spine_candidates"]),
            "high_priority_spine": [
                candidate for candidate in tesseract_map["memoir_spine_candidates"]
                if candidate["memoir_priority"] > 0.7
            ][:20]
        },
        "4d_clusters": tesseract_map["high_dimensional_clusters"],
        "coordinate_combinations": tesseract_map["coordinate_combinations"],
        "tesseract_insights": [
            f"Most common structure: {tesseract_map['x_structure_distribution'].most_common(1)[0][0] if tesseract_map['x_structure_distribution'] else 'none'}",
            f"Primary transmission mode: {tesseract_map['y_transmission_distribution'].most_common(1)[0][0] if tesseract_map['y_transmission_distribution'] else 'none'}",
            f"Dominant life purpose: {tesseract_map['z_purpose_distribution'].most_common(1)[0][0] if tesseract_map['z_purpose_distribution'] else 'none'}",
            f"Most common cognitive terrain: {tesseract_map['w_terrain_distribution'].most_common(1)[0][0] if tesseract_map['w_terrain_distribution'] else 'none'}"
        ]
    }

@router.get("/api/tesseract/analyze-4d-structure")
async def analyze_tesseract_structure():
    """Analyze current folder structure through Tesseract lens"""
    tesseract_analysis = {
        "dimensional_coherence": {},
        "coordinate_clusters": {},
        "organizational_gaps": {},
        "memoir_readiness_by_purpose": {},
        "4d_reorganization_opportunities": []
    }
    
    # Get current tesseract mapping
    try:
        tesseract_map_result = await extract_tesseract_coordinates()
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "z_purpose_distribution": Counter(tesseract_map_result["dimensional_distributions"]["z_purpose"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
    except Exception as e:
        return {"error": f"Failed to extract Tesseract coordinates: {str(e)}"}
    
    processed_folders = 0
    
    for folder_path in VAULT_PATH.rglob("*"):
        if folder_path.is_dir() and not folder_path.name.startswith('.'):
            md_files = list(folder_path.glob("*.md"))
            if md_files:
                
                # Analyze 4D coherence within folder
                folder_coordinates = []
                for md_file in md_files:
                    file_key = str(md_file.relative_to(VAULT_PATH))
                    if file_key in tesseract_map["coordinate_combinations"]:
                        folder_coordinates.append(tesseract_map["coordinate_combinations"][file_key])
                
                coherence_score = calculate_4d_coherence(folder_coordinates)
                dominant_coordinates = find_dominant_4d_pattern(folder_coordinates)
                
                folder_key = str(folder_path.relative_to(VAULT_PATH))
                tesseract_analysis["dimensional_coherence"][folder_key] = {
                    "file_count": len(md_files),
                    "4d_coherence_score": coherence_score,
                    "dominant_pattern": dominant_coordinates,
                    "scatter_analysis": analyze_coordinate_scatter(folder_coordinates),
                    "reorganization_urgency": calculate_4d_urgency(coherence_score, len(md_files))
                }
                
                processed_folders += 1
    
    # Identify cross-dimensional clusters that should be grouped
    tesseract_analysis["coordinate_clusters"] = tesseract_map_result["4d_clusters"]
    
    # Find gaps in memoir structure
    tesseract_analysis["memoir_readiness_by_purpose"] = assess_memoir_completeness_by_purpose(tesseract_map)
    
    return {
        "analysis_summary": {
            "folders_analyzed": processed_folders,
            "avg_4d_coherence": calculate_avg_coherence(tesseract_analysis["dimensional_coherence"]),
            "high_coherence_folders": len([
                f for f in tesseract_analysis["dimensional_coherence"].values()
                if f["4d_coherence_score"] > 0.7
            ])
        },
        "tesseract_structure_analysis": tesseract_analysis,
        "reorganization_recommendations": generate_4d_reorganization_recommendations(tesseract_analysis)
    }

def find_dominant_4d_pattern(coordinates_list: list) -> dict:
    """Find the dominant coordinate pattern in a folder"""
    if not coordinates_list:
        return {}
    
    # Count occurrences of each dimension value
    structure_counter = Counter(coord["x_structure"] for coord in coordinates_list)
    transmission_counter = Counter(coord["y_transmission"] for coord in coordinates_list)
    purpose_counter = Counter(coord["z_purpose"] for coord in coordinates_list)
    terrain_counter = Counter(coord["w_terrain"] for coord in coordinates_list)
    
    return {
        "dominant_structure": structure_counter.most_common(1)[0][0] if structure_counter else "none",
        "dominant_transmission": transmission_counter.most_common(1)[0][0] if transmission_counter else "none",
        "dominant_purpose": purpose_counter.most_common(1)[0][0] if purpose_counter else "none",
        "dominant_terrain": terrain_counter.most_common(1)[0][0] if terrain_counter else "none",
        "pattern_strength": {
            "structure": structure_counter.most_common(1)[0][1] / len(coordinates_list) if structure_counter else 0,
            "transmission": transmission_counter.most_common(1)[0][1] / len(coordinates_list) if transmission_counter else 0,
            "purpose": purpose_counter.most_common(1)[0][1] / len(coordinates_list) if purpose_counter else 0,
            "terrain": terrain_counter.most_common(1)[0][1] / len(coordinates_list) if terrain_counter else 0
        }
    }

def analyze_coordinate_scatter(coordinates_list: list) -> dict:
    """Analyze how scattered coordinates are across 4D space"""
    if not coordinates_list:
        return {"scatter_score": 0, "analysis": "No coordinates to analyze"}
    
    total_files = len(coordinates_list)
    
    # Count unique values in each dimension
    unique_structures = len(set(coord["x_structure"] for coord in coordinates_list))
    unique_transmissions = len(set(coord["y_transmission"] for coord in coordinates_list))
    unique_purposes = len(set(coord["z_purpose"] for coord in coordinates_list))
    unique_terrains = len(set(coord["w_terrain"] for coord in coordinates_list))
    
    # Calculate scatter (higher = more scattered)
    scatter_score = (unique_structures + unique_transmissions + unique_purposes + unique_terrains) / (4 * total_files)
    
    return {
        "scatter_score": round(scatter_score, 3),
        "dimension_variety": {
            "structures": unique_structures,
            "transmissions": unique_transmissions,
            "purposes": unique_purposes,
            "terrains": unique_terrains
        },
        "scatter_assessment": (
            "highly_scattered" if scatter_score > 0.75 else
            "moderately_scattered" if scatter_score > 0.5 else
            "somewhat_coherent" if scatter_score > 0.25 else
            "highly_coherent"
        )
    }

def calculate_4d_urgency(coherence_score: float, file_count: int) -> float:
    """Calculate reorganization urgency based on 4D coherence and impact"""
    # Low coherence = high urgency
    coherence_urgency = 1.0 - coherence_score
    
    # More files = higher impact, thus higher urgency
    impact_urgency = min(1.0, file_count / 50)  # Normalize around 50 files
    
    # Combine factors
    overall_urgency = (coherence_urgency * 0.7) + (impact_urgency * 0.3)
    
    return round(overall_urgency, 3)

def assess_memoir_completeness_by_purpose(tesseract_map: dict) -> dict:
    """Assess memoir readiness across Rick's 5 core purposes"""
    purpose_analysis = {}
    
    for purpose in ["tell-story", "help-addict", "prevent-death-poverty", "financial-amends", "help-world"]:
        purpose_files = [
            file_path for file_path, coords in tesseract_map["coordinate_combinations"].items()
            if coords["z_purpose"] == purpose
        ]
        
        # Analyze transmission modes for this purpose
        transmission_counts = Counter()
        terrain_counts = Counter()
        
        for file_path in purpose_files:
            coords = tesseract_map["coordinate_combinations"][file_path]
            transmission_counts[coords["y_transmission"]] += 1
            terrain_counts[coords["w_terrain"]] += 1
        
        purpose_analysis[purpose] = {
            "total_files": len(purpose_files),
            "narrative_files": transmission_counts.get("narrative", 0),
            "transmission_diversity": len(transmission_counts),
            "cognitive_terrains": dict(terrain_counts),
            "memoir_readiness": calculate_purpose_memoir_readiness(purpose, transmission_counts, terrain_counts),
            "sample_files": purpose_files[:10]
        }
    
    return purpose_analysis

def calculate_purpose_memoir_readiness(purpose: str, transmission_counts: Counter, terrain_counts: Counter) -> dict:
    """Calculate memoir readiness for each life purpose"""
    narrative_count = transmission_counts.get("narrative", 0)
    total_files = sum(transmission_counts.values())
    
    # Different purposes have different memoir requirements
    purpose_weights = {
        "tell-story": {"narrative_importance": 0.8, "min_files": 20},
        "help-addict": {"narrative_importance": 0.6, "min_files": 15},
        "prevent-death-poverty": {"narrative_importance": 0.4, "min_files": 10},
        "financial-amends": {"narrative_importance": 0.3, "min_files": 5},
        "help-world": {"narrative_importance": 0.5, "min_files": 10}
    }
    
    weights = purpose_weights.get(purpose, {"narrative_importance": 0.5, "min_files": 10})
    
    # Calculate readiness score
    volume_score = min(1.0, total_files / weights["min_files"])
    narrative_ratio = narrative_count / total_files if total_files > 0 else 0
    narrative_score = narrative_ratio * weights["narrative_importance"]
    
    # Bonus for diverse cognitive terrains (shows depth)
    terrain_diversity = len(terrain_counts) / 5  # Max 5 terrain types
    
    overall_readiness = (volume_score + narrative_score + terrain_diversity * 0.2) / 2
    
    return {
        "readiness_score": round(overall_readiness, 3),
        "volume_score": round(volume_score, 3),
        "narrative_score": round(narrative_score, 3),
        "narrative_percentage": round(narrative_ratio * 100, 1),
        "recommendations": generate_purpose_recommendations(purpose, volume_score, narrative_score, terrain_counts)
    }

def generate_purpose_recommendations(purpose: str, volume_score: float, narrative_score: float, terrain_counts: Counter) -> list:
    """Generate specific recommendations for improving purpose-based memoir readiness"""
    recommendations = []
    
    if volume_score < 0.5:
        recommendations.append(f"Need more content for '{purpose}' - aim for more documents in this area")
    
    if narrative_score < 0.4:
        recommendations.append(f"Convert more '{purpose}' content to narrative format for memoir use")
    
    if len(terrain_counts) < 2:
        recommendations.append(f"Add emotional depth - explore '{purpose}' across different cognitive terrains")
    
    # Purpose-specific recommendations
    purpose_specific = {
        "tell-story": ["Focus on chronological narrative", "Add more personal details and memories"],
        "help-addict": ["Include specific recovery experiences", "Document sponsor relationships and meeting insights"],
        "prevent-death-poverty": ["Chronicle health challenges and housing struggles", "Document practical survival strategies"],
        "financial-amends": ["Detail work history and financial recovery", "Include specific amends and responsibility steps"],
        "help-world": ["Connect creative work to larger purpose", "Document how systems and tools help others"]
    }
    
    recommendations.extend(purpose_specific.get(purpose, []))
    
    return recommendations

def calculate_avg_coherence(dimensional_coherence: dict) -> float:
    """Calculate average 4D coherence across all folders"""
    if not dimensional_coherence:
        return 0.0
    
    coherence_scores = [folder["4d_coherence_score"] for folder in dimensional_coherence.values()]
    return round(sum(coherence_scores) / len(coherence_scores), 3)

def generate_4d_reorganization_recommendations(tesseract_analysis: dict) -> list:
    """Generate specific 4D reorganization recommendations"""
    recommendations = []
    
    # Analyze coherence issues
    low_coherence_folders = [
        (folder_name, folder_data) for folder_name, folder_data in tesseract_analysis["dimensional_coherence"].items()
        if folder_data["4d_coherence_score"] < 0.5 and folder_data["file_count"] > 5
    ]
    
    if low_coherence_folders:
        recommendations.append({
            "type": "coherence_improvement",
            "priority": "high",
            "description": f"Reorganize {len(low_coherence_folders)} folders with low 4D coherence",
            "affected_folders": [folder[0] for folder in low_coherence_folders[:10]],
            "impact": "Significantly improved findability and memoir structure"
        })
    
    # Analyze cluster opportunities
    significant_clusters = [
        cluster for cluster in tesseract_analysis["coordinate_clusters"].values()
        if len(cluster) > 10
    ]
    
    if significant_clusters:
        recommendations.append({
            "type": "cluster_consolidation",
            "priority": "medium",
            "description": f"Consolidate {len(significant_clusters)} major 4D clusters into coherent folders",
            "cluster_count": len(significant_clusters),
            "impact": "Natural groupings based on Tesseract coordinates"
        })
    
    # Memoir-specific recommendations
    memoir_readiness = tesseract_analysis.get("memoir_readiness_by_purpose", {})
    low_readiness_purposes = [
        purpose for purpose, data in memoir_readiness.items()
        if data.get("memoir_readiness", {}).get("readiness_score", 0) < 0.5
    ]
    
    if low_readiness_purposes:
        recommendations.append({
            "type": "memoir_development",
            "priority": "critical",
            "description": f"Develop memoir content for purposes: {', '.join(low_readiness_purposes)}",
            "purposes_needing_work": low_readiness_purposes,
            "impact": "Essential for memoir production readiness"
        })
    
    return recommendations

@router.post("/api/tesseract/suggest-reorganization")
async def suggest_tesseract_reorganization(
    focus_purpose: str = "all",  # tell-story, help-addict, prevent-death-poverty, financial-amends, help-world, all
    consolidation_threshold: int = 5,
    memoir_priority: bool = True
):
    """Generate 4D Tesseract-aware reorganization suggestions"""
    
    # Get current 4D analysis
    try:
        tesseract_structure_result = await analyze_tesseract_structure()
        tesseract_map_result = await extract_tesseract_coordinates()
        
        tesseract_structure = tesseract_structure_result["tesseract_structure_analysis"]
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "z_purpose_distribution": Counter(tesseract_map_result["dimensional_distributions"]["z_purpose"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
    except Exception as e:
        return {"error": f"Failed to analyze Tesseract structure: {str(e)}"}
    
    suggestions = []
    
    # Primary suggestion: Organize by Purpose + Structure (Z + X dimensions)
    purpose_structure_groups = defaultdict(list)
    for file_path, coords in tesseract_map["coordinate_combinations"].items():
        if focus_purpose == "all" or coords["z_purpose"] == focus_purpose:
            group_key = f"{coords['z_purpose']}/{coords['x_structure']}"
            purpose_structure_groups[group_key].append({
                "file": file_path,
                "coordinates": coords
            })
    
    # Generate suggestions for each significant group
    for group_key, files in purpose_structure_groups.items():
        if len(files) >= consolidation_threshold:
            purpose, structure = group_key.split('/')
            
            suggestions.append({
                "action": "create_tesseract_folder",
                "group_key": group_key,
                "purpose": purpose,
                "structure": structure,
                "total_files": len(files),
                "suggested_path": generate_tesseract_folder_path(purpose, structure),
                "memoir_relevance": assess_memoir_relevance(purpose, structure),
                "priority": calculate_tesseract_priority(purpose, structure, len(files), memoir_priority),
                "4d_coherence": calculate_group_coherence(files),
                "sample_files": [f["file"] for f in files[:5]]
            })
    
    # Special memoir spine suggestion
    memoir_spine = identify_memoir_spine_structure(tesseract_map)
    if memoir_spine:
        suggestions.append({
            "action": "create_memoir_spine",
            "structure": memoir_spine,
            "priority": "critical",
            "memoir_relevance": "essential - creates narrative backbone"
        })
    
    # Identify 4D orphans (files scattered across dimensions)
    orphaned_files = find_4d_orphans(tesseract_structure)
    if orphaned_files:
        suggestions.append({
            "action": "consolidate_4d_orphans",
            "total_orphaned": len(orphaned_files),
            "suggested_target_path": "_tesseract-inbox/needs-classification",
            "priority": "medium",
            "rationale": "Files scattered across 4D space need dimensional alignment"
        })
    
    return {
        "focus_purpose": focus_purpose,
        "tesseract_suggestions": suggestions,
        "4d_analysis_summary": {
            "total_coordinates": len(tesseract_map["coordinate_combinations"]),
            "purpose_distribution": dict(tesseract_map["z_purpose_distribution"]),
            "memoir_spine_candidates": len(tesseract_map["memoir_spine_candidates"])
        },
        "recommended_folder_structure": generate_tesseract_folder_structure(),
        "implementation_phases": [
            "Phase 1: Create memoir spine (tell-story + narrative)",
            "Phase 2: Consolidate recovery content (help-addict purpose)",
            "Phase 3: Organize by remaining purposes",
            "Phase 4: Fine-tune by cognitive terrain (W-dimension)"
        ]
    }

def assess_memoir_relevance(purpose: str, structure: str) -> str:
    """Assess memoir relevance based on Tesseract coordinates"""
    
    # Purpose-based memoir relevance
    purpose_relevance = {
        "tell-story": "critical",
        "help-addict": "high",
        "prevent-death-poverty": "medium",
        "financial-amends": "low",
        "help-world": "medium"
    }
    
    # Structure-based memoir relevance
    structure_relevance = {
        "archetype": "high",  # Character development
        "protocol": "medium", # Life systems
        "shadowcast": "high", # Emotional depth
        "expansion": "low",   # Background material
        "summoning": "medium" # Pivotal moments
    }
    
    base_relevance = purpose_relevance.get(purpose, "low")
    structure_modifier = structure_relevance.get(structure, "medium")
    
    # Combine ratings
    if base_relevance == "critical":
        return "critical"
    elif base_relevance == "high" or structure_modifier == "high":
        return "high"
    elif base_relevance == "medium" or structure_modifier == "medium":
        return "medium"
    else:
        return "low"

def calculate_tesseract_priority(purpose: str, structure: str, file_count: int, memoir_priority: bool) -> str:
    """Calculate reorganization priority using Tesseract coordinates"""
    
    base_score = 0
    
    # Purpose-based priority
    purpose_scores = {
        "tell-story": 5,
        "help-addict": 4,
        "prevent-death-poverty": 3,
        "financial-amends": 2,
        "help-world": 3
    }
    base_score += purpose_scores.get(purpose, 1)
    
    # Structure-based priority
    structure_scores = {
        "archetype": 3,
        "protocol": 2,
        "shadowcast": 3,
        "expansion": 1,
        "summoning": 2
    }
    base_score += structure_scores.get(structure, 1)
    
    # File count impact
    if file_count > 20:
        base_score += 2
    elif file_count > 10:
        base_score += 1
    
    # Memoir priority boost
    if memoir_priority and purpose in ["tell-story", "help-addict"]:
        base_score += 2
    
    # Convert to priority level
    if base_score >= 8:
        return "critical"
    elif base_score >= 6:
        return "high"
    elif base_score >= 4:
        return "medium"
    else:
        return "low"

def calculate_group_coherence(files: list) -> float:
    """Calculate coherence for a group of files with same coordinates"""
    if not files:
        return 0.0
    
    # Files in same coordinate group should have high coherence by definition
    # But we can measure consistency in related metadata
    
    coordinates_list = [f["coordinates"] for f in files]
    return calculate_4d_coherence(coordinates_list)

def identify_memoir_spine_structure(tesseract_map: dict) -> dict:
    """Identify the core memoir structure from Tesseract analysis"""
    
    spine_candidates = tesseract_map.get("memoir_spine_candidates", [])
    
    if len(spine_candidates) < 10:
        return None
    
    # Organize spine by cognitive terrain (W-dimension) for emotional flow
    terrain_organization = defaultdict(list)
    for candidate in spine_candidates:
        terrain = candidate["coordinates"]["w_terrain"]
        terrain_organization[terrain].append(candidate)
    
    # Suggested memoir spine structure
    return {
        "total_spine_files": len(spine_candidates),
        "suggested_structure": {
            "memoir/spine/foundations/": f"Complex terrain files ({len(terrain_organization.get('complex', []))} files)",
            "memoir/spine/crisis/": f"Chaotic terrain files ({len(terrain_organization.get('chaotic', []))} files)",
            "memoir/spine/recovery/": f"Complicated terrain files ({len(terrain_organization.get('complicated', []))} files)",
            "memoir/spine/integration/": f"Obvious terrain files ({len(terrain_organization.get('obvious', []))} files)",
            "memoir/spine/fragments/": f"Confused terrain files ({len(terrain_organization.get('confused', []))} files)"
        },
        "terrain_files": dict(terrain_organization),
        "emotional_flow_rationale": "Organized by cognitive terrain for natural memoir progression"
    }

def find_4d_orphans(tesseract_structure: dict) -> list:
    """Find files that are scattered across 4D space without clear groupings"""
    orphans = []
    
    # Look for folders with very low coherence and high scatter
    for folder_name, folder_data in tesseract_structure.get("dimensional_coherence", {}).items():
        if (folder_data["4d_coherence_score"] < 0.3 and
            folder_data.get("scatter_analysis", {}).get("scatter_score", 0) > 0.7):
            orphans.append({
                "folder": folder_name,
                "file_count": folder_data["file_count"],
                "coherence_issue": "high_scatter",
                "scatter_score": folder_data.get("scatter_analysis", {}).get("scatter_score", 0)
            })
    
    return orphans

def generate_tesseract_folder_structure() -> dict:
    """Generate complete Tesseract-native folder structure for Rick's codex"""
    return {
        "memoir/": {
            "description": "Tell My Story - Primary memoir content",
            "subfolders": {
                "spine/": "Core narrative backbone organized by cognitive terrain",
                "personas/": "Archetype-based character studies and identity work",
                "practices/": "Protocol-based recovery and life management routines",
                "explorations/": "Shadowcast emotional fragments and mood pieces",
                "context/": "Expansion background and supporting material"
            }
        },
        "recovery/": {
            "description": "Help Another Addict - AA and recovery focused content",
            "subfolders": {
                "practices/": "Step work, sponsor work, meeting protocols",
                "personas/": "Recovery archetypes (sponsor, sponsee, group member)",
                "explorations/": "Emotional recovery work, inventory, amends prep",
                "activations/": "Summoning recovery energy, centering practices"
            }
        },
        "survival/": {
            "description": "Prevent Death/Poverty - Medical, housing, practical life",
            "subfolders": {
                "medical/": "Mayo clinic, health management, treatment protocols",
                "housing/": "Sober house, homelessness preparation, practical survival",
                "systems/": "Benefits, insurance, practical life management"
            }
        },
        "work-amends/": {
            "description": "Financial Amends - Employment, income, responsibility",
            "subfolders": {
                "job-search/": "Employment seeking, interviews, opportunities",
                "skills/": "Technical abilities, creative work, professional development",
                "planning/": "Financial recovery, debt management, future planning"
            }
        },
        "contribution/": {
            "description": "Help the World - Creative work, systems, tools",
            "subfolders": {
                "creative/": "AI art, music, comedy, creative expression",
                "systems/": "Technical tools, APIs, helpful systems",
                "philosophy/": "Wisdom, insights, contributions to understanding"
            }
        },
        "_tesseract-meta/": {
            "description": "Tesseract system files and coordinate mappings",
            "subfolders": {
                "coordinates/": "4D mapping files and analysis",
                "inbox/": "New content awaiting coordinate assignment",
                "templates/": "Tesseract-aware document templates"
            }
        }
    }

@router.get("/api/tesseract/memoir-readiness")
async def assess_tesseract_memoir_readiness():
    """Comprehensive memoir readiness assessment using 4D Tesseract analysis"""
    
    try:
        tesseract_map_result = await extract_tesseract_coordinates()
        tesseract_structure_result = await analyze_tesseract_structure()
        
        tesseract_map = {
            "coordinate_combinations": tesseract_map_result["coordinate_combinations"],
            "x_structure_distribution": Counter(tesseract_map_result["dimensional_distributions"]["x_structure"]),
            "y_transmission_distribution": Counter(tesseract_map_result["dimensional_distributions"]["y_transmission"]),
            "w_terrain_distribution": Counter(tesseract_map_result["dimensional_distributions"]["w_terrain"]),
            "memoir_spine_candidates": tesseract_map_result["memoir_spine_analysis"]["high_priority_spine"]
        }
        
        tesseract_structure = tesseract_structure_result["tesseract_structure_analysis"]
        
    except Exception as e:
        return {"error": f"Failed to analyze Tesseract memoir readiness: {str(e)}"}
    
    # Core memoir analysis
    memoir_analysis = {
        "overall_4d_readiness": 0,
        "dimensional_scores": {},
        "narrative_spine_strength": 0,
        "purpose_coverage": {},
        "cognitive_terrain_balance": {},
        "production_recommendations": []
    }
    
    # X-Dimension Analysis: Structure readiness
    structure_dist = tesseract_map["x_structure_distribution"]
    memoir_analysis["dimensional_scores"]["x_structure"] = {
        "archetype_content": structure_dist.get("archetype", 0),
        "protocol_systems": structure_dist.get("protocol", 0),
        "shadowcast_depth": structure_dist.get("shadowcast", 0),
        "narrative_readiness": calculate_structure_memoir_readiness(structure_dist)
    }
    
    # Y-Dimension Analysis: Transmission readiness
    transmission_dist = tesseract_map["y_transmission_distribution"]
    memoir_analysis["dimensional_scores"]["y_transmission"] = {
        "narrative_content": transmission_dist.get("narrative", 0),
        "total_content": sum(transmission_dist.values()),
        "narrative_percentage": transmission_dist.get("narrative", 0) / max(sum(transmission_dist.values()), 1) * 100,
        "transmission_readiness": calculate_transmission_memoir_readiness(transmission_dist)
    }
    
    # Z-Dimension Analysis: Purpose coverage (Rick's 5 core intents)
    purpose_coverage = tesseract_structure.get("memoir_readiness_by_purpose", {})
    memoir_analysis["purpose_coverage"] = purpose_coverage
    
    # Calculate overall purpose readiness
    purpose_scores = [data.get("memoir_readiness", {}).get("readiness_score", 0) for data in purpose_coverage.values()]
    avg_purpose_readiness = sum(purpose_scores) / len(purpose_scores) if purpose_scores else 0
    
    # W-Dimension Analysis: Cognitive terrain balance
    terrain_dist = tesseract_map["w_terrain_distribution"]
    memoir_analysis["cognitive_terrain_balance"] = {
        "terrain_distribution": dict(terrain_dist),
        "emotional_range": len(terrain_dist),  # More terrains = richer emotional content
        "chaos_integration": terrain_dist.get("chaotic", 0),  # Important for trauma memoir
        "complexity_depth": terrain_dist.get("complex", 0),   # Shows thoughtful processing
        "terrain_readiness": calculate_terrain_memoir_readiness(terrain_dist)
    }
    
    # Narrative spine analysis
    spine_candidates = tesseract_map["memoir_spine_candidates"]
    spine_strength = len([c for c in spine_candidates if c.get("memoir_priority", 0) > 0.6])
    memoir_analysis["narrative_spine_strength"] = spine_strength / max(len(spine_candidates), 1) if spine_candidates else 0
    
    # Calculate overall 4D readiness
    structure_score = memoir_analysis["dimensional_scores"]["x_structure"]["narrative_readiness"]
    transmission_score = memoir_analysis["dimensional_scores"]["y_transmission"]["transmission_readiness"]
    purpose_score = avg_purpose_readiness
    terrain_score = memoir_analysis["cognitive_terrain_balance"]["terrain_readiness"]
    spine_score = memoir_analysis["narrative_spine_strength"]
    
    # Weighted overall score (purpose and spine most important)
    memoir_analysis["overall_4d_readiness"] = (
        structure_score * 0.15 +
        transmission_score * 0.20 +
        purpose_score * 0.30 +
        terrain_score * 0.15 +
        spine_score * 0.20
    )
    
    return {
        "tesseract_memoir_analysis": memoir_analysis,
        "readiness_category": categorize_memoir_readiness(memoir_analysis["overall_4d_readiness"]),
        "estimated_completion_timeline": estimate_memoir_timeline(memoir_analysis),
        "4d_advantages": [
            "Tesseract coordinates provide multidimensional narrative structure",
            "Purpose-driven organization ensures meaningful content flow",
            "Cognitive terrain mapping enables emotional authenticity",
            "4D clustering reveals natural chapter boundaries"
        ]
    }

def calculate_structure_memoir_readiness(structure_dist: Counter) -> float:
    """Calculate memoir readiness based on X-dimension structure distribution"""
    total_structures = sum(structure_dist.values())
    if total_structures == 0:
        return 0.0
    
    # Weight different structures for memoir value
    structure_weights = {
        "archetype": 0.3,  # High value for character development
        "protocol": 0.2,  # Medium value for life systems
        "shadowcast": 0.3, # High value for emotional depth
        "expansion": 0.1,  # Lower value for background material
        "summoning": 0.25  # Good value for pivotal moments
    }
    
    weighted_score = 0.0
    for structure, count in structure_dist.items():
        weight = structure_weights.get(structure, 0.15)
        weighted_score += (count / total_structures) * weight
    
    return round(weighted_score, 3)

def calculate_transmission_memoir_readiness(transmission_dist: Counter) -> float:
    """Calculate memoir readiness based on Y-dimension transmission distribution"""
    total_transmissions = sum(transmission_dist.values())
    if total_transmissions == 0:
        return 0.0
    
    # Narrative content is most important for memoir
    narrative_ratio = transmission_dist.get("narrative", 0) / total_transmissions
    
    # Other transmission modes provide supporting value
    text_ratio = transmission_dist.get("text", 0) / total_transmissions
    
    # Calculate readiness (narrative most important)
    readiness = (narrative_ratio * 0.8) + (text_ratio * 0.2)
    
    return round(readiness, 3)

def calculate_terrain_memoir_readiness(terrain_dist: Counter) -> float:
    """Calculate memoir readiness based on W-dimension cognitive terrain balance"""
    total_terrain = sum(terrain_dist.values())
    if total_terrain == 0:
        return 0.0
    
    # Memoir benefits from emotional range across terrains
    terrain_diversity = len(terrain_dist) / 5  # Max 5 terrain types
    
    # Some terrains are more valuable for memoir
    terrain_weights = {
        "chaotic": 0.25,    # Essential for trauma memoir authenticity
        "complex": 0.3,     # Shows depth and processing
        "complicated": 0.2, # Good for technical/system content
        "confused": 0.15,   # Authentic but needs balance
        "obvious": 0.1      # Simple content, less memoir value
    }
    
    weighted_score = 0.0
    for terrain, count in terrain_dist.items():
        weight = terrain_weights.get(terrain, 0.15)
        weighted_score += (count / total_terrain) * weight
    
    # Combine weighted content with diversity bonus
    readiness = (weighted_score * 0.7) + (terrain_diversity * 0.3)
    
    return round(readiness, 3)

def categorize_memoir_readiness(overall_score: float) -> dict:
    """Categorize memoir readiness with specific guidance"""
    if overall_score >= 0.85:
        return {
            "category": "publication_ready",
            "description": "Memoir structure solid, content rich, ready for final editing",
            "confidence": "high"
        }
    elif overall_score >= 0.70:
        return {
            "category": "draft_complete",
            "description": "Strong foundation, needs content development and organization",
            "confidence": "medium-high"
        }
    elif overall_score >= 0.50:
        return {
            "category": "foundation_strong",
            "description": "Good 4D structure, needs more narrative content",
            "confidence": "medium"
        }
    else:
        return {
            "category": "development_phase",
            "description": "Early stage, focus on building content and structure",
            "confidence": "developing"
        }

def estimate_memoir_timeline(memoir_analysis: dict) -> dict:
    """Estimate timeline to memoir completion based on 4D analysis"""
    readiness_score = memoir_analysis["overall_4d_readiness"]
    spine_strength = memoir_analysis["narrative_spine_strength"]
    
    # Base timeline estimates (in months)
    if readiness_score >= 0.85:
        base_months = 2  # Just editing and refinement
    elif readiness_score >= 0.70:
        base_months = 6  # Content development and organization
    elif readiness_score >= 0.50:
        base_months = 12 # Building narrative content
    else:
        base_months = 18 # Fundamental development needed
    
    # Adjust based on spine strength
    if spine_strength > 0.8:
        spine_adjustment = -2  # Strong spine accelerates
    elif spine_strength > 0.5:
        spine_adjustment = 0   # Average spine
    else:
        spine_adjustment = 3   # Weak spine adds time
    
    estimated_months = max(1, base_months + spine_adjustment)
    
    return {
        "estimated_months": estimated_months,
        "estimated_range": f"{estimated_months-1}-{estimated_months+2} months",
        "key_factors": [
            f"Current 4D readiness: {round(readiness_score * 100, 1)}%",
            f"Narrative spine strength: {round(spine_strength * 100, 1)}%",
            "Timeline assumes consistent work on memoir development"
        ]
    }# Add these new imports to the existing routes.py
from app.utils import (
    # Existing imports...
    validate_markdown, write_markdown_file, parse_yaml_frontmatter,
    fix_yaml_frontmatter, generate_obsidian_yaml, apply_tag_consolidation,
    extract_all_tags, analyze_consolidation_opportunities, create_backup_snapshot,
    CRITICAL_CONSOLIDATIONS,
    
    # NEW: Content intelligence functions
    identify_document_archetype, extract_content_signature, count_internal_references,
    analyze_folder_content_types, measure_tag_coherence, extract_naming_patterns,
    calculate_urgency_score, group_by_archetype, generate_folder_path,
    calculate_priority, find_orphaned_files, chunked
)

# ============================================================================
# NEW: PHASE 2 CONTENT INTELLIGENCE ENDPOINTS
# ============================================================================

@router.post("/api/analysis/content-fingerprint")
async def analyze_content_patterns():
    """Create content fingerprints to understand document types and patterns"""
    patterns = {
        "document_types": Counter(),
        "content_signatures": {},
        "structural_patterns": {},
        "cross_reference_density": {},
        "narrative_markers": Counter()
    }
    
    processed_files = 0
    error_files = 0
    
    # Sample analysis for initial understanding (process all files but track progress)
    for md_file in VAULT_PATH.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            file_path_str = str(md_file.relative_to(VAULT_PATH))
            
            # Identify document archetypes
            archetype = identify_document_archetype(content)
            patterns["document_types"][archetype] += 1
            
            # Extract structural signatures
            signature = extract_content_signature(content)
            patterns["content_signatures"][file_path_str] = signature
            
            # Measure cross-reference density
            ref_density = count_internal_references(content)
            patterns["cross_reference_density"][file_path_str] = ref_density
            
            processed_files += 1
            
            # Progress tracking for large vaults
            if processed_files % 100 == 0:
                print(f"Processed {processed_files} files...")
                
        except Exception as e:
            error_files += 1
            print(f"Error processing {md_file}: {e}")
    
    # Calculate aggregate metrics
    total_words = sum(sig.get("word_count", 0) for sig in patterns["content_signatures"].values())
    avg_cross_refs = sum(patterns["cross_reference_density"].values()) / len(patterns["cross_reference_density"]) if patterns["cross_reference_density"] else 0
    
    # Identify most connected documents (high cross-reference density)
    top_connected = sorted(
        patterns["cross_reference_density"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    return {
        "analysis_summary": {
            "total_files_processed": processed_files,
            "processing_errors": error_files,
            "total_word_count": total_words,
            "avg_cross_references": round(avg_cross_refs, 2)
        },
        "document_archetypes": dict(patterns["document_types"].most_common()),
        "top_connected_documents": top_connected,
        "content_patterns": {
            "high_emotional_intensity": [
                path for path, sig in patterns["content_signatures"].items()
                if sig.get("emotional_intensity", 0) > 5
            ][:20],
            "memoir_candidates": [
                path for path, sig in patterns["content_signatures"].items()
                if sig.get("temporal_markers", {}).get("childhood_markers", 0) > 0 or
                   sig.get("personal_pronouns", {}).get("first_person", 0) > 10
            ][:20],
            "recovery_focus": [
                path for path in patterns["content_signatures"].keys()
                if identify_document_archetype(
                    VAULT_PATH.joinpath(path).read_text(encoding="utf-8")
                ) == "recovery-document"
            ][:20]
        },
        "structural_insights": {
            "files_with_yaml": sum(1 for sig in patterns["content_signatures"].values() if sig.get("has_yaml", False)),
            "files_with_code": sum(1 for sig in patterns["content_signatures"].values() if sig.get("has_code_blocks", False)),
            "highly_linked_content": len([d for d in patterns["cross_reference_density"].values() if d > 5])
        }
    }

@router.get("/api/analysis/folder-chaos")
async def analyze_folder_structure():
    """Analyze current folder structure for reorganization opportunities"""
    folder_analysis = {}
    processed_folders = 0
    
    for folder_path in VAULT_PATH.rglob("*"):
        if folder_path.is_dir() and not folder_path.name.startswith('.'):
            md_files = list(folder_path.glob("*.md"))
            if md_files:
                try:
                    # Analyze folder contents
                    content_types = analyze_folder_content_types(md_files)
                    tag_coherence = measure_tag_coherence(md_files)
                    naming_patterns = extract_naming_patterns(md_files)
                    
                    folder_key = str(folder_path.relative_to(VAULT_PATH))
                    folder_analysis[folder_key] = {
                        "file_count": len(md_files),
                        "content_types": content_types,
                        "tag_coherence_score": round(tag_coherence, 3),
                        "naming_patterns": naming_patterns,
                        "reorganization_urgency": round(
                            calculate_urgency_score(content_types, tag_coherence), 3
                        ),
                        "path_depth": len(folder_path.relative_to(VAULT_PATH).parts)
                    }
                    processed_folders += 1
                    
                except Exception as e:
                    print(f"Error analyzing folder {folder_path}: {e}")
    
    # Sort by urgency and identify chaos hotspots
    chaos_hotspots = sorted(
        folder_analysis.items(),
        key=lambda x: x[1]["reorganization_urgency"],
        reverse=True
    )[:20]
    
    # Generate structure suggestions
    structure_suggestions = generate_structure_suggestions(folder_analysis)
    
    return {
        "analysis_summary": {
            "total_folders_analyzed": processed_folders,
            "folders_with_files": len(folder_analysis),
            "avg_files_per_folder": sum(f["file_count"] for f in folder_analysis.values()) / len(folder_analysis) if folder_analysis else 0
        },
        "chaos_hotspots": chaos_hotspots,
        "structural_issues": {
            "deep_nested_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["path_depth"] > 4
            ],
            "singleton_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["file_count"] == 1
            ][:10],
            "mixed_content_folders": [
                folder for folder, analysis in folder_analysis.items()
                if analysis["content_types"]["type_diversity"] > 0.7
            ][:10]
        },
        "suggested_structure": structure_suggestions,
        "reorganization_impact": calculate_reorganization_impact(folder_analysis)
    }

def generate_structure_suggestions(folder_analysis: dict) -> dict:
    """Generate intelligent folder structure suggestions"""
    suggestions = {
        "consolidation_opportunities": [],
        "new_structure_proposal": {},
        "quick_wins": []
    }
    
    # Identify folders that could be consolidated
    content_type_groups = defaultdict(list)
    for folder, analysis in folder_analysis.items():
        dominant_type = analysis["content_types"]["dominant_type"]
        if dominant_type != "unknown":
            content_type_groups[dominant_type].append({
                "folder": folder,
                "file_count": analysis["file_count"],
                "urgency": analysis["reorganization_urgency"]
            })
    
    # Suggest consolidations for types with multiple folders
    for content_type, folders in content_type_groups.items():
        if len(folders) > 2:  # Multiple folders with same content type
            total_files = sum(f["file_count"] for f in folders)
            suggestions["consolidation_opportunities"].append({
                "content_type": content_type,
                "current_folders": [f["folder"] for f in folders],
                "total_files": total_files,
                "suggested_target": generate_folder_path(content_type),
                "priority": "high" if total_files > 20 else "medium"
            })
    
    # Propose new top-level structure based on Rick's content
    suggestions["new_structure_proposal"] = {
        "memoir/": "Personal narratives, memories, life stories",
        "recovery/": "AA, sobriety, addiction recovery documents",
        "health/": "Medical, therapy, mental health records",
        "creative/": "AI art, music, comedy, creative projects",
        "systems/": "Technical documentation, API, tools",
        "philosophy/": "Reflections, spiritual, existential content",
        "life/": "Daily life, practical matters, housing, etc",
        "_archive/": "Old versions, deprecated content",
        "_inbox/": "New, unsorted content"
    }
    
    # Quick wins - easy reorganizations
    for folder, analysis in folder_analysis.items():
        if (analysis["reorganization_urgency"] > 0.8 and
            analysis["file_count"] < 10 and
            analysis["content_types"]["type_diversity"] < 0.3):
            suggestions["quick_wins"].append({
                "folder": folder,
                "target": generate_folder_path(analysis["content_types"]["dominant_type"]),
                "file_count": analysis["file_count"],
                "rationale": "High urgency, low file count, coherent content type"
            })
    
    return suggestions

def calculate_reorganization_impact(folder_analysis: dict) -> dict:
    """Calculate potential impact of reorganization"""
    total_files = sum(f["file_count"] for f in folder_analysis.values())
    high_urgency_files = sum(
        f["file_count"] for f in folder_analysis.values()
        if f["reorganization_urgency"] > 0.7
    )
    
    return {
        "total_files_affected": total_files,
        "high_priority_files": high_urgency_files,
        "estimated_improvement": f"{round((high_urgency_files / total_files) * 100, 1)}% of files would benefit",
        "reorganization_complexity": "high" if total_files > 500 else "medium" if total_files > 100 else "low"
    }

@router.post("/api/reorganize/suggest")
async def suggest_reorganization(
    focus_area: str = "all",  # memoir, recovery, creative, medical, technical, all
    consolidation_threshold: int = 5,
    max_suggestions: int = 20
):
    """Generate intelligent folder reorganization suggestions"""
    
    # Get current analysis
    content_analysis = await analyze_content_patterns()
    folder_analysis = await analyze_folder_structure()
    
    suggestions = []
    
    # Group documents by content archetype
    document_types = content_analysis["document_archetypes"]
    
    # Filter by focus area if specified
    if focus_area != "all":
        focus_mappings = {
            "memoir": ["memoir-narrative"],
            "recovery": ["recovery-document"],
            "creative": ["creative-work"],
            "medical": ["medical-health"],
            "technical": ["technical-system"]
        }
        target_types = focus_mappings.get(focus_area, [focus_area])
    else:
        target_types = list(document_types.keys())
    
    # Generate consolidation suggestions for each archetype
    for archetype in target_types:
        file_count = document_types.get(archetype, 0)
        if file_count >= consolidation_threshold:
            
            # Find current folders containing this archetype
            current_locations = []
            for folder_path, folder_data in folder_analysis["chaos_hotspots"]:
                dominant_type = folder_data["content_types"]["dominant_type"]
                if dominant_type == archetype:
                    current_locations.append({
                        "folder": folder_path,
                        "file_count": folder_data["file_count"],
                        "urgency": folder_data["reorganization_urgency"]
                    })
            
            suggestions.append({
                "action": "consolidate_by_archetype",
                "archetype": archetype,
                "total_files": file_count,
                "current_scattered_locations": len(current_locations),
                "current_locations_sample": current_locations[:5],
                "suggested_target_path": generate_folder_path(archetype),
                "priority": calculate_priority(archetype, file_count),
                "estimated_time_savings": f"{file_count * 0.5:.1f} minutes per search",
                "memoir_relevance": get_memoir_relevance(archetype)
            })
    
    # Identify orphaned and deeply nested files
    orphaned_files = []
    for folder_path, folder_data in folder_analysis["chaos_hotspots"]:
        if (folder_data["path_depth"] > 4 and
            folder_data["file_count"] < 3):
            orphaned_files.extend([{
                "current_path": folder_path,
                "file_count": folder_data["file_count"],
                "suggested_target": "_inbox/needs-review",
                "reason": "deeply_nested_singleton"
            }])
    
    if orphaned_files:
        suggestions.append({
            "action": "rescue_orphaned_files",
            "total_orphaned": len(orphaned_files),
            "sample_locations": orphaned_files[:10],
            "suggested_target_path": "_inbox/needs-review",
            "priority": "medium",
            "rationale": "Files buried in deep folder structures are hard to find"
        })
    
    # Special memoir-focused suggestions
    if focus_area in ["all", "memoir"]:
        memoir_suggestions = generate_memoir_structure_suggestions(content_analysis)
        suggestions.extend(memoir_suggestions)
    
    # Limit results
    suggestions = suggestions[:max_suggestions]
    
    return {
        "focus_area": focus_area,
        "total_suggestions": len(suggestions),
        "high_priority_count": len([s for s in suggestions if s.get("priority") == "high"]),
        "suggestions": suggestions,
        "estimated_total_impact": calculate_suggestion_impact(suggestions),
        "next_steps": [
            "Review suggestions and select highest priority items",
            "Create backup before executing any moves",
            "Start with quick wins (small file counts, clear benefits)",
            "Execute in batches to allow for review and adjustment"
        ]
    }

def get_memoir_relevance(archetype: str) -> str:
    """Assess how relevant an archetype is to memoir writing"""
    memoir_relevance = {
        "memoir-narrative": "critical - primary memoir content",
        "recovery-document": "critical - central to your story",
        "medical-health": "high - important life context",
        "practical-life": "medium - daily life details",
        "philosophical-reflection": "medium - provides depth and insight",
        "creative-work": "low - supplementary creative expression",
        "technical-system": "low - behind-the-scenes infrastructure"
    }
    return memoir_relevance.get(archetype, "unknown")

def generate_memoir_structure_suggestions(content_analysis: dict) -> list:
    """Generate specific suggestions for memoir organization"""
    memoir_suggestions = []
    
    # Look for chronological organization opportunities
    temporal_files = []
    for file_path, signature in content_analysis.get("content_patterns", {}).get("memoir_candidates", []):
        if signature and "temporal_markers" in signature:
            temporal_files.append(file_path)
    
    if len(temporal_files) > 10:
        memoir_suggestions.append({
            "action": "create_chronological_memoir_structure",
            "archetype": "memoir-organization",
            "total_files": len(temporal_files),
            "suggested_structure": {
                "memoir/childhood/": "Early life, family, formative experiences",
                "memoir/addiction/": "Descent into addiction, dark times",
                "memoir/rock-bottom/": "Crisis points, consequences",
                "memoir/recovery/": "Getting sober, AA journey",
                "memoir/health-crisis/": "Cirrhosis diagnosis, Mayo treatment",
                "memoir/present/": "Current life, reflections, hope"
            },
            "priority": "critical",
            "memoir_relevance": "critical - creates narrative backbone for book",
            "rationale": "Chronological organization essential for memoir readability"
        })
    
    return memoir_suggestions

def calculate_suggestion_impact(suggestions: list) -> dict:
    """Calculate estimated impact of implementing suggestions"""
    total_files = sum(s.get("total_files", 0) for s in suggestions)
    high_priority = len([s for s in suggestions if s.get("priority") == "high"])
    
    # Estimate time savings
    search_time_savings = sum(
        float(s.get("estimated_time_savings", "0 minutes").split()[0])
        for s in suggestions if "estimated_time_savings" in s
    )
    
    return {
        "files_to_be_reorganized": total_files,
        "high_priority_actions": high_priority,
        "estimated_weekly_time_savings": f"{search_time_savings:.1f} minutes",
        "memoir_production_readiness": "significantly improved" if high_priority > 2 else "moderately improved"
    }

@router.post("/api/reorganize/execute")
async def execute_reorganization(
    suggestion_id: int,  # Which suggestion to execute
    batch_size: int = 25,
    dry_run: bool = True,
    create_backup: bool = True
):
    """Execute a specific reorganization suggestion in safe batches"""
    
    if create_backup and not dry_run:
        print("Creating backup before reorganization...")
        backup_path = create_backup_snapshot(VAULT_PATH)
        print(f"Backup created at: {backup_path}")
    else:
        backup_path = None
    
    # For this implementation, we'll work with a simple move plan
    # In production, you'd load the specific suggestion and create detailed move plans
    
    results = []
    total_moves = 0
    successful_moves = 0
    errors = []
    
    # This is a simplified version - would need suggestion storage/retrieval
    example_moves = [
        {"source": "old/path/file1.md", "target": "memoir/childhood/", "archetype": "memoir-narrative"},
        {"source": "scattered/file2.md", "target": "recovery/documents/", "archetype": "recovery-document"}
    ]
    
    try:
        for batch_num, batch in enumerate(chunked(example_moves, batch_size), 1):
            batch_results = []
            
            print(f"Processing batch {batch_num} ({len(batch)} files)...")
            
            for move in batch:
                try:
                    source_path = VAULT_PATH / move["source"]
                    target_dir = VAULT_PATH / move["target"]
                    
                    if not source_path.exists():
                        batch_results.append({
                            "file": move["source"],
                            "status": "error",
                            "error": "Source file not found"
                        })
                        continue
                    
                    if not dry_run:
                        # Create target directory
                        target_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Move file
                        target_path = target_dir / source_path.name
                        source_path.rename(target_path)
                        
                        status = "moved"
                        successful_moves += 1
                    else:
                        status = "planned"
                    
                    batch_results.append({
                        "file": move["source"],
                        "target": move["target"],
                        "archetype": move.get("archetype", "unknown"),
                        "status": status
                    })
                    
                    total_moves += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    errors.append(f"Error moving {move['source']}: {error_msg}")
                    batch_results.append({
                        "file": move["source"],
                        "status": "error",
                        "error": error_msg
                    })
            
            results.extend(batch_results)
            
            # Safety pause between batches (only in real execution)
            if not dry_run and batch_num < len(list(chunked(example_moves, batch_size))):
                time.sleep(2)
                
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "backup_path": str(backup_path) if backup_path else None
        }
    
    return {
        "status": "completed" if not errors else "completed_with_errors",
        "dry_run": dry_run,
        "backup_created": backup_path is not None,
        "backup_path": str(backup_path) if backup_path else None,
        "execution_summary": {
            "total_planned_moves": len(example_moves),
            "batches_processed": len(list(chunked(example_moves, batch_size))),
            "successful_moves": successful_moves,
            "total_errors": len(errors)
        },
        "results": results,
        "errors": errors,
        "recommendations": [
            "Review moved files to ensure they're in correct locations",
            "Update any internal links that may have broken",
            "Run tag audit to identify any cleanup needed after moves",
            "Consider creating index files for new folder structure"
        ]
    }

@router.get("/api/analysis/memoir-readiness")
async def assess_memoir_readiness():
    """Assess how ready the codex is for memoir production"""
    
    # Get content analysis
    content_patterns = await analyze_content_patterns()
    folder_structure = await analyze_folder_structure()
    
    # Analyze memoir-specific readiness factors
    memoir_files = []
    recovery_files = []
    chronological_files = []
    
    for archetype, count in content_patterns["document_archetypes"].items():
        if archetype == "memoir-narrative":
            memoir_files.append(count)
        elif archetype == "recovery-document":
            recovery_files.append(count)
    
    # Check for chronological markers
    temporal_content = len(content_patterns.get("content_patterns", {}).get("memoir_candidates", []))
    
    # Assess organization quality
    avg_urgency = sum(
        folder["reorganization_urgency"]
        for _, folder in folder_structure["chaos_hotspots"]
    ) / len(folder_structure["chaos_hotspots"]) if folder_structure["chaos_hotspots"] else 0
    
    # Calculate readiness scores
    content_score = min(100, (sum(memoir_files) + sum(recovery_files)) * 2)  # More content = better
    organization_score = max(0, 100 - (avg_urgency * 100))  # Less chaos = better
    temporal_score = min(100, temporal_content * 5)  # More chronological markers = better
    
    overall_readiness = (content_score + organization_score + temporal_score) / 3
    
    # Generate specific recommendations
    recommendations = []
    if content_score < 50:
        recommendations.append("Continue documenting key life events and memories")
    if organization_score < 70:
        recommendations.append("Prioritize folder reorganization to group related content")
    if temporal_score < 60:
        recommendations.append("Add more chronological context to existing documents")
    
    # Identify memoir structure gaps
    expected_chapters = [
        "early-life", "family-background", "addiction-onset", "spiral-downward",
        "rock-bottom", "recovery-beginning", "aa-journey", "health-crisis",
        "present-day", "future-hopes"
    ]
    
    missing_chapters = []
    for chapter in expected_chapters:
        # Simple check - would need more sophisticated content analysis
        chapter_content = sum(1 for file_type in content_patterns["document_archetypes"].keys()
                             if chapter.replace("-", " ") in file_type.lower())
        if chapter_content == 0:
            missing_chapters.append(chapter)
    
    return {
        "overall_readiness_score": round(overall_readiness, 1),
        "readiness_category": (
            "publication_ready" if overall_readiness >= 85 else
            "revision_ready" if overall_readiness >= 70 else
            "draft_ready" if overall_readiness >= 50 else
            "foundation_building"
        ),
        "component_scores": {
            "content_volume": round(content_score, 1),
            "organization_quality": round(organization_score, 1),
            "chronological_structure": round(temporal_score, 1)
        },
        "content_inventory": {
            "memoir_documents": sum(memoir_files),
            "recovery_documents": sum(recovery_files),
            "total_relevant_files": sum(memoir_files) + sum(recovery_files),
            "files_with_temporal_markers": temporal_content
        },
        "structural_assessment": {
            "folders_needing_reorganization": len([
                folder for _, folder in folder_structure["chaos_hotspots"]
                if folder["reorganization_urgency"] > 0.7
            ]),
            "average_organization_urgency": round(avg_urgency, 3)
        },
        "missing_content_areas": missing_chapters,
        "recommendations": recommendations,
        "next_steps": [
            "Focus on highest readiness score improvements first",
            "Use reorganization suggestions to improve structure",
            "Identify and fill content gaps in missing chapters",
            "Consider creating timeline documents for chronological flow"
        ]
    }

@router.post("/api/inload/scan-content")
async def scan_inload_content():
    """Scan all _inload directories and generate content signatures"""
    from .content_mining import InloadContentMiner
    
    try:
        # Initialize miner
        miner = InloadContentMiner(VAULT_PATH)
        
        # Scan content
        signatures = miner.scan_all_inload_content()
        
        # Classify content
        miner.classify_content()
        
        # Generate report
        report = miner.generate_mining_report()
        
        return {
            "status": "success",
            "scan_results": report,
            "total_files": len(signatures),
            "classifications": {
                category: len(files)
                for category, files in miner.mining_results.items()
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to scan _inload content"
        }

# Add these endpoints to your app/routes.py file
# Insert after the training endpoints section

def generate_smart_tags(chunk: dict) -> list:
    """Generate intelligent tags based on chunk analysis"""
    tags = []
    coords = chunk.get('coordinates', {})
    theme = chunk.get('theme', '')
    patterns = chunk.get('patterns', {})
    
    # Add coordinate tags
    if coords.get('x_structure'):
        tags.append(f"x-structure/{coords['x_structure']}")
    if coords.get('y_transmission'):
        tags.append(f"y-transmission/{coords['y_transmission']}")
    if coords.get('z_purpose'):
        tags.append(f"z-purpose/{coords['z_purpose']}")
    if coords.get('w_terrain'):
        tags.append(f"w-terrain/{coords['w_terrain']}")
    
    # Add theme tag
    if theme and theme != 'unknown':
        tags.append(f"theme/{theme}")
    
    # Add content-based tags
    if patterns.get('memoir_markers', 0) > 3:
        tags.append('memoir-gold')
    if patterns.get('recovery_markers', 0) > 2:
        tags.append('recovery')
    if patterns.get('medical_markers', 0) > 2:
        tags.append('medical')
    if patterns.get('ai_markers', 0) > 2:
        tags.append('ai-collaboration')
    if patterns.get('emotional_markers', 0) > 3:
        tags.append('emotional-depth')
    
    return tags

def calculate_tagging_confidence(chunk: dict) -> float:
    """Calculate confidence in auto-tagging suggestions"""
    patterns = chunk.get('patterns', {})
    quality = chunk.get('quality_score', 0)
    
    # High quality + strong patterns = high confidence
    pattern_strength = sum(patterns.values())
    pattern_score = min(pattern_strength / 20, 1.0)  # Normalize to 0-1
    quality_score = min(quality / 100, 1.0)
    
    # Weighted combination
    confidence = (pattern_score * 0.4) + (quality_score * 0.6)
    
    return round(confidence, 2)

@router.post("/api/chunks/create-review-queue")
async def create_review_queue():
    """
    Create a prioritized review queue of chunks needing human attention
    """
    
    training_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    review_queue = []
    
    # Load all chunks
    for batch_dir in (training_dir / "batch_outputs").glob("batch_*"):
        chunks_file = batch_dir / "extracted_chunks.json"
        if chunks_file.exists():
            with open(chunks_file, 'r') as f:
                chunks = json.load(f)
            
            for chunk in chunks:
                review_priority = calculate_review_priority(chunk)
                
                if review_priority > 0:  # Needs some level of review
                    review_queue.append({
                        'chunk': chunk,
                        'priority': review_priority,
                        'review_reason': get_review_reason(chunk),
                        'ai_suggestions': {
                            'tags': generate_smart_tags(chunk),
                            'destination': suggest_chunk_destination(
                                chunk.get('coordinates', {}),
                                chunk.get('quality_score', 0)
                            ),
                            'confidence': calculate_tagging_confidence(chunk)
                        }
                    })
    
    # Sort by priority
    review_queue.sort(key=lambda x: x['priority'], reverse=True)
    
    # Save queue
    queue_file = training_dir / "review_queue.json"
    with open(queue_file, 'w') as f:
        json.dump(review_queue, f, indent=2)
    
    return {
        'total_items': len(review_queue),
        'high_priority': len([x for x in review_queue if x['priority'] >= 0.8]),
        'medium_priority': len([x for x in review_queue if 0.5 <= x['priority'] < 0.8]),
        'low_priority': len([x for x in review_queue if x['priority'] < 0.5]),
        'queue_file': str(queue_file)
    }

@router.get("/api/chunks/review-queue")
async def get_review_queue(
    priority_filter: str = "all",  # all, critical, high, medium, low
    limit: int = 50
):
    """
    Get items from the review queue with optional filtering
    """
    training_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    queue_file = training_dir / "review_queue.json"

    if not queue_file.exists():
        return {
            'status': 'error',
            'message': 'Review queue not found. Run POST /api/chunks/create-review-queue first',
            'suggestion': 'curl -X POST http://localhost:5050/api/chunks/create-review-queue'
        }

    try:
        with open(queue_file, 'r') as f:
            queue = json.load(f)

        # Apply priority filter
        if priority_filter == "critical":
            filtered = [x for x in queue if x['priority'] >= 0.8]
        elif priority_filter == "high":
            filtered = [x for x in queue if 0.6 <= x['priority'] < 0.8]
        elif priority_filter == "medium":
            filtered = [x for x in queue if 0.4 <= x['priority'] < 0.6]
        elif priority_filter == "low":
            filtered = [x for x in queue if x['priority'] < 0.4]
        else:
            filtered = queue

        # Limit results
        filtered = filtered[:limit]

        return {
            'status': 'success',
            'total_in_queue': len(queue),
            'filtered_count': len(filtered),
            'priority_filter': priority_filter,
            'items': filtered
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to load review queue'
        }


@router.get("/api/chunks/review-batch")
async def get_review_batch(
    batch_size: int = 10,
    priority_filter: str = "high"  # critical, high, medium, low
):
    """
    Get a smart batch of chunks for human review with AI suggestions
    """
    training_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    queue_file = training_dir / "review_queue.json"

    if not queue_file.exists():
        return {
            'status': 'error',
            'message': 'Review queue not found. Create it first.',
            'create_queue_endpoint': 'POST /api/chunks/create-review-queue'
        }

    try:
        with open(queue_file, 'r') as f:
            queue = json.load(f)

        # Filter by priority
        if priority_filter == "critical":
            candidates = [x for x in queue if x['priority'] >= 0.8]
        elif priority_filter == "high":
            candidates = [x for x in queue if 0.6 <= x['priority'] < 0.8]
        elif priority_filter == "medium":
            candidates = [x for x in queue if 0.4 <= x['priority'] < 0.6]
        elif priority_filter == "low":
            candidates = [x for x in queue if x['priority'] < 0.4]
        else:
            candidates = queue

        # Take batch
        batch = candidates[:batch_size]

        return {
            'status': 'success',
            'batch_size': len(batch),
            'priority_filter': priority_filter,
            'remaining_in_filter': len(candidates) - batch_size,
            'total_remaining': len(queue),
            'chunks': batch,
            'review_instructions': {
                'for_each_chunk': [
                    'Review content_preview',
                    'Check AI suggested_tags',
                    'Verify suggested_destination makes sense',
                    'Decide: keep, modify, or reject'
                ],
                'actions': {
                    'approve': 'Accept AI suggestions as-is',
                    'modify': 'Change tags/destination before applying',
                    'reject': 'Mark for archive/trash'
                }
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'message': 'Failed to create review batch'
        }


@router.post("/api/chunks/approve-batch")
async def approve_review_batch(decisions: dict):
    """
    Apply human decisions from a review batch

    Expected format:
    {
        "decisions": [
            {
                "chunk_id": "...",
                "action": "approve|modify|reject",
                "tags": [...],  # if modified
                "destination": "..."  # if modified
            }
        ]
    }
    """

    results = {
        'approved': [],
        'modified': [],
        'rejected': [],
        'errors': []
    }

    for decision in decisions.get('decisions', []):
        try:
            chunk_id = decision['chunk_id']
            action = decision['action']

            if action == 'approve':
                results['approved'].append(chunk_id)
                # TODO: Apply tags and move to destination

            elif action == 'modify':
                results['modified'].append({
                    'chunk_id': chunk_id,
                    'new_tags': decision.get('tags', []),
                    'new_destination': decision.get('destination', '')
                })
                # TODO: Apply modified tags and move

            elif action == 'reject':
                results['rejected'].append(chunk_id)
                # TODO: Move to archive/trash

        except Exception as e:
            results['errors'].append({
                'chunk_id': decision.get('chunk_id', 'unknown'),
                'error': str(e)
            })

    return {
        'status': 'success',
        'summary': {
            'approved_count': len(results['approved']),
            'modified_count': len(results['modified']),
            'rejected_count': len(results['rejected']),
            'error_count': len(results['errors'])
        },
        'details': results,
        'note': 'Actual file operations not yet implemented - this is showing what would happen'
    }


@router.get("/api/chunks/review-stats")
async def get_review_statistics():
    """
    Get statistics about the review queue and progress
    """
    training_dir = Path("/Users/rickshangle/Vaults/flatline-codex/_training_output")
    queue_file = training_dir / "review_queue.json"

    if not queue_file.exists():
        return {
            'status': 'error',
            'message': 'Review queue not found'
        }

    try:
        with open(queue_file, 'r') as f:
            queue = json.load(f)

        # Calculate stats
        total = len(queue)
        by_priority = {
            'critical': len([x for x in queue if x['priority'] >= 0.8]),
            'high': len([x for x in queue if 0.6 <= x['priority'] < 0.8]),
            'medium': len([x for x in queue if 0.4 <= x['priority'] < 0.6]),
            'low': len([x for x in queue if x['priority'] < 0.4])
        }

        by_purpose = Counter(x['coordinates']['z_purpose'] for x in queue)
        by_theme = Counter(x.get('chunk_id', 'unknown').split('-')[0] for x in queue)

        quality_scores = [x['quality_score'] for x in queue]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            'status': 'success',
            'total_items': total,
            'by_priority': by_priority,
            'by_purpose': dict(by_purpose.most_common(5)),
            'quality_stats': {
                'average': round(avg_quality, 1),
                'min': min(quality_scores) if quality_scores else 0,
                'max': max(quality_scores) if quality_scores else 0,
                'memoir_gold': len([x for x in queue if x['quality_score'] >= 80])
            },
            'estimated_review_time': {
                'critical_items': f"{by_priority['critical'] * 2} minutes (2 min each)",
                'high_items': f"{by_priority['high'] * 1} minutes (1 min each)",
                'total_high_priority': f"{by_priority['critical'] * 2 + by_priority['high']} minutes"
            }
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

@router.get("/api/inload/priority-files")
async def get_priority_inload_files(category: str = "high_value", limit: int = 20):
    """Get priority files from specific category for manual review"""
    from .content_mining import InloadContentMiner
    
    valid_categories = [
        "high_value", "memoir_gold", "recovery_threads",
        "job_survival", "ai_collaboration", "creative_fragments"
    ]
    
    if category not in valid_categories:
        return {
            "status": "error",
            "message": f"Invalid category. Must be one of: {valid_categories}"
        }
    
    try:
        # Quick scan to get current state
        miner = InloadContentMiner(VAULT_PATH)
        miner.scan_all_inload_content()
        miner.classify_content()
        
        # Get requested category
        category_files = miner.mining_results.get(category, [])
        
        # Sort by quality/relevance and limit
        if category in ["high_value", "memoir_gold"]:
            sorted_files = sorted(category_files, key=lambda x: x.get('quality', 0), reverse=True)
        elif category == "recovery_threads":
            sorted_files = sorted(category_files, key=lambda x: x.get('recovery_markers', 0), reverse=True)
        elif category == "job_survival":
            sorted_files = sorted(category_files, key=lambda x: x.get('job_markers', 0) + x.get('medical_markers', 0), reverse=True)
        else:
            sorted_files = category_files
        
        return {
            "status": "success",
            "category": category,
            "total_in_category": len(category_files),
            "files": sorted_files[:limit],
            "suggested_destinations": get_suggested_destinations(category)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to get priority files for {category}"
        }

def get_suggested_destinations(category):
    """Get suggested destination folders for each category"""
    destinations = {
        "high_value": ["memoir/spine/", "recovery/practices/", "work-amends/"],
        "memoir_gold": ["memoir/spine/foundations/", "memoir/spine/recovery/", "memoir/spine/integration/"],
        "recovery_threads": ["recovery/practices/", "recovery/explorations/", "recovery/personas/"],
        "job_survival": ["work-amends/job-search/", "work-amends/skills/", "survival/medical/"],
        "ai_collaboration": ["contribution/systems/", "memoir/spine/integration/"],
        "creative_fragments": ["contribution/creative/", "memoir/explorations/"]
    }
    return destinations.get(category, ["_tesseract-inbox/needs-classification/"])

@router.post("/api/inload/extract-sample")
async def extract_content_sample(file_path: str, max_words: int = 200):
    """Extract content sample from specific file for manual review"""
    try:
        target_file = VAULT_PATH / file_path
        if not target_file.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}"
            }
        
        content = target_file.read_text(encoding='utf-8')
        words = content.split()
        
        # Extract sample
        sample_words = words[:max_words]
        sample_text = ' '.join(sample_words)
        
        # Get content signature
        from .content_mining import InloadContentMiner
        miner = InloadContentMiner(VAULT_PATH)
        signature = miner.extract_content_signature(target_file)
        
        return {
            "status": "success",
            "file_path": file_path,
            "total_words": len(words),
            "sample_text": sample_text,
            "signature": signature,
            "truncated": len(words) > max_words
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to extract sample from {file_path}"
        }

@router.post("/api/inload/batch-move")
async def batch_move_files(request: BatchMoveRequest):
    moves = request.moves

    # Validate moves structure
    required_fields = ["source_path", "destination_path"]
    for move in moves:
        if not all(field in move for field in required_fields):
            return {
                "status": "error",
                "message": f"Each move must have: {required_fields}"
            }
    
    try:
        # Create backup before moving
        backup_result = await create_emergency_backup()
        if backup_result["status"] != "success":
            return {
                "status": "error",
                "message": "Failed to create backup before batch move"
            }
        
        results = []
        for move in moves:
            source = VAULT_PATH / move["source_path"]
            destination = VAULT_PATH / move["destination_path"]
            
            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform move
            if source.exists():
                source.rename(destination)
                results.append({
                    "source": move["source_path"],
                    "destination": move["destination_path"],
                    "status": "success"
                })
            else:
                results.append({
                    "source": move["source_path"],
                    "destination": move["destination_path"],
                    "status": "error",
                    "message": "Source file not found"
                })
        
        successful_moves = len([r for r in results if r["status"] == "success"])
        
        return {
            "status": "success",
            "total_moves_attempted": len(moves),
            "successful_moves": successful_moves,
            "backup_created": backup_result["backup_path"],
            "move_results": results
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Batch move operation failed"
        }

@router.post("/api/inload/archive-low-priority")
async def archive_low_priority_content():
    """Move low-priority content to archive folder"""
    from .content_mining import InloadContentMiner
    
    try:
        # Scan to identify archive candidates
        miner = InloadContentMiner(VAULT_PATH)
        miner.scan_all_inload_content()
        miner.classify_content()
        
        archive_candidates = miner.mining_results["archive_candidates"]
        
        if not archive_candidates:
            return {
                "status": "success",
                "message": "No archive candidates found",
                "archived_count": 0
            }
        
        # Create archive directory
        archive_dir = VAULT_PATH / "_archive" / f"inload_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        backup_result = await create_emergency_backup()
        
        archived_files = []
        for candidate in archive_candidates:
            source_path = VAULT_PATH / candidate["file"]
            if source_path.exists():
                # Preserve directory structure in archive
                relative_path = source_path.relative_to(VAULT_PATH)
                archive_path = archive_dir / relative_path
                archive_path.parent.mkdir(parents=True, exist_ok=True)
                
                source_path.rename(archive_path)
                archived_files.append({
                    "original": candidate["file"],
                    "archived_to": str(archive_path.relative_to(VAULT_PATH)),
                    "quality_score": candidate["quality"]
                })
        
        return {
            "status": "success",
            "archived_count": len(archived_files),
            "archive_location": str(archive_dir.relative_to(VAULT_PATH)),
            "backup_created": backup_result["backup_path"],
            "archived_files": archived_files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Archive operation failed"
        }

@router.post("/api/snippets/analyze")
async def analyze_snippet_quality(quality_threshold: int = 20):
    """Analyze snippet quality and suggest reorganization"""
    from .snippet_batch_processor import process_current_snippets
    
    try:
        # Get AI collaboration files (includes snippets)
        ai_collaboration_result = await get_priority_inload_files("ai_collaboration", 200)
        
        if ai_collaboration_result["status"] != "success":
            return {"status": "error", "message": "Failed to get AI collaboration data"}
        
        # Process snippets
        snippet_analysis = process_current_snippets(
            VAULT_PATH,
            ai_collaboration_result,
            quality_threshold
        )
        
        return {
            "status": "success",
            "quality_threshold": quality_threshold,
            "snippet_analysis": snippet_analysis,
            "recommendations": generate_snippet_recommendations(snippet_analysis),
            "extraction_efficiency": calculate_extraction_efficiency(snippet_analysis)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to analyze snippet quality"
        }

@router.post("/api/snippets/process")
async def process_snippets(quality_threshold: int = 20, dry_run: bool = True):
    """Execute snippet processing and reorganization"""
    from .snippet_batch_processor import execute_snippet_reorganization, process_current_snippets
    
    try:
        # First analyze snippets
        ai_collaboration_result = await get_priority_inload_files("ai_collaboration", 200)
        snippet_analysis = process_current_snippets(VAULT_PATH, ai_collaboration_result, quality_threshold)
        
        # Execute the reorganization
        results = execute_snippet_reorganization(VAULT_PATH, snippet_analysis, dry_run)
        
        # Create comprehensive report
        processing_report = {
            "status": "success",
            "dry_run": dry_run,
            "processing_results": results,
            "efficiency_analysis": {
                "total_snippets_found": snippet_analysis["promote_count"] + snippet_analysis["archive_count"],
                "high_value_extracted": snippet_analysis["promote_count"],
                "extraction_efficiency_percent": round(
                    (snippet_analysis["promote_count"] / max(snippet_analysis["promote_count"] + snippet_analysis["archive_count"], 1)) * 100, 1
                )
            },
            "recommendations": generate_post_processing_recommendations(results, snippet_analysis)
        }
        
        return processing_report
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to process snippets"
        }

@router.get("/api/snippets/stats")
async def get_snippet_statistics():
    """Get statistics on snippet extraction efforts"""
    from .content_mining import InloadContentMiner
    
    try:
        # Scan current content
        miner = InloadContentMiner(VAULT_PATH)
        miner.scan_all_inload_content()
        miner.classify_content()
        
        # Find snippet-tagged files
        snippet_files = []
        total_ai_collaboration = len(miner.mining_results["ai_collaboration"])
        
        for file_path, signature in miner.content_signatures.items():
            if signature.get('file_path') and miner.is_snippet_file_by_signature(signature):
                snippet_files.append({
                    "file": file_path,
                    "quality": signature["quality_score"],
                    "theme": signature["dominant_theme"],
                    "word_count": signature["word_count"]
                })
        
        # Calculate statistics
        if snippet_files:
            qualities = [f["quality"] for f in snippet_files]
            avg_quality = sum(qualities) / len(qualities)
            high_quality_count = len([q for q in qualities if q >= 20])
            total_words = sum(f["word_count"] for f in snippet_files)
        else:
            avg_quality = 0
            high_quality_count = 0
            total_words = 0
        
        return {
            "status": "success",
            "snippet_statistics": {
                "total_snippet_files": len(snippet_files),
                "total_ai_collaboration_files": total_ai_collaboration,
                "snippet_percentage_of_ai_files": round(len(snippet_files) / max(total_ai_collaboration, 1) * 100, 1),
                "average_quality_score": round(avg_quality, 2),
                "high_quality_count": high_quality_count,
                "extraction_efficiency": round(high_quality_count / max(len(snippet_files), 1) * 100, 1),
                "total_words_extracted": total_words,
                "quality_distribution": {
                    "high_value": len([f for f in snippet_files if f["quality"] >= 50]),
                    "medium_value": len([f for f in snippet_files if 20 <= f["quality"] < 50]),
                    "low_value": len([f for f in snippet_files if f["quality"] < 20])
                }
            },
            "top_quality_snippets": sorted(snippet_files, key=lambda x: x["quality"], reverse=True)[:10],
            "efficiency_analysis": analyze_extraction_efficiency(snippet_files)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate snippet statistics"
        }

def generate_snippet_recommendations(snippet_analysis):
    """Generate recommendations based on snippet analysis"""
    recommendations = []
    
    promote_count = snippet_analysis["promote_count"]
    archive_count = snippet_analysis["archive_count"]
    total = promote_count + archive_count
    
    if total == 0:
        return ["No snippets found in current _inload"]
    
    efficiency = (promote_count / total) * 100
    
    if efficiency < 10:
        recommendations.extend([
            f"Very low extraction efficiency ({efficiency:.1f}%) suggests most ChatGPT conversations are casual",
            "Consider being more selective about which conversations to extract",
            "Focus extraction efforts on conversations with clear memoir/recovery/survival themes"
        ])
    elif efficiency < 25:
        recommendations.extend([
            f"Below-average extraction efficiency ({efficiency:.1f}%)",
            "Try to identify patterns in high-quality conversations for better targeting"
        ])
    else:
        recommendations.append(f"Good extraction efficiency ({efficiency:.1f}%) - worth continuing this approach")
    
    if promote_count > 0:
        recommendations.append(f"Promote {promote_count} high-quality snippets to organized folders")
    
    if archive_count > promote_count * 3:
        recommendations.append("Consider higher quality threshold to reduce low-value archiving work")
    
    return recommendations

def generate_post_processing_recommendations(results, snippet_analysis):
    """Generate recommendations after processing"""
    recommendations = []
    
    promoted = results["summary"]["promoted"]
    archived = results["summary"]["archived"]
    
    if promoted > 0:
        recommendations.extend([
            f"Successfully identified {promoted} valuable conversations from ChatGPT extraction efforts",
            "Review promoted snippets for integration into memoir or AI collaboration documentation",
            "Consider these conversations as templates for future high-value ChatGPT interactions"
        ])
    
    if archived > promoted * 2:
        recommendations.extend([
            f"High archive ratio ({archived} archived vs {promoted} promoted) suggests extraction process needs refinement",
            "Focus future ChatGPT conversations on memoir, recovery, or survival themes",
            "Consider shorter, more targeted conversation exports rather than full session dumps"
        ])
    
    # Efficiency feedback
    if promoted == 0:
        recommendations.append("No high-quality snippets found - reassess ChatGPT conversation approach for memoir relevance")
    
    return recommendations

def analyze_extraction_efficiency(snippet_files):
    """Analyze the efficiency of ChatGPT conversation extraction"""
    if not snippet_files:
        return {"efficiency": 0, "analysis": "No snippets found"}
    
    total = len(snippet_files)
    high_quality = len([f for f in snippet_files if f["quality"] >= 50])
    medium_quality = len([f for f in snippet_files if 20 <= f["quality"] < 50])
    
    efficiency = (high_quality + medium_quality * 0.5) / total * 100
    
    analysis_text = f"""
    Extraction efficiency: {efficiency:.1f}%
    - High quality: {high_quality}/{total} ({high_quality/total*100:.1f}%)
    - Medium quality: {medium_quality}/{total} ({medium_quality/total*100:.1f}%)
    - Total valuable: {high_quality + medium_quality}/{total}
    
    Efficiency assessment: {'Excellent' if efficiency >= 50 else 'Good' if efficiency >= 25 else 'Poor' if efficiency >= 10 else 'Very Poor'}
    """
    
    return {
        "efficiency_percent": round(efficiency, 1),
        "quality_breakdown": {
            "high": high_quality,
            "medium": medium_quality,
            "low": total - high_quality - medium_quality
        },
        "analysis": analysis_text.strip(),
        "recommendation": get_efficiency_recommendation(efficiency)
    }

def get_efficiency_recommendation(efficiency):
    """Get recommendation based on extraction efficiency"""
    if efficiency >= 50:
        return "Excellent extraction rate - continue current approach"
    elif efficiency >= 25:
        return "Good extraction rate - minor refinements could help"
    elif efficiency >= 10:
        return "Poor extraction rate - focus on memoir-relevant conversations only"
    else:
        return "Very poor extraction rate - reconsider extraction strategy entirely"

def calculate_extraction_efficiency(snippet_analysis):
    """Calculate extraction efficiency metrics"""
    total = snippet_analysis["promote_count"] + snippet_analysis["archive_count"]
    if total == 0:
        return {"efficiency": 0, "assessment": "No snippets processed"}
    
    efficiency = (snippet_analysis["promote_count"] / total) * 100
    
    return {
        "efficiency_percent": round(efficiency, 1),
        "high_value_count": snippet_analysis["promote_count"],
        "total_extracted": total,
        "assessment": "Excellent" if efficiency >= 50 else "Good" if efficiency >= 25 else "Poor" if efficiency >= 10 else "Very Poor"
    }
@router.get("/", response_class=HTMLResponse)
async def serve_api_documentation():
    """Serve API documentation at root endpoint"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flatline Codex API Documentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Monaco', monospace, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            line-height: 1.6;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0,0,0,0.4);
            border-radius: 12px;
            padding: 40px;
            border: 2px solid rgba(79, 158, 255, 0.3);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #4f9eff, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        h2 {
            color: #4f9eff;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(79, 158, 255, 0.3);
        }
        .subtitle { font-size: 1.2em; opacity: 0.8; margin-bottom: 30px; }
        .endpoint {
            background: rgba(0,0,0,0.3);
            border-left: 4px solid #4f9eff;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
        }
        .endpoint-header {
            font-family: 'Monaco', monospace;
            font-weight: bold;
            color: #6bcf7f;
            margin-bottom: 8px;
        }
        .method {
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-right: 10px;
        }
        .method.get { background: #6bcf7f; }
        .method.post { background: #4f9eff; }
        .endpoint-path { color: #ffd93d; }
        .endpoint-desc { color: #e0e0e0; margin-top: 5px; }
        .params {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 4px;
            margin-top: 8px;
            font-size: 0.9em;
            font-family: 'Monaco', monospace;
        }
        .example {
            background: rgba(107, 207, 127, 0.1);
            border-left: 3px solid #6bcf7f;
            padding: 10px;
            margin-top: 8px;
            font-size: 0.85em;
            font-family: 'Monaco', monospace;
            color: #b0e0b0;
        }
        .example-label {
            color: #6bcf7f;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .quick-links {
            background: rgba(79, 158, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .quick-links a {
            color: #4f9eff;
            text-decoration: none;
            margin-right: 20px;
            font-weight: bold;
        }
        .quick-links a:hover { color: #6bcf7f; text-decoration: underline; }
        .highlight-box {
            background: rgba(255, 215, 61, 0.1);
            border-left: 4px solid #ffd93d;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        code {
            background: rgba(0,0,0,0.5);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', monospace;
            color: #6bcf7f;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Flatline Codex API</h1>
        <p class="subtitle">Rick's 4D Memoir Organization System</p>
        
        <div class="quick-links">
            <strong>Quick Access:</strong>
            <a href="/viz">4D Visualization</a>
            <a href="/viz-clusters">Cluster View</a>
            <a href="/docs">OpenAPI Docs</a>
        </div>
        
        <div class="highlight-box">
            <strong>🔥 Most Used Endpoints:</strong><br>
            <code>GET /viz</code> - Interactive 4D content explorer<br>
            <code>GET /api/tesseract/memoir-readiness</code> - Check memoir production status<br>
            <code>GET /api/inload/mining-dashboard</code> - View unprocessed content<br>
            <code>GET /api/tags/consolidation-status</code> - Tag cleanup progress
        </div>
        
        <h2>Visualization & Dashboard</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/viz</span>
            </div>
            <div class="endpoint-desc">
                Interactive bubble chart showing content across Structure × Transmission × Purpose × Terrain dimensions.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                http://localhost:5050/viz
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/viz-clusters</span>
            </div>
            <div class="endpoint-desc">
                Cluster visualization showing natural content groupings by 4D coordinates with quality metrics.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                http://localhost:5050/viz-clusters
            </div>
        </div>
        
        <h2>Training Data Analysis</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/training/summary</span>
            </div>
            <div class="endpoint-desc">
                Overall training results from 30-file analysis including quality distributions and memoir potential.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/training/summary
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/training/high-quality</span>
            </div>
            <div class="endpoint-desc">
                Fetch chunks above quality threshold, optionally filtered by theme.
            </div>
            <div class="params">min_score (60), max_results (50), theme_filter (optional)</div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl "http://localhost:5050/api/training/high-quality?min_score=80&max_results=20"
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/training/chunks/search</span>
            </div>
            <div class="endpoint-desc">
                Search training chunks with multiple filters: text, theme, quality, coordinates.
            </div>
            <div class="params">query, theme, min_score, coordinate, max_results (100)</div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl "http://localhost:5050/api/training/chunks/search?query=recovery&min_score=50"
            </div>
        </div>
        
        <h2>Tag Management</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/tags/audit</span>
            </div>
            <div class="endpoint-desc">
                Comprehensive tag analysis: total tags, instances, top 50, unique list.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/tags/audit
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/tags/consolidation-status</span>
            </div>
            <div class="endpoint-desc">
                Current tag consolidation status with completeness percentage and next steps.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/tags/consolidation-status
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/tags/consolidate</span>
            </div>
            <div class="endpoint-desc">
                Consolidate tags redundant with Tesseract coordinates.
            </div>
            <div class="params">dry_run (true)</div>
            <div class="example">
                <div class="example-label">Example (dry run):</div>
                curl -X POST "http://localhost:5050/api/tags/consolidate?dry_run=true"
                <div style="margin-top: 5px;">
                <div class="example-label">Example (execute):</div>
                curl -X POST "http://localhost:5050/api/tags/consolidate?dry_run=false"
                </div>
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/tags/execute-technical-cleanup</span>
            </div>
            <div class="endpoint-desc">
                Remove technical artifacts and standardize formats.
            </div>
            <div class="params">dry_run (true)</div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST "http://localhost:5050/api/tags/execute-technical-cleanup?dry_run=true"
            </div>
        </div>
        
        <h2>Tesseract 4D System</h2>
        
        <div class="highlight-box">
            <strong>4D Dimensions:</strong><br>
            <strong>X (Structure):</strong> archetype, protocol, shadowcast, expansion, summoning<br>
            <strong>Y (Transmission):</strong> narrative, text, reference, data<br>
            <strong>Z (Purpose):</strong> tell-story, help-addict, prevent-death, financial-amends, help-world<br>
            <strong>W (Terrain):</strong> obvious, complicated, complex, chaotic, confused
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/tesseract/extract-coordinates</span>
            </div>
            <div class="endpoint-desc">
                Map entire codex into 4D space with dimensional distributions and memoir spine candidates.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST http://localhost:5050/api/tesseract/extract-coordinates
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/tesseract/memoir-readiness</span>
            </div>
            <div class="endpoint-desc">
                Comprehensive memoir readiness using 4D analysis with production recommendations.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/tesseract/memoir-readiness
            </div>
        </div>
        
        <h2>Content Analysis</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/analysis/content-fingerprint</span>
            </div>
            <div class="endpoint-desc">
                Create content fingerprints: document archetypes, structural signatures, cross-references.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST http://localhost:5050/api/analysis/content-fingerprint
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/analysis/memoir-readiness</span>
            </div>
            <div class="endpoint-desc">
                Assess memoir production readiness with content inventory and missing chapters.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/analysis/memoir-readiness
            </div>
        </div>
        
        <h2>_inload Content Mining</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/inload/mining-dashboard</span>
            </div>
            <div class="endpoint-desc">
                Comprehensive _inload status: quality distribution, themes, processing recommendations.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/inload/mining-dashboard
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/inload/scan-content</span>
            </div>
            <div class="endpoint-desc">
                Scan all _inload directories with classifications: high_value, memoir_gold, recovery_threads.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST http://localhost:5050/api/inload/scan-content
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/inload/priority-files</span>
            </div>
            <div class="endpoint-desc">
                Get priority files from category for manual review.
            </div>
            <div class="params">category (high_value), limit (20)</div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl "http://localhost:5050/api/inload/priority-files?category=memoir_gold&limit=10"
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/inload/batch-move</span>
            </div>
            <div class="endpoint-desc">
                Batch move files with backup. Body: [{source_path, destination_path}]
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST http://localhost:5050/api/inload/batch-move \\<br>
                &nbsp;&nbsp;-H "Content-Type: application/json" \\<br>
                &nbsp;&nbsp;-d '{"moves":[{"source_path":"_inload/file1.md","destination_path":"memoir/file1.md"}]}'
            </div>
        </div>
        
        <h2>Snippet Processing</h2>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method post">POST</span>
                <span class="endpoint-path">/api/snippets/analyze</span>
            </div>
            <div class="endpoint-desc">
                Analyze ChatGPT snippet quality and suggest reorganization.
            </div>
            <div class="params">quality_threshold (20)</div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl -X POST "http://localhost:5050/api/snippets/analyze?quality_threshold=30"
            </div>
        </div>
        
        <div class="endpoint">
            <div class="endpoint-header">
                <span class="method get">GET</span>
                <span class="endpoint-path">/api/snippets/stats</span>
            </div>
            <div class="endpoint-desc">
                Statistics on snippet extraction: efficiency metrics, quality distribution.
            </div>
            <div class="example">
                <div class="example-label">Example:</div>
                curl http://localhost:5050/api/snippets/stats
            </div>
        </div>
        
        <div class="highlight-box">
            <h3>Common Patterns</h3>
            <p><strong>Dry Run:</strong> Most POST endpoints default to <code>dry_run=true</code> for preview.</p>
            <p><strong>Backups:</strong> File operations auto-create backups unless disabled.</p>
            <p><strong>Quality:</strong> 80+ = memoir gold, 50+ = medium, &lt;20 = low.</p>
        </div>
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid rgba(79, 158, 255, 0.3); text-align: center; opacity: 0.7;">
            <p>Flatline Codex API - Base: <code>http://localhost:5050</code></p>
        </div>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@router.get("/review", response_class=HTMLResponse)
async def serve_review_interface():
    """Serve the chunk review interface"""
    # Use a raw string to avoid escape issues
    return HTMLResponse(content=open('app/static/review.html').read())

# Helper functions for review queue
def calculate_review_priority(chunk: dict) -> float:
    """Calculate review priority for a chunk"""
    quality = chunk.get('quality_score', 0)
    patterns = chunk.get('patterns', {})
    coords = chunk.get('coordinates', {})
    
    priority = 0.0
    
    # High quality = high priority
    if quality >= 80:
        priority += 0.4
    elif quality >= 50:
        priority += 0.2
    
    # Strong patterns = worth reviewing
    pattern_strength = sum(patterns.values())
    if pattern_strength > 10:
        priority += 0.3
    elif pattern_strength > 5:
        priority += 0.2
    
    # Recovery/memoir focused = important
    if patterns.get('recovery_markers', 0) > 2:
        priority += 0.2
    if patterns.get('memoir_markers', 0) > 2:
        priority += 0.2
    
    # Story-focused purpose
    if coords.get('z_purpose') == 'tell-story':
        priority += 0.1
    
    return min(1.0, priority)

def get_review_reason(chunk: dict) -> list:
    """Generate reasons why this chunk needs review"""
    reasons = []
    quality = chunk.get('quality_score', 0)
    patterns = chunk.get('patterns', {})
    coords = chunk.get('coordinates', {})
    
    if quality >= 80:
        reasons.append("High memoir potential (quality 80+)")
    
    if coords.get('z_purpose') == 'tell-story':
        reasons.append("Story-focused content")
    
    if patterns.get('memoir_markers', 0) > 3:
        reasons.append("Strong memoir markers detected")
    
    if patterns.get('recovery_markers', 0) > 2:
        reasons.append("Recovery narrative content")
    
    if 50 <= quality < 80:
        reasons.append("Borderline quality - needs decision")
    
    if not reasons:
        reasons.append("Standard review")
    
    return reasons

def suggest_chunk_destination(coords: dict, quality: float) -> str:
    """Suggest where a chunk should be filed"""
    z_purpose = coords.get('z_purpose', 'tell-story')
    x_structure = coords.get('x_structure', 'archetype')
    
    # Map purpose to base folder
    purpose_folders = {
        'tell-story': 'memoir',
        'help-addict': 'recovery',
        'prevent-death-poverty': 'survival',
        'financial-amends': 'work-amends',
        'help-world': 'contribution'
    }
    
    base = purpose_folders.get(z_purpose, 'memoir')
    
    # High quality memoir goes to spine
    if quality >= 80 and z_purpose == 'tell-story':
        return f"{base}/spine/foundations"
    
    # Otherwise organize by structure
    structure_folders = {
        'archetype': 'personas',
        'protocol': 'practices',
        'shadowcast': 'explorations',
        'expansion': 'context',
        'summoning': 'activations'
    }
    
    subfolder = structure_folders.get(x_structure, 'general')
    return f"{base}/{subfolder}"

@router.get("/api/inload/mining-dashboard")
async def get_mining_dashboard(format: str = "json"):
    """Get comprehensive dashboard of _inload mining status"""
    from .content_mining import InloadContentMiner
    
    try:
        # Scan current content
        miner = InloadContentMiner(VAULT_PATH)
        miner.scan_all_inload_content()
        miner.classify_content()
        
        # Find snippet-tagged files
        snippet_files = []
        total_ai_collaboration = len(miner.mining_results["ai_collaboration"])
        
        for file_path, signature in miner.content_signatures.items():
            if signature.get('file_path') and miner.is_snippet_file_by_signature(signature):
                snippet_files.append({
                    "file": file_path,
                    "quality": signature["quality_score"],
                    "theme": signature["dominant_theme"],
                    "word_count": signature["word_count"]
                })
        
        # Calculate statistics
        if snippet_files:
            qualities = [f["quality"] for f in snippet_files]
            avg_quality = sum(qualities) / len(qualities)
            high_quality_count = len([q for q in qualities if q >= 20])
            total_words = sum(f["word_count"] for f in snippet_files)
        else:
            avg_quality = 0
            high_quality_count = 0
            total_words = 0
        
        # Calculate metrics
        total_files = len(miner.content_signatures)
        total_words_all = sum(sig['word_count'] for sig in miner.content_signatures.values())
        
        # Quality distribution
        quality_distribution = defaultdict(int)
        for sig in miner.content_signatures.values():
            quality_range = f"{int(sig['quality_score'])}-{int(sig['quality_score'])+1}"
            quality_distribution[quality_range] += 1
        
        # Theme distribution
        theme_distribution = defaultdict(int)
        for sig in miner.content_signatures.values():
            theme_distribution[sig['dominant_theme']] += 1
        
        # Calculate processing recommendations
        high_priority_count = len(miner.mining_results["high_value"]) + len(miner.mining_results["memoir_gold"])
        medium_priority_count = len(miner.mining_results["recovery_threads"]) + len(miner.mining_results["job_survival"])
        archive_candidate_count = len(miner.mining_results["archive_candidates"])
        
        # Build response data
        response_data = {
            "status": "success",
            "overview": {
                "total_files": total_files,
                "total_words": total_words_all,
                "avg_quality": round(sum(sig['quality_score'] for sig in miner.content_signatures.values()) / total_files, 2) if total_files > 0 else 0
            },
            "distributions": {
                "quality": dict(quality_distribution),
                "themes": dict(theme_distribution)
            },
            "processing_recommendations": {
                "high_priority": high_priority_count,
                "medium_priority": medium_priority_count,
                "archive_candidates": archive_candidate_count,
                "processing_order": [
                    f"1. Review {high_priority_count} high-priority files first",
                    f"2. Process {medium_priority_count} medium-priority files",
                    f"3. Consider archiving {archive_candidate_count} low-quality files"
                ]
            },
            "classifications": {
                category: len(files)
                for category, files in miner.mining_results.items()
            }
        }
        
        # Return HTML if requested
        if format.lower() == "html":
            return HTMLResponse(content=generate_mining_dashboard_html(response_data))
        
        # Default JSON response
        return response_data
        
    except Exception as e:
        error_response = {
            "status": "error",
            "error": str(e),
            "message": "Failed to generate mining dashboard"
        }
        if format.lower() == "html":
            return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>")
        return error_response


def generate_mining_dashboard_html(data: dict) -> str:
    """Generate HTML visualization of mining dashboard data"""
    
    overview = data["overview"]
    distributions = data["distributions"]
    processing = data["processing_recommendations"]
    classifications = data["classifications"]
    
    # Generate quality distribution chart data
    quality_items = sorted(distributions["quality"].items(), key=lambda x: int(x[0].split('-')[0]))
    quality_chart_html = ""
    max_quality_count = max(distributions["quality"].values()) if distributions["quality"] else 1
    
    for quality_range, count in quality_items[:20]:  # Show top 20 ranges
        percentage = (count / max_quality_count) * 100
        quality_chart_html += f"""
        <div class="chart-row">
            <div class="chart-label">{quality_range}</div>
            <div class="chart-bar-container">
                <div class="chart-bar" style="width: {percentage}%"></div>
                <span class="chart-value">{count}</span>
            </div>
        </div>
        """
    
    # Generate theme distribution
    theme_colors = {
        "ai_collaboration": "#4f9eff",
        "survival": "#ffd93d",
        "recovery": "#6bcf7f",
        "creative": "#a78bfa",
        "technical": "#ff6b6b",
        "emotional": "#ff9f68",
        "memoir": "#fc85ae",
        "unclear": "#888888"
    }
    
    theme_chart_html = ""
    max_theme_count = max(distributions["themes"].values()) if distributions["themes"] else 1
    
    for theme, count in sorted(distributions["themes"].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / max_theme_count) * 100
        color = theme_colors.get(theme, "#999999")
        theme_chart_html += f"""
        <div class="chart-row">
            <div class="chart-label">{theme.replace('_', ' ').title()}</div>
            <div class="chart-bar-container">
                <div class="chart-bar" style="width: {percentage}%; background: {color};"></div>
                <span class="chart-value">{count}</span>
            </div>
        </div>
        """
    
    # Generate classification cards
    classification_cards_html = ""
    classification_colors = {
        "high_value": "#6bcf7f",
        "memoir_gold": "#fc85ae",
        "recovery_threads": "#4f9eff",
        "job_survival": "#ffd93d",
        "ai_collaboration": "#a78bfa",
        "creative_fragments": "#ff9f68",
        "archive_candidates": "#888888"
    }
    
    for category, count in classifications.items():
        color = classification_colors.get(category, "#999999")
        display_name = category.replace('_', ' ').title()
        classification_cards_html += f"""
        <div class="stat-card" style="border-color: {color};">
            <div class="stat-value" style="color: {color};">{count}</div>
            <div class="stat-label">{display_name}</div>
        </div>
        """
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>_inload Mining Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            padding: 30px 0;
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            margin-bottom: 30px;
            border: 2px solid rgba(79, 158, 255, 0.3);
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #4f9eff, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .subtitle {{
            font-size: 1.1em;
            opacity: 0.8;
        }}
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .overview-card {{
            background: rgba(0,0,0,0.3);
            padding: 25px;
            border-radius: 12px;
            border: 2px solid rgba(79, 158, 255, 0.2);
        }}
        .overview-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #4f9eff;
            margin-bottom: 5px;
        }}
        .overview-label {{
            opacity: 0.7;
            font-size: 1em;
        }}
        .section {{
            background: rgba(0,0,0,0.3);
            padding: 25px;
            border-radius: 12px;
            border: 2px solid rgba(79, 158, 255, 0.2);
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #4f9eff;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(79, 158, 255, 0.3);
        }}
        .chart-row {{
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }}
        .chart-label {{
            width: 100px;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
            color: #ffd93d;
        }}
        .chart-bar-container {{
            flex: 1;
            position: relative;
            height: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            overflow: hidden;
        }}
        .chart-bar {{
            height: 100%;
            background: linear-gradient(90deg, #4f9eff, #6bcf7f);
            transition: width 0.3s ease;
            border-radius: 4px;
        }}
        .chart-value {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-weight: bold;
            color: white;
            font-size: 0.9em;
        }}
        .classifications-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}
        .stat-card {{
            background: rgba(0,0,0,0.4);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .stat-label {{
            opacity: 0.8;
            font-size: 0.95em;
        }}
        .processing-steps {{
            background: rgba(255, 215, 61, 0.1);
            border-left: 4px solid #ffd93d;
            padding: 20px;
            border-radius: 8px;
        }}
        .processing-steps ol {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        .processing-steps li {{
            margin-bottom: 8px;
            color: #e0e0e0;
        }}
        .api-link {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
        }}
        .api-link a {{
            color: #4f9eff;
            text-decoration: none;
            font-family: 'Monaco', monospace;
        }}
        .api-link a:hover {{
            color: #6bcf7f;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 _inload Mining Dashboard</h1>
            <p class="subtitle">Content Analysis & Processing Recommendations</p>
        </header>
        
        <div class="overview-grid">
            <div class="overview-card">
                <div class="overview-value">{overview['total_files']:,}</div>
                <div class="overview-label">Total Files Scanned</div>
            </div>
            <div class="overview-card">
                <div class="overview-value">{overview['total_words']:,}</div>
                <div class="overview-label">Total Words</div>
            </div>
            <div class="overview-card">
                <div class="overview-value">{overview['avg_quality']:.1f}</div>
                <div class="overview-label">Average Quality Score</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Content Classifications</h2>
            <div class="classifications-grid">
                {classification_cards_html}
            </div>
        </div>
        
        <div class="section">
            <h2>Processing Recommendations</h2>
            <div class="processing-steps">
                <strong>Recommended Processing Order:</strong>
                <ol>
                    {''.join(f'<li>{step.split(". ", 1)[1]}</li>' for step in processing['processing_order'])}
                </ol>
            </div>
        </div>
        
        <div class="section">
            <h2>Theme Distribution</h2>
            {theme_chart_html}
        </div>
        
        <div class="section">
            <h2>Quality Score Distribution (Top 20 Ranges)</h2>
            {quality_chart_html}
        </div>
        
        <div class="api-link">
            <p>View JSON data: <a href="/api/inload/mining-dashboard?format=json">/api/inload/mining-dashboard?format=json</a></p>
            <p style="margin-top: 10px;">Return to: <a href="/">API Documentation</a></p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content
