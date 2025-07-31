"""
Management command to test database connectivity to Supabase databases.
"""
import os
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from dotenv import load_dotenv


class Command(BaseCommand):
    help = 'Test database connectivity to staging and production Supabase databases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--env',
            type=str,
            choices=['staging', 'production', 'both'],
            default='both',
            help='Which environment to test (staging, production, or both)'
        )

    def handle(self, *args, **options):
        env_choice = options['env']
        
        if env_choice in ['staging', 'both']:
            self.test_database('staging')
            
        if env_choice in ['production', 'both']:
            self.test_database('production')

    def test_database(self, env_name):
        """Test database connectivity for the specified environment."""
        self.stdout.write(f"\n🔍 Testing {env_name.upper()} database connection...")
        
        # Load environment file
        # The Django command runs from backend/, so go up one level to project root
        import os
        backend_dir = os.getcwd()  # Should be /app (the backend directory in Docker)
        project_root = os.path.dirname(backend_dir)  # Go up to the parent directory
        env_file = os.path.join(project_root, f'.env.{env_name}')
        
        # Debug: show what we're looking for
        self.stdout.write(f"🔍 Looking for env file: {env_file}")
        self.stdout.write(f"🔍 Backend dir: {backend_dir}")
        self.stdout.write(f"🔍 Project root: {project_root}")
        self.stdout.write(f"🔍 Env file exists: {os.path.exists(env_file)}")
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            self.stdout.write(f"✅ Loaded {env_file}")
        else:
            self.stdout.write(self.style.ERROR(f"❌ Environment file {env_file} not found"))
            return

        # Display connection info (without password)
        db_url = os.getenv('DATABASE_URL', 'Not set')
        db_host = os.getenv('SUPABASE_DB_HOST', 'Not set')
        supabase_url = os.getenv('SUPABASE_URL', 'Not set')
        
        # Mask password in URL for display
        display_url = db_url.replace(':your-password@', ':****@') if 'your-password' in db_url else db_url
        if '@' in display_url and ':' in display_url:
            parts = display_url.split('@')
            if len(parts) >= 2:
                auth_part = parts[0]
                if ':' in auth_part:
                    user_pass = auth_part.split(':')
                    if len(user_pass) >= 3:  # postgresql://user:pass
                        display_url = f"{user_pass[0]}:{user_pass[1]}:****@{parts[1]}"
        
        self.stdout.write(f"📍 Database URL: {display_url}")
        self.stdout.write(f"📍 Database Host: {db_host}")
        self.stdout.write(f"📍 Supabase URL: {supabase_url}")

        try:
            # Test basic connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT version();')
                result = cursor.fetchone()
                self.stdout.write(self.style.SUCCESS(f"✅ {env_name.upper()} DB Connection successful!"))
                
                version_info = result[0][:80] + "..." if len(result[0]) > 80 else result[0]
                self.stdout.write(f"📊 PostgreSQL Version: {version_info}")
                
                # Test table count in public schema
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name NOT LIKE 'nextauth_%'
                """)
                django_table_count = cursor.fetchone()[0]
                
                # Test NextAuth table count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'nextauth_%'
                """)
                nextauth_table_count = cursor.fetchone()[0]
                
                self.stdout.write(f"📊 Django tables in public schema: {django_table_count}")
                self.stdout.write(f"📊 NextAuth tables in public schema: {nextauth_table_count}")
                
                # Test extensions
                cursor.execute("""
                    SELECT extname, extversion 
                    FROM pg_extension 
                    WHERE extname IN ('vector', 'pg_trgm', 'uuid-ossp')
                    ORDER BY extname
                """)
                extensions = cursor.fetchall()
                
                self.stdout.write("🔧 Required extensions:")
                for ext_name, ext_version in extensions:
                    self.stdout.write(f"   ✅ {ext_name}: {ext_version}")
                
                # Test a simple query on one of our tables
                cursor.execute("SELECT COUNT(*) FROM articles_article;")
                article_count = cursor.fetchone()[0]
                self.stdout.write(f"📰 Articles in database: {article_count}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ {env_name.upper()} DB Connection failed: {str(e)}"))
            
        self.stdout.write("-" * 60) 