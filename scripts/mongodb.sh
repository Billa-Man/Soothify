#!/bin/bash

# MongoDB Management Script for Soothify

case "$1" in
  start)
    echo "🟢 Starting MongoDB..."
    brew services start mongodb-community
    echo "✅ MongoDB started on mongodb://localhost:27017"
    ;;
  stop)
    echo "🔴 Stopping MongoDB..."
    brew services stop mongodb-community
    echo "✅ MongoDB stopped"
    ;;
  status)
    echo "📊 MongoDB Status:"
    brew services list | grep mongodb
    echo ""
    echo "🔌 Port Check:"
    lsof -i :27017 || echo "No process listening on port 27017"
    ;;
  connect)
    echo "🔗 Connecting to MongoDB..."
    mongosh mongodb://localhost:27017/soothify
    ;;
  test)
    echo "🧪 Testing MongoDB connection..."
    mongosh --eval "db.adminCommand('hello')" --quiet
    if [ $? -eq 0 ]; then
      echo "✅ MongoDB is running and accessible"
    else
      echo "❌ MongoDB connection failed"
    fi
    ;;
  *)
    echo "MongoDB Management for Soothify"
    echo ""
    echo "Usage: $0 {start|stop|status|connect|test}"
    echo ""
    echo "Commands:"
    echo "  start   - Start MongoDB service"
    echo "  stop    - Stop MongoDB service"
    echo "  status  - Check MongoDB status"
    echo "  connect - Connect to Soothify database"
    echo "  test    - Test MongoDB connection"
    echo ""
    echo "Current MongoDB URI: mongodb://localhost:27017"
    echo "Database Name: soothify"
    ;;
esac
