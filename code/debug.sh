# Test different API endpoints to see what data is available

echo "=== Testing /api/training/summary ==="
curl -s "http://localhost:5050/api/training/summary" | python -m json.tool | head -50

echo -e "\n\n=== Testing /api/training/chunks/search (no params) ==="
curl -s "http://localhost:5050/api/training/chunks/search" | python -m json.tool | head -30

echo -e "\n\n=== Testing /api/training/chunks/search (max 500) ==="
curl -s "http://localhost:5050/api/training/chunks/search?max_results=500" | python -m json.tool | head -30

echo -e "\n\n=== Testing /api/training/high-quality (lower threshold) ==="
curl -s "http://localhost:5050/api/training/high-quality?min_score=0&max_results=500" | python -m json.tool | head -30

echo -e "\n\n=== Testing /api/training/batches ==="
curl -s "http://localhost:5050/api/training/batches" | python -m json.tool
