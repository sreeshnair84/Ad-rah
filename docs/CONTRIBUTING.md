# Contributing to Adara Digital Signage Platform

Thank you for your interest in contributing to the Adara Digital Signage Platform! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Security](#security)

## 🤝 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

### Our Standards

- **Respectful Communication**: Be respectful and inclusive in all interactions
- **Constructive Feedback**: Provide constructive feedback and accept it gracefully
- **Collaboration**: Work together to solve problems and improve the codebase
- **Quality Focus**: Maintain high standards for code quality and documentation

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12+** with UV package manager
- **Node.js 18+** with npm
- **Docker & Docker Compose**
- **Git**
- **Azure CLI** (for infrastructure contributions)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Open_kiosk
   ```

2. **Set up the development environment**
   ```bash
   # Run the automated setup script (Windows)
   .\setup-environment.ps1

   # Or manually install dependencies
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

3. **Start development services**
   ```bash
   cd backend/content_service
   docker-compose up -d
   ```

4. **Initialize sample data**
   ```bash
   uv run python seed_data.py
   ```

5. **Start the frontend**
   ```bash
   cd ../../frontend
   npm install
   npm run dev
   ```

### Development URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔄 Development Workflow

### Branching Strategy

We use a Git flow branching strategy:

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Create a bug fix branch
git checkout -b bugfix/issue-description

# Create a hotfix branch (from main)
git checkout -b hotfix/critical-fix
```

### Commit Guidelines

We follow conventional commit format:

```bash
# Feature commits
git commit -m "feat: add user authentication system"

# Bug fixes
git commit -m "fix: resolve device registration timeout"

# Documentation
git commit -m "docs: update API documentation"

# Refactoring
git commit -m "refactor: optimize database queries"

# Testing
git commit -m "test: add unit tests for RBAC service"
```

### Commit Types

- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

## 💻 Coding Standards

### Backend (Python/FastAPI)

#### Code Style
- Follow **PEP 8** standards
- Use **Black** for code formatting
- Use **isort** for import sorting
- Maximum line length: **88 characters**

#### Type Hints
```python
# ✅ Good
def create_user(email: str, password: str) -> User:
    pass

# ❌ Bad
def create_user(email, password):
    pass
```

#### Error Handling
```python
# ✅ Good
try:
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
except Exception as e:
    logger.error(f"Error retrieving user: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# ❌ Bad
user = await user_repo.get_by_email(email)
```

#### Database Operations
```python
# ✅ Good - Use repository pattern
class UserRepository:
    async def create_user(self, user_data: dict) -> str:
        result = await self.collection.insert_one(user_data)
        return str(result.inserted_id)

# ❌ Bad - Direct database calls in handlers
@app.post("/users")
async def create_user(user: UserCreate):
    result = await db.users.insert_one(user.dict())
    return {"id": str(result.inserted_id)}
```

### Frontend (TypeScript/Next.js)

#### Code Style
- Use **TypeScript** for all new code
- Follow **ESLint** and **Prettier** configurations
- Use **functional components** with hooks
- Maximum line length: **100 characters**

#### Component Structure
```typescript
// ✅ Good
interface UserCardProps {
  user: User;
  onEdit: (user: User) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ user, onEdit }) => {
  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <button onClick={() => onEdit(user)}>Edit</button>
    </div>
  );
};

// ❌ Bad
export const UserCard = ({ user, onEdit }) => {
  return (
    <div>
      <h3>{user.name}</h3>
      <button onClick={() => onEdit(user)}>Edit</button>
    </div>
  );
};
```

#### State Management
```typescript
// ✅ Good - Use Zustand for global state
const useUserStore = create<UserStore>((set) => ({
  users: [],
  setUsers: (users) => set({ users }),
  addUser: (user) => set((state) => ({ users: [...state.users, user] })),
}));

// ❌ Bad - Prop drilling
const UserList = ({ users, onUserSelect }) => {
  return (
    <div>
      {users.map((user) => (
        <UserItem
          key={user.id}
          user={user}
          onSelect={onUserSelect}
        />
      ))}
    </div>
  );
};
```

### Infrastructure (Bicep/Terraform)

#### Naming Conventions
```bicep
// ✅ Good
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${resourcePrefix}storage${environment}'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
}

// ❌ Bad
resource myStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'mystorageaccount'
  location: 'eastus'
}
```

## 🧪 Testing Guidelines

### Backend Testing

#### Unit Tests
```python
# tests/test_auth.py
import pytest
from app.auth import create_access_token, verify_password

class TestAuth:
    def test_create_access_token(self):
        token = create_access_token({"sub": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)

    def test_verify_password(self):
        hashed = hash_password("testpass")
        assert verify_password("testpass", hashed) is True
        assert verify_password("wrongpass", hashed) is False
```

#### Integration Tests
```python
# tests/test_user_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "profile": {"first_name": "Test", "last_name": "User"}
    }

    response = await client.post("/api/users", json=user_data)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]
