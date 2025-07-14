# DailyBrief Team Development Guide

This document outlines our internal development processes and standards for the DailyBrief project.

## Team Values

- **Quality First**: We prioritize code quality and maintainability
- **Collaborative Development**: We work together and learn from each other
- **Continuous Improvement**: We regularly refine our processes and codebase
- **Knowledge Sharing**: We document our work and share insights with the team

## Development Workflow

### 1. Task Management

We use our internal project management system to track tasks:

- **Backlog**: Upcoming features and improvements
- **Ready**: Tasks ready for development
- **In Progress**: Tasks currently being worked on
- **Review**: Tasks awaiting code review
- **Done**: Completed tasks

### 2. Branching Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/[task-id]-description**: Individual feature branches
- **fix/[task-id]-description**: Bug fix branches
- **release/vX.Y.Z**: Release preparation branches

### 3. Development Process

1. **Task Assignment**: Pick up a task from the "Ready" column
2. **Branch Creation**: Create a feature branch from `develop`
3. **Development**: Implement the feature or fix
4. **Testing**: Write tests and ensure all existing tests pass
5. **Code Review**: Submit a pull request for review
6. **Deployment**: After approval, changes are merged to `develop`

### 4. Pull Request Process

1. Create a pull request to the `develop` branch
2. Fill out the PR template with:
   - Summary of changes
   - Testing performed
   - Screenshots (if UI changes)
   - Related task IDs
3. Request review from at least one team member
4. Address any feedback from reviewers
5. Once approved, merge the PR

## Code Standards

### Python (Backend)

- **Formatting**: Black with 88 character line length
- **Imports**: Sorted with isort
- **Type Hints**: Required for all functions
- **Docstrings**: Required for all public functions and classes
- **Testing**: pytest with minimum 80% coverage

```python
# Example function with proper formatting and type hints
def process_article(article_id: int, force_reprocess: bool = False) -> ProcessingResult:
    """
    Process an article through the AI pipeline.
    
    Args:
        article_id: The ID of the article to process
        force_reprocess: Whether to reprocess even if already processed
        
    Returns:
        ProcessingResult object with status and metrics
        
    Raises:
        ArticleNotFoundError: If article doesn't exist
    """
    # Implementation...
```

### TypeScript (Frontend)

- **Formatting**: Prettier with default settings
- **Linting**: ESLint with strict configuration
- **Types**: Strict type checking, avoid `any`
- **Components**: Functional components with hooks
- **Testing**: Vitest with React Testing Library

```typescript
// Example component with proper typing
interface ArticleCardProps {
  article: Article;
  isHighlighted?: boolean;
  onSelect: (articleId: string) => void;
}

export const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  isHighlighted = false,
  onSelect,
}) => {
  // Implementation...
};
```

## Testing Requirements

- **Unit Tests**: Required for all business logic
- **Integration Tests**: Required for API endpoints
- **Component Tests**: Required for UI components
- **End-to-End Tests**: Required for critical user flows

## Documentation

### Code Documentation

- **Backend**: Docstrings for all public functions and classes
- **Frontend**: JSDoc comments for complex functions
- **API**: OpenAPI/Swagger documentation for endpoints

### Project Documentation

- **Architecture**: High-level architecture diagrams and descriptions
- **Setup Guide**: Environment setup and configuration
- **User Flows**: Key user journey documentation
- **Pipeline Documentation**: Detailed AI pipeline documentation

## Environment Setup

See the [README.md](README.md) for detailed setup instructions.

## Troubleshooting Common Issues

### Pipeline Failures

If the AI processing pipeline fails:

1. Check the Celery logs: `./docker.sh logs celery`
2. Verify API keys are valid
3. Use the reset command: `./docker.sh django reset_failed_to_fetch_pending`

### Database Issues

For database connection problems:

1. Ensure PostgreSQL is running: `docker ps | grep postgres`
2. Check database migrations: `./docker.sh django showmigrations`
3. Reset database if needed: `./docker.sh django reset_db`

### Frontend Development

For Next.js development issues:

1. Clear the cache: `cd frontend && rm -rf .next`
2. Reinstall dependencies: `cd frontend && npm ci`
3. Check for TypeScript errors: `cd frontend && npm run type-check`

## Contact Information

- **Project Lead**: [Name] - [email@company.com]
- **Backend Lead**: [Name] - [email@company.com]
- **Frontend Lead**: [Name] - [email@company.com]
- **DevOps Contact**: [Name] - [email@company.com]

## Team Meetings

- **Daily Standup**: 9:30 AM, Monday-Friday
- **Sprint Planning**: Every other Monday, 10:00 AM
- **Retrospective**: Every other Friday, 3:00 PM
- **Tech Sync**: Wednesdays, 2:00 PM

---

Thank you for contributing to DailyBrief! 