# Testing Guide

This project has different types of tests organized by their purpose and requirements.

## Test Types

### Unit Tests
Fast, isolated tests that mock all external dependencies.
- **Location**: `tests/unit/`
- **Purpose**: Test individual components in isolation
- **Dependencies**: No external services required

### Integration Tests
Tests that verify real component interactions with actual LLM calls.
- **Location**: `tests/integration/`
- **Purpose**: Test end-to-end functionality with real services
- **Dependencies**: Requires valid `OPENAI_API_KEY`

## Running Tests

### Run All Unit Tests (Fast)
```bash
# Run only unit tests (no LLM calls required)
pytest tests/unit/ -v
```

### Run All Tests Including Integration
```bash
# Requires OPENAI_API_KEY environment variable
export OPENAI_API_KEY=your_actual_key_here
pytest -v
```

### Run Only Integration Tests
```bash
# Run only integration tests with real LLM calls
export OPENAI_API_KEY=your_actual_key_here
pytest -m integration -v
```

### Skip Integration Tests
```bash
# Run all tests except integration tests
pytest -m "not integration" -v
```

## Test Markers

- `@pytest.mark.integration` - Tests that require real LLM API calls
- `@pytest.mark.unit` - Unit tests (optional marker)
- `@pytest.mark.slow` - Tests that take a long time to run

## Environment Setup for Integration Tests

Integration tests require a valid OpenAI API key:

1. Get an API key from https://platform.openai.com/api-keys
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. Run integration tests:
   ```bash
   pytest -m integration -v
   ```

## CI/CD Considerations

- **Unit tests**: Run on every commit (fast feedback)
- **Integration tests**: Run on pull requests or scheduled (requires API key secrets)

## Cost Considerations

Integration tests make real API calls which incur costs:
- Use `gpt-3.5-turbo` for cost efficiency during testing
- Monitor usage when running integration tests frequently
- Consider using test-specific prompts to minimize token usage
