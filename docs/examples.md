# Example Use Cases

This document provides comprehensive examples of how to use the AutoGen Codebase Understanding Agent for various development scenarios.

## Prerequisites

Before running these examples, ensure you have:
- Configured your `.env` file with valid API credentials
- Installed the codebase-agent: `uv sync`
- Verified your setup: `codebase-agent setup`

## Authentication Implementation Examples

### OAuth2 Implementation

**Scenario**: Adding OAuth2 authentication to an existing web application.

```bash
codebase-agent analyze "implement OAuth2 authentication with Google and GitHub providers"
```

**What the agent will analyze**:
- Existing user models and authentication patterns
- Current session management and security middleware
- Configuration files for environment variables
- API route structures and security decorators
- Frontend authentication components and state management

**Expected output includes**:
- Integration points for OAuth2 providers
- Required environment variables and configuration
- Database schema changes for OAuth tokens
- Frontend component modifications
- Security considerations and best practices

### JWT Token Authentication

**Scenario**: Implementing JWT-based API authentication.

```bash
codebase-agent analyze "add JWT token authentication for REST API endpoints"
```

**Analysis focus**:
- Current API authentication mechanisms
- Token generation and validation logic
- Middleware for token verification
- User session management patterns
- API error handling strategies

## API Development Examples

### REST API Endpoints

**Scenario**: Adding CRUD operations for a new resource.

```bash
codebase-agent analyze "create REST API endpoints for product management with validation"
```

**Agent examines**:
- Existing API routing patterns and conventions
- Database models and ORM usage
- Validation schemas and error handling
- HTTP status code usage patterns
- API documentation and testing patterns

### GraphQL Integration

**Scenario**: Adding GraphQL support to an existing REST API.

```bash
codebase-agent analyze "implement GraphQL API layer alongside existing REST endpoints"
```

**Analysis includes**:
- Current API architecture and data flow
- Database query patterns and performance considerations
- Authentication and authorization integration
- Schema definition and resolver patterns
- Caching and optimization strategies

## Database and Migration Examples

### Database Schema Changes

**Scenario**: Adding new tables and relationships.

```bash
codebase-agent analyze "add database tables for order management with foreign key relationships"
```

**Agent focuses on**:
- Existing database schema and migration patterns
- ORM model definitions and relationships
- Migration file structure and naming conventions
- Data validation and constraint patterns
- Index optimization strategies

### Data Migration

**Scenario**: Migrating data between different schema versions.

```bash
codebase-agent analyze "create data migration script to convert user roles from string to enum"
```

**Analysis covers**:
- Current data structure and relationships
- Migration safety and rollback strategies
- Data validation and integrity checks
- Performance considerations for large datasets
- Testing strategies for migration scripts

## Frontend Integration Examples

### React Component Integration

**Scenario**: Connecting React frontend to backend APIs.

```bash
codebase-agent analyze "integrate React components with user authentication API endpoints"
```

**Agent examines**:
- Existing React component architecture
- State management patterns (Redux, Context, etc.)
- API client configuration and error handling
- Authentication flow and token management
- Component lifecycle and data fetching patterns

### Form Handling and Validation

**Scenario**: Creating complex forms with validation.

```bash
codebase-agent analyze "implement multi-step form with client and server validation"
```

**Analysis includes**:
- Current form handling patterns and libraries
- Validation schemas and error display mechanisms
- State management for multi-step workflows
- API integration for form submission
- User experience and accessibility considerations

## Testing Implementation Examples

### Unit Testing Strategy

**Scenario**: Adding comprehensive unit tests for business logic.

```bash
codebase-agent analyze "implement unit tests for payment processing with mocking"
```

**Agent analyzes**:
- Existing test patterns and frameworks
- Mocking strategies for external dependencies
- Test data setup and teardown patterns
- Coverage requirements and reporting
- Testing utility functions and helpers

### Integration Testing

**Scenario**: Creating integration tests for API endpoints.

```bash
codebase-agent analyze "add integration tests for user registration and authentication flow"
```

**Focus areas**:
- Test database setup and isolation
- API client testing patterns
- Authentication flow testing
- Error scenario coverage
- Performance and load testing considerations

## Performance Optimization Examples

### Database Query Optimization

**Scenario**: Optimizing slow database queries.

```bash
codebase-agent analyze "optimize database queries for user dashboard with complex relationships"
```

**Analysis covers**:
- Current query patterns and performance bottlenecks
- Index optimization opportunities
- Query structure and JOIN patterns
- Caching strategies and cache invalidation
- Database connection pooling and optimization

### Frontend Performance

