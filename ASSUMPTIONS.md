# Assumptions

This document records reasonable assumptions made during the implementation of Customer Support Intelligence.

## Data & Analytics

1. **Satisfaction Score Range**: Assumed satisfaction scores range from 1-5. Scores above 5 are normalized by dividing by 20.
2. **SLA Thresholds**: SLA is considered met if resolution time is within: Critical < 240min, High < 480min, Medium < 1440min, Low < 2880min.
3. **Response Time**: Calculated as the difference between `first_response_at` and `created_at` in minutes.
4. **Resolution Time**: Calculated as the difference between `resolved_at` and `created_at` in minutes.
5. **Timezone**: All datetime values are stored in UTC. The sample dataset uses UTC.
6. **CSV Parsing**: Dates are parsed from common formats (ISO 8601, US format, EU format). Unparseable dates are set to null.

## Sentiment Analysis

7. **Rule-Based Approach**: Sentiment analysis uses a keyword-based approach with negation handling and intensifier detection. This is less accurate than transformer-based models but requires no external dependencies.
8. **Threshold**: Sentiment is classified as Positive if score > 0.15, Negative if < -0.15, and Neutral otherwise.
9. **Combined Text**: Both subject and description are combined for sentiment analysis.

## Ticket Classification

10. **Keyword Matching**: Classification uses keyword presence in subject and description text. This is a heuristic approach.
11. **Category List**: Fixed set of 10 categories (Billing, Technical Issue, Account Access, Product Issue, Shipping, Refund, Subscription, Login, Payment, Feature Request) plus "Other" as fallback.
12. **Minimum Confidence**: Classification confidence has a floor of 0.3 to avoid overly uncertain predictions.

## AI Layer

13. **Provider Abstraction**: The AI layer is designed to work without any external AI. When AI is unavailable, the application falls back to rule-based insights and calculated facts.
14. **Ollama Default**: When `AI_PROVIDER=local`, the system attempts to connect to Ollama at `http://localhost:11434`. If unavailable, AI features gracefully degrade.
15. **API Compatibility**: The API provider uses OpenAI-compatible `/v1/chat/completions` endpoint format, which works with most major LLM providers.
16. **No Hallucination**: AI-generated insights are based on actual computed analytics data. The system passes structured statistics to the LLM rather than allowing it to query the database directly.

## Authentication

17. **JWT Tokens**: Access tokens are used without refresh tokens for MVP simplicity. Tokens expire after 60 minutes by default.
18. **No RBAC**: All authenticated users have the same permissions. There is no role-based access control.
19. **Password Policy**: Minimum 8 characters required. No complexity requirements beyond length.

## Sample Data

20. **400 Tickets**: The sample dataset contains 400 synthetic tickets spanning 6 months.
21. **Realistic Distribution**: Categories are weighted (Billing ~25%, Technical ~20%, etc.) to reflect typical support distributions.
22. **Correlated Metrics**: Satisfaction scores correlate with response times and priority levels for realistic analytics.
23. **No Real Data**: All sample data is synthetically generated. No real customer data is used.

## Database

24. **PostgreSQL**: Required for production. SQLite is used only for testing.
25. **No Migrations in Docker**: Docker setup creates tables directly via SQLAlchemy `create_all()` for simplicity. Alembic migrations are available for manual setup.
26. **Dataset Ownership**: Users can only access their own datasets. Ownership is verified on every request.

## Frontend

27. **Desktop-First**: The UI is designed for desktop browsers (1200px+ width). Mobile is functional but not optimized.
28. **Local Storage**: Authentication tokens and theme preference are stored in localStorage.
29. **Selected Dataset**: The currently active dataset ID is stored in localStorage for cross-page persistence.
30. **No SSR**: The application is a client-side SPA. No server-side rendering.

## Upload

31. **Max File Size**: 10MB default limit for CSV uploads.
32. **CSV Only**: Only `.csv` file extensions are accepted.
33. **Column Auto-Detection**: Column names are normalized and matched against known aliases automatically.
34. **Graceful Degradation**: Missing optional columns (like `agent` or `channel`) default to "Unassigned" or "Email" respectively.

## Testing

35. **SQLite for Tests**: Backend tests use an in-memory SQLite database for speed and isolation.
36. **26 Tests**: Test suite covers authentication, datasets, analytics, tickets, and ML modules.
