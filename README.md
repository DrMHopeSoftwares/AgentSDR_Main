# AgentSDR

A production-ready multi-tenant Flask application with Supabase integration, featuring role-based access control (RBAC), organization management, and secure invitation system.

## 🚀 Features

- **Multi-tenant Architecture**: Complete data isolation between organizations
- **Role-Based Access Control**: Super Admin, Org Admin, and Member roles
- **Supabase Integration**: PostgreSQL database with Row Level Security (RLS)
- **Secure Authentication**: Email/password with Supabase GoTrue
- **Invitation System**: Email-based invitations with token expiry
- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Enterprise Security**: CSRF protection, rate limiting, secure cookies
- **Docker Support**: Containerized deployment ready

## 🏗️ Architecture

```
AgentSDR/
├── agentsdr/                 # Main application package
│   ├── auth/                # Authentication & user management
│   ├── core/                # Core utilities & models
│   ├── orgs/                # Organization management
│   ├── records/             # Example domain data
│   ├── admin/               # Super admin functionality
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, assets
├── supabase/                # Database schema & migrations
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
└── config files             # Docker, Makefile, etc.
```

## 🛠️ Tech Stack

- **Backend**: Flask 3.0, Python 3.11+
- **Database**: Supabase (PostgreSQL + GoTrue Auth)
- **Frontend**: Jinja2 + Tailwind CSS + Alpine.js + HTMX
- **Security**: Flask-Login, CSRF protection, RLS policies
- **Testing**: Pytest with coverage
- **Deployment**: Docker, Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Node.js 16+ (for Tailwind CSS)
- Supabase account
- SMTP server (for email invitations)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AgentSDR
make setup
```

### 2. Configure Environment

Copy the example environment file and update with your credentials:

```bash
cp env.example .env
```

Update `.env` with your Supabase and SMTP settings:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Flask Configuration
FLASK_SECRET_KEY=your-super-secret-key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### 3. Setup Supabase Database

1. Create a new Supabase project
2. Run the schema migration:

```sql
-- Copy and execute the contents of supabase/schema.sql
-- in your Supabase SQL editor
```

### 4. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for Tailwind CSS)
npm install
```

### 5. Build CSS

```bash
npm run build:css
```

### 6. Seed Database (Optional)

```bash
make seed
```

### 7. Run Development Server

```bash
make dev
```

Visit `http://localhost:5000` to see the application!

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
make docker-build

# Run with Docker Compose
make docker-run

# View logs
make docker-logs

# Stop containers
make docker-stop
```

### Production Deployment

1. Update environment variables for production
2. Build production CSS: `npm run build:css:prod`
3. Use production WSGI server (Gunicorn)

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest --cov=agentsdr --cov-report=html

# Lint code
make lint

# Format code
make format
```

## 📊 Database Schema

### Core Tables

- **users**: User profiles and authentication
- **organizations**: Multi-tenant organizations
- **organization_members**: User-org relationships with roles
- **invitations**: Email invitations with tokens
- **records**: Example domain data (scoped to orgs)

### Row Level Security (RLS)

All tables have RLS policies ensuring:
- Users can only access data from their organizations
- Super admins can access all data
- Org admins can manage their organization's data
- Invitations are secure with token expiry

## 🔐 Security Features

- **Authentication**: Supabase GoTrue with secure session management
- **Authorization**: Role-based access control with decorators
- **Data Isolation**: Complete multi-tenant data separation
- **CSRF Protection**: Flask-WTF CSRF tokens
- **Rate Limiting**: Flask-Limiter integration
- **Secure Cookies**: HTTP-only, secure, same-site cookies
- **Invitation Security**: Cryptographically secure tokens with expiry

## 👥 User Roles

### Super Admin
- Full platform access
- Manage all organizations and users
- View platform analytics
- Access admin panel

### Organization Admin
- Create and manage organizations
- Invite and remove members
- Assign member roles
- Manage organization settings

### Member
- Access organization data
- Create and manage records
- View organization members

## 📧 Invitation System

1. **Create Invitation**: Org admin invites user by email
2. **Email Delivery**: Secure HTML email with acceptance link
3. **Token Verification**: Cryptographically secure token validation
4. **Account Creation**: New users can sign up during acceptance
5. **Role Assignment**: User automatically added with specified role

## 🔧 Development

### Project Structure

```
agentsdr/
├── __init__.py              # Flask app factory
├── auth/                    # Authentication module
│   ├── routes.py           # Auth endpoints
│   ├── models.py           # User model
│   └── forms.py            # Auth forms
├── core/                    # Core utilities
│   ├── supabase_client.py  # Supabase integration
│   ├── rbac.py             # Authorization decorators
│   ├── models.py           # Pydantic models
│   └── email.py            # Email service
├── orgs/                    # Organization management
├── records/                 # Example domain data
├── admin/                   # Super admin functionality
└── templates/               # Jinja2 templates
```

### Adding New Features

1. **Create Blueprint**: Add new module in `agentsdr/`
2. **Define Models**: Use Pydantic for validation
3. **Add Routes**: Implement with proper authorization
4. **Create Templates**: Use Tailwind CSS for styling
5. **Write Tests**: Ensure coverage for new functionality

### Database Migrations

For schema changes:
1. Update `supabase/schema.sql`
2. Run in Supabase SQL editor
3. Update models if needed
4. Add tests for new functionality

## 🚀 Deployment

### Railway

1. Connect GitHub repository
2. Set environment variables
3. Deploy automatically

### Render

1. Create new Web Service
2. Connect repository
3. Set build command: `pip install -r requirements.txt && npm install && npm run build:css:prod`
4. Set start command: `gunicorn app:app`

### Fly.io

1. Install Fly CLI
2. Create `fly.toml` configuration
3. Deploy with `fly deploy`

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | Yes |
| `FLASK_SECRET_KEY` | Flask secret key | Yes |
| `SMTP_HOST` | SMTP server host | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SMTP_USER` | SMTP username | Yes |
| `SMTP_PASS` | SMTP password | Yes |
| `BASE_URL` | Application base URL | No |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting: `make lint`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the test suite for examples

## 🎯 Roadmap

- [ ] API endpoints for mobile apps
- [ ] Advanced analytics dashboard
- [ ] Webhook integrations
- [ ] Multi-language support
- [ ] Advanced file uploads
- [ ] Real-time notifications
- [ ] Audit logging
- [ ] Backup and restore functionality

---

Built with ❤️ using Flask and Supabase