```

### Frontend Testing

#### Component Tests
```typescript
// __tests__/UserCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from '../components/UserCard';

const mockUser = {
  id: '1',
  name: 'John Doe',
  email: 'john@example.com'
};

const mockOnEdit = jest.fn();

test('renders user information', () => {
  render(<UserCard user={mockUser} onEdit={mockOnEdit} />);

  expect(screen.getByText('John Doe')).toBeInTheDocument();
  expect(screen.getByText('john@example.com')).toBeInTheDocument();
});

test('calls onEdit when edit button is clicked', () => {
  render(<UserCard user={mockUser} onEdit={mockOnEdit} />);

  fireEvent.click(screen.getByText('Edit'));
  expect(mockOnEdit).toHaveBeenCalledWith(mockUser);
});
```

### Test Coverage Requirements

- **Backend**: Minimum 85% coverage
- **Frontend**: Minimum 80% coverage
- **Critical paths**: 95%+ coverage required

## 📚 Documentation

### Code Documentation

#### Python Docstrings
```python
def create_user(email: str, password: str) -> User:
    """
    Create a new user account.

    Args:
        email: User's email address
        password: User's password (will be hashed)

    Returns:
        User: Created user object

    Raises:
        ValueError: If email is invalid or password is too weak
        DuplicateError: If user already exists

    Example:
        >>> user = create_user("user@example.com", "securepass")
        >>> print(user.email)
        user@example.com
    """
```

#### TypeScript JSDoc
```typescript
/**
 * User management hook for CRUD operations
 *
 * @param userId - Optional user ID for specific user operations
 * @returns Object with user data and management functions
 *
 * @example
 * ```typescript
 * const { user, updateUser, deleteUser } = useUser('123');
 *
 * // Update user
 * await updateUser({ name: 'New Name' });
 *
 * // Delete user
 * await deleteUser();
 * ```
 */
export const useUser = (userId?: string) => {
  // Implementation
};
```

### API Documentation

All API endpoints must be documented using OpenAPI/Swagger:

```python
@router.post(
    "/users",
    response_model=UserResponse,
    summary="Create new user",
    description="Create a new user account with the provided information",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid input data"},
        409: {"description": "User already exists"}
    }
)
async def create_user(user: UserCreate):
    pass
```

## 🔄 Pull Request Process

### PR Template

Please use the following template for pull requests:

```markdown
## Description
Brief description of the changes made

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Testing
Describe the testing performed and any relevant test cases

## Screenshots (if applicable)
Add screenshots to help explain the changes

## Additional Notes
Any additional information or context
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: At least one maintainer review required
3. **Testing**: All tests must pass
4. **Documentation**: Update documentation if needed
5. **Approval**: Maintainers approve and merge

### Review Guidelines

#### For Reviewers
- Check code quality and adherence to standards
- Verify test coverage for new features
- Ensure proper error handling
- Review security implications
- Check performance impact

#### For Contributors
- Address all review comments
- Keep PRs focused on single features/issues
- Test thoroughly before requesting review
- Update documentation as needed

## 🐛 Reporting Issues

### Bug Reports

Please use the bug report template:

```markdown
**Describe the Bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment**
- OS: [e.g., Windows 10]
- Browser: [e.g., Chrome 91]
- Version: [e.g., v2.1.0]

**Additional Context**
Add any other context about the problem here.
```

### Feature Requests

Please use the feature request template:

```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is.

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions you've considered.

**Additional Context**
Add any other context or screenshots about the feature request here.
```

## 🔒 Security

### Security Considerations

- **Never commit secrets** to version control
- **Use environment variables** for sensitive configuration
- **Validate all inputs** to prevent injection attacks
- **Implement proper authentication** and authorization
- **Keep dependencies updated** to avoid vulnerabilities

### Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not create a public issue**
2. **Email security concerns** to security@adara.com
3. **Provide detailed information** about the vulnerability
4. **Allow time for investigation** before public disclosure

### Security Best Practices

#### Code Security
```python
# ✅ Good - Parameterized queries
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

# ❌ Bad - SQL injection vulnerable
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

#### Authentication Security
```python
# ✅ Good - Secure password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

## 🎉 Recognition

Contributors will be recognized in:

- **Release notes** for significant contributions
- **Contributors file** for all contributors
- **Hall of fame** for exceptional contributions
- **Company swag** for top contributors

## 📞 Getting Help

If you need help contributing:

- **Documentation**: Check [docs/](docs/) directory
- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Create an issue for bugs or feature requests
- **Slack**: Join our contributor Slack channel

## 📋 Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [API Documentation](docs/api.md)
- [Development Setup](docs/QUICKSTART.md)
- [Codebase Optimization Report](docs/CODEBASE_OPTIMIZATION_REPORT.md)

---

Thank you for contributing to the Adara Digital Signage Platform! 🚀</content>
<parameter name="filePath">C:\Users\Srees\Workarea\Open_kiosk\docs\CONTRIBUTING.md