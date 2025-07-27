#!/usr/bin/env python3
"""
deploy.py

This script deploys the Pydantic AI Agent stack with different configurations:
- Development: Local development with hot reload
- Production: Production deployment with optimized settings
- With RAG: Include RAG pipeline services

Usage:
  python deploy.py --mode dev                    # Development mode
  python deploy.py --mode prod                   # Production mode
  python deploy.py --mode dev --with-rag        # Dev mode with RAG pipeline
  python deploy.py --down --mode dev            # Stop services
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and print it."""
    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        sys.exit(1)

def validate_environment():
    """Check that required files exist."""
    required_files = [".env", "docker-compose.yml"]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"Error: Required file '{file}' not found in current directory")
            sys.exit(1)
    
    # Check for environment variables
    if not os.path.exists(".env"):
        print("Warning: .env file not found. Using default values.")

def deploy_stack(mode, with_rag, action="up", project_name="pydantic-agent"):
    """Deploy or stop the agent stack based on mode."""
    
    # Build base command
    cmd = ["docker", "compose", "-p", project_name]
    
    # Add appropriate compose files based on mode
    if mode == "dev":
        if not os.path.exists("docker-compose.dev.yml"):
            print("Error: docker-compose.dev.yml not found for development mode")
            sys.exit(1)
        cmd.extend(["-f", "docker-compose.dev.yml"])
        print("Development mode: Using docker-compose.dev.yml")
        
    elif mode == "prod":
        if not os.path.exists("docker-compose.yml"):
            print("Error: docker-compose.yml not found for production mode")
            sys.exit(1)
        cmd.extend(["-f", "docker-compose.yml"])
        print("Production mode: Using docker-compose.yml")
    
    else:
        print(f"Error: Invalid mode '{mode}'")
        sys.exit(1)
    
    # Add action (up/down)
    if action == "up":
        if with_rag:
            # Profile must come before 'up' command
            cmd.extend(["--profile", "with-rag"])
            print("Including RAG pipeline services")
        cmd.extend(["up", "-d", "--build"])
        print(f"Starting {mode} deployment with project name '{project_name}' (rebuilding containers)...")
    elif action == "down":
        if with_rag:
            # Profile must come before 'down' command
            cmd.extend(["--profile", "with-rag"])
            print("Including RAG pipeline services for shutdown")
        cmd.extend(["down"])
        print(f"Stopping {mode} deployment with project name '{project_name}'...")
    elif action == "logs":
        if with_rag:
            cmd.extend(["--profile", "with-rag"])
        cmd.extend(["logs", "-f"])
        print(f"Showing logs for {mode} deployment...")
    elif action == "ps":
        cmd.extend(["ps"])
        print(f"Showing status for {mode} deployment...")
    
    # Execute command
    run_command(cmd)
    
    if action == "up":
        print(f"\n✅ {mode.title()} deployment completed successfully!")
        
        if mode == "dev":
            print("\n📝 Development Deployment Notes:")
            print("- Frontend: http://localhost:3000")
            print("- Agent API: http://localhost:8001")
            print("- Hot reload enabled for all services")
            print("- Source code mounted as volumes")
            if with_rag:
                print("- RAG pipeline monitoring Google Drive and local directory")
                print("- Configure watch paths in .env file")
            
        elif mode == "prod":
            print("\n📝 Production Deployment Notes:")
            print("- Frontend: http://localhost:3000")
            print("- Agent API: http://localhost:8001") 
            print("- Optimized for production use")
            print("- No source code mounting")
            if with_rag:
                print("- RAG pipeline running in production mode")
        
        print(f"\n🔍 View logs: python deploy.py --mode {mode} --logs")
        print(f"📊 Check status: python deploy.py --mode {mode} --ps")
            
    elif action == "down":
        print(f"\n✅ {mode.title()} deployment stopped successfully!")

def check_docker():
    """Check if Docker and Docker Compose are installed."""
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        subprocess.run(["docker", "compose", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker and Docker Compose are required but not found.")
        print("Please install Docker Desktop or Docker Engine with Compose plugin.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Deploy the Pydantic AI Agent stack',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Development deployment
  python deploy.py --mode dev
  
  # Development with RAG pipeline
  python deploy.py --mode dev --with-rag
  
  # Production deployment  
  python deploy.py --mode prod
  
  # Stop development deployment
  python deploy.py --down --mode dev
  
  # Stop development deployment with RAG
  python deploy.py --down --mode dev --with-rag
  
  # View logs
  python deploy.py --mode dev --logs
  
  # Check status
  python deploy.py --mode dev --ps
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['dev', 'prod'], 
        required=True,
        help='Deployment mode: dev (development) or prod (production)'
    )
    
    parser.add_argument(
        '--with-rag', 
        action='store_true',
        help='Include RAG pipeline services (Google Drive and Local Files)'
    )
    
    parser.add_argument(
        '--project', 
        default='pydantic-agent',
        help='Docker Compose project name (default: pydantic-agent)'
    )
    
    parser.add_argument(
        '--down', 
        action='store_true',
        help='Stop and remove containers instead of starting them'
    )
    
    parser.add_argument(
        '--logs', 
        action='store_true',
        help='Show logs for running containers'
    )
    
    parser.add_argument(
        '--ps', 
        action='store_true',
        help='Show status of containers'
    )
    
    args = parser.parse_args()
    
    # Check Docker installation
    check_docker()
    
    # Validate environment
    validate_environment()
    
    # Determine action
    if args.down:
        action = "down"
    elif args.logs:
        action = "logs"
    elif args.ps:
        action = "ps"
    else:
        action = "up"
    
    # Deploy
    deploy_stack(args.mode, args.with_rag, action, args.project)

if __name__ == "__main__":
    main()