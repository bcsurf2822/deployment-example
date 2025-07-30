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

def deploy_stack(mode=None, deployment_type=None, with_rag=False, action="up", project_name="pydantic-agent"):
    """Deploy or stop the agent stack based on mode or deployment type."""
    
    # Build base command
    cmd = ["docker", "compose", "-p", project_name]
    
    # Handle deployment type (new cloud deployment)
    if deployment_type:
        cmd.extend(["-f", "docker-compose.yml"])
        
        if deployment_type == "cloud":
            if not os.path.exists("docker-compose.caddy.yml"):
                print("Error: docker-compose.caddy.yml not found for cloud deployment")
                sys.exit(1)
            cmd.extend(["-f", "docker-compose.caddy.yml"])
            print("Cloud deployment: Including Caddy service")
        elif deployment_type == "local":
            print("Local deployment: Using base docker-compose.yml")
        else:
            print(f"Error: Invalid deployment type '{deployment_type}'")
            sys.exit(1)
    
    # Handle legacy mode-based deployment
    elif mode:
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
    
    else:
        print("Error: Either --mode or --type must be specified")
        sys.exit(1)
    
    # Add action (up/down)
    if action == "up":
        if with_rag:
            # Profile must come before 'up' command
            cmd.extend(["--profile", "with-rag"])
            print("Including RAG pipeline services")
        cmd.extend(["up", "-d", "--build"])
        deployment_name = deployment_type or mode
        print(f"Starting {deployment_name} deployment with project name '{project_name}' (rebuilding containers)...")
    elif action == "down":
        if with_rag:
            # Profile must come before 'down' command
            cmd.extend(["--profile", "with-rag"])
            print("Including RAG pipeline services for shutdown")
        cmd.extend(["down"])
        deployment_name = deployment_type or mode
        print(f"Stopping {deployment_name} deployment with project name '{project_name}'...")
    elif action == "logs":
        if with_rag:
            cmd.extend(["--profile", "with-rag"])
        cmd.extend(["logs", "-f"])
        deployment_name = deployment_type or mode
        print(f"Showing logs for {deployment_name} deployment...")
    elif action == "ps":
        cmd.extend(["ps"])
        deployment_name = deployment_type or mode
        print(f"Showing status for {deployment_name} deployment...")
    
    # Execute command
    run_command(cmd)
    
    if action == "up":
        deployment_name = deployment_type or mode
        print(f"\n✅ {deployment_name.title()} deployment completed successfully!")
        
        if deployment_type == "cloud":
            print("\n📝 Cloud Deployment Notes:")
            print("- Standalone deployment with integrated Caddy reverse proxy")
            print("- Configure AGENT_API_HOSTNAME and FRONTEND_HOSTNAME in .env")
            print("- Caddy will automatically provision SSL certificates")
            print("- Services accessible via configured hostnames")
            print("\n🔍 View logs: python deploy.py --type cloud --logs")
            print("📊 Check status: python deploy.py --type cloud --ps")
            
        elif deployment_type == "local":
            print("\n📝 Local Deployment Notes:")
            print("- Frontend: http://localhost:3000")
            print("- Agent API: http://localhost:8001")
            print("- Using base docker-compose.yml configuration")
            print("\n🔍 View logs: python deploy.py --type local --logs")
            print("📊 Check status: python deploy.py --type local --ps")
            
        elif mode == "dev":
            print("\n📝 Development Deployment Notes:")
            print("- Frontend: http://localhost:3000")
            print("- Agent API: http://localhost:8001")
            print("- Hot reload enabled for all services")
            print("- Source code mounted as volumes")
            if with_rag:
                print("- RAG pipeline monitoring Google Drive and local directory")
                print("- Configure watch paths in .env file")
            print(f"\n🔍 View logs: python deploy.py --mode {mode} --logs")
            print(f"📊 Check status: python deploy.py --mode {mode} --ps")
            
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
        deployment_name = deployment_type or mode
        print(f"\n✅ {deployment_name.title()} deployment stopped successfully!")

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
  
  # Cloud deployment (standalone with Caddy)
  python deploy.py --type cloud
  
  # Local deployment (without Caddy)
  python deploy.py --type local
  
  # Stop development deployment
  python deploy.py --down --mode dev
  
  # Stop cloud deployment
  python deploy.py --down --type cloud
  
  # View logs (mode-based)
  python deploy.py --mode dev --logs
  
  # View logs (type-based)
  python deploy.py --type cloud --logs
  
  # Check status
  python deploy.py --mode dev --ps
        """
    )
    
    # Create mutually exclusive group for mode vs type
    deployment_group = parser.add_mutually_exclusive_group(required=True)
    
    deployment_group.add_argument(
        '--mode', 
        choices=['dev', 'prod'], 
        help='Deployment mode: dev (development) or prod (production)'
    )
    
    deployment_group.add_argument(
        '--type',
        choices=['local', 'cloud'],
        help='Deployment type: local (without Caddy) or cloud (with Caddy reverse proxy)'
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
    deploy_stack(
        mode=args.mode,
        deployment_type=getattr(args, 'type', None),
        with_rag=args.with_rag,
        action=action,
        project_name=args.project
    )

if __name__ == "__main__":
    main()