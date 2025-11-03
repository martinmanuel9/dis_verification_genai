#!/usr/bin/env python3
"""
Database Backup Manager for Litigation GenAI
Programmatic backup and restore for PostgreSQL, ChromaDB, and Redis

Usage:
    python backup_manager.py backup [--db-only]
    python backup_manager.py restore <backup_dir> [--skip-confirmation]
    python backup_manager.py list
    python backup_manager.py cleanup --keep <n>
"""

import os
import sys
import subprocess
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import argparse


class BackupManager:
    """Manages database backups for Litigation GenAI system"""

    def __init__(self, backup_root: str = "./backups"):
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(exist_ok=True)

        # Container names from docker-compose.yml
        self.containers = {
            "postgres": "postgres_db",
            "chromadb": "chromadb",
            "redis": "redis"
        }

        # Volume names from docker-compose.yml
        self.volumes = {
            "postgres": "litigation_genai_postgres_data",
            "chromadb": "litigation_genai_chroma_data",
            "redis": "litigation_genai_redis_data"
        }

    def run_command(self, cmd: List[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
        """Run a shell command with error handling"""
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(cmd)}")
            print(f"   Error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            raise

    def check_container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running"""
        result = self.run_command(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture=True,
            check=False
        )
        return container_name in result.stdout.split('\n')

    def validate_environment(self) -> bool:
        """Validate that all required containers are running"""
        print("Checking Docker containers...")
        all_running = True

        for service, container in self.containers.items():
            if self.check_container_running(container):
                print(f"  ✓ {service} ({container})")
            else:
                print(f"  ✗ {service} ({container}) - NOT RUNNING")
                all_running = False

        if not all_running:
            print("\n Not all containers are running!")
            print("   Start services with: docker compose up -d")
            return False

        print("All containers are running\n")
        return True

    def backup_postgres(self, backup_dir: Path) -> bool:
        """Backup PostgreSQL database using pg_dumpall"""
        print("[PostgreSQL] Backing up database...")
        backup_file = backup_dir / "postgres_backup.sql"

        try:
            with open(backup_file, 'w') as f:
                self.run_command(
                    ["docker", "exec", self.containers["postgres"],
                     "pg_dumpall", "-U", "g3nA1-user"],
                    check=True,
                )
                result = subprocess.run(
                    ["docker", "exec", self.containers["postgres"],
                     "pg_dumpall", "-U", "g3nA1-user"],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )

            size = backup_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✓ PostgreSQL backup complete ({size:.2f} MB)")
            return True
        except Exception as e:
            print(f"✗ PostgreSQL backup failed: {e}")
            return False

    def backup_chromadb(self, backup_dir: Path) -> bool:
        """Backup ChromaDB vector database"""
        print("[ChromaDB] Backing up vector database...")
        chroma_backup = backup_dir / "chromadb_data"

        try:
            # Copy from container (path: /chroma/chroma per docker-compose.yml)
            self.run_command(
                ["docker", "cp",
                 f"{self.containers['chromadb']}:/chroma/chroma",
                 str(chroma_backup)],
                check=True
            )

            # Calculate size
            total_size = sum(
                f.stat().st_size for f in chroma_backup.rglob('*') if f.is_file()
            ) / (1024 * 1024)  # MB

            print(f"ChromaDB backup complete ({total_size:.2f} MB)")
            return True
        except Exception as e:
            print(f"ChromaDB backup failed: {e}")
            return False

    def backup_redis(self, backup_dir: Path) -> bool:
        """Backup Redis cache"""
        print("[Redis] Backing up cache...")
        redis_backup = backup_dir / "redis_data"

        try:
            # Trigger Redis BGSAVE
            self.run_command(
                ["docker", "exec", self.containers["redis"],
                 "redis-cli", "BGSAVE"],
                check=False  # Don't fail if BGSAVE fails
            )

            # Wait briefly for save to complete
            import time
            time.sleep(2)

            # Copy data directory
            self.run_command(
                ["docker", "cp",
                 f"{self.containers['redis']}:/data",
                 str(redis_backup)],
                check=True
            )

            total_size = sum(
                f.stat().st_size for f in redis_backup.rglob('*') if f.is_file()
            ) / (1024 * 1024)  # MB

            print(f"Redis backup complete ({total_size:.2f} MB)")
            return True
        except Exception as e:
            print(f"Redis backup failed: {e}")
            return False

    def backup_application_data(self, backup_dir: Path) -> int:
        """Backup application data (images, local data, migrations)"""
        print("[Application] Backing up application data...")
        count = 0

        # Backup stored images
        if Path("./stored_images").exists():
            shutil.copytree("./stored_images", backup_dir / "stored_images")
            print("  ✓ Stored images")
            count += 1

        # Backup local data
        if Path("./data").exists():
            shutil.copytree("./data", backup_dir / "local_data")
            print("  ✓ Local data")
            count += 1

        # Backup migrations
        if Path("./migrations").exists():
            shutil.copytree("./migrations", backup_dir / "migrations")
            print("Migrations")
            count += 1

        if count > 0:
            print(f"Application data backup complete ({count} items)")
        else:
            print("No application data found")

        return count

    def create_backup_metadata(self, backup_dir: Path, db_only: bool) -> None:
        """Create backup metadata file"""
        # Get git info
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, check=False
            ).stdout.strip()

            commit = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, check=False
            ).stdout.strip()
        except:
            branch = "N/A"
            commit = "N/A"

        # Calculate total size
        total_size = sum(
            f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
        )

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "backup_type": "database_only" if db_only else "full",
            "git_branch": branch,
            "git_commit": commit,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "databases": ["postgresql", "chromadb", "redis"]
        }

        # Write JSON metadata
        with open(backup_dir / "backup_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        # Write human-readable metadata
        with open(backup_dir / "backup_info.txt", 'w') as f:
            f.write(f"""Litigation GenAI - Backup Information
=====================================
Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup Type: {"Database Only" if db_only else "Full Backup"}
Git Branch: {branch}
Git Commit: {commit}
Total Size: {metadata['total_size_mb']} MB

Databases Backed Up:
- PostgreSQL (relational database)
- ChromaDB (vector database)
- Redis (cache)
""")

        print("Metadata created")

    def create_backup(self, db_only: bool = False) -> Optional[Path]:
        """Create a full backup of all databases and optionally application data"""
        print("=" * 60)
        print("Litigation GenAI - Database Backup")
        print("=" * 60)

        # Validate environment
        if not self.validate_environment():
            return None

        # Create backup directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        print(f"Backup location: {backup_dir}")
        print(f"Database-only mode: {db_only}\n")

        # Backup databases
        success = True
        success &= self.backup_postgres(backup_dir)
        success &= self.backup_chromadb(backup_dir)
        success &= self.backup_redis(backup_dir)

        if not success:
            print("\nBackup failed - some databases could not be backed up")
            return None

        # Backup application data (unless db-only)
        if not db_only:
            self.backup_application_data(backup_dir)

        # Create metadata
        self.create_backup_metadata(backup_dir, db_only)

        # Summary
        total_size = sum(
            f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
        ) / (1024 * 1024)

        print("\n" + "=" * 60)
        print("BACKUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Location: {backup_dir}")
        print(f"Size: {total_size:.2f} MB")
        print(f"\nTo restore: python {sys.argv[0]} restore {backup_dir}")
        print("=" * 60)

        return backup_dir

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []

        for backup_dir in sorted(self.backup_root.iterdir(), reverse=True):
            if not backup_dir.is_dir():
                continue

            metadata_file = backup_dir / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
            else:
                # Legacy backup without JSON metadata
                metadata = {
                    "timestamp": backup_dir.name,
                    "backup_type": "unknown",
                    "total_size_mb": sum(
                        f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
                    ) / (1024 * 1024)
                }

            backups.append({
                "path": backup_dir,
                "name": backup_dir.name,
                **metadata
            })

        return backups

    def cleanup_old_backups(self, keep: int = 5) -> None:
        """Remove old backups, keeping only the most recent N"""
        backups = self.list_backups()

        if len(backups) <= keep:
            print(f"Found {len(backups)} backups, keeping all (limit: {keep})")
            return

        to_remove = backups[keep:]
        print(f"Removing {len(to_remove)} old backups (keeping {keep} most recent):")

        for backup in to_remove:
            print(f"  Removing: {backup['name']} ({backup['total_size_mb']:.2f} MB)")
            shutil.rmtree(backup['path'])

        print(f"✓ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(
        description="Database Backup Manager for Litigation GenAI"
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create a new backup')
    backup_parser.add_argument(
        '--db-only',
        action='store_true',
        help='Backup only databases (exclude application data)'
    )

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('backup_dir', help='Backup directory to restore from')
    restore_parser.add_argument(
        '--skip-confirmation',
        action='store_true',
        help='Skip confirmation prompt'
    )

    # List command
    list_parser = subparsers.add_parser('list', help='List all backups')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old backups')
    cleanup_parser.add_argument(
        '--keep',
        type=int,
        default=5,
        help='Number of recent backups to keep (default: 5)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = BackupManager()

    if args.command == 'backup':
        manager.create_backup(db_only=args.db_only)

    elif args.command == 'restore':
        print("❌ Restore functionality uses the shell script for safety.")
        print(f"   Run: ./restore.sh {args.backup_dir}")
        print("\n   The restore process requires careful handling of Docker volumes")
        print("   and is best done through the tested shell script.")

    elif args.command == 'list':
        backups = manager.list_backups()

        if not backups:
            print("No backups found")
            return

        print("\nAvailable Backups:")
        print("=" * 80)
        for backup in backups:
            print(f"📦 {backup['name']}")
            print(f"   Type: {backup['backup_type']}")
            print(f"   Size: {backup['total_size_mb']:.2f} MB")
            if 'git_branch' in backup:
                print(f"   Git: {backup['git_branch']} ({backup['git_commit']})")
            print()

    elif args.command == 'cleanup':
        manager.cleanup_old_backups(keep=args.keep)


if __name__ == '__main__':
    main()
