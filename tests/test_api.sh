#!/bin/bash
# Test script for API endpoints

BASE_URL="http://127.0.0.1:8765"

echo "🧪 Testing Calibre Intelligent Library API"
echo "=========================================="

# Test 1: Root endpoint
echo -e "\n1️⃣ Testing root endpoint..."
curl -s "$BASE_URL/" | python3 -m json.tool

# Test 2: Health check
echo -e "\n2️⃣ Testing health check..."
curl -s "$BASE_URL/health" | python3 -m json.tool

# Test 3: Stats
echo -e "\n3️⃣ Testing stats..."
curl -s "$BASE_URL/stats" | python3 -m json.tool

# Test 4: Get book (if exists)
echo -e "\n4️⃣ Testing get book (ID 1)..."
curl -s "$BASE_URL/book/1" | python3 -m json.tool

echo -e "\n✅ API tests completed!"