**Scenario**: Improving frontend loading performance.

```bash
codebase-agent analyze "optimize React application for faster initial page load"
```

**Agent examines**:
- Bundle size and code splitting opportunities
- Component rendering optimization
- State management efficiency
- Asset optimization and lazy loading
- Performance monitoring and metrics

## Security Implementation Examples

### Security Audit

**Scenario**: Reviewing application security patterns.

```bash
codebase-agent analyze "audit application security for common vulnerabilities and best practices"
```

**Security analysis includes**:
- Authentication and authorization patterns
- Input validation and sanitization
- SQL injection and XSS prevention
- CSRF protection mechanisms
- Secure configuration management

### Data Privacy Compliance

**Scenario**: Implementing GDPR/privacy compliance features.

```bash
codebase-agent analyze "implement user data export and deletion for privacy compliance"
```

**Focus areas**:
- Data collection and storage patterns
- User consent management
- Data export and portability
- Secure data deletion
- Audit logging and compliance reporting

## Microservices and Architecture Examples

### Service Decomposition

**Scenario**: Breaking down monolithic application into microservices.

```bash
codebase-agent analyze "identify microservice boundaries for user management and billing"
```

**Analysis includes**:
- Current service coupling and dependencies
- Data sharing and communication patterns
- Service boundary identification
- API gateway and routing considerations
- Database separation strategies

### Event-Driven Architecture

**Scenario**: Implementing event-driven communication between services.

```bash
codebase-agent analyze "implement event streaming for order processing workflow"
```

**Agent examines**:
- Current synchronous communication patterns
- Event schema design and versioning
- Message queue integration patterns
- Event sourcing and CQRS opportunities
- Error handling and dead letter patterns

## DevOps and Deployment Examples

### Container Deployment

**Scenario**: Containerizing application for deployment.

```bash
codebase-agent analyze "create Docker containers for production deployment with health checks"
```

**Analysis covers**:
- Current deployment patterns and dependencies
- Container optimization and security
- Health check and monitoring integration
- Configuration management in containers
- Multi-stage build optimization

### CI/CD Pipeline

**Scenario**: Setting up automated deployment pipeline.

```bash
codebase-agent analyze "implement CI/CD pipeline with automated testing and deployment"
```

**Focus areas**:
- Current build and test processes
- Deployment automation opportunities
- Environment management and configuration
- Testing integration and quality gates
- Monitoring and rollback strategies

## Advanced Use Cases

### Machine Learning Integration

**Scenario**: Adding ML features to existing application.

```bash
codebase-agent analyze "integrate recommendation engine with existing user behavior data"
```

**Analysis includes**:
- Data collection and preprocessing patterns
- Model training and deployment strategies
- API integration for ML services
- Performance and scalability considerations
- A/B testing and experimentation framework

### Real-time Features

**Scenario**: Adding real-time communication capabilities.

```bash
codebase-agent analyze "implement real-time chat functionality with WebSocket connections"
```

**Agent examines**:
- Current communication patterns and protocols
- WebSocket integration and fallback strategies
- Real-time state synchronization
- Scalability and connection management
- Security considerations for real-time features

## Tips for Effective Analysis

### Query Optimization

**Be specific about your goals**:
- ❌ "analyze the codebase"
- ✅ "implement user authentication with email verification"

**Include context about your environment**:
- ❌ "add database support"
- ✅ "add PostgreSQL support to existing SQLite application"

**Specify constraints and requirements**:
- ❌ "add payment processing"
- ✅ "integrate Stripe payment processing with webhook handling and subscription management"

### Iterative Analysis

For complex features, break them down into smaller queries:

1. **Discovery phase**: "analyze existing user management architecture"
2. **Planning phase**: "identify integration points for OAuth2 authentication"
3. **Implementation phase**: "provide step-by-step OAuth2 implementation with Google provider"

### Context Building

The agent learns from previous analysis in the same session. You can build on previous queries:

```bash
# First query
codebase-agent analyze "understand the current authentication system"

# Follow-up query building on previous knowledge
codebase-agent analyze "now add two-factor authentication to the existing system"
```

## Expected Analysis Times

| Codebase Size | Simple Query | Complex Query |
|---------------|--------------|---------------|
| Small (<1k files) | 30-60 seconds | 2-3 minutes |
| Medium (1k-10k files) | 1-2 minutes | 3-5 minutes |
| Large (10k+ files) | 2-5 minutes | 5-10 minutes |

**Note**: Times vary based on:
- Query complexity and specificity
- Model speed and API latency
- Codebase organization and structure
- Available system resources
